"""Alpha 7.28 (the user, 2026-11-22: «I want "sections" pages for the Stock synths, just like the mod synths … a similar interface to address the
Nova synth parameters, keep a close-enough interface layout»; «Build as proposed»; «top row of the alt-page … Macro assign on pad 25, knob seq on
32»; «optimally for flash size, recycle code»; «keep the color assignment, if the colors ever change on mod synths, they'll change here too»).

Synth 1 / 2's alt page (srcview: the synth's button / Preset again, its flag F_SRC; the morph view over it while a morph shows):
  * pads 1-8 = the section row: 1 Macros (the stock macros, as before), 2 OSC 1, 3 OSC 2, 4 VCA, 5 VCF, 6 FX, 7 Mod sources, 8 Mod matrix;
    the selected pad bright, the others dim, in the own synth's page colours (taken from vcf21 / modmx's constants at build time: Macros = the
    own synth's assigned-knobs page, OSC 1 / 2 = its OSC pages, VCA / VCF / FX = its Filter / VCA page, Mod sources = its modulation page, Mod
    matrix = its matrix page); the row hides while the knob sequencer's step view or the macro editor is on;
  * on a page other than Macros the 8 knobs set Nova parameters: the rows of the firmware's parameter table (0x0805454A) in ROWS, through the
    stock's setter as a received NRPN (macroed.c_mcset) and read back with the stock's getter; the range of each row from the table (lists:
    0..max, bipolar: centre +- range); a short list (64 values or fewer) moves one value every 128 / n knob events (at most 16: the type-knob
    rule), with macroed's accumulator; the knob LEDs = the page colour, bright as the value's place in its range;
  * Mod matrix: K1 = the slot 1..20 (an accumulator, 4 events a slot), K2 source 1, K3 source 2, K4 destination, K5 depth of that slot;
  * the tidy-up: the macro editor's pad moves from 32 to 25 and the knob sequencer's from 30 to 32 (presses forwarded as the old pads, the old
    pads' LEDs moved); pad 30 does nothing.
State (lost at power-off; nothing saved): the backup SRAM (icache.use_bkpon) NS: + 0 signature, + 4 the pages (Synth 1 bits 0-2, Synth 2 4-6),
+ 5 / + 6 the matrix slots, + 7 the accumulator (macroed.c_mcacc's byte 3 of r7 = NS + 4), + 8 the last knob, + 12 / + 16 the LED heads' LR,
+ 20 / + 24 their view / handler.  No stack while the chain below a slot-7 head runs (the LR in NS)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm,  # noqa: E402
                   lsls_reg, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, subs_imm8,
                   subs_reg, tst_reg, ldrh_imm)
from thumb import ldr_label, ldr_sp, str_sp, eors_reg, lsrs_imm, strb_reg  # noqa: E402
from build_sc14 import udiv  # noqa: E402

NS, SIG = 0x40024000, 0x3143534E                     # "NSC1" (the backup SRAM: icache.use_bkpon)
TABLE, GETTER = 0x0805454A, 0x08036192
SP_VT, AC64_VT = 0x0805AC9C, 0x0805AC64              # the synths' Preset view (slot 0 pad, slot 7 LEDs); the note tracks' macro handlers (slot 4 knob, slot 7 knob LEDs)
CTX = 0x200069E4
F_SRC, S_PAINT = 4, 20                               # srcview's flag in the SC14 state
F_SEL = 0x40                                         # macroed: a macro picked (the pads draw its number)
PAD_ED, PAD_SD, PAD_ED2, PAD_SD2 = 31, 29, 24, 31    # editor / knob sequencer: their pads before (32, 30) and now (25, 32)
MZ_ACT = 4                                           # morphz.O_ACT
# the rows of the pages OSC 1 .. Mod sources (K1..K8); 0xFF = nothing
ROWS = [[12, 13, 6, 7, 8, 9, 10, 11],                # OSC 1: semitones, cents, wave, wave interpolate, pulse width, virtual sync, density, density detune
        [21, 22, 15, 16, 17, 18, 19, 20],            # OSC 2: the same
        [40, 41, 42, 43, 39, 24, 25, 27],            # VCA: Env 1 attack, decay, sustain, release, velocity; Osc 1, Osc 2, noise levels
        [34, 36, 31, 38, 33, 35, 32, 45],            # VCF: frequency, resonance, drive, Env 2 -> frequency, type, tracking, drive type, Env 2 attack
        [78, 86, 79, 88, 89, 91, 92, 29],            # FX: distortion level, distortion type, chorus level, chorus type, rate, feedback, mod depth, post-FX level
        [59, 54, 71, 66, 50, 51, 52, 53]]            # Mod sources: LFO 1 rate, wave, LFO 2 rate, wave, Env 3 attack, decay, sustain, release
MX0, MX_MAP, MX_SLOTS, MX_STEP = 94, (0, 1, 3, 2), 20, 4   # the matrix: 20 slots x (source 1, source 2, depth, destination); K2..K5 = src1, src2, dest, depth


V2 = False                                           # Alpha 7.29 (use_v2)
# (V2) each macro destination code (macroed.DEST, 0..69) -> its row
DROW = ([3, 29, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 27, 34, 36, 31, 35, 38, 40, 41, 42, 43, 45, 46, 47, 48,
         49, 50, 51, 52, 53, 59, 60, 56, 71, 72, 68, 78, 79, 89, 91, 92, 93] + [MX0 + 4 * k + 2 for k in range(20)])
SESSION, SYN_AREA, PSIZE, PSET, XB, XSIG = 0x2003D71C, 0x2E4, 0xCA8, 0x380, 38, 0xD9   # (V2) Synth s's pattern p settings, bytes 38 / 39 (fm8store: 8..37)
MGR, PARAM_GET, MAC0 = 0x20040B10, 0x0803542C, 175  # macro m's slot 1: destination 175 + 17 m, start + 1, end + 2, depth + 3


def use_v2():
    """Alpha 7.29 (the user, 2026-11-22: «include a second macro page (with shift, like modsynths). And the "clear + knob to free a macro" and
    "duplicate + knob to assign a free macro" behaviors»; chosen: «8 extra knobs», «Macro, then extra knob», «Clear only first destination»):
      * Shift + pad 1 = Macros 2 (page 8): 8 extra knobs, each set straight to one Nova parameter (a row), not sequenceable; pad 1 in the own
        synth's non-sequenceable page colours (vcf21.NS_COL there, NS_SHIFT with Shift held elsewhere);
      * Duplicate + knob on a section page = that parameter to the first free macro (slot 1's depth 0: destination code, start 0, end 127, full
        depth; only the 70 macro destinations), else to the first free extra knob; nothing when it is already on a macro's slot 1 or an
        extra knob;  Clear + knob on Macros = that macro's slot 1 freed (its depth 0); on Macros 2 = that extra knob freed;
      * the extra knobs are saved with the project: bytes 38 / 39 of the settings of Synth s's patterns 0..7 (fm8store uses 8..37): 0xD9, the
        sum ^ 0xA5, the 8 rows (0xFF = none)."""
    global V2
    V2 = True


FIX = False                                          # Alpha 7.30 (use_fix)


def use_fix():
    """Alpha 7.30 (a review of 7.29): fm8store's project block is 2 + 30 bytes a pattern = bytes 8..39 of Synth 1 / 2's patterns 0..7, so 7.29's
    bytes 38 / 39 were the FM's (a save overwrote the extra knobs and an extra knob broke the FM's sum): the block goes to bytes 4 / 5 (the old
    per-pattern chain rules, unused with the group chains; patchain.use_keep46 keeps them on Clear + pattern); c_nsval reads through c_nsget and
    c_nsdup writes the macro's four fields in a loop (smaller)."""
    global FIX, XB
    FIX, XB = True, 4


V3 = False                                           # Alpha 7.32 (use_v3)
HAL_TICK = 0x2000081C
SYN_COL = (0x32, 0x20, 0x38, 0x26)                   # (V3) Synth 1 / 2 bright, then dim: the stock's track colours (0x08056464 [1], [2], [9], [10])
FL_COL = (0x01, 0x53, 0x45)                          # (V3) the hint: assigned white, freed red, no room orange
O_BEF, O_FL, O_FT = 5, 6, 24                         # (V3) from NS + 4: the page before pad 1's press, the hint (knob | 8 extra | kind << 4), its time
O_FH = 32                                            # (V3) from NS + 4: the macro handler the hint belongs to (a synth's or MIDI 1 / 2's)
O_SVH, O_SV = 28, 30                                 # (V3) the hinted knob's LED as the chain drew it (the stock does not redraw Macros' LEDs each frame), 0x80 | knob


def use_v3():
    """Alpha 7.32 (the user, 2026-11-22, on the device with 7.31: «The new knobs don't show their values with light. The assign method doesn't
    work. The stock macros should get the synth's color. Also, clear+knob is taken for stock ... we use pad1+knob for freeing up a knob. Restore
    clear+knob stock's behavior ... The freed up knob must be hinted/signaled, same when a knob is assigned»):
      * pad 1 (Macros) in the synth's own colour (Synth 1 magenta 0x32 / dim 0x38, Synth 2 green 0x20 / 0x26), not the own synth's yellow;
      * Clear + knob: on Macros the stock's (left = clear its automation, right = its default); on the other pages nothing;
      * pad 1 held + knob = that knob freed: on Macros 2 (the page before the press, or Shift held) the extra knob, else the macro's slot 1
        (depth 0); the page goes to Macros / Macros 2 and the knob's LED blinks red;
      * Duplicate + knob on a section page: the knob that holds the parameter afterwards (the new one, or the one that already had it: 7.30
        said nothing then, the usual case with a stock patch) blinks white and pad 1 blinks in that page's colour (Macros: the synth's,
        Macros 2: the non-sequenceable page's); no free macro or extra knob = the turned knob blinks orange.
    The hint: 3 blinks in 640 ms, over any page's knob LEDs (Macros too).
    The user, the same day: «apply the same clear method (pad1+knob on alt-view) for the mod macros too (clear+knob right or left do the same
    than stock, clear automation or current state)»: MIDI 1 / 2's own synth (p4dest.use_dup):
      * pad 1 held + knob = that slot of the assigned-knob page freed (Shift held, or the non-sequenceable page on the knobs: that page's slot);
        its LED blinks red;  Duplicate + knob on those two pages no longer frees (nothing);
      * Duplicate + knob on another page: p4dest assigns as before; the slot that holds the code afterwards blinks white (the turned knob orange
        when both rows are full);  Clear + knob: unchanged (vcf21: left = clear its automation, right = its default)."""
    global V3
    V3 = True


