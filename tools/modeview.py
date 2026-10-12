"""Synth source mode view for SC17.7 (ARM only): the modes move from "Shift in the synth Preset view" to the Shift + Scales view.

Shift + Scales opens the stock view 7 (object ctrl+0x34 = 0x20044128, vtable 0x0805A6A4): a 15-pad selector in columns 3-6
(it only works while the transport is stopped: the button case checks the transport store).  Its pads / LEDs in columns 1-2 are
free, so the 7 modes of the synth source go there:

    pad index  0   1   8   9   16  17  24      (columns 1-2 of the 4 rows)
    mode       0 Noise  1 In 1  2 In 2  3 In 1 inv  4 In 2 inv  5 Delay  6 Reverb

Pressing one sets the mode of the synth of the currently selected track (Synth 1 / Synth 2; other tracks: ignored); the LEDs show the
mode of that synth (bright = selected).  Every other pad goes to the stock handler of the view.  The synth Preset view is back to stock.

  slot 0 (press)  0x08044006 -> c_mpad        slot 7 (LEDs) 0x08047592 (generic getter) -> c_mleds
  Preset view vtable (0x0805AC9C) slots 0 / 7: restored to the stock handlers (SC15's c_spad / c_sleds are no longer used)
The mode bytes and the H9 hook (X:$3A01 / X:$3A02) are SC15's, unchanged.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list,  # noqa: E402
                   raw, h, adds_reg, strb_imm)

CTX = 0x200069E4
VIEW7_VT = 0x0805A6A4
VIEW7_PRESS, VIEW7_LEDS = 0x08044006, 0x08047592             # stock slot 0 handler / slot 7 (generic LED buffer getter)
TRACK_FN = 0x0805011E                                        # container: current track 0-7
MARK_DIRTY = 0x0803BDCC
S_MODE = 18                                                  # SC14 state: mode[2]
PADS = (0, 1, 8, 9, 16, 17, 24)                              # pad index of mode 0..6
COLORS = ((0x32, 0x38), (0x20, 0x26))                        # (bright, dim): Synth 1 / Synth 2
N_MODES = 7


def strh_w(rt, rn, imm12): return h(0xF8A0 | rn) + h(rt << 12 | imm12)


def arm_code(base, c_gst):
    a = Asm(base)
    # ---- c_mtrack: r0 = synth of the selected track (0 / 1), or 0xFF; clobbers r1-r3
    a.label("c_mtrack")
    a.emit(push_list, [4], lr=True)
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40); a.emit(ldr_imm, 0, 0, 0x2C)     # container
    a.emit(bl, TRACK_FN)
    a.emit(cmp_imm, 0, 1); a.emit(b_cond, "mt_ok", "ls"); a.emit(movs_imm, 0, 0xFF)
    a.label("mt_ok"); a.emit(pop_list, [4], pc=True)

    # ---- c_mpad (view, pad, vel)
    a.label("c_mpad")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    for m, pad in enumerate(PADS):
        a.emit(cmp_imm, 5, pad); a.emit(b_cond, f"mp_m{m}", "eq")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)                    # not a mode pad: the stock handler
    a.emit(raw, h(0xE8BD) + h(0x40F0)); a.emit(b_w, VIEW7_PRESS)                           # pop.w {r4-r7, lr}
    for m in range(N_MODES):
        a.label(f"mp_m{m}"); a.emit(movs_imm, 6, m); a.emit(b, "mp_go")
    a.label("mp_go")
    a.emit(bl, "c_mtrack"); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "mp_out", "eq"); a.emit(mov_reg, 7, 0)
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "mp_out", "eq")
    a.emit(adds_reg, 0, 0, 7); a.emit(strb_imm, 6, 0, S_MODE)
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 48); a.emit(bl, MARK_DIRTY)             # resend the Audio In group (H9)
    a.label("mp_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mleds (view) -> LED buffer: stock buffer + the 7 mode pads
    a.label("c_mleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, VIEW7_LEDS); a.emit(mov_reg, 4, 0)                                          # r4 = stock buffer
    a.emit(bl, "c_mtrack"); a.emit(mov_reg, 7, 0)
    a.emit(movs_imm, 6, 0xFF)                                                              # r6 = mode (0xFF: none)
    a.emit(cmp_imm, 7, 0xFF); a.emit(b_cond, "ml_p", "eq")
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ml_p", "eq")
    a.emit(adds_reg, 0, 0, 7); a.emit(ldrb_imm, 6, 0, S_MODE)
    a.label("ml_p")
    for m, pad in enumerate(PADS):
        a.emit(movs_imm, 1, 0)                                                             # off when the track is not a synth
        a.emit(cmp_imm, 7, 0xFF); a.emit(b_cond, f"ml_s{m}", "eq")
        a.emit(cmp_imm, 7, 0); a.emit(b_cond, f"ml_t{m}", "ne")
        a.emit(movs_imm, 1, COLORS[0][1]); a.emit(cmp_imm, 6, m); a.emit(b_cond, f"ml_s{m}", "ne"); a.emit(movs_imm, 1, COLORS[0][0]); a.emit(b, f"ml_s{m}")
        a.label(f"ml_t{m}")
        a.emit(movs_imm, 1, COLORS[1][1]); a.emit(cmp_imm, 6, m); a.emit(b_cond, f"ml_s{m}", "ne"); a.emit(movs_imm, 1, COLORS[1][0])
        a.label(f"ml_s{m}"); a.emit(raw, strh_w(1, 4, 2 * pad))
    a.emit(mov_reg, 0, 4); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()
