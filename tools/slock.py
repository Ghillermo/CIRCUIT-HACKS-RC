"""SC49.5 / Beta 3.48 (the user, 2026-10-29): the drums' extra lane, phase 2: state locks, ramps, the drums' automation view.

    «What if we made a mode that trades resolution on all knobs … but saved all of them?»; «Can we interpolate sweeps instead of saving every
    instance?»; chosen: «Both, per drum», «4-bit», «Ramps + draw by hand»; «on automation view (shift held inside velocity or velocity pressed
    twice) touch begin and end steps» (hold the begin step, tap the end step); Velocity twice on a drum latches that view; «Record held +
    1-16/17-32» switches a drum between the lane and the state locks («It implies length/resolution»).

lanex (phase 1) keeps a 7-bit code in each drum step's spare bits.  A drum in state-lock mode (lanex's assignment 0x80) reads it as:
  0 = nothing, 1..80 = a state of the project's pool, 127 = a step inside a ramp.
  * a state = the 14 drum values without a lane, 4 bits each (7 of 8 B): codes 1-8 of persist19, the filter mode (code 9), the bitcrush
    nibble, the distortion type, the K3 attack / start / cut (the chromatic pitch keeps its exact steps in lane 0, dpitch.use_lane0).  The
    scaled ones (7 bits) at 16 levels with the ends and the middle exact: q 0..8 = 8 q, q 9..15 = 64 + 9 (q - 8);
  * the pool (80 states, 8 B each, in bytes nothing else uses): the record's tail + 376 (20), + 680 (28), and the 16 scenes' spare bytes 2-3 of
    their 8 track entries (2 states a scene; the stock's save / recall / Duplicate / Clear of a scene leave them, emulated on SC49.3).  Which
    states are in use comes from the steps themselves (the drums in state-lock mode, their 8 patterns): no table, no signature; a new state =
    an identical one if there is, else the first one no step uses;
  * playback (dpitch's c_dpauto at micro step 0: da_g -> c_slchr, in front of lanex's c_xlchr): a state's step sets all 14 values; a ramp step
    finds the states before and after it in the pattern and sets the values between them (the filter mode and the distortion type: the first
    one's, switching at the end), again at micro steps 1-5 (the drum players' slot 2, c_slplay);
  * recording (Record armed, playing): a turn of one of the 14 values' knobs = the step that plays gets a state of the values now; three in a
    row on a line (each value within one level of the straight line, the stepped ones equal) = the middle one and the steps between become
    ramp steps: a sweep keeps its start, its stops and its turns;
  * Record held + a step (snapall) = a state of the values now; Clear + a lane knob to the left = the lane of the pattern that plays erased;
  * the automation view: a drum's Velocity view with Shift held, or latched by Velocity pressed again there (again = off; leaving the view =
    off; on the drums fixed velocity stays on Shift + Velocity, dblpress's Velocity twice keeps it for the other tracks): steps with a code
    yellow (0x2D), in state-lock mode ramp steps dim yellow (0x2E) and holding a step and tapping another = a ramp between them (a state made
    from the values now where an end has none);
  * Record held + 1-16/17-32 in a drum's views = lane <-> state locks; switching in or out of the state locks erases the drum's lane in its 8
    patterns (lanex's c_xlset calls from Record + knob / chromatic pad go through c_slset too); Record held in state-lock mode = the 8 knob LEDs
    white.
Part a (the hole, hole.add): the tables and the pool's helpers; part b (the image's end, build_sc41_5.add of PartB): the rest and the hooks.

SC49.6 / Beta 3.49 (use_cue; the user, 2026-10-29: «record+step must produce momentary visual cue on the step (yellow while held)»): every
Record held + step snapshot (recinst's on MIDI 1 / 2, snapall's on Synth 1 / 2 and the drums, lanex's and ours) leaves the swallowed pad in
recinst's RAM + 3 (pad + 1, or pad + 0x41 for a drum's) until the pad is let go: the LED task paints that pad yellow meanwhile.
RAM: modmx.MXR + 0x20C0: + 0 latch, + 1 the held step, + 2 / + 6 the last two keyframe steps of a recording (per drum), + 10 the ramp being
played (per drum: step, before, after, their states), + 30 a scratch byte, + 32 a state, + 48 "SL01", + 64 the states in use (80 B)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm,  # noqa: E402
                   ldrb_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm,
                   str_sp, strb_imm, strb_reg, strh_reg, subs_imm8, subs_reg, tst_reg, ldrb_w)
from build_sc14 import udiv  # noqa: E402
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import lanex as LX  # noqa: E402

RAM = MX.MXR + 0x20C0
O_LATCH, O_HELD, O_KP, O_KQ, O_CTX, O_SCR, O_BUF, O_SIG, O_USED = 0, 1, 2, 6, 10, 30, 32, 48, 64
SIG = struct.unpack("<I", b"SL01")[0]
STATE, RAMP, NST = 0x80, 127, 80
SEG_A, N_A, SEG_B, N_B = 376, 20, 680, 28                       # the record's tail offsets; the scenes after (2 a scene)
SCENES = 0x40
DP0, DP_SZ, PAT_SZ, DP_VT = LX.DP0, LX.DP_SZ, LX.PAT_SZ, 0x0805B72C
CONT_VT, DGRID, PARAM_GET, TRANSPORT = 0x0805A62C, 0x20043094, 0x0803542C, 0x20011034
MGR, S_CUR = 0x20040B10, 0x152
ID_VEL, ID_PAIR = 10, 21
YELLOW, YELLOW_DIM = 0x2D, 0x2E
# the 14 values: kind << 4 | argument (0 = persist19's code, 1 = filter mode, 2 = bitcrush nibble, 3 = distortion type, 4 = K3)
PARAMS = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x19, 0x24, 0x30, 0x40, 0x41, 0x42]
NV = len(PARAMS)
# the knobs whose turn may change one of them (knob + 8 with Shift): K2 K3 K4 K6 K7 K8, Shift + K1 K2 K3 K4 K5 K7 K8
OURS = sum(1 << k for k in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15))
CUE = False                                                         # (SC49.6) Record held + step: the held step pad yellow until let go


def use_cue():
    global CUE
    CUE = True


def sdiv(rd, rn, rm): return h(0xFB90 | rn) + h(0xF0F0 | rd << 8 | rm)
def negs(rd, rm): return h(0x4240 | rm << 3 | rd)
def ldrh0(rt, rn): return h(0x8800 | rn << 3 | rt)                  # ldrh rt, [rn]
def lsrs_r(rdn, rm): return h(0x40C0 | rm << 3 | rdn)               # lsrs rdn, rm
def SUBSP(n): return h(0xB080 | n // 4)                             # sub sp, #n
def ADDSP(n): return h(0xB000 | n // 4)                             # add sp, #n
RET = h(0x4770)
# the functions in order (each calls only earlier ones): a prefix goes into the hole (install), the rest to the image's end (PartB)
ORDER = ['t_sltab', 'c_slram', 'c_slb', 'c_slnib', 'c_slcpy', 'c_slenc', 'c_slkind', 'c_sllerp', 'c_slgetp', 'c_slsetp', 'c_slsnap', 'c_slpat',
         'c_slused', 'c_slalloc', 'c_slkey', 'c_slset', 'c_slapply', 'c_slctx', 'c_slpos', 'c_slnear', 'c_slchr', 'c_slplay', 'c_slcol', 'c_slrec',
         'c_sldrum', 'c_sldv', 'c_slknob', 'c_slkled', 'c_slbtn', 'c_slauto', 'c_slpage', 'c_slramp', 'c_slpad', 'c_slrel', 'c_slled', 'c_slsnp']


def arm_code(base, L, prev, lo, hi, tabaddr, ext=None):
    """The functions ORDER[lo:hi] at base (each calls only earlier ones, L or prev): part a = a prefix in the hole, part b = the rest."""
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    on = lambda n: lo <= ORDER.index(n) < hi
    t_ours, t_par = tabaddr, tabaddr + 2
    if on("t_sltab"):
        tab = bytes([OURS & 0xFF, OURS >> 8]) + bytes(PARAMS)
        a.label("t_sltab"); E(raw, tab + bytes(-len(tab) % 4))
    if on("c_slram"):
        # ---- c_slram() -> r0 = RAM (made the first time: the latch off, the held step, the keyframes and the ramps none); clobbers r1, r2
        a.label("c_slram")
        imm32(0, RAM); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "sr_x", "eq")
        E(str_imm, 2, 0, O_SIG); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_LATCH); E(movs_imm, 1, 0xFF); E(movs_imm, 2, O_HELD)
        a.label("sr_l"); E(strb_reg, 1, 0, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, O_SCR); E(b_cond, "sr_l", "lo")
        a.label("sr_x"); E(raw, RET)
    if on("c_slb"):
        # ---- c_slb(r0 = state 1..80, r1 = byte 0..7) -> r0 = its address, or 0; clobbers r2, r3
        a.label("c_slb")
        E(push_list, [4], lr=True); E(subs_imm8, 0, 1); E(mov_reg, 4, 0)
        imm32(0, LX.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 4, NST); E(b_cond, "sb_z", "hs"); E(cmp_imm, 0, 0); E(b_cond, "sb_x", "eq")
        E(cmp_imm, 4, N_A); E(b_cond, "sb_b", "hs"); imm32(2, LX.TAIL + SEG_A); E(b, "sb_l")
        a.label("sb_b"); E(cmp_imm, 4, N_A + N_B); E(b_cond, "sb_c", "hs"); E(subs_imm8, 4, N_A); imm32(2, LX.TAIL + SEG_B)
        a.label("sb_l"); E(adds_reg, 0, 0, 2); E(lsls_imm, 3, 4, 3); E(adds_reg, 0, 0, 3); E(adds_reg, 0, 0, 1); E(b, "sb_x")
        a.label("sb_c"); E(subs_imm8, 4, N_A + N_B)                                              # the scenes: 2 a scene, i = 8 (k & 1) + byte
        E(lsrs_imm, 2, 4, 1); E(movs_imm, 3, 40); E(muls, 3, 2); E(adds_reg, 0, 0, 3); E(adds_imm8, 0, SCENES + 2)
        E(movs_imm, 2, 1); E(ands_reg, 2, 4); E(lsls_imm, 2, 2, 3); E(adds_reg, 2, 2, 1)              # + i + (i & ~1)
        E(adds_reg, 0, 0, 2); E(lsrs_imm, 2, 2, 1); E(lsls_imm, 2, 2, 1); E(adds_reg, 0, 0, 2)
        a.label("sb_x"); E(pop_list, [4], pc=True)
        a.label("sb_z"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)
    if on("c_slnib"):
        # ---- c_slnib(r0 = state, r1 = value 0..13) -> r0 = its 4 bits; clobbers r1-r3
        a.label("c_slnib")
        E(push_list, [4], lr=True); E(mov_reg, 4, 1); E(lsrs_imm, 1, 1, 1); E(bl, "c_slb"); E(cmp_imm, 0, 0); E(b_cond, "sn_x", "eq")
        E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 1); E(tst_reg, 4, 1); E(b_cond, "sn_e", "eq"); E(lsrs_imm, 0, 0, 4)
        a.label("sn_e"); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
        a.label("sn_x"); E(pop_list, [4], pc=True)
    if on("c_slcpy"):
        # ---- c_slcpy(r0 = state, r1 = buffer, r2 = 0 write the state / 1 compare) -> r0 = 1 when equal (compare); clobbers r1-r3
        a.label("c_slcpy")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(movs_imm, 7, 0)
        a.label("sc_l")
        E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_slb"); E(cmp_imm, 0, 0); E(b_cond, "sc_n", "eq"); E(ldrb_reg, 1, 5, 7)
        E(cmp_imm, 6, 0); E(b_cond, "sc_c", "ne"); E(strb_imm, 1, 0, 0); E(b, "sc_s")
        a.label("sc_c"); E(ldrb_imm, 0, 0, 0); E(cmp_reg, 0, 1); E(b_cond, "sc_n", "ne")
        a.label("sc_s"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "sc_l", "lo")
        E(movs_imm, 0, 1); E(pop_list, [4, 5, 6, 7], pc=True)
        a.label("sc_n"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slenc"):
        # ---- c_slenc(r0 = 0..127) -> 4 bits; c_sldec(r0 = 4 bits) -> 0..127; clobber r1
        a.label("c_slenc")
        E(cmp_imm, 0, 64); E(b_cond, "se_h", "gt"); E(adds_imm8, 0, 4); E(lsrs_imm, 0, 0, 3); E(raw, RET)
        a.label("se_h"); E(subs_imm8, 0, 60); E(movs_imm, 1, 57); E(muls, 0, 1); E(lsrs_imm, 0, 0, 9); E(adds_imm8, 0, 8)
        E(cmp_imm, 0, 15); E(b_cond, "se_x", "ls"); E(movs_imm, 0, 15)
        a.label("se_x"); E(raw, RET)
        a.label("c_sldec")
        E(cmp_imm, 0, 8); E(b_cond, "sd_h", "hi"); E(lsls_imm, 0, 0, 3); E(raw, RET)
        a.label("sd_h"); E(subs_imm8, 0, 8); E(movs_imm, 1, 9); E(muls, 0, 1); E(adds_imm8, 0, 64); E(raw, RET)
    if on("c_slkind"):
        # ---- c_slkind(r1 = value 0..13) -> r2 = its kind, r3 = its argument (leaf)
        a.label("c_slkind")
        imm32(2, t_par); E(ldrb_reg, 3, 2, 1); E(lsrs_imm, 2, 3, 4); E(lsls_imm, 3, 3, 28); E(lsrs_imm, 3, 3, 28); E(raw, RET)
    if on("c_sllerp"):
        # ---- c_sllerp(r0 = a, r1 = b, r2 = pos | span << 8 (| more above)) -> r0 = a + (b - a) pos / span (a without a span); leaf
        a.label("c_sllerp")
        E(lsrs_imm, 3, 2, 8); E(lsls_imm, 3, 3, 24); E(lsrs_imm, 3, 3, 24); E(cmp_imm, 3, 0); E(b_cond, "sl_x", "eq")
        E(subs_reg, 1, 1, 0); E(lsls_imm, 2, 2, 24); E(lsrs_imm, 2, 2, 24); E(muls, 1, 2); E(raw, sdiv(1, 1, 3)); E(adds_reg, 0, 0, 1)
        a.label("sl_x"); E(raw, RET)
    if on("c_slgetp"):
        # ---- c_slgetp(r0 = drum, r1 = value 0..13) -> r0 = its 4 bits now; clobbers r1-r3
        a.label("c_slgetp")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(bl, "c_slkind"); E(mov_reg, 5, 3); E(mov_reg, 0, 4)
        E(cmp_imm, 2, 0); E(b_cond, "sg_1", "ne"); E(mov_reg, 1, 5); E(bl, L["c_xlget"]); E(adds_imm8, 0, 1); E(b_cond, "sg_z", "eq"); E(subs_imm8, 0, 1); E(b, "sg_e")
        a.label("sg_1"); E(cmp_imm, 2, 1); E(b_cond, "sg_2", "ne"); E(movs_imm, 1, 9); E(bl, L["c_dget"]); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(b, "sg_x")
        a.label("sg_2"); E(cmp_imm, 2, 2); E(b_cond, "sg_3", "ne"); E(movs_imm, 1, 4); E(bl, L["c_dnib_get"]); E(b, "sg_x")
        a.label("sg_3"); E(cmp_imm, 2, 3); E(b_cond, "sg_4", "ne"); E(bl, L["c_xt_get"]); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(b, "sg_x")
        a.label("sg_4"); E(mov_reg, 1, 5); E(bl, L["c_k3get"])
        a.label("sg_e"); E(bl, "c_slenc")
        a.label("sg_x"); E(pop_list, [4, 5], pc=True)
        a.label("sg_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)
    if on("c_slsetp"):
        # ---- c_slsetp(r0 = drum, r1 = value 0..13, r2 = 0..127 (scaled) / the value (the others)): set (persist19's codes and the filter mode
        #      when they differ); clobbers r0-r3
        a.label("c_slsetp")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 2); E(bl, "c_slkind"); E(mov_reg, 5, 3); E(mov_reg, 6, 2)
        E(cmp_imm, 6, 0); E(b_cond, "ss_1", "ne"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, L["c_xlput"]); E(b, "ss_x")
        a.label("ss_1"); E(cmp_imm, 6, 1); E(b_cond, "ss_2", "ne")
        E(mov_reg, 0, 4); E(movs_imm, 1, 9); E(bl, L["c_dget"]); E(adds_imm8, 0, 1); E(b_cond, "ss_x", "eq"); E(subs_imm8, 0, 1)
        E(movs_imm, 1, 7); E(ands_reg, 1, 0); E(cmp_reg, 1, 7); E(b_cond, "ss_x", "eq")
        E(movs_imm, 1, 7); E(bics_reg, 0, 1); E(orrs_reg, 0, 7); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(movs_imm, 1, 9); E(bl, L["c_dput"])
        E(movs_imm, 5, 9); E(b, "ss_m")
        a.label("ss_2"); E(cmp_imm, 6, 2); E(b_cond, "ss_3", "ne")
        E(mov_reg, 0, 4); E(movs_imm, 1, 4); E(mov_reg, 2, 7); E(bl, L["c_dnib_set"]); E(movs_imm, 5, 10); E(b, "ss_m")
        a.label("ss_3"); E(cmp_imm, 6, 3); E(b_cond, "ss_4", "ne")
        E(mov_reg, 0, 4); E(bl, L["c_xt_get"]); E(movs_imm, 1, 3); E(bics_reg, 0, 1); E(orrs_reg, 0, 7); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, L["c_xt_set"]); E(movs_imm, 5, 10); E(b, "ss_m")
        a.label("ss_4")
        E(cmp_imm, 5, 0); E(b_cond, "ss_k", "eq"); E(cmp_imm, 7, 120); E(b_cond, "ss_k", "ls"); E(movs_imm, 7, 120)          # start / cut: 120 at most
        a.label("ss_k"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, L["c_k3put"]); E(b, "ss_x")
        a.label("ss_m"); E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "ss_x", "eq"); E(mov_reg, 1, 5); E(bl, L["c_mark"])
        a.label("ss_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slsnap"):
        # ---- c_slsnap(r0 = drum, r1 = an 8-byte buffer, word aligned): the 14 values now; clobbers r0-r3
        a.label("c_slsnap")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 0, 0); E(str_imm, 0, 5, 0); E(str_imm, 0, 5, 4); E(movs_imm, 6, 0)
        a.label("sp_l")
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_slgetp")
        E(lsrs_imm, 1, 6, 1); E(ldrb_reg, 2, 5, 1); E(movs_imm, 3, 1); E(tst_reg, 6, 3); E(b_cond, "sp_e", "eq"); E(lsls_imm, 0, 0, 4)
        a.label("sp_e"); E(orrs_reg, 2, 0); E(strb_reg, 2, 5, 1)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "sp_l", "lo")
        E(pop_list, [4, 5, 6], pc=True)
    if on("c_slpat"):
        # ---- c_slpat(r0 = drum, r1 = pattern) -> r0 = the pattern's base; clobbers r1, r2.  c_slsel(r0 = drum) -> the selected one's (drumarp)
        a.label("c_slpat")
        E(movs_imm, 2, DP_SZ); E(muls, 2, 0); imm32(0, DP0); E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0x48)
        E(movw, 2, PAT_SZ); E(muls, 1, 2); E(adds_reg, 0, 0, 1); E(raw, RET)
        a.label("c_slsel")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_dapat"]); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_slpat"); E(pop_list, [4], pc=True)
    if on("c_slused"):
        # ---- c_slused() -> r0 = RAM, its + O_USED .. = 1 for each state a step of a drum in state-lock mode uses; clobbers r1-r3
        a.label("c_slused")
        E(push_list, [4, 5, 6, 7], lr=True); E(bl, "c_slram"); E(mov_reg, 7, 0)
        E(movs_imm, 1, 0); E(movs_imm, 2, 0)
        a.label("su_z"); E(adds_reg, 3, 7, 2); E(adds_imm8, 3, O_USED); E(strb_imm, 1, 3, 0); E(adds_imm8, 2, 1); E(cmp_imm, 2, NST); E(b_cond, "su_z", "lo")
        E(movs_imm, 4, 0)
        a.label("su_d"); E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "su_dn", "ne"); E(movs_imm, 5, 0)
        a.label("su_p"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_slpat"); E(mov_reg, 6, 0); E(movs_imm, 2, 0)
        a.label("su_s"); E(mov_reg, 0, 6); E(mov_reg, 1, 2); E(bl, L["c_xlrd"]); E(subs_imm8, 0, 1); E(cmp_imm, 0, NST); E(b_cond, "su_sn", "hs")
        E(adds_reg, 0, 7, 0); E(adds_imm8, 0, O_USED); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 0)
        a.label("su_sn"); E(adds_imm8, 2, 1); E(cmp_imm, 2, 32); E(b_cond, "su_s", "lo")
        E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "su_p", "lo")
        a.label("su_dn"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "su_d", "lo")
        E(mov_reg, 0, 7); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slalloc"):
        # ---- c_slalloc() -> r0 = a state holding RAM's buffer (an equal one in use, else the first free one, written), or 0; clobbers r1-r3
        a.label("c_slalloc")
        E(push_list, [4, 5, 6], lr=True); E(bl, "c_slused"); E(mov_reg, 5, 0); E(movs_imm, 6, 0); E(movs_imm, 4, 1)
        a.label("sa_l"); E(adds_reg, 0, 5, 4); E(adds_imm8, 0, O_USED - 1); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sa_u", "ne")
        E(cmp_imm, 6, 0); E(b_cond, "sa_n", "ne"); E(mov_reg, 6, 4); E(b, "sa_n")
        a.label("sa_u"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(adds_imm8, 1, O_BUF); E(movs_imm, 2, 1); E(bl, "c_slcpy"); E(cmp_imm, 0, 0); E(b_cond, "sa_y", "ne")
        a.label("sa_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, NST); E(b_cond, "sa_l", "ls")
        E(mov_reg, 4, 6); E(cmp_imm, 4, 0); E(b_cond, "sa_y", "eq")
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(adds_imm8, 1, O_BUF); E(movs_imm, 2, 0); E(bl, "c_slcpy")
        a.label("sa_y"); E(mov_reg, 0, 4); E(pop_list, [4, 5, 6], pc=True)
    if on("c_slkey"):
        # ---- c_slkey(r0 = drum, r1 = step, r2 = the pattern's base) -> r0 = the state the step got (the values now), or 0; clobbers r1-r3
        a.label("c_slkey")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, "c_slram"); E(adds_imm8, 0, O_BUF); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_slsnap")
        E(bl, "c_slalloc"); E(cmp_imm, 0, 0); E(b_cond, "sk_x", "eq"); E(push_list, [0])
        E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 3, 6); E(bl, L["c_xlwr"]); E(pop_list, [0])
        a.label("sk_x"); E(pop_list, [4, 5, 6], pc=True)
    if on("c_slset"):
        # ---- c_slset(r0 = drum, r1 = what the lane carries): lanex's c_xlset; in or out of the state locks = the lane erased in its 8 patterns
        a.label("c_slset")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, L["c_xlasg"])
        E(eors_reg, 0, 5); E(movs_imm, 1, STATE); E(tst_reg, 0, 1); E(b_cond, "st_e", "eq")                 # bit 7 the same: no erasing
        E(movs_imm, 6, 0)
        a.label("st_p"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_slpat"); E(mov_reg, 7, 0); E(movs_imm, 1, 0)
        a.label("st_s"); E(push_list, [1]); E(mov_reg, 0, 4); E(movs_imm, 2, 0); E(mov_reg, 3, 7); E(bl, L["c_xlwr"]); E(pop_list, [1])
        E(adds_imm8, 1, 1); E(cmp_imm, 1, 32); E(b_cond, "st_s", "lo"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "st_p", "lo")
        a.label("st_e"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_xlset"]); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slapply"):
        # ---- c_slapply(r0 = drum, r1 = state A, r2 = state B, r3 = pos | span << 8 | micro step 0 << 16): every value between A and B (the stepped
        #      ones A's, only at micro step 0); clobbers r0-r3
        a.label("c_slapply")
        E(push_list, [4, 5, 6, 7], lr=True); E(raw, SUBSP(8))                                     # [0] qa, [4] qb
        E(mov_reg, 4, 0); E(lsls_imm, 2, 2, 8); E(orrs_reg, 2, 1); E(mov_reg, 5, 2); E(mov_reg, 6, 3); E(movs_imm, 7, 0)
        a.label("ap_l")
        E(lsls_imm, 0, 5, 24); E(lsrs_imm, 0, 0, 24); E(mov_reg, 1, 7); E(bl, "c_slnib"); E(str_sp, 0, 0)
        E(lsrs_imm, 0, 5, 8); E(mov_reg, 1, 7); E(bl, "c_slnib"); E(str_sp, 0, 4)
        E(mov_reg, 1, 7); E(bl, "c_slkind")
        E(cmp_imm, 2, 1); E(b_cond, "ap_st", "eq"); E(cmp_imm, 2, 3); E(b_cond, "ap_st", "eq")
        E(cmp_imm, 2, 2); E(b_cond, "ap_sc", "ne")
        E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(b, "ap_lp")                                                    # the bitcrush nibble: its own scale
        a.label("ap_sc")                                                                                   # scaled: decoded, then between
        E(ldr_sp, 0, 4); E(bl, "c_sldec"); E(str_sp, 0, 4); E(ldr_sp, 0, 0); E(bl, "c_sldec"); E(ldr_sp, 1, 4)
        a.label("ap_lp"); E(mov_reg, 2, 6); E(bl, "c_sllerp"); E(b, "ap_set")
        a.label("ap_st"); E(lsrs_imm, 1, 6, 16); E(cmp_imm, 1, 0); E(b_cond, "ap_n", "eq"); E(ldr_sp, 0, 0)    # stepped: A's, at micro step 0
        a.label("ap_set"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_slsetp")
        a.label("ap_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, NV); E(b_cond, "ap_l", "lo")
        E(raw, ADDSP(8)); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slctx"):
        # ---- c_slctx(r0 = drum) -> r0 = its ramp context in RAM (step, before, after, A, B); clobbers r1, r2
        a.label("c_slctx")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_slram"); E(movs_imm, 1, 5); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, O_CTX)
        E(pop_list, [4], pc=True)
    if on("c_slpos"):
        # ---- c_slpos(r0 = a ramp context, r1 = step, r2 = micro step | micro step 0 << 16) -> r0 = r2 + pos | span << 8 (6 micro steps a step)
        a.label("c_slpos")
        E(push_list, [4], lr=True); E(ldrb_imm, 3, 0, 1); E(movs_imm, 4, 6)
        E(subs_reg, 1, 1, 3); E(muls, 1, 4); E(adds_reg, 2, 2, 1)                                         # + 6 (step - before)
        E(ldrb_imm, 1, 0, 2); E(subs_reg, 1, 1, 3); E(muls, 1, 4); E(lsls_imm, 1, 1, 8); E(orrs_reg, 2, 1)  # | 6 (after - before) << 8
        E(mov_reg, 0, 2); E(pop_list, [4], pc=True)
    if on("c_slnear"):
        # ---- c_slnear(r0 = a pattern's base, r1 = step, r2 = +1 / -1) -> r0 = the nearest state that way (0 none), r1 = its step; clobbers r2, r3
        a.label("c_slnear")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        a.label("nr_l"); E(adds_reg, 5, 5, 6); E(cmp_imm, 5, 31); E(b_cond, "nr_n", "hi")
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_xlrd"]); E(subs_imm8, 0, 1); E(cmp_imm, 0, NST); E(b_cond, "nr_l", "hs")
        E(adds_imm8, 0, 1); E(mov_reg, 1, 5); E(pop_list, [4, 5, 6], pc=True)
        a.label("nr_n"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)
    if on("c_slchr"):
        # ---- c_slchr (dpitch's c_dpauto at da_g, micro step 0: r5 = drum, r2 = step, r6 = lane 0's S or 0xFF, r7 = the player) -> r0 = c_dpcur(drum);
        #      lane mode = lanex's c_xlchr; state-lock mode = the step's state, or the ramp's values (its context kept for micro steps 1-5)
        a.label("c_slchr")
        E(push_list, [2, 4, 6, 7], lr=True)
        E(mov_reg, 0, 5); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "ch_s", "eq")
        E(pop_list, [2, 4, 6, 7]); E(pop_list, [3]); E(mov_reg, 14, 3); E(b_w, L["c_xlchr"])
        a.label("ch_s"); E(ldr_sp, 4, 0)                                                               # r4 = step
        E(mov_reg, 0, 5); E(bl, "c_slctx"); E(mov_reg, 7, 0); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 0)  # r7 = the context: no ramp
        E(mov_reg, 0, 5); E(bl, L["c_xlbase"]); E(mov_reg, 6, 0)                                     # r6 = base
        E(mov_reg, 1, 4); E(bl, L["c_xlrd"]); E(cmp_imm, 0, 0); E(b_cond, "ch_x", "eq")
        E(cmp_imm, 0, NST); E(b_cond, "ch_r", "hi")
        E(mov_reg, 1, 0); E(mov_reg, 2, 0); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 16); E(mov_reg, 0, 5); E(bl, "c_slapply"); E(b, "ch_x")
        a.label("ch_r"); E(cmp_imm, 0, RAMP); E(b_cond, "ch_x", "ne")
        E(mov_reg, 0, 6); E(mov_reg, 1, 4); E(movs_imm, 2, 1); E(raw, negs(2, 2)); E(bl, "c_slnear"); E(cmp_imm, 0, 0); E(b_cond, "ch_x", "eq")
        E(strb_imm, 0, 7, 3); E(strb_imm, 1, 7, 1)                                                    # A, before
        E(mov_reg, 0, 6); E(mov_reg, 1, 4); E(movs_imm, 2, 1); E(bl, "c_slnear"); E(cmp_imm, 0, 0); E(b_cond, "ch_x", "eq")
        E(strb_imm, 0, 7, 4); E(strb_imm, 1, 7, 2); E(strb_imm, 4, 7, 0)                             # B, after, the step: a ramp
        E(mov_reg, 0, 7); E(mov_reg, 1, 4); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 16); E(bl, "c_slpos"); E(mov_reg, 3, 0)
        E(ldrb_imm, 1, 7, 3); E(ldrb_imm, 2, 7, 4); E(mov_reg, 0, 5); E(bl, "c_slapply")
        a.label("ch_x"); E(mov_reg, 0, 5); E(bl, L["c_dpcur"]); E(pop_list, [2, 4, 6, 7], pc=True)
    if on("c_slplay"):
        # ---- c_slplay (the drum players' slot 2: this, pattern, step, micro step): the chain; micro steps 1-5 inside a ramp: the values between
        a.label("c_slplay")
        E(push_list, [0, 1, 2, 3, 4, 5], lr=True); E(mov_reg, 4, 0); E(bl, prev["play"]); E(str_sp, 0, 0)
        E(ldr_sp, 3, 12); E(cmp_imm, 3, 0); E(b_cond, "pl_x", "eq")
        imm32(1, DP0); E(subs_reg, 0, 4, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(5, 0, 1)); E(cmp_imm, 5, 3); E(b_cond, "pl_x", "hi")
        E(muls, 1, 5); E(cmp_reg, 1, 0); E(b_cond, "pl_x", "ne")
        E(mov_reg, 0, 5); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "pl_x", "ne")
        E(mov_reg, 0, 5); E(bl, "c_slctx"); E(mov_reg, 4, 0); E(ldrb_imm, 1, 0, 0); E(ldr_sp, 2, 8); E(cmp_reg, 1, 2); E(b_cond, "pl_x", "ne")
        E(mov_reg, 1, 2); E(ldr_sp, 2, 12); E(bl, "c_slpos"); E(mov_reg, 3, 0)
        E(ldrb_imm, 1, 4, 3); E(ldrb_imm, 2, 4, 4); E(mov_reg, 0, 5); E(bl, "c_slapply")
        a.label("pl_x"); E(pop_list, [0, 1, 2, 3, 4, 5], pc=True)
    if on("c_slcol"):
        # ---- c_slcol(r0 = state A, r1 = state M, r2 = state B, r3 = a | m << 8 | b << 16) -> r0 = 1 when M lies on the line A-B (each value within
        #      one level of it, the stepped ones equal); clobbers r1-r3
        a.label("c_slcol")
        E(push_list, [4, 5, 6, 7], lr=True); E(raw, SUBSP(16))                                              # [0] A [4] M [8] B [12] m - a | b - a << 8
        E(str_sp, 0, 0); E(str_sp, 1, 4); E(str_sp, 2, 8)
        E(lsls_imm, 0, 3, 24); E(lsrs_imm, 0, 0, 24); E(lsls_imm, 1, 3, 16); E(lsrs_imm, 1, 1, 24); E(subs_reg, 1, 1, 0)
        E(lsrs_imm, 2, 3, 16); E(subs_reg, 2, 2, 0); E(lsls_imm, 2, 2, 8); E(orrs_reg, 1, 2); E(str_sp, 1, 12); E(movs_imm, 7, 0)
        a.label("co_l")
        E(ldr_sp, 0, 0); E(mov_reg, 1, 7); E(bl, "c_slnib"); E(mov_reg, 4, 0)
        E(ldr_sp, 0, 4); E(mov_reg, 1, 7); E(bl, "c_slnib"); E(mov_reg, 5, 0)
        E(ldr_sp, 0, 8); E(mov_reg, 1, 7); E(bl, "c_slnib"); E(mov_reg, 6, 0)
        E(mov_reg, 1, 7); E(bl, "c_slkind"); E(cmp_imm, 2, 1); E(b_cond, "co_eq", "eq"); E(cmp_imm, 2, 3); E(b_cond, "co_eq", "eq")
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(ldr_sp, 2, 12); E(bl, "c_sllerp")
        E(subs_reg, 0, 5, 0); E(adds_imm8, 0, 1); E(cmp_imm, 0, 2); E(b_cond, "co_n", "hi"); E(b, "co_nx")
        a.label("co_eq"); E(cmp_reg, 4, 5); E(b_cond, "co_n", "ne"); E(cmp_reg, 5, 6); E(b_cond, "co_n", "ne")
        a.label("co_nx"); E(adds_imm8, 7, 1); E(cmp_imm, 7, NV); E(b_cond, "co_l", "lo")
        E(movs_imm, 0, 1); E(b, "co_r")
        a.label("co_n"); E(movs_imm, 0, 0)
        a.label("co_r"); E(raw, ADDSP(16)); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slrec"):
        # ---- c_slrec(r0 = drum): recording in state-lock mode, a value moved: a state of the values now at the step that plays; the line test
        #      with the last two keyframes of this pass (O_KQ, O_KP): on the line = the steps from O_KQ + 1 to here - 1 ramp steps
        a.label("c_slrec")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
        E(bl, L["c_xlbase"]); E(cmp_imm, 1, 31); E(b_cond, "rc_x", "hi"); E(mov_reg, 5, 0); E(mov_reg, 6, 1)
        E(bl, "c_slram"); E(mov_reg, 7, 0)
        E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(mov_reg, 2, 5); E(bl, "c_slkey"); E(cmp_imm, 0, 0); E(b_cond, "rc_x", "eq"); E(strb_imm, 0, 7, O_SCR)
        E(adds_reg, 3, 7, 4); E(ldrb_imm, 1, 3, O_KP); E(ldrb_imm, 2, 3, O_KQ)
        E(cmp_reg, 1, 6); E(b_cond, "rc_x", "eq")                                                           # the same step: rewritten
        E(cmp_imm, 1, 0xFF); E(b_cond, "rc_new", "eq"); E(cmp_reg, 6, 1); E(b_cond, "rc_new", "lo")         # none yet / behind: a new pass
        E(cmp_imm, 2, 0xFF); E(b_cond, "rc_sh", "eq")
        E(push_list, [1, 2])                                                                                 # [sp] kp, [4] kq
        E(mov_reg, 0, 5); E(mov_reg, 1, 2); E(bl, L["c_xlrd"]); E(push_list, [0])                           # [sp] A, [4] kp, [8] kq
        E(mov_reg, 0, 5); E(ldr_sp, 1, 4); E(bl, L["c_xlrd"]); E(mov_reg, 1, 0); E(ldr_sp, 0, 0)            # r0 = A, r1 = M
        E(mov_reg, 2, 0); E(subs_imm8, 2, 1); E(cmp_imm, 2, NST); E(b_cond, "rc_np", "hs")
        E(mov_reg, 2, 1); E(subs_imm8, 2, 1); E(cmp_imm, 2, NST); E(b_cond, "rc_np", "hs")
        E(ldr_sp, 3, 8); E(ldr_sp, 2, 4); E(lsls_imm, 2, 2, 8); E(orrs_reg, 3, 2); E(lsls_imm, 2, 6, 16); E(orrs_reg, 3, 2)   # kq | kp << 8 | s << 16
        E(ldrb_imm, 2, 7, O_SCR); E(bl, "c_slcol"); E(cmp_imm, 0, 0); E(b_cond, "rc_np", "eq")
        E(ldr_sp, 1, 8); E(adds_imm8, 1, 1)
        a.label("rc_f"); E(cmp_reg, 1, 6); E(b_cond, "rc_fe", "hs"); E(push_list, [1]); E(mov_reg, 0, 4); E(movs_imm, 2, RAMP); E(mov_reg, 3, 5)
        E(bl, L["c_xlwr"]); E(pop_list, [1]); E(adds_imm8, 1, 1); E(b, "rc_f")
        a.label("rc_fe"); E(raw, ADDSP(12)); E(adds_reg, 0, 7, 4); E(strb_imm, 6, 0, O_KP); E(b, "rc_x")
        a.label("rc_np"); E(raw, ADDSP(4)); E(pop_list, [1, 2])
        a.label("rc_sh"); E(adds_reg, 0, 7, 4); E(strb_imm, 1, 0, O_KQ); E(strb_imm, 6, 0, O_KP); E(b, "rc_x")
        a.label("rc_new"); E(adds_reg, 0, 7, 4); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, O_KQ); E(strb_imm, 6, 0, O_KP)
        a.label("rc_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_sldrum"):
        # ---- c_sldrum(r0 = a macro handler) -> r0 = its drum, or 4; clobbers r1-r3
        a.label("c_sldrum")
        E(push_list, [4, 5], lr=True); E(mov_reg, 5, 0); E(movs_imm, 4, 0)
        a.label("dd_l"); E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_reg, 0, 5); E(b_cond, "dd_x", "eq"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "dd_l", "lo")
        a.label("dd_x"); E(mov_reg, 0, 4); E(pop_list, [4, 5], pc=True)
    if on("c_sldv"):
        # ---- c_sldv(r0 = 0 a drum's views / 1 its Velocity view) -> r0 = the drum on the screen, or 4; clobbers r1-r3 (leaf)
        a.label("c_sldv")
        imm32(1, MGR); E(ldr_imm, 2, 1, 0x6C); E(ldr_imm, 3, 1, 0x2C); E(cmp_reg, 2, 3); E(b_cond, "dv_n", "ne")
        E(ldrb_w, 2, 1, S_CUR); E(subs_imm8, 2, 36); E(cmp_imm, 2, 31); E(b_cond, "dv_n", "hi")
        E(cmp_imm, 0, 0); E(b_cond, "dv_y", "eq"); E(movs_imm, 3, 7); E(ands_reg, 3, 2); E(cmp_imm, 3, 2); E(b_cond, "dv_n", "ne")
        a.label("dv_y"); E(lsrs_imm, 0, 2, 3); E(raw, RET)
        a.label("dv_n"); E(movs_imm, 0, 4); E(raw, RET)
    if on("c_slknob"):
        # ---- c_slknob (slot 4 of the drum macro handlers: handler, knob, delta): the chain (lanex); in state-lock mode Clear + a lane knob to the
        #      left = the lane of the playing pattern erased; recording (Record not held), one of the 14 values' knobs = c_slrec
        a.label("c_slknob")
        E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, prev["knob"]); E(str_sp, 0, 8)                                                                # the result in [sp + 8]
        E(mov_reg, 0, 4); E(bl, "c_sldrum"); E(cmp_imm, 0, 3); E(b_cond, "kn_x", "hi"); E(str_sp, 0, 4)    # [sp + 4] = drum
        E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "kn_x", "ne")
        E(bl, L["c_shift"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "kn_s", "eq"); E(movs_imm, 1, 8)
        a.label("kn_s"); E(adds_reg, 5, 5, 1)
        E(cmp_imm, 6, 0); E(b_cond, "kn_r", "ge")
        E(mov_reg, 0, 4); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "kn_r", "eq")
        imm32(0, L["t_xltab"]); E(ldrb_reg, 0, 0, 5); E(cmp_imm, 0, 0); E(b_cond, "kn_x", "eq")
        E(ldr_sp, 0, 4); E(bl, L["c_xlclr"]); E(b, "kn_x")
        a.label("kn_r")
        E(bl, L["c_xlheld"]); E(cmp_imm, 0, 0); E(b_cond, "kn_x", "ne")
        imm32(0, t_ours); E(raw, ldrh0(0, 0)); E(raw, lsrs_r(0, 5)); E(lsls_imm, 0, 0, 31); E(b_cond, "kn_x", "pl")
        E(bl, L["c_xlrec"]); E(cmp_imm, 0, 0); E(b_cond, "kn_x", "eq")
        E(ldr_sp, 0, 4); E(bl, "c_slrec")
        a.label("kn_x"); E(ldr_sp, 0, 8); E(str_sp, 0, 0); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    if on("c_slkled"):
        # ---- c_slkled (slot 7 of the drum macro handlers: handler -> the LED buffer): Record held in state-lock mode = the 8 knobs white
        a.label("c_slkled")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(bl, prev["kled"]); E(mov_reg, 5, 0)
        E(bl, L["c_xlheld"]); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq")
        E(mov_reg, 0, 4); E(bl, "c_sldrum"); E(cmp_imm, 0, 3); E(b_cond, "kl_x", "hi"); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "kl_x", "ne")
        E(movw, 0, LX.KNOB_WHITE); E(movs_imm, 1, 0)
        a.label("kl_l"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 16); E(b_cond, "kl_l", "lo")
        a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    if on("c_slbtn"):
        # ---- c_slbtn (the button press: ctrl, id): Record held + 1-16/17-32 in a drum's views = lane <-> state locks; Velocity with a drum's Velocity
        #      view on the screen (without Shift) = the automation view latched / unlatched (Shift + Velocity: the stock's fixed velocity); else the chain
        a.label("c_slbtn")
        E(push_list, [0, 1, 4], lr=True)
        E(cmp_imm, 1, ID_VEL); E(b_cond, "bt_v", "eq"); E(cmp_imm, 1, ID_PAIR); E(b_cond, "bt_p", "ne")
        E(bl, L["c_xlheld"]); E(cmp_imm, 0, 0); E(b_cond, "bt_p", "eq")
        E(movs_imm, 0, 0); E(bl, "c_sldv"); E(cmp_imm, 0, 3); E(b_cond, "bt_p", "hi"); E(mov_reg, 4, 0)
        E(bl, L["c_xlasg"]); E(movs_imm, 1, STATE); E(cmp_imm, 0, STATE); E(b_cond, "bt_t", "ne"); E(movs_imm, 1, 0)
        a.label("bt_t"); E(mov_reg, 0, 4); E(bl, "c_slset"); E(bl, L["c_xltaken"]); E(b, "bt_sw")
        a.label("bt_v"); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "bt_p", "ne")
        E(movs_imm, 0, 1); E(bl, "c_sldv"); E(cmp_imm, 0, 3); E(b_cond, "bt_p", "hi")
        E(bl, "c_slram"); E(ldrb_imm, 1, 0, O_LATCH); E(movs_imm, 2, 1); E(eors_reg, 1, 2); E(strb_imm, 1, 0, O_LATCH)
        a.label("bt_sw"); E(pop_list, [0, 1, 4], pc=True)
        a.label("bt_p"); E(pop_list, [0, 1, 4]); E(pop_list, [2]); E(mov_reg, 14, 2); E(b_w, prev["btn"])
    if on("c_slauto"):
        # ---- c_slauto() -> r0 = the drum whose automation view is on the screen (its Velocity view with Shift or the latch), or 4; clobbers r1-r3
        a.label("c_slauto")
        E(push_list, [4], lr=True); E(movs_imm, 0, 1); E(bl, "c_sldv"); E(cmp_imm, 0, 3); E(b_cond, "au_x", "hi"); E(mov_reg, 4, 0)
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "au_y", "ne")
        E(bl, "c_slram"); E(ldrb_imm, 0, 0, O_LATCH); E(cmp_imm, 0, 0); E(b_cond, "au_n", "eq")
        a.label("au_y"); E(mov_reg, 0, 4)
        a.label("au_x"); E(pop_list, [4], pc=True)
        a.label("au_n"); E(movs_imm, 0, 4); E(pop_list, [4], pc=True)
    if on("c_slpage"):
        # ---- c_slpage() -> r0 = the first step of the step pads (0 / 16); clobbers r1-r3
        a.label("c_slpage")
        E(push_list, [], lr=True); imm32(0, DGRID); E(ldr_imm, 0, 0, 0x58); E(movs_imm, 1, 2); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(lsls_imm, 0, 0, 4); E(pop_list, [], pc=True)
    if on("c_slramp"):
        # ---- c_slramp(r0 = drum, r1 = step, r2 = step): a ramp between them in the selected pattern (a state of the values now where an end has none)
        a.label("c_slramp")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
        E(cmp_reg, 1, 2); E(b_cond, "ra_o", "ls"); E(mov_reg, 3, 1); E(mov_reg, 1, 2); E(mov_reg, 2, 3)
        a.label("ra_o"); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(mov_reg, 0, 4); E(bl, "c_slsel"); E(mov_reg, 7, 0)
        for st, nm in ((5, "ra_1"), (6, "ra_2")):
            E(mov_reg, 0, 7); E(mov_reg, 1, st); E(bl, L["c_xlrd"]); E(subs_imm8, 0, 1); E(cmp_imm, 0, NST); E(b_cond, nm, "lo")
            E(mov_reg, 0, 4); E(mov_reg, 1, st); E(mov_reg, 2, 7); E(bl, "c_slkey")
            a.label(nm)
        E(adds_imm8, 5, 1)
        a.label("ra_l"); E(cmp_reg, 5, 6); E(b_cond, "ra_x", "hs"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, RAMP); E(mov_reg, 3, 7)
        E(bl, L["c_xlwr"]); E(adds_imm8, 5, 1); E(b, "ra_l")
        a.label("ra_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    if on("c_slpad"):
        # ---- c_slpad (slot 0 of the track views' container: cont, pad, velocity): the automation view of a drum in state-lock mode: hold a step,
        #      tap another = a ramp; the step pads swallowed there
        a.label("c_slpad")
        E(push_list, [0, 1, 2, 4, 5], lr=True)
        E(cmp_imm, 1, 15); E(b_cond, "pd_p", "hi")
        E(bl, "c_slauto"); E(cmp_imm, 0, 3); E(b_cond, "pd_p", "hi"); E(mov_reg, 4, 0)
        E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "pd_p", "ne")
        E(bl, "c_slpage"); E(ldr_sp, 1, 4); E(adds_reg, 5, 0, 1)                                             # r5 = the step
        E(bl, "c_slram"); E(ldrb_imm, 1, 0, O_HELD); E(cmp_imm, 1, 0xFF); E(b_cond, "pd_t", "ne"); E(strb_imm, 5, 0, O_HELD); E(b, "pd_sw")
        a.label("pd_t"); E(cmp_reg, 1, 5); E(b_cond, "pd_sw", "eq"); E(mov_reg, 0, 4); E(mov_reg, 2, 5); E(bl, "c_slramp")
        a.label("pd_sw"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
        a.label("pd_p"); E(pop_list, [0, 1, 2, 4, 5]); E(pop_list, [3]); E(mov_reg, 14, 3); E(b_w, prev["pad"])
    if on("c_slrel"):
        # ---- c_slrel (slot 1 of the container: cont, pad): a step pad let go while a step was held there: swallowed (the held one: let go)
        a.label("c_slrel")
        E(push_list, [0, 1], lr=True); E(bl, "c_slram"); E(ldrb_imm, 2, 0, O_HELD); E(cmp_imm, 2, 0xFF); E(b_cond, "rl_p", "eq")
        E(ldr_sp, 1, 4); E(cmp_imm, 1, 15); E(b_cond, "rl_p", "hi"); E(movs_imm, 3, 15); E(ands_reg, 2, 3); E(cmp_reg, 1, 2); E(b_cond, "rl_sw", "ne")
        E(movs_imm, 2, 0xFF); E(strb_imm, 2, 0, O_HELD)
        a.label("rl_sw"); E(pop_list, [0, 1], pc=True)
        a.label("rl_p"); E(pop_list, [0, 1]); E(pop_list, [2]); E(mov_reg, 14, 2); E(b_w, prev["rel"])
    if on("c_slled"):
        # ---- c_slled (the LED task's calls: ctrl, frame): the chain; stopped = no recording pass; the automation view: steps with a code yellow
        #      (state-lock mode: ramp steps dim yellow); the latch and the held step off away from a drum's Velocity view; (CUE) a snapshot's
        #      step pad held: yellow
        a.label("c_slled")
        E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1); E(bl, prev["led"])
        E(bl, "c_slram"); E(mov_reg, 7, 0)
        imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "le_r", "ne")
        E(movs_imm, 0, 0xFF); E(movs_imm, 1, O_KP)
        a.label("le_z"); E(strb_reg, 0, 7, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, O_CTX); E(b_cond, "le_z", "lo")
        a.label("le_r")
        E(movs_imm, 0, 1); E(bl, "c_sldv"); E(cmp_imm, 0, 3); E(b_cond, "le_d", "ls"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, O_LATCH)
        E(movs_imm, 0, 0xFF); E(strb_imm, 0, 7, O_HELD); E(b, "le_x")
        a.label("le_d"); E(bl, "c_slauto"); E(cmp_imm, 0, 3); E(b_cond, "le_x", "hi"); E(mov_reg, 4, 0)
        E(bl, "c_slsel"); E(mov_reg, 7, 0); E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(push_list, [0])
        E(bl, "c_slpage"); E(mov_reg, 4, 0); E(pop_list, [2]); E(movs_imm, 6, 0)                     # r2 = the mode (c_xlrd keeps it)
        a.label("le_l"); E(mov_reg, 0, 7); E(adds_reg, 1, 4, 6); E(bl, L["c_xlrd"]); E(cmp_imm, 0, 0); E(b_cond, "le_n", "eq")
        E(movs_imm, 1, YELLOW); E(cmp_imm, 2, STATE); E(b_cond, "le_c", "ne"); E(cmp_imm, 0, RAMP); E(b_cond, "le_c", "ne"); E(movs_imm, 1, YELLOW_DIM)
        a.label("le_c"); E(lsls_imm, 0, 6, 1); E(strh_reg, 1, 5, 0)
        a.label("le_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "le_l", "lo")
        a.label("le_x")
        if CUE:                                                                                         # a snapshot's pad held: yellow
            E(bl, L["c_rist"]); E(ldrb_imm, 0, 0, 3); E(subs_imm8, 0, 1); E(b_cond, "le_q", "mi")
            E(movs_imm, 1, 0x3F); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 1); E(movs_imm, 1, YELLOW); E(strh_reg, 1, 5, 0)
            a.label("le_q")
        E(pop_list, [3, 4, 5, 6, 7], pc=True)
    if on("c_slsnp"):
        # ---- c_slsnp (snapall's c_sacpad at cp_d, in place of lanex's bl c_xlsnap: r0 = the mark, r5 = the step): state-lock mode = a state of
        #      the values now at the step, then c_sadone; else lanex's c_xlsnap
        a.label("c_slsnp")
        E(push_list, [0, 4], lr=True)
        E(movs_imm, 0, 0); E(bl, "c_sldv"); E(mov_reg, 4, 0)                                          # (snapall checked the Note view)
        E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "np_l", "ne")
        E(mov_reg, 0, 4); E(bl, "c_slsel"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_slkey")
        E(pop_list, [0, 4]); E(pop_list, [1]); E(mov_reg, 14, 1); E(b_w, L["c_sadone"])
        a.label("np_l"); E(pop_list, [0, 4]); E(pop_list, [1]); E(mov_reg, 14, 1); E(b_w, L["c_xlsnap"])
    return a.assemble(external=ext) if ext else a.assemble()


def _labels(report):
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("lanex", k) for k in ("c_xlasg", "c_xlset", "c_xlbase", "c_xlrd", "c_xlwr", "c_xlget", "c_xlput", "c_xlrec", "c_xlheld",
                                       "c_xltaken", "c_xlclr", "c_xlchr", "c_xlpad", "t_xltab")}
    L.update({k: lab("lanexb", k) for k in ("c_xlknob", "c_xlkled", "c_xlsnap")})
    L.update({k: lab("persist19", k) for k in ("c_dget", "c_dput", "c_mark", "c_dnib_get", "c_dnib_set", "c_xt_get", "c_xt_set", "c_k3get",
                                                "c_k3put", "c_clr_held")})
    L.update(c_mh=lab("sc18", "c_mh"), c_shift=lab("sc15", "c_shift"), c_dpcur=lab("dpitch", "c_dpcur"), c_dapat=lab("drumarp", "c_dapat"),
             c_sadone=lab("snapall", "c_sadone"), c_rist=lab("recinst", "c_rist"))
    return L


def _prev(img):
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    return dict(knob=u(LX.MH_SLOT4) & ~1, kled=u(LX.MH_SLOT7) & ~1, btn=MP.bw_target(img, SV.BTN, BASE), pad=u(CONT_VT) & ~1,
                rel=u(CONT_VT + 4) & ~1, play=u(DP_VT + 8) & ~1, led=FD.bl_target(img, PK.LED_CALLS[0], BASE))


def install(img, report, base_addr):
    """Part a, at base_addr (hole.add): the longest prefix of ORDER that fits in what the hole has left; nothing patched."""
    import hole
    L, prev = _labels(report), _prev(img)
    for n in range(len(ORDER), 0, -1):
        code, labels = arm_code(base_addr, L, prev, 0, n, base_addr)
        if base_addr + ((len(code) + 3) & ~3) <= hole.HI:
            break
    LX._append(img, base_addr, code)
    return labels, code, {}


class PartB:
    """Part b, at the image's end (build_sc41_5.add, after part a): the rest of ORDER; da_g's and snapall's calls, lanex's two c_xlset calls,
    the heads of slots 4 / 7 of the drum macro handlers, of the button press, of slots 0 / 1 of the track views' container, of slot 2 of the
    drum players and of the LED task."""
    @staticmethod
    def install(img, report, base_addr):
        import ct_fw
        import hole
        BASE = ct_fw.APP_BASE
        rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
        lab = lambda m, k: int(report[m]["labels"][k], 16)
        L, prev = _labels(report), _prev(img)
        ext = {k: int(v, 16) for k, v in report["slock"]["labels"].items()}
        n = max(ORDER.index(k) for k in ext if k in ORDER) + 1
        assert prev["knob"] == L["c_xlknob"] and prev["kled"] == L["c_xlkled"], "slock: lanex's knob heads are not the first"
        for c in PK.LED_CALLS[1:]: assert FD.bl_target(img, c, BASE) == prev["led"], hex(c)
        da_g, cp_bl = lab("dpitch", "da_g"), lab("snapall", "cp_d") + 4
        assert rd(da_g, 4) == bl(da_g, L["c_xlchr"]) and rd(cp_bl, 4) == bl(cp_bl, L["c_xlsnap"])
        sets = []
        for lo, hi in ((L["c_xlpad"], L["c_xlpad"] + 0x60), (L["c_xlknob"], L["c_xlknob"] + 0x100)):
            sets += [x for x in range(lo, hi, 2) if rd(x, 4) == bl(x, L["c_xlset"])]
        assert len(sets) == 2, [hex(x) for x in sets]
        code, labels = arm_code(base_addr, L, prev, n, len(ORDER), ext["t_sltab"], ext)
        labels = {k: v for k, v in labels.items() if k not in ext}
        LX._append(img, base_addr, code)
        assert len(img) <= 0x70000, f"slock part b: the image is full ({len(img):#x})"
        A = {**ext, **labels}
        def put(at, data): img[at - BASE:at - BASE + len(data)] = data
        put(da_g, bl(da_g, A["c_slchr"])); put(cp_bl, bl(cp_bl, A["c_slsnp"]))
        for x in sets:
            put(x, bl(x, A["c_slset"])); hole.rehash(img, report, x)
        struct.pack_into("<I", img, LX.MH_SLOT4 - BASE, A["c_slknob"] | 1)
        struct.pack_into("<I", img, LX.MH_SLOT7 - BASE, A["c_slkled"] | 1)
        put(SV.BTN, b_w(SV.BTN, A["c_slbtn"]))
        struct.pack_into("<I", img, CONT_VT - BASE, A["c_slpad"] | 1)
        struct.pack_into("<I", img, CONT_VT + 4 - BASE, A["c_slrel"] | 1)
        struct.pack_into("<I", img, DP_VT + 8 - BASE, A["c_slplay"] | 1)
        for c in PK.LED_CALLS: put(c, bl(c, A["c_slled"]))
        prev.update(split=n)
        return labels, code, prev