V4 = False                                           # Alpha 7.33 (use_v4)


def use_v4():
    """Alpha 7.33 (the user, 2026-11-23: «erase now erases all macro destinations (not just 1)»): pad 1 held + knob on Macros resets all four
    slots of that macro (destination 0, start 0, end 127, depth 0 = 64: a stock patch's unused slot), not only slot 1."""
    global V4
    V4 = True


V5 = False                                           # Alpha 7.34 (use_v5)


def use_v5():
    """Alpha 7.34 (the user, 2026-11-23: «with transport running, open alt-view. choose pad 2 osc (leds go green). press pad1: knob behavior is
    back to macros, but color stays green. pause, start again and the colors go magenta»): while the transport runs the stock does not redraw
    the macros' knob LEDs, so a section page's colours stayed; on Macros the knob LEDs are now drawn every frame: the synth's colour (SYN_COL),
    bright as the macro's position (parameter 174 + 17 m); not while Clear is held (the stock's Clear colours)."""
    global V5
    V5 = True


V6 = False                                           # Alpha 7.35 (use_v6)


def use_v6():
    """Alpha 7.35 (the user, 2026-11-23: «The selected knob doesnt go to the free knob. instead, it goes to the shift knobs»: the parameter was
    already on a Macros 2 knob, so 7.32-7.34 only pointed at it): Duplicate + knob = a macro first: already on a macro's slot 1 = that macro;
    else, a macro destination with a free macro = that macro, and an extra knob that held the parameter is freed; only then Macros 2 (already
    there, else the first free extra knob; none = no room)."""
    global V6
    V6 = True


V7 = False                                           # Alpha 7.36 (use_v7)


def use_v7():
    """Alpha 7.36 (the user, 2026-11-23: «make duplicate (assign) work outside the alt-page, when playing regularly with a view opened»; chosen:
    «Section page follows»): the section page picked on Synth 1 / 2's alt page stays on that synth's knobs in its other views (Note, Velocity,
    Preset…: wherever its knobs go to its macro handler), with its LEDs and Duplicate + knob; Macros on the alt page = the stock's macros there
    again.  Not with the knob sequencer's step view on the screen; pad 1 held + knob frees only on the alt page (elsewhere pad 1 plays)."""
    global V7
    V7 = True


V8 = False                                           # Alpha 7.37 (use_v8)
O_SH, O_PK, O_ST = 7, 31, 36                         # (V8) from NS + 4: the macro on the slot pads (0x80 | synth << 6 | macro), the picked slot
                                                     #   (0xA0 | synth << 6 | slot << 3 | macro), the time of the macro's last move
SLOT_MS = 11                                         # (V8) the slot pads show for 2 ^ 11 ms after a macro knob's last move


def use_v8():
    """Alpha 7.37 (the user, 2026-11-23: «Pads 1, 9, 17 and 25 are now macro slots 1-4. Touching a macro knob while the alt-view is opened shows
    whether a pad is assigned (lit) or free (dim). Holding any of these pads while moving a knob selects the slot to be assigned next (if it's
    already assigned, it gets overwritten). The new assignment with duplicate copies destination and range. The new dedicated views need to have
    their adequate range»; chosen: «Move the editor to pad 26», «Clear + slot pad», «Match the section knob», «Always Macros 2»):
      * a macro knob moved on the alt page's Macros page: for 2 s pads 1 / 9 / 17 / 25 = that macro's slots 1-4, the synth's colour bright =
        in use (depth not 0), dim = free; the picked slot white (and the pads stay while a slot is picked);
      * a slot pad held + a knob (any page of the alt page) = that slot of that knob's macro picked (the knob does not move anything; pad 1
        held from a section page: the page comes back);  Duplicate + knob on a section page then writes the slot: the destination, start 0,
        end 127, depth = half the parameter's span (0..127 = full; the post-FX level 52..82 and the two LFO sync lists 0..35 less), and the
        pick is used up;  without a pick, or a parameter that is no macro destination: Macros 2 (already there, else the first free knob);
      * Clear + a slot pad while they show = that slot unused (destination 0, 0..127, depth 0);
      * the macro editor on pad 26 (pad 25 = slot 4);  pad 1 held + knob with Macros 2 on the knobs before (or Shift) still frees that
        Macros 2 knob;  a tap on pad 1 = Macros as before."""
    global V8
    assert V4
    V8 = True


V9 = False                                           # Alpha 7.42 (use_v9)


def use_v9():
    """Alpha 7.42 (the user, 2026-11-24: Macros 2 gets automation lanes, «Like the macros», «Two: start and middle»; tools/m2lanes.py): two
    calls for m2lanes, each a bl to c_nsret (bx lr) that m2lanes points at its own code (labels kn_m2 / kn_m2c in the report):
      * a Macros 2 knob that changed its parameter: kn_m2 (r0 = synth, r1 = knob, r2 = the value written, r3 = the macro handler);
      * Clear + knob on Macros 2 (before: nothing): kn_m2c (r0 = synth, r1 = knob, r2 = the delta, r3 = the knob's row or 0xFF)."""
    global V9
    V9 = True


