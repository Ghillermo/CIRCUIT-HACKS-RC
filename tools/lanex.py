"""SC49.2 / Beta 3.47 (the user, 2026-10-28 / 29: «is there any way to find more drum lanes?» -> «B: study hidden bits first»; «Assignable per drum»;
«Record held + knob»; «Chromatic pitch» by default; «While Record is held»): one more automation lane per drum, in the spare bits of each step.

The stock (read in the firmware, the 173 sessions of the card's copy, emulated): a drum pattern's step arrays are velocity + 0, probability + 0x20
(1..7: bits 3-7 always 0), sample flip + 0x40, micro steps + 0x60 (a mask of 6 bits: bits 6-7 always 0); the drum's edit store keeps them as
parameters 0-7, 8-15, 16-23 = the micro steps, 24-31 = the flips, and its setters replace a whole byte (0x0804A21C velocity, 0x0804A244 micro steps,
0x0804A270 probability, 0x0804A29C flip).  Copies (pattern <-> store, paste, move, Duplicate, Nudge) carry the whole bytes.
  * playback: the hit test 0x0804AA08 compares the whole probability byte with the random value & 7; the micro step bit is tested alone;
  * the probability view (0x0804F322) draws up to the whole byte; the Micro Step view ignores bits 6-7;
  * a hit added / removed (0x0804EC18 / 0x0804EC3E, 0x08050062 / 0x080500B2), the probability view's own (0x0804F2AE: the micro step byte written
    directly with a whole-byte mask), a flip on an empty step (0x0803E63E) and the probability view's pads (0x0804F300 / 0x0804F30C) reset the
    byte; Clear + step (0x0803E1A8) clears it, as it clears the step's lanes.

Ours: a 7-bit code a step = probability bits 3-7 (low 5 bits) + micro step bits 6-7 (high 2 bits); 0 = nothing, else the value + 1 (0..126).
  * the hit test: (random << 29) against (probability << 29) (the same 10 bytes, no hook); the probability view draws probability & 7; every
    resetting call above goes to a setter that keeps the spare bits (c_xlprb / c_xlmic), the view's own micro step byte through c_xlpvm;
  * a drum's lane carries one parameter, per project: the record's tail + 357: "X1", 4 bytes (0 = the chromatic pitch, 1..8 = persist19's mailbox
    codes: 1 pitch envelope, 2 ring mod frequency, 3 LFO amount, 4 LFO speed, 5 filter envelope, 6 resonance, 7 envelope shape, 8 ring mod amount),
    a check byte; without the block every drum carries the chromatic pitch;
  * playback (dpitch's c_dpauto at micro step 0, at da_g: bl c_xlchr): the chromatic lane gives the step's S when lane 0 has no chromatic step
    (lane 0 wins: older recordings); a code lane sets the drum's saved value (persist19's c_dput + c_mark; the tick sends it);
  * recording (Record armed, playing, no count-in): turning the assigned knob writes the step that plays; a chromatic pad writes the chromatic
    lane (dpitch's bl c_dplane in c_dppad -> c_xlplane: lane 0 is not written then);
  * Record held + a knob that carries a code = that drum's lane carries it; Record held + a chromatic pad = the chromatic pitch (the pad swallowed);
    Record's state back on its release (recinst's «a snapshot taken»);
  * Clear held + the lane's knob turned left (K1 for the chromatic pitch) = the lane of the pattern that plays erased;
  * Record held + a step (snapall) also writes the lane's value when it is not the default (S 64, the codes 0);
  * LEDs, Record held in a drum's views: the assigned knob white; the chromatic pitch = the Preset button blinking white.
RAM: MXR + 0x2000..0x20BF (where a chromatic pad's lane-0 bytes go when the chromatic lane takes them)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg,  # noqa: E402
                   ldrb_w, lsls_imm, lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, str_sp,
                   strb_imm, strh_reg, subs_imm8, ands_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

SESSION_OBJ, TAIL, O_BLK, SIG0, SIG1 = 0x2003D71C, 0x27024, 357, 0x58, 0x31        # "X1"
DP0, DP_SZ, PAT_SZ = 0x20040810, 0x90, 0x6A8
ENG, TRANSPORT = 0x20038EC0, 0x20011034
PARAM_GET, PARAM_WPTR = 0x0803542C, 0x080354FA
MH_VT = 0x0805AADC
MH_SLOT4, MH_SLOT7 = MH_VT + 0x10, MH_VT + 0x1C
MGR, S_CUR, DRUM_V0, DRUM_NOTE0 = 0x20040B10, 0x152, 36, 37
HAL_TICK = 0x2000081C
SCRATCH = MX.MXR + 0x2000
LED_PRESET, WHITE, KNOB_WHITE = 32 + 8, 0x01, (127 + 2) << 8 | 0x01
CHROM = 0x80                                     # (the knob table) K1 without Shift: the chromatic lane's knob for Clear
PLAIN = {0: CHROM, 1: 2, 3: 5, 5: 6, 6: 3}         # knob -> code without Shift (persist19.REMAP_PLAIN; K1 = the stock pitch)
SHIFTED = {0: 1, 1: 8, 3: 7, 6: 4}                # with Shift (persist19.REMAP_SHIFT, without the filter mode)
BIP = (1, 3, 4, 5, 7)                             # persist19's bipolar codes (two's complement in bits 0-6)

# the stock's code patched in place
HIT_AT, HIT_OLD = 0x0804AA14, bytes.fromhex("03f0070391f820509d42")     # and r3, #7; ldrb.w r5, [r1, #0x20]; cmp r5, r3
HIT_NEW = h(0x075B) + bytes.fromhex("91f82050") + h(0x076D) + h(0x429D)   # lsls r3, r3, #29; (the same ldrb.w); lsls r5, r5, #29; cmp r5, r3
PV_AT, PV_OLD = 0x0804F388, bytes.fromhex("c9b25ffa87fe")                 # uxtb r1, r1; uxtb.w lr, r7
PV_NEW = bytes.fromhex("01f00701") + h(0x46BE)                            # and.w r1, r1, #7; mov lr, r7
PVM_AT, PVM_OLD = 0x0804F2EC, bytes.fromhex("012202fa04f442460f402743")   # movs r2, #1; lsl.w r4, r2, r4; mov r2, r8; ands r7, r1; orrs r7, r4
MIC_SET, PRB_SET = 0x0804A244, 0x0804A270
MIC_CALLS = (0x0803E64E, 0x0804EC2C, 0x0804EC52, 0x08050096, 0x080500E0)
PRB_CALLS = (0x0803E658, 0x0804EC5C, 0x080500A0, 0x080500EA, 0x0804F300, 0x0804F30C)
PRB_TAIL = 0x0804EC3A                             # b.w 0x0804A270 (0x0804EC18's tail call)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev, part, ext=None):
    """part "a" (the hole): the tables, the helpers, the stock's setters and dpitch's spots; part "b" (the image's end): the knobs, the LEDs,
    the snapshot; ext = part a's labels."""
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    if part == "b":
        return arm_code_b(a, E, imm32, RET, L, prev, ext)
    k2c = bytes(PLAIN.get(k, 0) for k in range(8)) + bytes(SHIFTED.get(k, 0) for k in range(8))
    c2k = bytes([0xFF] + [next((k for k, c in list(PLAIN.items()) + list(SHIFTED.items()) if c == code), 0xFF) for code in range(1, 9)])
    bip = bytes([0x40 if c in BIP else 0 for c in range(9)])
    tabs = k2c + c2k + bip
    a.label("t_xltab"); E(raw, tabs + bytes(-len(tabs) % 4)); t_k2c, t_c2k, t_bip = base, base + 16, base + 25

    # ---- c_xlraw() -> r0 = the block (the record's tail + 357), or 0; c_xlblk() -> r0 = it when it holds ours, or 0; clobber r1, r2
    a.label("c_xlraw")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "xr_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("xr_x"); E(raw, RET)
    a.label("c_xlblk")
    E(push_list, [], lr=True); E(bl, "c_xlraw"); E(cmp_imm, 0, 0); E(b_cond, "xb_x", "eq")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, SIG0); E(b_cond, "xb_n", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, SIG1); E(b_cond, "xb_n", "ne")
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 0, 2 + k); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 0, 6); E(cmp_reg, 1, 2); E(b_cond, "xb_x", "eq")
    a.label("xb_n"); E(movs_imm, 0, 0)
    a.label("xb_x"); E(pop_list, [], pc=True)

    # ---- c_xlasg(r0 = drum) -> r0 = what its lane carries (0 = the chromatic pitch); clobbers r1, r2
    a.label("c_xlasg")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_xlblk"); E(cmp_imm, 0, 0); E(b_cond, "xa_x", "eq")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 2)
    a.label("xa_x"); E(pop_list, [4], pc=True)

    # ---- c_xlset(r0 = drum, r1 = what it carries): the block made when missing (all chromatic); clobbers r0-r3
    a.label("c_xlset")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_xlblk"); E(cmp_imm, 0, 0); E(b_cond, "xs_ok", "ne")
    E(bl, "c_xlraw"); E(cmp_imm, 0, 0); E(b_cond, "xs_x", "eq")
    E(movs_imm, 1, SIG0); E(strb_imm, 1, 0, 0); E(movs_imm, 1, SIG1); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0)
    for k in range(4): E(strb_imm, 1, 0, 2 + k)
    a.label("xs_ok")
    E(adds_reg, 1, 0, 4); E(strb_imm, 5, 1, 2)
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 0, 2 + k); E(eors_reg, 1, 2)
    E(strb_imm, 1, 0, 6)
    a.label("xs_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_xlbase(r0 = drum) -> r0 = the pattern it plays (its base), r1 = the step that plays; clobbers r2, r3
    a.label("c_xlbase")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(adds_imm8, 0, 4); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 5, 0, 0)
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(push_list, [0])
    E(mov_reg, 0, 5); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0)
    E(movw, 0, PAT_SZ); E(muls, 1, 0)
    imm32(0, DP0); E(movs_imm, 2, DP_SZ); E(muls, 2, 4); E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0x48); E(adds_reg, 0, 0, 1)
    E(pop_list, [1]); E(pop_list, [4, 5], pc=True)

    # ---- c_xlrd(r0 = a pattern's base, r1 = step) -> r0 = the step's code; clobbers r1
    a.label("c_xlrd")
    E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 0x20); E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 1, 1, 3)
    E(adds_imm8, 0, 0x40); E(ldrb_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 6); E(lsls_imm, 0, 0, 5); E(orrs_reg, 0, 1); E(raw, RET)

    # ---- c_xlwr(r0 = drum, r1 = step, r2 = code, r3 = the pattern's base): the step's spare bits, then the drum's edit store; clobbers r0-r3
    a.label("c_xlwr")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(mov_reg, 7, 3)
    E(adds_reg, 0, 7, 5); E(adds_imm8, 0, 0x20)
    E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(lsls_imm, 2, 6, 27); E(lsrs_imm, 2, 2, 24); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, 0)
    E(adds_imm8, 0, 0x40)
    E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 0x3F); E(ands_reg, 1, 2); E(lsrs_imm, 2, 6, 5); E(lsls_imm, 2, 2, 6); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, 0)
    imm32(0, DP0); E(movs_imm, 1, DP_SZ); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, L["c_dasync"])
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xlget(r0 = drum, r1 = what its lane carries) -> r0 = its value now (0..127, the codes' as offset binary), r1 = its default;
    #      r0 = -1 when there is none; clobbers r2, r3
    a.label("c_xlget")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 0); E(b_cond, "xg_c", "ne")
    E(bl, L["c_dpnow"]); E(movs_imm, 1, 64); E(pop_list, [4, 5], pc=True)
    a.label("xg_c")
    E(bl, L["c_dget"]); E(adds_imm8, 0, 1); E(b_cond, "xg_n", "eq"); E(subs_imm8, 0, 1)
    E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); imm32(2, t_bip); E(ldrb_reg, 1, 2, 5); E(eors_reg, 0, 1)
    E(pop_list, [4, 5], pc=True)
    a.label("xg_n"); E(subs_imm8, 0, 1); E(pop_list, [4, 5], pc=True)

    # ---- c_xlput(r0 = drum, r1 = code 1..8, r2 = the value 0..126): the drum's saved value, marked for the tick; clobbers r0-r3
    a.label("c_xlput")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, L["c_dget"]); E(adds_imm8, 0, 1); E(b_cond, "xp_x", "eq"); E(subs_imm8, 0, 1); E(mov_reg, 7, 0)
    imm32(2, t_bip); E(ldrb_reg, 2, 2, 5); E(eors_reg, 6, 2)
    E(movs_imm, 1, 0x80); E(ands_reg, 1, 7); E(orrs_reg, 6, 1); E(cmp_reg, 6, 7); E(b_cond, "xp_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["c_dput"])
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "xp_x", "eq"); E(mov_reg, 1, 5); E(bl, L["c_mark"])
    a.label("xp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xlcode(r0 = a value 0..127) -> r0 = its code 1..127; c_xlrec() -> r0 = 1 while recording (playing, Record, no count-in); clobber r1-r3
    a.label("c_xlcode")
    E(cmp_imm, 0, 126); E(b_cond, "xc_c", "ls"); E(movs_imm, 0, 126)
    a.label("xc_c"); E(adds_imm8, 0, 1); E(raw, RET)
    a.label("c_xlrec")
    E(push_list, [4], lr=True); imm32(4, TRANSPORT)
    for k, z in ((0, "eq"), (1, "eq"), (2, "ne")):
        E(mov_reg, 0, 4); E(movs_imm, 1, k); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "xq_n", z)
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("xq_n"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_xlheld() -> r0 = 1 while recinst's Record is held; c_xltaken(): recinst's «a snapshot taken» (Record's state back on release)
    a.label("c_xlheld")
    E(push_list, [], lr=True); E(bl, L["c_rist"]); E(ldrb_imm, 0, 0, 0); E(pop_list, [], pc=True)
    a.label("c_xltaken")
    E(push_list, [], lr=True); E(bl, L["c_rist"]); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 1); E(pop_list, [], pc=True)

    # ---- c_xlclr(r0 = drum): its lane erased in the pattern that plays; clobbers r0-r3
    a.label("c_xlclr")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(bl, "c_xlbase"); E(mov_reg, 6, 0); E(movs_imm, 5, 0)
    a.label("xk_l")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(mov_reg, 3, 6); E(bl, "c_xlwr")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, "xk_l", "lo")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_xlmic / c_xlprb (store, step, value): the stock's setters, the spare bits (micro steps 6-7, probability 3-7) kept
    a.label("c_xlmic")
    E(push_list, [3, 4, 5], lr=True); E(movs_imm, 3, 0x3F); E(movs_imm, 4, 16); E(b, "xm_s")
    a.label("c_xlprb")
    E(push_list, [3, 4, 5], lr=True); E(movs_imm, 3, 7); E(movs_imm, 4, 8)
    a.label("xm_s")
    E(push_list, [2, 3])
    E(movs_imm, 5, 3); E(ands_reg, 5, 1); E(lsrs_imm, 1, 1, 2); E(adds_reg, 1, 1, 4); E(bl, PARAM_WPTR)
    E(pop_list, [2, 3])
    E(ldr_imm, 1, 0, 0); E(lsls_imm, 5, 5, 3); E(ands_reg, 2, 3); E(lsls_reg, 2, 5); E(lsls_reg, 3, 5); E(bics_reg, 1, 3); E(orrs_reg, 1, 2)
    E(str_imm, 1, 0, 0)
    E(pop_list, [3, 4, 5], pc=True)

    # ---- c_xlpvm (the probability view's new hit, in place of 12 bytes at 0x0804F2EC: r1 = the micro step word, r4 = the step's shift)
    #      -> r7 = the word with micro step 0 of the step (bits 6-7 kept), r4 = 1 << shift, r2 = r8
    a.label("c_xlpvm")
    E(movs_imm, 2, 0x3F); E(lsls_reg, 2, 4); E(bics_reg, 1, 2); E(movs_imm, 2, 1); E(lsls_reg, 2, 4); E(orrs_reg, 1, 2)
    E(mov_reg, 7, 1); E(mov_reg, 4, 2); E(mov_reg, 2, 8); E(raw, RET)

    # ---- c_xlchr (dpitch's c_dpauto at da_g, micro step 0 of a drum's step: r5 = drum, r2 = step, r6 = lane 0's S or 0xFF, r7 = the player)
    #      -> the extra lane applied (r6 = its S for the chromatic pitch), then r0 = c_dpcur(drum) as the 6 bytes it replaces
    a.label("c_xlchr")
    E(push_list, [4], lr=True); E(mov_reg, 4, 2)
    E(mov_reg, 0, 5); E(bl, "c_xlbase"); E(mov_reg, 1, 4); E(bl, "c_xlrd"); E(cmp_imm, 0, 0); E(b_cond, "xh_x", "eq")
    E(subs_imm8, 0, 1); E(mov_reg, 4, 0)                                                 # r4 = the value
    E(mov_reg, 0, 5); E(bl, "c_xlasg"); E(cmp_imm, 0, 0); E(b_cond, "xh_k", "ne")
    E(cmp_imm, 6, 0xFF); E(b_cond, "xh_x", "ne"); E(mov_reg, 6, 4); E(b, "xh_x")
    a.label("xh_k"); E(cmp_imm, 0, 8); E(b_cond, "xh_x", "hi")
    E(mov_reg, 1, 0); E(mov_reg, 0, 5); E(mov_reg, 2, 4); E(bl, "c_xlput")
    a.label("xh_x"); E(mov_reg, 0, 5); E(bl, L["c_dpcur"]); E(pop_list, [4], pc=True)

    # ---- c_xlplane (dpitch's c_dppad, in place of its bl c_dplane: r0 = drum; the caller's r5 = the pad's S): the chromatic lane takes the
    #      recorded step (lane 0's bytes go to SCRATCH), any other lane leaves it to lane 0
    a.label("c_xlplane")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_xlasg"); E(cmp_imm, 0, 0); E(b_cond, "xl_0", "ne")
    E(mov_reg, 0, 4); E(bl, "c_xlbase"); E(cmp_imm, 1, 31); E(b_cond, "xl_s", "hi"); E(mov_reg, 3, 0)
    E(mov_reg, 0, 5); E(push_list, [1, 3]); E(bl, "c_xlcode"); E(mov_reg, 2, 0); E(pop_list, [1, 3]); E(mov_reg, 0, 4); E(bl, "c_xlwr")
    a.label("xl_s"); imm32(0, SCRATCH); E(pop_list, [4], pc=True)
    a.label("xl_0"); E(mov_reg, 0, 4); E(bl, L["c_dplane"]); E(pop_list, [4], pc=True)

    # ---- c_xlpad (dpitch's c_dppad entry, b.w: r0 = the chromatic view, r1 = the note's value): Record held = the drum's lane takes the
    #      chromatic pitch (swallowed); else c_dppad's first 4 bytes and on
    a.label("c_xlpad")
    E(push_list, [0, 1, 4], lr=True)
    E(bl, "c_xlheld"); E(cmp_imm, 0, 0); E(b_cond, "xd_n", "eq")
    E(movs_imm, 4, 0)
    a.label("xd_l")
    E(mov_reg, 0, 4); E(bl, L["c_dview"]); E(ldr_sp, 1, 0); E(cmp_reg, 0, 1); E(b_cond, "xd_y", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "xd_l", "lo"); E(b, "xd_n")
    a.label("xd_y"); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_xlset"); E(bl, "c_xltaken")
    E(pop_list, [0, 1, 4], pc=True)
    a.label("xd_n"); E(pop_list, [0, 1, 4]); E(pop_list, [2]); E(mov_reg, 14, 2)
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(b_w, L["c_dppad"] + 4)

    return a.assemble()


