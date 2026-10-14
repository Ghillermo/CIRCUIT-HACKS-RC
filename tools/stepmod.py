"""SC40.3 (the user, 2026-10-13): two modes for the two lower rows of the probability view of the note tracks:

    mode 1 (Pattern Settings twice, as the stock opens that view)
                           row 3 = the stock probability
                           row 4 = FREQUENCY: pad n = the step sounds once every n times its pattern plays, the last of each n (pad 1 = always);
                                   the count starts again at every Play
    mode 2 (pad 25 of the Pattern Settings view, peach there on a note track)
                           row 3 = DYNAMICS: a random change of the velocity (V), and of the position and the length in micro steps (M, drawn
                                   apart for the two), per play:
                               pad 1 none | 2 M -3..0 | 3 M -3..0, V 0..+32 | 4 V 0..+32 | 5 M -2..+2, V 0..+32 | 6 M -2..+2 | 7 M 0..+3 | 8 V -32..+32
                           row 4 = the random-mutate of SC39 (tools/mutate39.py), as before
    The values stay in the step (they play whatever view is on the screen and are saved with the project).
    With mode 2 on the screen and recording, what the two rows of mode 2 produced is written into the step (the note, the velocity, the length,
    the position); otherwise nothing is written (SC39 wrote the mutated note whenever recording).

The step's byte [3] (free, as byte [2]: mutate39) holds the frequency - 1 (bits 0-2) and the dynamics (bits 4-6); they travel with the pattern.

The player (vtable 0x0805B750, one object per note track; + 4 = a random word the stock draws at tick 0 of every step, 0x0804A6B8, of which it only
uses bits 0-2 for the probability; + 8 = the track's store: pattern / step / tick; + 0x10 = the pattern's store: first and last step / sync rate):
  * 0x08040D4C(this, pattern, step, micro step, flag) builds, for one micro step, the mask of the step's units that start in it (this + 0x13C +
    micro step): the unit's bit in byte [0], the probability (byte [1] >= bits 0-2 of the random word), the unit's micro step (unit byte [2]).
    Its 14 bytes at 0x08040D8A (probability and micro step tests) -> bl c_rfmask, which adds:
      - the frequency: the pass = (the global tick - the tick within the step + half a step) / (the pattern's steps x the ticks per step); the
        step is left out unless pass % n = n - 1 (the global tick: the engine's store [0x20038ECC + 0x90], 0 at Play);
      - the position: the unit's micro step + an offset drawn from 4 bits of the step's random word (bits 3 + 4 x unit: the same for the six calls
        of a step), clamped to 0..5: a note never moves out of its step (a note on micro step 0 cannot go earlier).
  * 0x08040E5A plays the units of the mask: its two loads at 0x08040EFC already go to c_mutnote (SC39); now to c_rfnote = c_mutnote, then the
    velocity and the length (the stock generator, one call), then the writes when recording with mode 2 on the screen.
The views: slots 0 / 7 / 8 and the listener's thunk of the probability view (in front of mutate39's); slots 0 / 7 of the Pattern Settings view
(0x0805AB4C: its pads 0..15 first / last step, 16..23 sync rate, 28..31 direction; 24..27 were free): pad 25 on a note track = a tap of the
Pattern Settings button through the controller (the stock goes to the probability view) with "mode 2" asked; the LED task calls count the
passes.  "On the screen" = the probability view's LED buffer getter (slot 7) ran in the last three LED passes; a view that opens takes the mode
asked (else mode 1).  State: 2 bytes of the Master FX block's idle LED buffer (c_gst() + 146): tag, bit 0 the mode, bit 1 "row 3 must be redrawn
by the stock", bit 2 mode 2 asked, bits 4-5 the LED passes left.

SC40.4 (use_passcount(); the user, 2026-10-13: «arregla frecuencia añadiendo el contador»): the frequency counts the plays of each pattern
instead of the time since Play (with a chain of patterns the time is shared between them: "every 2" in a chain of two never sounded in one
pattern and always in the other).  32 counters (4 note tracks x 8 patterns) of 10 bits (0..839 = the least common multiple of 1..8), in the same
idle LED buffer: the low bytes at c_gst() + 148..179, the high pairs of bits at + 180..184 and + 140..142; they are cleared when the tag is
written (the CC editor's backup goes over these bytes: the counts start again) and by the LED task while the transport is stopped (state bit 3 =
"some count is not 0"), so every Play starts at 0.  The count of a pattern goes up where the stock ends a pass of it: in the track advance
0x0802CB3C, at 0x0802CD42 (the pattern's end flag r4 or the scene change flag [sp, #0x44], for the playing store only, fp = 0), in front of the
choice of the next pattern; the step of the next pass is built after it.  The step sounds when count % n = n - 1.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, lsls_imm,  # noqa: E402
                   lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, nop, orrs_reg, pop_list, push_list, raw, h, str_sp, strb_imm,
                   strb_reg, strh_reg, subs_imm8, subs_reg, tst_reg)
import packio as PK  # noqa: E402
import mutate39 as MU  # noqa: E402
import mpatch as MP  # noqa: E402
import sckn as SK  # noqa: E402

MASK_HOOK, MASK_BACK = 0x08040D8A, 0x08040D98
MASK_OLD = bytes.fromhex("6878704503d3a7799f4208bf1143")      # ldrb r0,[r5,#1]; cmp r0,lr; blo; ldrb r7,[r4,#6]; cmp r7,r3; it eq; orrs r1,r2
ENGINE, TICKS_TAB = 0x20038ECC, 0x0805B8B8                    # the sequencer engine (+ 0x90: the global tick's store); ticks per step by sync rate
PS_VT, PS_PAD, PS_BUF = 0x0805AB4C, 0x0804CE0C, 0x0804CF8C      # the Pattern Settings view: its pads (slot 0), its LED buffer getter (slot 7)
MGR, CONT, BTN_PRESS, BTN_RELEASE = 0x20040B10, 0x20040DB8, 0x08033320, 0x0803381A
SEL_STORE = CONT + 0x188                                      # the selected track (0..3 = the note tracks)
PS_TOGGLE, COL_TOGGLE = 24, MU.COL_LIT                        # pad 25, peach
ST_OFF, MAGIC = SK.ST_OFF + 2, 0x5D
STEP_BYTE, SH_FREQ, SH_DYN = 3, 0, 4
BTN_PS = 12                                                   # Pattern Settings
COL_FREQ, COL_DYN, COL_DIM = 0x2D, 0x17, 0x02                 # yellow, green, dim white (steady codes)
# dynamics by level: (M low, M high, V low, V high)
DYN = ((0, 0, 0, 0), (-3, 0, 0, 0), (-3, 0, 0, 32), (0, 0, 0, 32), (-2, 2, 0, 32), (-2, 2, 0, 0), (0, 3, 0, 0), (0, 0, -32, 32))
M_BIAS, V_BIAS = 8, 64
# SC40.7 (the user, 2026-10-14): the dynamics again: 2 drunk, 3 drunk and accents, 4 accents, 5 dragging and accents, 6 dragging, 7 balanced dynamics,
# 8 accent dynamics (pads 1..8 = levels 0..7)
DYN2 = ((0, 0, 0, 0), (-2, 2, 0, 0), (-2, 2, 0, 32), (0, 0, 0, 32), (-1, 3, 0, 32), (-1, 3, 0, 0), (0, 0, -32, 32), (0, 0, -32, 64))


def use_dyn2():
    global DYN
    DYN = DYN2


ENGINE_OBJ = 0x20038EC0                                       # the engine itself (0x20038ECC is its interface at + 0xC): + 0x30 + 4 t = the playing store of track t,
                                                              # + 0x50 the pattern's, + 0x70 the next one's, + 0x90 the global tick's (SC40.3 read ENGINE + 0x90: not the tick)
PASSCNT = False                                               # SC40.4: the frequency counts the plays of each pattern
PASS_HOOK, PASS_OLD = 0x0802CD42, bytes.fromhex("9df84410")   # ldrb.w r1, [sp, #0x44] in the track advance 0x0802CB3C
CNT_MAX, CNT_LOW, CNT_HI_A, CNT_HI_B, HI_SPLIT = 840, 2, 34, -6, 5     # (offsets from the state: + 148, + 180, + 140)
ST_COUNTS = 8                                                 # state bit 3


def use_passcount():
    global PASSCNT
    PASSCNT = True
MAX_LEN, MAX_MICRO = 0x60, 5
INV = dict(eq="ne", ne="eq", lo="hs", hs="lo", hi="ls", ls="hi", ge="lt", lt="ge", gt="le", le="gt", mi="pl", pl="mi")


def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def ldr_r9(rt, off): return h(0xF8D9) + h(rt << 12 | off)
def str_r9(rt, off): return h(0xF8C9) + h(rt << 12 | off)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def dyn_table():
    out = b""
    for mlo, mhi, vlo, vhi in DYN:
        out += bytes([mlo + M_BIAS, mhi - mlo + 1, vlo + V_BIAS, vhi - vlo + 1])
    return out


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_r{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def get(k): imm32(0, MU.PLAY_STORE); E(movs_imm, 1, k); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    t_dyn = base; E(raw, dyn_table())

    # ---- c_rfst() -> r0 = the state (tag written when the bytes were someone else's: mode 1), 0 without the block; clobbers r1-r3
    a.label("c_rfst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "rs_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "rs_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1)
    if PASSCNT: E(bl, "c_rfclr")
    a.label("rs_x"); E(pop_list, [4], pc=True)

    if PASSCNT:
        # ---- c_rfclr (r0 = the state): the 32 counts to 0; r0 kept, clobbers r1, r2
        a.label("c_rfclr")
        E(movs_imm, 1, 0); E(movs_imm, 2, CNT_LOW)
        a.label("cl_a"); E(strb_reg, 1, 0, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, CNT_HI_A + HI_SPLIT); E(b_cond, "cl_a", "lo")
        E(subs_imm8, 0, -CNT_HI_B); E(strb_imm, 1, 0, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 2); E(adds_imm8, 0, -CNT_HI_B)
        E(raw, h(0x4770))

        # ---- c_rfcadr (r0 = the counter 0..31, r5 = the state) -> r1 = the address of its low byte, r2 = of its high bits, r3 = their shift
        a.label("c_rfcadr")
        E(adds_reg, 1, 5, 0); E(adds_imm8, 1, CNT_LOW)
        E(movs_imm, 3, 3); E(ands_reg, 3, 0); E(lsls_imm, 3, 3, 1)
        E(lsrs_imm, 0, 0, 2); E(cmp_imm, 0, HI_SPLIT); E(b_cond, "ca_b", "hs")
        E(adds_imm8, 0, CNT_HI_A); E(b, "ca_j")
        a.label("ca_b"); E(subs_imm8, 0, HI_SPLIT - CNT_HI_B)
        a.label("ca_j"); E(adds_reg, 2, 5, 0); E(raw, h(0x4770))

        # ---- c_rfcget (r0 = the counter) -> r0 = the count (0 without the block); clobbers r1-r3
        a.label("c_rfcget")
        E(push_list, [4, 5, 6], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "cg_x", "eq")
        E(mov_reg, 5, 0); E(mov_reg, 0, 4); E(bl, "c_rfcadr")
        E(ldrb_imm, 0, 1, 0); E(ldrb_imm, 2, 2, 0); E(lsrs_reg, 2, 3); E(lsls_imm, 2, 2, 30); E(lsrs_imm, 2, 2, 22); E(orrs_reg, 0, 2)
        a.label("cg_x"); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_rfcinc (r0 = the counter): its count + 1 (839 -> 0); clobbers r0-r3
        a.label("c_rfcinc")
        E(push_list, [4, 5, 6], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "ci_x", "eq")
        E(mov_reg, 5, 0); E(mov_reg, 0, 4); E(bl, "c_rfcadr")
        E(ldrb_imm, 0, 1, 0); E(ldrb_imm, 6, 2, 0)
        E(mov_reg, 4, 6); E(lsrs_reg, 4, 3); E(lsls_imm, 4, 4, 30); E(lsrs_imm, 4, 4, 22); E(orrs_reg, 0, 4)
        E(adds_imm8, 0, 1); E(movw, 4, CNT_MAX); E(cmp_reg, 0, 4); E(b_cond, "ci_w", "lo"); E(movs_imm, 0, 0)
        a.label("ci_w")
        E(strb_imm, 0, 1, 0); E(lsrs_imm, 0, 0, 8)
        E(movs_imm, 4, 3); E(lsls_reg, 4, 3); E(bics_reg, 6, 4); E(lsls_reg, 0, 3); E(orrs_reg, 6, 0); E(strb_imm, 6, 2, 0)
        E(ldrb_imm, 0, 5, 1); E(movs_imm, 4, ST_COUNTS); E(orrs_reg, 0, 4); E(strb_imm, 0, 5, 1)
        a.label("ci_x"); E(pop_list, [4, 5, 6], pc=True)

        # ---- c_rfpass (from the track advance, in place of its ldrb.w r1, [sp, #0x44]): r4 = the pattern's end flag, fp = 0 for the playing
        #      store, [sp] = the track, r9 = the pattern that ends -> a note track's pattern played once more; r1 = [sp, #0x44]
        a.label("c_rfpass")
        E(raw, h(0xE92D) + h(0x500F))                                                 # push.w {r0-r3, r12, lr}
        E(raw, h(0xF89D) + h(0x0000 | (24 + 0x44))); E(orrs_reg, 0, 4); E(b_cond, "ps_x", "eq")
        E(raw, h(0xF1BB) + h(0x0F00)); E(b_cond, "ps_x", "ne")                        # cmp.w fp, #0
        E(raw, h(0xF89D) + h(0x0000 | 24)); E(cmp_imm, 0, 4); E(b_cond, "ps_x", "hs")
        E(lsls_imm, 0, 0, 3); E(mov_reg, 1, 9); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(adds_reg, 0, 0, 1); E(bl, "c_rfcinc")
        a.label("ps_x")
        E(raw, h(0xE8BD) + h(0x500F))                                                 # pop.w {r0-r3, r12, lr}
        E(raw, h(0xF89D) + h(0x1044)); E(raw, h(0x4770))

    # ---- c_rfrec() -> r0 = 1 when what mode 2 produces is to be written: mode 2 on the screen and recording; clobbers r1-r3
    a.label("c_rfrec")
    E(push_list, [4], lr=True)
    E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "rr_n", "eq")
    E(ldrb_imm, 4, 0, 1); E(lsrs_imm, 0, 4, 4); E(b_cond, "rr_n", "eq")
    E(movs_imm, 0, 1); E(ands_reg, 0, 4); E(b_cond, "rr_n", "eq")
    for k, skip in ((0, "eq"), (1, "eq"), (2, "ne")):
        get(k); E(cmp_imm, 0, 0); E(b_cond, "rr_n", skip)
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("rr_n"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_rfmask (from the mask builder, in place of its probability and micro step tests): r5 = the step, r4 = the unit - 4, r8 = the unit's
    #      number, r3 = the micro step, r2 = the unit's bit, r1 = the mask so far, r9 = the player -> r1 |= r2 when the unit starts here;
    #      lr = the probability threshold again (the loop's), r0 / r7 free there
    a.label("c_rfmask")
    E(mov_reg, 7, 14)
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7])
    E(raw, ldr_r9(0, 4)); E(mov_reg, 6, 0)                                            # r6 = the step's random word
    E(movs_imm, 1, 7); E(ands_reg, 1, 0)
    E(ldrb_imm, 0, 5, 1); E(cmp_reg, 0, 1); bc("fm_no", "lo")                         # the stock probability
    E(ldrb_imm, 0, 5, STEP_BYTE); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(b_cond, "fm_fq", "eq")
    # the frequency
    E(adds_imm8, 0, 1); E(mov_reg, 7, 0)                                              # r7 = n
    if PASSCNT:
        E(raw, ldr_r9(4, 8))                                                          # the track: whose playing store is the player's
        imm32(1, ENGINE_OBJ + 0x30); E(movs_imm, 5, 0)
        a.label("fq_l"); E(ldr_imm, 2, 1, 0); E(cmp_reg, 2, 4); E(b_cond, "fq_f", "eq")
        E(adds_imm8, 1, 4); E(adds_imm8, 5, 8); E(cmp_imm, 5, 32); E(b_cond, "fq_l", "lo"); E(b, "fm_fr")
        a.label("fq_f")
        E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(adds_reg, 0, 0, 5)
        E(bl, "c_rfcget")                                                             # the plays of this pattern so far
        E(raw, udiv(2, 0, 7)); E(muls, 2, 7); E(subs_reg, 0, 0, 2)
        E(adds_imm8, 0, 1); E(ldr_sp, 5, 20); E(cmp_reg, 0, 7); bc("fm_no", "ne")
    else:
        E(raw, ldr_r9(0, 0x10)); E(movs_imm, 1, 1); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(cmp_imm, 0, 7); E(b_cond, "fm_r", "ls"); E(movs_imm, 0, 7)
        a.label("fm_r")
        E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 1, 1, 0); E(ldr_imm, 4, 1, 0)   # r4 = the ticks per step
        E(raw, ldr_r9(0, 8)); E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0)
        E(lsrs_imm, 1, 4, 1); E(subs_reg, 5, 1, 0)                                        # r5 = half a step - the tick within the step
        E(raw, ldr_r9(0, 0x10)); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 2, 0, 0); E(ldrb_imm, 3, 0, 1)
        E(subs_reg, 0, 3, 2); E(adds_imm8, 0, 1); E(cmp_reg, 3, 2); E(b_cond, "fm_s", "hs"); E(adds_imm8, 0, 32)
        a.label("fm_s")
        E(muls, 4, 0); E(cmp_imm, 4, 0); E(b_cond, "fm_fr", "eq")                         # r4 = the ticks of one pass
        imm32(0, ENGINE + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0)
        E(adds_reg, 0, 0, 5)
        E(raw, udiv(1, 0, 4)); E(raw, udiv(2, 1, 7)); E(muls, 2, 7); E(subs_reg, 1, 1, 2)
        E(adds_imm8, 1, 1); E(ldr_sp, 5, 20); E(cmp_reg, 1, 7); bc("fm_no", "ne")
    a.label("fm_fr"); E(ldr_sp, 5, 20)
    a.label("fm_fq")
    # the micro step
    E(ldr_sp, 4, 16); E(ldrb_imm, 0, 4, 6)                                            # r0 = the unit's
    E(ldrb_imm, 1, 5, STEP_BYTE); E(lsrs_imm, 1, 1, SH_DYN); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(b_cond, "fm_cmp", "eq")
    E(lsls_imm, 1, 1, 2); imm32(2, t_dyn); E(adds_reg, 2, 2, 1)
    E(ldrb_imm, 3, 2, 1); E(cmp_imm, 3, 1); E(b_cond, "fm_cmp", "eq")                 # r3 = the span
    E(mov_reg, 1, 8); E(lsls_imm, 1, 1, 2); E(adds_imm8, 1, 3); E(mov_reg, 7, 1)      # r7 = the shift of the unit's four bits
    E(mov_reg, 1, 6); E(lsrs_reg, 1, 7); E(movs_imm, 5, 15); E(ands_reg, 1, 5)
    E(raw, udiv(5, 1, 3)); E(muls, 5, 3); E(subs_reg, 1, 1, 5)
    E(ldrb_imm, 5, 2, 0); E(adds_reg, 1, 1, 5); E(subs_imm8, 1, M_BIAS)               # the offset
    E(adds_reg, 1, 1, 0)
    E(cmp_imm, 1, 0); E(b_cond, "fm_l", "ge"); E(movs_imm, 1, 0)
    a.label("fm_l"); E(cmp_imm, 1, MAX_MICRO); E(b_cond, "fm_h", "le"); E(movs_imm, 1, MAX_MICRO)
    a.label("fm_h")
    E(ldr_sp, 3, 12); E(cmp_reg, 1, 3); E(b_cond, "fm_no", "ne")
    E(cmp_reg, 1, 0); E(b_cond, "fm_yes", "eq")
    E(mov_reg, 5, 1); E(mov_reg, 4, 2)                                                # r5 = the new micro step, r4 = the table's row
    E(bl, "c_rfrec"); E(cmp_imm, 0, 0); E(b_cond, "fm_yes", "eq")
    E(ldrb_imm, 1, 4, 0); E(movs_imm, 0, M_BIAS); E(subs_reg, 0, 0, 1)                # written: the unit's four bits = "offset 0" for the later calls
    E(movs_imm, 1, 15); E(lsls_reg, 1, 7); E(bics_reg, 6, 1); E(lsls_reg, 0, 7); E(orrs_reg, 6, 0); E(raw, str_r9(6, 4))
    E(ldr_sp, 4, 16); E(strb_imm, 5, 4, 6)
    E(b, "fm_yes")
    a.label("fm_cmp"); E(ldr_sp, 3, 12); E(cmp_reg, 0, 3); E(b_cond, "fm_no", "ne")
    a.label("fm_yes"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7]); E(orrs_reg, 1, 2); E(b, "fm_ret")
    a.label("fm_no"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7])
    a.label("fm_ret")
    E(raw, ldr_r9(0, 4)); E(lsls_imm, 0, 0, 29); E(lsrs_imm, 0, 0, 29); E(mov_reg, 14, 0)
    E(raw, h(0x4738))                                                                 # bx r7

    # ---- c_rfnote (from the player, in place of its two loads; as c_mutnote): r4 = the unit - 4, r7 = the unit's number, r0 = the player,
    #      r6 = [r4, #5] -> r5 = the note, sl = the velocity, r6 = the gate / tie; everything else as it was
    a.label("c_rfnote")
    E(push_list, [0, 1, 2, 3, 4, 5, 7], lr=True)                                      # sp: r0, r1 (the step's note), r2 (the write flag), r3, r4, r5, r7, lr
    E(ldrb_imm, 1, 4, 4); E(str_sp, 1, 4)
    E(bl, L["c_mutnote"])
    E(lsls_imm, 1, 7, 2); E(subs_reg, 7, 4, 1)                                        # r7 = the step
    E(bl, "c_rfrec"); E(str_sp, 0, 8)
    E(cmp_imm, 0, 0); E(b_cond, "fn_d", "ne")
    E(ldr_sp, 1, 4); E(strb_imm, 1, 4, 4)                                             # not to be written: the step keeps its note
    a.label("fn_d")
    E(ldrb_imm, 1, 7, STEP_BYTE); E(lsrs_imm, 1, 1, SH_DYN); E(movs_imm, 2, 7); E(ands_reg, 1, 2); bc("fn_x", "eq")
    E(lsls_imm, 1, 1, 2); imm32(2, t_dyn); E(adds_reg, 2, 2, 1); E(mov_reg, 7, 2)     # r7 = the table's row
    E(bl, MU.RANDOM)
    E(ldrb_imm, 3, 7, 3); E(lsrs_imm, 1, 0, 8); E(lsls_imm, 1, 1, 16); E(lsrs_imm, 1, 1, 16)
    E(raw, udiv(2, 1, 3)); E(muls, 2, 3); E(subs_reg, 1, 1, 2)
    E(ldrb_imm, 2, 7, 2); E(adds_reg, 1, 1, 2); E(subs_imm8, 1, V_BIAS)
    E(mov_reg, 3, 10); E(adds_reg, 1, 1, 3)
    E(cmp_imm, 1, 1); E(b_cond, "fn_v1", "ge"); E(movs_imm, 1, 1)
    a.label("fn_v1"); E(cmp_imm, 1, 127); E(b_cond, "fn_v2", "le"); E(movs_imm, 1, 127)
    a.label("fn_v2"); E(mov_reg, 10, 1)
    E(cmp_imm, 6, 0x80); E(b_cond, "fn_w", "hs")                                      # a tied unit keeps its length
    E(ldrb_imm, 3, 7, 1); E(lsrs_imm, 1, 0, 24)
    E(raw, udiv(2, 1, 3)); E(muls, 2, 3); E(subs_reg, 1, 1, 2)
    E(ldrb_imm, 2, 7, 0); E(adds_reg, 1, 1, 2); E(subs_imm8, 1, M_BIAS)
    E(adds_reg, 1, 1, 6)
    E(cmp_imm, 1, 1); E(b_cond, "fn_l1", "ge"); E(movs_imm, 1, 1)
    a.label("fn_l1"); E(cmp_imm, 1, MAX_LEN); E(b_cond, "fn_l2", "le"); E(movs_imm, 1, MAX_LEN)
    a.label("fn_l2"); E(mov_reg, 6, 1)
    a.label("fn_w")
    E(ldr_sp, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "fn_x", "eq")
    E(mov_reg, 1, 10); E(strb_imm, 1, 4, 7); E(strb_imm, 6, 4, 5)
    a.label("fn_x")
    E(str_sp, 5, 20)
    E(pop_list, [0, 1, 2, 3, 4, 5, 7], pc=True)

    # ---- c_rfset (view, value, shift): the 3 bits of the selected step's byte [3], with the stock's conditions for the probability
    a.label("c_rfset")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 7, 2)
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 0x10); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "se_go", "ne")
    E(ldr_imm, 0, 4, 0x10); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "se_go", "eq")
    E(ldr_imm, 0, 4, 0x14); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "se_x", "eq")
    a.label("se_go")
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 6, 0, 8)
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "se_x", "eq")   # a step without notes
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, MU.PARAM_WPTR)
    E(ldrb_imm, 1, 0, STEP_BYTE); E(movs_imm, 2, 7); E(lsls_reg, 2, 7); E(bics_reg, 1, 2); E(lsls_reg, 5, 7); E(orrs_reg, 1, 5); E(strb_imm, 1, 0, STEP_BYTE)
    E(mov_reg, 0, 6); E(bl, MU.PARAM_COMMIT)
    a.label("se_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_rfpad (view, pad, velocity): mode 1: row 4 (8..15) = the frequency; mode 2: row 3 (0..7) = the dynamics; the rest to the chain
    a.label("c_rfpad")
    E(cmp_imm, 1, 15); E(b_cond, "pd_f", "hi")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_rfst"); E(movs_imm, 4, 0); E(cmp_imm, 0, 0); E(b_cond, "pd_m", "eq")
    E(ldrb_imm, 4, 0, 1); E(movs_imm, 0, 1); E(ands_reg, 4, 0)
    a.label("pd_m")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4)
    E(cmp_imm, 4, 0); E(b_cond, "pd_t", "ne")
    E(cmp_imm, 1, 8); E(b_cond, "pd_c", "lo")
    E(subs_imm8, 1, 8); E(movs_imm, 2, SH_FREQ); E(bl, "c_rfset"); E(b, "pd_x")
    a.label("pd_t")
    E(cmp_imm, 1, 8); E(b_cond, "pd_c", "hs")
    E(movs_imm, 2, SH_DYN); E(bl, "c_rfset")
    a.label("pd_x"); E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("pd_c"); E(raw, popw([0, 1, 2, 3, 4], lr=True))
    a.label("pd_f"); E(b_w, prev["pad"])

    # ---- c_rfrow (view): mode 1: row 4 = the frequency as a yellow bar; mode 2: row 4 = mutate39's, row 3 = the dynamics (the chosen one green)
    a.label("c_rfrow")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0)
    E(bl, "c_rfst"); E(movs_imm, 7, 0); E(cmp_imm, 0, 0); E(b_cond, "rw_m", "eq")
    E(ldrb_imm, 7, 0, 1); E(movs_imm, 0, 1); E(ands_reg, 7, 0); E(b_cond, "rw_m", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_mutrow"])
    a.label("rw_m")
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET)
    E(ldrb_imm, 5, 0, 0); E(ldrb_imm, 6, 0, STEP_BYTE)
    E(cmp_imm, 7, 0); E(b_cond, "rw_s", "eq"); E(lsrs_imm, 6, 6, SH_DYN)
    a.label("rw_s"); E(movs_imm, 1, 7); E(ands_reg, 6, 1)
    E(ldr_imm, 0, 4, 4); E(ldr_imm, 4, 0, 0)                                          # r4 = the view's LEDs
    E(movs_imm, 3, 0)
    a.label("rw_l")
    E(movs_imm, 2, 0); E(cmp_imm, 5, 0); E(b_cond, "rw_w", "eq")
    E(movs_imm, 2, COL_DIM); E(cmp_imm, 7, 0); E(b_cond, "rw_t", "ne")
    E(cmp_reg, 3, 6); E(b_cond, "rw_w", "hi"); E(movs_imm, 2, COL_FREQ); E(b, "rw_w")
    a.label("rw_t"); E(cmp_reg, 3, 6); E(b_cond, "rw_w", "ne"); E(movs_imm, 2, COL_DYN)
    a.label("rw_w")
    E(mov_reg, 0, 3); E(cmp_imm, 7, 0); E(b_cond, "rw_i", "ne"); E(adds_imm8, 0, 8)
    a.label("rw_i"); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 4, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "rw_l", "lo")
    E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_rfled (view): the stock's listener, then our rows
    a.label("c_rfled_t"); E(subs_imm8, 0, 8)
    a.label("c_rfled")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, MU.PROB_LISTEN)
    E(mov_reg, 0, 4); E(bl, "c_rfrow")
    E(pop_list, [4], pc=True)

    # ---- c_rfbuf (view) -> its LED buffer (slot 7, every LED pass): the view is on the screen; row 3 back to the stock's after mode 2
    a.label("c_rfbuf")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 4, 0)
    E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "bf_r", "eq")
    E(mov_reg, 5, 0); E(ldrb_imm, 1, 5, 1)
    E(lsrs_imm, 2, 1, 4); E(b_cond, "bf_o", "ne")
    E(lsrs_imm, 1, 1, 2); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(adds_imm8, 1, 2)   # it opens: the mode asked (else mode 1), row 3 to be redrawn
    a.label("bf_o"); E(movs_imm, 2, 0x30); E(orrs_reg, 1, 2)
    E(movs_imm, 2, 2); E(tst_reg, 1, 2); E(b_cond, "bf_s", "eq")
    E(bics_reg, 1, 2); E(strb_imm, 1, 5, 1); E(mov_reg, 0, 4); E(bl, MU.PROB_LISTEN); E(b, "bf_r")
    a.label("bf_s"); E(strb_imm, 1, 5, 1)
    a.label("bf_r")
    E(mov_reg, 0, 4); E(bl, "c_rfrow")
    E(mov_reg, 0, 4); E(pop_list, [3, 4, 5]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, MU.PROB_BUF)     # ldr lr, [sp], #4

    # ---- c_rfnt() -> flags: lo when the selected track is a note track; clobbers r0-r3
    a.label("c_rfnt")
    E(push_list, [4], lr=True)
    imm32(0, SEL_STORE); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 4)
    E(pop_list, [4], pc=True)

    # ---- c_rfpspad (the Pattern Settings view: view, pad, velocity): pad 25 on a note track = the probability view in mode 2
    a.label("c_rfpspad")
    E(cmp_imm, 1, PS_TOGGLE); E(b_cond, "pp_f", "ne")
    E(push_list, [4], lr=True)
    E(bl, "c_rfnt"); E(b_cond, "pp_x", "hs")
    E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "pp_x", "eq")
    E(ldrb_imm, 1, 0, 1); E(movs_imm, 2, 4); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, 1)
    imm32(0, MGR); E(movs_imm, 1, BTN_PS); E(bl, BTN_PRESS)
    imm32(0, MGR); E(movs_imm, 1, BTN_PS); E(bl, BTN_RELEASE)
    a.label("pp_x"); E(pop_list, [4], pc=True)
    a.label("pp_f"); E(b_w, PS_PAD)

    # ---- c_rfpsbuf (the Pattern Settings view) -> its LED buffer (slot 7): pad 25 in peach on a note track
    a.label("c_rfpsbuf")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0)
    E(movs_imm, 5, 0); E(bl, "c_rfnt"); E(b_cond, "pb_w", "hs"); E(movs_imm, 5, COL_TOGGLE)
    a.label("pb_w")
    E(ldr_imm, 0, 4, 4); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 2 * PS_TOGGLE); E(strh_reg, 5, 0, 1)
    E(mov_reg, 0, 4); E(pop_list, [4, 5]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, PS_BUF)

    # ---- c_rfledtask (the LED task calls: ctrl, frame): the chain; one LED pass less to "the view is on the screen"
    a.label("c_rfledtask")
    if not PASSCNT:
        E(push_list, [4], lr=True)
        E(bl, prev["ledtask"])
        E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq")
        E(ldrb_imm, 1, 0, 1); E(lsrs_imm, 2, 1, 4); E(b_cond, "lt_x", "eq")
        E(subs_imm8, 1, 0x10); E(strb_imm, 1, 0, 1)
        a.label("lt_x"); E(pop_list, [4], pc=True)
        return a.assemble()
    E(push_list, [3, 4, 5], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_rfst"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq")
    E(mov_reg, 4, 0)
    E(ldrb_imm, 1, 4, 1); E(lsrs_imm, 2, 1, 4); E(b_cond, "lt_s", "eq")
    E(subs_imm8, 1, 0x10); E(strb_imm, 1, 4, 1)
    a.label("lt_s")
    if True:                                                                          # stopped: every count back to 0
        E(movs_imm, 2, ST_COUNTS); E(tst_reg, 1, 2); E(b_cond, "lt_x", "eq")
        get(0); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "ne")
        E(ldrb_imm, 1, 4, 1); E(movs_imm, 2, ST_COUNTS); E(bics_reg, 1, 2); E(strb_imm, 1, 4, 1)
        E(mov_reg, 0, 4); E(bl, "c_rfclr")
    a.label("lt_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the mask builder's tests -> c_rfmask, the player's loads -> c_rfnote, the probability view's slots 0 / 7 / 8 and its listener
    thunk, the Pattern Settings view's slots 0 / 7, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_mutnote=lab("mutate39", "c_mutnote"), c_mutrow=lab("mutate39", "c_mutrow"))
    prev = dict(pad=u(MU.PROB_VT) & ~1, ledtask=lab("compkn", "c_ckledtask"))
    assert u(PS_VT) == PS_PAD | 1 and u(PS_VT + 28) == PS_BUF | 1
    assert prev["pad"] == lab("mutate39", "c_mutpad") and u(MU.PROB_VT + 28) == lab("mutate39", "c_mutbuf") | 1 and u(MU.PROB_VT + 32) == lab("mutate39", "c_mutled") | 1
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    put(MASK_HOOK, bl(MASK_HOOK, labels["c_rfmask"]) + nop() * 5, MASK_OLD)
    assert MASK_HOOK + 14 == MASK_BACK
    put(MU.NOTE_LOAD, bl(MU.NOTE_LOAD, labels["c_rfnote"]), bl(MU.NOTE_LOAD, L["c_mutnote"]))
    if PASSCNT: put(PASS_HOOK, bl(PASS_HOOK, labels["c_rfpass"]), PASS_OLD)
    struct.pack_into("<I", img, MU.PROB_VT - BASE, labels["c_rfpad"] | 1)
    struct.pack_into("<I", img, MU.PROB_VT + 28 - BASE, labels["c_rfbuf"] | 1)
    struct.pack_into("<I", img, MU.PROB_VT + 32 - BASE, labels["c_rfled"] | 1)
    struct.pack_into("<I", img, MU.PROB_VT2 - BASE, labels["c_rfled_t"] | 1)
    struct.pack_into("<I", img, PS_VT - BASE, labels["c_rfpspad"] | 1)
    struct.pack_into("<I", img, PS_VT + 28 - BASE, labels["c_rfpsbuf"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_rfledtask"])
    return labels, code, prev
