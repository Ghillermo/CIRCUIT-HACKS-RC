"""SC45.8 (the user, 2026-10-21: «Durante el modo split, aguantar un pad de track abre sus controles en la capa de potes»): in split4's split
keyboard, a track button held = the eight knobs (and their LEDs) are that track's.

The track views' container (vtable 0x0805A62C) gives the knobs to the knob handler of the current track, [cont + 0x148 + 4 t] (0x08043A20; slot 4 =
the knob (obj, knob, delta), slot 7 = its LED buffer, 16 B copied to the frame + 0x44 by the container's LED slot 0x08043C42).  With the split on:
  * a track button (Synth 1 / 2, MIDI 1 / 2, Drum 1-4: ids 0..7) is no longer passed on when pressed (split4 ended the split there): it is held;
    a note track also gets split4's held bit and "first" (another note track pressed meanwhile = a new pair, split4's way);
  * while it is held, the container's knob slot -> that track's knob handler, and its LED slot copies that handler's 16 B of knob LEDs;
  * let go: a tap (under 400 ms, no knob turned) = the press passed on then (split4 ends the split and the stock selects the track, as before);
    else nothing (the split stays).
Shift + a track button: as before.  State: modmx.MXR + 0x2A0 (12 B, RAM, with a signature).  In the hole.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsls_reg,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, subs_reg)
import srcview as SV  # noqa: E402
import split4 as S4  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402

SKR = MX.MXR + 0x2A0                  # + 0 signature, + 4 the track held (0xFF none), + 5 a knob turned, + 8 the press time
SIG = 0x314E4B53                      # "SKN1"
O_TRK, O_USED, O_T0 = 4, 5, 8
N_IDS = 8                             # Synth 1, Synth 2, MIDI 1, MIDI 2, Drum 1-4
HAL_TICK = 0x2000081C                 # 1 ms
TAP_MS = 400
HANDLERS = 0x148                      # the container's knob handlers, one per track
LED_GET = 0x0804758C                  # (obj) -> its LED buffer (slot 7)
KNOB_LEDS = 0x44                      # the frame's knob LEDs (entries 34..41)
INV = SV.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev, s4on):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_k{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_skst() -> r0 = SKR, set up at the first use; clobbers r1, r2
    a.label("c_skst")
    imm32(0, SKR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "ks_i", "ne"); E(raw, h(0x4770))
    a.label("ks_i")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, O_TRK); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_USED); E(raw, h(0x4770))

    # ---- c_skobj(r0 = cont) -> r0 = the knob handler of the track held (0: none, or the split off); clobbers r1-r3
    a.label("c_skobj")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, s4on); E(cmp_imm, 0, 0); E(b_cond, "ko_x", "eq")
    E(bl, "c_skst"); E(ldrb_imm, 1, 0, O_TRK); E(movs_imm, 0, 0); E(cmp_imm, 1, N_IDS); E(b_cond, "ko_x", "hs")
    E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 1, 4); E(movs_imm, 2, HANDLERS >> 2); E(lsls_imm, 2, 2, 2); E(adds_reg, 1, 1, 2); E(ldr_imm, 0, 1, 0)
    a.label("ko_x"); E(pop_list, [4], pc=True)

    # ---- c_skbtn (ctrl, id): the head of the button chain
    a.label("c_skbtn")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, N_IDS - 1); bc("kb_prev", "hi")
    E(bl, s4on); E(cmp_imm, 0, 0); bc("kb_prev", "eq")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, SV.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("kb_prev", "ne")   # Shift: as before
    E(bl, "c_skst"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 6, O_TRK); E(cmp_imm, 0, 0xFF); E(b_cond, "kb_new", "eq")
    # one held already: another note track with a note track held = a new pair (split4); anything else ignored
    E(cmp_imm, 0, S4.N_TRK - 1); bc("kb_x", "hi"); E(cmp_imm, 5, S4.N_TRK - 1); bc("kb_x", "hi")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, O_TRK); E(b, "kb_prev")
    a.label("kb_new")
    E(strb_imm, 5, 6, O_TRK); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_USED)
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 6, O_T0)
    E(cmp_imm, 5, S4.N_TRK - 1); bc("kb_x", "hi")
    E(bl, "c_s4stp"); E(ldrb_imm, 1, 0, S4.O_HELD); E(movs_imm, 2, 1); E(lsls_reg, 2, 5); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, S4.O_HELD)
    E(strb_imm, 5, 0, S4.O_FIRST)
    a.label("kb_x"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("kb_prev"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])

    # ---- c_s4stp() -> r0 = split4's state (its signature already set: the split is on)
    a.label("c_s4stp")
    imm32(0, S4.SPR); E(raw, h(0x4770))

    # ---- c_skrel (ctrl, id): the head of the button release
    a.label("c_skrel")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_skst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, O_TRK); E(ldr_sp, 1, 4); E(cmp_reg, 0, 1); bc("kr_prev", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, O_TRK)
    E(ldrb_imm, 0, 4, O_USED); E(cmp_imm, 0, 0); bc("kr_prev", "ne")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(ldr_imm, 1, 4, O_T0); E(subs_reg, 0, 0, 1)
    imm32(1, TAP_MS); E(cmp_reg, 0, 1); bc("kr_prev", "hs")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, prev["btn"])                           # a tap: the press passed on now (split4 ends the split)
    a.label("kr_prev"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["rel"])

    # ---- the container's slot 4 (cont, knob, delta): the track held's knob handler
    a.label("c_skknob")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, "c_skobj"); E(cmp_imm, 0, 0); E(b_cond, "kk_prev", "eq"); E(mov_reg, 4, 0)
    E(bl, "c_skst"); E(movs_imm, 1, 1); E(strb_imm, 1, 0, O_USED)
    E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0x10); E(blx_reg, 3)
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("kk_prev"); E(pop_list, [0, 1, 2, 4]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, prev["knob"])      # pop {lr}

    # ---- the container's slot 7 (cont) -> the frame: the knob LEDs of the track held
    a.label("c_skled")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["led"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_skobj"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")
    E(bl, LED_GET); E(movs_imm, 2, 0); E(movs_imm, 3, KNOB_LEDS); E(adds_reg, 3, 3, 5)
    a.label("kl_c")
    E(raw, h(0x5A81)); E(raw, h(0x5299))                                           # ldrh r1, [r0, r2]; strh r1, [r3, r2]
    E(adds_imm8, 2, 2); E(cmp_imm, 2, 16); E(b_cond, "kl_c", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the button press / release and of the container's slots 4 / 7."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), rel=MP.bw_target(img, SV.BTN_REL, BASE),
                knob=u(SV.CT_VT + 16) & ~1, led=u(SV.CT_VT + 28) & ~1)
    code, labels = arm_code(base_addr, prev, int(report["split4"]["labels"]["c_s4on"], 16))
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert SKR + 12 <= MX.MXR + 0x300
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = b_w(SV.BTN, labels["c_skbtn"])
    img[SV.BTN_REL - BASE:SV.BTN_REL - BASE + 4] = b_w(SV.BTN_REL, labels["c_skrel"])
    struct.pack_into("<I", img, SV.CT_VT + 16 - BASE, labels["c_skknob"] | 1)
    struct.pack_into("<I", img, SV.CT_VT + 28 - BASE, labels["c_skled"] | 1)
    return labels, code, prev