def arm_code_b(a, E, imm32, RET, L, prev, ext):
    t_k2c, t_c2k = ext["t_xltab"], ext["t_xltab"] + 16
    # ---- c_xlknob (slot 4 of the drum macro handlers: handler, knob, delta): Record held = assign; Clear + left = erase; recording = write
    a.label("c_xlknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 5, 1); E(movs_imm, 7, 0); E(movs_imm, 4, 0)
    a.label("xn_f")
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_reg, 0, 6); E(b_cond, "xn_h", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "xn_f", "lo"); E(b, "xn_p")
    a.label("xn_h")                                                                         # r4 = drum
    E(bl, L["c_shift"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "xn_s", "eq"); E(movs_imm, 1, 8)
    a.label("xn_s"); E(adds_reg, 1, 1, 5); E(cmp_imm, 1, 15); E(b_cond, "xn_p", "hi"); imm32(0, t_k2c); E(ldrb_reg, 7, 0, 1)   # r7 = its code
    E(cmp_imm, 7, 0); E(b_cond, "xn_p", "eq")
    E(bl, "c_xlheld"); E(cmp_imm, 0, 0); E(b_cond, "xn_c", "eq")
    E(cmp_imm, 7, 8); E(b_cond, "xn_p", "hi")                                                # Record held: the knob of a code
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_xlset"); E(bl, "c_xltaken"); E(b, "xn_x")
    a.label("xn_c")                                                                         # Clear held + a left turn of the lane's knob
    E(ldr_sp, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "xn_p", "ge")
    E(mov_reg, 0, 6); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "xn_p", "eq")
    E(mov_reg, 0, 4); E(bl, "c_xlasg"); E(mov_reg, 1, 7); E(cmp_imm, 1, CHROM); E(b_cond, "xn_m", "ne"); E(movs_imm, 1, 0)
    a.label("xn_m"); E(cmp_reg, 0, 1); E(b_cond, "xn_p", "ne")
    E(mov_reg, 0, 4); E(bl, "c_xlclr")
    a.label("xn_p")                                                                         # the chain, then the recording
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(bl, prev["knob"]); E(str_sp, 0, 0)
    E(cmp_imm, 4, 3); E(b_cond, "xn_x", "hi"); E(cmp_imm, 7, 8); E(b_cond, "xn_x", "hi"); E(cmp_imm, 7, 0); E(b_cond, "xn_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_xlasg"); E(cmp_reg, 0, 7); E(b_cond, "xn_x", "ne")
    E(bl, "c_xlrec"); E(cmp_imm, 0, 0); E(b_cond, "xn_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_xlget"); E(adds_imm8, 0, 1); E(b_cond, "xn_x", "eq"); E(subs_imm8, 0, 1)
    E(bl, "c_xlcode"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, "c_xlbase"); E(cmp_imm, 1, 31); E(b_cond, "xn_x", "hi")
    E(mov_reg, 3, 0); E(mov_reg, 2, 6); E(mov_reg, 0, 4); E(bl, "c_xlwr")
    a.label("xn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)

    # ---- c_xlkled (slot 7 of the drum macro handlers: handler -> the LED buffer): Record held = the knob of the lane's code white
    a.label("c_xlkled")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(bl, prev["kled"]); E(mov_reg, 5, 0)
    E(bl, "c_xlheld"); E(cmp_imm, 0, 0); E(b_cond, "xe_x", "eq")
    E(movs_imm, 6, 0)
    a.label("xe_f")
    E(mov_reg, 0, 6); E(bl, L["c_mh"]); E(cmp_reg, 0, 4); E(b_cond, "xe_h", "eq")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "xe_f", "lo"); E(b, "xe_x")
    a.label("xe_h")
    E(mov_reg, 0, 6); E(bl, "c_xlasg"); E(cmp_imm, 0, 8); E(b_cond, "xe_x", "hi")
    imm32(1, t_c2k); E(ldrb_reg, 1, 1, 0); E(cmp_imm, 1, 7); E(b_cond, "xe_x", "hi")
    E(lsls_imm, 1, 1, 1); E(movw, 0, KNOB_WHITE); E(strh_reg, 0, 5, 1)
    a.label("xe_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_xlled (the LED task's calls: ctrl, frame): the chain; Record held in a drum's views with the chromatic lane = Preset blinking white
    a.label("c_xlled")
    E(push_list, [3, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, "c_xlheld"); E(cmp_imm, 0, 0); E(b_cond, "xt_x", "eq")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "xt_x", "ne")
    E(ldrb_w, 1, 0, S_CUR); E(subs_imm8, 1, DRUM_V0); E(cmp_imm, 1, 31); E(b_cond, "xt_x", "hi"); E(lsrs_imm, 0, 1, 3)
    E(bl, "c_xlasg"); E(cmp_imm, 0, 0); E(b_cond, "xt_x", "ne")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(movs_imm, 1, 1); E(ands_reg, 0, 1)      # 1 = white (256 ms on / off)
    E(movs_imm, 1, 2 * LED_PRESET); E(strh_reg, 0, 5, 1)
    a.label("xt_x"); E(pop_list, [3, 4, 5], pc=True)

    # ---- c_xlsnap (snapall's c_sacpad at cp_d, in place of its bl c_sadone: r0 = the mark; r5 = the step): the lane's value, then c_sadone
    a.label("c_xlsnap")
    E(push_list, [0, 4, 5, 6, 7], lr=True)
    imm32(0, MGR); E(ldrb_w, 1, 0, S_CUR); E(subs_imm8, 1, DRUM_NOTE0); E(lsrs_imm, 4, 1, 3)              # r4 = drum (snapall checked the view)
    E(mov_reg, 0, 4); E(bl, "c_xlasg"); E(mov_reg, 1, 0); E(cmp_imm, 1, 8); E(b_cond, "xs2_x", "hi")
    E(mov_reg, 0, 4); E(bl, "c_xlget"); E(adds_imm8, 0, 1); E(b_cond, "xs2_x", "eq"); E(subs_imm8, 0, 1)
    E(cmp_reg, 0, 1); E(b_cond, "xs2_x", "eq")
    E(bl, "c_xlcode"); E(mov_reg, 7, 0)
    E(mov_reg, 0, 4); E(bl, L["c_dapat"]); E(movw, 1, PAT_SZ); E(muls, 1, 0)
    imm32(0, DP0); E(movs_imm, 2, DP_SZ); E(muls, 2, 4); E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0x48); E(adds_reg, 3, 0, 1)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, "c_xlwr")
    a.label("xs2_x"); E(pop_list, [0, 4, 5, 6, 7]); E(pop_list, [1]); E(mov_reg, 14, 1); E(b_w, L["c_sadone"])
    return a.assemble(external=ext)


