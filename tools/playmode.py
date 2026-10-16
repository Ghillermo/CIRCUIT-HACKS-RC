"""SC40.8 (the user, 2026-10-13 / 14): three more pads in the Pattern Settings view of the note tracks (its pads 26-28 were free; pad 25 = the
dynamics / mutate mode of tools/stepmod.py):

    pad 26  NUDGE: the pattern is written again so that the chosen first step is step 1; what was in front of it goes to the end.  The whole
            steps with their knob automation rotate, over 16 steps (the first and the last step within 1-16) or over the 32; the first step
            becomes 1 and the last one moves with it.
    pad 27  FRACTAL play order: 1 · 1 2 · 1 2 3 · ... · 1..n over the pattern's steps; the pattern ends (one play: chains, scenes, the
            frequency) after the last step of the whole run, and starts again.
    pad 28  DECONSTRUCTED play order: the diagonals of the 4 x 4 grid, 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 (17-32: the same in the
            second half); a step outside the pattern's first / last step is skipped.
    Pads 27 / 28 and the stock's four direction pads (29-32) exclude each other; they have the direction pads' colours, pad 26 its own.

The order is a byte of the pattern: byte 7 of its 40 settings bytes (bytes 4..7 are zero in every session of the user's card; 4..6 = the chain
rule of tools/patchain.py), 1 = fractal, 2 = deconstructed, with the stock's direction left at "forward": a firmware without this plays it forward.
The engine (hooks where the stock reads the direction byte; the same for every track, the pads only offer it on the note tracks for now):
  * 0x0802C552 in 0x0802C4E4 («the pattern ends at this step»): with an order of ours the answer is ours, given to the stock's own code as
    "forward, at the last step" or as a direction it does nothing with;
  * 0x0802CC14 in the track advance 0x0802CB3C (the next step): ours in r5, and a direction the stock skips;
  * 0x0802CD84 there (the step a pattern starts at): the first step of our order, the fractal's group back to one step.
The fractal's group size is a byte per track in the running part of the project's tail (patchain's, + 32), cleared while the transport is
stopped; the deconstructed order needs no state (the place in the order is found from the step that plays).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, add_sp_imm, adds_imm3, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, h, str_sp, strb_imm, strb_reg, strh_reg, sub_sp_imm, subs_imm8,
                   subs_reg)
import packio as PK  # noqa: E402
import mutate39 as MU  # noqa: E402
import stepmod as SM  # noqa: E402
import patchain as PC  # noqa: E402

END_HOOK, STEP_HOOK, START_HOOK = 0x0802C552, 0x0802CC14, 0x0802CD84
DIR_OLD = bytes.fromhex("00780328")                           # ldrb r0, [r0]; cmp r0, #3
DIR_GET = 0x0803C790                                          # (object, track, pattern) -> the pattern's direction
PS_VT = SM.PS_VT
ENG = PC.ENG
PAD_NUDGE, PAD_FRAC, PAD_DEC, PAD_DIR = 25, 26, 27, 28        # pad indices (pads 26, 27, 28, 29-32)
M_FRAC, M_DEC = 1, 2
S_K = PC.SCR + 32                                             # the fractal's group size - 1, a byte per track (offset from the tail)
COL_NUDGE, COL_SEL, COL_UNSEL = 0x09, 0x5F, 0x60             # orange; the stock's colours of the direction pads (chosen / not)
STEP_SZ, LANE_SZ, LANES, AUTO_OFF, SET_OFF = 28, 6, 12, 0x3A8, 0x380
DIAG = [r * 4 + (r + d) % 4 for d in range(4) for r in range(4)]
ORDER = DIAG + [16 + s for s in DIAG]
INV = dict(eq="ne", ne="eq", lo="hs", hs="lo", hi="ls", ls="hi")
DRUMS = False                                                 # SC40.9: the three pads on the drum tracks too (see use_drums)
DSYNC = False                                                 # SC43 (use_dsync)


def use_dsync():
    """SC43: Nudge on a drum pattern also puts the rotated arrays into the drum's edit store (drumstore.py: the stock's next commit undid it) and
    rotates drumpat's step bytes (+ 0x88)."""
    global DSYNC
    assert DRUMS
    DSYNC = True
CLRMOD = False                                                # SC41.7 (see use_clrmod)
PAD_MODE2, MGR_HELD = 24, 0x20                                # pad 25 (stepmod's mode 2); the held buttons = p0 of [[ctrl + 0x20] + 0xC], bit 0 Clear


