"""S579D (diagnostic, 2026-11-15): catch the writer of the one-byte corruption behind the Beta 5.63 crash («pattern chain is broken»).

The record showed the listener vtable word of Drum 4's velocity-bar object (class C, [CONT + 0xB0 + 4 d] = 0x2004353c / 0x20043580 / 0x200435c4 /
0x20043608 on the device's heap, vtable 0x0805AD7C at + 0, listener vtable 0x0805ADA8 at + 8) changed from 0x0805ADA8 to 0x0805AD60 (the low byte
0xA8 -> 0x60); nothing in emulation reproduces it.  This head of the LED task (both calls, in front of the chain) checks the two words of the four
objects every frame (~90 Hz) and, at the first difference, freezes the black box (state ST_FROZEN | ST_MANUAL | 0x80; the ring then holds the
last 16 gestures before the write, the view they were made in, and the times) so the gesture that writes there can be read with the app
(Caja negra…).  The chain runs first with nothing of ours on the stack (the LR in RAM, as the SC56.7 rule); the check uses r4-r7 after it.
RAM: 0x2004FAF0 (8 B): + 0 the LR, + 4 fired (1), + 5 the drum + 1 (free: after patrev's 0x2004FAE0..0x2004FAE7, below 0x2004FC00).
Code in dspz's first gap (dspz.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b, b_cond, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, movs_imm, movt, movw, pop_list, push_list, raw, strb_imm  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import blackbox as BB  # noqa: E402

CW = 0x2004FAF0
CONT = 0x20040DB8                                             # the track views' container; + 0xB0 + 4 d = the drums' velocity bars (class C)
VT_C, VT_CL = 0x0805AD7C, 0x0805ADA8
STATE = BB.ST_FROZEN | BB.ST_MANUAL | 0x80
assert CW >= 0x2004FAE8 and CW + 8 <= 0x2004FC00


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, v >> 16)
    # ---- c_cwled (the LED task's calls: ctrl, frame): the chain (nothing on the stack), then the four velocity bars' two vtable words
    a.label("c_cwled")
    imm32(2, CW); E(raw, h(0xF8C2) + h(0xE000))                                  # str.w lr, [r2]
    E(bl, prev["ledtask"])
    E(push_list, [4, 5, 6, 7])
    imm32(4, CW); E(ldrb_imm, 0, 4, 4); E(cmp_imm, 0, 0); E(b_cond, "cw_x", "ne")        # fired already
    imm32(0, BB.BB); E(ldrb_imm, 0, 0, BB.O.ST); E(lsls_imm, 0, 0, 31); E(b_cond, "cw_x", "mi")   # the record is frozen already
    imm32(4, CONT + 0xB0); imm32(5, VT_C); imm32(6, VT_CL); E(movs_imm, 7, 0)
    a.label("cw_l")
    E(lsls_imm, 0, 7, 2); E(raw, h(0x5820))                                      # ldr r0, [r4, r0]: the object
    E(ldr_imm, 1, 0, 0); E(cmp_reg, 1, 5); E(b_cond, "cw_f", "ne")
    E(ldr_imm, 1, 0, 8); E(cmp_reg, 1, 6); E(b_cond, "cw_f", "ne")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "cw_l", "lo")
    E(b, "cw_x")
    a.label("cw_f")                                                               # a word differs: note the drum, freeze the black box once
    imm32(0, CW); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 4); E(adds_imm8, 7, 1); E(strb_imm, 7, 0, 5)
    E(movs_imm, 0, STATE); E(bl, L["c_bbfrz"])
    a.label("cw_x")
    E(pop_list, [4, 5, 6, 7]); imm32(2, CW); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))      # bx r2: the LR from RAM
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); the two LED task calls -> c_cwled."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    L = dict(c_bbfrz=int(report["blackbox"]["labels"]["c_bbfrz"], 16))
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_cwled"])
    report["cwatch"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()}, ram=hex(CW))
    return labels, code, prev
