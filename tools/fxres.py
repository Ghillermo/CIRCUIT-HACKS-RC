"""SC44.4 (the user, 2026-10-19: «cambia master reso a shift+octave up/down, saltos de 16 en 16», «sin ciclar en max/min»): in the FX view the
master filter resonance moves to Shift + Octave UP / DOWN, +16 / -16, stopping at 127 / 0; the "1-16 / 17-32" button (id 21) is stock again.

Before (SC19 .. SC44.3, fxkeys.PAGE_BTN): id 21 in the FX view stepped the resonance by 32 and wrapped to 0 after 127; leds18 lit its LED (53)
green there.  Octave UP / DOWN pick the delay / reverb sends page (fxkeys c_octup / c_octdn, the b.w at the cases 0x08033660 / 0x08033620).

Ours:
  * the two Octave cases: with the FX view active and Shift held, the resonance (project parameter 0x21 idx 1, the getter 0x08036192 and the
    listener 0x08034D92, as fxkeys) +16 / -16 clamped to 0..127, out through the stock epilogue; else the previous hook (the sends page);
    with Shift the stock lets ids 19 / 20 through;
  * id 21: its 4 stock bytes back (ldr r0, [r4, #0x24]; movs r1, #0x15);
  * leds18's c_ledtask: the green of LED 53 off (its movw / movw / strh = nops); the LED task chain: with the FX view and Shift, Octave
    UP / DOWN yellow (0x2D, the Shift convention).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, strh_reg, subs_imm8, raw)
import fxkeys as K  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import leds18 as L18  # noqa: E402

STEP, YELLOW = 16, 0x2D
NOP10 = bytes.fromhex("00bf") * 5


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit

    # ---- c_rsstep(r0 = 1 up / 0 down): the resonance +-STEP, clamped; clobbers r0-r3
    a.label("c_rsstep")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0)
    E(movs_imm, 0, 0x21); E(movs_imm, 1, 1); E(bl, K.GETTER); E(mov_reg, 3, 0)
    E(cmp_imm, 4, 0); E(b_cond, "rq_dn", "eq")
    E(cmp_imm, 3, 127); E(b_cond, "rq_x", "hs")                                       # at the top: nothing
    E(adds_imm8, 3, STEP); E(cmp_imm, 3, 127); E(b_cond, "rq_set", "ls"); E(movs_imm, 3, 127); E(b, "rq_set")
    a.label("rq_dn")
    E(cmp_imm, 3, 0); E(b_cond, "rq_x", "eq")                                         # at the bottom: nothing
    E(cmp_imm, 3, STEP); E(b_cond, "rq_lo", "ls"); E(subs_imm8, 3, STEP); E(b, "rq_set")
    a.label("rq_lo"); E(movs_imm, 3, 0)
    a.label("rq_set")
    E(movw, 0, K.CTX & 0xFFFF); E(movt, 0, K.CTX >> 16)
    E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(movs_imm, 1, 0x21); E(movs_imm, 2, 1)
    E(bl, K.PARAM_SET)
    a.label("rq_x"); E(pop_list, [4], pc=True)

    # ---- the Octave cases (b.w from the stock; r4 = controller, r5 = id)
    for name, up in (("c_rsdn", 0), ("c_rsup", 1)):
        a.label(name)
        E(ldr_imm, 0, 4, K.CTRL_VIEW); E(ldr_imm, 1, 4, K.CTRL_FX); E(cmp_reg, 0, 1); E(b_cond, name + "_f", "ne")
        E(push_list, [2, 3]); E(bl, L["c_shift"]); E(mov_reg, 1, 0); E(pop_list, [2, 3])
        E(cmp_imm, 1, 0); E(b_cond, name + "_f", "eq")
        E(movs_imm, 0, up); E(bl, "c_rsstep"); E(b_w, K.BTN_EXIT)
        a.label(name + "_f"); E(b_w, prev["up" if up else "dn"])

    # ---- c_rsledtask (the LED task calls: ctrl, frame): the chain; FX view + Shift: Octave UP / DOWN yellow
    a.label("c_rsledtask")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(ldr_imm, 0, 4, K.CTRL_VIEW); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    E(ldr_imm, 1, 4, K.CTRL_FX); E(cmp_reg, 0, 1); E(b_cond, "rl_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    for led in (L18.LED_OCT_DN, L18.LED_OCT_UP):
        E(movs_imm, 0, YELLOW); E(movw, 1, 2 * led); E(strh_reg, 0, 5, 1)
    a.label("rl_x"); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the two Octave cases, id 21 back to stock, LED 53 not green, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    fk = {k: int(v, 16) for k, v in report["fxkeys"]["labels"].items()}
    assert MP.bw_target(img, K.BTN_PAGE, BASE) == fk["c_pgbtn"], "id 21 is not fxkeys' resonance step"
    lt = int(report["leds18"]["labels"]["c_ledtask"], 16)
    green = (bytes(movw(0, L18.LIGHT_GREEN)) + bytes(movw(1, 2 * 53)) + bytes(strh_reg(0, 5, 1)))
    seg = bytes(img[lt - BASE:lt - BASE + 0x40])
    assert seg.count(green) == 1, "LED 53's green not found in c_ledtask"
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    prev = dict(dn=MP.bw_target(img, K.BTN_DOWN, BASE), up=MP.bw_target(img, K.BTN_UP, BASE),
                ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[K.BTN_DOWN - BASE:K.BTN_DOWN - BASE + 4] = b_w(K.BTN_DOWN, labels["c_rsdn"])
    img[K.BTN_UP - BASE:K.BTN_UP - BASE + 4] = b_w(K.BTN_UP, labels["c_rsup"])
    img[K.BTN_PAGE - BASE:K.BTN_PAGE - BASE + 4] = bytes(ldr_imm(0, 4, 0x24)) + bytes(movs_imm(1, 0x15))
    o = lt - BASE + seg.index(green)
    img[o:o + len(green)] = NOP10
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_rsledtask"])
    return labels, code, prev
