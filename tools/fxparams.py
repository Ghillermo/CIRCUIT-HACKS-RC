"""SC21.2: Shift + knob in the FX view = the reverb / delay PARAMETERS (ARM only).

The FX view (object ctrl+0x44) has two sub-views of one class (vtable 0x0805AF3C): [fx+0xC] = the delay sends, [fx+0x10] = the reverb sends (the knobs are the sends of Synth 1, Synth 2,
Drums 1-4, Audio 1, Audio 2); the page shown is chosen with Octave up / down (SC17.5).  With Shift held (the stock does nothing useful there) the 8 knobs of the page shown are:
  reverb page  K1 type (0-5: Chamber, Small Room, Large Room, Small Hall, Large Hall, Great Hall)   K2 decay (0-127)   K3 damping (0-127)           K4-K8: nothing
  delay page   K1 time (0-127)   K2 time sync (0-35)   K3 feedback (0-127)   K4 width (0-127)   K5 left-right ratio (0-12)   K6 slew rate (0-127)    K7-K8: nothing
(the Programmer's Reference Guide v3, "Project Control", MIDI channel 16, NRPN 1:18..1:20 and 1:6..1:11; the project parameters of type 0x20 are the indices 8..10 and 19..24 in that order,
ranges as in the firmware's NRPN table).  The value is set through the listener the MIDI input uses (0x08034D92(this + 4, 0x20, index, value)), so the store, the UI, the DSP update and the project
saving are the stock ones.  The stepped parameters (max < 127) move one step per click, the others by the click's delta, clamped.
LEDs: while Shift is held the knob LEDs of the page shown show the values as brightness (peach = delay, cream = reverb, the colours of the FX view's Octave LEDs; the unused knobs dark); on release
(or when the view is shown again without Shift) both sub-views are repainted by the stock routine 0x0805095A.  The sub-view buffer is persistent (its entries 16..23 are the knobs), so the repaint
is remembered in bit 4 of the byte 179 of the Master FX block.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, strb_w, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, strh_imm, adds_reg, subs_reg, ands_reg, orrs_reg, muls, strh_reg, ldrb_reg, tst_reg)

CTX = 0x200069E4
SUB_VT = 0x0805AF3C
SLOT4, SLOT7 = SUB_VT + 0x10, SUB_VT + 0x1C
STOCK_KNOB, STOCK_LEDS, REPAINT = 0x08050830, 0x08047592, 0x0805095A
GETTER, PARAM_SET = 0x08036192, 0x08034D92
CTRL_VIEW, CTRL_FX = 0x6C, 0x44
FLAGS_BYTE, F_FXLED = 179, 0x10
COL_DELAY, COL_REVERB = 0x6B, 0x2A
# (project index, maximum, brightness multiplier) per knob; delay first (6), then reverb (3)
DELAY = ((19, 127, 1), (20, 35, 3), (21, 127, 1), (22, 127, 1), (23, 12, 10), (24, 127, 1))
REVERB = ((8, 5, 25), (9, 127, 1), (10, 127, 1))
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L):
    """L: c_shift, c_gfst (addresses)."""
    a = Asm(base)
    zc = [0]
    def bc(target, cond):
        zc[0] += 1; n = f"_x{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)
    a.label("t_fx")                                                               # 4 bytes per knob (index, max, multiplier, 0): delay K1..K6, reverb K1..K3
    for idx, mx, mul in DELAY + REVERB: a.emit(raw, bytes([idx, mx, mul, 0]))

    # ---- c_fxsub(r0 = sub-view) -> r0 = 1 (delay page) / 2 (reverb page) when the FX view is the active view and r0 is one of its two sub-views, else 0; clobbers r1-r3
    a.label("c_fxsub")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(movw, 1, CTX & 0xFFFF); a.emit(movt, 1, CTX >> 16); a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); bc("fs_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); bc("fs_no", "eq")        # the controller
    a.emit(ldr_imm, 2, 1, CTRL_VIEW); a.emit(ldr_imm, 3, 1, CTRL_FX); a.emit(cmp_reg, 2, 3); bc("fs_no", "ne")
    a.emit(ldr_imm, 0, 3, 0x0C); a.emit(cmp_reg, 4, 0); a.emit(b_cond, "fs_d", "eq")
    a.emit(ldr_imm, 0, 3, 0x10); a.emit(cmp_reg, 4, 0); a.emit(b_cond, "fs_r", "eq")
    a.label("fs_no"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)
    a.label("fs_d"); a.emit(movs_imm, 0, 1); a.emit(pop_list, [4], pc=True)
    a.label("fs_r"); a.emit(movs_imm, 0, 2); a.emit(pop_list, [4], pc=True)

    # ---- c_fxent(r0 = page 1 / 2, r1 = knob) -> r0 = address of the table entry, or 0 when the knob has no parameter on that page; clobbers r2
    a.label("c_fxent")
    a.emit(cmp_imm, 0, 1); a.emit(b_cond, "fe_r", "ne")
    a.emit(cmp_imm, 1, len(DELAY)); a.emit(b_cond, "fe_none", "hs")
    a.emit(movs_imm, 0, 0); a.emit(b, "fe_go")
    a.label("fe_r")
    a.emit(cmp_imm, 1, len(REVERB)); a.emit(b_cond, "fe_none", "hs")
    a.emit(movs_imm, 0, 4 * len(DELAY))
    a.label("fe_go")
    a.emit(lsls_imm, 2, 1, 2); a.emit(adds_reg, 0, 0, 2)
    a.emit(movw, 2, base & 0xFFFF); a.emit(movt, 2, base >> 16); a.emit(adds_reg, 0, 0, 2)
    a.emit(raw, h(0x4770))                                                        # bx lr
    a.label("fe_none"); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))

    # ---- c_fxknob(sub, knob, delta): slot 4 of the sub-views
    a.label("c_fxknob")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("fk_stock", "eq")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_fxsub"); a.emit(cmp_imm, 0, 0); bc("fk_stock", "eq")
    a.emit(mov_reg, 1, 5); a.emit(bl, "c_fxent"); a.emit(cmp_imm, 0, 0); bc("fk_done", "eq")      # a knob without a parameter: swallowed
    a.emit(mov_reg, 7, 0)                                                         # r7 = the table entry
    a.emit(ldrb_imm, 1, 7, 0); a.emit(movs_imm, 0, 0x20); a.emit(bl, GETTER)      # r0 = the current value
    a.emit(ldrb_imm, 2, 7, 1)                                                     # r2 = max
    a.emit(cmp_imm, 2, 127); a.emit(b_cond, "fk_cont", "hs")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "fk_up", "gt"); a.emit(movs_imm, 6, 0); a.emit(subs_imm8, 6, 1); a.emit(b, "fk_cont")      # stepped: one click = +-1
    a.label("fk_up"); a.emit(movs_imm, 6, 1)
    a.label("fk_cont")
    a.emit(mov_reg, 3, 0); a.emit(adds_reg, 0, 0, 6)                              # r0 = new = old + delta
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fk_p", "ge"); a.emit(movs_imm, 0, 0)
    a.label("fk_p"); a.emit(cmp_reg, 0, 2); a.emit(b_cond, "fk_c", "le"); a.emit(mov_reg, 0, 2)
    a.label("fk_c"); a.emit(cmp_reg, 0, 3); bc("fk_done", "eq")                    # unchanged: nothing to send
    a.emit(mov_reg, 3, 0)
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x10); a.emit(ldr_imm, 0, 0, 0)
    a.emit(adds_imm8, 0, 4); a.emit(movs_imm, 1, 0x20); a.emit(ldrb_imm, 2, 7, 0)
    a.emit(bl, PARAM_SET)
    a.label("fk_done")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("fk_stock")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, STOCK_KNOB)

    # ---- c_fxleds(sub-view): slot 7 of the sub-views = the stock LEDs; with Shift held in the FX view the knob entries (16..23) show the parameters
    a.label("c_fxleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, STOCK_LEDS); a.emit(mov_reg, 5, 0)          # r5 = the buffer
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); bc("fl_out", "eq")
    a.emit(mov_reg, 7, 0)                                                         # r7 = the Master FX block (the flag byte)
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_fxsub"); a.emit(mov_reg, 6, 0)           # r6 = page (0 = not the FX view)
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("fl_noshift", "eq")
    a.emit(cmp_imm, 6, 0); bc("fl_out", "eq")
    # Shift held on a page: paint
    a.emit(ldrb_w, 0, 7, FLAGS_BYTE); a.emit(movs_imm, 1, F_FXLED); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 7, FLAGS_BYTE)
    a.emit(movs_imm, 4, 0)                                                        # r4 = knob
    a.label("fl_k")
    a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 4); a.emit(bl, "c_fxent"); a.emit(cmp_imm, 0, 0); bc("fl_dark", "eq")
    a.emit(mov_reg, 3, 0)                                                         # r3 = entry
    a.emit(ldrb_imm, 1, 3, 0); a.emit(movs_imm, 0, 0x20); a.emit(push_list, [3])
    a.emit(bl, GETTER); a.emit(pop_list, [3])                                     # r0 = value
    a.emit(ldrb_imm, 1, 3, 2); a.emit(muls, 0, 1)                                 # brightness = value * multiplier (0..127)
    a.emit(cmp_imm, 0, 127); a.emit(b_cond, "fl_b", "ls"); a.emit(movs_imm, 0, 127)
    a.label("fl_b")
    a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8)                            # (brightness + 2) << 8 | colour (the converter hook of persist19.KNOB_LEVELS splits it)
    a.emit(movs_imm, 1, COL_DELAY); a.emit(cmp_imm, 6, 1); a.emit(b_cond, "fl_c", "eq"); a.emit(movs_imm, 1, COL_REVERB)
    a.label("fl_c"); a.emit(orrs_reg, 0, 1); a.emit(b, "fl_w")
    a.label("fl_dark"); a.emit(movs_imm, 0, 0)
    a.label("fl_w")
    a.emit(lsls_imm, 1, 4, 1); a.emit(adds_reg, 1, 1, 5); a.emit(strh_imm, 0, 1, 32)       # entry 16 + knob
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, 8); bc("fl_k", "lo")
    a.emit(b, "fl_out")
    a.label("fl_noshift")                                                         # Shift not held: if we painted, give the stock LEDs back (both sub-views)
    a.emit(ldrb_w, 0, 7, FLAGS_BYTE); a.emit(movs_imm, 1, F_FXLED); a.emit(tst_reg, 0, 1); bc("fl_out", "eq")
    a.emit(cmp_imm, 6, 0); bc("fl_out", "eq")                                     # painted, but not looking at the FX view now: repaint when it is shown
    a.emit(ldrb_w, 0, 7, FLAGS_BYTE); a.emit(movs_imm, 1, F_FXLED); a.emit(raw, h(0x4388)); a.emit(strb_w, 0, 7, FLAGS_BYTE)   # bics r0, r1
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40)
    a.emit(ldr_imm, 0, 0, CTRL_FX); a.emit(mov_reg, 7, 0)                          # r7 = the FX view
    a.emit(ldr_imm, 0, 7, 0x0C); a.emit(bl, REPAINT)
    a.emit(ldr_imm, 0, 7, 0x10); a.emit(bl, REPAINT)
    a.label("fl_out")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and re-point slots 4 / 7 of the FX sub-view class."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    w = lambda addr: struct.unpack_from("<I", img, addr - BASE)[0]
    assert w(SLOT4) == STOCK_KNOB | 1 and w(SLOT7) == STOCK_LEDS | 1, (hex(w(SLOT4)), hex(w(SLOT7)))
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16))
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SLOT4 - BASE, labels["c_fxknob"] | 1)
    struct.pack_into("<I", img, SLOT7 - BASE, labels["c_fxleds"] | 1)
    return labels, code
