"""SC43.5 (the user, 2026-10-17: «Keep k1 chromatic, make s+k6 continuous pitch. Stock saved pitch affects continuous pitch, not chromatic»): the
drum pitch in two parts.

The stock (read in the firmware): a drum's Pitch (stock parameter, 0..127, 64 = the sample as it is; saved, automated, its CC) is a LINEAR rate
change: word = (256 + 2 x trunc(1.5 x (P - 64))) << 8 (0.25 .. 1.73 x).  SC09 turned it into semitones (word = 0x10000 x 2^((P - 64) / 12)), SC12
multiplies by the chromatic view's cents (c_conv0..3 at the 4 drum DSP handlers' calls 0x080287FA, 0x08028896, 0x0802892A, 0x080289BE), SC08 / SC11
make the chromatic view's pads set P = 64 + bias + the note (and record it), SC11 sets the bias from P when the view opens.

Ours:
  * a chromatic value S per drum (0..127, 64 = none; the record's tail + 48: 0xD5, S of the four drums, a check byte; saved with the project; 64
    without the block);
  * the pitch word = the stock's linear word of P x 2^((S - 64) / 12) x the cents: the four calls go to c_dpc0..3, which runs SC12's c_conv(d) on S
    and multiplies by the linear factor of P;
  * K1 (no Shift) = S, one semitone a step (in the chromatic view also the keyboard's bias, as SC11's); Clear + K1 right = 64 (and the pitch
    envelope, its Shift layer, back to 0); Shift + K6 = the stock Pitch through the stock handler (continuous, as the original); Clear + K6 right =
    also P back to 64 (as a received CC);
  * the chromatic view's pads set S (live: the step is not recorded) and the bias starts from S when the view opens;
  * LEDs: K1 = |S - 64| x 2 in the drum's colour (dim at 64); with Shift K6 = |P - 64| x 2.

SC43.6 (use_rec): the chromatic steps recorded again, in lane 7 of the drum pattern (see use_rec).
SC43.7 (use_lane0): K1 = the stock pitch again, the chromatic steps tagged in the drum's own pitch lane (see use_lane0).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm, ldrb_w, ldrh_imm, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, strb_imm, strb_w, strh_imm, subs_imm8, subs_reg)
import build_sc12 as S12  # noqa: E402

SESSION_OBJ, TAIL, O_BLK, MAGIC = 0x2003D71C, 0x27024, 48, 0xD5
MH_VT = 0x0805AADC
DK_STOCK = 0x0804FCC4                                    # the stock drum knob handler (obj, knob, delta): knob 1 = Pitch
MARK_DIRTY, PARAM_GET, PARAM_SET, CTX = 0x0803BDCC, 0x0803542C, 0x08034D92, 0x200069E4
BIAS, FLAG = 0x52, 0x51
DP_OLD = bytes.fromhex("e06894f82410043903681b689847")  # SC11's c_dpad2 at dp_c2: ldr r0, [r4, #0xc]; ldrb.w r1, [r4, #0x24]; subs r1, #4; ...; blx r3
DRUM_COL = (0x45, 0x2D, 0x49, 0x4D)
REC = False                                              # SC43.6 (use_rec)
O_EFF, O_ACT = 54, 58                                    # (REC) the tail + 54 + d = the S a step put, + 58 bit d = it sounds (RAM)
LANE, LANE_IDS = 7, (89, 92)                             # (REC) the drum pattern's lane 7 = the stock's pan automation of the drum (ids 89-92)
DP0, DP_SZ, PAT_SZ = 0x20040810, 0x90, 0x6A8
ENG, TRANSPORT = 0x20038EC0, 0x20011034
AUTO_CALL, AUTO = 0x0804A752, 0x0804A7CA                 # (REC) the players' step: bl to the automation of the step (player, pattern, step, micro step)
REC_GATE = 0x0802E62C                                    # (REC) the automation gate (gate, id, value); its head is SC05's b.w
DSP_W, PITCH_X = 0x080292F8, 0xA4                        # the drum's pitch word: X:$A4 + 10 d (0x080292F8(0, word, address), as its DSP group)


L0 = False                                               # SC43.7 (use_lane0)
LV_AT, LV_OLD, LV_BACK = 0x0804A946, bytes.fromhex("0f5c7fe7"), 0x0804A84A   # (L0) in 0x0804A7CA: ldrb r7, [r1, r0] (a lane's byte at the micro step); b (the apply)


def use_lane0():
    """SC43.7 (the user, 2026-10-17: «alternatives to sacrifice pan, I want to be able to both pitch the drums continuously and have chromatic pads»;
    «1 if able»): K1 is the stock Pitch again (continuous and linear, saved, automated, its CC), the chromatic pads transpose on top (the word =
    the linear factor of P x 2^((S - 64) / 12) x the cents, as SC43.5), and the recorded chromatic steps go to the drum's pitch lane (lane 0)
    with bit 7 set (0x80 | S, S 0..126): a step holds a knob movement or a chromatic note.  The stock (emulated): 0x0804A7CA takes the value of a
    lane at a micro step (the drums: the raw byte, ldrb r7, [r1, r0] at 0x0804A946, no interpolation) and applies it when it changes; that
    load -> c_dplv, which gives 0xFFFF (no change) for a drum's lane 0 byte 0x80..0xFE, so P is not moved by a chromatic step; c_dpauto (micro step 0) takes S
    from it.  Lane 7 is the drum's pan automation again (its gate and its halfwords untouched; SC43.6 had the stock apply its chromatic steps as
    the pan too, before c_dpauto).  Clear + K1 (the stock: left 40 clicks = the lane deleted, right = 64) also puts S back to 64 at once;
    Shift + K6 and the LEDs of K1 / K6 are the chain's again."""
    global L0, LANE
    assert REC
    L0 = True
    LANE = 0


