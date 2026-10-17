"""SC44 (the user, 2026-10-17: «A, but instead of Sk8, sample selection mode overtakes the note expand view, and the available samples are the whole
library. Ideally, sample flipping (recorded live or sequenced) will be available too»): the sample picker and the sample flips of the own engine's
sample mode (vcf21.use_sampler, vcf21_dsp.use_sampler).

While MIDI 1 / 2 is in the sample mode, its expanded Note view (Note twice: [ctrl + 0x152] = 24 / 33; the tracks' container 0x0805A62C dispatches it)
is the picker:
  * rows 1-2 = the 16 steps of the page (1-16 / 17-32 = the other half): hold a step and tap a sample = that step's flip; Clear + step = no flip;
    LEDs: a flip = peach, none = dim cyan (the background), the step playing = white, the held one = green;
  * rows 3-4 = 16 samples of the pack (Octave down / up = the next / previous of 4 pages, as the own synth's patch slots: all 64): a tap = the track's sample (code 25, saved with the engine) and it sounds
    (note 60 = as recorded, through the engine); with Record + Play the tap is recorded: a note 60 and the flip in its step; LEDs: the track's
    sample cyan, the held step's flip yellow, the others dim;
  * a flip is a byte of lane 8 of the MIDI track's pattern = 0x80 | the sample, the same in the step's six micro steps (0xFF = none).  Lane 8 is
    the track's level automation (the gate's ids 60 + t; lanes 8-11 of a note track = level, reverb, delay, pan): the stock writes 0..127 there and
    plays every byte but 0xFF (0x0804BA8C / 0x0804BB02: ldrb.w r2, [rN, #0x3a8], then the lane's id from [obj + 0x58]); both loads -> c_spal1 /
    c_spal2: a byte 0x80..0xFE of lane 8 = 0xFF, so a flip does not move the level, and the level automation of other steps still plays.  A flip
    replaces the level automation of its step (and recording the level overwrites flips); it moves with the steps (Nudge, duplicate) and goes
    with the project;
  * the players' slot 2 (every micro step): a MIDI track in the sample mode: the lane's byte of that micro step = the pending sample of the notes
    that start there (vcf21.c_vsmpend: the TRIG carries it), none = cleared.
State (RAM): SC16's block (c_gst() + 24) bytes 14 (page bits 0-1, half bit 2) and 15 (the held step + 1); nothing saved.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import ldrb_w  # noqa: E402
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_sp, strb_imm, strb_reg, strh_reg, ands_reg, subs_imm8,
                   subs_reg, eors_reg, bics_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import arp as A  # noqa: E402

MGR, S_CUR, PICK = 0x20040B10, 0x152, (24, 33)
CONT_VT = 0x0805A62C                                          # slot 0 pad (obj, pad, vel), slot 1 release (obj, pad), slot 7 the LED buffer (obj)
TX, NOTE_ON_VT, NOTE_OFF_VT = 0x20011334, 0x08059FC4, 0x08059FC8
REC, REC_ON, REC_OFF = 0x2003C168, 0x0802E56A, 0x0802E5CC
ENG, TRANSPORT, PARAM_GET = 0x20038EC0, 0x20011034, 0x0803542C
HELD = 0x20                                                   # [[ctrl + 0x20] + 0xC] p0: the held buttons (bit 0 Clear)
LANE = 0x3A8 + 8 * 192                                        # lane 8 of a note pattern (6 bytes a step): the track's level automation (0..127, the gate's
                                                              # ids 60 + t); a flip = 0x80 | the sample, hidden from the stock's lane player
FLIP = 0x80
LV_READS = ((0x0804BAC6, 3, "c_spal1"), (0x0804BB2C, 2, "c_spal2"))   # the stock's ldrb.w r2, [rN, #0x3a8] of the lane player (0x0804BA8C, 0x0804BB02)
PAT_SZ, ROOT = 0xCA8, 60
ID_DOWN, ID_UP, ID_HALF = 19, 20, 21
O_ST, O_HELD = 14, 15                                         # bytes of SC16's block
COL_FLIP, COL_DIM, COL_PLAY, COL_HELD, COL_SEL, COL_HF, COL_BTN, COL_HALF = 0x6A, 0x02, 0x01, 0x17, 0x4D, 0x2D, 0x01, 0x17
COL_STEP = 0x4E                                               # rows 1-2: the steps' background = dim cyan (the user, 2026-10-17; 0x4E steady, 0x4F blinks)
LED_DOWN, LED_UP, LED_HALF = 51, 52, 53                       # the LED task's frame: Octave down / up, 1-16 / 17-32


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_spk() -> r0 = the track 0 / 1 whose picker is on the screen, or 0xFF; clobbers r1-r3
    a.label("c_spk")
    E(push_list, [4], lr=True)
    imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 4, 0); E(cmp_imm, 1, PICK[0]); E(b_cond, "pk_m", "eq")
    E(movs_imm, 4, 1); E(cmp_imm, 1, PICK[1]); E(b_cond, "pk_n", "ne")
    a.label("pk_m"); E(mov_reg, 0, 4); E(bl, L["c_vsmode"]); E(cmp_imm, 0, 0); E(b_cond, "pk_n", "eq")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("pk_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_spst() -> r0 = the state bytes (SC16's block + 14), or 0; clobbers r1, r2
    a.label("c_spst")
    E(push_list, [3], lr=True); E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "ps_x", "eq"); E(adds_imm8, 0, O_ST)
    a.label("ps_x"); E(pop_list, [3], pc=True)

    # ---- c_splb(r0 = track 0 / 1, r1 = step) -> r0 = the address of its lane-8 bytes in the pattern it plays; clobbers r1-r3
    a.label("c_splb")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(adds_imm8, 0, 2); E(bl, L["c_arpat"]); E(movw, 1, PAT_SZ); E(muls, 0, 1); E(mov_reg, 2, 0)            # r2 = pattern x its size
    E(adds_imm8, 4, 2); E(mov_reg, 0, 4); E(bl, L["c_arply"]); E(ldr_imm, 0, 0, 0x48); E(adds_reg, 0, 0, 2)
    imm32(1, LANE); E(adds_reg, 0, 0, 1); E(movs_imm, 1, 6); E(muls, 1, 5); E(adds_reg, 0, 0, 1)
    E(pop_list, [4, 5], pc=True)

    # ---- c_spset(r0 = track, r1 = step, r2 = the sample, or 0xFF = none): 0x80 | the sample (or 0xFF) in the six micro steps; clobbers r0-r3
    a.label("c_spset")
    E(push_list, [4], lr=True); E(mov_reg, 4, 2); E(cmp_imm, 4, 0xFF); E(b_cond, "pt_e", "eq"); E(movs_imm, 3, FLIP); E(orrs_reg, 4, 3)
    a.label("pt_e"); E(bl, "c_splb"); E(movs_imm, 1, 0)
    a.label("pt_l"); E(strb_reg, 4, 0, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, 6); E(b_cond, "pt_l", "lo")
    E(pop_list, [4], pc=True)

    # ---- c_sptp(r0 = store, r1 = parameter) -> r0 = its byte; clobbers r1-r3
    a.label("c_sptp")
    E(push_list, [3], lr=True); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(pop_list, [3], pc=True)

    # ---- c_spnote(r0 = track, r1 = 1 on / 0 off, r2 = velocity): the sample's note through the transmitter (MIDI out + the engine)
    a.label("c_spnote")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 6, 2)
    imm32(3, NOTE_ON_VT); E(cmp_imm, 1, 0); E(b_cond, "pn_o", "ne"); imm32(3, NOTE_OFF_VT); E(movs_imm, 6, 0)
    a.label("pn_o"); E(ldr_imm, 5, 3, 0)
    imm32(0, TX); E(mov_reg, 1, 4); E(adds_imm8, 1, 2); E(movs_imm, 2, ROOT); E(mov_reg, 3, 6); E(raw, h(0x47A8))       # blx r5
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_sprec() -> r0 = 1 while playing with Record armed; clobbers r1-r3
    a.label("c_sprec")
    E(push_list, [3], lr=True); imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, "c_sptp"); E(cmp_imm, 0, 0); E(b_cond, "pr_x", "eq")
    imm32(0, TRANSPORT); E(movs_imm, 1, 1); E(bl, "c_sptp"); E(cmp_imm, 0, 0); E(b_cond, "pr_x", "eq"); E(movs_imm, 0, 1)
    a.label("pr_x"); E(pop_list, [3], pc=True)

    # ---- c_spstep(r0 = track) -> r0 = the step it plays; clobbers r1-r3
    a.label("c_spstep")
    E(push_list, [3], lr=True); E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 1); E(bl, "c_sptp"); E(pop_list, [3], pc=True)

    # ---- c_sppad (the container's slot 0: obj, pad, velocity)
    a.label("c_sppad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, "c_spk"); E(cmp_imm, 0, 0xFF); E(b_cond, "pp_f", "eq"); E(mov_reg, 7, 0)                               # r7 = the track
    E(bl, "c_spst"); E(cmp_imm, 0, 0); E(b_cond, "pp_f", "eq"); E(mov_reg, 6, 0)                                 # r6 = the state
    E(ldr_sp, 5, 4)                                                                                                # r5 = the pad
    E(cmp_imm, 5, 16); E(b_cond, "pp_s", "hs")
    E(ldrb_imm, 4, 6, 0); E(lsrs_imm, 4, 4, 2); E(movs_imm, 0, 1); E(ands_reg, 4, 0); E(lsls_imm, 4, 4, 4); E(adds_reg, 4, 4, 5)   # r4 = the step
    imm32(0, MGR); E(ldr_imm, 0, 0, HELD); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(lsls_imm, 0, 0, 31); E(b_cond, "pp_h", "pl")
    E(mov_reg, 0, 7); E(mov_reg, 1, 4); E(movs_imm, 2, 0xFF); E(bl, "c_spset"); E(b, "pp_x")                     # Clear + step: no flip
    a.label("pp_h"); E(adds_imm8, 5, 1); E(strb_imm, 5, 6, 1); E(b, "pp_x")                                      # the held step + 1
    a.label("pp_s")                                                                                                # a sample: 16 page + pad - 16
    E(ldrb_imm, 4, 6, 0); E(movs_imm, 0, 3); E(ands_reg, 4, 0); E(lsls_imm, 4, 4, 4); E(adds_reg, 4, 4, 5); E(subs_imm8, 4, 16)
    E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, 0); E(b_cond, "pp_sel", "eq")
    E(subs_imm8, 0, 1); E(ldrb_imm, 1, 6, 0); E(lsrs_imm, 1, 1, 2); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(lsls_imm, 1, 1, 4); E(adds_reg, 1, 1, 0)
    E(mov_reg, 0, 7); E(mov_reg, 2, 4); E(bl, "c_spset"); E(b, "pp_snd")                                         # held step + sample: its flip
    a.label("pp_sel")                                                                                              # the track's sample: code 25
    E(mov_reg, 0, 7); E(movs_imm, 1, 25); E(bl, L["c_vvaddr"]); E(strb_imm, 4, 0, 0)
    E(mov_reg, 0, 7); E(movs_imm, 1, 25); E(bl, L["c_vmark"]); E(bl, L["c_vsave"])
    E(bl, "c_sprec"); E(cmp_imm, 0, 0); E(b_cond, "pp_snd", "eq")                                                # recording: the note and its flip
    imm32(0, REC); E(movs_imm, 1, ROOT); E(ldr_sp, 2, 8); E(mov_reg, 3, 7); E(adds_imm8, 3, 2); E(bl, REC_ON)
    E(mov_reg, 0, 7); E(bl, "c_spstep"); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(mov_reg, 2, 4); E(bl, "c_spset")
    a.label("pp_snd")                                                                                              # it sounds: the pending flip, the note
    E(movs_imm, 1, 0xC0); E(orrs_reg, 1, 4); E(mov_reg, 0, 7); E(bl, L["c_vsmpend"])
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(ldr_sp, 2, 8); E(bl, "c_spnote")
    a.label("pp_x"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(raw, RET)
    a.label("pp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_sprel (the container's slot 1: obj, pad)
    a.label("c_sprel")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
    E(bl, "c_spk"); E(cmp_imm, 0, 0xFF); E(b_cond, "rl_f", "eq"); E(mov_reg, 7, 0)
    E(bl, "c_spst"); E(cmp_imm, 0, 0); E(b_cond, "rl_f", "eq"); E(mov_reg, 6, 0)
    E(ldr_sp, 5, 4); E(cmp_imm, 5, 16); E(b_cond, "rl_s", "hs")
    E(ldrb_imm, 0, 6, 1); E(subs_imm8, 0, 1); E(cmp_reg, 0, 5); E(b_cond, "rl_z", "ne"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 1)
    a.label("rl_z"); E(b, "rl_x")
    a.label("rl_s")
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(bl, "c_spnote")
    E(bl, "c_sprec"); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    imm32(0, REC); E(movs_imm, 1, ROOT); E(mov_reg, 2, 7); E(adds_imm8, 2, 2); E(bl, REC_OFF)
    a.label("rl_x"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True)); E(raw, RET)
    a.label("rl_f"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True)); E(b_w, prev["rel"])

    # ---- c_spbtn (the head of the button chain: ctrl, id): Octave = the page, 1-16 / 17-32 = the half
    a.label("c_spbtn")
    E(cmp_imm, 1, ID_DOWN); E(b_cond, "pb_f", "lo"); E(cmp_imm, 1, ID_HALF); E(b_cond, "pb_f", "hi")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pb_p", "ne")
    E(bl, "c_spk"); E(cmp_imm, 0, 0xFF); E(b_cond, "pb_p", "eq")
    E(bl, "c_spst"); E(cmp_imm, 0, 0); E(b_cond, "pb_p", "eq"); E(mov_reg, 4, 0); E(ldrb_imm, 0, 4, 0)
    E(cmp_imm, 5, ID_HALF); E(b_cond, "pb_o", "ne"); E(movs_imm, 1, 4); E(eors_reg, 0, 1); E(b, "pb_w")
    a.label("pb_o"); E(movs_imm, 1, 3); E(ands_reg, 1, 0); E(bics_reg, 0, 1)
    E(cmp_imm, 5, ID_DOWN); E(b_cond, "pb_d", "ne"); E(cmp_imm, 1, 3); E(b_cond, "pb_c", "hs"); E(adds_imm8, 1, 1); E(b, "pb_c")
    a.label("pb_d"); E(cmp_imm, 1, 0); E(b_cond, "pb_c", "eq"); E(subs_imm8, 1, 1)
    a.label("pb_c"); E(orrs_reg, 0, 1)
    a.label("pb_w"); E(strb_imm, 0, 4, 0); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("pb_p"); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("pb_f"); E(b_w, prev["btn"])

    # ---- c_spleds (the container's slot 7: obj -> the LED buffer): the chain; the picker's pads and the Octave buttons
    a.label("c_spleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_spk"); E(cmp_imm, 0, 0xFF); E(b_cond, "pl_x", "eq"); E(mov_reg, 7, 0)
    E(bl, "c_spst"); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq"); E(mov_reg, 6, 0)
    E(movs_imm, 4, 0)
    a.label("pl_st")                                                                                               # the steps
    E(ldrb_imm, 1, 6, 0); E(lsrs_imm, 1, 1, 2); E(movs_imm, 0, 1); E(ands_reg, 1, 0); E(lsls_imm, 1, 1, 4); E(adds_reg, 1, 1, 4)
    E(push_list, [1]); E(mov_reg, 0, 7); E(bl, "c_splb"); E(ldrb_imm, 0, 0, 0); E(pop_list, [1])
    E(movs_imm, 3, COL_STEP); E(cmp_imm, 0, FLIP); E(b_cond, "pl_c1", "lo"); E(cmp_imm, 0, 0xFF); E(b_cond, "pl_c1", "eq"); E(movs_imm, 3, COL_FLIP)
    a.label("pl_c1")
    E(ldrb_imm, 0, 6, 1); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "pl_c2", "ne"); E(movs_imm, 3, COL_HELD); E(b, "pl_w")
    a.label("pl_c2")
    E(push_list, [1, 3]); imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, "c_sptp"); E(pop_list, [1, 3]); E(cmp_imm, 0, 0); E(b_cond, "pl_w", "eq")
    E(push_list, [1, 3]); E(mov_reg, 0, 7); E(bl, "c_spstep"); E(pop_list, [1, 3]); E(cmp_reg, 0, 1); E(b_cond, "pl_w", "ne"); E(movs_imm, 3, COL_PLAY)
    a.label("pl_w"); E(lsls_imm, 0, 4, 1); E(strh_reg, 3, 5, 0)
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "pl_st", "lo")
    E(mov_reg, 0, 7); E(movs_imm, 1, 25); E(bl, L["c_vvaddr"]); E(ldrb_imm, 0, 0, 0); E(mov_reg, 3, 0)          # r3 = the track's sample
    E(ldrb_imm, 0, 6, 1); E(movs_imm, 2, 0xFF); E(cmp_imm, 0, 0); E(b_cond, "pl_nh", "eq")                         # r2 = the held step's flip
    E(push_list, [3]); E(subs_imm8, 0, 1); E(ldrb_imm, 1, 6, 0); E(lsrs_imm, 1, 1, 2); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(lsls_imm, 1, 1, 4)
    E(adds_reg, 1, 1, 0); E(mov_reg, 0, 7); E(bl, "c_splb"); E(ldrb_imm, 2, 0, 0)
    E(cmp_imm, 2, FLIP); E(b_cond, "pl_hn", "lo"); E(cmp_imm, 2, 0xFF); E(b_cond, "pl_hn", "eq"); E(movs_imm, 0, 63); E(ands_reg, 2, 0); E(b, "pl_hp")
    a.label("pl_hn"); E(movs_imm, 2, 0xFF)
    a.label("pl_hp"); E(pop_list, [3])
    a.label("pl_nh")
    E(ldrb_imm, 1, 6, 0); E(movs_imm, 0, 3); E(ands_reg, 1, 0); E(lsls_imm, 1, 1, 4); E(movs_imm, 4, 0)            # r1 = the page's first sample
    a.label("pl_sm")
    E(adds_reg, 0, 1, 4); E(movs_imm, 6, COL_DIM); E(cmp_reg, 0, 2); E(b_cond, "pl_s1", "ne"); E(movs_imm, 6, COL_HF)
    a.label("pl_s1"); E(cmp_reg, 0, 3); E(b_cond, "pl_s2", "ne"); E(movs_imm, 6, COL_SEL)
    a.label("pl_s2"); E(adds_imm8, 4, 16); E(lsls_imm, 0, 4, 1); E(strh_reg, 6, 5, 0); E(subs_imm8, 4, 16)
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "pl_sm", "lo")
    a.label("pl_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_spledtask (the LED task calls: ctrl, frame): the chain; with the picker on the screen Octave down / up lit when there is a next /
    #      previous page, 1-16 / 17-32 green on the second half
    a.label("c_spledtask")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_spk"); E(cmp_imm, 0, 0xFF); E(b_cond, "lt_x", "eq")
    E(bl, "c_spst"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq"); E(ldrb_imm, 4, 0, 0)
    E(movs_imm, 0, 3); E(ands_reg, 0, 4); E(movs_imm, 2, 0); E(cmp_imm, 0, 3); E(b_cond, "lt_d", "hs"); E(movs_imm, 2, COL_BTN)
    a.label("lt_d"); E(movs_imm, 1, 2 * LED_DOWN); E(strh_reg, 2, 5, 1)
    E(movs_imm, 2, 0); E(cmp_imm, 0, 0); E(b_cond, "lt_u", "eq"); E(movs_imm, 2, COL_BTN)
    a.label("lt_u"); E(movs_imm, 1, 2 * LED_UP); E(strh_reg, 2, 5, 1)
    E(movs_imm, 2, COL_DIM); E(lsrs_imm, 0, 4, 3); E(b_cond, "lt_h", "cc"); E(movs_imm, 2, COL_HALF)
    a.label("lt_h"); E(movs_imm, 1, 2 * LED_HALF); E(strh_reg, 2, 5, 1)
    a.label("lt_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_spply (the players' slot 2: this, pattern, step, micro step): a MIDI track in the sample mode: the flip of the notes starting here
    a.label("c_spply")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(bl, L["c_artrk"]); E(subs_imm8, 0, 2); E(cmp_imm, 0, 1); E(b_cond, "py_x", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_vsmode"]); E(cmp_imm, 0, 0); E(b_cond, "py_x", "eq")
    E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x48); E(ldr_sp, 1, 4); E(movw, 2, PAT_SZ); E(muls, 1, 2); E(adds_reg, 0, 0, 1)
    imm32(1, LANE); E(adds_reg, 0, 0, 1); E(ldr_sp, 1, 8); E(movs_imm, 2, 6); E(muls, 1, 2); E(adds_reg, 0, 0, 1); E(ldr_sp, 1, 12); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, FLIP); E(b_cond, "py_n", "lo"); E(cmp_imm, 1, 0xFF); E(b_cond, "py_v", "ne")
    a.label("py_n"); E(movs_imm, 1, 0); E(b, "py_w")
    a.label("py_v"); E(movs_imm, 0, 63); E(ands_reg, 1, 0); E(movs_imm, 0, 0xC0); E(orrs_reg, 1, 0)
    a.label("py_w"); E(mov_reg, 0, 4); E(bl, L["c_vsmpend"])
    a.label("py_x"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["ply"])

    # ---- c_spal1 / c_spal2 (in place of the stock's ldrb.w r2, [r3 / r2, #0x3a8] in the note tracks' lane player 0x0804BA8C / 0x0804BB02, r5 =
    #      the lane, r0-r3 free there): lane 8 (the track's level) with a flip (0x80..0xFE) = nothing for the stock (0xFF); its level automation
    #      (0..127) as before
    a.label("c_spal1"); E(raw, ldrb_w(2, 3, 0x3A8)); E(b, "al_c")
    a.label("c_spal2"); E(raw, ldrb_w(2, 2, 0x3A8))
    a.label("al_c"); E(cmp_imm, 5, 8); E(b_cond, "al_x", "ne"); E(cmp_imm, 2, FLIP); E(b_cond, "al_x", "lo"); E(movs_imm, 2, 0xFF)
    a.label("al_x"); E(raw, RET)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the container's slots 0 / 1 / 7, the head of the button chain, the players' slot 2."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_scst=lab("sc16", "c_scst"), c_shift=lab("sc15", "c_shift"), c_artrk=lab("arp", "c_artrk"), c_arply=lab("arp", "c_arply"), c_arpat=lab("arp", "c_arpat"))
    for n in ("c_vsmode", "c_vsmpend", "c_vvaddr", "c_vmark", "c_vsave"): L[n] = lab("vcf20", n)
    prev = dict(pad=u(CONT_VT) & ~1, rel=u(CONT_VT + 4) & ~1, leds=u(CONT_VT + 28) & ~1, btn=MP.bw_target(img, MP.BTN_ENTRY, BASE),
                ply=u(A.PLAYER_VT + 8) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, CONT_VT - BASE, labels["c_sppad"] | 1)
    struct.pack_into("<I", img, CONT_VT + 4 - BASE, labels["c_sprel"] | 1)
    struct.pack_into("<I", img, CONT_VT + 28 - BASE, labels["c_spleds"] | 1)
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_spbtn"])
    struct.pack_into("<I", img, A.PLAYER_VT + 8 - BASE, labels["c_spply"] | 1)
    for at, rn, lab in LV_READS:
        assert bytes(img[at - BASE:at - BASE + 4]) == ldrb_w(2, rn, 0x3A8), hex(at)
        img[at - BASE:at - BASE + 4] = bl(at, labels[lab])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_spledtask"])
    return labels, code, prev