def _labels(img, report):
    import ct_fw
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    return dict(c_rist=lab("recinst", "c_rist"), c_mh=lab("sc18", "c_mh"), c_shift=lab("sc15", "c_shift"), c_dview=lab("sc11", "c_dview"),
                c_dget=lab("persist19", "c_dget"), c_dput=lab("persist19", "c_dput"), c_mark=lab("persist19", "c_mark"),
                c_clr_held=lab("persist19", "c_clr_held"), c_dpnow=lab("dpitch", "c_dpnow"), c_dpcur=lab("dpitch", "c_dpcur"),
                c_dplane=lab("dpitch", "c_dplane"), c_dppad=lab("dpitch", "c_dppad"), c_dapat=lab("drumarp", "c_dapat"),
                c_dasync=lab("drumarp", "c_dasync"), c_sadone=lab("snapall", "c_sadone"))


def _append(img, base_addr, code):
    import ct_fw
    img += bytes([0xFF]) * (base_addr - ct_fw.APP_BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])


def install(img, report, base_addr):
    """Part a, at base_addr (hole.add): the stock's code patched in place, the setters' calls, dpitch's three spots."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = _labels(img, report)
    da_g = lab("dpitch", "da_g")
    assert rd(da_g, 6) == h(0x4628) + bl(da_g + 2, L["c_dpcur"]), "dpitch: da_g is not mov r0, r5; bl c_dpcur"
    assert rd(L["c_dppad"], 4) == h(0xB530) + h(0x4604), "dpitch: c_dppad does not start with push {r4, r5, lr}; mov r4, r0"
    pl = next(x for x in range(L["c_dppad"], lab("dpitch", "dv_x"), 2) if rd(x, 4) == bl(x, L["c_dplane"]))
    assert rd(HIT_AT, 10) == HIT_OLD and rd(PV_AT, 6) == PV_OLD and rd(PVM_AT, 12) == PVM_OLD
    for c in MIC_CALLS: assert rd(c, 4) == bl(c, MIC_SET), hex(c)
    for c in PRB_CALLS: assert rd(c, 4) == bl(c, PRB_SET), hex(c)
    assert rd(PRB_TAIL, 4) == b_w(PRB_TAIL, PRB_SET)
    code, labels = arm_code(base_addr, L, {}, "a")
    _append(img, base_addr, code)
    def put(at, data): img[at - BASE:at - BASE + len(data)] = data
    put(HIT_AT, HIT_NEW); put(PV_AT, PV_NEW)
    put(PVM_AT, bl(PVM_AT, labels["c_xlpvm"]) + h(0xBF00) * 4)
    for c in MIC_CALLS: put(c, bl(c, labels["c_xlmic"]))
    for c in PRB_CALLS: put(c, bl(c, labels["c_xlprb"]))
    put(PRB_TAIL, b_w(PRB_TAIL, labels["c_xlprb"]))
    put(da_g, bl(da_g, labels["c_xlchr"]) + h(0xBF00))
    put(L["c_dppad"], b_w(L["c_dppad"], labels["c_xlpad"]))
    put(pl, bl(pl, labels["c_xlplane"]))
    return labels, code, {}


class PartB:
    """Part b, at the image's end (build_sc41_5.add, after part a): the heads of slots 4 / 7 of the drum macro handlers and of the LED task's
    calls, snapall's c_sadone call."""
    @staticmethod
    def install(img, report, base_addr):
        import ct_fw
        BASE = ct_fw.APP_BASE
        u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
        rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
        L = _labels(img, report)
        ext = {k: int(v, 16) for k, v in report["lanex"]["labels"].items()}
        prev = dict(knob=u(MH_SLOT4) & ~1, kled=u(MH_SLOT7) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
        for c in PK.LED_CALLS[1:]: assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        cp_d = int(report["snapall"]["labels"]["cp_d"], 16)
        cp_bl = cp_d + 4
        assert rd(cp_d, 4) == h(0x9801) + h(0x3041) and rd(cp_bl, 4) == bl(cp_bl, L["c_sadone"]), "snapall: cp_d is not ldr; adds #0x41; bl c_sadone"
        code, labels = arm_code(base_addr, L, prev, "b", ext)
        labels = {k: v for k, v in labels.items() if k not in ext}
        _append(img, base_addr, code)
        assert len(img) <= 0x70000, f"lanex part b: the image is full ({len(img):#x})"
        def put(at, data): img[at - BASE:at - BASE + len(data)] = data
        put(cp_bl, bl(cp_bl, labels["c_xlsnap"]))
        struct.pack_into("<I", img, MH_SLOT4 - BASE, labels["c_xlknob"] | 1)
        struct.pack_into("<I", img, MH_SLOT7 - BASE, labels["c_xlkled"] | 1)
        for c in PK.LED_CALLS: put(c, bl(c, labels["c_xlled"]))
        return labels, code, prev
