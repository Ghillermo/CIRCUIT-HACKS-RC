"""FX view keys for SC17.5 (ARM only).

In the FX view (FX button, view object ctrl+0x44):
  Octave UP   (button 20): knobs = delay sends   (stock page of the FX view: store [fx+0x20] p0 = 1)
  Octave DOWN (button 19): knobs = reverb sends  (p0 = 0)
  button 16  ("1-16 / 17-32"): reset:
      * delay and reverb send of every track = 0  (project parameters 0x20 idx 0-7 reverb, 11-18 delay)
      * master filter position = 64 (centre, off)  (project parameter 0x21 idx 0; the resonance is left alone)
      * Master FX off: held / latched pads of the SC14 Gater / Auto-Filter and of the SC17 Master FX view cleared
  Everywhere else the buttons are untouched (stock).  Nothing is saved by the keys themselves.

How: the stock button handler 0x08033320 (frame {r3, r4, r5, lr}; r4 = controller, r5 = button id) dispatches by
`tbh`.  The first 4 bytes of the cases 19 / 20 / 16-17 (`ldr r0,[r4,#0x6c]` + `ldr r1,[r4,#X]`: active view,
then a view to compare with) are replaced with `b.w` to the hooks below, which test "active view == FX view",
do their job and leave through the stock epilogue 0x08033706, or else run the two displaced instructions and
return to the stock case.  Parameters are set through the same listener the MIDI input uses for project parameters
(0x08034D92(this+4, type, idx, value), this = [[[ctx]+0x10]]), so stores, UI and DSP follow as with a CC message.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list,  # noqa: E402
                   strb_imm, adds_imm8)

CTX = 0x200069E4
CTRL_VIEW, CTRL_FX = 0x6C, 0x44            # controller: active view, FX view object
BTN_DOWN, BTN_UP, BTN_PAIR = 0x08033620, 0x08033660, 0x080336D0
BTN_DOWN_BACK, BTN_UP_BACK, BTN_PAIR_BACK = 0x08033624, 0x08033664, 0x080336D4
BTN_EXIT = 0x08033706                      # pop {r0, r4, r5, pc}
STOCK_CMP = {BTN_DOWN: (0x2C, "ldr r0, [r4, #0x6c]|ldr r1, [r4, #0x2c]"), BTN_UP: (0x2C, "ldr r0, [r4, #0x6c]|ldr r1, [r4, #0x2c]"),
             BTN_PAIR: (0x34, "ldr r0, [r4, #0x6c]|ldr r1, [r4, #0x34]")}
RESET_BTN = 16                             # id 16 of the 16/17 pair (SC17.5: reset; SC17.6: resonance step)
# SC19: ids 16 / 17 are RECORD / PLAY (LEDs 48 / 49), not "1-16 / 17-32"; the page button is id 21 (case 0x080336F8: command 0x15 to the
# object ctrl+0x24; LED 53, between Octave UP and Tempo / Swing).  With PAGE_BTN the resonance step moves there and 16 / 17 stay stock.
PAGE_BTN = False
BTN_PAGE, BTN_PAGE_BACK = 0x080336F8, 0x080336FC
# SC17.6 (CLEAR_RESET = True): the reset moves to the Duplicate button, id 24 (cases 23 / 24 share one stock handler: the
# Clear / Duplicate modifiers of the object ctrl+0x20; store bit 0 = Clear (id 23) is the one the knob pages read for
# "Clear + knob = reset to default", so Clear stays as it is and Duplicate, unused in the FX view, takes the reset);
# button 16 steps the master filter resonance by RES_STEP (after the maximum: 0).
CLEAR_RESET = False                        # (flag name kept: "the reset is on a modifier button of the Clear / Duplicate pair")
BTN_CLEAR, BTN_CLEAR_BACK, CLEAR_BTN = 0x08033612, 0x08033616, 24
RES_STEP = 32
GETTER = 0x08036192                        # project parameter value (type, idx)
PARAM_SET = 0x08034D92                     # project parameter listener (this + 4, type, idx, value)
STORE_PTR, STORE_COMMIT = 0x080354FA, 0x080353C0
FX_PAGE = 0x20                             # FX view: store [fx + 0x20], p0: 1 = delay sends, else reverb sends
# SC14 state (c_gst): held, latch, gater, auto-filter
S14_CLEAR = (4, 5, 6, 7)
# SC17 Master FX block (c_gfst): held, latch
GFX_CLEAR = (5, 6)
SEND_REVERB = range(0, 8)
SEND_DELAY = range(11, 19)


TRIMPG = False                                   # SC49.3 (use_trimpg)


def use_trimpg():
    """SC49.3 (flash for the drums' extra lane, phase 2): fxres (SC44.4) puts id 21's stock instructions back; the resonance step on it (c_pgbtn,
    c_res) runs from nowhere: not emitted, the hook not written."""
    global TRIMPG
    TRIMPG = True


def hooks():
    """(address, label, expected stock disassembly of the 4 replaced bytes) of the b.w hooks in the button handler."""
    h = [(BTN_DOWN, "c_octdn", STOCK_CMP[BTN_DOWN][1]), (BTN_UP, "c_octup", STOCK_CMP[BTN_UP][1])]
    if PAGE_BTN:
        if not TRIMPG: h.append((BTN_PAGE, "c_pgbtn", "ldr r0, [r4, #0x24]|movs r1, #0x15"))
    else: h.append((BTN_PAIR, "c_pair", STOCK_CMP[BTN_PAIR][1]))
    if CLEAR_RESET: h.append((BTN_CLEAR, "c_dup", "ldr r0, [r4, #0x20]|mov r1, r5"))
    return h


def arm_code(base, c_gst, c_gfst, c_shift=None):
    a = Asm(base)
    # ---- c_page(r0 = FX view, r1 = value): [fx+0x20] p0 = value, committed (as stock 0x08045794..0x080457B0)
    a.label("c_page")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 4, 1)
    a.emit(ldr_imm, 0, 5, FX_PAGE); a.emit(movs_imm, 1, 0); a.emit(bl, STORE_PTR)
    a.emit(strb_imm, 4, 0, 0)
    a.emit(ldr_imm, 0, 5, FX_PAGE); a.emit(bl, STORE_COMMIT)
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_reset: sends, master filter, Master FX
    a.label("c_reset")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x10); a.emit(ldr_imm, 0, 0, 0)
    a.emit(adds_imm8, 0, 4); a.emit(mov_reg, 4, 0)                             # r4 = target
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 0x21); a.emit(movs_imm, 2, 0); a.emit(movs_imm, 3, 64)   # master filter: centre
    a.emit(bl, PARAM_SET)
    a.emit(movs_imm, 5, 0)
    a.label("rs_l")
    a.emit(cmp_imm, 5, SEND_REVERB.stop); a.emit(b_cond, "rs_do", "lo")
    a.emit(cmp_imm, 5, SEND_DELAY.start); a.emit(b_cond, "rs_next", "lo")
    a.label("rs_do")
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 0x20); a.emit(mov_reg, 2, 5); a.emit(movs_imm, 3, 0)
    a.emit(bl, PARAM_SET)
    a.label("rs_next")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, SEND_DELAY.stop); a.emit(b_cond, "rs_l", "lo")
    a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "rs_g", "eq")     # SC14 Gater / Auto-Filter
    a.emit(movs_imm, 1, 0)
    for off in S14_CLEAR: a.emit(strb_imm, 1, 0, off)
    a.label("rs_g")
    a.emit(bl, c_gfst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "rs_out", "eq")  # SC17 Master FX pads
    a.emit(movs_imm, 1, 0)
    for off in GFX_CLEAR: a.emit(strb_imm, 1, 0, off)
    a.label("rs_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- hooks (entered by b.w from the stock cases; r4 = controller, r5 = button id)
    for name, val, back, off in (("c_octdn", 0, BTN_DOWN_BACK, 0x2C), ("c_octup", 1, BTN_UP_BACK, 0x2C)):
        a.label(name)
        a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, CTRL_FX); a.emit(cmp_reg, 0, 1)
        a.emit(b_cond, name + "_s", "ne")
        a.emit(movs_imm, 1, val); a.emit(bl, "c_page")
        a.emit(b_w, BTN_EXIT)
        a.label(name + "_s")
        a.emit(ldr_imm, 1, 4, off); a.emit(b_w, back)                         # displaced: r0 = view already loaded

    if PAGE_BTN:
        if not TRIMPG:
            assert CLEAR_RESET, "the page button steps the resonance (CLEAR_RESET builds)"
            a.label("c_pgbtn")                                                      # id 21 in the FX view: resonance step
            a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, CTRL_FX); a.emit(cmp_reg, 0, 1)
            a.emit(b_cond, "pg_s", "ne")
            a.emit(bl, "c_res"); a.emit(b_w, BTN_EXIT)
            a.label("pg_s")
            a.emit(ldr_imm, 0, 4, 0x24); a.emit(movs_imm, 1, 0x15); a.emit(b_w, BTN_PAGE_BACK)   # displaced instructions
    else:
        a.label("c_pair")
        a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, CTRL_FX); a.emit(cmp_reg, 0, 1)
        a.emit(b_cond, "pr_s", "ne"); a.emit(cmp_imm, 5, RESET_BTN); a.emit(b_cond, "pr_s", "ne")
        a.emit(bl, "c_res" if CLEAR_RESET else "c_reset"); a.emit(b_w, BTN_EXIT)
        a.label("pr_s")
        a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, 0x34); a.emit(b_w, BTN_PAIR_BACK)

    if CLEAR_RESET:
        if not (TRIMPG and PAGE_BTN):
            # ---- c_res: master filter resonance (project parameter 0x21 idx 1) += RES_STEP, clamped to 127; at 127 -> 0
            a.label("c_res")
            a.emit(push_list, [4], lr=True)
            a.emit(movs_imm, 0, 0x21); a.emit(movs_imm, 1, 1); a.emit(bl, GETTER)
            a.emit(cmp_imm, 0, 127); a.emit(b_cond, "rz", "hs")
            a.emit(adds_imm8, 0, RES_STEP); a.emit(cmp_imm, 0, 127); a.emit(b_cond, "rk", "ls")
            a.emit(movs_imm, 0, 127); a.emit(b, "rk")
            a.label("rz"); a.emit(movs_imm, 0, 0)
            a.label("rk"); a.emit(mov_reg, 3, 0)
            a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
            a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x10); a.emit(ldr_imm, 0, 0, 0)
            a.emit(adds_imm8, 0, 4); a.emit(movs_imm, 1, 0x21); a.emit(movs_imm, 2, 1)
            a.emit(bl, PARAM_SET)
            a.emit(pop_list, [4], pc=True)
        # ---- c_dup: Duplicate (id 24) pressed in the FX view without Shift -> reset; the stock handler always runs after
        a.label("c_dup")
        a.emit(ldr_imm, 0, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 4, CTRL_FX); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "cl_s", "ne")
        a.emit(cmp_imm, 5, CLEAR_BTN); a.emit(b_cond, "cl_s", "ne")
        a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cl_s", "ne")
        a.emit(bl, "c_reset")
        a.label("cl_s")
        a.emit(ldr_imm, 0, 4, 0x20); a.emit(mov_reg, 1, 5); a.emit(b_w, BTN_CLEAR_BACK)    # displaced instructions
    return a.assemble()

