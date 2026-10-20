"""SC44.2 (the user, 2026-10-18: «add split keyboard for any two tracks»): the split keyboard of SC38.9 (srcview.use_split: Synth 1 + Synth 2) for any two
of the note tracks: Synth 1, Synth 2, MIDI 1, MIDI 2 (track buttons 0..3).  Hold one, press another: pads 1-16 play the one held first, pads 17-32
the other one, each through its own Note view (its scale, octave, velocity: the bottom half of that view's keyboard, as srcview), LEDs = their
keyboard windows.  A single track button, or any other view button (ids 0..15), ends it (the notes still held are released first); Play, Record,
Octave, Shift, Clear... leave it on.  The drum tracks are not keyboards: Drum 1-4 buttons go to the stock.

How (srcview's split, generalised, in front of it): a new head of the button chain (c_s4btn, at 0x08033320) and of the button release (c_s4rel, at
0x0803381A, in front of srcview's c_brel) keep the held bits of buttons 0..3; the second button of a pair is swallowed (srcview never sees the pair,
so its own split never starts); underneath, the stock pads held are released and a tap on Note leaves the first track's Note view on the screen; the
track views' container's slots 0 / 1 / 7 are ours in front of srcview's (pad, release, LEDs) while the split is on.  State: SPR (our RAM after
modmx's, see modmx.MXR), with a signature."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, ldr_sp, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrh_reg, lsls_imm,  # noqa: E402
                   lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, tst_reg)
import srcview as SV  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402

SPR = MX.MXR + 0xC0                   # 0x200450C0
SIG = 0x34535053                      # "SPS4"
O_HELD, O_FIRST, O_ON, O_TOP, O_BOT, O_MASK = 4, 5, 6, 7, 8, 12
N_TRK = 4                             # buttons 0..3 = Synth 1, Synth 2, MIDI 1, MIDI 2
S_PAINT = 20                          # SC14's state byte with srcview's flags (build_sc15.S_PAINT)
INV = SV.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev, gst):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_s{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def mask_addr(rd, cont):                                                        # rd = &[cont + HELD_MASK] (the stock's pads held)
        E(movs_imm, rd, SV.HELD_MASK >> 4); E(lsls_imm, rd, rd, 4); E(adds_reg, rd, rd, cont)

    # ---- c_s4st() -> r0 = SPR, set up at the first use; clobbers r1-r3
    a.label("c_s4st")
    imm32(0, SPR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_i", "ne"); E(raw, h(0x4770))
    a.label("st_i")
    E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, O_FIRST); E(str_imm, 2, 0, 0); E(raw, h(0x4770))

    # ---- c_s4trk(r0 = pad 0..31) -> r0 = the track of that half; clobbers r1-r3
    a.label("c_s4trk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_s4st")
    E(ldrb_imm, 1, 0, O_TOP); E(cmp_imm, 4, 16); E(b_cond, "tk_x", "lo"); E(ldrb_imm, 1, 0, O_BOT)
    a.label("tk_x"); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_s4view(r0 = cont, r1 = pad) -> r0 = the Note view of that half's track; clobbers r1-r3
    a.label("c_s4view")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(mov_reg, 0, 1); E(bl, "c_s4trk"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(movs_imm, 2, 1); E(bl, SV.NV_GET)
    E(pop_list, [4], pc=True)

    # ---- c_s4prel(r0 = cont, r1 = pad): a pad of the split keyboard released (if it holds one)
    a.label("c_s4prel")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 31); bc("pr_x", "hi")
    E(bl, "c_s4st"); E(mov_reg, 7, 0)
    E(ldr_imm, 0, 7, O_MASK); E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(tst_reg, 0, 1); bc("pr_x", "eq")
    E(bics_reg, 0, 1); E(str_imm, 0, 7, O_MASK)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_s4view"); E(cmp_imm, 0, 0); bc("pr_x", "eq")
    E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(movs_imm, 1, 15); E(raw, h(0x4029)); E(adds_imm8, 1, 16); E(blx_reg, 3)   # ands r1, r5: (pad & 15) + 16
    a.label("pr_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_s4off(r0 = ctrl): the notes still held released, the split off
    a.label("c_s4off")
    E(push_list, [4, 5, 6], lr=True)
    E(ldr_imm, 4, 0, 0x2C); E(movs_imm, 5, 0)
    a.label("of_l"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_s4prel"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, "of_l", "lo")
    E(bl, "c_s4st"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_ON)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_s4btn (ctrl, id): the head of the button chain
    a.label("c_s4btn")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_s4st"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, N_TRK - 1); bc("sb_other", "hi")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, SV.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("sb_prev", "ne")   # Shift: the stock
    E(ldrb_imm, 0, 6, O_HELD); E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(mov_reg, 2, 0); E(bics_reg, 2, 1); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, O_HELD)
    E(cmp_imm, 2, 0); bc("sb_single", "eq")
    # a second note track: the split, the first one held on top
    E(ldrb_imm, 7, 6, O_FIRST); E(movs_imm, 1, 1); E(lsls_reg, 1, 7); E(tst_reg, 2, 1); E(b_cond, "sb_f", "ne")
    E(movs_imm, 7, 0)                                                               # (the first is not held any more: the lowest held)
    a.label("sb_lo"); E(movs_imm, 1, 1); E(lsls_reg, 1, 7); E(tst_reg, 2, 1); E(b_cond, "sb_f", "ne"); E(adds_imm8, 7, 1); E(b, "sb_lo")
    a.label("sb_f")
    E(ldrb_imm, 0, 6, O_ON); E(cmp_imm, 0, 0); E(b_cond, "sb_new", "eq")
    E(ldrb_imm, 0, 6, O_TOP); E(cmp_reg, 0, 7); E(b_cond, "sb_chg", "ne"); E(ldrb_imm, 0, 6, O_BOT); E(cmp_reg, 0, 5); bc("sb_x", "eq")
    a.label("sb_chg"); E(mov_reg, 0, 4); E(bl, "c_s4off"); E(b, "sb_on")
    a.label("sb_new")                                                               # the pads held the stock's way: released
    E(push_list, [7]); E(ldr_imm, 7, 4, 0x2C); mask_addr(6, 7); E(movs_imm, 5, 0)
    a.label("sb_rl")
    E(ldr_imm, 0, 6, 0); E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(tst_reg, 0, 1); E(b_cond, "sb_rn", "eq")
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, SV.CT_REL & ~1)
    a.label("sb_rn"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, "sb_rl", "lo")
    E(pop_list, [7]); E(ldr_sp, 5, 4)                                              # the id again
    a.label("sb_on")
    E(mov_reg, 0, 4); E(movs_imm, 1, SV.ID_NOTE); E(bl, SV.BTN)                    # the first track's Note view underneath ...
    E(mov_reg, 0, 4); E(movs_imm, 1, SV.ID_NOTE); E(bl, SV.BTN_REL)
    E(bl, "c_s4st"); E(strb_imm, 7, 0, O_TOP); E(strb_imm, 5, 0, O_BOT)
    E(movs_imm, 1, 0); E(str_imm, 1, 0, O_MASK); E(movs_imm, 1, 1); E(strb_imm, 1, 0, O_ON)   # ... then the split on
    E(b, "sb_x")
    a.label("sb_single")                                                            # one track button: the first; it ends a split, then the stock
    E(strb_imm, 5, 6, O_FIRST)
    E(ldrb_imm, 0, 6, O_ON); E(cmp_imm, 0, 0); bc("sb_prev", "eq")
    E(mov_reg, 0, 4); E(bl, "c_s4off")
    E(cmp_imm, 5, 1); bc("sb_prev", "hi")                                           # Synth 1 / 2: srcview's split flag set, so srcview ends "its" split
    E(bl, gst); E(cmp_imm, 0, 0); bc("sb_prev", "eq")                               # and sends the press to the stock (not the source view's second press)
    E(ldrb_imm, 1, 0, S_PAINT); E(movs_imm, 2, SV.F_SPLIT); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, S_PAINT); E(b, "sb_prev")
    a.label("sb_other")
    E(ldrb_imm, 0, 6, O_ON); E(cmp_imm, 0, 0); bc("sb_prev", "eq")
    E(cmp_imm, 5, 15); bc("sb_prev", "hi")
    E(mov_reg, 0, 4); E(bl, "c_s4off")
    a.label("sb_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["btn"])
    a.label("sb_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)

    # ---- c_s4rel (ctrl, id): the head of the button release
    a.label("c_s4rel")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(mov_reg, 4, 1); E(cmp_imm, 4, N_TRK - 1); E(b_cond, "rl_x", "hi")
    E(bl, "c_s4st"); E(ldrb_imm, 1, 0, O_HELD); E(movs_imm, 2, 1); E(lsls_reg, 2, 4); E(bics_reg, 1, 2); E(strb_imm, 1, 0, O_HELD)
    a.label("rl_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["rel"])

    # ---- the container's slot 0 (cont, pad, vel) / slot 1 (cont, pad) / slot 7 (cont)
    a.label("c_s4on")                                                               # -> r0 = 1 while our split is on; clobbers r1-r3
    E(push_list, [], lr=True); E(bl, "c_s4st"); E(ldrb_imm, 0, 0, O_ON); E(pop_list, [], pc=True)
    a.label("c_s4pad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_s4on"); E(cmp_imm, 0, 0); bc("cp_prev", "eq")
    E(cmp_imm, 5, 31); bc("cp_x", "hi")
    E(bl, "c_s4st"); E(ldr_imm, 1, 0, O_MASK); E(movs_imm, 2, 1); E(lsls_reg, 2, 5); E(orrs_reg, 1, 2); E(str_imm, 1, 0, O_MASK)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_s4view"); E(cmp_imm, 0, 0); bc("cp_x", "eq")
    E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0); E(movs_imm, 1, 15); E(raw, h(0x4029)); E(adds_imm8, 1, 16); E(mov_reg, 2, 6); E(blx_reg, 3)
    a.label("cp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("cp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["cpad"])
    a.label("c_s4crel")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_s4on"); E(cmp_imm, 0, 0); E(b_cond, "cr_prev", "eq")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, "c_s4prel")
    E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("cr_prev"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["crel"])
    a.label("c_s4led")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["cled"]); E(mov_reg, 5, 0)
    E(bl, "c_s4on"); E(cmp_imm, 0, 0); bc("cl_x", "eq")
    E(movs_imm, 6, 0)
    a.label("cl_t")
    E(lsls_imm, 1, 6, 4); E(mov_reg, 0, 4); E(bl, "c_s4view"); E(cmp_imm, 0, 0); bc("cl_n", "eq")   # (pad 0 / 16 picks the half's track)
    E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 28); E(blx_reg, 3)                      # its keyboard window
    E(lsls_imm, 1, 6, 5); E(adds_reg, 1, 1, 5); E(movs_imm, 7, 0)
    a.label("cl_c")
    E(raw, h(0x5BC2)); E(raw, h(0x53CA))                                           # ldrh r2,[r0,r7]; strh r2,[r1,r7]
    E(adds_imm8, 7, 2); E(cmp_imm, 7, 32); E(b_cond, "cl_c", "lo")
    a.label("cl_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); bc("cl_t", "lo")
    a.label("cl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the heads of the button press / release and of the container's slots 0 / 1 / 7."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), rel=MP.bw_target(img, SV.BTN_REL, BASE),
                cpad=u(SV.CT_VT) & ~1, crel=u(SV.CT_VT + 4) & ~1, cled=u(SV.CT_VT + 28) & ~1)
    code, labels = arm_code(base_addr, prev, int(report["sc14"]["labels"]["c_gst"], 16))
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or base_addr < 0x08018800          # in the hole: hole.add moves it back
    assert SPR + 16 <= 0x2004FE00 - 0x1000
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = b_w(SV.BTN, labels["c_s4btn"])
    img[SV.BTN_REL - BASE:SV.BTN_REL - BASE + 4] = b_w(SV.BTN_REL, labels["c_s4rel"])
    struct.pack_into("<I", img, SV.CT_VT - BASE, labels["c_s4pad"] | 1)
    struct.pack_into("<I", img, SV.CT_VT + 4 - BASE, labels["c_s4crel"] | 1)
    struct.pack_into("<I", img, SV.CT_VT + 28 - BASE, labels["c_s4led"] | 1)
    return labels, code, prev
