"""S564D (diagnostic, 2026-11-15): catch the writer of the one-word corruptions behind the 5.63 / 5.64 crashes with the Cortex-M7's DWT.

The black boxes: Beta 5.63, the listener vtable word of Drum 4's velocity-bar object 0x20043610 changed 0x0805ADA8 -> 0x0805AD60; Beta 5.64 (twice),
the word 0x20042988 (the listener vtable of Synth 1's Preset view, right after MIDI 2's 16-pad probability-view LED array) changed 0x0805ACC8 ->
0x000F0009 (MIDI 1's blue 0x09 / dim 0x0F as two LED halfwords: pads 21-22 of a painter writing a 16-pad buffer as if it had 32).  The heap layout
is the same at every boot (the records' addresses match the emulation's), so: a head of the LED task arms, once, DWT comparators 0 / 1 on those two
words (MASK 2: the word; FUNCTION 6: write), with DEMCR.TRCENA | MON_EN; the first write raises the DebugMonitor exception (vector 12, the
stock's default handler before), whose handler hands the stacked frame to the black box's fault capture (blackbox.c_bbfltc: the frame's registers,
the writer's PC / LR, the ring of the last gestures, the view), then disarms both comparators and returns: the device goes on (the crash may follow;
the record is frozen first, so it keeps the writer).  The app (Caja negra…) shows it as a fault record of vector 12.
RAM 0x2004FAF0 (8 B): + 0 the LED head's LR, + 4 armed.  Code in dspz's first gap (dspz.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b, b_cond, bl, cmp_imm, h, ldr_imm, ldrb_imm, movs_imm, movt, movw, mov_reg, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

DW = 0x2004FAF0
WATCH = (0x20042988, 0x20043610)
DEMCR, DFSR, DWT_LAR, DWT_COMP0 = 0xE000EDFC, 0xE000ED30, 0xE0001FB0, 0xE0001020
VEC_DEBUGMON = 0x08010000 + 4 * 12
assert DW + 8 <= 0x2004FC00


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, v >> 16)
    # ---- c_dwled (the LED task's calls: ctrl, frame): the chain (nothing on the stack), then arm the comparators once
    a.label("c_dwled")
    imm32(2, DW); E(raw, h(0xF8C2) + h(0xE000))                                  # str.w lr, [r2]
    E(bl, prev["ledtask"])
    imm32(2, DW); E(ldrb_imm, 0, 2, 4); E(cmp_imm, 0, 0); E(b_cond, "dw_x", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 2, 4)
    imm32(0, DEMCR); E(ldr_imm, 1, 0, 0); imm32(2, 0x01010000); E(orrs_reg, 1, 2); E(str_imm, 1, 0, 0)   # TRCENA | MON_EN
    imm32(0, DWT_LAR); imm32(1, 0xC5ACCE55); E(str_imm, 1, 0, 0)
    imm32(0, DWT_COMP0)
    for i, w in enumerate(WATCH):                                                # COMPn, MASKn = 2, FUNCTIONn = 6 (write); 16 B a comparator
        E(movs_imm, 1, 0); E(str_imm, 1, 0, 16 * i + 8)
        imm32(1, w); E(str_imm, 1, 0, 16 * i)
        E(movs_imm, 1, 2); E(str_imm, 1, 0, 16 * i + 4)
        E(movs_imm, 1, 6); E(str_imm, 1, 0, 16 * i + 8)
    a.label("dw_x")
    imm32(2, DW); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))                       # bx r2: the LR from RAM
    # ---- c_dwmon (vector 12, DebugMonitor: a DWT match): the black box's fault capture with the stacked frame, then the comparators off
    a.label("c_dwmon")
    E(mov_reg, 1, 14); E(movs_imm, 0, 4); E(raw, h(0x4201)); E(b_cond, "dm_p", "ne")        # tst r1, r0: EXC_RETURN bit 2
    E(raw, h(0xF3EF) + h(0x8208)); E(b, "dm_g")                                  # mrs r2, msp
    a.label("dm_p"); E(raw, h(0xF3EF) + h(0x8209))                               # mrs r2, psp
    a.label("dm_g")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(movs_imm, 0, 12); E(bl, L["c_bbfltc"])                                     # (r0 = the vector, r1 = EXC_RETURN, r2 = the frame)
    imm32(0, DWT_COMP0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 24)
    imm32(0, DFSR); E(movs_imm, 1, 4); E(str_imm, 1, 0, 0)                      # DFSR.DWTTRAP cleared
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); the two LED task calls -> c_dwled, vector 12 -> c_dwmon."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    L = dict(c_bbfltc=int(report["blackbox"]["labels"]["c_bbfltc"], 16))
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert struct.unpack_from("<I", img, VEC_DEBUGMON - BASE)[0] == 0x0805998B
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_dwled"])
    struct.pack_into("<I", img, VEC_DEBUGMON - BASE, labels["c_dwmon"] | 1)
    report["dwtwatch"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              ram=hex(DW), watch=[hex(w) for w in WATCH])
    return labels, code, prev