def use_rec():
    """SC43.6 (the user, 2026-10-17: the chromatic view's per-step recording, lost in SC43.5: «bring it back»).

    The stock (read in the firmware, the 173 sessions of the card's copy): a drum pattern has 8 automation lanes (+ 0xA8 + 192 lane, 6 micro steps
    a step); the gate's table 0x08059080 gives a drum's ids 40 + 5 d .. 43 + 5 d = lanes 0-3 (its knobs), 44 + 5 d = its sample flips, and lanes
    4-7 = the parameters every track has (ids 64 + d, 72 + d, 81 + d, 89 + d); 85 + track = the pan (the Mixer's Clear + pan knob deletes that
    id), so lane 7 = the drum's pan automation, empty in all 173 sessions (lanes 0-6 are used).  The players' step (0x0804A714) runs the
    automation of the step (0x0804A7CA: a halfword a lane in [player + 0x40] / [+ 0x44], 0xFFFF = none) before its hits.

    Ours: lane 7 of the drums = their chromatic steps (0..127, 0xFF = none), not their pan automation:
      * with Record armed and the transport running (no count-in) a pad of the chromatic view also writes S into the six micro steps of lane 7 of
        the drum's playing pattern at its playing step;
      * after the automation of a drum's step (the bl at 0x0804A752 -> c_dpauto) lane 7's halfwords are 0xFFFF (the stock does not move the pan
        from it) and, at micro step 0, the lane's byte is the S of the step (0xFF: the knob's): the pitch word written at once (X:$A4 + 10 d)
        when it changes, before the hits; the drum's DSP group uses it too; stopped (the LED task), the knobs' S again;
      * the gate drops ids 89-92 (a drum's pan is not recorded: it would write over the steps);
      * Clear + K1 to the left = lane 7 of the playing pattern back to 0xFF (red LED).  Duplicate, Clear, Nudge of a pattern carry its lane 7."""
    global REC
    REC = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    E(raw, bytes(DRUM_COL)); t_col = base

    # ---- c_dpblk() -> r0 = the block (the tail + 48), or 0; clobbers r1
    a.label("c_dpblk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "pb_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("pb_x"); E(raw, RET)

    # ---- c_dpok(r0 = the block) -> r0 = 1 when it holds ours; clobbers r1-r3
    a.label("c_dpok")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "po_n", "ne")
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 0, 1 + k); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 0, 5); E(cmp_reg, 1, 2); E(b_cond, "po_n", "ne")
    E(movs_imm, 0, 1); E(raw, RET)
    a.label("po_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_dpnow(r0 = drum) -> r0 = its S (64 without the block); clobbers r1-r3
    a.label("c_dpnow")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_dpblk"); E(mov_reg, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "pn_d", "eq")
    E(bl, "c_dpok"); E(cmp_imm, 0, 0); E(b_cond, "pn_d", "eq")
    E(adds_reg, 0, 5, 4); E(ldrb_imm, 0, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("pn_d"); E(movs_imm, 0, 64); E(pop_list, [4, 5], pc=True)

    # ---- c_dpput(r0 = drum, r1 = S 0..127): the block made when missing (64s), the drum's pitch sent again; clobbers r0-r3
    a.label("c_dpput")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_dpblk"); E(mov_reg, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "pp_x", "eq")
    E(bl, "c_dpok"); E(cmp_imm, 0, 0); E(b_cond, "pp_ok", "ne")
    E(movs_imm, 0, MAGIC); E(strb_imm, 0, 6, 0); E(movs_imm, 0, 64)
    for k in range(4): E(strb_imm, 0, 6, 1 + k)
    a.label("pp_ok")
    E(adds_reg, 0, 6, 4); E(strb_imm, 5, 0, 1)
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 6, 1 + k); E(eors_reg, 1, 2)
    E(strb_imm, 1, 6, 5)
    E(lsls_imm, 1, 4, 3); E(subs_reg, 1, 1, 4); E(adds_imm8, 1, 2); E(movs_imm, 0, 0x10); E(bl, MARK_DIRTY)   # (0x10, 7 d + 2): the drum's group again
    a.label("pp_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dpc0..3 (the drum DSP handlers' bl c_conv(d): r0 = P) -> r0 = the word: c_conv(d) of S, x the linear factor of P
    for d in range(4):
        a.label(f"c_dpc{d}")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(movs_imm, 0, d); E(b, "dc_t")
    if REC:
        a.label("c_dpword")                                                             # c_dpword(r0 = drum, r1 = P) -> r0 = the word
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 1); E(b, "dc_t")
    a.label("dc_t")
    E(raw, h(0xB401))                                                                  # push {r0}: the drum
    E(bl, "c_dpcur" if REC else "c_dpnow"); E(raw, h(0xBC02))                          # pop {r1}
    E(lsls_imm, 1, 1, 4); imm32(2, L["c_conv0"]); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, 1)   # c_conv0 + 16 d (thumb)
    E(raw, h(0x4788))                                                                  # blx r1: SC12's word of S (cents too)
    E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(subs_imm8, 0, 64)                                              # d = P - 64; t = d + trunc(d / 2)
    E(mov_reg, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "dc_p", "ge"); E(raw, h(0x4249)); E(lsrs_imm, 1, 1, 1); E(raw, h(0x4249)); E(b, "dc_q")   # negs r1
    a.label("dc_p"); E(lsrs_imm, 1, 1, 1)
    a.label("dc_q"); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 128); E(lsls_imm, 0, 0, 1)    # 256 + 2 t
    E(muls, 0, 5); E(lsrs_imm, 0, 0, 8)
    imm32(1, 0x7FFFFF); E(cmp_reg, 0, 1); E(b_cond, "dc_x", "ls"); E(mov_reg, 0, 1)
    a.label("dc_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_dpdrum(r0 = a macro handler) -> r0 = its drum 0..3, or 0xFF (SC11's: (byte + 0x30) - 40) / 5); clobbers r1
    a.label("c_dpdrum")
    E(ldrb_w, 0, 0, 0x30); E(subs_imm8, 0, 40); E(movs_imm, 1, 0)
    a.label("dd_l"); E(cmp_imm, 0, 5); E(b_cond, "dd_e", "lo"); E(subs_imm8, 0, 5); E(adds_imm8, 1, 1); E(b, "dd_l")
    a.label("dd_e"); E(mov_reg, 0, 1); E(cmp_imm, 0, 3); E(b_cond, "dd_x", "ls"); E(movs_imm, 0, 0xFF)
    a.label("dd_x"); E(raw, RET)

    if L0:
        # ---- c_dpknob (L0; the drum macro handlers' slot 4: handler, knob, delta): Clear + K1 = S back to 64 too; always the chain (the stock Pitch)
        a.label("c_dpknob")
        E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
        E(cmp_imm, 1, 0); E(b_cond, "dk_f", "ne")
        E(bl, "c_dpdrum"); E(cmp_imm, 0, 3); E(b_cond, "dk_f", "hi"); E(mov_reg, 7, 0)
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "dk_f", "ne")
        E(raw, h(0x9800)); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "dk_f", "eq")
        E(mov_reg, 0, 7); E(bl, "c_dpnow"); E(cmp_imm, 0, 64); E(b_cond, "dk_f", "eq")
        E(mov_reg, 0, 7); E(movs_imm, 1, 64); E(bl, "c_dpput")
        a.label("dk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])
    else:
        # ---- c_dpknob (the drum macro handlers' slot 4: handler, knob, delta): K1 = S, Shift + K6 = the stock Pitch, Clear + K6 = P back to 64 too
        a.label("c_dpknob")
        E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
        E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(bl, "c_dpdrum"); E(cmp_imm, 0, 3); E(b_cond, "dk_f", "hi"); E(mov_reg, 7, 0)       # r7 = the drum
        E(bl, L["c_shift"]); E(mov_reg, 4, 0)                                               # r4 = Shift
        E(cmp_imm, 5, 0); E(b_cond, "dk_6", "ne"); E(cmp_imm, 4, 0); E(b_cond, "dk_f", "ne")  # Shift + K1: the chain (pitch envelope / the cents)
        E(raw, h(0x9800)); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "dk_s", "eq")  # ldr r0, [sp]: Clear held?
        E(cmp_imm, 6, 0); E(b_cond, "dk_cl" if REC else "dk_e", "le")
        E(mov_reg, 0, 7); E(movs_imm, 1, 64); E(bl, "c_dpput")
        E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_dzero"])                            # its Shift layer (the pitch envelope)
        E(raw, h(0x9800)); E(movs_imm, 1, 0); E(movs_imm, 2, 1); E(bl, L["c_clr_set"])       # blue
        E(b, "dk_e")
        a.label("dk_s")                                                                     # S += delta, 0..127; in the chromatic view the bias too
        E(mov_reg, 0, 7); E(bl, "c_dpnow"); E(adds_reg, 1, 0, 6)
        E(cmp_imm, 1, 0); E(b_cond, "dk_l", "ge"); E(movs_imm, 1, 0)
        a.label("dk_l"); E(cmp_imm, 1, 127); E(b_cond, "dk_h", "le"); E(movs_imm, 1, 127)
        a.label("dk_h"); E(subs_reg, 6, 1, 0); E(mov_reg, 0, 7); E(bl, "c_dpput")            # r6 = the change applied
        E(mov_reg, 0, 7); E(bl, L["c_dview"]); E(cmp_imm, 0, 0); E(b_cond, "dk_e", "eq")
        E(ldrb_w, 1, 0, FLAG); E(lsls_imm, 1, 1, 31); E(b_cond, "dk_e", "eq")
        E(ldrb_w, 1, 0, BIAS); E(raw, sxtb(1, 1)); E(adds_reg, 1, 1, 6); E(strb_w, 1, 0, BIAS)
        E(b, "dk_e")
        a.label("dk_6")
        E(cmp_imm, 5, 5); E(b_cond, "dk_f", "ne")
        E(cmp_imm, 4, 0); E(b_cond, "dk_6c", "eq")
        E(raw, h(0x9800)); E(movs_imm, 1, 1); E(mov_reg, 2, 6); E(bl, DK_STOCK); E(b, "dk_e")    # Shift + K6: the stock Pitch
        a.label("dk_6c")                                                                    # K6 with Clear right: P back to 64 as well, then the chain
        E(raw, h(0x9800)); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "dk_f", "eq"); E(cmp_imm, 6, 0); E(b_cond, "dk_f", "le")
        imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0); E(adds_imm8, 0, 4)
        E(movs_imm, 1, 0x10); E(lsls_imm, 2, 7, 3); E(subs_reg, 2, 2, 7); E(adds_imm8, 2, 2); E(movs_imm, 3, 64); E(bl, PARAM_SET)
        a.label("dk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])
        a.label("dk_e"); E(raw, h(0xB003)); E(pop_list, [4, 5, 6, 7], pc=True)                  # add sp, #12
        if REC:
            a.label("dk_cl")                                                                # Clear + K1 left: lane 7 of the playing pattern deleted, red
            E(cmp_imm, 6, 0); E(b_cond, "dk_e", "eq")
            E(mov_reg, 0, 7); E(bl, "c_dplane"); E(movs_imm, 1, 0xFF); E(movs_imm, 2, 0)
            a.label("dk_cz"); E(raw, h(0x5481)); E(adds_imm8, 2, 1); E(cmp_imm, 2, 192); E(b_cond, "dk_cz", "lo")   # strb r1, [r0, r2]
            E(mov_reg, 0, 7); E(bl, "c_dpoff")
            E(raw, h(0x9800)); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(bl, L["c_clr_set"])       # red
            E(b, "dk_e")

    # ---- c_dppad(r0 = the chromatic drum view, r1 = the note's value): S (instead of SC11's Pitch); clobbers r0-r3
    a.label("c_dppad")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 0, 0)
    a.label("dv_l")
    E(push_list, [0]); E(bl, L["c_dview"]); E(pop_list, [1]); E(cmp_reg, 0, 4); E(b_cond, "dv_y", "eq")
    E(adds_imm8, 1, 1); E(mov_reg, 0, 1); E(cmp_imm, 0, 4); E(b_cond, "dv_l", "lo"); E(pop_list, [4, 5], pc=True)
    a.label("dv_y"); E(mov_reg, 0, 1)
    if REC: E(mov_reg, 4, 0)                                                            # r4 = the drum
    E(mov_reg, 1, 5); E(bl, "c_dpput")
    if REC:                                                                             # Record armed and playing (not the count-in): into lane 7
        for k, z in ((0, "eq"), (1, "eq"), (2, "ne")):
            imm32(0, TRANSPORT); E(movs_imm, 1, k); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "dv_x", z)
        E(mov_reg, 0, 4); E(bl, "c_dplane"); E(raw, h(0xB401))                           # push {r0}: the lane
        E(mov_reg, 0, 4); E(adds_imm8, 0, 4); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
        E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(raw, h(0xBC02))       # the playing step; pop {r1}
        E(cmp_imm, 0, 31); E(b_cond, "dv_x", "hi")
        E(movs_imm, 2, 6); E(muls, 0, 2); E(adds_reg, 1, 1, 0)
        if L0:                                                                          # 0x80 | S (S at most 126: 0xFF is the empty byte)
            E(mov_reg, 3, 5); E(cmp_imm, 3, 126); E(b_cond, "dv_t", "ls"); E(movs_imm, 3, 126)
            a.label("dv_t"); E(adds_imm8, 3, 0x80)
            for m in range(6): E(strb_imm, 3, 1, m)
        else:
            for m in range(6): E(strb_imm, 5, 1, m)
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dpeff")
        a.label("dv_x")
    E(pop_list, [4, 5], pc=True)

    if REC:
        from build_sc14 import udiv
        # ---- c_dpcur(r0 = drum) -> r0 = the S that sounds: a step's while it plays, else the knob's; clobbers r1-r3
        a.label("c_dpcur")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(bl, "c_dpblk"); E(cmp_imm, 0, 0); E(b_cond, "cu_k", "eq")
        E(ldrb_imm, 1, 0, O_ACT - O_BLK); E(raw, h(0x40E1)); E(lsls_imm, 1, 1, 31); E(b_cond, "cu_k", "pl")   # lsrs r1, r4
        E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, O_EFF - O_BLK); E(pop_list, [4], pc=True)
        a.label("cu_k"); E(mov_reg, 0, 4); E(bl, "c_dpnow"); E(pop_list, [4], pc=True)
        # ---- c_dpeff(r0 = drum, r1 = a step's S 0..127, or 0xFF = none); clobbers r0-r3
        a.label("c_dpeff")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
        E(bl, "c_dpblk"); E(cmp_imm, 0, 0); E(b_cond, "ef_x", "eq")
        E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 0, O_ACT - O_BLK); E(raw, h(0x438A))       # lsls r1, r4; bics r2, r1
        E(cmp_imm, 5, 127); E(b_cond, "ef_w", "hi")
        E(orrs_reg, 2, 1); E(adds_reg, 3, 0, 4); E(strb_imm, 5, 3, O_EFF - O_BLK)
        a.label("ef_w"); E(strb_imm, 2, 0, O_ACT - O_BLK)
        a.label("ef_x"); E(pop_list, [4, 5], pc=True)
        # ---- c_dpoff(r0 = drum): no step's S, the knob's pitch to the DSP (the interface task only); clobbers r0-r3
        a.label("c_dpoff")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(movs_imm, 1, 0xFF); E(bl, "c_dpeff")
        E(lsls_imm, 1, 4, 3); E(subs_reg, 1, 1, 4); E(adds_imm8, 1, 2); E(movs_imm, 0, 0x10); E(bl, MARK_DIRTY)
        E(pop_list, [4], pc=True)
        # ---- c_dplane(r0 = drum) -> r0 = lane 7 of the pattern it plays; clobbers r1-r3
        a.label("c_dplane")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(adds_imm8, 0, 4); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
        E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0)                          # the pattern
        imm32(0, PAT_SZ); E(muls, 1, 0); imm32(0, DP0); E(movs_imm, 2, DP_SZ); E(muls, 2, 4); E(adds_reg, 0, 0, 2); E(ldr_imm, 0, 0, 0x48)
        E(adds_reg, 0, 0, 1); imm32(1, 0xA8 + 192 * LANE); E(adds_reg, 0, 0, 1)
        E(pop_list, [4], pc=True)
        # ---- c_dpauto (the players' step: bl 0x0804A7CA(player, pattern, step, micro step)): the stock's, then for a drum lane 7 = its S
        a.label("c_dpauto")
        E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
        E(bl, AUTO)
        E(pop_list, [0, 1, 2, 3])
        E(mov_reg, 7, 0); E(mov_reg, 6, 1)                                                    # r7 = the player, r6 = the pattern
        imm32(4, DP0); E(subs_reg, 4, 0, 4); E(movs_imm, 5, DP_SZ); E(raw, udiv(5, 4, 5))
        E(cmp_imm, 5, 3); E(b_cond, "da_x", "hi")
        E(movs_imm, 0, DP_SZ); E(muls, 0, 5); E(cmp_reg, 0, 4); E(b_cond, "da_x", "ne")      # r5 = the drum
        if not L0:
            E(ldrb_w, 0, 7, 0x38); E(cmp_imm, 0, LANE); E(b_cond, "da_m", "ls")
            E(movw, 4, 0xFFFF); E(ldr_imm, 0, 7, 0x40); E(strh_imm, 4, 0, 2 * LANE); E(ldr_imm, 0, 7, 0x44); E(strh_imm, 4, 0, 2 * LANE)
            a.label("da_m")
        E(cmp_imm, 3, 0); E(b_cond, "da_x", "ne"); E(cmp_imm, 2, 31); E(b_cond, "da_x", "hi")
        E(ldr_imm, 0, 7, 0x48); imm32(4, PAT_SZ); E(muls, 4, 6); E(adds_reg, 0, 0, 4); imm32(4, 0xA8 + 192 * LANE); E(adds_reg, 0, 0, 4)
        E(movs_imm, 4, 6); E(muls, 4, 2); E(adds_reg, 0, 0, 4); E(ldrb_imm, 6, 0, 0)          # r6 = the lane's byte at the step
        if L0:                                                                          # a chromatic step = 0x80 | S; anything else = none
            E(cmp_imm, 6, 0x80); E(b_cond, "da_n", "lo"); E(cmp_imm, 6, 0xFF); E(b_cond, "da_n", "eq"); E(subs_imm8, 6, 0x80); E(b, "da_g")
            a.label("da_n"); E(movs_imm, 6, 0xFF)
            a.label("da_g")
        E(mov_reg, 0, 5); E(bl, "c_dpcur"); E(mov_reg, 4, 0)                                  # r4 = the S before
        E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_dpeff")
        E(mov_reg, 0, 5); E(bl, "c_dpcur"); E(cmp_reg, 0, 4); E(b_cond, "da_x", "eq")
        E(mov_reg, 0, 5); E(bl, L["c_pitchnow"]); E(mov_reg, 1, 0); E(mov_reg, 0, 5); E(bl, "c_dpword")
        E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(movs_imm, 2, 10); E(muls, 2, 5); E(adds_imm8, 2, PITCH_X); E(bl, DSP_W)
        a.label("da_x"); E(pop_list, [4, 5, 6, 7], pc=True)
        if not L0:
            # ---- c_dpgate (the automation gate: gate, id, value): a drum's pan (ids 89-92) not recorded
            a.label("c_dpgate")
            E(cmp_imm, 1, LANE_IDS[0]); E(b_cond, "dg_f", "lo"); E(cmp_imm, 1, LANE_IDS[1]); E(b_cond, "dg_f", "hi")
            E(movs_imm, 0, 1); E(raw, RET)
            a.label("dg_f"); E(b_w, prev["gate"])
        else:
            # ---- c_dplv (L0; in place of 0x0804A7CA's ldrb r7, [r1, r0]; b 0x0804A84A: r5 = the lane, r6 = the player; r0-r3 free there):
            #      a drum's lane 0 byte 0x80..0xFE (a chromatic step) -> 0xFFFF, so the stock does not move P
            a.label("c_dplv")
            E(raw, h(0x5C0F))                                                                # ldrb r7, [r1, r0]
            E(cmp_imm, 5, 0); E(b_cond, "lv_x", "ne"); E(cmp_imm, 7, 0x80); E(b_cond, "lv_x", "lo"); E(cmp_imm, 7, 0xFF); E(b_cond, "lv_x", "eq")
            imm32(1, DP0); E(subs_reg, 1, 6, 1); E(movs_imm, 2, DP_SZ); E(raw, udiv(3, 1, 2)); E(cmp_imm, 3, 3); E(b_cond, "lv_x", "hi")
            E(muls, 2, 3); E(cmp_reg, 2, 1); E(b_cond, "lv_x", "ne")
            E(movw, 7, 0xFFFF)
            a.label("lv_x"); E(b_w, LV_BACK)
        # ---- c_dpledtask (the LED task calls: ctrl, frame): the chain; stopped, the steps' S give way to the knobs'
        a.label("c_dpledtask")
        E(push_list, [3, 4, 5], lr=True)
        E(bl, prev["ledtask"])
        E(bl, "c_dpblk"); E(cmp_imm, 0, 0); E(b_cond, "dt_x", "eq"); E(ldrb_imm, 5, 0, O_ACT - O_BLK); E(cmp_imm, 5, 0); E(b_cond, "dt_x", "eq")
        imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "dt_x", "ne")
        E(movs_imm, 4, 0)
        a.label("dt_l"); E(mov_reg, 0, 5); E(raw, h(0x40E0)); E(lsls_imm, 0, 0, 31); E(b_cond, "dt_n", "pl")   # lsrs r0, r4
        E(mov_reg, 0, 4); E(bl, "c_dpoff")
        a.label("dt_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "dt_l", "lo")
        a.label("dt_x"); E(pop_list, [3, 4, 5], pc=True)

    if not L0:
        # ---- c_dpled (the drum macro handlers' slot 7: handler -> the LED buffer): K1 = S; with Shift K6 = P (|v - 64| x 2, dim at 64)
        a.label("c_dpled")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
        E(mov_reg, 0, 4); E(bl, "c_dpdrum"); E(cmp_imm, 0, 3); E(b_cond, "dl_x", "hi"); E(mov_reg, 7, 0)
        imm32(1, t_col); E(adds_reg, 1, 1, 7); E(ldrb_imm, 6, 1, 0)                           # r6 = the drum's colour
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "dl_s", "ne")
        E(mov_reg, 0, 7); E(bl, "c_dpnow"); E(movs_imm, 1, 0); E(b, "dl_w")
        a.label("dl_s")
        E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 10)   # P; position 5
        a.label("dl_w")
        E(subs_imm8, 0, 64); E(b_cond, "dl_p", "pl"); E(raw, h(0x4240))                        # negs r0, r0
        a.label("dl_p"); E(lsls_imm, 0, 0, 1); E(cmp_imm, 0, 127); E(b_cond, "dl_c", "ls"); E(movs_imm, 0, 127)
        a.label("dl_c"); E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 6); E(raw, h(0x5268))   # strh r0, [r5, r1]
        a.label("dl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the four conversion calls, slots 4 / 7 of the drum macro handlers, SC11's pad setter call and its bias start."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_conv0=lab("sc12", "c_conv0"), c_dview=lab("sc11", "c_dview"), c_shift=lab("sc15", "c_shift"),
             c_clr_held=lab("persist19", "c_clr_held"), c_clr_set=lab("persist19", "c_clr_set"), c_dzero=lab("persist19", "c_dzero"))
    for d in range(1, 4): assert lab("sc12", f"c_conv{d}") == L["c_conv0"] + 16 * d
    prev = dict(knob=u(MH_VT + 16) & ~1, leds=u(MH_VT + 28) & ~1)
    if REC:
        import packio as PK, fxdiag as FD, mpatch as MP
        prev.update(gate=MP.bw_target(img, REC_GATE, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
        assert bytes(img[AUTO_CALL - BASE:AUTO_CALL - BASE + 4]) == bl_enc(AUTO_CALL, AUTO)
        if L0: assert bytes(img[LV_AT - BASE:LV_AT - BASE + 4]) == LV_OLD
        L["c_pitchnow"] = lab("sc11", "c_pitchnow")
    for d, c in enumerate(S12.CALLS):
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, lab("sc12", f"c_conv{d}")), hex(c)
    pad_at = lab("sc11", "dp_c2"); assert bytes(img[pad_at - BASE:pad_at - BASE + 14]) == DP_OLD, hex(pad_at)
    bias_at = lab("sc11", "c_shbtn2") + 0x38; assert bytes(img[bias_at - BASE:bias_at - BASE + 4]) == bl_enc(bias_at, lab("sc11", "c_pitchnow")), hex(bias_at)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for d, c in enumerate(S12.CALLS):
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels[f"c_dpc{d}"])
    struct.pack_into("<I", img, MH_VT + 16 - BASE, labels["c_dpknob"] | 1)
    if not L0: struct.pack_into("<I", img, MH_VT + 28 - BASE, labels["c_dpled"] | 1)
    if REC:
        from thumb import b_w as bw
        img[AUTO_CALL - BASE:AUTO_CALL - BASE + 4] = bl_enc(AUTO_CALL, labels["c_dpauto"])
        if L0: img[LV_AT - BASE:LV_AT - BASE + 4] = bw(LV_AT, labels["c_dplv"])
        else: img[REC_GATE - BASE:REC_GATE - BASE + 4] = bw(REC_GATE, labels["c_dpgate"])
        for c in PK.LED_CALLS:
            assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
            img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_dpledtask"])
    img[pad_at - BASE:pad_at - BASE + 14] = h(0x4620) + h(0x4611) + bl_enc(pad_at + 4, labels["c_dppad"]) + h(0xBF00) * 3   # mov r0, r4; mov r1, r2; bl
    img[bias_at - BASE:bias_at - BASE + 4] = bl_enc(bias_at, labels["c_dpnow"])
    return labels, code, prev
