"""Alpha 7.08 (the user, 2026-11-19: «FX sequencer change.  The current FX sequencer is discarded.  Instead, we make a new step sequencer on the
Master FX view.  Hold an FX pad, then a song pointer step: every iteration, the FX plays at that step.  Clear + a pad without an FX: that step is
muted.  Clear + a pad with an FX / mute: that step is back to normal» -> «All, including sample», «Add», «With the project»).

The 16 steps are the song pointer's (pads 9-24 of the Master FX view = steps 1-16 of the 16-step cycle, c_spcur).  Each step holds a mask
(16 bits): bits 0-6 = top pads 1-7 (the effects 1-6 and the sample on pad 7), bits 8-13 = bottom pads 26-31 (the slots, the gesture on 31),
bit 14 = random, bit 15 = mute.
  * an FX pad held ([MGR + 0x84]: pads 1-7, 26-31) + a step pad = those pads added to the step (a muted step loses its mute); the song pointer
    does not see that press;
  * Clear + a step pad: an empty step = muted; a step with FX or mute = empty again;
  * Duplicate + a step pad (the user, 2026-11-19: «Also add random step … duplicate + step: random») = random on / off (the mute off): each time
    the step comes round, one of its FX picked at random (an empty random step: one of the six top effects); violet;
  * playing (the transport on), during step s: its top effects join the pads held / latched (a wrapper of every call of build_sc17's c_fsqfx), its
    slots and mute go through c_fxsq (the old sequencer's hook: its 4 bytes, a b.w to vcf21's c_fsqbits, now a b.w here; slot bits 0-5 = pads
    26-31, bit 7 = the whole master muted, masterfx_dsp's B_MUTE) as the old sequencer's did; the sample (pad 7): entering a step with it =
    start + gate (as a press of pad 7), leaving it = the gate off;
  * the step pads: a step with FX in the colour of its first pad (the pad's own LED), a muted step red; the playhead white as before;
  * saved with the project: 32 bytes in bytes 8..39 of the settings of MIDI 1's pattern 8 (projsyn 0..4, stpair 5 / 6; MIDI 2's 5 / 6 = wtui):
    byte i = the top bits of step i, byte 16 + i = its bottom bits | mute in bit 6 | random in bit 7; bit 7 of byte i (i < 16) = i & 1 (the signature: a factory pack's
    garbage, all 0 or all 0xFF, does not pass); written by a head of the save call (when something is set or the block is ours), read by a head of
    the load's re-send (a load, a new project, power-up: no block = empty);
  * the old sequencer's way in (pad 31 of the engine row with no voice) is closed: the pad does nothing and is not lit.
RAM FXS = 0x2004FB10 (48 B, free below drumpat's CNT): + 0 "FXS1", + 4 the step last seen (0xFF), + 5 1 = the sample's gate is ours, + 6 the random step's pick, + 8 the random state, + 16 the masks.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (lsrs_reg, lsls_reg, muls, eors_reg, subs_imm8, Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, bics_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrh_imm,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm,
                   strb_reg, strh_imm, tst_reg)
import build_sc17 as S  # noqa: E402
import fxdiag as FD  # noqa: E402
import persist19 as P19  # noqa: E402
import projsyn as PS  # noqa: E402
import qmute as Q  # noqa: E402
import vcf21 as V  # noqa: E402

FXS = 0x2004FB10
SIG = 0x31535846                                   # "FXS1"
O_SIG, O_LAST, O_GATE, O_PICK, O_RNG, O_M = 0, 4, 5, 6, 8, 16
PAT = 7                                            # MIDI 1's pattern 8
BLK = PS.AREA + PS.PSIZE * PAT + PS.SET + PS.BYTE0
RESEND_CALL = 0x0802F5B4
PARAM_GET = 0x0803542C
HELD = 0x84
TOPMASK = 0x7F                                     # pads 1-7
BOT0, BOTN = 25, 6                                 # pads 26-31 = indices 25..30
MUTE = 0x8000
RANDOM = 0x4000                                    # (the user, 2026-11-19: «Also add random step … duplicate + step: random»)
COL_MUTE = 0x53
COL_RAND = 0x49                                    # violet
RND_A, RND_C = 1664525, 1013904223
SMP_START = 0x10                                   # S_JF: the pending command 1 = start
MODESEL_CMP = bytes.fromhex("1e2d")                # modesel's `cmp r5, #30` (PAD_FXS) in c_mspad


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
def strh_w(rt, rn, off): return h(0xF8A0 | rn) + h(rt << 12 | off)
def ldrh_w(rt, rn, off): return h(0xF8B0 | rn) + h(rt << 12 | off)
def ldrh_reg(rt, rn, rm): return h(0x5A00 | rm << 6 | rn << 3 | rt)
def strh_reg(rt, rn, rm): return h(0x5200 | rm << 6 | rn << 3 | rt)
RET = h(0x4770)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def held(rd):                                                         # rd = the pads held (bit = pad)
        imm32(rd, Q.MGR); E(raw, h(0xF8D0 | rd) + h(rd << 12 | HELD))

    # ---- c_fqst -> r0 = FXS (signed; cleared the first time); clobbers r1-r3
    a.label("c_fqst")
    imm32(0, FXS); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    a.label("c_fqclr")                                                    # (r0 = FXS, r2 = SIG) the masks empty
    E(str_imm, 2, 0, O_SIG); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, O_LAST); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_GATE)
    E(movs_imm, 2, O_M)
    a.label("st_z"); E(raw, h(0x5081)); E(adds_imm8, 2, 4); E(cmp_imm, 2, O_M + 32); E(b_cond, "st_z", "lo")   # str r1, [r0, r2]
    a.label("st_x"); E(raw, RET)

    # ---- c_fqblk -> r0 = the project's block (MIDI 1's pattern 8, settings + 8), 0 = no record; clobbers r1
    a.label("c_fqblk")
    imm32(0, PS.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq")
    imm32(1, BLK); E(adds_reg, 0, 0, 1)
    a.label("bk_x"); E(raw, RET)

    # ---- c_fqsig(r0 = block) -> r0 = 1 when bit 7 of each of the first 16 bytes j = j & 1; clobbers r1-r3
    a.label("c_fqsig")
    E(movs_imm, 1, 0)
    a.label("sg_l"); E(ldrb_reg, 2, 0, 1); E(lsrs_imm, 2, 2, 7); E(movs_imm, 3, 1); E(ands_reg, 3, 1); E(cmp_reg, 2, 3); E(b_cond, "sg_n", "ne")
    E(adds_imm8, 1, 1); E(cmp_imm, 1, 16); E(b_cond, "sg_l", "lo")
    E(movs_imm, 0, 1); E(raw, RET)
    a.label("sg_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_fqpick(r0 = the candidates, 0 = the six top effects) -> r0 = one of them (a single bit) at random; clobbers r1-r3
    a.label("c_fqpick")
    E(push_list, [4, 5], lr=True)
    E(cmp_imm, 0, 0); E(b_cond, "pk_c", "ne"); E(movs_imm, 0, 0x3F)
    a.label("pk_c"); E(mov_reg, 4, 0); E(movs_imm, 1, 0); E(movs_imm, 2, 0)
    a.label("pk_n"); E(mov_reg, 3, 4); E(lsrs_reg, 3, 2); E(lsls_imm, 3, 3, 31); E(b_cond, "pk_z", "eq"); E(adds_imm8, 1, 1)
    a.label("pk_z"); E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "pk_n", "lo")             # r1 = how many
    imm32(5, FXS); E(ldr_imm, 2, 5, O_RNG); imm32(3, V.HAL_TICK); E(ldr_imm, 3, 3, 0); E(adds_reg, 2, 2, 3)
    imm32(3, RND_A); E(muls, 2, 3); imm32(3, RND_C); E(adds_reg, 2, 2, 3); E(str_imm, 2, 5, O_RNG)
    E(lsrs_imm, 2, 2, 16); E(muls, 2, 1); E(lsrs_imm, 2, 2, 16)                              # r2 = which, 0..n-1
    E(movs_imm, 0, 0)
    a.label("pk_w"); E(mov_reg, 3, 4); E(lsrs_reg, 3, 0); E(lsls_imm, 3, 3, 31); E(b_cond, "pk_s", "eq")
    E(cmp_imm, 2, 0); E(b_cond, "pk_f", "eq"); E(subs_imm8, 2, 1)
    a.label("pk_s"); E(adds_imm8, 0, 1); E(b, "pk_w")
    a.label("pk_f"); E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(mov_reg, 0, 3); E(pop_list, [4, 5], pc=True)

    # ---- c_fqcur (r4 = the Master FX block) -> r0 = the mask of the step playing (0: stopped); the sample's start / gate on a step change
    a.label("c_fqcur")
    E(push_list, [5, 6, 7], lr=True)
    imm32(0, S.PLAY_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 5, 0xFF); E(cmp_imm, 0, 0); E(b_cond, "cu_s", "eq")
    E(bl, L["c_spcur"]); E(mov_reg, 5, 0)                                  # r5 = the step 0-15 / 0xFF
    a.label("cu_s")
    E(bl, "c_fqst"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 0); E(cmp_imm, 5, 16); E(b_cond, "cu_m", "hs")
    E(lsls_imm, 1, 5, 1); E(adds_imm8, 1, O_M)
    E(raw, ldrh_reg(7, 6, 1))                                             # r7 = the mask
    a.label("cu_m")
    E(ldrb_imm, 0, 6, O_LAST); E(cmp_reg, 0, 5); E(b_cond, "cu_k", "eq")
    E(strb_imm, 5, 6, O_LAST)
    E(movs_imm, 0, RANDOM >> 8); E(lsls_imm, 0, 0, 8); E(tst_reg, 7, 0); E(b_cond, "cu_nr", "eq")   # a random step: one of its FX (none: a top effect)
    E(bics_reg, 7, 0); E(mov_reg, 0, 7); E(bl, "c_fqpick"); E(mov_reg, 7, 0); E(raw, strh_w(7, 6, O_PICK))
    a.label("cu_nr")
    E(raw, ldrb_w(1, 4, S.S_JF))
    E(ldrb_imm, 0, 6, O_GATE); E(cmp_imm, 0, 0); E(b_cond, "cu_g", "eq")  # our gate: off (a latched loop keeps it)
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_GATE)
    E(movs_imm, 2, S.SMB_LOOP); E(tst_reg, 1, 2); E(b_cond, "cu_g", "ne"); E(movs_imm, 2, S.SMB_GATE); E(bics_reg, 1, 2)
    a.label("cu_g")
    E(movs_imm, 2, 1 << S.SMP_PAD); E(tst_reg, 7, 2); E(b_cond, "cu_w", "eq")   # the sample on this step: start, the gate held
    E(movs_imm, 2, 0x30 | S.SMB_LOOP); E(bics_reg, 1, 2); E(movs_imm, 2, SMP_START | S.SMB_GATE); E(orrs_reg, 1, 2)
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, O_GATE)
    a.label("cu_w"); E(raw, strb_w(1, 4, S.S_JF)); E(b, "cu_x")
    a.label("cu_k")                                                       # the same step: a random one plays what it picked
    E(movs_imm, 0, RANDOM >> 8); E(lsls_imm, 0, 0, 8); E(tst_reg, 7, 0); E(b_cond, "cu_x", "eq"); E(raw, ldrh_w(7, 6, O_PICK))
    a.label("cu_x"); E(mov_reg, 0, 7); E(pop_list, [5, 6, 7], pc=True)

    # ---- c_fqsq (build_sc17's c_fxsq; r4 = the block) -> slot bits 0-5 (pads 26-31) | bit 7 = mute
    a.label("c_fqsq")
    E(push_list, [], lr=True)
    E(bl, "c_fqcur"); E(lsrs_imm, 0, 0, 8); E(movs_imm, 1, 0xBF); E(ands_reg, 0, 1)
    E(pop_list, [], pc=True)

    # ---- c_fqfx (every bl c_fsqfx; r4 = the block) -> c_fsqfx's bits | the step's top effects (pads 1-6)
    a.label("c_fqfx")
    E(push_list, [5], lr=True)
    E(bl, prev["fsqfx"]); E(mov_reg, 5, 0)
    E(bl, "c_fqcur"); E(movs_imm, 1, 0x3F); E(ands_reg, 0, 1); E(orrs_reg, 0, 5)
    E(pop_list, [5], pc=True)

    # ---- c_fqsp (the entry of c_sp_press: r0 = pad 8-23): an FX pad held / Clear / Duplicate held = ours, else the song pointer
    a.label("c_fqsp")
    E(push_list, [0, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 0)
    E(raw, h(0x3D08))                                                     # subs r5, #8: the step 0-15
    held(6)
    E(movs_imm, 7, TOPMASK); E(ands_reg, 7, 6)
    E(lsrs_imm, 6, 6, BOT0); E(movs_imm, 0, (1 << BOTN) - 1); E(ands_reg, 6, 0); E(lsls_imm, 6, 6, 8); E(orrs_reg, 7, 6)   # r7 = the FX held
    E(bl, "c_fqst"); E(mov_reg, 4, 0); E(lsls_imm, 6, 5, 1); E(adds_imm8, 6, O_M)                                       # r6 = the mask's offset
    E(cmp_imm, 7, 0); E(b_cond, "sp_c", "eq")
    E(raw, ldrh_reg(0, 4, 6)); E(lsls_imm, 0, 0, 17); E(lsrs_imm, 0, 0, 17); E(orrs_reg, 0, 7)                         # + the FX, the mute off
    a.label("sp_w"); E(raw, strh_reg(0, 4, 6))
    E(raw, h(0xB001)); E(pop_list, [4, 5, 6, 7], pc=True)                 # add sp, #4 (r0)
    a.label("sp_c")
    E(bl, L["c_gclrh"]); E(cmp_imm, 0, 0); E(b_cond, "sp_cl", "ne")
    imm32(0, Q.MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "sp_s", "eq")                              # Duplicate held: random on / off, the mute off
    E(raw, ldrh_reg(0, 4, 6)); E(movs_imm, 1, RANDOM >> 8); E(lsls_imm, 1, 1, 8); E(eors_reg, 0, 1)
    E(lsls_imm, 0, 0, 17); E(lsrs_imm, 0, 0, 17); E(b, "sp_w")
    a.label("sp_cl")
    E(raw, ldrh_reg(1, 4, 6)); E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "sp_w", "ne")
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 15); E(b, "sp_w")                # empty: muted
    a.label("sp_s")                                                       # the song pointer: c_sp_press's first two instructions, then the rest
    E(raw, popw([0, 4, 5, 6, 7], lr=True))
    E(push_list, [4, 5, 6], lr=True); E(raw, h(0x3807))                   # subs r0, #7
    E(b_w, prev["sp_press"] + 4)

    # ---- c_fqled (every bl c_sp_leds: r0 = the LED buffer): then the steps with FX in their first pad's colour, muted ones red, not the playhead
    a.label("c_fqled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["sp_leds"])
    E(bl, L["c_spcur"]); E(mov_reg, 5, 0)
    E(bl, "c_fqst"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 0)
    a.label("ld_l")
    E(cmp_reg, 7, 5); E(b_cond, "ld_n", "eq")
    E(lsls_imm, 1, 7, 1); E(adds_imm8, 1, O_M); E(raw, ldrh_reg(1, 6, 1)); E(cmp_imm, 1, 0); E(b_cond, "ld_n", "eq")
    E(movs_imm, 0, COL_MUTE)
    E(lsls_imm, 2, 1, 16); E(b_cond, "ld_w", "mi")                       # bit 15: muted
    E(movs_imm, 0, COL_RAND); E(lsls_imm, 2, 1, 17); E(b_cond, "ld_w", "mi")   # bit 14: random
    E(movs_imm, 2, 0)                                                     # r2 = the first pad (index)
    E(movs_imm, 3, TOPMASK); E(tst_reg, 1, 3); E(b_cond, "ld_t", "ne")
    E(lsrs_imm, 1, 1, 8); E(movs_imm, 2, BOT0)
    a.label("ld_t"); E(lsrs_imm, 3, 1, 1); E(b_cond, "ld_f", "cs"); E(mov_reg, 1, 3); E(adds_imm8, 2, 1); E(b, "ld_t")
    a.label("ld_f"); E(lsls_imm, 2, 2, 1); E(raw, ldrh_reg(0, 4, 2))      # its own LED
    a.label("ld_w"); E(lsls_imm, 2, 7, 1); E(adds_imm8, 2, 16); E(raw, strh_reg(0, 4, 2))
    a.label("ld_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "ld_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fqsave (the bl of the stock save): the masks into the record's block (when one is set or the block is ours), then the chain
    a.label("c_fqsave")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    imm32(0, FXS); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "sv_x", "ne")
    E(mov_reg, 6, 0)
    E(bl, "c_fqblk"); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq"); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0); E(movs_imm, 2, 0)
    a.label("sv_a"); E(lsls_imm, 3, 1, 1); E(adds_imm8, 3, O_M); E(raw, ldrh_reg(3, 6, 3)); E(orrs_reg, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, 16); E(b_cond, "sv_a", "lo")
    E(cmp_imm, 2, 0); E(b_cond, "sv_w", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fqsig"); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq")
    a.label("sv_w")
    E(movs_imm, 5, 0)
    a.label("sv_l")
    E(lsls_imm, 3, 5, 1); E(adds_imm8, 3, O_M); E(raw, ldrh_reg(3, 6, 3))                    # r3 = the mask
    E(lsls_imm, 7, 5, 31); E(lsrs_imm, 7, 7, 24)                                           # r7 = (i & 1) << 7
    E(movs_imm, 0, TOPMASK); E(ands_reg, 0, 3); E(orrs_reg, 0, 7); E(raw, strb_reg(0, 4, 5))
    E(lsrs_imm, 0, 3, 8); E(movs_imm, 1, 0x3F); E(ands_reg, 0, 1)
    E(lsrs_imm, 1, 3, 15); E(lsls_imm, 1, 1, 6); E(orrs_reg, 0, 1)
    E(lsls_imm, 1, 3, 17); E(lsrs_imm, 1, 1, 31); E(lsls_imm, 1, 1, 7); E(orrs_reg, 0, 1)    # random -> bit 7
    E(adds_imm8, 5, 16); E(raw, strb_reg(0, 4, 5))
    E(raw, h(0x3D10))                                                                      # subs r5, #16
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 16); E(b_cond, "sv_l", "lo")
    a.label("sv_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["save"])

    # ---- c_fqload (the load's re-send: a load, a new project, power-up): the masks from the project's block, or empty
    a.label("c_fqload")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    imm32(0, FXS); imm32(2, SIG); E(bl, "c_fqclr"); E(mov_reg, 6, 0)
    E(bl, "c_fqblk"); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq"); E(mov_reg, 4, 0)
    E(bl, "c_fqsig"); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq")
    E(movs_imm, 5, 0)
    a.label("lo_l")
    E(ldrb_reg, 0, 4, 5); E(movs_imm, 1, TOPMASK); E(ands_reg, 0, 1)
    E(adds_imm8, 5, 16); E(ldrb_reg, 1, 4, 5); E(raw, h(0x3D10))                           # subs r5, #16
    E(movs_imm, 2, 0x3F); E(ands_reg, 2, 1); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2)
    E(lsrs_imm, 2, 1, 7); E(lsls_imm, 2, 2, 14); E(orrs_reg, 0, 2)                           # bit 7 -> random
    E(lsls_imm, 1, 1, 25); E(lsrs_imm, 1, 1, 31); E(lsls_imm, 1, 1, 15); E(orrs_reg, 0, 1)   # bit 6 -> the mute
    E(lsls_imm, 3, 5, 1); E(adds_imm8, 3, O_M); E(raw, strh_reg(0, 6, 3))
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 16); E(b_cond, "lo_l", "lo")
    a.label("lo_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["resend"])
    return a.assemble()


def bl_sites(img, BASE, target):
    out = []
    for o in range(0, len(img) - 4, 2):
        h1, h2 = struct.unpack_from("<HH", img, o)
        if h1 & 0xF800 != 0xF000 or h2 & 0xD000 != 0xD000: continue
        if FD.bl_target(img, BASE + o, BASE) == target: out.append(BASE + o)
    return out


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    s17 = {k: int(v, 16) for k, v in report["sc17"]["labels"].items()}
    ms = {k: int(v, 16) for k, v in report["modesel"]["labels"].items()}
    L = dict(c_spcur=s17["c_spcur"], c_gclrh=s17["c_gclrh"])
    prev = dict(fsqfx=s17["c_fsqfx"], sp_press=s17["c_sp_press"], sp_leds=s17["c_sp_leds"],
                save=FD.bl_target(img, P19.SAVE_CALL, BASE), resend=FD.bl_target(img, RESEND_CALL, BASE))
    fx = s17["c_fxsq"]
    assert bytes(img[prev["sp_press"] - BASE:prev["sp_press"] - BASE + 4]) == bytes.fromhex("70b50738"), "c_sp_press: push {r4-r6, lr}; subs r0, #7"
    s_fx = bl_sites(img, BASE, prev["fsqfx"])
    s_led = bl_sites(img, BASE, prev["sp_leds"])
    assert len(s_fx) >= 3 and len(s_led) >= 1, (s_fx, s_led)
    import modesel
    if not modesel.NOFSQ:                                  # (without vcf21.use_nofsq: modesel's pad 31 code is there; branches past it)
        i0 = ms["c_mspad"] - BASE
        k = bytes(img[i0:ms["sp_nf"] - BASE]).find(MODESEL_CMP)
        assert k >= 0 and k % 2 == 0, "modesel: cmp r5, #30"
        cmp_at = ms["c_mspad"] + k
        led_at = ms["ml_fw"] - 16
        assert bytes(img[led_at - BASE + 4:led_at - BASE + 6]) == bytes([0x0F, 0x21]), "modesel: movs r1, #0x0F after bl c_msmode"
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    put_bl = lambda at, lb: img.__setitem__(slice(at - BASE, at - BASE + 4), bl(at, labels[lb]))
    img[fx - BASE:fx - BASE + 4] = b_w(fx, labels["c_fqsq"])
    img[prev["sp_press"] - BASE:prev["sp_press"] - BASE + 4] = b_w(prev["sp_press"], labels["c_fqsp"])
    for s_ in s_fx: put_bl(s_, "c_fqfx")
    for s_ in s_led: put_bl(s_, "c_fqled")
    put_bl(P19.SAVE_CALL, "c_fqsave"); put_bl(RESEND_CALL, "c_fqload")
    prev.update(fx_sites=len(s_fx), led_sites=len(s_led))
    if not modesel.NOFSQ:
        def b16(at, to): return struct.pack("<H", 0xE000 | (((to - at - 4) >> 1) & 0x7FF))
        img[cmp_at - BASE:cmp_at - BASE + 2] = b16(cmp_at, ms["sp_nf"])                   # modesel: pad 31 no longer the FX sequencer
        img[led_at - BASE:led_at - BASE + 4] = b16(led_at, ms["ml_fn"]) + bytes.fromhex("00bf")   # ... nor lit
        import hole
        hole.rehash(img, report, cmp_at); hole.rehash(img, report, led_at)               # modesel lives in the hole
        prev.update(cmp_at=cmp_at, led_at=led_at)
    return labels, code, prev
