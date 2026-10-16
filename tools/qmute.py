"""SC43.4 (the user, 2026-10-16: «Regardless of cue mode, shift + channel selection pad sets cue reproduction / stop and makes it blink (again to
cancel); the pattern … will start / stop on the next bar»): in the Mixer view, Shift + one of the eight track pads (row 1) queues that track's mute
toggle for the next bar.

The stock (read in the firmware, emulated): the Mixer view (0x200447D4, vtable 0x0805A668), slot 0 = 0x08046626(view, pad): pads 0-7 toggle the
track's mute (the store [[view + 0x68] + [view + 0x60] x pad], parameter 0, then 0x080353C0); it does not look at Shift.  The global tick (24 a
quarter note) is parameter 0 of [0x20038EC0 + 0x90].

Ours:
  * the Mixer view's slot 0 (in front of the chain; not on its Master FX page): Shift + pads 1-8 = that track's bit in a pending mask (again = cancel);
  * the LED task: stopped, the pending toggles happen at once (the next bar is the first one); playing, when the bar of (tick + 1) changes (96 ticks
    a bar; one tick early, so that the downbeat already plays or is already silent); each through the stock's own handler; the pending pads blink
    (dark every other 256 ms) while the Mixer view is on the screen;
  * RAM in the record's tail + 954 (the mask) / + 955 (the last bar, 0xFF stopped), reset by each load (in front of the others at the end of the
    stock's «apply session»).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, ands_reg)
from build_sc14 import udiv  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402

MIX_VT, MIX_VIEW, MIX_PAD = 0x0805A668, 0x200447D4, 0x08046626
MGR = 0x20040B10
ENG, TRANSPORT, PARAM_GET, HAL_TICK = 0x20038EC0, 0x20011034, 0x0803542C, 0x2000081C
SESSION_OBJ, TAIL, O_PEND, O_BAR = 0x2003D71C, 0x27024, 954, 955
TICKS_BAR, LEAD = 96, 1


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_qmt() -> r0 = the record's tail + 954, or 0; clobbers r1
    a.label("c_qmt")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "qt_x", "eq")
    imm32(1, TAIL + O_PEND); E(adds_reg, 0, 0, 1)
    a.label("qt_x"); E(raw, h(0x4770))

    # ---- c_qmpad (the Mixer view's slot 0: view, pad, velocity): Shift + pads 1-8 = queue / cancel that track's toggle
    a.label("c_qmpad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, 8); E(b_cond, "qp_f", "hs")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "qp_f", "eq")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "qp_f", "ne")                                       # Master FX: its pads
    E(bl, "c_qmt"); E(cmp_imm, 0, 0); E(b_cond, "qp_f", "eq"); E(mov_reg, 4, 0)
    E(ldr_sp, 1, 4); E(movs_imm, 0, 1); E(raw, h(0x4088)); E(ldrb_imm, 1, 4, 0); E(raw, h(0x4041)); E(strb_imm, 1, 4, 0)   # lsls r0, r1; eors r1, r0
    E(raw, h(0xB003)); E(pop_list, [4], pc=True)                                                         # add sp, #12
    a.label("qp_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["pad"])

    # ---- c_qmdo(r0 = the block): the pending toggles through the stock's handler; clobbers r0-r3
    a.label("c_qmdo")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, 0); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)
    E(movs_imm, 5, 0)
    a.label("qd_l"); E(mov_reg, 0, 4); E(raw, h(0x40E8)); E(lsls_imm, 0, 0, 31); E(b_cond, "qd_n", "pl")   # lsrs r0, r5
    imm32(0, MIX_VIEW); E(mov_reg, 1, 5); E(movs_imm, 2, 127); E(bl, MIX_PAD)
    a.label("qd_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "qd_l", "lo")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_qmledtask (the LED task calls: ctrl, frame): the chain; the bar; the blinking pads
    a.label("c_qmledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_qmt"); E(cmp_imm, 0, 0); E(b_cond, "ql_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "ql_p", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, 1)                                                             # stopped: at once
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "ql_l", "eq"); E(mov_reg, 0, 4); E(bl, "c_qmdo"); E(b, "ql_l")
    a.label("ql_p")
    imm32(0, ENG + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, LEAD); E(movs_imm, 1, TICKS_BAR); E(raw, udiv(0, 0, 1)); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1)   # r0 = the bar (low byte)
    E(ldrb_imm, 1, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "ql_l", "eq"); E(strb_imm, 0, 4, 1)
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "ql_l", "eq"); E(mov_reg, 0, 4); E(bl, "c_qmdo")
    a.label("ql_l")                                                                                        # the Mixer on the screen: the pending pads blink
    E(ldrb_imm, 6, 4, 0); E(cmp_imm, 6, 0); E(b_cond, "ql_x", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x6C); imm32(1, MIX_VIEW); E(cmp_reg, 0, 1); E(b_cond, "ql_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "ql_x", "ne")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(lsls_imm, 0, 0, 31); E(b_cond, "ql_x", "pl")
    E(movs_imm, 7, 0)
    a.label("ql_b"); E(mov_reg, 0, 6); E(raw, h(0x40F8)); E(lsls_imm, 0, 0, 31); E(b_cond, "ql_bn", "pl")    # lsrs r0, r7
    E(lsls_imm, 1, 7, 1); E(movs_imm, 0, 0); E(raw, h(0x5268))                                             # strh r0, [r5, r1]
    a.label("ql_bn"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ql_b", "lo")
    a.label("ql_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_qmload (the end of the stock's «apply session», in front of the others): nothing pending from what a file holds
    a.label("c_qmload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, "c_qmt"); E(cmp_imm, 0, 0); E(b_cond, "qo_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 1)
    a.label("qo_x"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; slot 0 of the Mixer view, the LED task calls, the end of «apply session»."""
    import ct_fw
    import struct
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gact=int(report["sc17"]["labels"]["c_gact"], 16))
    prev = dict(pad=u(MIX_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), load=MP.bw_target(img, P19.LOAD_END, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MIX_VT - BASE, labels["c_qmpad"] | 1)
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_qmload"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_qmledtask"])
    return labels, code, prev
