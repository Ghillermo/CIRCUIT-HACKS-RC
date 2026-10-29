"""SC49.7 / Beta 5.0 (the user, 2026-10-29: «make automation view (velocity shift) available on drums»; chosen: all four parts, «Hold = preview,
tap = ramp»): the drums' automation view does what autorel's does on Synth 1 / 2 and MIDI 1 / 2.

The view is slock's (a drum's Velocity view with Shift held, or latched by Velocity pressed again there).  In it, on the step pads (pads 1-16, + 16
on the 17-32 page) of the pattern the drum shows (drumarp's c_dapat):
  * LEDs: a step with automation yellow: a byte <> 0xFF in its 6 micro steps of lanes 0-3 (pitch, decay, distortion, EQ: + 0xA8 + 192 k + 6 step),
    or a code in the extra lane (lanex); a marked step red; slock's dim yellow of a ramp step stays;
  * Shift + a yellow step = its values, until Shift is let go: the stock lanes through the stock's own lane route (the drum player's
    [+ 0x2C] slot 0 (target, [[player + 0x3C] + k], value), as the playback; the knob store and the sound follow), lane 0's chromatic bytes
    (0x80 | S) and a chromatic extra lane as dpitch's S, a code lane (lanex 1..8) as that value, a state (state locks) as all 14 values; the
    knobs it moves yellow (the drum macro handlers' slot 7).  Before the first change everything it can change is kept (the 4 stock knobs, S,
    the 14 values exactly) and put back when Shift is let go (and no step is held), or when the view is left;
  * Shift + a step with no automation = a release mark (red; again = off): the extra lane's code 126 (lanex's values stop at 124 now: c_xlcode
    clamps there).  At a marked step (dpitch's c_dpauto, micro step 0: da_g, in front of slock's c_slchr) the 4 stock knobs and the extra lane's
    code parameter (lane mode) go back to the values saved in the project (the session record: + 0x26FBC + 11 d + 2 + k; persist19's bytes);
  * Clear + a step = its automation erased (lanes 0-3 and the extra lane), the hit stays;
  * state-lock drums (slock): holding a yellow step previews it, tapping another while one is held draws slock's ramp (the preview put back
    first, so the new ends take the values of the knobs); Shift + a step without automation marks it (then held, as slock does).
RAM: modmx.MXR + 0x2180: + 0 "DV01", + 4 the previewed drum + 1, + 5 the swallowed pad + 1, + 6 the knobs it moved (bits), + 8 the 4 stock knobs,
+ 12 S, + 13 the 14 values."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, blx_reg, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm,  # noqa: E402
                   ldrb_reg, ldrh_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm,
                   strb_imm, strb_reg, strh_reg, subs_imm8)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import lanex as LX  # noqa: E402
import slock as SL  # noqa: E402
import persist19 as P19  # noqa: E402

RAM = MX.MXR + 0x2180
O_ACT, O_SW, O_MASK, O_STK, O_S, O_V = 4, 5, 6, 8, 12, 13
SIG = struct.unpack("<I", b"DV01")[0]
MARK, RAMP, STATE, NST, NV = 126, SL.RAMP, SL.STATE, SL.NST, SL.NV
DP0, DP_SZ = LX.DP0, LX.DP_SZ
MGR, PARAM_GET, SESSION_OBJ = 0x20040B10, 0x0803542C, 0x2003D71C
REC_DRUMS = 0x26FBC + 2                        # + 11 d + k: the drum's pitch, decay, distortion, EQ as the project saved them
REC_XM = 0x26000                               # persist19's drum bytes: the record + REC_XM + t_rec[8 d + code - 1]
YELLOW, RED = 0x2D, 0x53
KNOB_OF_LANE = (0, 2, 7, 4)                    # pitch K1, decay K3, distortion K8, EQ K5 (persist19.REMAP_PLAIN_STOCK)
RET = h(0x4770)


def rec_offsets():
    """persist19's record byte of drum d's code c (1..8), - REC_XM."""
    out = []
    for d in range(4):
        for c in range(1, 9):
            ctx, off = P19.FLAT[P19.XM_DRUMS + 9 * d + c - 1]
            out.append(P19.REC_BASE[ctx] + off - REC_XM)
    assert all(0 <= x < 0x10000 for x in out)
    return out


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def tail(lst, target):                                       # pop lst, then b.w target with lr restored
        E(pop_list, lst); E(pop_list, [3]); E(mov_reg, 14, 3); E(b_w, target)

    # ---- tables: the stock lanes' knob bits; persist19's record bytes
    a.label("t_dvkl"); E(raw, bytes(1 << k for k in KNOB_OF_LANE))
    a.label("t_dvrec"); E(raw, b"".join(struct.pack("<H", x) for x in rec_offsets()))

    # ---- c_dvram() -> r0 = RAM (the first time: nothing previewed or swallowed); clobbers r1, r2
    a.label("c_dvram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "dr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_ACT); E(strb_imm, 1, 0, O_SW)
    a.label("dr_x"); E(raw, RET)

    # ---- c_dvlane(r0 = a pattern's base, r1 = step, r2 = lane) -> r0 = its first byte <> 0xFF of the 6 micro steps (0xFF none); leaf
    a.label("c_dvlane")
    E(movs_imm, 3, 192); E(muls, 3, 2); E(adds_reg, 0, 0, 3); E(movs_imm, 3, 6); E(muls, 3, 1); E(adds_reg, 0, 0, 3); E(adds_imm8, 0, 0xA8)
    E(movs_imm, 2, 0)
    a.label("dl_l"); E(ldrb_reg, 1, 0, 2); E(cmp_imm, 1, 0xFF); E(b_cond, "dl_x", "ne"); E(adds_imm8, 2, 1); E(cmp_imm, 2, 6); E(b_cond, "dl_l", "lo")
    a.label("dl_x"); E(mov_reg, 0, 1); E(raw, RET)

    # ---- c_dvauto(r0 = base, r1 = step) -> r0 = 0 nothing (or a ramp step only), 1 automation, 2 marked; clobbers r1-r3
    a.label("c_dvauto")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_xlrd"]); E(cmp_imm, 0, MARK); E(b_cond, "da_m", "eq"); E(cmp_imm, 0, 0); E(b_cond, "da_k", "eq"); E(cmp_imm, 0, RAMP); E(b_cond, "da_y", "ne")
    a.label("da_k"); E(movs_imm, 6, 0)
    a.label("da_l"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_dvlane"); E(cmp_imm, 0, 0xFF); E(b_cond, "da_y", "ne")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "da_l", "lo"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)
    a.label("da_y"); E(movs_imm, 0, 1); E(pop_list, [4, 5, 6], pc=True)
    a.label("da_m"); E(movs_imm, 0, 2); E(pop_list, [4, 5, 6], pc=True)
    # ---- c_dvyel(r0 = drum, r1 = step) -> c_dvauto of the pattern it shows; clobbers r1-r3
    a.label("c_dvyel")
    E(push_list, [1], lr=True); E(bl, L["c_slsel"]); E(pop_list, [1]); E(bl, "c_dvauto"); E(pop_list, [], pc=True)

    # ---- c_dvset(r0 = drum, r1 = lane 0..3, r2 = value): the stock's lane route (the player's [+ 0x2C] slot 0); clobbers r0-r3
    a.label("c_dvset")
    E(push_list, [4], lr=True)
    E(movs_imm, 3, DP_SZ); E(muls, 3, 0); imm32(0, DP0); E(adds_reg, 3, 3, 0)
    E(ldr_imm, 0, 3, 0x2C); E(ldr_imm, 3, 3, 0x3C); E(ldrb_reg, 1, 3, 1); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0); E(raw, blx_reg(3))
    E(pop_list, [4], pc=True)

    # ---- c_dvget(r0 = drum, r1 = value 0..13) -> r0 = it exactly (slock's kinds: persist19's code / K3 as 0..127, the others as stored)
    a.label("c_dvget")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_slkind"])
    E(cmp_imm, 2, 0); E(b_cond, "dg_4", "ne"); E(mov_reg, 1, 3); E(bl, L["c_xlget"]); E(pop_list, [4], pc=True)
    a.label("dg_4"); E(cmp_imm, 2, 4); E(b_cond, "dg_o", "ne"); E(mov_reg, 0, 4); E(mov_reg, 1, 3); E(bl, L["c_k3get"]); E(pop_list, [4], pc=True)
    a.label("dg_o"); E(mov_reg, 0, 4); E(bl, L["c_slgetp"]); E(pop_list, [4], pc=True)

    # ---- c_dvprev(r0 = drum, r1 = step): its values played (the first time: what it can change kept)
    a.label("c_dvprev")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_dvram"); E(mov_reg, 7, 0); E(ldrb_imm, 0, 7, O_ACT); E(cmp_imm, 0, 0); E(b_cond, "dp_h", "ne")
    E(movs_imm, 6, 0)                                                                                 # the 4 stock knobs: the macro store
    a.label("dp_k"); E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(ldr_imm, 0, 0, 0xC); E(mov_reg, 1, 6); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(adds_reg, 1, 7, 6); E(strb_imm, 0, 1, O_STK); E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "dp_k", "lo")
    E(mov_reg, 0, 4); E(bl, L["c_dpnow"]); E(strb_imm, 0, 7, O_S)
    E(movs_imm, 6, 0)
    a.label("dp_v"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_dvget"); E(adds_reg, 1, 7, 6); E(strb_imm, 0, 1, O_V)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "dp_v", "lo")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 7, O_ACT); E(movs_imm, 0, 0); E(strb_imm, 0, 7, O_MASK)
    a.label("dp_h"); E(mov_reg, 0, 4); E(bl, L["c_slsel"]); E(mov_reg, 6, 0)                          # r6 = the base
    E(push_list, [7]); E(movs_imm, 7, 0)                                                              # r7 = lane
    a.label("dp_l"); E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, "c_dvlane"); E(cmp_imm, 0, 0xFF); E(b_cond, "dp_n", "eq")
    E(cmp_imm, 0, 0x80); E(b_cond, "dp_s", "lo")
    E(cmp_imm, 7, 0); E(b_cond, "dp_n", "ne"); E(movs_imm, 1, 0x7F); E(ands_reg, 1, 0); E(mov_reg, 0, 4); E(bl, L["c_dpput"]); E(b, "dp_b")   # lane 0's S
    a.label("dp_s"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_dvset")
    a.label("dp_b"); imm32(0, base); E(ldrb_reg, 0, 0, 7); E(bl, "c_dvor")                           # t_dvkl[lane]
    a.label("dp_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "dp_l", "lo"); E(pop_list, [7])
    E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, L["c_xlrd"]); E(cmp_imm, 0, 0); E(b_cond, "dp_x", "eq"); E(cmp_imm, 0, MARK); E(b_cond, "dp_x", "hs")
    E(mov_reg, 5, 0)                                                                                  # r5 = the code
    E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "dp_c", "ne")
    E(cmp_imm, 5, NST); E(b_cond, "dp_x", "hi")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 5); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 16); E(bl, L["c_slapply"])
    E(movs_imm, 0, 0xFF); E(bl, "c_dvor"); E(b, "dp_x")
    a.label("dp_c"); E(subs_imm8, 5, 1); E(cmp_imm, 0, 0); E(b_cond, "dp_p", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dpput"]); E(movs_imm, 0, 1); E(bl, "c_dvor"); E(b, "dp_x")   # the chromatic pitch: K1
    a.label("dp_p"); E(cmp_imm, 0, 8); E(b_cond, "dp_x", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(mov_reg, 2, 5); E(bl, L["c_xlput"])
    imm32(0, L["t_xltab"] + 16); E(ldrb_reg, 0, 0, 6); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(movs_imm, 1, 1); E(raw, h(0x4081))   # lsls r1, r0
    E(mov_reg, 0, 1); E(bl, "c_dvor")
    a.label("dp_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_dvor(r0 = knob bits): RAM's + O_MASK |= them; clobbers r0-r2
    a.label("c_dvor")
    E(push_list, [0], lr=True); E(bl, "c_dvram"); E(pop_list, [1]); E(ldrb_imm, 2, 0, O_MASK); E(orrs_reg, 2, 1); E(strb_imm, 2, 0, O_MASK)
    E(pop_list, [], pc=True)

    # ---- c_dvrest(): a preview's values put back (nothing previewed: nothing); clobbers r0-r3
    a.label("c_dvrest")
    E(push_list, [4, 5, 6], lr=True); E(bl, "c_dvram"); E(mov_reg, 5, 0); E(ldrb_imm, 4, 5, O_ACT); E(cmp_imm, 4, 0); E(b_cond, "dt_x", "eq")
    E(subs_imm8, 4, 1); E(movs_imm, 0, 0); E(strb_imm, 0, 5, O_ACT); E(strb_imm, 0, 5, O_MASK); E(movs_imm, 6, 0)
    a.label("dt_k"); E(adds_reg, 2, 5, 6); E(ldrb_imm, 2, 2, O_STK); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_dvset")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "dt_k", "lo")
    E(ldrb_imm, 1, 5, O_S); E(mov_reg, 0, 4); E(bl, L["c_dpput"]); E(movs_imm, 6, 0)
    a.label("dt_v"); E(adds_reg, 2, 5, 6); E(ldrb_imm, 2, 2, O_V); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, L["c_slsetp"])
    E(adds_imm8, 6, 1); E(cmp_imm, 6, NV); E(b_cond, "dt_v", "lo")
    a.label("dt_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dvmark(r0 = drum, r1 = step): the release mark on / off; c_dverase(r0 = drum, r1 = step): lanes 0-3 and the extra lane erased
    a.label("c_dvmark")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, L["c_slsel"]); E(mov_reg, 6, 0)
    E(mov_reg, 1, 5); E(bl, L["c_xlrd"]); E(movs_imm, 2, MARK); E(cmp_imm, 0, MARK); E(b_cond, "dm_w", "ne"); E(movs_imm, 2, 0)
    a.label("dm_w"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 3, 6); E(bl, L["c_xlwr"]); E(pop_list, [4, 5, 6], pc=True)
    a.label("c_dverase")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, L["c_slsel"]); E(mov_reg, 6, 0)
    E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 1, 1, 0); E(adds_imm8, 1, 0xA8); E(movs_imm, 2, 0xFF); E(movs_imm, 0, 4)   # r1 = lane 0 of the step
    a.label("de_k"); E(movs_imm, 3, 0)
    a.label("de_l"); E(strb_reg, 2, 1, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "de_l", "lo")
    E(adds_imm8, 1, 192); E(subs_imm8, 0, 1); E(b_cond, "de_k", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(mov_reg, 3, 6); E(bl, L["c_xlwr"]); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dvrls(r0 = drum): a marked step plays: the 4 stock knobs and the extra lane's code (lane mode) as the project saved them
    a.label("c_dvrls")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    imm32(0, SESSION_OBJ); E(ldr_imm, 6, 0, 0x14)                                                     # r6 = the record
    imm32(5, REC_DRUMS); E(adds_reg, 5, 5, 6); E(movs_imm, 0, 11); E(muls, 0, 4); E(adds_reg, 5, 5, 0)
    for k in range(4):
        E(ldrb_imm, 2, 5, k); E(mov_reg, 0, 4); E(movs_imm, 1, k); E(bl, "c_dvset")
    E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(subs_imm8, 0, 1); E(cmp_imm, 0, 7); E(b_cond, "dz_x", "hi"); E(mov_reg, 5, 0)   # r5 = code - 1
    E(lsls_imm, 1, 4, 3); E(adds_reg, 1, 1, 5); E(lsls_imm, 1, 1, 1); imm32(0, base + 4); E(raw, ldrh_reg(1, 0, 1))   # t_dvrec[8 d + code - 1]
    imm32(0, REC_XM); E(adds_reg, 0, 0, 6); E(ldrb_reg, 2, 0, 1); E(movs_imm, 0, 0x7F); E(ands_reg, 2, 0)
    imm32(0, L["t_xltab"] + 25 + 1); E(ldrb_reg, 0, 0, 5); E(eors_reg, 2, 0)                          # t_bip[code]
    E(adds_imm8, 5, 1); E(mov_reg, 1, 5); E(mov_reg, 0, 4); E(bl, L["c_xlput"])
    a.label("dz_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dvchr (dpitch's c_dpauto at da_g, micro step 0: r5 = drum, r2 = step, r6 = lane 0's S or 0xFF, r7 = the player): a marked step =
    #      c_dvrls, r0 = c_dpcur(drum); else the chain (slock's c_slchr)
    a.label("c_dvchr")
    E(push_list, [2, 4], lr=True)
    E(mov_reg, 0, 5); E(bl, L["c_xlbase"]); E(ldr_sp, 1, 0); E(bl, L["c_xlrd"]); E(cmp_imm, 0, MARK); E(b_cond, "dc_r", "eq")
    tail([2, 4], prev["chr"])
    a.label("dc_r"); E(mov_reg, 0, 5); E(bl, "c_dvrls"); E(mov_reg, 0, 5); E(bl, L["c_dpcur"]); E(pop_list, [2, 4], pc=True)

    # ---- c_dvclr() -> r0 = 1 while Clear is held (the held buttons [[ctrl + 0x20] + 0xC] p0 bit 0); clobbers r1-r3
    a.label("c_dvclr")
    E(push_list, [], lr=True); imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET)
    E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(pop_list, [], pc=True)

    # ---- c_dvpad (slot 0 of the track views' container: cont, pad, velocity): the drums' automation view; else the chain (slock's c_slpad)
    a.label("c_dvpad")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(cmp_imm, 1, 15); E(b_cond, "dq_p", "hi")
    E(bl, L["c_slauto"]); E(cmp_imm, 0, 3); E(b_cond, "dq_p", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_slpage"]); E(ldr_sp, 1, 4); E(adds_reg, 5, 0, 1)                                        # r5 = the step
    E(bl, "c_dvclr"); E(cmp_imm, 0, 0); E(b_cond, "dq_n", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dverase"); E(b, "dq_sw")
    a.label("dq_n"); E(bl, L["c_shift"]); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, L["c_xlasg"]); E(cmp_imm, 0, STATE); E(b_cond, "dq_s", "eq")
    E(cmp_imm, 6, 0); E(b_cond, "dq_p", "eq")                                                         # lane mode: Shift only
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvyel"); E(cmp_imm, 0, 1); E(b_cond, "dq_m", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvprev"); E(b, "dq_sw")
    a.label("dq_m"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvmark")
    a.label("dq_sw"); E(bl, "c_dvram"); E(ldr_sp, 1, 4); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, O_SW); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("dq_s")                                                                                   # state locks: slock holds / ramps
    E(bl, L["c_slram"]); E(ldrb_imm, 0, 0, 1); E(cmp_imm, 0, 0xFF); E(b_cond, "dq_h", "eq")
    E(bl, "c_dvrest"); E(b, "dq_p")                                                                   # a ramp: the knobs' values for its ends
    a.label("dq_h"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvyel"); E(cmp_imm, 0, 1); E(b_cond, "dq_t", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvprev"); E(b, "dq_p")
    a.label("dq_t"); E(cmp_imm, 6, 0); E(b_cond, "dq_p", "eq"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dvmark")
    a.label("dq_p"); tail([0, 1, 2, 4, 5, 6], prev["pad"])

    # ---- c_dvrel (slot 1 of the container: cont, pad): the release of a pad we took: swallowed; else the chain
    a.label("c_dvrel")
    E(push_list, [0, 1], lr=True); E(bl, "c_dvram"); E(ldrb_imm, 2, 0, O_SW); E(ldr_sp, 1, 4); E(adds_imm8, 1, 1); E(cmp_reg, 1, 2); E(b_cond, "dw_p", "ne")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_SW); E(pop_list, [0, 1], pc=True)
    a.label("dw_p"); E(pop_list, [0, 1]); E(pop_list, [2]); E(mov_reg, 14, 2); E(b_w, prev["rel"])

    # ---- c_dvled (the LED task's calls: ctrl, frame): the chain; a preview put back once Shift is let go (and no step held) or the view left;
    #      the view: the steps with automation yellow, the marked ones red
    a.label("c_dvled")
    E(push_list, [3, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1); E(bl, prev["led"])
    E(bl, "c_dvram"); E(ldrb_imm, 0, 0, O_ACT); E(cmp_imm, 0, 0); E(b_cond, "dv_a", "eq")
    E(bl, L["c_slauto"]); E(cmp_imm, 0, 3); E(b_cond, "dv_r", "hi")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "dv_a", "ne")
    E(bl, L["c_slram"]); E(ldrb_imm, 0, 0, 1); E(cmp_imm, 0, 0xFF); E(b_cond, "dv_a", "ne")
    a.label("dv_r"); E(bl, "c_dvrest")
    a.label("dv_a"); E(bl, L["c_slauto"]); E(cmp_imm, 0, 3); E(b_cond, "dv_x", "hi")
    E(bl, L["c_slsel"]); E(mov_reg, 7, 0); E(bl, L["c_slpage"]); E(mov_reg, 6, 0); E(movs_imm, 4, 0)
    a.label("dv_l"); E(mov_reg, 0, 7); E(adds_reg, 1, 6, 4); E(bl, "c_dvauto"); E(cmp_imm, 0, 0); E(b_cond, "dv_n", "eq")
    E(movs_imm, 1, YELLOW); E(cmp_imm, 0, 2); E(b_cond, "dv_c", "ne"); E(movs_imm, 1, RED)
    a.label("dv_c"); E(lsls_imm, 0, 4, 1); E(strh_reg, 1, 5, 0)
    a.label("dv_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "dv_l", "lo")
    a.label("dv_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_dvkled (slot 7 of the drum macro handlers: handler -> the LED buffer): the chain; the previewed drum: the knobs it moved yellow
    a.label("c_dvkled")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(bl, prev["kled"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_sldrum"]); E(mov_reg, 4, 0)
    E(bl, "c_dvram"); E(ldrb_imm, 1, 0, O_ACT); E(subs_imm8, 1, 1); E(cmp_reg, 1, 4); E(b_cond, "dk_x", "ne")
    E(ldrb_imm, 2, 0, O_MASK); E(movs_imm, 1, 0); E(movs_imm, 3, YELLOW)
    a.label("dk_l"); E(lsrs_imm, 2, 2, 1); E(b_cond, "dk_n", "cc"); E(strb_reg, 3, 5, 1)
    a.label("dk_n"); E(adds_imm8, 1, 2); E(cmp_imm, 1, 16); E(b_cond, "dk_l", "lo")
    a.label("dk_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    code, labels = a.assemble()
    assert labels["t_dvkl"] == base and labels["t_dvrec"] == base + 4
    return code, labels


def _labels(report):
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    sl = {**{k: int(v, 16) for k, v in report["slock"]["labels"].items()}, **{k: int(v, 16) for k, v in report["slockb"]["labels"].items()}}
    L = {k: sl[k] for k in ("c_slauto", "c_slram", "c_slsel", "c_slpage", "c_slkind", "c_slgetp", "c_slsetp", "c_slapply", "c_sldrum")}
    L.update({k: lab("lanex", k) for k in ("c_xlasg", "c_xlrd", "c_xlwr", "c_xlget", "c_xlput", "c_xlbase", "t_xltab", "c_xlcode")})
    L.update(c_k3get=lab("persist19", "c_k3get"), c_mh=lab("sc18", "c_mh"), c_shift=lab("sc15", "c_shift"),
             c_dpnow=lab("dpitch", "c_dpnow"), c_dpput=lab("dpitch", "c_dpput"), c_dpcur=lab("dpitch", "c_dpcur"))
    return L


def install(img, report, base_addr):
    """At the image's end: the heads of slots 0 / 1 of the track views' container, of the LED task, of slot 7 of the drum macro handlers and
    da_g's call (all slock's now); lanex's c_xlcode clamps at 124 (code 126 = the mark)."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    rd = lambda at, n: bytes(img[at - BASE:at - BASE + n])
    u = lambda at: struct.unpack_from("<I", img, at - BASE)[0]
    L = _labels(report)
    da_g = int(report["dpitch"]["labels"]["da_g"], 16)
    prev = dict(pad=u(SL.CONT_VT) & ~1, rel=u(SL.CONT_VT + 4) & ~1, kled=u(LX.MH_SLOT7) & ~1, led=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                chr=FD.bl_target(img, da_g, BASE))
    for c in PK.LED_CALLS[1:]: assert FD.bl_target(img, c, BASE) == prev["led"], hex(c)
    sl = {**{k: int(v, 16) for k, v in report["slock"]["labels"].items()}, **{k: int(v, 16) for k, v in report["slockb"]["labels"].items()}}
    assert (prev["pad"], prev["rel"], prev["kled"], prev["chr"]) == (sl["c_slpad"], sl["c_slrel"], sl["c_slkled"], sl["c_slchr"])
    xc = L["c_xlcode"]
    assert rd(xc, 2) == h(0x287E) and rd(xc + 4, 2) == h(0x207E), rd(xc, 6).hex()        # cmp r0, #126; bls; movs r0, #126
    code, labels = arm_code(base_addr, L, prev)
    LX._append(img, base_addr, code)
    assert len(img) <= 0x70000, f"dautov: the image is full ({len(img):#x})"
    def put(at, data): img[at - BASE:at - BASE + len(data)] = data
    put(xc, h(0x287C)); put(xc + 4, h(0x207C)); hole.rehash(img, report, xc)
    struct.pack_into("<I", img, SL.CONT_VT - BASE, labels["c_dvpad"] | 1)
    struct.pack_into("<I", img, SL.CONT_VT + 4 - BASE, labels["c_dvrel"] | 1)
    struct.pack_into("<I", img, LX.MH_SLOT7 - BASE, labels["c_dvkled"] | 1)
    put(da_g, bl(da_g, labels["c_dvchr"]))
    for c in PK.LED_CALLS: put(c, bl(c, labels["c_dvled"]))
    return labels, code, prev
