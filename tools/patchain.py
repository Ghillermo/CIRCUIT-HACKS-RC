"""SC40.5 (the user, 2026-10-13 / 14): pattern chains.  Every pattern of every track can hold a rule «play n times, then jump to B; the next
time, to C»: AAABAAAC (n = 3), AAAAAAAAB (n = 8, no C), ABAC (n = 1).  B and C play once and the track comes back to the pattern that sent it
there (unless they hold a rule of their own, which then goes on).  Each scene remembers, per track, whether the track follows these rules or the
stock chain; a scene ends when its longest chain ends (the stock's rule: the eight tracks have finished) and can repeat up to 8 times.

Where it lives
  * the rule: bytes 4 / 5 / 6 of the pattern's 40 settings bytes in the project record (n 1..8, B + 1, C + 1 or 0); bytes 4..7 are zero in the
    14 080 patterns of the 220 sessions of the user's card, the device saves them and copies them with the pattern (SC403D on the unit);
  * per project, in the last 1000 bytes of the record (saved and loaded by the stock, SC403D): "CTC1", a checksum, the tracks that follow the
    rules, 16 scene flags, 16 scene repeats (a tail without the mark or with a wrong sum = none of ours: the Shadow Child pack has garbage there);
  * the running state (counts, the pattern to come back to, which of B / C is next, the edit mode) in 64 bytes further on in that tail, in RAM:
    it is zeroed whenever a project is loaded (persist19's hook at the end of the stock's "apply session", in front of it; the mark «made for
    this project» is the last free byte of the Master FX block's idle LED buffer, c_gst() + 143) and takes no RAM.

The sequencer (the engine 0x20038EC0; the track advance 0x0802CB3C runs for the playing store, fp = 0, and for the look-ahead store, fp = 1):
  * 0x0802CD4A (the choice of the next pattern when a pattern ends: «forced or current = last of the chain -> first, else current + 1») ->
    bl c_pcnext; b 0x0802CD66.  A scene change takes the track's flag of that scene; a forced restart (a new chain, a scene) clears the track's
    state; the look-ahead call computes the same answer without changing anything.
  * 0x0802C65E (in 0x0802C5F8: «the track ends its chain here» = no chain pending and the pattern is the last of its chain) -> bl c_pcend: for a
    track that follows a rule, the chain ends when the track comes back from the last jump of the cycle (from C, or from B when there is no C).
  * 0x0802C6A6 (the next scene) -> c_pcscn: the current scene again while it has repeats left; the committing call (0x0802C74C) counts them.
  * the scene save (the first of its eight writes, 0x0802DC90) -> c_pcssave: the scene takes the tracks that follow the rules now; saved again
    within 1.5 s = one repeat more (up to 8), else once; the scene copy (0x0802DE42) -> c_pcscopy copies both.

The Patterns view (button 13, vtable 0x0805A5F0: 8 columns = the tracks, 4 rows = patterns 1-4 or 5-8 with Octave down / up; Clear + pad
clears, Duplicate copies, Shift + pad switches at once; with Shift the stock ignores the Octave buttons there):
  * Shift + Octave up = the chain edit (Octave up white); Shift + Octave down, or any view button, leaves it;
  * in the edit: a pattern = A (it is selected as the stock does and its track follows the rules from now on); A again = one play more (n, the
    knob LEDs count them); another pattern of the track = B, the next one = C; Clear + pattern = its rule gone.  LEDs: a pattern with a rule
    white (dim when its track follows the stock chain); the one being edited yellow, its B green, its C red;
  * out of the edit a plain pattern press is the stock's and puts the track back on the stock chain; Clear + pad also clears the rule.

SC40.6 (use_v2(); the user, 2026-10-14, after SC40.5):
  * «al pulsar Shift, el toggle utilizable se ilumina en amarillo: una convención para todos los atajos disponibles»: with Shift held in the
    Patterns view the Octave button that does something is yellow (up out of the edit, down in it); in the edit Octave up is green;
  * the Mixer view (its two lower rows = the scenes; not in its Master FX page): a saved scene whose tracks run a rule (its flag and a rule on
    the first pattern of the track's chain there) is peach, the current one brighter; the track pads of the tracks that run a rule now blink;
  * «Shift + pads 9-16 fijan 1-8 repeticiones de la escena actual (número de pad seleccionado iluminado)»: with Shift held the second row is
    yellow, the repeats of the current scene green; saving a scene again no longer changes its repeats.  While a scene repeats the stock does
    not apply it again (the mutes are those the user left) and every track goes on where it was: only the scene's first play restarts them.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import ldrh_reg  # noqa: E402
from thumb import (Asm, add_sp_imm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, ldr_imm,  # noqa: E402
                   ldr_sp, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, nop, orrs_reg,
                   pop_list, push_list, raw, h, str_imm, str_sp, strb_imm, strb_reg, strh_reg, sub_sp_imm, subs_imm3, subs_imm8, subs_reg, tst_reg)
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import mpatch as MP  # noqa: E402

SESSION_OBJ, TAIL = P19.SESSION_OBJ, 0x27024
MGR = 0x20040B10
PV, PV_VT, PV_PAD, TRACKFN = 0x200441A8, 0x0805A5F0, 0x080446E6, 0x0804423C     # the Patterns view, its pad handler, pad -> track
BTN_ENTRY = MP.BTN_ENTRY
NEXT_HOOK, NEXT_BACK = 0x0802CD4A, 0x0802CD66
NEXT_OLD = bytes.fromhex("9df8180018b99df80210894502d18df8018003e009f101098df80190")
END_HOOK, END_OLD = 0x0802C65E, bytes.fromhex("baf1000f")                       # cmp.w sl, #0
SCN_FN, SCN_BODY, SCN_OLD = 0x0802C6A6, 0x0802C6AC, bytes.fromhex("f8b500f12c05")   # push {r3-r7, lr}; add.w r5, r0, #0x2c
SCN_COMMIT = 0x0802C74C                                                         # bl 0x0802C6A6 where the stock takes the next scene for good
SC_SET, SC_SAVE, SC_COPY = 0x0802B2CC, 0x0802DC90, 0x0802DE42                   # the scene store's setter; its first call of the save, of the copy
MAGIC = struct.unpack("<I", b"CTC1")[0]
# the persistent part (offsets from the tail): the checksum covers 5..47
P_SUM, P_LIVE, P_FLAGS, P_REPS, P_END, SUM_XOR = 4, 5, 8, 24, 48, 0x5A
# the running part (offsets from the tail + 64)
SCR, SCR_LEN = 64, 64
S_EDIT, S_FOCUS, S_A, S_STAGE, S_LIVE, S_REPC, S_LASTSC, S_LASTT, S_CNT, S_RET, S_TOG = 0, 1, 2, 3, 4, 5, 6, 7, 8, 16, 24
ST_INIT, INIT_TAG = 143, 0xC7                                 # c_gst() + 143 (the last free byte of the idle LED buffer): the running part belongs to the loaded project
SET_NOTE, SET_DRUM = 0x380 + 4, 0x80 + 4                      # byte 4 of the settings in a note / drum pattern
REC_SYNTH, REC_MIDI, REC_DRUM, PAT_NOTE, PAT_DRUM = 0x2E4, 0x1A27C, 0xCD74, 0xCA8, 0x6A8
MAX_N, REP_MAX, REP_WINDOW = 8, 8, 6                          # (the window in 256 ms units)
COL_RULE, COL_OFF, COL_A, COL_B, COL_C = 0x01, 0x02, 0x2D, 0x17, 0x53
KNOB_ON, LED_UP, BTN_DOWN, BTN_UP = 0x01 | (127 + 2) << 8, 52, 19, 20
ENG, MIXV, MIX_VT = 0x20038EC0, 0x200447D4, 0x0805A668      # the engine, the Mixer view and its vtable
SC_FIRST = 0x0802B336                                         # (scene store [ENG + 0x24], scene, track) -> the first pattern of the track's chain there
COL_SHIFT, COL_MODE, COL_SEL, COL_SC, COL_SCCUR = 0x2D, 0x17, 0x17, 0x6B, 0x6A   # a shortcut that Shift offers (yellow), the edit, the chosen repeats, a scene with rules / the current one
LED_DOWN = 51
PLAY_STORE = 0x20011034                                       # the transport (mutate39.PLAY_STORE): parameter 0 = running
V2 = False
V3 = False                                                    # SC40.9: one chain mode for the whole project (see use_v3)
RULECHK = False                                               # SC41.2: c_pcrule refuses a track or a pattern out of 0..7 (see use_rulecheck)


def use_v2():
    global V2
    V2 = True


def use_rulecheck():
    """SC41.2 (a review of SC41.1 in emulation: the stock's tick, given a wrong engine, handed the end-of-pattern hook a drum pattern 0x84, and
    c_pcrule turned it into an address past the end of the RAM, 0x2005F494: a bus fault on the unit): c_pcrule answers 0 («no rule») for a track or
    a pattern outside 0..7.  Its callers already treat 0 as «the stock's»: the chains, the play orders, the Patterns view's LEDs."""
    global RULECHK
    RULECHK = True


def use_v3():
    """SC40.9 (the user, 2026-10-14, after SC40.8 on the unit: «todo ok, pero no permite mezclar escenas con cadenas y escenas normales» ->
    «quiero un modo global»): Shift + Octave up / down in the Patterns view = the chain mode on / off for every track at once (no more one
    track at a time); it stays on when the view is left; a scene remembers the mode it was saved in and puts it back when it starts (playing:
    in the track advance; stopped: from the LED task, when the current scene changes).  A project without anything of ours, and its scenes,
    start in the normal mode.  In the mode a pattern press edits the rules as before; Clear + a pattern with a rule = the rule gone, without
    one = the stock's clear; a track that the mode leaves on a B / C pattern goes back to its A.  The stock's Clear of a pattern also clears
    its play order (byte 7 of the settings, tools/playmode.py)."""
    global V2, V3
    V2 = V3 = True


INV = dict(eq="ne", ne="eq", lo="hs", hs="lo", hi="ls", ls="hi", ge="lt", lt="ge", gt="le", le="gt", mi="pl", pl="mi")


def rule_offset(track, pattern):
    """Offset in the record of the rule (3 bytes) of a pattern."""
    i = track * 8 + pattern
    if i < 16: return REC_SYNTH + i * PAT_NOTE + SET_NOTE
    if i < 32: return REC_MIDI + (i - 16) * PAT_NOTE + SET_NOTE
    return REC_DRUM + (i - 32) * PAT_DRUM + SET_DRUM


def checksum(tail): return (sum(tail[P_LIVE:P_END]) ^ SUM_XOR) & 0xFF
def ldrb_sp(rt, off): return h(0xF89D) + h(rt << 12 | off)
def strb_sp(rt, off): return h(0xF88D) + h(rt << 12 | off)
def popw(regs, lr=False, pc=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0) | (1 << 15 if pc else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
POP_LR, BX_LR = h(0xF85D) + h(0xEB04), h(0x4770)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def get(store, k): imm32(0, store); E(movs_imm, 1, k); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    t_eq = base; E(raw, bytes(range(8)) + b"\xFF\xFF\xFF\xFF")

    # ---- c_pcsumv (r0 = the tail) -> r0 = the checksum its persistent part should carry; clobbers r1-r3
    a.label("c_pcsumv")
    E(movs_imm, 1, P_LIVE); E(movs_imm, 2, 0)
    a.label("sv_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, P_END); E(b_cond, "sv_l", "lo")
    E(movs_imm, 0, SUM_XOR); E(eors_reg, 0, 2); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24); E(raw, BX_LR)

    # ---- c_pcvalid (r0 = the tail) -> r0 = 1 when its persistent part is ours (the mark and the sum); clobbers r1-r3
    a.label("c_pcvalid")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(ldr_imm, 0, 4, 0); imm32(1, MAGIC); E(cmp_reg, 0, 1); E(b_cond, "va_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pcsumv"); E(ldrb_imm, 1, 4, P_SUM); E(cmp_reg, 0, 1); E(b_cond, "va_n", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("va_n"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pcsum (r0 = the tail): its checksum written; clobbers r0-r3
    a.label("c_pcsum")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_pcsumv"); E(strb_imm, 0, 4, P_SUM)
    E(pop_list, [4], pc=True)

    # ---- c_pcfix (r0 = the tail): a persistent part that is not ours becomes an empty one of ours (every track of every scene follows the
    #      rules, every scene plays once); clobbers r0-r3
    a.label("c_pcfix")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_pcvalid"); E(cmp_imm, 0, 0); E(b_cond, "fx_x", "ne")
    imm32(1, MAGIC); E(str_imm, 1, 4, 0)
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, 6); E(strb_imm, 0, 4, 7)
    E(movs_imm, 1, SCR + S_LIVE); E(ldrb_reg, 0, 4, 1); E(strb_imm, 0, 4, P_LIVE)
    E(movs_imm, 0, 0 if V3 else 0xFF); E(movs_imm, 1, P_FLAGS)
    a.label("fx_a"); E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, P_REPS); E(b_cond, "fx_a", "lo")
    E(movs_imm, 0, 1)
    a.label("fx_b"); E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, P_REPS + 16); E(b_cond, "fx_b", "lo")
    E(movs_imm, 0, 0)
    a.label("fx_c"); E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, P_END); E(b_cond, "fx_c", "lo")
    E(mov_reg, 0, 4); E(bl, "c_pcsum")
    a.label("fx_x"); E(pop_list, [4], pc=True)

    # ---- c_pcmir (r0 = the tail): the tracks that follow the rules into the persistent part, when it is ours; clobbers r0-r3
    a.label("c_pcmir")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_pcvalid"); E(cmp_imm, 0, 0); E(b_cond, "mi_x", "eq")
    E(movs_imm, 1, SCR + S_LIVE); E(ldrb_reg, 0, 4, 1); E(strb_imm, 0, 4, P_LIVE)
    E(mov_reg, 0, 4); E(bl, "c_pcsum")
    a.label("mi_x"); E(pop_list, [4], pc=True)

    # ---- c_pcst() -> r0 = the tail of the loaded project's record, its running part ready (zeroed after a load; the tracks that follow the
    #      rules from the project, all of them when it has nothing of ours); 0 without a record or without the state block; clobbers r1-r3
    a.label("c_pcst")
    E(push_list, [4, 5, 6], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "st_0", "eq")
    E(adds_imm8, 0, ST_INIT); E(mov_reg, 4, 0)
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "st_0", "eq")
    imm32(1, TAIL); E(adds_reg, 5, 0, 1)
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, INIT_TAG); E(b_cond, "st_ok", "eq")
    E(movs_imm, 0, INIT_TAG); E(strb_imm, 0, 4, 0)
    E(movs_imm, 0, 0); E(movs_imm, 1, SCR)
    a.label("st_z"); E(strb_reg, 0, 5, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, SCR + SCR_LEN); E(b_cond, "st_z", "lo")
    E(mov_reg, 0, 5); E(bl, "c_pcvalid")
    if V3:                                                                            # one mode: all the tracks or none; a project without ours: none
        E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "st_w", "eq"); E(ldrb_imm, 1, 5, P_LIVE); E(cmp_imm, 1, 0); E(b_cond, "st_w", "eq"); E(movs_imm, 1, 0xFF)
        a.label("st_w"); E(movs_imm, 0, SCR + S_LIVE); E(strb_reg, 1, 5, 0)
        E(movs_imm, 0, 1); E(ands_reg, 1, 0); E(movs_imm, 0, SCR + S_EDIT); E(strb_reg, 1, 5, 0)
    else:
        E(movs_imm, 1, 0xFF); E(cmp_imm, 0, 0); E(b_cond, "st_w", "eq"); E(ldrb_imm, 1, 5, P_LIVE)
        a.label("st_w"); E(movs_imm, 0, SCR + S_LIVE); E(strb_reg, 1, 5, 0)
    a.label("st_ok"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6], pc=True)
    a.label("st_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pcload (at the end of the stock's "apply session", in front of persist19's): the running part is to be made again
    a.label("c_pcload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "ld_x", "eq")
    E(adds_imm8, 0, ST_INIT); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    a.label("ld_x"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])

    # ---- c_pcrule (r0 = track, r1 = pattern) -> r0 = the address of the pattern's rule (n, B + 1, C + 1), 0 without a record; clobbers r1-r3
    a.label("c_pcrule")
    if RULECHK: E(cmp_imm, 0, 8); E(b_cond, "ru_0", "hs"); E(cmp_imm, 1, 8); E(b_cond, "ru_0", "hs")
    E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 1)
    E(cmp_imm, 0, 32); E(b_cond, "ru_n", "lo")
    E(subs_imm8, 0, 32); imm32(1, PAT_DRUM); imm32(2, REC_DRUM + SET_DRUM); E(b, "ru_j")
    a.label("ru_n")
    imm32(1, PAT_NOTE); imm32(2, REC_SYNTH + SET_NOTE); E(cmp_imm, 0, 16); E(b_cond, "ru_j", "lo")
    E(subs_imm8, 0, 16); imm32(2, REC_MIDI + SET_NOTE)
    a.label("ru_j"); E(muls, 0, 1); E(adds_reg, 0, 0, 2)
    imm32(1, SESSION_OBJ); E(ldr_imm, 1, 1, 0x14); E(cmp_imm, 1, 0); E(b_cond, "ru_0", "eq")
    E(adds_reg, 0, 0, 1); E(raw, BX_LR)
    a.label("ru_0"); E(movs_imm, 0, 0); E(raw, BX_LR)

    # ---- c_pcget (r0 = track, r1 = pattern) -> r0 = n | (B + 1) << 8 | (C + 1) << 16 of a rule that can run, else 0; clobbers r1-r3
    a.label("c_pcget")
    E(push_list, [3, 4], lr=True)
    E(mov_reg, 4, 1); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); E(b_cond, "ge_0", "eq")
    E(ldrb_imm, 1, 0, 0); E(ldrb_imm, 2, 0, 1); E(ldrb_imm, 3, 0, 2)
    E(cmp_imm, 1, 0); E(b_cond, "ge_0", "eq"); E(cmp_imm, 1, MAX_N); E(b_cond, "ge_0", "hi")
    E(cmp_imm, 2, 0); E(b_cond, "ge_0", "eq"); E(cmp_imm, 2, 8); E(b_cond, "ge_0", "hi"); E(cmp_imm, 3, 8); E(b_cond, "ge_0", "hi")
    E(subs_imm3, 0, 2, 1); E(cmp_reg, 0, 4); E(b_cond, "ge_0", "eq")                 # B = the pattern itself
    E(lsls_imm, 2, 2, 8); E(orrs_reg, 1, 2); E(lsls_imm, 3, 3, 16); E(orrs_reg, 1, 3); E(mov_reg, 0, 1)
    E(pop_list, [3, 4], pc=True)
    a.label("ge_0"); E(movs_imm, 0, 0); E(pop_list, [3, 4], pc=True)

    # ---- c_pczr (r0 = track, r1 = pattern): its rule gone; clobbers r0-r3
    a.label("c_pczr")
    E(push_list, [4], lr=True)
    E(bl, "c_pcrule"); E(cmp_imm, 0, 0); E(b_cond, "zr_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 2)
    a.label("zr_x"); E(pop_list, [4], pc=True)

    # ---- c_pcstep (r0 = the tail, r1 = track, r2 = the pattern that ends, r3 = 1 to move the state on) -> r0 = the next pattern by the
    #      rules, 0xFF = the stock's choice
    a.label("c_pcstep")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 6, 0); E(mov_reg, 4, 1); E(mov_reg, 5, 2); E(str_sp, 3, 0)
    if V3:                                                                            # the mode is off: a track left on a B / C pattern goes back to its A
        E(movs_imm, 0, SCR + S_LIVE); E(ldrb_reg, 0, 6, 0); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); E(b_cond, "sp_lv", "ne")
        E(adds_reg, 7, 6, 4); E(adds_imm8, 7, SCR + S_CNT)
        E(ldrb_imm, 0, 7, S_RET - S_CNT); E(cmp_imm, 0, 0); bc("sp_stock", "eq")
        E(ldr_sp, 3, 0); E(cmp_imm, 3, 0); bc("sp_s3", "eq"); E(movs_imm, 3, 0); E(strb_imm, 3, 7, S_RET - S_CNT); E(b, "sp_s3")
        a.label("sp_lv")
    else:
        E(movs_imm, 0, SCR + S_LIVE); E(ldrb_reg, 0, 6, 0); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); bc("sp_stock", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcget"); E(str_sp, 0, 4)
    E(adds_reg, 7, 6, 4); E(adds_imm8, 7, SCR + S_CNT)                               # r7 -> the track's count (+ 8 its return, + 16 its B / C bits)
    E(cmp_imm, 0, 0); E(b_cond, "sp_nr", "eq")
    E(lsls_imm, 1, 0, 24); E(lsrs_imm, 1, 1, 24)                                     # n
    E(ldrb_imm, 2, 7, 0); E(adds_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "sp_j", "hs")
    E(ldr_sp, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "sp_s1", "eq"); E(strb_imm, 2, 7, 0)
    a.label("sp_s1"); E(mov_reg, 0, 5); E(b, "sp_x")
    a.label("sp_j")
    E(ldr_sp, 0, 4); E(lsrs_imm, 1, 0, 8); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(lsrs_imm, 2, 0, 16)   # r1 = B + 1, r2 = C + 1
    E(ldrb_imm, 3, 7, S_TOG - S_CNT); E(lsrs_reg, 3, 5); E(lsls_imm, 3, 3, 31); E(b_cond, "sp_b", "eq")
    E(cmp_imm, 2, 0); E(b_cond, "sp_b", "eq"); E(mov_reg, 1, 2)
    a.label("sp_b"); E(subs_imm8, 1, 1)                                              # r1 = the target
    E(ldr_sp, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "sp_s2", "eq")
    E(movs_imm, 3, 0); E(strb_imm, 3, 7, 0)
    E(adds_imm3, 3, 5, 1); E(strb_imm, 3, 7, S_RET - S_CNT)
    E(cmp_imm, 2, 0); E(b_cond, "sp_s2", "eq")
    E(ldrb_imm, 3, 7, S_TOG - S_CNT); E(movs_imm, 0, 1); E(lsls_reg, 0, 5); E(eors_reg, 3, 0); E(strb_imm, 3, 7, S_TOG - S_CNT)
    a.label("sp_s2"); E(mov_reg, 0, 1); E(b, "sp_x")
    a.label("sp_nr")
    E(ldrb_imm, 0, 7, S_RET - S_CNT); E(cmp_imm, 0, 0); E(b_cond, "sp_stock", "eq")
    E(ldr_sp, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "sp_s3", "eq"); E(movs_imm, 3, 0); E(strb_imm, 3, 7, S_RET - S_CNT)
    a.label("sp_s3"); E(subs_imm8, 0, 1); E(b, "sp_x")
    a.label("sp_stock"); E(movs_imm, 0, 0xFF)
    a.label("sp_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pcnext (from the track advance, in place of its choice of the next pattern): [sp] = the track, r9 = the pattern that ends,
    #      r8 = the first of the chain, [sp, #2] = the last, [sp, #0x18] = forced, [sp, #0x44] = a scene change, [sp, #0x48] = the scene,
    #      fp = 0 for the playing store -> [sp, #1] = the next pattern
    F = 20                                                                            # (our five pushed words)
    a.label("c_pcnext")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(raw, ldrb_sp(4, F)); E(mov_reg, 5, 9)
    E(raw, ldrb_sp(0, F + 0x18)); E(cmp_imm, 0, 0); E(b_cond, "nx_f", "ne")
    E(raw, ldrb_sp(1, F + 2)); E(cmp_reg, 5, 1); E(b_cond, "nx_f", "eq")
    E(adds_imm3, 7, 5, 1); E(b, "nx_h")
    a.label("nx_f"); E(mov_reg, 7, 8)
    a.label("nx_h")                                                                   # r7 = the stock's choice
    E(cmp_imm, 4, 8); bc("nx_x", "hs")
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); bc("nx_x", "eq"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 11); E(cmp_imm, 0, 0); E(b_cond, "nx_pv", "ne")
    E(raw, ldrb_sp(0, F + 0x44)); E(cmp_imm, 0, 0); E(b_cond, "nx_ns", "eq")
    # a scene starts: the track takes its flag of that scene
    E(raw, ldrb_sp(1, F + 0x48)); E(mov_reg, 0, 6); E(bl, "c_pcsflag")
    if V3:                                                                            # ... and the mode shown is the scene's
        E(movs_imm, 1, 1); E(mov_reg, 2, 0); E(ands_reg, 2, 1); E(movs_imm, 3, SCR + S_EDIT); E(strb_reg, 2, 6, 3)
    E(lsrs_reg, 0, 4); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(lsls_reg, 0, 4)       # the track's bit of the flags
    E(movs_imm, 3, SCR + S_LIVE); E(ldrb_reg, 2, 6, 3); E(lsls_reg, 1, 4); E(bics_reg, 2, 1); E(orrs_reg, 2, 0); E(strb_reg, 2, 6, 3)
    E(b, "nx_rs")
    a.label("nx_ns")
    E(raw, ldrb_sp(0, F + 0x18)); E(cmp_imm, 0, 0); E(b_cond, "nx_go", "eq")
    a.label("nx_rs")                                                                  # a restart: the track's state cleared
    E(adds_reg, 1, 6, 4); E(adds_imm8, 1, SCR + S_CNT); E(movs_imm, 0, 0)
    E(strb_imm, 0, 1, 0); E(strb_imm, 0, 1, S_RET - S_CNT); E(strb_imm, 0, 1, S_TOG - S_CNT)
    E(b, "nx_x")
    a.label("nx_go"); E(movs_imm, 3, 1); E(b, "nx_st")
    a.label("nx_pv")                                                                  # the look-ahead: the same answer, nothing changed
    E(raw, ldrb_sp(0, F + 0x44)); E(raw, ldrb_sp(1, F + 0x18)); E(orrs_reg, 0, 1); E(b_cond, "nx_x", "ne")
    E(movs_imm, 3, 0)
    a.label("nx_st")
    E(mov_reg, 0, 6); E(mov_reg, 1, 4); E(mov_reg, 2, 5); E(bl, "c_pcstep")
    E(cmp_imm, 0, 0xFF); E(b_cond, "nx_x", "eq"); E(mov_reg, 7, 0)
    a.label("nx_x"); E(raw, strb_sp(7, F + 1)); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pcsflag (r0 = the tail, r1 = scene) -> r0 = the tracks that follow the rules in that scene (all of them when the project has
    #      nothing of ours); clobbers r1-r3
    a.label("c_pcsflag")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_pcvalid")
    E(movs_imm, 1, 0 if V3 else 0xFF); E(cmp_imm, 0, 0); E(b_cond, "sf_x", "eq")
    E(cmp_imm, 5, 16); E(b_cond, "sf_x", "hs")
    E(adds_imm8, 5, P_FLAGS); E(ldrb_reg, 1, 4, 5)
    if V3: E(cmp_imm, 1, 0); E(b_cond, "sf_x", "eq"); E(movs_imm, 1, 0xFF)
    a.label("sf_x"); E(mov_reg, 0, 1); E(pop_list, [4, 5], pc=True)

    # ---- c_pcend (from 0x0802C5F8, in place of its cmp.w sl, #0): r7 = the track, fp = its pattern, which ends now, sl = a chain pending,
    #      r0 = its chain entry -> the flags and r0 for the stock's «itt eq; ldrbeq r0, [r0, #1]; cmpeq fp, r0; bne not at the end»
    a.label("c_pcend")
    E(push_list, [0, 4, 5, 6, 7], lr=True)
    E(mov_reg, 0, 10); E(cmp_imm, 0, 0); E(b_cond, "en_s", "ne")
    E(mov_reg, 4, 7); E(mov_reg, 5, 11)
    E(cmp_imm, 4, 8); E(b_cond, "en_s", "hs")
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "en_s", "eq"); E(mov_reg, 6, 0)
    E(movs_imm, 0, SCR + S_LIVE); E(ldrb_reg, 0, 6, 0); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); E(b_cond, "en_s", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcget"); E(cmp_imm, 0, 0); E(b_cond, "en_n", "ne")     # a rule: the cycle goes on
    E(adds_reg, 1, 6, 4); E(adds_imm8, 1, SCR + S_CNT)
    E(ldrb_imm, 0, 1, S_RET - S_CNT); E(cmp_imm, 0, 0); E(b_cond, "en_s", "eq")        # nothing of ours running: the stock's test
    E(subs_imm8, 0, 1); E(ldrb_imm, 2, 1, S_TOG - S_CNT); E(lsrs_reg, 2, 0); E(lsls_imm, 2, 2, 31); E(b_cond, "en_n", "ne")   # B played, C to come
    imm32(0, t_eq - 1); E(adds_reg, 0, 0, 5); E(b, "en_o")                             # the end: [r0, #1] = the pattern
    a.label("en_n"); imm32(0, t_eq + 8 - 1)                                            # not the end: [r0, #1] = 0xFF
    a.label("en_o")
    E(add_sp_imm, 4); E(pop_list, [4, 5, 6, 7]); E(raw, POP_LR); E(cmp_reg, 0, 0); E(raw, BX_LR)
    a.label("en_s")
    E(pop_list, [0, 4, 5, 6, 7]); E(raw, POP_LR); E(raw, END_OLD); E(raw, BX_LR)

    # ---- c_pcrep (r0 = the engine, r1 = 1 to count) -> r0 = 1 when the current scene plays again, r1 = the current scene
    a.label("c_pcrep")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 7, 1)
    E(mov_reg, 0, 4); E(adds_imm8, 0, 0x2C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 5, 0, 0)   # r5 = the scene
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "rp_n", "eq"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(adds_imm8, 0, 0xA0); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "rp_z", "ne")                                          # a scene asked for: no repeats
    E(mov_reg, 0, 6); E(bl, "c_pcvalid"); E(cmp_imm, 0, 0); E(b_cond, "rp_z", "eq")
    E(cmp_imm, 5, 16); E(b_cond, "rp_z", "hs")
    E(mov_reg, 0, 5); E(adds_imm8, 0, P_REPS); E(ldrb_reg, 0, 6, 0)                    # its repeats
    E(cmp_imm, 0, REP_MAX); E(b_cond, "rp_c", "ls"); E(movs_imm, 0, 1)
    a.label("rp_c")
    E(movs_imm, 2, SCR + S_REPC); E(ldrb_reg, 1, 6, 2); E(adds_imm8, 1, 1); E(cmp_reg, 1, 0); E(b_cond, "rp_z", "hs")
    E(cmp_imm, 7, 0); E(b_cond, "rp_y", "eq"); E(strb_reg, 1, 6, 2)
    a.label("rp_y"); E(movs_imm, 0, 1); E(mov_reg, 1, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    a.label("rp_z")
    E(cmp_imm, 7, 0); E(b_cond, "rp_n", "eq"); E(movs_imm, 2, SCR + S_REPC); E(movs_imm, 1, 0); E(strb_reg, 1, 6, 2)
    a.label("rp_n"); E(movs_imm, 0, 0); E(mov_reg, 1, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_pcscn (the stock's "next scene", r0 = the engine): the current one while it has repeats left; c_pcscn_c counts (the commit)
    for name, count in (("c_pcscn", 0), ("c_pcscn_c", 1)):
        a.label(name)
        E(push_list, [0, 1, 2, 3], lr=True)
        E(movs_imm, 1, count); E(bl, "c_pcrep"); E(cmp_imm, 0, 0); E(b_cond, name + "_s", "eq")
        E(mov_reg, 0, 1); E(add_sp_imm, 16); E(pop_list, [], pc=True)
        a.label(name + "_s"); E(pop_list, [0, 1, 2, 3]); E(raw, POP_LR)
        E(raw, SCN_OLD); E(b_w, SCN_BODY)

    # ---- c_pcssave (the scene save's first write: r0 = the scene store, r1 = the scene, ...): the scene takes the tracks that follow the
    #      rules; saved again soon = one repeat more; then the stock's write
    a.label("c_pcssave")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(mov_reg, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "ss_x", "hs")
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "ss_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_pcfix")
    E(movs_imm, 1, SCR + S_LIVE); E(ldrb_reg, 0, 6, 1); E(mov_reg, 1, 4); E(adds_imm8, 1, P_FLAGS); E(strb_reg, 0, 6, 1)
    if not V2:
        imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 5, 0, 24)   # r5 = the time
        E(movs_imm, 2, 1)                                                                  # r2 = the repeats
        E(movs_imm, 1, SCR + S_LASTSC); E(ldrb_reg, 0, 6, 1); E(adds_imm3, 3, 4, 1); E(cmp_reg, 0, 3); E(b_cond, "ss_w", "ne")
        E(movs_imm, 1, SCR + S_LASTT); E(ldrb_reg, 0, 6, 1); E(subs_reg, 0, 5, 0); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24)
        E(cmp_imm, 0, REP_WINDOW); E(b_cond, "ss_w", "hs")
        E(mov_reg, 1, 4); E(adds_imm8, 1, P_REPS); E(ldrb_reg, 2, 6, 1); E(cmp_imm, 2, REP_MAX); E(b_cond, "ss_w", "hs"); E(adds_imm8, 2, 1)
        a.label("ss_w")
        E(mov_reg, 1, 4); E(adds_imm8, 1, P_REPS); E(strb_reg, 2, 6, 1)
        E(movs_imm, 1, SCR + S_LASTSC); E(adds_imm3, 0, 4, 1); E(strb_reg, 0, 6, 1)
        E(movs_imm, 1, SCR + S_LASTT); E(strb_reg, 5, 6, 1)
    E(mov_reg, 0, 6); E(bl, "c_pcsum")
    a.label("ss_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6]); E(raw, POP_LR); E(b_w, SC_SET)

    # ---- c_pcscopy (the scene copy's first write: r1 = the destination, [r7, #1] = the source): flags and repeats copied
    a.label("c_pcscopy")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(mov_reg, 4, 1); E(ldrb_imm, 5, 7, 1)
    E(cmp_imm, 4, 16); E(b_cond, "sc_x", "hs"); E(cmp_imm, 5, 16); E(b_cond, "sc_x", "hs")
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "sc_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_pcvalid"); E(cmp_imm, 0, 0); E(b_cond, "sc_x", "eq")
    for off in (P_FLAGS, P_REPS):
        E(mov_reg, 1, 5); E(adds_imm8, 1, off); E(ldrb_reg, 0, 6, 1); E(mov_reg, 1, 4); E(adds_imm8, 1, off); E(strb_reg, 0, 6, 1)
    E(mov_reg, 0, 6); E(bl, "c_pcsum")
    a.label("sc_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6]); E(raw, POP_LR); E(b_w, SC_SET)

    # ---- c_pcon() -> r0 = the Patterns view when it is on the screen, else 0; clobbers r1
    a.label("c_pcon")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(0, PV); E(cmp_reg, 0, 1); E(b_cond, "on_n", "ne"); E(raw, BX_LR)
    a.label("on_n"); E(movs_imm, 0, 0); E(raw, BX_LR)

    if V3:
        # ---- c_pcmode (r0 = the tail, r1 = 1 / 0): the chain mode on (every track follows the rules, their running state cleared, the tail
        #      made ours) or off; clobbers r0-r3
        a.label("c_pcmode")
        E(push_list, [4, 5, 6], lr=True)
        E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 4); E(adds_imm8, 6, SCR)
        E(strb_imm, 5, 6, S_EDIT); E(movs_imm, 1, 0); E(strb_imm, 1, 6, S_FOCUS)
        E(cmp_imm, 5, 0); E(b_cond, "md_w", "eq")
        E(movs_imm, 0, S_CNT)
        a.label("md_z"); E(strb_reg, 1, 6, 0); E(adds_imm8, 0, 1); E(cmp_imm, 0, S_CNT + 24); E(b_cond, "md_z", "lo")
        E(movs_imm, 1, 0xFF)
        a.label("md_w"); E(strb_imm, 1, 6, S_LIVE)
        E(cmp_imm, 5, 0); E(b_cond, "md_m", "eq"); E(mov_reg, 0, 4); E(bl, "c_pcfix")
        a.label("md_m"); E(mov_reg, 0, 4); E(bl, "c_pcmir")
        E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pcbtn (the controller's button press: ctrl, id): a view button leaves the chain edit; Shift + Octave up / down in the Patterns
    #      view = the chain edit on / off
    a.label("c_pcbtn")
    E(cmp_imm, 1, 16); E(b_cond, "bt_v", "lo"); E(cmp_imm, 1, BTN_DOWN); E(b_cond, "bt_o", "eq"); E(cmp_imm, 1, BTN_UP); E(b_cond, "bt_f", "ne")
    a.label("bt_o")
    E(push_list, [0, 1, 4], lr=True)
    E(bl, "c_pcon"); E(cmp_imm, 0, 0); E(b_cond, "bt_c", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "bt_c", "eq")
    if V3:
        E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "bt_c", "eq")
        E(ldr_sp, 1, 4); E(movs_imm, 2, 0); E(cmp_imm, 1, BTN_UP); E(b_cond, "bt_s", "ne"); E(movs_imm, 2, 1)
        a.label("bt_s"); E(mov_reg, 1, 2); E(bl, "c_pcmode")
    else:
        E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "bt_c", "eq"); E(adds_imm8, 0, SCR)
        E(ldr_sp, 1, 4); E(movs_imm, 2, 0); E(cmp_imm, 1, BTN_UP); E(b_cond, "bt_s", "ne"); E(movs_imm, 2, 1)
        a.label("bt_s"); E(strb_imm, 2, 0, S_EDIT); E(movs_imm, 2, 0); E(strb_imm, 2, 0, S_FOCUS)
    E(pop_list, [0, 1, 4], pc=True)
    a.label("bt_v")
    E(push_list, [0, 1, 4], lr=True)
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "bt_c", "eq"); E(adds_imm8, 0, SCR)
    E(movs_imm, 1, 0)
    if not V3: E(strb_imm, 1, 0, S_EDIT)                                               # (V3: the mode stays; only the rule being edited is left)
    E(strb_imm, 1, 0, S_FOCUS)
    a.label("bt_c"); E(raw, popw([0, 1, 4], lr=True))
    a.label("bt_f"); E(b_w, prev["btn"])

    # ---- c_pcpad (the Patterns view's pad press: view, pad, velocity)
    a.label("c_pcpad")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); bc("pp_ch", "eq"); E(mov_reg, 6, 0); E(adds_imm8, 6, SCR)   # r6 = the running part
    E(ldr_sp, 0, 4); E(bl, TRACKFN); E(mov_reg, 4, 0)                                  # r4 = the track
    E(ldr_sp, 0, 0); E(ldrb_w, 1, 0, 0x78); E(lsls_imm, 1, 1, 2); E(ldr_sp, 2, 4); E(lsrs_imm, 2, 2, 3); E(adds_reg, 5, 1, 2)   # r5 = the pattern
    E(cmp_imm, 4, 8); bc("pp_ch", "hs"); E(cmp_imm, 5, 8); bc("pp_ch", "hs")
    E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x2C); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 7, 0, 0); E(movs_imm, 0, 3); E(ands_reg, 7, 0)   # r7 = Clear / Duplicate held
    E(ldrb_imm, 0, 6, S_EDIT); E(cmp_imm, 0, 0); E(b_cond, "pp_e", "ne")
    # out of the edit
    E(cmp_imm, 7, 0); E(b_cond, "pp_nc", "ne")
    if V3: E(b, "pp_ch")
    else:
        E(ldrb_imm, 0, 6, S_LIVE); E(movs_imm, 1, 1); E(lsls_reg, 1, 4); E(bics_reg, 0, 1); E(strb_imm, 0, 6, S_LIVE)   # the stock chain from now on
        E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(bl, "c_pcmir"); E(b, "pp_ch")
    a.label("pp_nc")
    if V3:                                                                            # Clear: the rule and the play order too
        E(lsls_imm, 0, 7, 31); bc("pp_ch", "eq"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pczr")
        a.label("pp_zo"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); bc("pp_ch", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 3); E(b, "pp_ch")
    else:
        E(lsls_imm, 0, 7, 31); bc("pp_ch", "eq"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pczr"); E(b, "pp_ch")   # Clear: the rule too
    # the edit
    a.label("pp_e")
    E(lsls_imm, 0, 7, 30); bc("pp_ch", "mi")                                           # Duplicate: the stock's copy
    E(lsls_imm, 0, 7, 31); E(b_cond, "pp_e2", "eq")
    if V3:                                                                            # Clear + a pattern without a rule: the stock's clear (and its play order)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); bc("pp_ch", "eq")
        E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("pp_zo", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pczr")                                # Clear: the rule only
    E(ldrb_imm, 0, 6, S_FOCUS); E(mov_reg, 1, 4); E(adds_imm8, 1, 0x80); E(cmp_reg, 0, 1); bc("pp_x", "ne")
    E(ldrb_imm, 0, 6, S_A); E(cmp_reg, 0, 5); bc("pp_x", "ne"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, S_FOCUS); E(b, "pp_x")
    a.label("pp_e2")
    E(ldrb_imm, 0, 6, S_FOCUS); E(mov_reg, 1, 4); E(adds_imm8, 1, 0x80); E(cmp_reg, 0, 1); E(b_cond, "pp_new", "ne")
    E(mov_reg, 0, 4); E(ldrb_imm, 1, 6, S_A); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); bc("pp_x", "eq"); E(mov_reg, 7, 0)   # r7 = the rule
    E(ldrb_imm, 0, 6, S_A); E(cmp_reg, 5, 0); E(b_cond, "pp_bc", "ne")
    E(ldrb_imm, 1, 7, 0); E(cmp_imm, 1, MAX_N); bc("pp_x", "hs"); E(adds_imm8, 1, 1); E(strb_imm, 1, 7, 0); E(b, "pp_x")   # A again: once more
    a.label("pp_bc")
    E(adds_imm3, 1, 5, 1); E(ldrb_imm, 0, 6, S_STAGE); E(cmp_imm, 0, 0); E(b_cond, "pp_c", "ne")
    E(strb_imm, 1, 7, 1); E(movs_imm, 0, 1); E(strb_imm, 0, 6, S_STAGE); E(b, "pp_x")
    a.label("pp_c"); E(strb_imm, 1, 7, 2); E(movs_imm, 0, 2); E(strb_imm, 0, 6, S_STAGE); E(b, "pp_x")
    a.label("pp_new")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 0x80); E(strb_imm, 0, 6, S_FOCUS); E(strb_imm, 5, 6, S_A)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcget"); E(cmp_imm, 0, 0); E(b_cond, "pp_fr", "eq")
    E(lsrs_imm, 0, 0, 16); E(movs_imm, 1, 1); E(cmp_imm, 0, 0); E(b_cond, "pp_st", "eq"); E(movs_imm, 1, 2); E(b, "pp_st")
    a.label("pp_fr")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); E(b_cond, "pp_f0", "eq")
    E(movs_imm, 1, 1); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 2)
    a.label("pp_f0"); E(movs_imm, 1, 0)
    a.label("pp_st"); E(strb_imm, 1, 6, S_STAGE)
    E(ldrb_imm, 0, 6, S_LIVE); E(movs_imm, 1, 1); E(lsls_reg, 1, 4); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, S_LIVE)   # the track follows the rules
    E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(bl, "c_pcfix")
    E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(bl, "c_pcmir")
    a.label("pp_ch"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])
    a.label("pp_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7], pc=True)

    if V2:
        # ---- c_pcledtask (the LED task calls: ctrl, frame): the chain; the chain edit on the screen: the rules over the stock's picture
        a.label("c_pcledtask")
        E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
        E(mov_reg, 5, 1); E(bl, prev["ledtask"])
        E(bl, "c_pcst"); E(cmp_imm, 0, 0); bc("lt_x", "eq"); E(mov_reg, 6, 0); E(adds_imm8, 6, SCR)
        if V3:                                                                             # stopped, another scene: the mode it was saved in
            imm32(0, ENG + 0x2C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 4, 0, 0); E(adds_imm8, 4, 1)
            E(ldrb_imm, 7, 6, S_LASTSC); E(cmp_reg, 7, 4); E(b_cond, "lt_ss", "eq")
            E(strb_imm, 4, 6, S_LASTSC); E(cmp_imm, 7, 0); E(b_cond, "lt_ss", "eq")
            imm32(0, PLAY_STORE); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "lt_ss", "ne")
            E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(subs_imm3, 1, 4, 1); E(bl, "c_pcsflag")
            E(movs_imm, 1, 1); E(ands_reg, 1, 0); E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(bl, "c_pcmode")
            a.label("lt_ss")
        E(bl, L["c_shift"]); E(mov_reg, 9, 0)                                              # r9 = Shift held
        E(bl, "c_pcon"); E(cmp_imm, 0, 0); bc("lt_mix", "eq"); E(mov_reg, 8, 0)
        # the Patterns view: Octave up green in the edit; with Shift the Octave button that does something yellow
        E(ldrb_imm, 4, 6, S_EDIT); E(cmp_imm, 4, 0); E(b_cond, "lt_i", "eq")
        E(movs_imm, 0, 2 * LED_UP); E(movs_imm, 1, COL_MODE); E(strh_reg, 1, 5, 0)
        a.label("lt_i")
        E(mov_reg, 0, 9); E(cmp_imm, 0, 0); E(b_cond, "lt_j", "eq")
        E(movs_imm, 0, 2 * LED_UP); E(cmp_imm, 4, 0); E(b_cond, "lt_y", "eq"); E(movs_imm, 0, 2 * LED_DOWN)
        a.label("lt_y"); E(movs_imm, 1, COL_SHIFT); E(strh_reg, 1, 5, 0)
        a.label("lt_j")
        E(cmp_imm, 4, 0); bc("lt_x", "eq")
        E(mov_reg, 0, 8); E(ldrb_w, 7, 0, 0x78); E(lsls_imm, 7, 7, 2)                      # r7 = the first pattern of the page
        E(movs_imm, 4, 0)
        a.label("lt_l")
        E(mov_reg, 0, 4); E(bl, TRACKFN); E(mov_reg, 10, 0)                                # r10 = the track of the pad
        E(lsrs_imm, 1, 4, 3); E(adds_reg, 1, 1, 7); E(mov_reg, 11, 1)                      # r11 = its pattern
        E(cmp_imm, 0, 8); bc("lt_n", "hs")
        E(bl, "c_pcget"); E(cmp_imm, 0, 0); E(b_cond, "lt_f", "eq")
        E(movs_imm, 2, COL_OFF); E(ldrb_imm, 1, 6, S_LIVE); E(mov_reg, 3, 10); E(lsrs_reg, 1, 3); E(lsls_imm, 1, 1, 31); E(b_cond, "lt_w", "eq")
        E(movs_imm, 2, COL_RULE)
        a.label("lt_w"); E(lsls_imm, 0, 4, 1); E(strh_reg, 2, 5, 0)
        a.label("lt_f")                                                                    # the rule being edited
        E(ldrb_imm, 0, 6, S_FOCUS); E(mov_reg, 1, 10); E(adds_imm8, 1, 0x80); E(cmp_reg, 0, 1); E(b_cond, "lt_n", "ne")
        E(mov_reg, 0, 10); E(ldrb_imm, 1, 6, S_A); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); E(b_cond, "lt_n", "eq")
        E(mov_reg, 1, 11); E(ldrb_imm, 2, 6, S_A); E(cmp_reg, 1, 2); E(b_cond, "lt_b", "ne"); E(movs_imm, 2, COL_A); E(b, "lt_p")
        a.label("lt_b"); E(adds_imm8, 1, 1); E(ldrb_imm, 2, 0, 1); E(cmp_reg, 2, 1); E(b_cond, "lt_c", "ne"); E(movs_imm, 2, COL_B); E(b, "lt_p")
        a.label("lt_c"); E(ldrb_imm, 2, 0, 2); E(cmp_reg, 2, 1); E(b_cond, "lt_n", "ne"); E(movs_imm, 2, COL_C)
        a.label("lt_p"); E(lsls_imm, 0, 4, 1); E(strh_reg, 2, 5, 0)
        a.label("lt_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 32); bc("lt_l", "lo")
        # the knob LEDs: the plays of the rule being edited
        E(ldrb_imm, 0, 6, S_FOCUS); E(cmp_imm, 0, 0x80); bc("lt_x", "lo")
        E(subs_imm8, 0, 0x80); E(ldrb_imm, 1, 6, S_A); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); bc("lt_x", "eq")
        E(ldrb_imm, 4, 0, 0); E(movs_imm, 3, 0)
        a.label("lt_k")
        E(movs_imm, 2, 0); E(cmp_reg, 3, 4); E(b_cond, "lt_kw", "hs"); E(movw, 2, KNOB_ON)
        a.label("lt_kw"); E(mov_reg, 0, 3); E(adds_imm8, 0, 60); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
        E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "lt_k", "lo")
        E(b, "lt_x")
        # the Mixer view (not its Master FX page): the scenes with rules, the tracks that run one, the repeats with Shift
        a.label("lt_mix")
        imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(0, MIXV); E(cmp_reg, 0, 1); bc("lt_x", "ne")
        E(bl, L["c_gact"]); E(cmp_imm, 0, 0); bc("lt_x", "ne")
        E(mov_reg, 0, 6); E(subs_imm8, 0, SCR); E(mov_reg, 10, 0)                          # r10 = the tail
        imm32(0, ENG + 0x2C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(mov_reg, 8, 0)   # r8 = the current scene
        E(movs_imm, 4, 0)
        a.label("ms_l")
        E(mov_reg, 0, 4); E(adds_imm8, 0, 16); E(lsls_imm, 0, 0, 1); E(ldrh_reg, 1, 5, 0)
        E(cmp_imm, 1, 0); E(b_cond, "ms_n", "eq"); E(cmp_imm, 1, COL_OFF); E(b_cond, "ms_n", "eq")     # (an empty scene)
        E(mov_reg, 0, 10); E(mov_reg, 1, 4); E(bl, "c_pcchained"); E(cmp_imm, 0, 0); E(b_cond, "ms_n", "eq")
        E(movs_imm, 2, COL_SC); E(cmp_reg, 4, 8); E(b_cond, "ms_w", "ne"); E(movs_imm, 2, COL_SCCUR)
        a.label("ms_w"); E(mov_reg, 0, 4); E(adds_imm8, 0, 16); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
        a.label("ms_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); bc("ms_l", "lo")
        imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsls_imm, 0, 0, 23); E(b_cond, "mb_x", "pl")     # the blink: 256 ms off, 256 ms on
        E(movs_imm, 4, 0)
        a.label("mb_l")
        E(ldrb_imm, 0, 6, S_LIVE); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); E(b_cond, "mb_n", "eq")
        E(adds_reg, 1, 6, 4); E(ldrb_imm, 7, 1, S_RET)
        imm32(0, ENG + 0x30); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET)
        E(ldrb_imm, 1, 0, 0); E(mov_reg, 0, 4); E(bl, "c_pcget"); E(orrs_reg, 0, 7); E(b_cond, "mb_n", "eq")
        E(lsls_imm, 0, 4, 1); E(movs_imm, 2, 0); E(strh_reg, 2, 5, 0)
        a.label("mb_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "mb_l", "lo")
        a.label("mb_x")
        E(mov_reg, 0, 9); E(cmp_imm, 0, 0); bc("lt_x", "eq")                               # Shift: the repeats of the current scene
        E(mov_reg, 0, 10); E(bl, "c_pcvalid"); E(movs_imm, 7, 0); E(cmp_imm, 0, 0); E(b_cond, "mr_d", "eq")
        E(mov_reg, 0, 8); E(cmp_imm, 0, 16); E(b_cond, "mr_d", "hs"); E(adds_imm8, 0, P_REPS); E(mov_reg, 1, 10); E(ldrb_reg, 7, 1, 0)
        E(cmp_imm, 7, 0); E(b_cond, "mr_d", "eq"); E(subs_imm8, 7, 1); E(cmp_imm, 7, 7); E(b_cond, "mr_d", "ls"); E(movs_imm, 7, 0)
        a.label("mr_d"); E(movs_imm, 4, 0)
        a.label("mr_l"); E(movs_imm, 2, COL_SHIFT); E(cmp_reg, 4, 7); E(b_cond, "mr_w", "ne"); E(movs_imm, 2, COL_SEL)
        a.label("mr_w"); E(mov_reg, 0, 4); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
        E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "mr_l", "lo")
        a.label("lt_x"); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], pc=True))

        # ---- c_pcchained (r0 = the tail, r1 = scene) -> r0 = 1 when a track of that scene runs a rule: its flag there and a rule on the first
        #      pattern of its chain there
        a.label("c_pcchained")
        E(push_list, [3, 4, 5, 6, 7], lr=True)
        E(mov_reg, 6, 0); E(mov_reg, 5, 1); E(bl, "c_pcsflag"); E(mov_reg, 7, 0)
        E(movs_imm, 4, 0)
        a.label("cc_l")
        E(mov_reg, 0, 7); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); E(b_cond, "cc_n", "eq")
        imm32(0, ENG + 0x24); E(ldr_imm, 0, 0, 0); E(mov_reg, 1, 5); E(mov_reg, 2, 4); E(bl, SC_FIRST)
        E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pcget"); E(cmp_imm, 0, 0); E(b_cond, "cc_y", "ne")
        a.label("cc_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "cc_l", "lo")
        E(movs_imm, 0, 0); E(pop_list, [3, 4, 5, 6, 7], pc=True)
        a.label("cc_y"); E(movs_imm, 0, 1); E(pop_list, [3, 4, 5, 6, 7], pc=True)

        # ---- c_pcmixpad (the Mixer view's pad press: view, pad, velocity): Shift + pads 9-16 = the repeats of the current scene
        a.label("c_pcmixpad")
        E(cmp_imm, 1, 8); E(b_cond, "mp_f", "lo"); E(cmp_imm, 1, 16); E(b_cond, "mp_f", "hs")
        E(push_list, [0, 1, 2, 4, 5], lr=True)
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq")
        E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "ne")
        E(bl, "c_pcst"); E(cmp_imm, 0, 0); E(b_cond, "mp_c", "eq"); E(mov_reg, 4, 0)
        E(bl, "c_pcfix")
        imm32(0, ENG + 0x2C); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 5, 0, 0); E(cmp_imm, 5, 16); E(b_cond, "mp_x", "hs")
        E(ldr_sp, 1, 4); E(subs_imm8, 1, 7); E(adds_imm8, 5, P_REPS); E(strb_reg, 1, 4, 5)
        E(mov_reg, 0, 4); E(bl, "c_pcsum")
        a.label("mp_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
        a.label("mp_c"); E(raw, popw([0, 1, 2, 4, 5], lr=True))
        a.label("mp_f"); E(b_w, prev["mixpad"])
        return a.assemble()
    # ---- c_pcledtask (the LED task calls: ctrl, frame): the chain; the chain edit on the screen: the rules over the stock's picture
    a.label("c_pcledtask")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_pcon"); E(cmp_imm, 0, 0); bc("lt_x", "eq"); E(mov_reg, 8, 0)
    E(bl, "c_pcst"); E(cmp_imm, 0, 0); bc("lt_x", "eq"); E(mov_reg, 6, 0); E(adds_imm8, 6, SCR)
    E(ldrb_imm, 0, 6, S_EDIT); E(cmp_imm, 0, 0); bc("lt_x", "eq")
    E(movs_imm, 0, 2 * LED_UP); E(movs_imm, 1, COL_RULE); E(strh_reg, 1, 5, 0)
    E(mov_reg, 0, 8); E(ldrb_w, 7, 0, 0x78); E(lsls_imm, 7, 7, 2)                      # r7 = the first pattern of the page
    E(movs_imm, 4, 0)
    a.label("lt_l")
    E(mov_reg, 0, 4); E(bl, TRACKFN); E(mov_reg, 10, 0)                                # r10 = the track of the pad
    E(lsrs_imm, 1, 4, 3); E(adds_reg, 1, 1, 7); E(mov_reg, 11, 1)                      # r11 = its pattern
    E(cmp_imm, 0, 8); bc("lt_n", "hs")
    E(bl, "c_pcget"); E(cmp_imm, 0, 0); E(b_cond, "lt_f", "eq")
    E(movs_imm, 2, COL_OFF); E(ldrb_imm, 1, 6, S_LIVE); E(mov_reg, 3, 10); E(lsrs_reg, 1, 3); E(lsls_imm, 1, 1, 31); E(b_cond, "lt_w", "eq")
    E(movs_imm, 2, COL_RULE)
    a.label("lt_w"); E(lsls_imm, 0, 4, 1); E(strh_reg, 2, 5, 0)
    a.label("lt_f")                                                                    # the rule being edited
    E(ldrb_imm, 0, 6, S_FOCUS); E(mov_reg, 1, 10); E(adds_imm8, 1, 0x80); E(cmp_reg, 0, 1); E(b_cond, "lt_n", "ne")
    E(mov_reg, 0, 10); E(ldrb_imm, 1, 6, S_A); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); E(b_cond, "lt_n", "eq")
    E(mov_reg, 1, 11); E(ldrb_imm, 2, 6, S_A); E(cmp_reg, 1, 2); E(b_cond, "lt_b", "ne"); E(movs_imm, 2, COL_A); E(b, "lt_p")
    a.label("lt_b"); E(adds_imm8, 1, 1); E(ldrb_imm, 2, 0, 1); E(cmp_reg, 2, 1); E(b_cond, "lt_c", "ne"); E(movs_imm, 2, COL_B); E(b, "lt_p")
    a.label("lt_c"); E(ldrb_imm, 2, 0, 2); E(cmp_reg, 2, 1); E(b_cond, "lt_n", "ne"); E(movs_imm, 2, COL_C)
    a.label("lt_p"); E(lsls_imm, 0, 4, 1); E(strh_reg, 2, 5, 0)
    a.label("lt_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 32); bc("lt_l", "lo")
    # the knob LEDs: the plays of the rule being edited
    E(ldrb_imm, 0, 6, S_FOCUS); E(cmp_imm, 0, 0x80); bc("lt_x", "lo")
    E(subs_imm8, 0, 0x80); E(ldrb_imm, 1, 6, S_A); E(bl, "c_pcrule"); E(cmp_imm, 0, 0); bc("lt_x", "eq")
    E(ldrb_imm, 4, 0, 0); E(movs_imm, 3, 0)
    a.label("lt_k")
    E(movs_imm, 2, 0); E(cmp_reg, 3, 4); E(b_cond, "lt_kw", "hs"); E(movw, 2, KNOB_ON)
    a.label("lt_kw"); E(mov_reg, 0, 3); E(adds_imm8, 0, 60); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "lt_k", "lo")
    a.label("lt_x"); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], pc=True))
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the three hooks of the sequencer, the scene save / copy, the end of the load, the Patterns view's pad slot, the head of
    the button chain, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_shift=lab("sc15", "c_shift"), c_gact=lab("sc17", "c_gact"))
    prev = dict(pad=u(PV_VT) & ~1, btn=MP.bw_target(img, BTN_ENTRY, BASE), ledtask=lab("stepmod", "c_rfledtask"), load=MP.bw_target(img, P19.LOAD_END, BASE))
    assert prev["pad"] == PV_PAD and prev["load"] == lab("persist19", "c_pl_load")
    if V2: prev["mixpad"] = u(MIX_VT) & ~1
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    assert NEXT_BACK - NEXT_HOOK == len(NEXT_OLD)
    put(NEXT_HOOK, bl(NEXT_HOOK, labels["c_pcnext"]) + b(NEXT_HOOK + 4, NEXT_BACK) + nop() * 11, NEXT_OLD)
    put(END_HOOK, bl(END_HOOK, labels["c_pcend"]), END_OLD)
    put(SCN_FN, b_w(SCN_FN, labels["c_pcscn"]) + nop(), SCN_OLD)
    put(SCN_COMMIT, bl(SCN_COMMIT, labels["c_pcscn_c"]), bl(SCN_COMMIT, SCN_FN))
    put(SC_SAVE, bl(SC_SAVE, labels["c_pcssave"]), bl(SC_SAVE, SC_SET))
    put(SC_COPY, bl(SC_COPY, labels["c_pcscopy"]), bl(SC_COPY, SC_SET))
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_pcload"])
    struct.pack_into("<I", img, PV_VT - BASE, labels["c_pcpad"] | 1)
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_pcbtn"])
    if V2: struct.pack_into("<I", img, MIX_VT - BASE, labels["c_pcmixpad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_pcledtask"])
    return labels, code, prev
