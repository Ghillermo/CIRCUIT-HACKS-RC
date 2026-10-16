"""SC42.8 (the user, 2026-10-16): «arpeggiator en drums: mismo comportamiento, pero en vez de saltar entre notas salta entre samples»; of the three
readings offered, «C» = the samples held in the drum's Preset view, as the notes held for the note tracks' arpeggiator.

The stock (read in the firmware, emulated):
  * a drum's Preset view (vtable 0x0805ABBC, [[ctrl + 0x2C] + 0x8C + 4 d]): pad p = sample p + 32 x the page ([view + 0x20] p0); a press sets the
    drum's sample through [view + 0xC] (slot 0: (obj, the sample parameter's id [view + 0x24], sample)), stops what it sounded (0x0804E0E8) and plays
    it (0x0804E0BA(view, pad, velocity): [view + 0x10] note-on); [view + 0x2C] = the drum's selected sample (the same store as the player's
    [+ 0x5C]), [view + 0x3C] p0 = the pad held; [view + 0x51] bit 0 = the chromatic view (SC08);
  * the drum players (0x20040810 + 0x90 d): slot 4 (0x080411CA) sets the sample of the step's first hit (its sample flip, or the selected one)
    through [this + 0x50] (the same class: (obj, [[this + 0x54] + 8], sample)); slot 2 = every micro step (rollers' c_rlplay in front); the hit is
    [this + 0x4C]'s note-on (note [this + 0x58]; [this + 0x59] = sounding).

Ours:
  * the setting: a byte per drum and pattern (bit 7 on, bits 0-2 the order as the note arpeggiator's, bits 3-6 the resolution: 0 the drum's sync
    rate, 1..8 = 1/32T .. 1/4) in the record's tail + 600 ("AD", a check byte, 32 bytes from + 604: saved with the project; free in the builds without
    stutdiag); the drum's Pattern Settings view, Shift held: pad 25 on / off, pads 27-32 the order, pads 17-24 the resolution (the same again = the
    drum's); their LEDs as the note tracks' (the chosen ones green, pad 25 green while on);
  * the input: in the Preset view of a drum whose playing pattern has it on (no Shift / Clear / Duplicate, not the chromatic view), the first sample
    pad held is the stock's; a second one held with it is not the stock's (no selection, no sound) and starts the arpeggio of the samples held,
    sorted, in the chosen order (the note arpeggiator's c_arord): each step sets the drum's sample through the player's [+ 0x50] and hits through
    its interface (the pad's velocity), like a sample flip; while playing on the drum's grid of micro steps (the player's slot 2), stopped from the
    LED task at the project's tempo; it goes on while any sample is held; at the end the drum's selected sample again; not recorded (SC42.9, use_rec:
    recorded while playing with Record);
  * the running state (tail + 636..663, RAM): n, a magic, the drum, k / group / place (c_arord's), 6 samples, 6 velocities, the stock's first
    sample, flags, the next time (ms), the time the view was last drawn (no view for 200 ms: stopped).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm,  # noqa: E402
                   ldrb_reg, ldrh_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, str_sp,
                   strb_imm, strb_reg, strh_reg, subs_imm8, subs_reg, tst_reg)
from build_sc14 import udiv  # noqa: E402

MGR = 0x20040B10
DPV_VT = 0x0805ABBC                                      # the drums' Preset view
PS_VT = 0x0805AB4C                                       # the Pattern Settings view
DP_VT, DP0, DP_SZ = 0x0805B72C, 0x20040810, 0x90
SEL_STORE = 0x20040DB8 + 0x188                           # the selected track (4..7 = the drums)
ENG = 0x20038EC0                                         # + 0x30 + 4 t: what track t plays (p0 the pattern)
TRANSPORT, TEMPO, HAL_TICK = 0x20011034, 0x20011404, 0x2000081C
PARAM_GET = 0x0803542C
TICKS_TAB = 0x0805B8B8
SESSION_OBJ, TAIL, O_BLK, O_ST = 0x2003D71C, 0x27024, 600, 636
MAGIC = 0xD7
PS_PAD_RATE, PS_PAD_ARP, PS_PAD_ORD = 16, 24, 26
ORD_OF_PAD = (4, 5, 0, 1, 2, 3)                          # pads 27-32: fractal, deconstructed, up, down, ping-pong, random (the note arpeggiator's)
COL_ON = 0x17
SEEN_MS = 200
# the running state
S_N, S_MAG, S_DRUM, S_K, S_FG, S_FP, S_SMP, S_VEL, S_FIRST, S_FL, S_NEXT, S_SEEN = 0, 1, 2, 3, 4, 5, 6, 12, 18, 19, 20, 24


NOTEOFF = False                                          # SC43.1 (use_noteoff)


def use_noteoff():
    """SC43.1: each hit leaves its note-off to rollers' c_rloffset / c_rlsweep (rollers.use_noteoff): stopped, the last hit of an arpeggio never got
    one (the drum's boxes of the Note view stayed white, its MIDI note hung)."""
    global NOTEOFF
    NOTEOFF = True


REC = False                                              # SC42.9 (use_rec)
SYNC = False                                             # SC43 (use_sync)


def use_sync():
    """SC43: the recorded hits also go into the drum's edit store (drumstore.py), or the stock's next commit put the old arrays back."""
    global SYNC
    assert REC
    SYNC = True


def use_rec():
    """SC42.9 (the user, 2026-10-16: «sí, graba los samples con record»): playing with Record (not in the count-in), each hit of the arpeggio is
    written into the drum's pattern: the micro step's bit, the sample as the step's sample flip (one a step: the last one wins), and on an empty
    step its velocity and probability 7."""
    global REC
    REC = True


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def mls_(rd, rn, rm, ra): return h(0xFB00 | rn) + h(ra << 12 | rd << 8 | 0x10 | rm)      # rd = ra - rn * rm


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    zc = [0]
    INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi"}
    def bc(target, cond):
        zc[0] += 1; n = f"_d{zc[0]}"; E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    RET = h(0x4770)
    E(raw, bytes(ORD_OF_PAD) + bytes([PS_PAD_ORD + ORD_OF_PAD.index(m) for m in range(6)])); t_ord = base

    # ---- c_datail() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_datail")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "tl_x", "eq"); imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("tl_x"); E(raw, RET)

    # ---- c_dasum(r0 = the block) -> r1 = the check byte of its 32 settings; clobbers r2, r3
    a.label("c_dasum")
    E(movs_imm, 1, 0x5A); E(movs_imm, 3, 0)
    a.label("su_l"); E(adds_reg, 2, 0, 3); E(ldrb_imm, 2, 2, 4); E(eors_reg, 1, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, 32); E(b_cond, "su_l", "lo")
    E(raw, RET)

    # ---- c_dablk() -> r0 = our block when valid, else 0; clobbers r1-r3
    a.label("c_dablk")
    E(push_list, [4], lr=True)
    E(bl, "c_datail"); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq"); imm32(1, O_BLK); E(adds_reg, 4, 0, 1)
    E(ldrb_imm, 0, 4, 0); E(cmp_imm, 0, 0x41); E(b_cond, "bk_0", "ne"); E(ldrb_imm, 0, 4, 1); E(cmp_imm, 0, 0x44); E(b_cond, "bk_0", "ne")
    E(mov_reg, 0, 4); E(bl, "c_dasum"); E(ldrb_imm, 2, 4, 2); E(cmp_reg, 1, 2); E(b_cond, "bk_0", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("bk_0"); E(movs_imm, 0, 0)
    a.label("bk_x"); E(pop_list, [4], pc=True)

    # ---- c_dacfg(r0 = drum 0..3, r1 = pattern) -> r0 = the setting (0 = off); clobbers r1-r3
    a.label("c_dacfg")
    E(push_list, [4], lr=True)
    E(cmp_imm, 0, 3); E(b_cond, "cf_0", "hi"); E(cmp_imm, 1, 7); E(b_cond, "cf_0", "hi")
    E(lsls_imm, 4, 0, 3); E(adds_reg, 4, 4, 1)
    E(bl, "c_dablk"); E(cmp_imm, 0, 0); E(b_cond, "cf_x", "eq")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 4); E(pop_list, [4], pc=True)
    a.label("cf_0"); E(movs_imm, 0, 0)
    a.label("cf_x"); E(pop_list, [4], pc=True)

    # ---- c_daset(r0 = drum, r1 = pattern, r2 = setting): the block made when missing; clobbers r0-r3
    a.label("c_daset")
    E(push_list, [4, 5, 6], lr=True)
    E(lsls_imm, 4, 0, 3); E(adds_reg, 4, 4, 1); E(mov_reg, 5, 2)
    E(bl, "c_dablk"); E(cmp_imm, 0, 0); E(b_cond, "st_w", "ne")
    E(bl, "c_datail"); E(cmp_imm, 0, 0); E(b_cond, "st_x", "eq"); imm32(1, O_BLK); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 0x41); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0x44); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(movs_imm, 2, 36)
    a.label("st_z"); E(subs_imm8, 2, 1); E(strb_reg, 1, 0, 2); E(cmp_imm, 2, 3); E(b_cond, "st_z", "hi")
    a.label("st_w"); E(mov_reg, 6, 0); E(adds_reg, 0, 0, 4); E(strb_imm, 5, 0, 4)
    E(mov_reg, 0, 6); E(bl, "c_dasum"); E(strb_imm, 1, 6, 2)
    a.label("st_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dast() -> r0 = the running state (valid), or 0; c_daini(r0 = drum) -> r0 = the state, emptied for that drum; clobber r1, r2
    a.label("c_dast")
    E(raw, h(0xB500)); E(bl, "c_datail"); E(cmp_imm, 0, 0); E(b_cond, "ds_x", "eq"); imm32(1, O_ST); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, S_MAG); E(cmp_imm, 1, MAGIC); E(b_cond, "ds_x", "eq"); E(movs_imm, 0, 0)
    a.label("ds_x"); E(raw, h(0xBD00))
    a.label("c_daini")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_datail"); E(cmp_imm, 0, 0); E(b_cond, "di_x", "eq"); imm32(1, O_ST); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 0); E(movs_imm, 2, 28)
    a.label("di_z"); E(subs_imm8, 2, 1); E(strb_reg, 1, 0, 2); E(cmp_imm, 2, 0); E(b_cond, "di_z", "ne")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, S_MAG); E(strb_imm, 4, 0, S_DRUM); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, S_FIRST)
    a.label("di_x"); E(pop_list, [4], pc=True)

    # ---- c_dadrum(r0 = a view) -> r0 = 0..3 when it is a drum's Preset view, else 0xFF; clobbers r1, r2
    a.label("c_dadrum")
    imm32(1, MGR); E(ldr_imm, 1, 1, 0x2C); E(cmp_imm, 1, 0); E(b_cond, "dd_n", "eq"); E(adds_imm8, 1, 0x8C); E(movs_imm, 2, 0)
    a.label("dd_l"); E(ldr_imm, 3, 1, 0); E(cmp_reg, 3, 0); E(b_cond, "dd_f", "eq"); E(adds_imm8, 1, 4); E(adds_imm8, 2, 1); E(cmp_imm, 2, 4); E(b_cond, "dd_l", "lo")
    a.label("dd_n"); E(movs_imm, 0, 0xFF); E(raw, RET)
    a.label("dd_f"); E(mov_reg, 0, 2); E(raw, RET)

    # ---- c_dapat(r0 = drum) -> r0 = the pattern it plays; clobbers r1-r3
    a.label("c_dapat")
    E(raw, h(0xB500)); E(adds_imm8, 0, 4); E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(raw, h(0xBD00))

    # ---- c_dati(r0 = drum) -> r0 = the ticks of an arpeggio step (its resolution, or the drum's sync rate); c_datps(r0 = drum) -> r0 = its ticks a step
    a.label("c_datps")
    E(raw, h(0xB500)); E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x10)
    E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 7); E(b_cond, "tp_a", "ls"); E(movs_imm, 0, 3)
    a.label("tp_a"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(raw, h(0xBD00))
    a.label("c_dati")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_dapat"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_dacfg")
    E(lsrs_imm, 0, 0, 3); E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "ti_f", "eq"); E(cmp_imm, 0, 8); E(b_cond, "ti_f", "hi")
    E(subs_imm8, 0, 1); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(pop_list, [4], pc=True)
    a.label("ti_f"); E(mov_reg, 0, 4); E(bl, "c_datps"); E(pop_list, [4], pc=True)

    # ---- c_dasmp(r0 = drum, r1 = sample): the drum's sample through its player's setter (as the stock's sample flip); clobbers r0-r3
    a.label("c_dasmp")
    E(push_list, [4], lr=True)
    E(mov_reg, 2, 1); E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0); E(adds_reg, 4, 0, 1)
    E(ldr_imm, 0, 4, 0x50); E(ldr_imm, 1, 4, 0x54); E(ldrb_imm, 1, 1, 8); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0); E(raw, h(0x4798))   # blx r3
    E(pop_list, [4], pc=True)

    # ---- c_dahit(r0 = drum, r1 = velocity): a hit through its player's interface (off first if it sounds); clobbers r0-r3
    a.label("c_dahit")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 6, 1); E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0); E(adds_reg, 4, 0, 1)
    E(movw, 1, 0x59); E(ldrb_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "dh_on", "eq")
    E(ldr_imm, 0, 4, 0x4C); E(movs_imm, 1, 0x58); E(ldrb_reg, 1, 4, 1); E(movs_imm, 2, 0); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(raw, h(0x4798))
    a.label("dh_on")
    E(ldr_imm, 0, 4, 0x4C); E(movs_imm, 1, 0x58); E(ldrb_reg, 1, 4, 1); E(mov_reg, 2, 6); E(movs_imm, 3, 0); E(ldr_imm, 5, 0, 0); E(ldr_imm, 5, 5, 0); E(raw, h(0x47A8))
    E(movs_imm, 0, 1); E(movs_imm, 1, 0x59); E(strb_reg, 0, 4, 1)
    if NOTEOFF: E(mov_reg, 0, 4); E(bl, L["c_rloffset"])
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dafire(r0 = the state): the next sample of the order on the drum
    a.label("c_dafire")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); E(b_cond, "fi_x", "eq")
    E(ldrb_imm, 0, 4, S_DRUM); E(bl, "c_dapat"); E(mov_reg, 1, 0); E(ldrb_imm, 0, 4, S_DRUM); E(bl, "c_dacfg"); E(movs_imm, 1, 7); E(ands_reg, 1, 0)
    E(mov_reg, 0, 4); E(bl, L["c_arord"]); E(adds_reg, 0, 0, 4); E(ldrb_imm, 5, 0, S_SMP); E(ldrb_imm, 6, 0, S_VEL)
    E(ldrb_imm, 0, 4, S_DRUM); E(mov_reg, 1, 5); E(bl, "c_dasmp")
    E(ldrb_imm, 0, 4, S_DRUM); E(mov_reg, 1, 6); E(bl, "c_dahit")
    if REC: E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(pop_list, [4, 5, 6], pc=True)            # (REC) r0 = the sample, r1 = the velocity
    a.label("fi_x")
    if REC: E(movs_imm, 0, 0xFF)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_daend(r0 = the state): the arpeggio stops: the drum's selected sample again; clobbers r0-r3
    a.label("c_daend")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "en_z", "pl")
    E(ldrb_imm, 0, 4, S_DRUM); E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x5C)
    E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0xFF); E(b_cond, "en_z", "eq")
    E(ldrb_imm, 0, 4, S_DRUM); E(bl, "c_dasmp")
    a.label("en_z"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, S_FL); E(strb_imm, 0, 4, S_N)
    E(pop_list, [4, 5], pc=True)

    # ---- c_dains(r0 = state, r1 = sample, r2 = velocity) / c_dadel(r0 = state, r1 = sample) -> r0 = 1 when it was there: the sorted list (6 at most)
    a.label("c_dains")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(ldrb_imm, 5, 4, S_N); E(movs_imm, 3, 0)
    a.label("in_f"); E(cmp_reg, 3, 5); E(b_cond, "in_p", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_SMP); E(cmp_reg, 6, 1); E(b_cond, "in_p", "hs"); E(adds_imm8, 3, 1); E(b, "in_f")
    a.label("in_p")
    E(cmp_reg, 3, 5); E(b_cond, "in_n", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_SMP); E(cmp_reg, 6, 1); E(b_cond, "in_n", "ne")
    E(strb_imm, 2, 0, S_VEL); E(b, "in_x")                                                # already there: its velocity
    a.label("in_n"); E(cmp_imm, 5, 6); E(b_cond, "in_x", "hs")
    E(mov_reg, 7, 5)
    a.label("in_s"); E(cmp_reg, 7, 3); E(b_cond, "in_w", "ls")
    E(adds_reg, 0, 4, 7); E(subs_imm8, 0, 1); E(ldrb_imm, 6, 0, S_SMP); E(strb_imm, 6, 0, S_SMP + 1); E(ldrb_imm, 6, 0, S_VEL); E(strb_imm, 6, 0, S_VEL + 1)
    E(subs_imm8, 7, 1); E(b, "in_s")
    a.label("in_w"); E(adds_reg, 0, 4, 3); E(strb_imm, 1, 0, S_SMP); E(strb_imm, 2, 0, S_VEL); E(adds_imm8, 5, 1); E(strb_imm, 5, 4, S_N)
    a.label("in_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("c_dadel")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(ldrb_imm, 5, 4, S_N); E(movs_imm, 3, 0)
    a.label("de_f"); E(cmp_reg, 3, 5); E(b_cond, "de_0", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_SMP); E(cmp_reg, 6, 1); E(b_cond, "de_m", "eq")
    E(adds_imm8, 3, 1); E(b, "de_f")
    a.label("de_m"); E(subs_imm8, 5, 1); E(strb_imm, 5, 4, S_N)
    a.label("de_s"); E(cmp_reg, 3, 5); E(b_cond, "de_1", "hs")
    E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_SMP + 1); E(strb_imm, 6, 0, S_SMP); E(ldrb_imm, 6, 0, S_VEL + 1); E(strb_imm, 6, 0, S_VEL)
    E(adds_imm8, 3, 1); E(b, "de_s")
    a.label("de_1"); E(movs_imm, 0, 1); E(pop_list, [4, 5, 6], pc=True)
    a.label("de_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dasample(r0 = view, r1 = pad) -> r0 = the sample of the pad (pad + 32 x the page); clobbers r1-r3
    a.label("c_dasample")
    E(push_list, [4], lr=True); E(mov_reg, 4, 1)
    E(ldr_imm, 0, 0, 0x20); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(lsls_imm, 0, 0, 5); E(adds_reg, 0, 0, 4)
    E(pop_list, [4], pc=True)

    # ---- c_daok(r0 = view) -> r0 = the drum when the arpeggio may take a press there (a drum's Preset view, no Shift / Clear / Duplicate, not
    #      the chromatic view, its playing pattern's arpeggiator on), else 0xFF; clobbers r1-r3
    a.label("c_daok")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 5, 0); E(bl, "c_dadrum"); E(cmp_imm, 0, 3); bc("ok_n", "hi"); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0x51); E(ldrb_reg, 0, 5, 1); E(lsls_imm, 0, 0, 31); bc("ok_n", "mi")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("ok_n", "ne")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 3); E(tst_reg, 0, 1); bc("ok_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_dapat"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_dacfg"); E(lsls_imm, 0, 0, 24); bc("ok_n", "pl")
    E(mov_reg, 0, 4); E(pop_list, [4, 5], pc=True)
    a.label("ok_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5], pc=True)

    # ---- c_dapad (the drums' Preset view slot 0: view, pad, velocity)
    a.label("c_dapad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 1, 32); bc("pd_s", "hs")
    E(bl, "c_daok"); E(cmp_imm, 0, 3); bc("pd_s", "hi"); E(mov_reg, 7, 0)                  # r7 = the drum
    E(bl, "c_dast"); E(cmp_imm, 0, 0); E(b_cond, "pd_i", "eq"); E(ldrb_imm, 1, 0, S_DRUM); E(cmp_reg, 1, 7); E(b_cond, "pd_g", "eq")
    E(bl, "c_daend")                                                                        # another drum's: over
    a.label("pd_i"); E(mov_reg, 0, 7); E(bl, "c_daini"); E(cmp_imm, 0, 0); bc("pd_s", "eq")
    a.label("pd_g"); E(mov_reg, 4, 0)                                                       # r4 = the state
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, "c_dasample"); E(mov_reg, 5, 0)                # r5 = the sample
    E(ldrb_imm, 6, 4, S_N)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(ldr_sp, 2, 8); E(bl, "c_dains")
    E(cmp_imm, 6, 0); E(b_cond, "pd_2", "ne")
    E(strb_imm, 5, 4, S_FIRST); E(b, "pd_s")                                                # the first: the stock's
    a.label("pd_2")
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 1, 0, 31); E(b_cond, "pd_t", "mi")
    E(movs_imm, 1, 1); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, S_FL)                           # it starts: the order from its start, the clock now
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, S_K); E(strb_imm, 0, 4, S_FG); E(strb_imm, 0, 4, S_FP)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 4, S_NEXT)
    a.label("pd_t"); E(raw, h(0xB003)); E(pop_list, [4, 5, 6, 7], pc=True)                   # add sp, #12: taken
    a.label("pd_s"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_darel (that view's slot 1: view, pad): a sample of the arpeggio let go; the stock's first one to the stock
    a.label("c_darel")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(cmp_imm, 1, 32); bc("rl_s", "hs")
    E(bl, "c_dadrum"); E(cmp_imm, 0, 3); bc("rl_s", "hi"); E(mov_reg, 5, 0)
    E(bl, "c_dast"); E(cmp_imm, 0, 0); bc("rl_s", "eq"); E(mov_reg, 4, 0); E(ldrb_imm, 1, 4, S_DRUM); E(cmp_reg, 1, 5); bc("rl_s", "ne")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, "c_dasample"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_dadel"); E(cmp_imm, 0, 0); bc("rl_s", "eq")
    E(ldrb_imm, 0, 4, S_FIRST); E(cmp_reg, 0, 5); bc("rl_t", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S_FIRST)                                        # the stock's own pad: its release (the selection), then the end
    E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); bc("rl_s", "ne")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, prev["rel"]); E(mov_reg, 0, 4); E(bl, "c_daend")
    E(raw, h(0xB002)); E(pop_list, [4, 5], pc=True)
    a.label("rl_t")
    E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); E(b_cond, "rl_k", "ne"); E(mov_reg, 0, 4); E(bl, "c_daend")
    a.label("rl_k"); E(raw, h(0xB002)); E(pop_list, [4, 5], pc=True)                         # add sp, #8
    a.label("rl_s"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["rel"])

    # ---- c_daleds (that view's slot 7: view) -> its LEDs; the stamp of the arpeggio's view
    a.label("c_daleds")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_dadrum"); E(mov_reg, 4, 0)
    E(bl, "c_dast"); E(cmp_imm, 0, 0); E(b_cond, "dl_x", "eq"); E(ldrb_imm, 1, 0, S_DRUM); E(cmp_reg, 1, 4); E(b_cond, "dl_x", "ne")
    imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, S_SEEN)
    a.label("dl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)

    # ---- c_daplay (the drum players' slot 2: this, pattern, step, micro step): the chain, then the arpeggio on the drum's grid
    a.label("c_daplay")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    E(bl, prev["play"])
    E(bl, "c_dast"); E(cmp_imm, 0, 0); bc("dp_x", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); bc("dp_x", "pl")
    E(ldrb_imm, 5, 4, S_DRUM); E(movs_imm, 0, DP_SZ); E(muls, 0, 5); imm32(1, DP0); E(adds_reg, 0, 0, 1); E(ldr_sp, 1, 0); E(cmp_reg, 0, 1); bc("dp_x", "ne")
    # due when ((6 step + micro) x tps) mod (6 x the arpeggio's ticks) = 0
    E(mov_reg, 0, 5); E(bl, "c_datps"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 5); E(bl, "c_dati"); E(movs_imm, 1, 6); E(muls, 1, 0)                     # r1 = 6 x the arpeggio's ticks
    E(ldr_sp, 0, 8); E(movs_imm, 2, 6); E(muls, 0, 2); E(ldr_sp, 2, 12); E(adds_reg, 0, 0, 2); E(muls, 0, 6)
    E(raw, udiv(2, 0, 1)); E(raw, mls_(0, 2, 1, 0)); E(cmp_imm, 0, 0); bc("dp_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_dafire")
    if REC:                                                                                 # recording: into the pattern
        E(cmp_imm, 0, 0xFF); bc("dp_x", "eq"); E(mov_reg, 6, 0); E(mov_reg, 7, 1)
        for k, want in ((1, "ne"), (2, "eq")):
            imm32(0, TRANSPORT); E(movs_imm, 1, k); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("dp_x", "eq" if want == "ne" else "ne")
        E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x48); E(ldr_sp, 1, 4); E(movw, 2, 0x6A8); E(muls, 1, 2); E(adds_reg, 0, 0, 1)
        E(ldr_sp, 1, 8); E(adds_reg, 0, 0, 1)                                                # r0 = the step's velocity byte
        E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "dp_v", "ne"); E(strb_imm, 7, 0, 0); E(movs_imm, 1, 7); E(movs_imm, 2, 0x20); E(strb_reg, 1, 0, 2)
        a.label("dp_v")
        E(movs_imm, 1, 0x40); E(strb_reg, 6, 0, 1)                                          # the sample flip
        E(adds_imm8, 0, 0x60); E(ldrb_imm, 1, 0, 0); E(ldr_sp, 2, 12); E(movs_imm, 3, 1); E(raw, h(0x4093)); E(orrs_reg, 1, 3); E(strb_imm, 1, 0, 0)   # lsls r3, r2
        if SYNC:
            E(ldr_sp, 0, 0); E(ldr_imm, 2, 0, 0x48); E(ldr_sp, 1, 4); E(movw, 3, 0x6A8); E(muls, 1, 3); E(adds_reg, 2, 2, 1); E(ldr_sp, 1, 8); E(bl, "c_dasync")
    a.label("dp_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_daledtask (the LED task calls: ctrl, frame): the chain; the view gone for 200 ms = over; stopped: the arpeggio at the project's tempo
    a.label("c_daledtask")
    E(push_list, [3, 4, 5, 6], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_dast"); E(cmp_imm, 0, 0); bc("lt_x", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); bc("lt_x", "eq")
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0); E(ldr_imm, 1, 4, S_SEEN); E(subs_reg, 0, 5, 1); imm32(1, SEEN_MS); E(cmp_reg, 0, 1); E(b_cond, "lt_v", "ls")
    E(mov_reg, 0, 4); E(bl, "c_daend"); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S_FIRST); E(b, "lt_x")
    a.label("lt_v")
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); bc("lt_x", "pl")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("lt_x", "ne")
    E(ldr_imm, 1, 4, S_NEXT); E(subs_reg, 0, 5, 1); bc("lt_x", "mi")
    E(mov_reg, 0, 4); E(bl, "c_dafire")
    E(ldrb_imm, 0, 4, S_DRUM); E(bl, "c_dati"); E(mov_reg, 6, 0)                              # the next time: + 2500 ticks / BPM ms
    imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 30); E(b_cond, "lt_b", "hs"); E(movs_imm, 1, 120)
    a.label("lt_b"); imm32(0, 2500); E(muls, 0, 6); E(raw, udiv(0, 0, 1))
    E(ldr_imm, 1, 4, S_NEXT); E(adds_reg, 1, 1, 0); E(subs_reg, 2, 5, 1); E(b_cond, "lt_w", "mi"); E(adds_reg, 1, 5, 0)   # still behind: from now
    a.label("lt_w"); E(str_imm, 1, 4, S_NEXT)
    a.label("lt_x"); E(pop_list, [3, 4, 5, 6], pc=True)

    # ---- c_dapspad (the Pattern Settings view slot 0: view, pad, velocity): a drum track, Shift: pads 17-24 / 25 / 27-32
    a.label("c_dapspad")
    E(cmp_imm, 1, PS_PAD_RATE); E(b_cond, "pp_f", "lo"); E(cmp_imm, 1, 31); E(b_cond, "pp_f", "hi"); E(cmp_imm, 1, PS_PAD_ARP + 1); E(b_cond, "pp_f", "eq")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 6, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "eq")
    E(bl, L["c_pmtp"]); E(subs_imm8, 0, 4); E(cmp_imm, 0, 3); E(b_cond, "pp_p", "hi")      # r0 = the drum, r1 = its pattern
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_dacfg")
    E(cmp_imm, 6, PS_PAD_ARP); E(b_cond, "pp_k", "hs")
    E(subs_imm8, 6, PS_PAD_RATE - 1); E(lsrs_imm, 1, 0, 3); E(movs_imm, 2, 15); E(ands_reg, 1, 2); E(cmp_reg, 1, 6); E(b_cond, "pp_rs", "ne")
    E(movs_imm, 6, 0)
    a.label("pp_rs"); E(movs_imm, 1, 0x78); E(bics_reg, 0, 1); E(lsls_imm, 6, 6, 3); E(orrs_reg, 0, 6); E(b, "pp_w")
    a.label("pp_k"); E(cmp_imm, 6, PS_PAD_ARP); E(b_cond, "pp_o", "ne")
    E(movs_imm, 1, 0x80); E(eors_reg, 0, 1); E(b, "pp_w")
    a.label("pp_o")
    E(movs_imm, 1, 0xF8); E(ands_reg, 0, 1); E(subs_imm8, 6, PS_PAD_ORD); imm32(2, t_ord); E(ldrb_reg, 2, 2, 6); E(orrs_reg, 0, 2)
    a.label("pp_w"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_daset")
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("pp_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True))
    a.label("pp_f"); E(b_w, prev["pspad"])

    # ---- c_dapsbuf (that view's LED buffer getter): the chain; a drum track: pad 25 green while on; with Shift the chosen order / resolution green
    a.label("c_dapsbuf")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["psbuf"]); E(mov_reg, 5, 0)
    E(bl, L["c_pmtp"]); E(subs_imm8, 0, 4); E(cmp_imm, 0, 3); bc("pb_x", "hi")
    E(bl, "c_dacfg"); E(mov_reg, 4, 0)
    E(movs_imm, 1, COL_ON); E(lsls_imm, 0, 4, 24); E(b_cond, "pb_a", "pl"); E(movs_imm, 0, 2 * PS_PAD_ARP); E(strh_reg, 1, 5, 0)
    a.label("pb_a")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("pb_x", "eq")
    E(movs_imm, 0, 7); E(ands_reg, 0, 4); imm32(2, t_ord + 6); E(ldrb_reg, 0, 2, 0); E(lsls_imm, 0, 0, 1); E(movs_imm, 1, COL_ON); E(strh_reg, 1, 5, 0)
    E(lsrs_imm, 0, 4, 3); E(movs_imm, 2, 15); E(ands_reg, 0, 2); E(cmp_imm, 0, 0); E(b_cond, "pb_x", "eq"); E(cmp_imm, 0, 8); E(b_cond, "pb_x", "hi")
    E(adds_imm8, 0, PS_PAD_RATE - 1); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    a.label("pb_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    if SYNC:
        import drumstore
        drumstore.emit_sync(a, "c_dasync")
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the drums' Preset view slots 0 / 1 / 7, the Pattern Settings view slots 0 / 7, the drum players' slot 2, the LED task calls."""
    import ct_fw
    import packio as PK, fxdiag as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_arord=lab("arp", "c_arord"), c_shift=lab("sc15", "c_shift"), c_pmtp=lab("playmode", "c_pmtp"))
    if NOTEOFF: L["c_rloffset"] = lab("rollers", "c_rloffset")
    prev = dict(pad=u(DPV_VT) & ~1, rel=u(DPV_VT + 4) & ~1, leds=u(DPV_VT + 28) & ~1, pspad=u(PS_VT) & ~1, psbuf=u(PS_VT + 28) & ~1,
                play=u(DP_VT + 8) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["play"] == lab("rollers", "c_rlplay"), hex(prev["play"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for vt, k, nm in ((DPV_VT, 0, "c_dapad"), (DPV_VT, 1, "c_darel"), (DPV_VT, 7, "c_daleds"), (PS_VT, 0, "c_dapspad"), (PS_VT, 7, "c_dapsbuf"), (DP_VT, 2, "c_daplay")):
        struct.pack_into("<I", img, vt + 4 * k - BASE, labels[nm] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_daledtask"])
    return labels, code, prev