def page_colours():
    """(bright, dim) of the 8 pads, from the own synth's constants (a change there changes these on the next build)"""
    import vcf21 as V, modmx as MX
    c = [V.COL_PAGE2[0], V.COL_PAGE[1], V.COL_PAGE[2], V.COL_PAGE[0], V.COL_PAGE[0], V.COL_PAGE[0], V.COL_PAGE2[1], MX.COL_MX]
    return c + [(V.NS_COL, V.NS_SHIFT)] if V2 else c


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def str_lr(rn, off): return h(0xF8C0 | rn) + h(0xE000 | off)         # str.w lr, [rn, #off]


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, (v >> 16) & 0xFFFF)
    cols = page_colours()
    assert not V9 or V8, "use_v9 needs use_v8"
    ED2 = 25 if V8 else PAD_ED2                                                                     # (V8) the macro editor's pad: 26

    # ---- c_nsst() -> r0 = NS + 4 (the first time: zeroed, signed); clobbers r1, r2
    a.label("c_nsst")
    imm32(0, NS); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8)
    if V3: E(str_imm, 1, 0, 4 + O_SVH)                                                       # (V3) no knob LED put aside
    a.label("st_x"); E(adds_imm8, 0, 4); E(raw, h(0x4770))

    # ---- c_nspg(r4 = synth) -> r0 = its page 0..7; clobbers r1, r2
    a.label("c_nspg")
    E(push_list, [], lr=True); E(bl, "c_nsst"); E(ldrb_imm, 0, 0, 0); E(lsls_imm, 1, 4, 2); E(lsrs_reg, 0, 1); E(movs_imm, 1, 15 if V2 else 7); E(ands_reg, 0, 1)
    E(pop_list, [], pc=True)

    if V3:
        # ---- c_nsput(r4 = synth, r3 = page): written; clobbers r0-r3
        a.label("c_nsput")
        E(push_list, [5], lr=True); E(bl, "c_nsst"); E(ldrb_imm, 1, 0, 0); E(lsls_imm, 2, 4, 2); E(movs_imm, 5, 15); E(lsls_reg, 5, 2); E(bics_reg, 1, 5)
        E(lsls_reg, 3, 2); E(orrs_reg, 1, 3); E(strb_imm, 1, 0, 0); E(pop_list, [5], pc=True)
        # ---- c_nsflash(r0 = the hint, r1 = the macro handler): kept with the time; clobbers r0-r3
        a.label("c_nsflash")
        E(push_list, [1], lr=True); E(mov_reg, 3, 0); E(bl, "c_nsst"); E(strb_imm, 3, 0, O_FL); E(pop_list, [1]); E(str_imm, 1, 0, O_FH)
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, O_FT); E(pop_list, [], pc=True)
        # ---- c_nsfl() -> r0 = the hint while it blinks on (3 blinks of 128 ms in 640 ms), else 0; clobbers r1-r3
        a.label("c_nsfl")
        E(push_list, [], lr=True); E(bl, "c_nsst"); E(ldrb_imm, 3, 0, O_FL); E(ldr_imm, 1, 0, O_FT); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0)
        E(subs_reg, 2, 2, 1); E(movs_imm, 0, 0); E(lsrs_imm, 2, 2, 7); E(cmp_imm, 2, 5); E(b_cond, "fl_x", "hs")
        E(lsrs_imm, 2, 2, 1); E(b_cond, "fl_x", "cs"); E(mov_reg, 0, 3)
        a.label("fl_x"); E(pop_list, [], pc=True)

    if V7:
        # ---- c_nssyn(r0 = a macro handler) -> r0 = 0 / 1 when it is Synth 1 / 2's, else 0xFF; clobbers r1-r3
        a.label("c_nssyn")
        E(mov_reg, 3, 0); imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sy_n", "eq")
        E(ldr_imm, 0, 0, 0x40); E(cmp_imm, 0, 0); E(b_cond, "sy_n", "eq"); E(ldr_imm, 0, 0, 0x2C); E(cmp_imm, 0, 0); E(b_cond, "sy_n", "eq")
        E(raw, h(0xF8D0) + h(1 << 12 | 0x148)); E(cmp_reg, 1, 3); E(b_cond, "sy_0", "eq")
        E(raw, h(0xF8D0) + h(1 << 12 | 0x14C)); E(cmp_reg, 1, 3); E(b_cond, "sy_1", "eq")
        a.label("sy_n"); E(movs_imm, 0, 0xFF); E(raw, h(0x4770))
        a.label("sy_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))
        a.label("sy_1"); E(movs_imm, 0, 1); E(raw, h(0x4770))
        # ---- c_nsfw(r0 = a macro handler) -> r0 = its synth when its section page follows it here (not Macros, no step view), else 0xFF; clobbers r1-r3
        a.label("c_nsfw")
        E(push_list, [4], lr=True); E(bl, "c_nssyn"); E(mov_reg, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "fw_n", "hi")
        E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); E(b_cond, "fw_n", "ne")
        E(bl, "c_nspg"); E(cmp_imm, 0, 0); E(b_cond, "fw_n", "eq"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
        a.label("fw_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_nsalt(r0 = view) -> r0 = the synth whose alt page this view is, else 0xFF; clobbers r1-r3
    a.label("c_nsalt")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "al_n", "eq")
    E(ldrb_imm, 1, 0, S_PAINT); E(movs_imm, 2, F_SRC); E(tst_reg, 1, 2); E(b_cond, "al_n", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_synth"]); E(cmp_imm, 0, 1); E(b_cond, "al_x", "ls")
    a.label("al_n"); E(movs_imm, 0, 0xFF)
    a.label("al_x"); E(pop_list, [4], pc=True)

    # ---- c_nsmz() -> r0 = 1 when a morph view is on the screen; clobbers r1-r3
    a.label("c_nsmz")
    E(push_list, [4, 6], lr=True)
    E(bl, L["c_mzst"]); E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, MZ_ACT); E(movs_imm, 0, 0); E(cmp_imm, 4, 3); E(b_cond, "mz_x", "hi")
    E(bl, L["c_mzmv"])
    a.label("mz_x"); E(pop_list, [4, 6], pc=True)

    # ---- c_nsrow(r4 = synth, r1 = knob, r2 = page 1..7) -> r0 = the row, 0xFE = the matrix's slot knob, 0xFF = nothing; clobbers r1-r3
    a.label("c_nsrow")
    if V2: E(cmp_imm, 2, 8); E(b_cond, "rw_n8", "ne"); E(b, "c_nsxrow"); a.label("rw_n8")          # (V2) Macros 2: the extra knob's row
    E(cmp_imm, 2, 7); E(b_cond, "rw_m", "eq")
    E(subs_imm8, 2, 1); E(lsls_imm, 2, 2, 3); E(adds_reg, 2, 2, 1); E(ldr_label, 3, "t_rows"); E(ldrb_reg, 0, 3, 2); E(raw, h(0x4770))
    a.label("rw_m"); E(movs_imm, 0, 0xFE); E(cmp_imm, 1, 0); E(b_cond, "rw_x", "eq"); E(movs_imm, 0, 0xFF); E(cmp_imm, 1, 4); E(b_cond, "rw_x", "hi")
    E(ldr_label, 3, "t_mx"); E(subs_imm8, 1, 1); E(ldrb_reg, 2, 3, 1)                                     # the slot's field
    imm32(3, NS + 5); E(ldrb_reg, 0, 3, 4); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 2); E(adds_imm8, 0, MX0)
    a.label("rw_x"); E(raw, h(0x4770))

    if V9: a.label("c_nsret"); E(raw, h(0x4770))                                              # (V9) m2lanes' two calls, until it points them

    # ---- c_nsrng(r0 = row) -> r0 = lo, r1 = hi (raw bytes); clobbers r2, r3
    a.label("c_nsrng")
    E(lsls_imm, 0, 0, 3); imm32(3, TABLE); E(adds_reg, 3, 3, 0)
    E(ldrb_imm, 1, 3, 7); E(movs_imm, 0, 0); E(ldrb_imm, 2, 3, 4); E(cmp_imm, 2, 2); E(b_cond, "rg_x", "ne")
    E(ldrb_imm, 0, 3, 5); E(adds_reg, 1, 1, 0); E(ldrb_imm, 2, 3, 6); E(raw, h(0xB252)); E(adds_reg, 0, 0, 2)   # (sxtb r2, r2)
    a.label("rg_x"); E(raw, h(0x4770))

    # ---- c_nsval(r4 = synth, r0 = row) -> r0 = the value, r1 = lo, r2 = hi; clobbers r3
    a.label("c_nsval")
    E(push_list, [5], lr=True); E(mov_reg, 5, 0); E(bl, "c_nsrng"); E(push_list, [0, 1])
    if FIX: E(mov_reg, 1, 5); E(bl, "c_nsget")
    else: E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1)
    E(pop_list, [1, 2]); E(pop_list, [5], pc=True)

    if V2:
        # ---- c_nsxa(r4 = synth, r1 = k 0..9) -> r0 = byte k of the synth's extra-knob block in the RAM record, 0 = no record; clobbers r1-r3
        a.label("c_nsxa")
        imm32(0, SESSION); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "xa_x", "eq")
        E(lsrs_imm, 2, 1, 1); E(lsls_imm, 3, 4, 3); E(adds_reg, 2, 2, 3); imm32(3, PSIZE); E(muls, 2, 3); E(adds_reg, 0, 0, 2)
        E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(adds_reg, 0, 0, 1); imm32(1, SYN_AREA + PSET + XB); E(adds_reg, 0, 0, 1)
        a.label("xa_x"); E(raw, h(0x4770))
        # ---- c_nsxsum(r4) -> r0 = the sum of bytes 2..9 ^ 0xA5, r1 = 1 when bytes 0 / 1 = the signature / that sum (0 without a record); clobbers r2, r3
        a.label("c_nsxsum")
        E(push_list, [5, 6], lr=True); E(movs_imm, 5, 0); E(movs_imm, 6, 2)
        a.label("xs_l"); E(mov_reg, 1, 6); E(bl, "c_nsxa"); E(cmp_imm, 0, 0); E(b_cond, "xs_n", "eq"); E(ldrb_imm, 0, 0, 0); E(adds_reg, 5, 5, 0)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 10); E(b_cond, "xs_l", "lo")
        E(movs_imm, 0, 0xA5); E(eors_reg, 5, 0); E(lsls_imm, 5, 5, 24); E(lsrs_imm, 5, 5, 24)
        E(movs_imm, 1, 0); E(bl, "c_nsxa"); E(ldrb_imm, 2, 0, 0); E(ldrb_imm, 3, 0, 1); E(mov_reg, 0, 5); E(movs_imm, 1, 0)
        E(cmp_imm, 2, XSIG); E(b_cond, "xs_x", "ne"); E(cmp_reg, 3, 5); E(b_cond, "xs_x", "ne"); E(movs_imm, 1, 1); E(b, "xs_x")
        a.label("xs_n"); E(movs_imm, 1, 0)
        a.label("xs_x"); E(pop_list, [5, 6], pc=True)
        # ---- c_nsxrow(r4 = synth, r1 = extra knob 0..7) -> r0 = its row, 0xFF = none (or no valid block); clobbers r1-r3
        a.label("c_nsxrow")
        E(push_list, [5], lr=True); E(mov_reg, 5, 1); E(bl, "c_nsxsum"); E(movs_imm, 0, 0xFF); E(cmp_imm, 1, 0); E(b_cond, "xr_x", "eq")
        E(adds_imm8, 5, 2); E(mov_reg, 1, 5); E(bl, "c_nsxa"); E(ldrb_imm, 0, 0, 0)
        a.label("xr_x"); E(pop_list, [5], pc=True)
        # ---- c_nsxset(r4 = synth, r1 = extra knob 0..7, r2 = row or 0xFF): written, the block made valid; clobbers r0-r3
        a.label("c_nsxset")
        E(push_list, [5, 6], lr=True); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, "c_nsxsum"); E(cmp_imm, 1, 0); E(b_cond, "xw_v", "ne")
        E(movs_imm, 1, 0); E(bl, "c_nsxa"); E(cmp_imm, 0, 0); E(b_cond, "xw_x", "eq")                 # no valid block: 8 x none
        E(movs_imm, 1, 2)
        a.label("xw_z"); E(push_list, [1]); E(bl, "c_nsxa"); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 0); E(pop_list, [1]); E(adds_imm8, 1, 1); E(cmp_imm, 1, 10); E(b_cond, "xw_z", "lo")
        a.label("xw_v"); E(adds_imm8, 5, 2); E(mov_reg, 1, 5); E(bl, "c_nsxa"); E(strb_imm, 6, 0, 0)
        E(bl, "c_nsxsum"); E(mov_reg, 5, 0); E(movs_imm, 1, 0); E(bl, "c_nsxa"); E(movs_imm, 1, XSIG); E(strb_imm, 1, 0, 0); E(strb_imm, 5, 0, 1)
        a.label("xw_x"); E(pop_list, [5, 6], pc=True)
        # ---- c_nsget(r4 = synth, r1 = parameter) -> r0 = its value; clobbers r1-r3
        a.label("c_nsget")
        E(push_list, [], lr=True); E(mov_reg, 0, 4); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(pop_list, [], pc=True)
        if V8:
            # ---- c_nsdup(r4 = synth, r0 = row) -> r0 = the hint: the picked slot (a macro destination), else Macros 2
            a.label("c_nsdup")
            E(push_list, [5, 6, 7], lr=True); E(mov_reg, 5, 0); E(movs_imm, 7, 0); E(ldr_label, 1, "t_drow")
            a.label("d8_c"); E(ldrb_reg, 0, 1, 7); E(cmp_reg, 0, 5); E(b_cond, "d8_m", "eq"); E(adds_imm8, 7, 1); E(cmp_imm, 7, len(DROW)); E(b_cond, "d8_c", "lo"); E(b, "d8_e")
            a.label("d8_m"); E(bl, "c_nsst"); E(ldrb_imm, 6, 0, O_PK); E(lsrs_imm, 1, 6, 6); E(mov_reg, 2, 4); E(adds_imm8, 2, 2); E(cmp_reg, 1, 2); E(b_cond, "d8_e", "ne")
            E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_PK); E(movs_imm, 1, 0xC7); E(ands_reg, 1, 6); E(strb_imm, 1, 0, O_SH)     # the pick used; its macro on the pads
            imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, O_ST)
            E(movs_imm, 1, 7); E(ands_reg, 1, 6); E(movs_imm, 0, 17); E(muls, 1, 0); E(lsrs_imm, 0, 6, 3); E(movs_imm, 2, 3); E(ands_reg, 0, 2); E(lsls_imm, 0, 0, 2)
            E(adds_reg, 1, 1, 0); E(adds_imm8, 1, MAC0); E(push_list, [6]); E(movs_imm, 6, 0)                              # r1 = the slot's first parameter
            a.label("d8_wl"); E(ldr_label, 3, "t_dupv"); E(ldrb_reg, 2, 3, 6); E(cmp_imm, 2, 0xFF); E(b_cond, "d8_wv", "ne"); E(mov_reg, 2, 7)
            a.label("d8_wv"); E(push_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(pop_list, [1]); E(adds_imm8, 1, 1)
            E(adds_imm8, 6, 1); E(cmp_imm, 6, 3); E(b_cond, "d8_wl", "lo")
            E(push_list, [1]); E(mov_reg, 0, 5); E(bl, "c_nsrng"); E(subs_reg, 1, 1, 0); E(adds_imm8, 1, 1); E(lsrs_imm, 1, 1, 1); E(adds_imm8, 1, 64)   # depth: half the span
            E(cmp_imm, 1, 127); E(b_cond, "d8_dk", "ls"); E(movs_imm, 1, 127)
            a.label("d8_dk"); E(mov_reg, 2, 1); E(pop_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_mcset"])
            E(pop_list, [6]); E(movs_imm, 0, 7); E(ands_reg, 0, 6); E(movs_imm, 1, 0x10); E(orrs_reg, 0, 1); E(b, "d8_x")
            a.label("d8_e"); E(movs_imm, 6, 0)                                                         # Macros 2: already there
            a.label("d8_xa"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_reg, 0, 5); E(b_cond, "d8_hx", "eq"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d8_xa", "lo")
            E(movs_imm, 6, 0)                                                                           # else the first free extra knob
            a.label("d8_el"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_imm, 0, 0xFF); E(b_cond, "d8_en", "ne")
            E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(bl, "c_nsxset"); E(b, "d8_hx")
            a.label("d8_en"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d8_el", "lo")
            E(movs_imm, 0, 0x30); E(b, "d8_x")
            a.label("d8_hx"); E(movs_imm, 0, 0x18); E(orrs_reg, 0, 6)
            a.label("d8_x"); E(pop_list, [5, 6, 7], pc=True)
        elif V6:
            # ---- c_nsdup(r4 = synth, r0 = row) -> r0 = the hint: a macro first (already there, else a free one, the extra knob freed), then Macros 2
            a.label("c_nsdup")
            E(push_list, [5, 6, 7], lr=True); E(mov_reg, 5, 0); E(movs_imm, 6, 0)
            a.label("d6_a")
            E(movs_imm, 0, 17); E(muls, 0, 6); E(mov_reg, 7, 0); E(adds_imm8, 0, MAC0 + 3); E(mov_reg, 1, 0); E(bl, "c_nsget"); E(cmp_imm, 0, 64); E(b_cond, "d6_an", "eq")
            E(mov_reg, 1, 7); E(adds_imm8, 1, MAC0); E(bl, "c_nsget"); E(cmp_imm, 0, 70); E(b_cond, "d6_an", "hs")
            E(ldr_label, 1, "t_drow"); E(ldrb_reg, 0, 1, 0); E(cmp_reg, 0, 5); E(b_cond, "d6_hm", "eq")
            a.label("d6_an"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d6_a", "lo")
            E(movs_imm, 7, 0); E(ldr_label, 1, "t_drow")                                               # r7 = its destination code
            a.label("d6_c"); E(ldrb_reg, 0, 1, 7); E(cmp_reg, 0, 5); E(b_cond, "d6_m", "eq"); E(adds_imm8, 7, 1); E(cmp_imm, 7, len(DROW)); E(b_cond, "d6_c", "lo"); E(b, "d6_e")
            a.label("d6_m"); E(movs_imm, 6, 0)
            a.label("d6_ml")                                                                            # the first macro whose slot 1 has no depth
            E(movs_imm, 0, 17); E(muls, 0, 6); E(adds_imm8, 0, MAC0); E(push_list, [0]); E(adds_imm8, 0, 3); E(mov_reg, 1, 0); E(bl, "c_nsget"); E(pop_list, [1])
            E(cmp_imm, 0, 64); E(b_cond, "d6_mn", "ne")
            E(push_list, [6]); E(movs_imm, 6, 0)
            a.label("d6_wl"); E(ldr_label, 3, "t_dupv"); E(ldrb_reg, 2, 3, 6); E(cmp_imm, 2, 0xFF); E(b_cond, "d6_wv", "ne"); E(mov_reg, 2, 7)
            a.label("d6_wv"); E(push_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(pop_list, [1]); E(adds_imm8, 1, 1)
            E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "d6_wl", "lo")
            E(movs_imm, 6, 0)
            a.label("d6_xl"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_reg, 0, 5); E(b_cond, "d6_xn", "ne")   # an extra knob with it: freed
            E(mov_reg, 1, 6); E(movs_imm, 2, 0xFF); E(bl, "c_nsxset")
            a.label("d6_xn"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d6_xl", "lo"); E(pop_list, [6]); E(b, "d6_hm")
            a.label("d6_mn"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d6_ml", "lo")
            a.label("d6_e"); E(movs_imm, 6, 0)                                                         # Macros 2: already there
            a.label("d6_xa"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_reg, 0, 5); E(b_cond, "d6_hx", "eq"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d6_xa", "lo")
            E(movs_imm, 6, 0)                                                                           # else the first free extra knob
            a.label("d6_el"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_imm, 0, 0xFF); E(b_cond, "d6_en", "ne")
            E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(bl, "c_nsxset"); E(b, "d6_hx")
            a.label("d6_en"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "d6_el", "lo")
            E(movs_imm, 0, 0x30); E(b, "d6_x")
            a.label("d6_hm"); E(movs_imm, 0, 0x10); E(orrs_reg, 0, 6); E(b, "d6_x")
            a.label("d6_hx"); E(movs_imm, 0, 0x18); E(orrs_reg, 0, 6)
            a.label("d6_x"); E(pop_list, [5, 6, 7], pc=True)
        else:
            # ---- c_nsdup(r4 = synth, r0 = row): the row to the first free macro (if a macro destination), else the first free extra knob
            a.label("c_nsdup")
            E(push_list, [5, 6, 7], lr=True); E(mov_reg, 5, 0)
            E(movs_imm, 6, 0)                                                                           # already there: a macro's slot 1 or an extra knob
            a.label("dp_a")
            E(movs_imm, 0, 17); E(muls, 0, 6); E(mov_reg, 7, 0); E(adds_imm8, 0, MAC0 + 3); E(mov_reg, 1, 0); E(bl, "c_nsget"); E(cmp_imm, 0, 64); E(b_cond, "dp_an", "eq")
            E(mov_reg, 1, 7); E(adds_imm8, 1, MAC0); E(bl, "c_nsget"); E(cmp_imm, 0, 70); E(b_cond, "dp_an", "hs")
            E(ldr_label, 1, "t_drow"); E(ldrb_reg, 0, 1, 0); E(cmp_reg, 0, 5); E(b_cond, "dp_hm" if V3 else "dp_x", "eq")
            a.label("dp_an")
            E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_reg, 0, 5); E(b_cond, "dp_hx" if V3 else "dp_x", "eq")
            E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "dp_a", "lo")
            E(movs_imm, 7, 0); E(ldr_label, 1, "t_drow")                                               # r7 = its destination code
            a.label("dp_c"); E(ldrb_reg, 0, 1, 7); E(cmp_reg, 0, 5); E(b_cond, "dp_m", "eq"); E(adds_imm8, 7, 1); E(cmp_imm, 7, len(DROW)); E(b_cond, "dp_c", "lo"); E(b, "dp_e")
            a.label("dp_m"); E(movs_imm, 6, 0)
            a.label("dp_ml")                                                                            # the first macro whose slot 1 has no depth
            E(movs_imm, 0, 17); E(muls, 0, 6); E(adds_imm8, 0, MAC0); E(push_list, [0]); E(adds_imm8, 0, 3); E(mov_reg, 1, 0); E(bl, "c_nsget"); E(pop_list, [1])
            E(cmp_imm, 0, 64); E(b_cond, "dp_mn", "ne")
            if FIX:                                                                                    # destination, start 0, end 127, depth 127
                if V3: E(push_list, [6])
                E(movs_imm, 6, 0)
                a.label("dp_wl"); E(ldr_label, 3, "t_dupv"); E(ldrb_reg, 2, 3, 6); E(cmp_imm, 2, 0xFF); E(b_cond, "dp_wv", "ne"); E(mov_reg, 2, 7)
                a.label("dp_wv"); E(push_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(pop_list, [1]); E(adds_imm8, 1, 1)
                E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "dp_wl", "lo")
                if V3: E(pop_list, [6]); E(b, "dp_hm")
            else:
              for off, val in ((0, None), (1, 0), (2, 127), (3, 127)):
                E(push_list, [1])
                if off: E(adds_imm8, 1, off)
                if val is None: E(mov_reg, 2, 7)
                else: E(movs_imm, 2, val)
                E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(pop_list, [1])
            E(b, "dp_x")
            a.label("dp_mn"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "dp_ml", "lo")
            a.label("dp_e"); E(movs_imm, 6, 0)                                                         # the first free extra knob
            a.label("dp_el"); E(mov_reg, 1, 6); E(bl, "c_nsxrow"); E(cmp_imm, 0, 0xFF); E(b_cond, "dp_en", "ne")
            E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(bl, "c_nsxset"); E(b, "dp_hx" if V3 else "dp_x")
            a.label("dp_en"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "dp_el", "lo")
            if V3:                                                                                     # (V3) r0 = the hint: no room / a macro / an extra knob
                E(movs_imm, 0, 0x30); E(b, "dp_x")
                a.label("dp_hm"); E(movs_imm, 0, 0x10); E(orrs_reg, 0, 6); E(b, "dp_x")
                a.label("dp_hx"); E(movs_imm, 0, 0x18); E(orrs_reg, 0, 6)
            a.label("dp_x"); E(pop_list, [5, 6, 7], pc=True)
        # ---- c_nsheld() -> r0 = the held buttons (bit 0 Clear, bit 1 Duplicate); clobbers r1-r3
        a.label("c_nsheld")
        E(push_list, [], lr=True); imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(pop_list, [], pc=True)

    if V8:
        # ---- c_nsshow(r4 = synth) -> r0 = the picked slot's byte, else the shown macro's while its 2 s last, else 0; clobbers r1-r3
        a.label("c_nsshow")
        E(push_list, [], lr=True); E(bl, "c_nsst"); E(mov_reg, 3, 0)
        E(ldrb_imm, 0, 3, O_PK); E(lsrs_imm, 1, 0, 6); E(mov_reg, 2, 4); E(adds_imm8, 2, 2); E(cmp_reg, 1, 2); E(b_cond, "sh_x", "eq")
        E(ldrb_imm, 0, 3, O_SH); E(lsrs_imm, 1, 0, 6); E(cmp_reg, 1, 2); E(b_cond, "sh_0", "ne")
        E(ldr_imm, 1, 3, O_ST); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(subs_reg, 2, 2, 1); E(lsrs_imm, 2, 2, SLOT_MS); E(b_cond, "sh_x", "eq")
        a.label("sh_0"); E(movs_imm, 0, 0)
        a.label("sh_x"); E(pop_list, [], pc=True)
        # ---- c_nsunuse(r4 = synth, r1 = a slot's first parameter): destination 0, 0..127, depth 0 (64); clobbers r0-r3
        a.label("c_nsunuse")
        E(push_list, [5, 6], lr=True); E(mov_reg, 5, 1); E(movs_imm, 6, 0)
        a.label("un_l"); E(ldr_label, 3, "t_dupv"); E(mov_reg, 2, 6); E(adds_imm8, 2, 4); E(ldrb_reg, 2, 3, 2); E(adds_reg, 1, 5, 6); E(mov_reg, 0, 4); E(bl, L["c_mcset"])
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "un_l", "lo"); E(pop_list, [5, 6], pc=True)

    # ---- c_nspad (the synths' Preset view slot 0: view, pad, velocity)
    a.label("c_nspad")
    E(push_list, [0, 1, 2, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, "c_nsalt"); E(mov_reg, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "pd_f", "hi")
    E(bl, "c_nsmz"); E(cmp_imm, 0, 0); E(b_cond, "pd_f", "ne")
    E(movs_imm, 0, PAD_SD); E(cmp_imm, 5, PAD_SD2); E(b_cond, "pd_as", "eq")                       # pad 32 = the knob sequencer (as pad 30)
    E(cmp_imm, 5, PAD_SD); E(b_cond, "pd_s", "eq")                                                 # pad 30: nothing
    E(movs_imm, 0, PAD_ED); E(cmp_imm, 5, ED2); E(b_cond, "pd_as", "eq")                           # pad 25 (V8: 26) = the macro editor (as pad 32)
    if V8:                                                                                         # (V8) pads 9 / 17 / 25 stay ours
        E(cmp_imm, 5, 8); E(b_cond, "pd_lo", "lo"); E(movs_imm, 0, 7); E(tst_reg, 5, 0); E(b_cond, "pd_f", "ne"); E(cmp_imm, 5, 24); E(b_cond, "pd_f", "hi")
        a.label("pd_lo")
    else: E(cmp_imm, 5, 8); E(b_cond, "pd_f", "hs")
    E(bl, L["c_mcsrc"]); E(cmp_imm, 0, 1); E(b_cond, "pd_f", "hi")                                 # the step view open: its pads
    E(bl, L["c_mcon"]); E(cmp_imm, 0, 0); E(b_cond, "pd_f", "ne")                                  # the editor on: its pads
    if V8:                                                                                         # (V8) a slot pad: Clear = that slot unused; pads 9 / 17 / 25 alone nothing
        E(movs_imm, 0, 7); E(tst_reg, 5, 0); E(b_cond, "pd_n8", "ne")
        E(bl, "c_nsheld"); E(lsrs_imm, 0, 0, 1); E(b_cond, "pd_nc", "cc")
        E(bl, "c_nsshow"); E(cmp_imm, 0, 0); E(b_cond, "pd_s", "eq")
        E(movs_imm, 1, 7); E(ands_reg, 1, 0); E(movs_imm, 0, 17); E(muls, 1, 0); E(lsrs_imm, 0, 5, 1); E(adds_reg, 1, 1, 0); E(adds_imm8, 1, MAC0)
        E(bl, "c_nsunuse"); E(b, "pd_s")
        a.label("pd_nc"); E(cmp_imm, 5, 0); E(b_cond, "pd_s", "ne")
        a.label("pd_n8")
    if V2:                                                                                         # (V2) Shift + pad 1 = Macros 2
        E(cmp_imm, 5, 0); E(b_cond, "pd_ns", "ne"); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pd_ns", "eq"); E(movs_imm, 5, 8)
        a.label("pd_ns")
    if V3:                                                                                         # (V3) pad 1: the page before the press kept
        E(movs_imm, 0, 7); E(tst_reg, 5, 0); E(b_cond, "pd_w", "ne")
        E(bl, "c_nspg"); E(mov_reg, 3, 0); E(bl, "c_nsst"); E(strb_imm, 3, 0, O_BEF)
        a.label("pd_w"); E(mov_reg, 3, 5); E(bl, "c_nsput")
    else:
        E(bl, "c_nsst"); E(ldrb_imm, 1, 0, 0); E(lsls_imm, 2, 4, 2); E(movs_imm, 3, 15 if V2 else 7); E(lsls_reg, 3, 2); E(bics_reg, 1, 3)
        E(lsls_reg, 5, 2); E(orrs_reg, 1, 5); E(strb_imm, 1, 0, 0)
    a.label("pd_s"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("pd_as"); E(str_sp, 0, 4)                                                         # (str r0, [sp, #4]: the pad below)
    a.label("pd_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

    # ---- c_nsleds (that view's slot 7: view) -> the LED buffer: the chain first, nothing on the stack
    a.label("c_nsleds")
    imm32(1, NS); E(raw, str_lr(1, 12)); E(str_imm, 0, 1, 20)
    E(bl, prev["leds"])
    E(push_list, [4, 5, 6, 7]); E(mov_reg, 5, 0)
    imm32(0, NS); E(ldr_imm, 0, 0, 20); E(bl, "c_nsalt"); E(mov_reg, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "le_x", "hi")
    E(bl, "c_nsmz"); E(cmp_imm, 0, 0); E(b_cond, "le_x", "ne")
    E(bl, L["c_mcon"]); E(cmp_imm, 0, 0); E(b_cond, "le_m", "eq")
    E(ldrb_imm, 1, 0, 1); E(movs_imm, 2, F_SEL); E(tst_reg, 1, 2); E(b_cond, "le_x", "ne")           # a macro picked: its number on the pads
    a.label("le_m")
    E(ldrh_imm, 0, 5, 2 * PAD_ED); E(ldrh_imm, 1, 5, 2 * PAD_SD)                                   # the two pads moved
    E(strh_imm, 0, 5, 2 * ED2); E(strh_imm, 1, 5, 2 * PAD_SD2); E(movs_imm, 0, 0); E(strh_imm, 0, 5, 2 * PAD_SD)
    E(bl, L["c_mcsrc"]); E(cmp_imm, 0, 1); E(b_cond, "le_x", "hi")
    E(bl, L["c_mcon"]); E(cmp_imm, 0, 0); E(b_cond, "le_x", "ne")
    E(bl, "c_nspg"); E(mov_reg, 6, 0); E(movs_imm, 7, 0); E(ldr_label, 3, "t_col")
    a.label("le_p")
    E(adds_reg, 1, 3, 7); E(ldrb_imm, 0, 1, len(cols)); E(cmp_reg, 7, 6); E(b_cond, "le_w", "ne"); E(ldrb_imm, 0, 1, 0)
    a.label("le_w"); E(lsls_imm, 1, 7, 1); E(raw, h(0x5268))                                       # (strh r0, [r5, r1])
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "le_p", "lo")
    if V3:                                                                                         # (V3) pad 1 in the synth's colour
        E(ldr_label, 3, "t_syn"); E(adds_reg, 3, 3, 4); E(ldrb_imm, 0, 3, 0); E(cmp_imm, 6, 0); E(b_cond, "le_s", "eq"); E(ldrb_imm, 0, 3, 2)
        a.label("le_s"); E(strh_imm, 0, 5, 0); E(ldr_label, 3, "t_col")
    if V2:                                                                                         # (V2) pad 1: Macros 2's colour on it, its dim one with Shift
        E(ldrb_imm, 0, 3, 8); E(cmp_imm, 6, 8); E(b_cond, "le_8", "eq")
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "le_fl" if V3 else "le_x", "eq"); E(ldr_label, 3, "t_col"); E(ldrb_imm, 0, 3, 8 + len(cols))
        a.label("le_8"); E(strh_imm, 0, 5, 0)
    if V8:                                                                                         # (V8) the slot pads: in use bright, free dim, the picked one white
        a.label("le_fl"); E(bl, "c_nsshow"); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "le_x", "eq"); E(movs_imm, 7, 0)
        a.label("le_sl"); E(movs_imm, 1, 7); E(ands_reg, 1, 6); E(movs_imm, 0, 17); E(muls, 1, 0); E(lsls_imm, 0, 7, 2); E(adds_reg, 1, 1, 0); E(adds_imm8, 1, MAC0 + 3)
        E(bl, "c_nsget"); E(ldr_label, 3, "t_syn"); E(adds_reg, 3, 3, 4); E(ldrb_imm, 1, 3, 2); E(cmp_imm, 0, 64); E(b_cond, "le_sw", "eq"); E(ldrb_imm, 1, 3, 0)
        a.label("le_sw"); E(lsls_imm, 0, 7, 4); E(raw, h(0x5229)); E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "le_sl", "lo")   # (strh r1, [r5, r0])
        E(movs_imm, 0, 0x20); E(tst_reg, 6, 0); E(b_cond, "le_x", "eq")
        E(lsrs_imm, 0, 6, 3); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 4); E(movs_imm, 1, 1); E(raw, h(0x5229))
    elif V3:                                                                                       # (V3) an assignment's hint: pad 1 blinks in its page's colour
        a.label("le_fl"); E(bl, "c_nsfl"); E(lsrs_imm, 1, 0, 4); E(cmp_imm, 1, 1); E(b_cond, "le_x", "ne")
        E(ldr_label, 3, "t_syn"); E(adds_reg, 3, 3, 4); E(ldrb_imm, 1, 3, 0); E(movs_imm, 2, 8); E(tst_reg, 0, 2); E(b_cond, "le_h", "eq")
        E(ldr_label, 3, "t_col"); E(ldrb_imm, 1, 3, 8)
        a.label("le_h"); E(strh_imm, 1, 5, 0)
    a.label("le_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7]); imm32(1, NS); E(ldr_imm, 1, 1, 12); E(raw, h(0x4708))   # bx r1

    # ---- c_nsknob (the macro handlers' slot 4: handler, knob, delta)
    a.label("c_nsknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(cmp_imm, 5, 8); E(b_cond, "kn_f", "hs")
    E(bl, L["c_mcsrc"]); E(mov_reg, 4, 0); E(cmp_imm, 4, 1)
    if V3: E(b_cond, "kn_sy", "ls")
    if V7:                                                                                         # (V7) another view of a synth whose section page follows
        E(ldr_sp, 0, 0); E(bl, "c_nsfw"); E(mov_reg, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "kn_sy", "ls")
    if V3: E(b, "kn_ow"); a.label("kn_sy")                                                    # (V3) not a synth's alt page: MIDI 1 / 2's own synth?
    else: E(b_cond, "kn_f", "hi")
    E(bl, L["c_mcon"]); E(cmp_imm, 0, 0); E(b_cond, "kn_f", "ne")
    E(bl, "c_nsmz"); E(cmp_imm, 0, 0); E(b_cond, "kn_f", "ne")
    E(bl, "c_nsst"); E(mov_reg, 7, 0)                                                              # r7 = NS + 4 (macroed's accumulator: byte 3)
    if V3:                                                                                         # (V3) Clear / Duplicate / pad 1 held: kn_v3 (after kn_f)
        E(b, "kn_v3"); a.label("kn_nb")
    elif V2:                                                                                       # (V2) Clear / Duplicate held + a knob
        E(bl, "c_nsheld"); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "kn_nb", "eq"); E(mov_reg, 6, 0)
        E(bl, "c_nspg"); E(mov_reg, 2, 0)
        E(lsrs_imm, 1, 6, 1); E(b_cond, "kn_cl", "cs")                                              # (bit 0 = Clear -> carry)
        E(cmp_imm, 2, 0); E(b_cond, "kn_e", "eq"); E(cmp_imm, 2, 8); E(b_cond, "kn_e", "eq")           # Duplicate: a section page's parameter
        E(mov_reg, 1, 5); E(bl, "c_nsrow"); E(cmp_imm, 0, 0xFE); E(b_cond, "kn_e", "hs"); E(bl, "c_nsdup"); E(b, "kn_e")
        a.label("kn_cl")
        E(cmp_imm, 2, 8); E(b_cond, "kn_c8", "eq"); E(cmp_imm, 2, 0); E(b_cond, "kn_e", "ne")
        E(movs_imm, 1, 17); E(muls, 1, 5); E(adds_imm8, 1, MAC0 + 3); E(movs_imm, 2, 64); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(b, "kn_e")   # Clear on Macros: slot 1's depth 0
        a.label("kn_c8"); E(mov_reg, 1, 5); E(movs_imm, 2, 0xFF); E(bl, "c_nsxset"); E(b, "kn_e")      # Clear on Macros 2: the extra knob freed
        a.label("kn_nb")
    E(bl, "c_nspg"); E(mov_reg, 2, 0); E(cmp_imm, 2, 0)
    if V8:                                                                                         # (V8) Macros: this macro's slots on the pads for 2 s
        E(b_cond, "kn_pg8", "ne"); E(lsls_imm, 0, 4, 6); E(orrs_reg, 0, 5); E(movs_imm, 1, 0x80); E(orrs_reg, 0, 1); E(strb_imm, 0, 7, O_SH)
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 7, O_ST); E(b, "kn_f"); a.label("kn_pg8")
    else: E(b_cond, "kn_f", "eq")
    E(ldrb_imm, 1, 7, 4); E(cmp_reg, 1, 5); E(b_cond, "kn_k", "eq"); E(strb_imm, 5, 7, 4); E(movs_imm, 1, 0); E(strb_imm, 1, 7, 3)   # another knob: the accumulator from 0
    a.label("kn_k")
    E(mov_reg, 1, 5); E(bl, "c_nsrow"); E(cmp_imm, 0, 0xFE); E(b_cond, "kn_r", "lo"); E(b_cond, "kn_e", "hi")
    E(movs_imm, 0, MX_STEP); E(bl, L["c_mcacc"]); E(adds_reg, 2, 7, 4); E(ldrb_imm, 1, 2, 1); E(adds_reg, 1, 1, 0)   # the matrix slot
    E(b_cond, "kn_e", "mi"); E(cmp_imm, 1, MX_SLOTS); E(b_cond, "kn_e", "hs"); E(strb_imm, 1, 2, 1); E(b, "kn_e")
    a.label("kn_r")
    E(mov_reg, 5, 0); E(bl, "c_nsrng")                                                             # r5 = the row (the knob is done with)
    E(subs_reg, 1, 1, 0); E(adds_imm8, 1, 1); E(cmp_imm, 1, 64); E(b_cond, "kn_v", "hi")             # a list of n <= 64: a value every 128 / n events (2..16)
    E(movs_imm, 0, 128); E(raw, udiv(0, 0, 1)); E(cmp_imm, 0, 2); E(b_cond, "kn_v", "lo"); E(cmp_imm, 0, 16); E(b_cond, "kn_a", "ls"); E(movs_imm, 0, 16)
    a.label("kn_a"); E(bl, L["c_mcacc"]); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "kn_e", "eq")
    a.label("kn_v")
    E(mov_reg, 0, 5); E(bl, "c_nsval"); E(adds_reg, 3, 0, 6)                                       # r3 = the value + the step, inside lo..hi
    E(cmp_reg, 3, 1); E(b_cond, "kn_lo", "ge"); E(mov_reg, 3, 1)
    a.label("kn_lo"); E(cmp_reg, 3, 2); E(b_cond, "kn_hi", "le"); E(mov_reg, 3, 2)
    a.label("kn_hi"); E(cmp_reg, 3, 0); E(b_cond, "kn_e", "eq")
    if V9: E(mov_reg, 6, 3)                                                                        # (V9) the value kept (the delta is done with)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 3); E(bl, L["c_mcset"])
    if V9:                                                                                         # (V9) Macros 2: m2lanes records it
        E(bl, "c_nspg"); E(cmp_imm, 0, 8); E(b_cond, "kn_e", "ne")
        E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(mov_reg, 2, 6); E(ldr_sp, 3, 0); a.label("kn_m2"); E(bl, "c_nsret")
    a.label("kn_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])
    if V3:
        a.label("kn_v3")
        E(bl, "c_nsheld"); E(mov_reg, 3, 0)                                                        # (r6 = the delta: kept for kn_nb)
        E(lsrs_imm, 1, 3, 1); E(b_cond, "kn_d", "cc")                                              # Clear: Macros = the stock's, else nothing
        E(bl, "c_nspg"); E(cmp_imm, 0, 0)
        if V9:                                                                                     # (V9) Macros 2: m2lanes (left = the lane cleared, right = the patch's value)
            E(b_cond, "k3_f", "eq"); E(cmp_imm, 0, 8); E(b_cond, "k3_e", "ne")
            E(mov_reg, 1, 5); E(movs_imm, 2, 8); E(bl, "c_nsrow"); E(mov_reg, 3, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6)
            a.label("kn_m2c"); E(bl, "c_nsret"); E(b, "k3_e")
        else:
            E(b_cond, "k3_e", "ne"); E(b, "k3_f")
        a.label("kn_d"); E(lsrs_imm, 1, 3, 2); E(b_cond, "kn_p", "cc")                             # Duplicate: a section page's parameter assigned
        E(bl, "c_nspg"); E(mov_reg, 2, 0); E(cmp_imm, 2, 0); E(b_cond, "k3_e", "eq"); E(cmp_imm, 2, 8); E(b_cond, "k3_e", "eq")
        E(mov_reg, 1, 5); E(bl, "c_nsrow"); E(cmp_imm, 0, 0xFE); E(b_cond, "k3_e", "hs"); E(bl, "c_nsdup")
        E(cmp_imm, 0, 0x30); E(b_cond, "kn_h", "ne"); E(orrs_reg, 0, 5)
        a.label("kn_h"); E(ldr_sp, 1, 0); E(bl, "c_nsflash"); E(b, "k3_e")
        if V8:                                                                                     # (V8) a slot pad held: that slot of this knob's macro picked
            a.label("kn_p"); E(bl, L["c_mcsrc"]); E(cmp_imm, 0, 1); E(b_cond, "k3_nb", "hi")
            imm32(0, MGR + 0x84); E(ldr_imm, 0, 0, 0); imm32(1, 0x01010101); E(ands_reg, 0, 1); E(b_cond, "k3_nb", "eq")
            E(lsrs_imm, 1, 0, 1); E(b_cond, "kn_pk", "cc"); E(mov_reg, 6, 0)                        # pad 1 with Shift / Macros 2 before: that Macros 2 knob freed
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "kn_x8", "ne")
            E(bl, "c_nsst"); E(ldrb_imm, 0, 0, O_BEF); E(cmp_imm, 0, 8); E(b_cond, "kn_x8", "eq"); E(mov_reg, 0, 6)
            a.label("kn_pk"); E(movs_imm, 1, 0)
            a.label("kn_pl"); E(lsrs_imm, 2, 0, 1); E(b_cond, "kn_pf", "cs"); E(lsrs_imm, 0, 0, 8); E(adds_imm8, 1, 1); E(b, "kn_pl")
            a.label("kn_pf"); E(lsls_imm, 6, 1, 3); E(orrs_reg, 6, 5); E(lsls_imm, 0, 4, 6); E(orrs_reg, 6, 0); E(movs_imm, 0, 0xA0); E(orrs_reg, 6, 0)
            E(bl, "c_nsst"); E(strb_imm, 6, 0, O_PK); E(lsrs_imm, 1, 6, 3); E(movs_imm, 2, 3); E(ands_reg, 1, 2); E(b_cond, "k3_e", "ne")
            E(ldrb_imm, 3, 0, O_BEF); E(bl, "c_nsput"); E(b, "k3_e")                                # pad 1: the page before its press back
            a.label("kn_x8"); E(movs_imm, 3, 8); E(bl, "c_nsput"); E(mov_reg, 1, 5); E(movs_imm, 2, 0xFF); E(bl, "c_nsxset")
            E(movs_imm, 0, 0x28); E(orrs_reg, 0, 5); E(ldr_sp, 1, 0); E(bl, "c_nsflash"); E(b, "k3_e")
        else:
            a.label("kn_p")
            if V7: E(bl, L["c_mcsrc"]); E(cmp_imm, 0, 1); E(b_cond, "k3_nb", "hi")                    # (V7) the free gesture: the alt page only
            imm32(0, MGR + 0x84); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 1); E(b_cond, "k3_nb", "cc")   # pad 1 held: that knob freed
            E(movs_imm, 6, 8); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "kn_t", "ne")
            E(bl, "c_nsst"); E(ldrb_imm, 0, 0, O_BEF); E(cmp_imm, 0, 8); E(b_cond, "kn_t", "eq"); E(movs_imm, 6, 0)
            a.label("kn_t"); E(mov_reg, 3, 6); E(bl, "c_nsput"); E(cmp_imm, 6, 8); E(b_cond, "kn_x8", "eq")
            if V4:                                                                                     # (V4) the macro's 4 slots: destination 0, 0..127, depth 64
                E(movs_imm, 1, 17); E(muls, 1, 5); E(adds_imm8, 1, MAC0); E(movs_imm, 6, 0)
                a.label("kn_cl4"); E(ldr_label, 3, "t_dupv"); E(movs_imm, 2, 3); E(ands_reg, 2, 6); E(adds_imm8, 2, 4); E(ldrb_reg, 2, 3, 2)
                E(push_list, [1]); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(pop_list, [1]); E(adds_imm8, 1, 1); E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "kn_cl4", "lo")
                E(movs_imm, 6, 0); E(b, "kn_fr")
            else:
                E(movs_imm, 1, 17); E(muls, 1, 5); E(adds_imm8, 1, MAC0 + 3); E(movs_imm, 2, 64); E(mov_reg, 0, 4); E(bl, L["c_mcset"]); E(b, "kn_fr")
            a.label("kn_x8"); E(mov_reg, 1, 5); E(movs_imm, 2, 0xFF); E(bl, "c_nsxset")
            a.label("kn_fr"); E(movs_imm, 0, 0x20); E(orrs_reg, 0, 5); E(orrs_reg, 0, 6); E(ldr_sp, 1, 0); E(bl, "c_nsflash"); E(b, "k3_e")
        a.label("k3_e"); E(b, "kn_e")
        a.label("k3_f"); E(b, "kn_f")
        a.label("k3_nb"); E(b, "kn_nb")
        # (V3) MIDI 1 / 2's own synth: pad 1 held + knob = the slot freed; Duplicate + knob: the hint, then p4dest (the registers back at kn_f)
        a.label("kn_ow")
        E(ldr_sp, 0, 0); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); E(b_cond, "o3_f", "hi"); E(mov_reg, 4, 0)
        E(bl, "c_nsheld"); E(mov_reg, 7, 0); E(mov_reg, 0, 4); E(bl, L["c_p4pg"]); E(mov_reg, 6, 0)
        E(lsrs_imm, 0, 7, 1); E(b_cond, "o3_f", "cs")                                              # Clear: vcf21's
        imm32(0, MGR + 0x84); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 1); E(b_cond, "ow_d", "cc")
        E(cmp_imm, 6, 0); E(b_cond, "o3_f", "eq")                                                 # pad 1 held: page 4's / the non-sequenceable slot freed
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ow_n", "ne"); E(cmp_imm, 6, 2); E(b_cond, "ow_n", "eq")
        E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(movs_imm, 6, 0); E(b, "ow_fr")
        a.label("ow_n"); E(mov_reg, 0, 4); E(bl, L["c_vrow2"]); E(movs_imm, 6, 8)
        a.label("ow_fr"); E(movs_imm, 1, 0); E(strb_reg, 1, 0, 5)
        E(movs_imm, 0, 0x60); E(orrs_reg, 0, 5); E(orrs_reg, 0, 6); E(ldr_sp, 1, 0); E(bl, "c_nsflash"); E(b, "o3_e")
        a.label("ow_d"); E(lsrs_imm, 0, 7, 2); E(b_cond, "o3_f", "cc")                              # Duplicate: on the two pages nothing
        E(cmp_imm, 6, 0); E(b_cond, "o3_e", "ne")
        for fn in ("c_von", "c_edact", "c_sdview"):
            E(mov_reg, 0, 4); E(bl, L[fn]); E(cmp_imm, 0, 0); E(b_cond, "o3_f", "eq" if fn == "c_von" else "ne")
        E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(lsls_imm, 6, 0, 4); E(adds_reg, 6, 6, 5)           # p4dest's code of this knob
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ow_s", "eq"); E(adds_imm8, 6, 8)
        a.label("ow_s"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, L["c_vkc"]); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "o3_f", "eq")
        E(bl, L["c_p4idx"]); imm32(1, L["t_dcode"]); E(ldrb_reg, 0, 1, 0); E(cmp_reg, 0, 6); E(b_cond, "o3_f", "ne")
        E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(mov_reg, 7, 0); E(mov_reg, 0, 4); E(bl, L["c_vrow2"]); E(mov_reg, 4, 0)   # r7 page 4's row, r4 the other
        for code, row, lab_ in ((6, 7, "ow_h4"), (6, 4, "ow_h8"), (None, 7, "ow_h4"), (None, 4, "ow_h8")):   # the holder, else the first free slot
            E(mov_reg, 0, row)
            if code is None: E(movs_imm, 1, 0)
            else: E(mov_reg, 1, code)
            E(bl, L["c_p4has"]); E(cmp_imm, 0, 8); E(b_cond, lab_, "ne")
        E(movs_imm, 0, 0x70); E(orrs_reg, 0, 5); E(b, "ow_fl")                                     # no room: the turned knob orange
        a.label("ow_h8"); E(movs_imm, 1, 0x58); E(orrs_reg, 0, 1); E(b, "ow_fl")
        a.label("ow_h4"); E(movs_imm, 1, 0x50); E(orrs_reg, 0, 1)
        a.label("ow_fl"); E(ldr_sp, 1, 0); E(bl, "c_nsflash"); E(b, "o3_f")
        a.label("o3_e"); E(b, "kn_e")
        a.label("o3_f"); E(b, "kn_f")

    # ---- c_nskleds (the macro handlers' slot 7: handler) -> the knob LEDs: the chain first, nothing on the stack
    a.label("c_nskleds")
    imm32(1, NS); E(raw, str_lr(1, 16)); E(str_imm, 0, 1, 24)
    E(bl, prev["kleds"])
    E(push_list, [4, 5, 6, 7]); E(mov_reg, 5, 0)
    E(bl, L["c_mcsrc"]); E(mov_reg, 4, 0); E(cmp_imm, 4, 1)
    if V3: E(b_cond, "kl_sy", "ls")
    if V7:                                                                                         # (V7) another view of a synth whose section page follows
        imm32(0, NS); E(ldr_imm, 0, 0, 24); E(bl, "c_nsfw"); E(mov_reg, 4, 0); E(cmp_imm, 4, 1); E(b_cond, "kl_sy", "ls")
    if V3: E(b, "kl_fl"); a.label("kl_sy")                                                    # (V3) another track: its hint only
    else: E(b_cond, "kl_x", "hi")
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")                   # the handler of that synth only (macroed's check)
    E(ldr_imm, 0, 0, 0x40); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq"); E(ldr_imm, 0, 0, 0x2C); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")
    E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(raw, h(0xF8D0) + h(0 << 12 | 0x148)); imm32(1, NS); E(ldr_imm, 1, 1, 24); E(cmp_reg, 0, 1); E(b_cond, "kl_x", "ne")
    E(bl, L["c_mcon"]); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "ne")
    E(bl, "c_nsmz"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "ne")
    E(bl, "c_nspg"); E(mov_reg, 6, 0); E(cmp_imm, 6, 0)
    if V3: E(b_cond, "kl_pg", "ne"); E(b, "kl_m0" if V5 else "kl_fl"); a.label("kl_pg")
    else: E(b_cond, "kl_x", "eq")
    E(movs_imm, 7, 0)
    a.label("kl_l")
    E(mov_reg, 1, 7); E(mov_reg, 2, 6); E(bl, "c_nsrow"); E(movs_imm, 1, 0); E(cmp_imm, 0, 0xFE); E(b_cond, "kl_w", "hi"); E(b_cond, "kl_r", "lo")
    imm32(1, NS + 5); E(ldrb_reg, 0, 1, 4); E(movs_imm, 1, 6); E(muls, 0, 1); E(b, "kl_c")         # the slot: 6 x slot (0..114)
    a.label("kl_r")
    E(bl, "c_nsval"); E(subs_reg, 0, 0, 1); E(movs_imm, 3, 127); E(muls, 0, 3); E(subs_reg, 2, 2, 1)   # (value - lo) x 127 / (hi - lo)
    E(b_cond, "kl_c", "eq"); E(raw, udiv(0, 0, 2))
    a.label("kl_c")                                                                                # r0 = 0..127: the page colour, that bright
    E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(ldr_label, 1, "t_col"); E(ldrb_reg, 1, 1, 6); E(orrs_reg, 1, 0)
    a.label("kl_w"); E(lsls_imm, 0, 7, 1); E(raw, h(0x5229))                                       # (strh r1, [r5, r0])
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "kl_l", "lo")
    if V3: E(b, "kl_fl")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7]); imm32(1, NS); E(ldr_imm, 1, 1, 16); E(raw, h(0x4708))
    if V3:                                                                                         # (V3) the hint: its knob blinks (white / red / orange)
        if V5:                                                                                     # (V5) Macros: the synth's colour, bright as each macro's position
            a.label("kl_m0"); E(bl, "c_nsheld"); E(lsrs_imm, 0, 0, 1); E(b_cond, "kl_fl", "cs"); E(movs_imm, 7, 0)
            a.label("kl_ml"); E(movs_imm, 1, 17); E(muls, 1, 7); E(adds_imm8, 1, MAC0 - 1); E(bl, "c_nsget")
            E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(ldr_label, 1, "t_syn"); E(ldrb_reg, 1, 1, 4); E(orrs_reg, 1, 0)
            E(lsls_imm, 0, 7, 1); E(raw, h(0x5229)); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "kl_ml", "lo")   # (strh r1, [r5, r0])
        a.label("kl_fl"); E(bl, "c_nsst"); E(mov_reg, 7, 0)
        E(ldr_imm, 1, 7, O_FH); E(ldr_imm, 2, 7, 20); E(cmp_reg, 1, 2); E(b_cond, "kl_x", "ne")       # another handler's hint (NS + 24 = this one)
        E(ldrb_imm, 6, 7, O_FL); E(ldr_imm, 1, 7, O_FT); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(subs_reg, 2, 2, 1); E(lsrs_imm, 2, 2, 7)
        E(ldrb_imm, 3, 7, O_SV); E(movs_imm, 1, 7); E(ands_reg, 1, 6); E(lsls_imm, 1, 1, 1)   # r1 = 2 x the hint's knob, r3 = the LED put aside
        E(cmp_imm, 2, 5); E(b_cond, "kl_end", "hs"); E(cmp_imm, 6, 0); E(b_cond, "kl_end", "eq")
        E(cmp_imm, 3, 0); E(b_cond, "kl_sv", "eq"); E(movs_imm, 0, 0x80); E(eors_reg, 3, 0); E(lsls_imm, 3, 3, 1); E(cmp_reg, 3, 1); E(b_cond, "kl_on", "eq")
        E(push_list, [1, 2]); E(bl, "kl_rs"); E(pop_list, [1, 2])                                  # another knob's: back, this one put aside
        a.label("kl_sv"); E(raw, h(0x5A68)); E(strh_imm, 0, 7, O_SVH); E(lsrs_imm, 0, 1, 1); E(movs_imm, 3, 0x80); E(orrs_reg, 0, 3); E(strb_imm, 0, 7, O_SV)   # (ldrh r0, [r5, r1])
        a.label("kl_on"); E(lsrs_imm, 2, 2, 1); E(b_cond, "kl_off", "cs")
        E(lsrs_imm, 2, 6, 4); E(movs_imm, 3, 3); E(ands_reg, 2, 3); E(subs_imm8, 2, 1); E(ldr_label, 3, "t_flc"); E(ldrb_reg, 3, 3, 2)
        E(movs_imm, 2, 0x81); E(lsls_imm, 2, 2, 8); E(orrs_reg, 3, 2); E(raw, h(0x526B)); E(b, "kl_x")   # (strh r3, [r5, r1])
        a.label("kl_off"); E(ldrh_imm, 3, 7, O_SVH); E(raw, h(0x526B)); E(b, "kl_x")
        a.label("kl_end"); E(cmp_imm, 3, 0); E(b_cond, "kl_x", "eq"); E(bl, "kl_rs"); E(b, "kl_x")
        # kl_rs(r7 = NS + 4, r5 = the LEDs): the LED put aside back, none put aside; clobbers r0, r1, r3
        a.label("kl_rs"); E(ldrb_imm, 0, 7, O_SV); E(movs_imm, 1, 7); E(ands_reg, 1, 0); E(lsls_imm, 1, 1, 1); E(ldrh_imm, 3, 7, O_SVH); E(raw, h(0x526B))
        E(movs_imm, 0, 0); E(strb_imm, 0, 7, O_SV); E(raw, h(0x4770))

    # ---- data
    a.label("t_col"); E(raw, bytes(c[0] for c in cols) + bytes(c[1] for c in cols))
    a.label("t_rows"); E(raw, bytes(r for page in ROWS for r in page))
    a.label("t_mx"); E(raw, bytes(MX_MAP))
    if V2: a.label("t_drow"); E(raw, bytes(DROW))
    if V2 and FIX: a.label("t_dupv"); E(raw, bytes([0xFF, 0, 127, 127]) + (bytes([0, 0, 127, 64]) if V4 else b""))   # (V4) + an unused slot
    if V3: a.label("t_syn"); E(raw, bytes(SYN_COL)); a.label("t_flc"); E(raw, bytes(FL_COL) + bytes(1))
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add places it): heads of the synths' Preset view slots 0 / 7 and the macro handlers' slots 4 / 7."""
    import fm8store as FS
    assert not FIX or XB + 2 <= FS.PBYTE0, "the extra knobs' bytes overlap fm8store's project block (2 + 30 bytes from byte 8)"
    import ct_fw
    BASE = ct_fw.APP_BASE
    R = report
    lab = lambda mod, n: int(R[mod]["labels"][n], 16)
    L = dict(c_sdscr=lab("vcf20", "c_sdscr"), c_shift=lab("sc15", "c_shift"), c_gst=lab("sc14", "c_gst"), c_synth=lab("sc15", "c_synth"), c_mcsrc=lab("macroed", "c_mcsrc"), c_mcon=lab("macroed", "c_mcon"),
             c_mcacc=lab("macroed", "c_mcacc"), c_mcset=lab("macroed", "c_mcset"), c_mzst=lab("morphz", "c_mzst"), c_mzmv=lab("morphz", "c_mzmv"))
    if V3:
        L.update({k: lab("vcf20", k) for k in ("c_vtrack", "c_von", "c_edact", "c_sdview", "c_vpage", "c_vrow", "c_vrow2", "c_vkc")})
        L.update({k: lab("p4dest", k) for k in ("c_p4pg", "c_p4has", "c_p4idx")}); L["t_dcode"] = lab("modmx", "t_dcode")
    rd = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0] & ~1
    prev = dict(pad=rd(SP_VT), leds=rd(SP_VT + 4 * 7), knob=rd(AC64_VT + 4 * 4), kleds=rd(AC64_VT + 4 * 7))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for slot, lb in ((SP_VT, "c_nspad"), (SP_VT + 4 * 7, "c_nsleds"), (AC64_VT + 4 * 4, "c_nsknob"), (AC64_VT + 4 * 7, "c_nskleds")):
        struct.pack_into("<I", img, slot - BASE, labels[lb] | 1)
    report["novasec"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                             ram=hex(NS), bytes=len(code))
    return labels, code, prev
