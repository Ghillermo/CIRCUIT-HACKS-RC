"""SC40.9 (the user, 2026-10-14): Master FX per session, the master compressor in the Sidechain view, the recording of the internal MIDI routes.

1. MASTER FX PER SESSION («los 20 knobs de la fila superior y también la asignación de los pads», «nada fijado»).  The 20 knob bytes of the five
   top-row effects (the Master FX block + 8) and the attack / release of the master compressor travel with the project, in the last 1000 bytes
   of its record (saved and loaded whole by the stock, SC403D on the unit), 128 bytes into that tail, behind patchain's: "MFX1", a checksum,
   20 knobs, attack, release.  A project without the block (an old one, a new one) keeps what the unit has.
     * the save (the bl at 0x0802FE5E, in front of the other hooks) writes the block into the RAM record, unless the loaded project's own values
       are still waiting to be applied;
     * after a load (patchain zeroes the running part of the tail then; the byte + 40 of that part = «applied») the LED task copies the block
       into the Master FX block, marks it for the DSP and sets the two compressor values through the listener of the MIDI input.
   The slot assignments (the lower row) already are in the project (persist19); persist19.GFX_SESSION loads them from every project that has them.
2. THE MASTER COMPRESSOR («Compresor no aparece.  Colocar máster comp en vistas de sidechain»): in the Sidechain view K7 = attack, K8 = release
   (values 3 / 4 of the master group, type 0x21), their LEDs white with the value.  SC40.2 had them on K1 / K2 of the Setup view, where nothing
   showed on the unit: the Setup view is not the controller's active view (it is [ctrl + 0x68], shown while the mode [ctrl + 0x14] is 8, and
   only button presses are forwarded to it), so compkn's hooks never ran.  They are taken out (the slot back to the stock's stub, its LED code
   skipped).
3. RECORDING THE INTERNAL ROUTES («cuando implementamos transmisión de midi 1 / 2 a synth 1 / 2, activar la grabación accidentalmente escribía en
   Synth 1 / 2.  Esto no nos interesa por defecto, pero sería interesante para, por ejemplo, grabar cambios de escala o de octava en tiempo real.
   Permite que los ruteos internos de MIDI se graben con un toggle en Setup (por ejemplo, en Record: amarillo activa grabación interna, apagado:
   por defecto, sin grabación)»): what a MIDI track sends to an internal track (SC05 / SC06) is injected with the «internal» bit set, and the
   three recorder gates (0x0802E56A, 0x0802E5CC, 0x0802E62C) return without recording then.  Record in the Setup view (not its Advanced page;
   the stock does nothing with it there) toggles a byte; while it is on the gates record as for an external message.  The Record LED in the
   Setup view: yellow = on, dark = off.  Off at power-up (two bytes of the Setup view object, in the padding after its «Advanced» flag, which the unit leaves as the allocator gave it: «on» is a value of 16 bits).
   Note: everything injected is recorded then, the auditions of the step-drummer of Synth 1 / 2 too.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thumb  # noqa: E402
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm,  # noqa: E402
                   lsrs_imm, ldrh_imm, strh_imm, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, h, str_imm, strb_imm, strb_reg, strh_reg, subs_imm8)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import patchain as PC  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import sckn as SK  # noqa: E402
import compkn as CK  # noqa: E402

MGR, CTX = 0x20040B10, 0x200069E4
GETTER, PARAM_SET = 0x08036192, 0x08034D92
SAVE_CALL = P19.SAVE_CALL
S_KNOB, S_DIRTY, N_KNOBS = 8, 28, 20                          # the Master FX block (build_sc17): 5 sets x 4 knobs, «send the parameters again»
S_APPL, APPL = PC.SCR + 40, 0xA5                              # the running part of the tail: this project's block has been applied
BLK, B_SUM, B_KNOB, B_COMP, B_END, SUM_XOR = 128, 4, 5, 25, 27, 0xA6
MAGIC = struct.unpack("<I", b"MFX1")[0]
TYPE, IDX = 0x21, (3, 4)                                      # the master group: the compressor's attack, its release
KNOBS = (6, 7)                                                # K7, K8 of the Sidechain view
COL_COMP, COL_REC, LED_REC = 0x01, 0x2D, 48
SETUP_VT, SETUP_OBJ, ADV_OFF, REC_OFF, REC_ON = CK.SETUP_VT, CK.SETUP_OBJ, CK.ADV_OFF, 0x26, 0x5CA7      # (the halfword at + 0x26)
MODE_STORE, MODE_SETUP, SETUP_PTR, BTN_REC = 0x14, 8, 0x68, 16   # [ctrl + 0x14] parameter 0 = 8: every button press goes to [ctrl + 0x68]'s slot 2
GATES = (0x0802E56A, 0x0802E5CC, 0x0802E62C)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
BX_LR = h(0x4770)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def getter(idx_reg=None, idx=None):                       # -> r0 = the value of the master group
        E(movs_imm, 0, TYPE)
        if idx is None: E(mov_reg, 1, idx_reg)
        else: E(movs_imm, 1, idx)
        E(bl, GETTER)
    def setter(idx_reg, val_reg):                             # (the listener of the MIDI input: the store, the DSP, MIDI out)
        E(mov_reg, 3, val_reg)
        imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
        E(adds_imm8, 0, 4); E(movs_imm, 1, TYPE); E(mov_reg, 2, idx_reg); E(bl, PARAM_SET)

    # ---- c_fssumv (r0 = the block) -> r0 = the checksum it should carry; clobbers r1-r3
    a.label("c_fssumv")
    E(movs_imm, 1, B_KNOB); E(movs_imm, 2, 0)
    a.label("sv_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, B_END); E(b_cond, "sv_l", "lo")
    E(movs_imm, 0, SUM_XOR); E(eors_reg, 0, 2); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24); E(raw, BX_LR)

    # ---- c_fsvalid (r0 = the block) -> r0 = 1 when it is ours (the mark and the sum); clobbers r1-r3
    a.label("c_fsvalid")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(ldr_imm, 0, 4, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); E(b_cond, "va_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fssumv"); E(ldrb_imm, 1, 4, B_SUM); E(cmp_reg, 0, 1); E(b_cond, "va_n", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("va_n"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_fsapply(): once after every load, the project's block (if it has one) into the unit; clobbers r0-r3
    a.label("c_fsapply")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ap_x", "eq"); E(mov_reg, 5, 0)
    E(bl, L["c_pcst"]); E(cmp_imm, 0, 0); E(b_cond, "ap_x", "eq"); E(mov_reg, 4, 0)
    E(movs_imm, 1, S_APPL); E(ldrb_reg, 0, 4, 1); E(cmp_imm, 0, APPL); E(b_cond, "ap_x", "eq")
    E(movs_imm, 0, APPL); E(strb_reg, 0, 4, 1)
    E(adds_imm8, 4, BLK); E(mov_reg, 0, 4); E(bl, "c_fsvalid"); E(cmp_imm, 0, 0); E(b_cond, "ap_x", "eq")
    E(movs_imm, 6, 0)
    a.label("ap_k")                                                                   # the knobs (bit 7 of the unit's byte kept)
    E(mov_reg, 0, 6); E(adds_imm8, 0, B_KNOB); E(ldrb_reg, 1, 4, 0); E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2)
    E(mov_reg, 0, 6); E(adds_imm8, 0, S_KNOB); E(ldrb_reg, 3, 5, 0); E(movs_imm, 2, 0x80); E(ands_reg, 3, 2); E(orrs_reg, 1, 3); E(strb_reg, 1, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, N_KNOBS); E(b_cond, "ap_k", "lo")
    E(movs_imm, 0, 1); E(strb_imm, 0, 5, S_DIRTY)
    E(movs_imm, 6, 0)
    a.label("ap_c")                                                                   # the compressor
    E(mov_reg, 0, 6); E(adds_imm8, 0, B_COMP); E(ldrb_reg, 7, 4, 0); E(movs_imm, 2, 0x7F); E(ands_reg, 7, 2)
    E(mov_reg, 5, 6); E(adds_imm8, 5, IDX[0])
    getter(idx_reg=5); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(cmp_reg, 0, 7); E(b_cond, "ap_n", "eq")
    setter(5, 7)
    a.label("ap_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, len(IDX)); E(b_cond, "ap_c", "lo")
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fssave (in the place of the bl to the stock save: r0 = the session manager): the block into the record, then the chain
    a.label("c_fssave")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "sa_x", "eq"); E(mov_reg, 5, 0)
    E(bl, L["c_pcst"]); E(cmp_imm, 0, 0); E(b_cond, "sa_x", "eq"); E(mov_reg, 4, 0)
    E(movs_imm, 1, S_APPL); E(ldrb_reg, 0, 4, 1); E(cmp_imm, 0, APPL); E(b_cond, "sa_x", "ne")       # (the project's own values first)
    E(adds_imm8, 4, BLK); imm32(0, MAGIC); E(str_imm, 0, 4, 0)
    E(movs_imm, 6, 0)
    a.label("sa_k")
    E(mov_reg, 0, 6); E(adds_imm8, 0, S_KNOB); E(ldrb_reg, 1, 5, 0); E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2)
    E(mov_reg, 0, 6); E(adds_imm8, 0, B_KNOB); E(strb_reg, 1, 4, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, N_KNOBS); E(b_cond, "sa_k", "lo")
    for k, idx in enumerate(IDX):
        getter(idx=idx); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(strb_imm, 0, 4, B_COMP + k)
    E(mov_reg, 0, 4); E(bl, "c_fssumv"); E(strb_imm, 0, 4, B_SUM)
    a.label("sa_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["save"])

    # ---- c_fsknob (the track views' container, slot 4: container, knob, delta): the Sidechain view: K7 / K8 = the compressor's attack / release
    a.label("c_fsknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, SK.MODE_OFF); E(cmp_imm, 0, SK.MODE_SC); E(b_cond, "kn_f", "ne")
    E(cmp_imm, 5, KNOBS[0]); E(b_cond, "kn_f", "lo"); E(cmp_imm, 5, KNOBS[-1]); E(b_cond, "kn_f", "hi")
    E(mov_reg, 4, 5); E(subs_imm8, 4, KNOBS[0] - IDX[0])
    getter(idx_reg=4); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(mov_reg, 7, 0)
    E(adds_reg, 0, 0, 6); E(cmp_imm, 0, 0); E(b_cond, "kn_l", "ge"); E(movs_imm, 0, 0)
    a.label("kn_l"); E(cmp_imm, 0, 127); E(b_cond, "kn_h", "le"); E(movs_imm, 0, 127)
    a.label("kn_h"); E(cmp_reg, 0, 7); E(b_cond, "kn_e", "eq")
    E(mov_reg, 7, 0); setter(4, 7)
    a.label("kn_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_fssbtn (the Setup view's slot 2: view, button): Record, not in the Advanced page = the recording of the internal routes on / off
    a.label("c_fssbtn")
    E(cmp_imm, 1, BTN_REC); E(b_cond, "sb_f", "ne")
    E(ldrb_w, 2, 0, ADV_OFF); E(cmp_imm, 2, 0); E(b_cond, "sb_f", "ne")
    E(ldrh_imm, 2, 0, REC_OFF); E(movw, 3, REC_ON); E(cmp_reg, 2, 3); E(b_cond, "sb_w", "ne"); E(movs_imm, 3, 0)
    a.label("sb_w"); E(strh_imm, 3, 0, REC_OFF); E(raw, BX_LR)
    a.label("sb_f"); E(b_w, prev["sbtn"])

    # ---- the recorder gates: with the toggle on an injected message is recorded as an external one; else SC05's gate
    for addr in GATES:
        cave, prologue = prev["gates"][addr]
        a.label(f"c_fsgate_{addr:x}")
        E(push_list, [0, 1])
        imm32(0, SETUP_OBJ + REC_OFF); E(ldrh_imm, 0, 0, 0); E(movw, 1, REC_ON); E(cmp_reg, 0, 1)
        E(pop_list, [0, 1])
        E(b_cond, f"ga_{addr:x}", "eq"); E(b_w, cave)
        a.label(f"ga_{addr:x}"); E(raw, prologue); E(b_w, addr + 4)

    # ---- c_fsledtask (the LED task calls: ctrl, frame): the chain; the project's block after a load; the Sidechain view: K7 / K8 white with
    #      their value; the Setup view: Record yellow / dark
    a.label("c_fsledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_fsapply")
    E(bl, L["c_skon"]); E(cmp_imm, 0, 0); E(b_cond, "lt_s", "eq")
    for k, idx in zip(KNOBS, IDX):
        getter(idx=idx); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1)
        E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(movs_imm, 1, COL_COMP); E(orrs_reg, 0, 1); E(movs_imm, 1, 2 * (60 + k)); E(strh_reg, 0, 5, 1)
    a.label("lt_s")
    imm32(0, MGR); E(ldr_imm, 1, 0, SETUP_PTR); imm32(2, SETUP_OBJ); E(cmp_reg, 1, 2); E(b_cond, "lt_x", "ne")
    E(ldr_imm, 0, 0, MODE_STORE); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, MODE_SETUP); E(b_cond, "lt_x", "ne")
    imm32(0, SETUP_OBJ); E(ldrb_w, 1, 0, ADV_OFF); E(cmp_imm, 1, 0); E(b_cond, "lt_x", "ne")
    E(ldrh_imm, 1, 0, REC_OFF); E(movw, 3, REC_ON); E(movs_imm, 2, 0); E(cmp_reg, 1, 3); E(b_cond, "lt_w", "ne"); E(movs_imm, 2, COL_REC)
    a.label("lt_w"); E(movs_imm, 0, 2 * LED_REC); E(strh_reg, 2, 5, 0)
    a.label("lt_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def gate_prev(img, base):
    """Each gate's cave (SC05 / SC06) and the stock's 4 bytes it carries: {gate: (cave, bytes)}."""
    out = {}
    for addr in GATES:
        cave = MP.bw_target(img, addr, base)
        for off in range(4, 64, 2):
            if bytes(img[cave + off - base:cave + off - base + 4]) == b_w(cave + off, addr + 4):
                out[addr] = (cave, bytes(img[cave + off - 4 - base:cave + off - base])); break
        else:
            raise AssertionError(hex(addr))
    return out


def install(img, report, base_addr):
    """Append the code; the save call, slot 4 of the container, slot 2 of the Setup view (and compkn's hooks out), the three gates, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gfst=lab("sc17", "c_gfst"), c_pcst=lab("patchain", "c_pcst"), c_skon=lab("sckn", "c_skon"))
    prev = dict(knob=u(SK.CT_VT + 16) & ~1, ledtask=lab("playmode", "c_pmledtask"), save=FD.bl_target(img, SAVE_CALL, BASE), sbtn=u(SETUP_VT + 8) & ~1,
                gates=gate_prev(img, BASE))
    assert prev["knob"] == lab("sckn", "c_skknob")
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_fssave"])
    struct.pack_into("<I", img, SK.CT_VT + 16 - BASE, labels["c_fsknob"] | 1)
    struct.pack_into("<I", img, SETUP_VT + 8 - BASE, labels["c_fssbtn"] | 1)
    for addr in GATES:
        img[addr - BASE:addr - BASE + 4] = b_w(addr, labels[f"c_fsgate_{addr:x}"])
    # compkn (SC40.2) out: its knob slot back to the stock's, its LED code skipped
    assert u(SETUP_VT + 16) & ~1 == lab("compkn", "c_ckknob")
    struct.pack_into("<I", img, SETUP_VT + 16 - BASE, int(report["compkn"]["prev"]["knob"], 16) | 1)
    skip, end = lab("compkn", "c_ckledtask") + 8, lab("compkn", "cl_x")
    assert bytes(img[skip - BASE:skip - BASE + 4]) == movw(0, MGR & 0xFFFF), hex(skip)
    img[skip - BASE:skip - BASE + 2] = b(skip, end)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_fsledtask"])
    prev["gates"] = {hex(k): hex(v[0]) for k, v in prev["gates"].items()}
    return labels, code, prev
