"""SC18.2 LEDs (ARM only): FX view button colours and the new drum knobs lit.

FX view (controller + 0x44 active):
  Octave UP (delay sends) = PEACH, Octave DOWN (reverb sends) = CREAM, Duplicate (reset) = LIGHT_BLUE,
  "1-16 / 17-32" (master resonance step) = LIGHT_GREEN.
  How: both callers of the stock LED task 0x08034196(ctrl, out) (0x08033B46, 0x0803415A) call c_ledtask instead, which
  runs the task and then, with the FX view active, overwrites the panel LEDs of those buttons in `out`.
  Panel LED numbers, found in emulation by pressing the buttons (table 0x08059438 = (source, element) per LED):
    48 = "1-16 / 17-32" (button 16; track sub-view element 0), 51 / 52 = Octave DOWN / UP (active view elements 32 / 33),
    55 = Clear (id 23), 56 = Duplicate (id 24) (both from the Clear / Duplicate object ctrl+0x20).
Drum knobs: the drum macro handlers (vtable 0x0805AADC, one per drum, controller-container + 0x158 + 4d) give the knob
  LEDs through slot 7 (generic 0x08047592 = [[obj+4]]); stock leaves K1 / K3 / K5 / K7 at 0 (off) and K2 / K4 / K6 / K8
  at the dynamic codes 0xE1 + 4d...  c_mhleds puts the drum's bright colour (palette index 5 + d) on K1 / K3 / K5 / K7.

LED codes are Novation's own (the RGB table is not in the image): the colours below are provisional picks from the
stock palette 0x08056464 and are the constants to change after looking at them on the hardware.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, bl, cmp_imm, cmp_reg, ldr_imm, mov_reg, movs_imm, pop_list, push_list, strh_imm,  # noqa: E402
                   adds_imm8, movw, strh_reg, b)

LED_TASK = 0x08034196
LED_TASK_CALLS = (0x08033B46, 0x0803415A)
CTRL_VIEW, CTRL_FX = 0x6C, 0x44
LED_PAIR, LED_OCT_DN, LED_OCT_UP, LED_DUP = 48, 51, 52, 56
PALETTE = 0x08056464                  # palette index -> LED code (halfwords)
# provisional colours (LED codes): delay / reverb / reset / resonance
PEACH = 0x45                          # palette index 5 (Drum 1 bright)
CREAM = 0x49                          # palette index 7 (Drum 3 bright)
LIGHT_BLUE = 0x09                     # palette index 3 (MIDI 1 bright)
LIGHT_GREEN = 0x20                    # palette index 2 (Synth 2 bright)
MH_VT = 0x0805AADC
MH_SLOT7 = MH_VT + 0x1C
GENERIC_LEDS = 0x08047592             # ldr r0,[r0,#4]; ldr r0,[r0]; bx lr
NEW_KNOBS = (0, 2, 4, 6)              # K1, K3, K5, K7


def drum_codes(img):
    """bright LED code of drums 1..4 (palette indices 5..8)"""
    import ct_fw
    return [struct.unpack_from("<H", img, PALETTE - ct_fw.APP_BASE + 2 * (5 + d))[0] for d in range(4)]


def arm_code(base, c_mh, dcodes):
    a = Asm(base)
    # ---- c_ledtask(ctrl, out): stock task, then the FX view button colours
    a.label("c_ledtask")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(bl, LED_TASK)
    a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, CTRL_FX)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "lt_x", "eq")
    a.emit(cmp_reg, 0, 1); a.emit(b_cond, "lt_x", "ne")
    for led, code in ((LED_OCT_UP, PEACH), (LED_OCT_DN, CREAM), (LED_DUP, LIGHT_BLUE), (LED_PAIR, LIGHT_GREEN)):
        a.emit(movw, 0, code); a.emit(movw, 1, 2 * led)
        a.emit(strh_reg, 0, 5, 1)
    a.label("lt_x")
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_mhleds(obj): slot 7 of the drum macro handlers: stock buffer + K1 / K3 / K5 / K7 in the drum colour
    a.label("c_mhleds")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(ldr_imm, 5, 4, 4); a.emit(ldr_imm, 5, 5, 0)                           # r5 = [[obj+4]] (as GENERIC_LEDS)
    a.emit(movs_imm, 6, 0)
    a.label("ml_loop")
    a.emit(mov_reg, 0, 6); a.emit(bl, c_mh)                                      # r0 = handler of drum r6 (clobbers r1, r2)
    a.emit(cmp_reg, 0, 4); a.emit(b_cond, "ml_hit", "eq")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 4); a.emit(b_cond, "ml_loop", "lo")
    a.emit(b, "ml_x")
    a.label("ml_hit")
    for d in range(4):                                                           # r1 = code of drum r6
        a.emit(movs_imm, 1, dcodes[d]); a.emit(cmp_imm, 6, d); a.emit(b_cond, "ml_set", "eq")
    a.label("ml_set")
    for k in NEW_KNOBS:
        a.emit(strh_imm, 1, 5, 2 * k)
    a.label("ml_x")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and patch the two LED task calls and slot 7 of the drum macro handler vtable."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    for c in LED_TASK_CALLS:
        assert text(c, 4) == f"bl #{LED_TASK:#x}", text(c, 4)
    assert struct.unpack_from("<I", img, MH_SLOT7 - BASE)[0] == GENERIC_LEDS | 1
    c_mh = int(report["sc18"]["labels"]["c_mh"], 16)
    dcodes = drum_codes(img)
    code, labels = arm_code(base_addr, c_mh, dcodes)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for c in LED_TASK_CALLS:
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_ledtask"])
    struct.pack_into("<I", img, MH_SLOT7 - BASE, labels["c_mhleds"] | 1)
    return labels, code, dcodes