def use_clrmod():
    """SC41.7 (the user, 2026-10-15: «en vista normal pattern settings, clear + pad 25 borra los random-mutate y dynamics»): Clear held + pad 25 of the
    Pattern Settings view on a note track = every step of the pattern the track plays loses its random-mutate level (byte 2) and its dynamics (bits 4-6
    of byte 3); the frequency (bits 0-2) stays.  Without Clear pad 25 opens mode 2 as before.  c_pmclrpad in front of c_pmpspad in slot 0."""
    global CLRMOD
    CLRMOD = True
D_SET_OFF, D_AUTO_OFF, D_LANES, D_ARRAYS = 0x80, 0xA8, 8, 4   # a drum pattern: four arrays of 32 bytes (velocity, probability, sample, micro steps), the settings, 8 lanes


def use_drums():
    """SC40.9 (the user, 2026-10-14: the note tracks work on the unit): pads 26-28 of the Pattern Settings view on the four drum tracks as well.
    The engine hooks already were for every track.  Nudge on a drum pattern rotates its four per-step arrays (one byte a step: velocity,
    probability, sample flip, micro steps; seen in the 173 sessions of the card's copy) and its 8 automation lanes."""
    global DRUMS
    DRUMS = True
POP_LR, BX_LR = h(0xF85D) + h(0xEB04), h(0x4770)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_sp(rt, off): return h(0xF89D) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    t_ord = base; E(raw, bytes(ORDER))

    # ---- c_pminfo (r0 = track, r1 = pattern) -> r0 = its order (0 = the stock's), r1 = its first step, r2 = its last; clobbers r3
    a.label("c_pminfo")
    E(push_list, [4], lr=True)
    E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); E(b_cond, "in_0", "eq")
    E(mov_reg, 4, 0); E(subs_imm8, 4, 4)
    E(ldrb_imm, 0, 4, 7); E(ldrb_imm, 1, 4, 1); E(ldrb_imm, 2, 4, 0)
    E(cmp_imm, 0, M_DEC); E(b_cond, "in_0", "hi"); E(cmp_reg, 1, 2); E(b_cond, "in_0", "hi"); E(cmp_imm, 2, 31); E(b_cond, "in_0", "hi")
    E(pop_list, [4], pc=True)
    a.label("in_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pmdidx (r0 = step) -> r0 = its place in the deconstructed order + 1 (0: none); clobbers r1-r3
    a.label("c_pmdidx")
    imm32(3, t_ord); E(movs_imm, 1, 0)
    a.label("di_l"); E(ldrb_reg, 2, 3, 1); E(adds_imm8, 1, 1); E(cmp_reg, 2, 0); E(b_cond, "di_f", "eq"); E(cmp_imm, 1, 32); E(b_cond, "di_l", "lo")
    E(movs_imm, 1, 0)
    a.label("di_f"); E(mov_reg, 0, 1); E(raw, BX_LR)

    # ---- c_pmdscan (r0 = the place to look from, r1 = the first step, r2 = the last) -> r0 = the next step of the order within them, 0xFF: none
    a.label("c_pmdscan")
    E(push_list, [4], lr=True); imm32(4, t_ord)
    a.label("ds_l")
    E(cmp_imm, 0, 32); E(b_cond, "ds_0", "hs"); E(ldrb_reg, 3, 4, 0); E(adds_imm8, 0, 1)
    E(cmp_reg, 3, 1); E(b_cond, "ds_l", "lo"); E(cmp_reg, 3, 2); E(b_cond, "ds_l", "hi")
    E(mov_reg, 0, 3); E(pop_list, [4], pc=True)
    a.label("ds_0"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_pmk (r0 = track) -> r0 = the address of its fractal group byte (0: none); clobbers r1-r3
    a.label("c_pmk")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, L["c_pcst"]); E(cmp_imm, 0, 0); E(b_cond, "pk_x", "eq")
    E(adds_imm8, 0, S_K); E(adds_reg, 0, 0, 4)
    a.label("pk_x"); E(pop_list, [4], pc=True)

    # ---- c_pmend (in 0x0802C4E4, in place of «ldrb r0, [r0]; cmp r0, #3»): r4 = the track, r6 = the engine, fp = the step, r8 = the
    #      last step -> the direction and its flags for the stock; an order of ours: "forward, at the last step" when the pattern ends here,
    #      else a direction the stock answers "no" to
    a.label("c_pmend")
    E(ldrb_imm, 0, 0, 0)
    E(push_list, [0, 1, 2, 3, 5, 6, 7], lr=True)
    E(lsls_imm, 1, 4, 2); E(adds_reg, 1, 1, 6); E(ldr_imm, 0, 1, 0x30); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 1, 0, 0)
    E(mov_reg, 0, 4); E(bl, "c_pminfo"); E(cmp_imm, 0, 0); E(b_cond, "pe_x", "eq")
    E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(cmp_imm, 0, M_DEC); E(b_cond, "pe_d", "eq")
    E(mov_reg, 0, 4); E(bl, "c_pmk"); E(cmp_imm, 0, 0); E(b_cond, "pe_x", "eq")
    E(ldrb_imm, 0, 0, 0); E(adds_reg, 0, 0, 5); E(mov_reg, 1, 11); E(cmp_reg, 1, 0); E(b_cond, "pe_n", "lo")       # inside the group
    E(cmp_reg, 0, 6); E(b_cond, "pe_y", "hs"); E(b, "pe_n")                                                    # the group is the whole pattern
    a.label("pe_d")
    E(mov_reg, 0, 11); E(bl, "c_pmdidx"); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_pmdscan"); E(cmp_imm, 0, 0xFF); E(b_cond, "pe_n", "ne")
    a.label("pe_y"); E(movs_imm, 0, 0); E(str_sp, 0, 0); E(mov_reg, 11, 8); E(b, "pe_x")
    a.label("pe_n"); E(movs_imm, 0, 4); E(str_sp, 0, 0)
    a.label("pe_x"); E(pop_list, [0, 1, 2, 3, 5, 6, 7]); E(raw, POP_LR); E(cmp_imm, 0, 3); E(raw, BX_LR)

    # ---- c_pmstep (in the track advance, in place of «ldrb r0, [r0]; cmp r0, #3»): [sp] = the track, r9 = the pattern, r6 = the step,
    #      r4 = the pattern ends, fp = 0 for the playing store -> the direction and its flags; an order of ours: r5 = the next step and a
    #      direction the stock skips
    F = 32
    a.label("c_pmstep")
    E(ldrb_imm, 0, 0, 0)
    E(push_list, [0, 1, 2, 3, 4, 6, 7], lr=True)
    E(raw, ldrb_sp(7, F)); E(mov_reg, 0, 7); E(mov_reg, 1, 9); E(bl, "c_pminfo"); E(cmp_imm, 0, 0); E(b_cond, "ps_x", "eq")
    E(ldr_sp, 3, 16); E(cmp_imm, 3, 0); E(b_cond, "ps_s", "ne")                        # the pattern ends: the start hook's job
    E(cmp_imm, 0, M_DEC); E(b_cond, "ps_d", "eq")
    E(mov_reg, 4, 1)                                                                  # r4 = the first step
    E(mov_reg, 0, 7); E(bl, "c_pmk"); E(cmp_imm, 0, 0); E(b_cond, "ps_x", "eq"); E(mov_reg, 3, 0)
    E(ldrb_imm, 0, 3, 0); E(adds_reg, 1, 4, 0); E(cmp_reg, 6, 1); E(b_cond, "ps_g", "hs")
    E(adds_imm3, 5, 6, 1); E(b, "ps_s")
    a.label("ps_g")                                                                   # the group ends: the next one is a step longer
    E(mov_reg, 5, 4); E(mov_reg, 1, 11); E(cmp_imm, 1, 0); E(b_cond, "ps_s", "ne"); E(adds_imm8, 0, 1); E(strb_imm, 0, 3, 0); E(b, "ps_s")
    a.label("ps_d")
    E(mov_reg, 4, 1); E(mov_reg, 7, 2)
    E(mov_reg, 0, 6); E(bl, "c_pmdidx"); E(mov_reg, 1, 4); E(mov_reg, 2, 7); E(bl, "c_pmdscan"); E(cmp_imm, 0, 0xFF); E(b_cond, "ps_o", "ne")
    E(movs_imm, 0, 0); E(mov_reg, 1, 4); E(mov_reg, 2, 7); E(bl, "c_pmdscan")
    a.label("ps_o"); E(mov_reg, 5, 0)
    a.label("ps_s"); E(movs_imm, 0, 4); E(str_sp, 0, 0)
    a.label("ps_x"); E(pop_list, [0, 1, 2, 3, 4, 6, 7]); E(raw, POP_LR); E(cmp_imm, 0, 3); E(raw, BX_LR)

    # ---- c_pmstart (in the track advance, in place of its bl to the direction getter: r1 = the track, r2 = the pattern that starts) -> the
    #      direction; an order of ours: r5 = its first step, the fractal's group back to one step, and a direction the stock skips
    a.label("c_pmstart")
    E(push_list, [1, 2, 4, 6, 7], lr=True)
    E(bl, DIR_GET); E(mov_reg, 6, 0)
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, "c_pminfo"); E(cmp_imm, 0, 0); E(b_cond, "pt_x", "eq")
    E(mov_reg, 4, 1); E(cmp_imm, 0, M_DEC); E(b_cond, "pt_f", "ne")
    E(movs_imm, 0, 0); E(bl, "c_pmdscan"); E(cmp_imm, 0, 0xFF); E(b_cond, "pt_x", "eq"); E(mov_reg, 5, 0); E(b, "pt_k")
    a.label("pt_f"); E(mov_reg, 5, 4)
    a.label("pt_k")
    E(mov_reg, 0, 11); E(cmp_imm, 0, 0); E(b_cond, "pt_4", "ne")
    E(ldr_sp, 0, 0); E(bl, "c_pmk"); E(cmp_imm, 0, 0); E(b_cond, "pt_4", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    a.label("pt_4"); E(movs_imm, 6, 4)
    a.label("pt_x"); E(mov_reg, 0, 6); E(pop_list, [1, 2, 4, 6, 7], pc=True)

    # ---- c_pmrot (r0 = an array, r1 = the size of an element (<= 28), r2 = its elements, r3 = k): the array rotated k elements to the left
    a.label("c_pmrot")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 32)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(muls, 6, 5); E(mov_reg, 7, 3)
    a.label("ro_k"); E(cmp_imm, 7, 0); E(b_cond, "ro_x", "eq")
    E(movs_imm, 0, 0); E(mov_reg, 2, 13)
    a.label("ro_1"); E(ldrb_reg, 1, 4, 0); E(strb_reg, 1, 2, 0); E(adds_imm8, 0, 1); E(cmp_reg, 0, 5); E(b_cond, "ro_1", "lo")
    E(mov_reg, 0, 5)
    a.label("ro_2"); E(cmp_reg, 0, 6); E(b_cond, "ro_3", "hs"); E(ldrb_reg, 1, 4, 0); E(subs_reg, 2, 0, 5); E(strb_reg, 1, 4, 2); E(adds_imm8, 0, 1); E(b, "ro_2")
    a.label("ro_3"); E(subs_reg, 3, 6, 5); E(movs_imm, 0, 0)
    a.label("ro_4"); E(mov_reg, 2, 13); E(ldrb_reg, 1, 2, 0); E(adds_reg, 2, 3, 0); E(strb_reg, 1, 4, 2); E(adds_imm8, 0, 1); E(cmp_reg, 0, 5); E(b_cond, "ro_4", "lo")
    E(subs_imm8, 7, 1); E(b, "ro_k")
    a.label("ro_x"); E(add_sp_imm, 32); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pmnudge (r0 = the Pattern Settings view, r1 = track (a note track), r2 = pattern): the pattern rotated so that its first step is
    #      step 1: the steps and the twelve automation lanes, over 16 or 32 steps; then first = 0 and the last step moved, through the view's store
    a.label("c_pmnudge")
    if DRUMS:
        # (SC40.9) a drum track: its four byte arrays and eight lanes.  [sp]: n, the new last step, the track then the lanes, the offset of the lanes
        E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
        E(mov_reg, 7, 0); E(str_sp, 1, 8); E(mov_reg, 0, 1); E(mov_reg, 1, 2); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); bc("nu_x", "eq")
        E(subs_imm8, 0, 4); E(ldrb_imm, 5, 0, 1); E(ldrb_imm, 6, 0, 0)                 # r5 = the first step, r6 = the last
        imm32(1, SET_OFF); E(ldr_sp, 2, 8); E(cmp_imm, 2, 4); E(b_cond, "nu_o", "lo"); E(movs_imm, 1, D_SET_OFF)
        a.label("nu_o"); E(subs_reg, 4, 0, 1)                                         # r4 = the pattern
        E(cmp_imm, 5, 0); bc("nu_x", "eq"); E(cmp_imm, 5, 31); bc("nu_x", "hi"); E(cmp_imm, 6, 31); bc("nu_x", "hi")
        E(movs_imm, 3, 32); E(cmp_imm, 5, 16); E(b_cond, "nu_n", "hs"); E(cmp_imm, 6, 16); E(b_cond, "nu_n", "hs"); E(movs_imm, 3, 16)
        a.label("nu_n"); E(str_sp, 3, 0)
        E(subs_reg, 6, 6, 5); E(b_cond, "nu_l", "pl"); E(adds_reg, 6, 6, 3)            # the new last step
        a.label("nu_l"); E(str_sp, 6, 4)
        E(ldr_sp, 0, 8); E(cmp_imm, 0, 4); E(b_cond, "nu_dr", "hs")
        E(mov_reg, 0, 4); E(movs_imm, 1, STEP_SZ); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
        E(movs_imm, 0, LANES); E(str_sp, 0, 8); imm32(0, AUTO_OFF); E(str_sp, 0, 12); E(b, "nu_la")
        a.label("nu_dr")
        E(movs_imm, 6, 0)
        a.label("nu_d1"); E(lsls_imm, 0, 6, 5); E(adds_reg, 0, 0, 4); E(movs_imm, 1, 1); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
        E(adds_imm8, 6, 1); E(cmp_imm, 6, D_ARRAYS); E(b_cond, "nu_d1", "lo")
        if DSYNC:                                                                     # drumpat's bytes; the drum's edit store
            E(mov_reg, 0, 4); E(adds_imm8, 0, 0x88); E(movs_imm, 1, 1); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
            E(ldr_sp, 0, 8); E(subs_imm8, 0, 4); E(mov_reg, 1, 4); E(bl, "c_pmdsync")
        E(movs_imm, 0, D_LANES); E(str_sp, 0, 8); E(movs_imm, 0, D_AUTO_OFF); E(str_sp, 0, 12)
        a.label("nu_la")
        E(movs_imm, 6, 0)
        a.label("nu_a")
        E(ldr_sp, 0, 12); E(adds_reg, 0, 0, 4); E(movs_imm, 1, LANE_SZ * 32); E(muls, 1, 6); E(adds_reg, 0, 0, 1)
        E(movs_imm, 1, LANE_SZ); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
        E(adds_imm8, 6, 1); E(ldr_sp, 0, 8); E(cmp_reg, 6, 0); E(b_cond, "nu_a", "lo")
        E(ldr_imm, 0, 7, 0xC); E(movs_imm, 1, 0); E(bl, MU.PARAM_WPTR)
        E(ldr_sp, 1, 4); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
        E(ldr_imm, 0, 7, 0xC); E(bl, MU.PARAM_COMMIT)
        a.label("nu_x"); E(add_sp_imm, 16); E(pop_list, [4, 5, 6, 7], pc=True)
    else:
        E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
        E(mov_reg, 7, 0); E(mov_reg, 0, 1); E(mov_reg, 1, 2); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); bc("nu_x", "eq")
        E(subs_imm8, 0, 4); E(ldrb_imm, 5, 0, 1); E(ldrb_imm, 6, 0, 0)                     # r5 = the first step, r6 = the last
        imm32(1, SET_OFF); E(subs_reg, 4, 0, 1)                                           # r4 = the pattern
        E(cmp_imm, 5, 0); bc("nu_x", "eq"); E(cmp_imm, 5, 31); bc("nu_x", "hi"); E(cmp_imm, 6, 31); bc("nu_x", "hi")
        E(movs_imm, 3, 32); E(cmp_imm, 5, 16); E(b_cond, "nu_n", "hs"); E(cmp_imm, 6, 16); E(b_cond, "nu_n", "hs"); E(movs_imm, 3, 16)
        a.label("nu_n"); E(str_sp, 3, 0)
        E(subs_reg, 6, 6, 5); E(b_cond, "nu_l", "pl"); E(adds_reg, 6, 6, 3)                # the new last step
        a.label("nu_l"); E(str_sp, 6, 4)
        E(mov_reg, 0, 4); E(movs_imm, 1, STEP_SZ); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
        E(movs_imm, 6, 0)
        a.label("nu_a")
        imm32(0, AUTO_OFF); E(adds_reg, 0, 0, 4); E(movs_imm, 1, LANE_SZ * 32); E(muls, 1, 6); E(adds_reg, 0, 0, 1)
        E(movs_imm, 1, LANE_SZ); E(ldr_sp, 2, 0); E(mov_reg, 3, 5); E(bl, "c_pmrot")
        E(adds_imm8, 6, 1); E(cmp_imm, 6, LANES); E(b_cond, "nu_a", "lo")
        E(ldr_imm, 0, 7, 0xC); E(movs_imm, 1, 0); E(bl, MU.PARAM_WPTR)
        E(ldr_sp, 1, 4); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
        E(ldr_imm, 0, 7, 0xC); E(bl, MU.PARAM_COMMIT)
        a.label("nu_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    if DSYNC:
        import drumstore
        drumstore.emit_syncall(a, "c_pmdsync")

    # ---- c_pmtp() -> r0 = the selected track, r1 = the pattern it plays; clobbers r2, r3
    a.label("c_pmtp")
    E(push_list, [4], lr=True)
    imm32(0, SM.SEL_STORE); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 4, 0, 0)
    imm32(0, ENG + 0x30); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET)
    E(ldrb_imm, 1, 0, 0); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_pmpspad (the Pattern Settings view's pad press: view, pad, velocity), a note track: pad 26 nudge, 27 / 28 an order of ours,
    #      29-32 the stock's direction (ours off)
    a.label("c_pmpspad")
    E(cmp_imm, 1, PAD_NUDGE); bc("pp_f", "lo"); E(cmp_imm, 1, 31); bc("pp_f", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 7, 0)
    if not DRUMS: E(bl, L["c_rfnt"]); bc("pp_c", "hs")
    E(bl, "c_pmtp"); E(mov_reg, 4, 0); E(mov_reg, 6, 1)
    E(cmp_imm, 5, PAD_NUDGE); E(b_cond, "pp_m", "ne")
    E(mov_reg, 0, 7); E(mov_reg, 1, 4); E(mov_reg, 2, 6); E(bl, "c_pmnudge"); E(b, "pp_x")
    a.label("pp_m")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); bc("pp_c", "eq")
    E(cmp_imm, 5, PAD_DIR); E(b_cond, "pp_d", "hs")
    E(subs_imm8, 5, PAD_FRAC - M_FRAC); E(strb_imm, 5, 0, 3)                           # (byte 7 of the settings = the rule's address + 3)
    E(mov_reg, 0, 4); E(bl, "c_pmk"); E(cmp_imm, 0, 0); E(b_cond, "pp_w", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    a.label("pp_w")                                                                   # the stock's direction: forward
    E(ldr_imm, 0, 7, 0xC); E(movs_imm, 1, 2); E(bl, MU.PARAM_WPTR); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    E(ldr_imm, 0, 7, 0xC); E(bl, MU.PARAM_COMMIT)
    a.label("pp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("pp_d"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 3)
    a.label("pp_c"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.label("pp_f"); E(b_w, prev["pspad"])

    # ---- c_pmpsbuf (the Pattern Settings view's LED buffer getter): pads 26-28 and the direction pads
    a.label("c_pmpsbuf")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0); E(ldr_imm, 0, 7, 4); E(ldr_imm, 5, 0, 0)
    def led(idx, reg): E(movs_imm, 0, 2 * idx); E(strh_reg, reg, 5, 0)
    if not DRUMS:
        E(bl, L["c_rfnt"]); E(b_cond, "pb_n", "lo")
        E(movs_imm, 1, 0); led(PAD_NUDGE, 1); led(PAD_FRAC, 1); led(PAD_DEC, 1); E(b, "pb_x")
        a.label("pb_n")
    E(bl, "c_pmtp"); E(bl, L["c_pcrule"]); E(movs_imm, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "pb_m", "eq"); E(ldrb_imm, 4, 0, 3)
    a.label("pb_m")
    E(movs_imm, 1, COL_NUDGE); led(PAD_NUDGE, 1)
    for idx, m in ((PAD_FRAC, M_FRAC), (PAD_DEC, M_DEC)):
        E(movs_imm, 1, COL_UNSEL); E(cmp_imm, 4, m); E(b_cond, f"pb_{idx}", "ne"); E(movs_imm, 1, COL_SEL)
        a.label(f"pb_{idx}"); led(idx, 1)
    E(ldr_imm, 0, 7, 0xC); E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0)
    E(cmp_imm, 4, 0); E(b_cond, "pb_d", "eq"); E(movs_imm, 6, 0xFF)                     # an order of ours: no direction pad chosen
    a.label("pb_d"); E(movs_imm, 3, 0)
    a.label("pb_l")
    E(movs_imm, 1, COL_UNSEL); E(cmp_reg, 3, 6); E(b_cond, "pb_w", "ne"); E(movs_imm, 1, COL_SEL)
    a.label("pb_w"); E(mov_reg, 0, 3); E(adds_imm8, 0, PAD_DIR); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 4); E(b_cond, "pb_l", "lo")
    a.label("pb_x"); E(mov_reg, 0, 7); E(pop_list, [3, 4, 5, 6, 7]); E(raw, POP_LR); E(b_w, prev["psbuf"])

    # ---- c_pmledtask (the LED task calls: ctrl, frame): the chain; stopped: every fractal group back to one step
    a.label("c_pmledtask")
    E(push_list, [4], lr=True)
    E(bl, prev["ledtask"])
    imm32(0, MU.PLAY_STORE); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "ne")
    E(bl, L["c_pcst"]); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(adds_imm8, 0, S_K); E(movs_imm, 1, 0)
    for k in range(8): E(strb_imm, 1, 0, k)
    a.label("pl_x"); E(pop_list, [4], pc=True)
    if CLRMOD:
        # ---- c_pmclr (r0 = track, r1 = pattern): the 32 steps' random-mutate and dynamics to 0
        a.label("c_pmclr")
        E(push_list, [4], lr=True)
        E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "eq")
        E(subs_imm8, 0, 4); imm32(1, SET_OFF); E(subs_reg, 4, 0, 1); E(movs_imm, 2, 32)
        a.label("cl_l")
        E(movs_imm, 1, 0); E(strb_imm, 1, 4, 2); E(ldrb_imm, 1, 4, 3); E(movs_imm, 3, 0x70); E(raw, h(0x4399)); E(strb_imm, 1, 4, 3)   # bics r1, r3
        E(adds_imm8, 4, STEP_SZ); E(subs_imm8, 2, 1); E(b_cond, "cl_l", "ne")
        a.label("cl_x"); E(pop_list, [4], pc=True)
        # ---- c_pmclrpad (the Pattern Settings view's pad press): Clear held + pad 25 on a note track = c_pmclr on the pattern it plays
        a.label("c_pmclrpad")
        E(cmp_imm, 1, PAD_MODE2); E(b_cond, "cp_f", "ne")
        E(push_list, [0, 1, 2, 4], lr=True)
        imm32(0, SM.MGR); E(ldr_imm, 0, 0, MGR_HELD); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(lsls_imm, 0, 0, 31); E(b_cond, "cp_c", "eq")
        E(bl, L["c_rfnt"]); E(b_cond, "cp_c", "hs")
        E(bl, "c_pmtp"); E(bl, "c_pmclr")
        E(pop_list, [0, 1, 2, 4], pc=True)
        a.label("cp_c"); E(raw, h(0xE8BD) + h(0x4017))                                  # pop.w {r0, r1, r2, r4, lr}
        a.label("cp_f"); E(b_w, "c_pmpspad")
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the three hooks of the engine, the Pattern Settings view's slots 0 / 7 (in front of stepmod's), the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_pcrule=lab("patchain", "c_pcrule"), c_pcst=lab("patchain", "c_pcst"), c_rfnt=lab("stepmod", "c_rfnt"))
    prev = dict(pspad=u(PS_VT) & ~1, psbuf=u(PS_VT + 28) & ~1, ledtask=lab("xpatch", "c_xqledtask"))
    assert prev["pspad"] == lab("stepmod", "c_rfpspad") and prev["psbuf"] == lab("stepmod", "c_rfpsbuf")
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    put(END_HOOK, bl(END_HOOK, labels["c_pmend"]), DIR_OLD)
    put(STEP_HOOK, bl(STEP_HOOK, labels["c_pmstep"]), DIR_OLD)
    put(START_HOOK, bl(START_HOOK, labels["c_pmstart"]), bl(START_HOOK, DIR_GET))
    struct.pack_into("<I", img, PS_VT - BASE, labels["c_pmclrpad" if CLRMOD else "c_pmpspad"] | 1)
    struct.pack_into("<I", img, PS_VT + 28 - BASE, labels["c_pmpsbuf"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_pmledtask"])
    return labels, code, prev
