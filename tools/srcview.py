"""SC19.1: the synth source switch (noise / audio input 1 / 2 / inverted) gets its own view, opened by pressing a Synth button a second time.

Why: SC15..SC19 changed the source with Shift + pads 25-29 of the synth Preset view, but a pad press there is a stock gesture
(choosing the patch that is already chosen resets it) and Shift + Synth 1 / 2 never reaches the button handler (the Shift mask of
0x08033320 only lets ids 9-13, 15-17, 19, 20, 22-26 and 27 through; ids 0-8, 14 and 21 are dropped).

How it works (Synth 1 = id 0, Synth 2 = id 1):
  * c_bentry replaces the first 4 bytes of the stock button handler 0x08033320 (push {r3, r4, r5, lr}; mov r4, r0), runs them itself
    and falls back into the stock code at 0x08033326, except in two cases:
      - the source view is open and any button but Shift is pressed: the view is closed (flag cleared), then the stock handler runs
        (Synth 1 goes back to the track view, Preset to the normal patch list, ...);
      - Synth s is pressed while its own track view is the current one (byte [ctrl + 0x152] = 9 s + 1: track s, sub-mode 1; the table
        at 0x0805877C is index = 9 * track + sub-mode, sub-mode 0 = Preset view) and Shift is not held: that second press is turned into a
        tap on Preset (stock press + release of id 8, which opens the Preset view of the selected track) and the flag is set.
  * The flag is bit 2 of the SC14 state byte +20 (SC15 uses bits 0 / 1 there for "pads painted"); nothing is saved.  The byte is written by two tasks
    (the UI task in c_bentry, the LED task in c_xleds): every write goes through c_rmw, a read-modify-write with interrupts off.
  * The synth Preset view (vtable 0x0805AC9C) keeps its two hooked slots, now with the flag instead of Shift: c_xpad (slot 0, pad press)
    and c_xleds (slot 7, LEDs).  While the flag is set every pad press is swallowed except pads 25-29 (index 24..28) = noise, input 1,
    input 2, input 1 inverted, input 2 inverted, which set the mode of the synth being shown (then the Audio In group is marked dirty so
    SC15's H9 hook sends it to the DSP); the LEDs show those five pads (selected bright, the rest dim, in the synth's colours) and
    every other pad dark.  When the flag goes away the stock view is repainted once.
  * Without the flag both slots are stock: Shift + pads 25-29 of the Preset view do nothing special any more.

SC38.9 (SPLIT, use_split(); the user, 2026-10-11: «pulsar synth1 y synth2 a la vez abre una vista de pads para tocar donde la fila superior es synth 1 y
la inferior synth 2»): a split keyboard over the track views' container (vtable 0x0805A62C, [ctrl + 0x2C]):
  * the press / release of Synth 1 / 2 set / clear bits 3 / 4 of the same state byte (F_HELD << id; the release hook c_brel takes the first 4 bytes of the
    stock release 0x0803381A, the same prologue as the press); a Synth button pressed while the other one is held (no Shift) sets bit 5 (F_SPLIT) and
    is swallowed; underneath, a tap on Note (id 9, through the hooked entry before the flag is set: it also closes the source view that a
    second press of the first synth may have opened) leaves the first synth's Note view; the pads still held in the stock's way are released first (the container's mask
    [cont + 0x190], its own release 0x080435F0);
  * with F_SPLIT the container's slots 0 / 1 / 7 (pad, release, LEDs) are ours: pads 1-16 (index 0..15) = the keyboard pads of Synth 1's Note view
    (its object 0x08043A84(cont, 0, 1), class 0x0805A064: pad index + 16, the bottom half of its own view), pads 17-32 = Synth 2's (the same index):
    each half plays its synth with its own scale, octave and velocity, through its own Note view (proved in emulation: the hidden Synth 2 view plays
    Synth 2's note); the pressed pads are kept in the container's own mask, so a release goes to the view that played the note;
  * the LEDs: the container's buffer (rebuilt by the stock at every call) with pads 0..15 = Synth 1's keyboard window (its slot 7: the 16 keys of the
    bottom half) and 16..31 = Synth 2's;
  * any track / view button (ids 0..15) ends the split (the notes still held are released first); a single Synth button goes straight to the stock (not
    taken for the "second press" of the source view); the other buttons (Play, Record, Octave, Shift, Clear, ...) leave it on.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, mov_reg, movs_imm,  # noqa: E402
                   orrs_reg, bics_reg, tst_reg, strb_imm, strh_reg, strh_imm, subs_imm8, adds_imm8, adds_reg, pop_list, push_list, raw, h)

BTN = 0x08033320                      # stock button handler (ctrl, id); frame push {r3, r4, r5, lr}
BTN_BODY = 0x08033326                 # after push / mov r4, r0 / mov r5, r1
BTN_TXT = "push {r3, r4, r5, lr}|mov r4, r0|mov r5, r1"
BTN_REL = 0x0803381A                  # stock button release (ctrl, id)
PARAM_GET = 0x0803542C
MARK_DIRTY = 0x0803BDCC
SP_VT = 0x0805AC9C                    # synth Preset view vtable
SLOT_PAD, SLOT_LEDS = 0, 7
S_CUR = 0x152                         # controller: 9 * track + sub-mode (0 = Preset, 1 = track view)
ID_PRESET, ID_SHIFT = 8, 27
ID_NOTE = 9
F_SRC = 4                             # bit 2 of SC14 state byte +20
SPLIT = False                         # SC38.9: Synth 1 + Synth 2 = a split keyboard (see the docstring; use_split)
F_HELD, F_SPLIT = 0x08, 0x20          # bits 3 / 4 = Synth 1 / 2 held, bit 5 = the split keyboard is on
CT_VT = 0x0805A62C                    # the track views' container: slot 0 pad, 1 release, 7 LEDs
CT_PAD, CT_REL, CT_LED = 0x080435B1, 0x080435F1, 0x08043C43
NV_GET = 0x08043A84                   # (cont, track, sub-mode) -> the sub-view (sub-mode 1 = the track's Note view)
HELD_MASK = 0x190                     # the container's pads held (u32)
BTN_REL_TXT = "push {r3, r4, r5, lr}|mov r4, r0|mov r5, r1"


def use_split():
    """SC38.9: Synth 1 + Synth 2 pressed together = a split keyboard (pads 1-16 Synth 1, 17-32 Synth 2)."""
    global SPLIT
    SPLIT = True
KEEPPLAY = False                      # SC43.7 (use_keepplay)
ID_KEEP = (16, 17)                    # (KEEPPLAY) Record, Play


def use_keepplay():
    """SC43.7 (the user, 2026-10-17: «en sinte 1 y 2 step-drummer, pulsar play o record envía a la vista Preset»): Record and Play (ids 16 / 17)
    keep the source view open (and the step-drummer view inside it), as Shift does; they do not change the view in the stock."""
    global KEEPPLAY
    KEEPPLAY = True


METER = False                         # SC20D: pad rows 2 and 3 (bytes 16..47 of the LED buffer) belong to the DSP meter tick (tools/meter20.py)
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K):
    """L: addresses of c_gst / c_synth; K: constants from build_sc15 (S_MODE, S_PAINT, PAD0, N_MODES, COLORS, SP_PRESS, SP_LEDS, SP_REPAINT)."""
    a = Asm(base)
    zc = [0]
    S_MODE, S_PAINT, PAD0, NM = K["S_MODE"], K["S_PAINT"], K["PAD0"], K["N_MODES"]

    def bc(target, cond):                              # conditional branch, +-2KB
        zc[0] += 1; n = f"_c{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    # ---- c_rmw (r0 = address, r1 = bits to set, r2 = bits to clear) -> r3 = new byte.  The UI task (c_bentry) and the LED task (c_xleds) share
    #      the byte at S_PAINT: the read-modify-write runs with interrupts off (PRIMASK saved and restored, as the RTOS does around its critical sections)
    a.label("c_rmw")
    a.emit(push_list, [4], lr=True)
    a.emit(raw, bytes([0xEF, 0xF3, 0x10, 0x84]))                               # mrs r4, primask
    a.emit(raw, bytes([0x72, 0xB6]))                                           # cpsid i
    a.emit(ldrb_imm, 3, 0, 0); a.emit(orrs_reg, 3, 1); a.emit(bics_reg, 3, 2); a.emit(strb_imm, 3, 0, 0)
    a.emit(raw, bytes([0x84, 0xF3, 0x10, 0x88]))                               # msr primask, r4
    a.emit(pop_list, [4], pc=True)

    # ---- c_bentry (ctrl = r0, id = r1): see the module docstring.  Scratch r0-r3 only (frame of the stock handler)
    a.label("c_bentry")
    a.emit(push_list, [3, 4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    if SPLIT:                                                                  # the split keyboard first: 1 = swallowed, 2 = straight to the stock
        a.emit(bl, "c_spbtn"); a.emit(cmp_imm, 0, 1); bc("be_done", "eq"); a.emit(cmp_imm, 0, 2); bc("be_stock", "eq")
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("be_stock", "eq")
    a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc("be_closed", "eq")
    a.emit(cmp_imm, 5, ID_SHIFT); bc("be_stock", "eq")                         # Shift keeps the view
    if KEEPPLAY:
        for k in ID_KEEP: a.emit(cmp_imm, 5, k); bc("be_stock", "eq")          # so do Record and Play
    a.emit(adds_imm8, 0, S_PAINT); a.emit(movs_imm, 1, 0); a.emit(bl, "c_rmw"); a.emit(b, "be_stock")      # clear the flag (r2 = F_SRC)
    a.label("be_closed")                                                       # view closed: a second press of a Synth button?
    a.emit(cmp_imm, 5, 1); bc("be_stock", "hi")
    a.emit(ldrb_w, 1, 4, S_CUR)
    a.emit(lsls_imm, 2, 5, 3); a.emit(adds_reg, 2, 2, 5); a.emit(adds_imm8, 2, 1)   # r2 = 9 * id + 1
    a.emit(cmp_reg, 1, 2); bc("be_stock", "ne")
    a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(cmp_imm, 0, 0); bc("be_stock", "ne")                                # Shift held: stock (it drops the press)
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, ID_PRESET); a.emit(bl, BTN)     # tap on Preset: press ...
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, ID_PRESET); a.emit(bl, BTN_REL)  # ... and release
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("be_done", "eq")
    a.emit(adds_imm8, 0, S_PAINT); a.emit(movs_imm, 1, F_SRC); a.emit(movs_imm, 2, 0); a.emit(bl, "c_rmw")   # set the flag
    a.label("be_done")
    a.emit(pop_list, [3, 4, 5], pc=True)
    a.label("be_stock")
    a.emit(b_w, BTN_BODY)

    if SPLIT:
        from thumb import lsls_reg, blx_reg, ldrh_imm, subs_reg, str_imm, lsrs_imm
        def mask_addr(rd, cont):                                               # rd = &[cont + HELD_MASK]
            a.emit(movs_imm, rd, HELD_MASK >> 4); a.emit(lsls_imm, rd, rd, 4); a.emit(adds_reg, rd, rd, cont)
        def note_view(cont, track_reg):                                        # r0 = the track's Note view (clobbers r0-r3)
            a.emit(mov_reg, 0, cont); a.emit(mov_reg, 1, track_reg); a.emit(movs_imm, 2, 1); a.emit(bl, NV_GET)
        # ---- c_splon -> r0 = 1 while the split keyboard is on
        a.label("c_splon")
        a.emit(push_list, [], lr=True)
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "so_x", "eq")
        a.emit(ldrb_imm, 0, 0, S_PAINT); a.emit(lsrs_imm, 0, 0, 5); a.emit(movs_imm, 1, 1); a.emit(raw, h(0x4008))   # ands r0, r1
        a.label("so_x"); a.emit(pop_list, [], pc=True)
        # ---- c_spbtn (ctrl, id) -> r0 = 0 (go on), 1 (swallowed), 2 (straight to the stock)
        a.label("c_spbtn")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("sb_0", "eq"); a.emit(mov_reg, 6, 0); a.emit(adds_imm8, 6, S_PAINT)   # r6 = &state byte
        a.emit(cmp_imm, 5, 1); bc("sb_other", "hi")
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, F_HELD); a.emit(lsls_reg, 1, 5); a.emit(movs_imm, 2, 0); a.emit(bl, "c_rmw")   # held
        a.emit(movs_imm, 2, 1); a.emit(subs_reg, 2, 2, 5); a.emit(movs_imm, 1, F_HELD); a.emit(lsls_reg, 1, 2)                     # the other one
        a.emit(tst_reg, 3, 1); bc("sb_single", "eq")
        a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); bc("sb_0", "ne")                                                     # Shift held: the stock (it drops the press)
        a.emit(ldrb_imm, 3, 6, 0); a.emit(movs_imm, 1, F_SPLIT); a.emit(tst_reg, 3, 1); bc("sb_1", "ne")   # already on
        a.emit(ldr_imm, 7, 4, 0x2C); mask_addr(5, 7)                                              # r7 = cont, r5 = &mask
        a.emit(movs_imm, 6, 0)                                                                     # the pads held the stock's way: released
        a.label("sb_rl")
        a.emit(ldr_imm, 0, 5, 0)
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 6); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sb_rn", "eq")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 6); a.emit(bl, CT_REL & ~1)
        a.label("sb_rn")
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 32); bc("sb_rl", "lo")
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, ID_NOTE); a.emit(bl, BTN)       # the first synth's Note view underneath (closes the source view) ...
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, ID_NOTE); a.emit(bl, BTN_REL)
        a.emit(bl, L["c_gst"]); a.emit(adds_imm8, 0, S_PAINT); a.emit(movs_imm, 1, F_SPLIT); a.emit(movs_imm, 2, F_SRC); a.emit(bl, "c_rmw")   # ... then the split on
        a.label("sb_1"); a.emit(movs_imm, 0, 1); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("sb_single")                                                   # one Synth button: ends the split, then the stock (no "second press")
        a.emit(movs_imm, 1, F_SPLIT); a.emit(tst_reg, 3, 1); bc("sb_0", "eq")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_spoff"); a.emit(movs_imm, 0, 2); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("sb_other")
        a.emit(ldrb_imm, 3, 6, 0); a.emit(movs_imm, 1, F_SPLIT); a.emit(tst_reg, 3, 1); bc("sb_0", "eq")
        a.emit(cmp_imm, 5, 15); bc("sb_0", "hi")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_spoff")
        a.label("sb_0"); a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_spoff (ctrl): the notes still held on the split keyboard released, the flag cleared
        a.label("c_spoff")
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(ldr_imm, 4, 0, 0x2C); a.emit(movs_imm, 5, 0)
        a.label("sf_l")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sprel")
        a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 32); bc("sf_l", "lo")
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sf_x", "eq")
        a.emit(adds_imm8, 0, S_PAINT); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, F_SPLIT); a.emit(bl, "c_rmw")
        a.label("sf_x"); a.emit(pop_list, [4, 5, 6], pc=True)
        # ---- c_cpad (cont, pad, vel): the container's slot 0
        a.label("c_cpad")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
        a.emit(bl, "c_splon"); a.emit(cmp_imm, 0, 0); bc("cp_stock", "eq")
        a.emit(cmp_imm, 5, 31); bc("cp_x", "hi")
        mask_addr(7, 4); a.emit(ldr_imm, 0, 7, 0); a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 5); a.emit(orrs_reg, 0, 1); a.emit(str_imm, 0, 7, 0)
        a.emit(lsrs_imm, 7, 5, 4); note_view(4, 7)                                                    # pads 1-16 Synth 1, 17-32 Synth 2
        a.emit(cmp_imm, 0, 0); bc("cp_x", "eq")
        a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 0); a.emit(movs_imm, 1, 16); a.emit(orrs_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(blx_reg, 3)
        a.label("cp_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("cp_stock")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, CT_PAD & ~1)
        # ---- c_crel (cont, pad): the container's slot 1; c_sprel = a pad of the split keyboard released (if it holds one)
        a.label("c_crel")
        a.emit(push_list, [4, 5], lr=True); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(bl, "c_splon"); a.emit(cmp_imm, 0, 0); bc("cr_stock", "eq")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_sprel"); a.emit(pop_list, [4, 5], pc=True)
        a.label("cr_stock")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(raw, popw([4, 5], lr=True)); a.emit(b_w, CT_REL & ~1)
        a.label("c_sprel")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(cmp_imm, 5, 31); bc("sr_x", "hi")
        mask_addr(7, 4); a.emit(ldr_imm, 0, 7, 0); a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 5); a.emit(tst_reg, 0, 1); bc("sr_x", "eq")
        a.emit(bics_reg, 0, 1); a.emit(str_imm, 0, 7, 0)
        a.emit(lsrs_imm, 7, 5, 4); note_view(4, 7)
        a.emit(cmp_imm, 0, 0); bc("sr_x", "eq")
        a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 4); a.emit(movs_imm, 1, 16); a.emit(orrs_reg, 1, 5); a.emit(blx_reg, 3)
        a.label("sr_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_cled (cont): the container's slot 7; with the split keyboard pads 0..15 = Synth 1's keys, 16..31 = Synth 2's
        a.label("c_cled")
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(mov_reg, 4, 0)
        a.emit(bl, CT_LED & ~1); a.emit(mov_reg, 5, 0)
        a.emit(bl, "c_splon"); a.emit(cmp_imm, 0, 0); bc("cl_x", "eq")
        a.emit(movs_imm, 6, 0)
        a.label("cl_t")
        note_view(4, 6); a.emit(cmp_imm, 0, 0); bc("cl_n", "eq")
        a.emit(ldr_imm, 3, 0, 0); a.emit(ldr_imm, 3, 3, 28); a.emit(blx_reg, 3)                        # its keyboard window
        a.emit(lsls_imm, 1, 6, 5); a.emit(adds_reg, 1, 1, 5); a.emit(movs_imm, 7, 0)                    # r1 = the half of the buffer
        a.label("cl_c")
        a.emit(raw, h(0x5BC2)); a.emit(raw, h(0x53CA))                                                  # ldrh r2,[r0,r7]; strh r2,[r1,r7]
        a.emit(adds_imm8, 7, 2); a.emit(cmp_imm, 7, 32); a.emit(b_cond, "cl_c", "lo")
        a.label("cl_n")
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 2); bc("cl_t", "lo")
        a.label("cl_x"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_brel (ctrl, id): the stock release's first 4 bytes; Synth 1 / 2 released = its held bit cleared
        a.label("c_brel")
        a.emit(push_list, [3, 4, 5], lr=True); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(cmp_imm, 5, 1); bc("br_s", "hi")
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("br_s", "eq")
        a.emit(adds_imm8, 0, S_PAINT); a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, F_HELD); a.emit(lsls_reg, 2, 5); a.emit(bl, "c_rmw")
        a.label("br_s"); a.emit(b_w, BTN_REL + 6)

    # ---- c_xpad (view, pad, vel): slot 0 of the synth Preset view
    a.label("c_xpad")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("xp_stock", "eq")
    a.emit(mov_reg, 7, 0)                                                      # r7 = SC14 state
    a.emit(ldrb_imm, 1, 7, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc("xp_stock", "eq")
    a.emit(mov_reg, 0, 4); a.emit(bl, L["c_synth"]); a.emit(cmp_imm, 0, 1); bc("xp_out", "hi")   # r0 = synth shown
    a.emit(mov_reg, 6, 0)
    a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 1, PAD0); a.emit(cmp_imm, 1, NM - 1); bc("xp_out", "hi")
    a.emit(adds_reg, 0, 7, 6); a.emit(strb_imm, 1, 0, S_MODE)
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 48); a.emit(bl, MARK_DIRTY)  # resend the Audio In group (H9)
    a.label("xp_out")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)                                    # every other press is swallowed
    a.label("xp_stock")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, K["SP_PRESS"])

    # ---- c_xleds (view) -> LED buffer: slot 7 of the synth Preset view
    a.label("c_xleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(bl, K["SP_LEDS"]); a.emit(mov_reg, 5, 0)                            # r5 = stock buffer (32 pads first)
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("xl_out", "eq")
    a.emit(mov_reg, 6, 0)                                                      # r6 = SC14 state
    a.emit(mov_reg, 0, 4); a.emit(bl, L["c_synth"]); a.emit(cmp_imm, 0, 1); bc("xl_out", "hi")
    a.emit(mov_reg, 7, 0)                                                      # r7 = synth
    a.emit(movs_imm, 2, 1); a.emit(raw, h(0x40BA))                             # r2 = 1 << synth ("painted" bit)
    a.emit(ldrb_imm, 3, 6, S_PAINT)
    a.emit(movs_imm, 0, F_SRC); a.emit(tst_reg, 3, 0); bc("xl_off", "eq")
    a.emit(tst_reg, 3, 2); bc("xl_pt", "ne")                                   # source view: remember that we paint over the stock buffer
    a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, S_PAINT)
    a.emit(mov_reg, 1, 2); a.emit(movs_imm, 2, 0); a.emit(bl, "c_rmw")
    if not METER:
        a.label("xl_pt")
        a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
        a.label("xl_z")
        a.emit(strh_reg, 1, 5, 0); a.emit(adds_imm8, 0, 2); a.emit(cmp_imm, 0, 64); bc("xl_z", "lo")      # all 32 pads dark
    else:                                                                      # first paint: all dark; later: rows 1 and 4 only (rows 2 / 3 = meter)
        a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
        a.label("xl_z")
        a.emit(strh_reg, 1, 5, 0); a.emit(adds_imm8, 0, 2); a.emit(cmp_imm, 0, 64); bc("xl_z", "lo")
        a.emit(b, "xl_zd")
        a.label("xl_pt")
        a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
        a.label("xl_z1")
        a.emit(strh_reg, 1, 5, 0); a.emit(adds_imm8, 0, 2); a.emit(cmp_imm, 0, 16); bc("xl_z1", "lo")
        a.emit(movs_imm, 0, 48)
        a.label("xl_z2")
        a.emit(strh_reg, 1, 5, 0); a.emit(adds_imm8, 0, 2); a.emit(cmp_imm, 0, 64); bc("xl_z2", "lo")
        a.label("xl_zd")
    a.emit(adds_reg, 3, 6, 7); a.emit(ldrb_imm, 3, 3, S_MODE)                  # r3 = mode of the synth shown
    a.emit(cmp_imm, 7, 0); bc("xl_s2", "ne")
    a.emit(movs_imm, 0, K["COLORS"][0][0]); a.emit(movs_imm, 1, K["COLORS"][0][1]); a.emit(b, "xl_paint")
    a.label("xl_s2"); a.emit(movs_imm, 0, K["COLORS"][1][0]); a.emit(movs_imm, 1, K["COLORS"][1][1])
    a.label("xl_paint")
    for i in range(NM):
        a.emit(cmp_imm, 3, i); bc(f"xl_d{i}", "ne")
        a.emit(strh_imm, 0, 5, 2 * (PAD0 + i)); a.emit(b, f"xl_n{i}")
        a.label(f"xl_d{i}"); a.emit(strh_imm, 1, 5, 2 * (PAD0 + i))
        a.label(f"xl_n{i}")
    a.emit(b, "xl_out")
    a.label("xl_off")                                                          # closed: repaint the stock view once
    a.emit(tst_reg, 3, 2); bc("xl_out", "eq")
    a.emit(mov_reg, 0, 6); a.emit(adds_imm8, 0, S_PAINT)
    a.emit(movs_imm, 1, 0); a.emit(bl, "c_rmw")                                # r2 = the synth's bit
    a.emit(mov_reg, 0, 4); a.emit(bl, K["SP_REPAINT"])
    a.label("xl_out")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr; patch the stock button handler's first 4 bytes and re-point slots 0 / 7 of the synth Preset view."""
    import ct_fw
    import build_sc15 as s15
    BASE = ct_fw.APP_BASE
    assert text(BTN, 6) == BTN_TXT, text(BTN, 6)
    assert s15.N_MODES in (5, 7) and (s15.N_MODES == 7 or not METER), s15.N_MODES          # 5 = noise, inputs; 7 = + delay / reverb return (SC20D.1 proved them)
    l15 = report["sc15"]["labels"]
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_synth=int(l15["c_synth"], 16))
    K = dict(S_MODE=s15.S_MODE, S_PAINT=s15.S_PAINT, PAD0=s15.PAD0, N_MODES=s15.N_MODES, COLORS=s15.COLORS,
             SP_PRESS=s15.SP_PRESS, SP_LEDS=s15.SP_LEDS, SP_REPAINT=s15.SP_REPAINT)
    assert struct.unpack_from("<I", img, SP_VT + 4 * SLOT_PAD - BASE)[0] == int(l15["c_spad"], 16) | 1
    assert struct.unpack_from("<I", img, SP_VT + 4 * SLOT_LEDS - BASE)[0] == int(l15["c_sleds"], 16) | 1
    code, labels = arm_code(base_addr, L, K)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SP_VT + 4 * SLOT_PAD - BASE, labels["c_xpad"] | 1)
    struct.pack_into("<I", img, SP_VT + 4 * SLOT_LEDS - BASE, labels["c_xleds"] | 1)
    img[BTN - BASE:BTN - BASE + 4] = b_w(BTN, labels["c_bentry"])
    if SPLIT:
        assert text(BTN_REL, 6) == BTN_REL_TXT, text(BTN_REL, 6)
        for k, (stock, lab) in enumerate(((CT_PAD, "c_cpad"), (CT_REL, "c_crel"))):
            assert struct.unpack_from("<I", img, CT_VT + 4 * k - BASE)[0] == stock
            struct.pack_into("<I", img, CT_VT + 4 * k - BASE, labels[lab] | 1)
        assert struct.unpack_from("<I", img, CT_VT + 28 - BASE)[0] == CT_LED
        struct.pack_into("<I", img, CT_VT + 28 - BASE, labels["c_cled"] | 1)
        img[BTN_REL - BASE:BTN_REL - BASE + 4] = b_w(BTN_REL, labels["c_brel"])
    return labels, code
