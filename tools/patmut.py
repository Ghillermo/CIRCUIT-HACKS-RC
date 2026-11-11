"""SC55.8 / Beta 5.43: the pattern mutate, ported from mefisme's Rhythm Plus (https://github.com/mefisme/rhythm-plus, MIT, commit 7fb8ddd,
modules/mutset.py; credit mefisme) with the user's design for it (RYTHM docs/DISENO_RH86.md, 2026-11-10).

What it does: in the Patterns view (or the Mixer), Shift + a Duplicate tap gives each selected track a short list of patterns taken from its current
chain, in a random order, that loops in place of the chain; the patterns themselves never change.

  * the list = f(seed, track, settings, the chain): made again whenever one of them changes (a setting back to its value = the list back; a chain
    changed while playing = the same seed over the new chain), cached in RAM;
  * Shift + Duplicate tap (Patterns view, Mixer: the stock does nothing there) = a new seed, a list for every selected track; held 1/3 s in the
    Patterns view = the settings page; Clear + Duplicate (any view) = every list ends; a pattern pad of a track (no Clear / Duplicate held) ends
    that track's list (the stock's press then does its job);
  * the settings page (one page, peach: the chosen value bright, the others dim): column 1 Length 1-4, column 2 Length 5-8, column 3 Length type
    (as the chain / exact / random 1..Length), column 4 Amount (all / most / some / a little: how many of the chain's slots change), column 5
    Repeats (on / off: two neighbours never the same), column 6 Keep slot 1 (off / on: slot 1 = the chain's first); the track buttons bright =
    selected (a track switched on while lists play gets its own, off = its list ends); Duplicate closes it, any other view or button too (not
    Record, Play, Clear);
  * the Patterns view, closed: in the column of a track with a list, the pads of the patterns not in its list are dark (the playing one keeps the
    stock's colour); Shift held: Duplicate yellow (Patterns view and Mixer);
  * patchain: a track with a list plays it, the others follow the chain rules (one hook: c_pmnext in front of c_pcnext at 0x0802CD4A);
  * saved: the project's record tail + 367..375 (a mark, the tracks with a list, the tracks not selected, the seed, the settings, a check: the
    bytes are zero in the card's sessions but the Shadow Child pack's garbage); each scene's spare bytes 34..39 (zero in all 173 sessions; the stock's scene save writes byte 33): the
    tracks with a list, the seed, the settings, a check; the scene save / copy write them, a scene starting (playing) or picked while stopped puts
    them back (a scene without them: no lists).
RAM modmx.MXR + 0x22C0..0x22FF (64 B, after flipview's), signature "PMU1"."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm,  # noqa: E402
                   ldr_sp, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg,
                   pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strb_w, strh_imm, subs_imm3, subs_imm8, subs_reg, sub_sp_imm, add_sp_imm, tst_reg, str_sp)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import patchain as PC  # noqa: E402
import mpatch as MP  # noqa: E402
import janko as JK  # noqa: E402

RAM = MX.MXR + 0x22C0
SIG = struct.unpack("<I", b"PMU1")[0]
R_FL, R_T0, R_STAMP, R_KEY, R_POS, R_LIST = 4, 8, 12, 16, 24, 32
FL_OPEN, FL_PEND = 1, 2
TAIL_OFF = PC.TAIL + 367
B_MARK, B_ACT, B_OFF, B_SEED, B_S0, B_S1, B_CHK, MARK = 0, 1, 2, 3, 5, 6, 7, 0xB7
SC_BASE, SC_LEN, SC_SAVED, SC_OFF, SC_CHK = 0x40, 40, 32, 34, 0xA5      # a scene: rec + 0x40 + 40 s; byte 32 = saved (the stock's save writes 33 too); ours 34..39
HOLD_MS = 333
ID_CLEAR, ID_DUP, ID_REC, ID_PLAY, ID_SHIFT = 23, 24, 16, 17, 27
LED_DUP, LED_TRK = 56, 32
C_ON, C_DIM, C_SHIFT = 0x6A, 0x6B, 0x2D                     # peach bright / dim (the chain scenes' peach), the Shift yellow
CHAINS = PC.ENG + 0x9C                                      # PARAM_GET([ENG + 0x9C], t) -> first, last
PLAYING = PC.ENG + 0x30                                     # [ENG + 0x30 + 4 t] item 0 = the pattern playing
LCG_A, LCG_C, MIX = 1664525, 1013904223, 0x9E3779B1
NREP = 16
CPSID, CPSIE, RET = h(0xB672), h(0xB662), h(0x4770)
popw, POP_LR = PC.popw, PC.POP_LR
ldrb_sp, strb_sp = PC.ldrb_sp, PC.strb_sp
INV = dict(PC.INV, cs="cc", cc="cs")
AMT8 = False                # (SC55.9) eight Amount levels (columns 4 / 5 of the page; S0 bits 5-7; Repeats off = S1 bit 1, columns 6 / 7)
END = False                 # (SC55.9) a mutating track's chain ends with its list's last slot (c_pmend ahead of patchain's c_pcend)
R_END = 5                   # (END) the byte c_pmend's answer points at: fp or 0xFF


def use_v2():
    """SC55.9 / Beta 5.44 (the user, 2026-11-10: «make 8 amounts and mutated patterns end the scene, like Remix just did», Remix's RH88):
    Amount in eight steps (all, 7/8 .. 1/8 of the chain's slots change) on columns 4 / 5 of the page, Repeats on column 6, Keep slot 1 on 7;
    the end of a mutating track's chain = its list's last slot, so a chain of scenes moves on when the lists are over (the stock's test,
    «the last pattern of the chain», could fall in the middle of a list or never come)"""
    global AMT8, END
    AMT8 = END = True


# ---------------------------------------------------------------- the model (tests): the same integer steps as c_pmgen
def settings(length=4, ltype=0, amount=0, norep=False, keep1=False, amt8=None):
    if AMT8 if amt8 is None else amt8:
        return ((length - 1) ^ 3) | ltype << 3 | amount << 5, (1 if keep1 else 0) | (2 if norep else 0)
    return ((length - 1) ^ 3) | ltype << 3 | amount << 5 | (0x80 if norep else 0), 1 if keep1 else 0


def model(t, first, last, seed, s0, s1, amt8=None):
    """-> the list (patterns 0..7)"""
    M = 0xFFFFFFFF
    if last < first: first, last = last, first
    c = last - first + 1
    chain = first << 4 | last
    stamp = seed | s0 << 16 | s1 << 24
    st = [((stamp + t * 0x1000193 + chain * 0x9E37) * MIX) & M]
    def rnd(n):
        st[0] = (st[0] * LCG_A + LCG_C) & M
        return ((st[0] >> 16) * n) >> 16
    L = ((s0 & 7) ^ 3) + 1
    a8 = AMT8 if amt8 is None else amt8
    if a8: ltype, amount, norep, keep1 = s0 >> 3 & 3, s0 >> 5 & 7, s1 >> 1 & 1, s1 & 1
    else: ltype, amount, norep, keep1 = s0 >> 3 & 3, s0 >> 5 & 3, s0 >> 7, s1 & 1
    ln = L if ltype == 1 else 1 + rnd(L) if ltype == 2 else c
    slots, filled = [0] * 8, 0
    if keep1 and ln >= 2:
        slots[0] = first; filled |= 1
    if amount:
        cc = min(ln, c); base = 1 if keep1 and ln >= 2 else 0; n = cc - base
        if n > 0:
            ch = max(1, (n * (8 - amount) + 4) >> 3) if a8 else max(1, (n * (4 - amount) + 2) >> 2)
            chg, k = 0, 0
            while k < ch:
                p = rnd(n); bit = 1 << (p + base)
                if not chg & bit: chg |= bit; k += 1
            for i in range(base, cc):
                if not chg >> i & 1: slots[i] = first + i; filled |= 1 << i
    for i in range(ln):
        if filled >> i & 1: continue
        tries = NREP
        while True:
            v = first + rnd(c)
            if norep and tries and ln > 1:
                tries -= 1
                pv, nx = (i - 1) % ln, (i + 1) % ln
                if (filled >> pv & 1 and slots[pv] == v) or (filled >> nx & 1 and slots[nx] == v): continue
            break
        slots[i] = v; filled |= 1 << i
    return slots[:ln]


def pack_word(lst):
    w = len(lst) << 24
    for i, v in enumerate(lst): w |= (v & 7) << 3 * i
    return w


# ---------------------------------------------------------------- the code
def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_q{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, PK.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def ram(rd): imm32(rd, RAM)

    # ---- c_pmram() -> r0 = RAM, set up the first time (no signature: zero, the positions 0xFF); clobbers r1-r3
    a.label("c_pmram")
    ram(0); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "rm_x", "ne"); E(raw, RET)
    a.label("rm_x")
    E(movs_imm, 1, 0); E(movs_imm, 3, 64)
    a.label("rm_z"); E(subs_imm8, 3, 1); E(strb_reg, 1, 0, 3); E(b_cond, "rm_z", "ne")
    E(movs_imm, 1, 0xFF); E(movs_imm, 3, 8)
    a.label("rm_p"); E(subs_imm8, 3, 1); E(adds_reg, 2, 0, 3); E(strb_imm, 1, 2, R_POS); E(cmp_imm, 3, 0); E(b_cond, "rm_p", "ne")
    imm32(2, SIG); E(str_imm, 2, 0, 0); E(raw, RET)

    # ---- c_pmblk() -> r0 = the project's block (record tail + 367), r1 = 1 when it is ours (mark and check); clobbers r2, r3
    a.label("c_pmblk")
    imm32(0, PC.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); imm32(1, TAIL_OFF); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 0); E(ldrb_imm, 2, 0, B_MARK); E(cmp_imm, 2, MARK); E(b_cond, "bk_x", "ne")
    E(movs_imm, 2, 0); E(movs_imm, 3, B_ACT)
    a.label("bk_s"); E(ldrb_reg, 1, 0, 3); E(adds_reg, 2, 2, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, B_CHK); E(b_cond, "bk_s", "lo")
    E(movs_imm, 1, 0x5A); E(eors_reg, 2, 1); E(lsls_imm, 2, 2, 24); E(lsrs_imm, 2, 2, 24)
    E(ldrb_imm, 3, 0, B_CHK); E(movs_imm, 1, 0); E(cmp_reg, 2, 3); E(b_cond, "bk_x", "ne"); E(movs_imm, 1, 1)
    a.label("bk_x"); E(raw, RET)

    # ---- c_pmget(r0 = byte of the block) -> r0 = its value (0 when the block is not ours); clobbers r1-r3
    a.label("c_pmget")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_pmblk")
    E(cmp_imm, 1, 0); E(b_cond, "gt_0", "eq"); E(ldrb_reg, 0, 0, 4); E(pop_list, [4], pc=True)
    a.label("gt_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pmset(r0 = byte of the block, r1 = value): written, the block made ours (zero before), the check; clobbers r0-r3
    a.label("c_pmset")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(raw, CPSID)
    E(bl, "c_pmblk"); E(cmp_imm, 1, 0); E(b_cond, "st_w", "ne")
    E(movs_imm, 1, 0); E(movs_imm, 2, B_CHK + 1)
    a.label("st_z"); E(subs_imm8, 2, 1); E(strb_reg, 1, 0, 2); E(b_cond, "st_z", "ne")
    E(movs_imm, 1, MARK); E(strb_imm, 1, 0, B_MARK)
    a.label("st_w"); E(strb_reg, 5, 0, 4)
    E(movs_imm, 2, 0); E(movs_imm, 3, B_ACT)
    a.label("st_s"); E(ldrb_reg, 1, 0, 3); E(adds_reg, 2, 2, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, B_CHK); E(b_cond, "st_s", "lo")
    E(movs_imm, 1, 0x5A); E(eors_reg, 2, 1); E(strb_imm, 2, 0, B_CHK)
    E(raw, CPSIE)
    E(pop_list, [4, 5], pc=True)

    # ---- c_pmstamp() -> r0 = seed | S0 << 16 | S1 << 24 (0 when the block is not ours); clobbers r1-r3
    a.label("c_pmstamp")
    E(push_list, [], lr=True); E(bl, "c_pmblk"); E(cmp_imm, 1, 0); E(b_cond, "sp_0", "eq")
    E(ldrb_imm, 1, 0, B_SEED); E(ldrb_imm, 2, 0, B_SEED + 1); E(lsls_imm, 2, 2, 8); E(orrs_reg, 1, 2)
    E(ldrb_imm, 2, 0, B_S0); E(lsls_imm, 2, 2, 16); E(orrs_reg, 1, 2); E(ldrb_imm, 2, 0, B_S1); E(lsls_imm, 2, 2, 24); E(orrs_reg, 1, 2)
    E(mov_reg, 0, 1); E(pop_list, [], pc=True)
    a.label("sp_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

    # ---- c_pmrnd (r7 = the state): the next step -> r0 = r0 * (state >> 16) >> 16 (a draw 0 .. r0 - 1); clobbers r3
    a.label("c_pmrnd")
    imm32(3, LCG_A); E(muls, 7, 3); imm32(3, LCG_C); E(adds_reg, 7, 7, 3)
    E(lsrs_imm, 3, 7, 16); E(muls, 0, 3); E(lsrs_imm, 0, 0, 16); E(raw, RET)

    # ---- c_pmgen(r0 = track, r1 = chain (first << 4 | last), r2 = stamp) -> r0 = the list word (length << 24 | 3 bits a slot); clobbers r1-r3
    #      stack: + 0..7 the slots, + 8 filled (bit i), + 9 the length, + 10 first, + 11 c (the chain's length), + 12 S0, + 13 S1
    a.label("c_pmgen")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
    E(lsrs_imm, 4, 1, 4); E(movs_imm, 5, 15); E(ands_reg, 5, 1)                     # r4 = first, r5 = last
    E(cmp_reg, 5, 4); E(b_cond, "gn_o", "hs"); E(mov_reg, 3, 4); E(mov_reg, 4, 5); E(mov_reg, 5, 3)
    a.label("gn_o")
    E(lsls_imm, 6, 4, 4); E(orrs_reg, 6, 5)                                          # r6 = the chain byte (ordered)
    E(subs_reg, 5, 5, 4); E(adds_imm8, 5, 1)                                         # r5 = c
    E(movs_imm, 3, 0); E(str_sp, 3, 0); E(str_sp, 3, 4); E(str_sp, 3, 8)
    E(raw, strb_sp(4, 10)); E(raw, strb_sp(5, 11))
    E(lsrs_imm, 3, 2, 16); E(raw, strb_sp(3, 12)); E(lsrs_imm, 3, 2, 24); E(raw, strb_sp(3, 13))
    imm32(3, 0x1000193); E(muls, 3, 0); E(adds_reg, 7, 2, 3)                         # the state: (stamp + t K1 + chain K2) MIX
    imm32(3, 0x9E37); E(muls, 3, 6); E(adds_reg, 7, 7, 3); imm32(3, MIX); E(muls, 7, 3)
    # the length
    E(raw, ldrb_sp(1, 12)); E(movs_imm, 0, 7); E(ands_reg, 0, 1); E(movs_imm, 2, 3); E(eors_reg, 0, 2); E(adds_imm8, 0, 1)   # r0 = Length
    E(lsrs_imm, 2, 1, 3); E(movs_imm, 3, 3); E(ands_reg, 2, 3)                       # r2 = the length type
    E(mov_reg, 6, 5)                                                                 # r6 = the length (as the chain)
    E(cmp_imm, 2, 1); E(b_cond, "gn_l2", "ne"); E(mov_reg, 6, 0); E(b, "gn_ld")
    a.label("gn_l2"); E(cmp_imm, 2, 2); E(b_cond, "gn_ld", "ne"); E(bl, "c_pmrnd"); E(adds_imm8, 0, 1); E(mov_reg, 6, 0)
    a.label("gn_ld"); E(raw, strb_sp(6, 9))
    # keep slot 1
    E(movs_imm, 4, 0)                                                                # r4 = base (1 when slot 1 is kept)
    E(raw, ldrb_sp(1, 13)); E(lsrs_imm, 1, 1, 1); E(b_cond, "gn_k", "cc"); E(cmp_imm, 6, 2); E(b_cond, "gn_k", "lo")
    E(raw, ldrb_sp(0, 10)); E(raw, strb_sp(0, 0)); E(movs_imm, 0, 1); E(raw, strb_sp(0, 8)); E(movs_imm, 4, 1)
    a.label("gn_k")
    # the amount: the chain's slots that stay
    E(raw, ldrb_sp(1, 12)); E(lsrs_imm, 1, 1, 5)
    if not AMT8: E(movs_imm, 0, 3); E(ands_reg, 1, 0)
    E(cmp_imm, 1, 0); bc("gn_r", "eq")
    E(movs_imm, 0, 8 if AMT8 else 4); E(subs_reg, 1, 0, 1)                           # r1 = k
    E(mov_reg, 5, 6); E(raw, ldrb_sp(0, 11)); E(cmp_reg, 5, 0); E(b_cond, "gn_c", "ls"); E(mov_reg, 5, 0)
    a.label("gn_c")                                                                  # r5 = cc
    E(subs_reg, 2, 5, 4); bc("gn_r", "le")                                           # r2 = n (eligible slots)
    E(muls, 1, 2); E(adds_imm8, 1, 4 if AMT8 else 2); E(lsrs_imm, 1, 1, 3 if AMT8 else 2); E(cmp_imm, 1, 0); E(b_cond, "gn_m", "ne"); E(movs_imm, 1, 1)
    a.label("gn_m")                                                                  # r1 = how many change
    E(push_list, [5, 6]); E(mov_reg, 5, 2); E(mov_reg, 6, 1); E(movs_imm, 2, 0)        # r5 = n, r6 = left to pick, r2 = the mask
    a.label("gn_a")
    E(cmp_imm, 6, 0); E(b_cond, "gn_ad", "eq")
    E(mov_reg, 0, 5); E(bl, "c_pmrnd"); E(adds_reg, 0, 0, 4); E(movs_imm, 1, 1); E(lsls_reg, 1, 0)
    E(tst_reg, 2, 1); E(b_cond, "gn_a", "ne"); E(orrs_reg, 2, 1); E(subs_imm8, 6, 1); E(b, "gn_a")
    a.label("gn_ad"); E(pop_list, [5, 6])
    E(mov_reg, 1, 4)                                                                 # i = base .. cc - 1: unchanged = first + i
    a.label("gn_f")
    E(cmp_reg, 1, 5); E(b_cond, "gn_r", "hs")
    E(mov_reg, 0, 2); E(lsrs_reg, 0, 1); E(lsls_imm, 0, 0, 31); E(b_cond, "gn_fn", "mi")
    E(raw, ldrb_sp(0, 10)); E(adds_reg, 0, 0, 1); E(mov_reg, 3, 13); E(strb_reg, 0, 3, 1)
    E(raw, ldrb_sp(0, 8)); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(orrs_reg, 0, 3); E(raw, strb_sp(0, 8))
    a.label("gn_fn"); E(adds_imm8, 1, 1); E(b, "gn_f")
    # the random slots
    a.label("gn_r")
    E(movs_imm, 4, 0)                                                                # r4 = i
    a.label("gn_i")
    E(cmp_reg, 4, 6); bc("gn_w", "hs")
    E(raw, ldrb_sp(0, 8)); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); bc("gn_in", "mi")
    E(movs_imm, 5, NREP)                                                             # r5 = tries
    a.label("gn_p")
    E(raw, ldrb_sp(0, 11)); E(bl, "c_pmrnd"); E(raw, ldrb_sp(1, 10)); E(adds_reg, 0, 0, 1)   # r0 = v
    if AMT8: E(raw, ldrb_sp(1, 13)); E(lsls_imm, 1, 1, 30); E(b_cond, "gn_s", "pl")  # repeats on (S1 bit 1 clear)
    else: E(raw, ldrb_sp(1, 12)); E(lsls_imm, 1, 1, 24); E(b_cond, "gn_s", "pl")     # repeats on (S0 bit 7 clear)
    E(cmp_imm, 5, 0); E(b_cond, "gn_s", "eq"); E(cmp_imm, 6, 1); E(b_cond, "gn_s", "ls"); E(subs_imm8, 5, 1)
    E(subs_imm3, 1, 4, 1); E(b_cond, "gn_pv", "pl"); E(adds_reg, 1, 1, 6)            # r1 = (i - 1) mod len
    a.label("gn_pv"); E(bl, "gn_chk"); E(b_cond, "gn_p", "eq")
    E(adds_imm3, 1, 4, 1); E(cmp_reg, 1, 6); E(b_cond, "gn_nx", "lo"); E(movs_imm, 1, 0)   # r1 = (i + 1) mod len
    a.label("gn_nx"); E(bl, "gn_chk"); E(b_cond, "gn_p", "eq")
    a.label("gn_s")
    E(mov_reg, 3, 13); E(strb_reg, 0, 3, 4)
    E(raw, ldrb_sp(1, 8)); E(movs_imm, 3, 1); E(lsls_reg, 3, 4); E(orrs_reg, 1, 3); E(raw, strb_sp(1, 8))
    a.label("gn_in"); E(adds_imm8, 4, 1); E(b, "gn_i")
    # ---- gn_chk (r0 = v, r1 = slot; c_pmgen's frame: a leaf): Z = 1 when that slot is filled and holds v; clobbers r2, r3
    a.label("gn_chk")
    E(raw, ldrb_sp(2, 8)); E(lsrs_reg, 2, 1); E(lsls_imm, 2, 2, 31); E(b_cond, "ck_n", "pl")
    E(mov_reg, 3, 13); E(ldrb_reg, 2, 3, 1); E(cmp_reg, 0, 2); E(raw, RET)
    a.label("ck_n"); E(movs_imm, 2, 1); E(cmp_imm, 2, 0); E(raw, RET)
    # the word
    a.label("gn_w")
    E(lsls_imm, 0, 6, 24); E(movs_imm, 1, 0)
    a.label("gn_wl")
    E(cmp_reg, 1, 6); E(b_cond, "gn_wx", "hs")
    E(mov_reg, 3, 13); E(ldrb_reg, 2, 3, 1); E(movs_imm, 3, 7); E(ands_reg, 2, 3)
    E(movs_imm, 3, 3); E(muls, 3, 1); E(lsls_reg, 2, 3); E(orrs_reg, 0, 2); E(adds_imm8, 1, 1); E(b, "gn_wl")
    a.label("gn_wx"); E(add_sp_imm, 16); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pmlist(r0 = track, r1 = chain byte) -> r0 = its list word, from the cache when the stamp and the chain are the same; clobbers r1-r3
    a.label("c_pmlist")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_pmstamp"); E(mov_reg, 6, 0); E(bl, "c_pmram"); E(mov_reg, 7, 0)
    E(ldr_imm, 0, 7, R_STAMP); E(cmp_reg, 0, 6); E(b_cond, "ls_s", "eq")
    E(str_imm, 6, 7, R_STAMP); E(movs_imm, 0, 0); E(movs_imm, 1, 8)
    a.label("ls_z"); E(subs_imm8, 1, 1); E(lsls_imm, 2, 1, 2); E(adds_reg, 2, 2, 7); E(str_imm, 0, 2, R_LIST); E(cmp_imm, 1, 0); E(b_cond, "ls_z", "ne")
    a.label("ls_s")
    E(lsls_imm, 2, 4, 2); E(adds_reg, 2, 2, 7); E(ldr_imm, 0, 2, R_LIST); E(lsrs_imm, 1, 0, 31); E(b_cond, "ls_g", "eq")
    E(adds_reg, 1, 7, 4); E(ldrb_imm, 1, 1, R_KEY); E(cmp_reg, 1, 5); E(b_cond, "ls_x", "eq")
    a.label("ls_g")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_pmgen")
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 31); E(orrs_reg, 0, 1)
    E(lsls_imm, 2, 4, 2); E(adds_reg, 2, 2, 7); E(str_imm, 0, 2, R_LIST); E(adds_reg, 1, 7, 4); E(strb_imm, 5, 1, R_KEY)
    a.label("ls_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pmchain(r0 = track) -> r0 = its current chain byte (first << 4 | last); clobbers r1-r3
    a.label("c_pmchain")
    E(push_list, [], lr=True); E(mov_reg, 1, 0); imm32(0, CHAINS); E(ldr_imm, 0, 0, 0); E(bl, PK.PARAM_GET)
    E(ldrb_imm, 1, 0, 0); E(ldrb_imm, 0, 0, 1); E(lsls_imm, 1, 1, 4); E(orrs_reg, 0, 1); E(pop_list, [], pc=True)

    # ---- c_pmscr(r0 = scene) -> r0 = its record bytes (rec + 0x40 + 40 s), r1 = 1 when they hold ours (saved, check); clobbers r2, r3
    a.label("c_pmscr")
    E(movs_imm, 1, SC_LEN); E(muls, 1, 0); imm32(0, PC.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, SC_BASE)
    E(movs_imm, 1, 0); E(ldrb_w, 2, 0, SC_SAVED); E(cmp_imm, 2, 0); E(b_cond, "sr_x", "eq")
    E(movs_imm, 2, 0); E(movs_imm, 3, SC_OFF)
    a.label("sr_s"); E(ldrb_reg, 1, 0, 3); E(adds_reg, 2, 2, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, SC_OFF + 5); E(b_cond, "sr_s", "lo")
    E(movs_imm, 1, SC_CHK); E(eors_reg, 2, 1); E(lsls_imm, 2, 2, 24); E(lsrs_imm, 2, 2, 24)
    E(ldrb_w, 3, 0, SC_OFF + 5); E(movs_imm, 1, 0); E(cmp_reg, 2, 3); E(b_cond, "sr_x", "ne"); E(movs_imm, 1, 1)
    a.label("sr_x"); E(raw, RET)

    # ---- c_pmsload(r0 = scene): its lists back (the tracks, the seed, the settings), or none when it holds nothing of ours; clobbers r0-r3
    a.label("c_pmsload")
    E(push_list, [4, 5], lr=True)
    E(cmp_imm, 0, 16); E(b_cond, "sl_x", "hs")
    E(bl, "c_pmscr"); E(mov_reg, 4, 0); E(cmp_imm, 1, 0); E(b_cond, "sl_0", "eq")
    for k, off in enumerate((B_ACT, B_SEED, B_SEED + 1, B_S0, B_S1)):
        E(ldrb_w, 1, 4, SC_OFF + k); E(movs_imm, 0, off); E(bl, "c_pmset")
    E(b, "sl_x")
    a.label("sl_0"); E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "eq")
    E(movs_imm, 0, B_ACT); E(movs_imm, 1, 0); E(bl, "c_pmset")
    a.label("sl_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_pmnext (in place of the bl c_pcnext at 0x0802CD4A; the frame as c_pcnext's: [sp] = the track, r8 = the chain's first, [sp, #2] its
    #      last, [sp, #0x18] forced, [sp, #0x44] a scene change, [sp, #0x48] the scene, fp = 1 the look-ahead) -> [sp, #1]; else c_pcnext
    F = 20
    a.label("c_pmnext")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(raw, ldrb_sp(4, F)); E(cmp_imm, 4, 8); bc("nx_pc", "hs")
    E(movs_imm, 6, 0)                                                                # r6 = 1: slot 1 (forced, a scene starts)
    E(raw, ldrb_sp(0, F + 0x18)); E(cmp_imm, 0, 0); E(b_cond, "nx_sc", "eq"); E(movs_imm, 6, 1)
    a.label("nx_sc")
    E(raw, ldrb_sp(0, F + 0x44)); E(cmp_imm, 0, 0); E(b_cond, "nx_a", "eq")
    E(movs_imm, 6, 1); E(ldr_sp, 0, F + 0x48)
    E(mov_reg, 1, 11); E(cmp_imm, 1, 0); E(b_cond, "nx_ld", "eq")
    # the look-ahead into a new scene: that scene's list, nothing changed
    E(bl, "c_pmscr"); E(cmp_imm, 1, 0); bc("nx_pc", "eq")
    E(ldrb_w, 1, 0, SC_OFF); E(lsrs_reg, 1, 4); E(lsls_imm, 1, 1, 31); bc("nx_pc", "pl")
    E(ldrb_w, 2, 0, SC_OFF + 1); E(ldrb_w, 1, 0, SC_OFF + 2); E(lsls_imm, 1, 1, 8); E(orrs_reg, 2, 1)
    E(ldrb_w, 1, 0, SC_OFF + 3); E(lsls_imm, 1, 1, 16); E(orrs_reg, 2, 1); E(ldrb_w, 1, 0, SC_OFF + 4); E(lsls_imm, 1, 1, 24); E(orrs_reg, 2, 1)
    E(mov_reg, 0, 4); E(bl, "nx_cb"); E(bl, "c_pmgen"); E(b, "nx_s0")
    a.label("nx_ld"); E(bl, "c_pmsload")
    a.label("nx_a")
    E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); bc("nx_pc", "pl")
    E(mov_reg, 0, 4); E(bl, "nx_cb"); E(bl, "c_pmlist")
    E(cmp_imm, 6, 0); E(b_cond, "nx_s0", "ne")
    E(mov_reg, 5, 0); E(bl, "c_pmram"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, R_POS)
    E(adds_imm8, 1, 1); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24)                   # 0xFF + 1 = 0
    E(lsrs_imm, 2, 5, 24); E(movs_imm, 3, 15); E(ands_reg, 2, 3); E(cmp_reg, 1, 2); E(b_cond, "nx_sl", "lo"); E(movs_imm, 1, 0)
    a.label("nx_sl"); E(mov_reg, 3, 0); E(mov_reg, 0, 5); E(b, "nx_p")
    a.label("nx_s0")                                                                  # slot 1
    E(mov_reg, 5, 0); E(bl, "c_pmram"); E(adds_reg, 3, 0, 4); E(mov_reg, 0, 5); E(movs_imm, 1, 0)
    a.label("nx_p")                                                                   # r0 = the word, r1 = the slot, r3 = RAM + track
    E(mov_reg, 2, 11); E(cmp_imm, 2, 0); E(b_cond, "nx_v", "ne"); E(strb_imm, 1, 3, R_POS)
    a.label("nx_v")
    E(movs_imm, 2, 3); E(muls, 2, 1); E(lsrs_reg, 0, 2); E(movs_imm, 1, 7); E(ands_reg, 0, 1)
    E(raw, strb_sp(0, F + 1)); E(pop_list, [4, 5, 6, 7], pc=True)
    # nx_cb(r0 = track; a leaf, c_pmnext's frame) -> r1 = the chain byte from the frame (r8, [sp, #2]); r0 kept
    a.label("nx_cb")
    E(mov_reg, 1, 8); E(lsls_imm, 1, 1, 4); E(raw, ldrb_sp(3, F + 2)); E(orrs_reg, 1, 3); E(raw, RET)
    a.label("nx_pc"); E(raw, popw([4, 5, 6, 7], lr=True)); E(b_w, prev["next"])

    # ---- c_pmssave (the scene save's first write: r1 = the scene): ours into the scene, then the chain rules' (c_pcssave)
    a.label("c_pmssave")
    E(push_list, [0, 1, 2, 3, 4, 5], lr=True)
    E(cmp_imm, 1, 16); E(b_cond, "ss_x", "hs")
    E(mov_reg, 0, 1); E(bl, "c_pmscr"); E(mov_reg, 4, 0)
    E(bl, "c_pmblk"); E(mov_reg, 5, 0); E(movs_imm, 2, 0)
    for k, off in enumerate((B_ACT, B_SEED, B_SEED + 1, B_S0, B_S1)):
        if k == 0:
            E(cmp_imm, 1, 0); E(b_cond, "ss_n", "ne"); E(movs_imm, 0, 0); E(strb_w, 0, 4, SC_OFF); E(strb_w, 0, 4, SC_OFF + 5); E(b, "ss_x")
            a.label("ss_n")
        E(ldrb_imm, 0, 5, off); E(strb_w, 0, 4, SC_OFF + k); E(adds_reg, 2, 2, 0)
    E(movs_imm, 0, SC_CHK); E(eors_reg, 2, 0); E(strb_w, 2, 4, SC_OFF + 5)
    a.label("ss_x"); E(pop_list, [0, 1, 2, 3, 4, 5]); E(raw, POP_LR); E(b_w, prev["ssave"])

    # ---- c_pmscopy (the scene copy's first write: r1 = the destination, [r7, #1] = the source): ours copied, then c_pcscopy
    a.label("c_pmscopy")
    E(push_list, [0, 1, 2, 3, 4, 5], lr=True)
    E(ldrb_imm, 5, 7, 1); E(cmp_imm, 1, 16); E(b_cond, "sy_x", "hs"); E(cmp_imm, 5, 16); E(b_cond, "sy_x", "hs")
    E(mov_reg, 0, 1); E(bl, "c_pmscr"); E(mov_reg, 4, 0); E(mov_reg, 0, 5); E(bl, "c_pmscr")
    E(movs_imm, 2, SC_OFF)
    a.label("sy_l"); E(ldrb_reg, 1, 0, 2); E(strb_reg, 1, 4, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, SC_OFF + 6); E(b_cond, "sy_l", "lo")
    a.label("sy_x"); E(pop_list, [0, 1, 2, 3, 4, 5]); E(raw, POP_LR); E(b_w, prev["scopy"])

    # ---- c_pmheld(r0 = ctrl) -> r0 = the buttons held (bit 0 Clear, bit 1 Duplicate); clobbers r1-r3
    a.label("c_pmheld")
    E(push_list, [], lr=True); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(pop_list, [], pc=True)

    # ---- c_pmview() -> r0 = 1 the Patterns view on the screen, 2 the Mixer (not its Master FX page), else 0; clobbers r1-r3
    a.label("c_pmview")
    E(push_list, [], lr=True); imm32(0, PC.MGR); E(ldr_imm, 1, 0, 0x6C)
    imm32(0, PC.PV); E(cmp_reg, 0, 1); E(b_cond, "vw_m", "ne"); E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    a.label("vw_m"); imm32(0, PC.MIXV); E(cmp_reg, 0, 1); E(b_cond, "vw_0", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "vw_0", "ne"); E(movs_imm, 0, 2); E(pop_list, [], pc=True)
    a.label("vw_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

    # ---- c_pmseed(): a new seed, every selected track a list (from slot 1); clobbers r0-r3
    a.label("c_pmseed")
    E(push_list, [4], lr=True)
    now(0); imm32(1, MIX); E(muls, 0, 1); E(lsrs_imm, 4, 0, 16)
    E(movs_imm, 0, B_SEED); E(mov_reg, 1, 4); E(bl, "c_pmset")
    E(movs_imm, 0, B_SEED + 1); E(lsrs_imm, 1, 4, 8); E(bl, "c_pmset")
    E(movs_imm, 0, B_OFF); E(bl, "c_pmget"); E(movs_imm, 1, 0xFF); E(eors_reg, 1, 0)
    E(movs_imm, 0, B_ACT); E(bl, "c_pmset")
    E(bl, "c_pmram"); E(movs_imm, 1, 0xFF); E(movs_imm, 2, 8)
    a.label("sd_p"); E(subs_imm8, 2, 1); E(adds_reg, 3, 0, 2); E(strb_imm, 1, 3, R_POS); E(cmp_imm, 2, 0); E(b_cond, "sd_p", "ne")
    E(pop_list, [4], pc=True)

    # ---- c_pmbtn (the head of the button press: ctrl, id)
    a.label("c_pmbtn")
    E(push_list, [0, 1, 4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_pmram"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, ID_DUP); E(b_cond, "bn_o", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pmheld"); E(lsrs_imm, 0, 0, 1); E(b_cond, "bn_d", "cc")
    E(movs_imm, 0, B_ACT); E(movs_imm, 1, 0); E(bl, "c_pmset"); E(b, "bn_p")       # Clear + Duplicate: every list ends
    a.label("bn_d")
    E(ldrb_imm, 0, 6, R_FL); E(lsrs_imm, 0, 0, 1); E(b_cond, "bn_sh", "cc")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, R_FL); E(b, "bn_p")                         # the page open: Duplicate closes it
    a.label("bn_sh")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "bn_p", "eq")
    E(bl, "c_pmview"); E(cmp_imm, 0, 0); E(b_cond, "bn_p", "eq")
    now(0); E(str_imm, 0, 6, R_T0); E(movs_imm, 0, FL_PEND); E(strb_imm, 0, 6, R_FL); E(b, "bn_p")
    a.label("bn_o")                                                                  # another button with the page open
    E(ldrb_imm, 0, 6, R_FL); E(lsrs_imm, 0, 0, 1); E(b_cond, "bn_p", "cc")
    E(cmp_imm, 5, 8); E(b_cond, "bn_k", "hs")
    E(movs_imm, 0, B_OFF); E(bl, "c_pmget"); E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(eors_reg, 1, 0)   # a track button: selected / not
    E(movs_imm, 0, B_OFF); E(bl, "c_pmset")
    E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(cmp_imm, 0, 0); E(b_cond, "bn_sw", "eq")   # lists playing: that track joins (selected) / leaves
    E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(bics_reg, 0, 1); E(push_list, [0, 1]); E(movs_imm, 0, B_OFF); E(bl, "c_pmget"); E(pop_list, [2, 3])
    E(tst_reg, 0, 3); E(b_cond, "bn_j", "ne"); E(orrs_reg, 2, 3)
    a.label("bn_j"); E(mov_reg, 1, 2); E(movs_imm, 0, B_ACT); E(bl, "c_pmset")
    E(adds_reg, 0, 6, 5); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, R_POS)
    a.label("bn_sw"); E(pop_list, [0, 1, 4, 5, 6], pc=True)
    a.label("bn_k")
    for k in (ID_REC, ID_PLAY, ID_CLEAR, ID_SHIFT):
        E(cmp_imm, 5, k); E(b_cond, "bn_p", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, R_FL)
    a.label("bn_p"); E(raw, popw([0, 1, 4, 5, 6], lr=True)); E(b_w, prev["btn"])

    # ---- c_pmrel (the head of the button release: ctrl, id): Shift + Duplicate let go before the page opened = a new seed
    a.label("c_pmrel")
    E(cmp_imm, 1, ID_DUP); E(b_cond, "rl_p", "ne")
    E(push_list, [0, 1, 4], lr=True)
    E(bl, "c_pmram"); E(ldrb_imm, 1, 0, R_FL); E(lsrs_imm, 2, 1, 2); E(b_cond, "rl_x", "cc")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, R_FL); E(bl, "c_pmseed")
    a.label("rl_x"); E(raw, popw([0, 1, 4], lr=True))
    a.label("rl_p"); E(b_w, prev["rel"])

    # ---- c_pmpad (the Patterns view's pad press: view, pad, velocity): the page's values; a pattern of a track ends its list
    a.label("c_pmpad")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    E(bl, "c_pmram"); E(mov_reg, 6, 0)
    E(ldr_sp, 0, 4); E(bl, PC.TRACKFN); E(mov_reg, 4, 0); E(ldr_sp, 5, 4); E(lsrs_imm, 5, 5, 3)   # r4 = the column, r5 = the row
    E(ldrb_imm, 0, 6, R_FL); E(lsrs_imm, 0, 0, 1); bc("pd_pg", "cs")
    E(cmp_imm, 4, 8); bc("pd_ch", "hs")
    imm32(0, PC.MGR); E(bl, "c_pmheld"); E(cmp_imm, 0, 0); bc("pd_ch", "ne")
    E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(movs_imm, 1, 1); E(lsls_reg, 1, 4); E(tst_reg, 0, 1); bc("pd_ch", "eq")
    E(bics_reg, 0, 1); E(mov_reg, 1, 0); E(movs_imm, 0, B_ACT); E(bl, "c_pmset")
    a.label("pd_ch"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])
    # the page: r4 = the column, r5 = the row; values into S0 / S1
    a.label("pd_pg")
    E(movs_imm, 0, B_S0); E(bl, "c_pmget"); E(mov_reg, 7, 0)                         # r7 = S0
    E(cmp_imm, 4, 1); E(b_cond, "pd_t", "hi")
    E(lsls_imm, 1, 4, 2); E(adds_reg, 1, 1, 5); E(movs_imm, 2, 3); E(eors_reg, 1, 2)    # Length - 1 = 4 col + row, XOR 3
    E(movs_imm, 2, 7); E(bics_reg, 7, 2); E(orrs_reg, 7, 1); E(b, "pd_w0")
    a.label("pd_t"); E(cmp_imm, 4, 2); E(b_cond, "pd_am", "ne"); E(cmp_imm, 5, 3); bc("pd_x", "hs")
    E(movs_imm, 2, 3 << 3); E(bics_reg, 7, 2); E(lsls_imm, 1, 5, 3); E(orrs_reg, 7, 1); E(b, "pd_w0")
    if AMT8:                                                                         # Amount = 4 (column - 3) + row; Repeats off / Keep slot 1 = S1 bits 1 / 0
        a.label("pd_am"); E(cmp_imm, 4, 4); E(b_cond, "pd_rp", "hi")
        E(subs_imm3, 1, 4, 3); E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 1, 5); E(lsls_imm, 1, 1, 5)
        E(movs_imm, 2, 7 << 5); E(bics_reg, 7, 2); E(orrs_reg, 7, 1)
        a.label("pd_w0"); E(lsls_imm, 7, 7, 24); E(lsrs_imm, 1, 7, 24); E(movs_imm, 0, B_S0); E(bl, "c_pmset"); E(b, "pd_x")
        a.label("pd_rp"); E(cmp_imm, 5, 2); bc("pd_x", "hs"); E(cmp_imm, 4, 6); bc("pd_x", "hi")
        E(movs_imm, 0, B_S1); E(bl, "c_pmget"); E(mov_reg, 1, 0); E(movs_imm, 2, 1); E(mov_reg, 3, 5)
        E(cmp_imm, 4, 5); E(b_cond, "pd_k1", "ne"); E(movs_imm, 2, 2); E(lsls_imm, 3, 3, 1)
        a.label("pd_k1"); E(bics_reg, 1, 2); E(orrs_reg, 1, 3); E(movs_imm, 0, B_S1); E(bl, "c_pmset")
    else:
        a.label("pd_am"); E(cmp_imm, 4, 3); E(b_cond, "pd_rp", "ne")
        E(movs_imm, 2, 3 << 5); E(bics_reg, 7, 2); E(lsls_imm, 1, 5, 5); E(orrs_reg, 7, 1); E(b, "pd_w0")
        a.label("pd_rp"); E(cmp_imm, 5, 2); bc("pd_x", "hs"); E(cmp_imm, 4, 4); E(b_cond, "pd_k1", "ne")
        E(movs_imm, 2, 0x80); E(bics_reg, 7, 2); E(lsls_imm, 1, 5, 7); E(orrs_reg, 7, 1)
        a.label("pd_w0"); E(lsls_imm, 7, 7, 24); E(lsrs_imm, 1, 7, 24); E(movs_imm, 0, B_S0); E(bl, "c_pmset"); E(b, "pd_x")
        a.label("pd_k1"); E(cmp_imm, 4, 5); E(b_cond, "pd_x", "ne"); E(mov_reg, 1, 5); E(movs_imm, 0, B_S1); E(bl, "c_pmset")
    a.label("pd_x"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_pmmix (the Mixer's pad press: view, pad, velocity): the stock's (and the chain rules'), then, stopped, a scene picked = its lists
    a.label("c_pmmix")
    E(push_list, [0, 1, 2, 4], lr=True); E(bl, prev["mix"])
    E(ldr_sp, 4, 4); E(subs_imm8, 4, 16); E(cmp_imm, 4, 16); E(b_cond, "mx_x", "hs")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mx_x", "ne")
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "mx_x", "ne")
    imm32(0, PC.MGR); E(bl, "c_pmheld"); E(cmp_imm, 0, 0); E(b_cond, "mx_x", "ne")
    imm32(0, PC.PLAY_STORE); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mx_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pmsload")
    a.label("mx_x"); E(pop_list, [0, 1, 2, 4], pc=True)

    # ---- c_pmled (the LED task calls: ctrl, frame): the page / the lists over the stock's picture
    a.label("c_pmled")
    E(raw, PC.pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 5, 1); E(bl, prev["led"])
    E(bl, "c_pmram"); E(mov_reg, 6, 0)
    E(bl, "c_pmview"); E(mov_reg, 8, 0)                                              # r8 = the view (1 Patterns, 2 Mixer)
    E(ldrb_imm, 7, 6, R_FL)
    # the page held open: Shift + Duplicate held HOLD_MS in the Patterns view
    E(lsrs_imm, 0, 7, 2); E(b_cond, "ld_o", "cc")
    E(mov_reg, 0, 8); E(cmp_imm, 0, 1); E(b_cond, "ld_o", "ne")
    now(0); E(ldr_imm, 1, 6, R_T0); E(subs_reg, 0, 0, 1); E(movw, 1, HOLD_MS); E(cmp_reg, 0, 1); E(b_cond, "ld_o", "lo")
    E(movs_imm, 7, FL_OPEN); E(strb_imm, 7, 6, R_FL)                                # (pending = Duplicate still down: the release clears it)
    a.label("ld_o")
    E(lsrs_imm, 0, 7, 1); E(b_cond, "ld_sh", "cc")
    E(mov_reg, 0, 8); E(cmp_imm, 0, 1); bc("ld_pg", "eq")
    E(movs_imm, 7, 0); E(strb_imm, 7, 6, R_FL)                                       # another view: closed
    a.label("ld_sh")                                                                 # Shift held: Duplicate yellow (Patterns, Mixer)
    E(mov_reg, 0, 8); E(cmp_imm, 0, 0); bc("ld_x", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ld_ls", "eq")
    E(movs_imm, 0, 2 * LED_DUP); E(movs_imm, 1, C_SHIFT); E(raw, h(0x5229))         # strh r1, [r5, r0]
    a.label("ld_ls")
    E(mov_reg, 0, 8); E(cmp_imm, 0, 1); bc("ld_x", "ne")
    # the Patterns view, closed: the pads of the patterns outside a track's list dark
    E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(mov_reg, 9, 0); E(cmp_imm, 0, 0); bc("ld_x", "eq")
    imm32(0, PC.PV); E(ldrb_w, 0, 0, 0x78); E(lsls_imm, 0, 0, 2); E(mov_reg, 10, 0)    # r10 = the page's first pattern
    E(movs_imm, 4, 0)
    a.label("lp_l")
    E(mov_reg, 0, 4); E(bl, PC.TRACKFN); E(mov_reg, 7, 0); E(cmp_imm, 0, 8); E(b_cond, "lp_n", "hs")
    E(mov_reg, 1, 9); E(lsrs_reg, 1, 0); E(lsls_imm, 1, 1, 31); E(b_cond, "lp_n", "pl")
    E(bl, "c_pmchain"); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(bl, "c_pmlist"); E(mov_reg, 11, 0)   # r11 = the list
    E(mov_reg, 0, 10); E(lsrs_imm, 2, 4, 3); E(adds_reg, 2, 2, 0)                     # r2 = the pad's pattern
    E(lsls_imm, 1, 7, 2); imm32(0, PLAYING); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(push_list, [2]); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(pop_list, [2]); E(ldrb_imm, 0, 0, 0)
    E(cmp_reg, 0, 2); E(b_cond, "lp_n", "eq")                                       # the one playing: the stock's colour
    E(mov_reg, 0, 11); E(lsrs_imm, 1, 0, 24); E(movs_imm, 3, 15); E(ands_reg, 1, 3)   # r1 = the length
    a.label("lp_s")
    E(cmp_imm, 1, 0); E(b_cond, "lp_d", "eq")
    E(movs_imm, 3, 7); E(ands_reg, 3, 0); E(cmp_reg, 3, 2); E(b_cond, "lp_n", "eq"); E(lsrs_imm, 0, 0, 3); E(subs_imm8, 1, 1); E(b, "lp_s")
    a.label("lp_d"); E(lsls_imm, 0, 4, 1); E(movs_imm, 1, 0); E(raw, h(0x5229))       # dark
    a.label("lp_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 32); bc("lp_l", "lo")
    E(b, "ld_x")
    # the page
    a.label("ld_pg")
    E(movs_imm, 0, B_S0); E(bl, "c_pmget"); E(mov_reg, 9, 0); E(movs_imm, 0, B_S1); E(bl, "c_pmget"); E(mov_reg, 10, 0)
    E(movs_imm, 4, 0)
    a.label("pg_l")
    E(mov_reg, 0, 4); E(bl, PC.TRACKFN); E(lsrs_imm, 1, 4, 3)                        # r0 = the column, r1 = the row
    E(movs_imm, 2, 0)                                                                # r2 = the colour
    E(mov_reg, 3, 9)
    E(cmp_imm, 0, 1); E(b_cond, "pg_t", "hi")                                        # Length: (S0 & 7) ^ 3 = 4 col + row
    E(movs_imm, 7, 7); E(ands_reg, 3, 7); E(movs_imm, 7, 3); E(eors_reg, 3, 7); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(b, "pg_c")
    a.label("pg_t"); E(cmp_imm, 0, 2); E(b_cond, "pg_a", "ne"); E(cmp_imm, 1, 3); E(b_cond, "pg_w", "hs")
    E(lsrs_imm, 3, 3, 3); E(movs_imm, 7, 3); E(ands_reg, 3, 7); E(mov_reg, 0, 1); E(b, "pg_c")
    if AMT8:
        a.label("pg_a"); E(cmp_imm, 0, 4); E(b_cond, "pg_r", "hi")
        E(subs_imm3, 0, 0, 3); E(lsls_imm, 0, 0, 2); E(adds_reg, 0, 0, 1); E(lsrs_imm, 3, 3, 5); E(b, "pg_c")
        a.label("pg_r"); E(cmp_imm, 1, 2); E(b_cond, "pg_w", "hs"); E(mov_reg, 3, 10); E(cmp_imm, 0, 5); E(b_cond, "pg_k", "ne")
        E(lsrs_imm, 3, 3, 1); E(b, "pg_k1")
        a.label("pg_k"); E(cmp_imm, 0, 6); E(b_cond, "pg_w", "ne")
        a.label("pg_k1"); E(movs_imm, 7, 1); E(ands_reg, 3, 7); E(mov_reg, 0, 1)
    else:
        a.label("pg_a"); E(cmp_imm, 0, 3); E(b_cond, "pg_r", "ne")
        E(lsrs_imm, 3, 3, 5); E(movs_imm, 7, 3); E(ands_reg, 3, 7); E(mov_reg, 0, 1); E(b, "pg_c")
        a.label("pg_r"); E(cmp_imm, 1, 2); E(b_cond, "pg_w", "hs"); E(cmp_imm, 0, 4); E(b_cond, "pg_k", "ne")
        E(lsrs_imm, 3, 3, 7); E(mov_reg, 0, 1); E(b, "pg_c")
        a.label("pg_k"); E(cmp_imm, 0, 5); E(b_cond, "pg_w", "ne"); E(mov_reg, 3, 10); E(movs_imm, 7, 1); E(ands_reg, 3, 7); E(mov_reg, 0, 1)
    a.label("pg_c"); E(movs_imm, 2, C_DIM); E(cmp_reg, 0, 3); E(b_cond, "pg_w", "ne"); E(movs_imm, 2, C_ON)
    a.label("pg_w"); E(lsls_imm, 0, 4, 1); E(raw, h(0x522A))                          # strh r2, [r5, r0]
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 32); E(b_cond, "pg_l", "lo")
    E(movs_imm, 0, B_OFF); E(bl, "c_pmget"); E(mov_reg, 9, 0); E(movs_imm, 4, 0)       # the track buttons: selected bright
    a.label("pg_b")
    E(movs_imm, 2, C_ON); E(mov_reg, 1, 9); E(lsrs_reg, 1, 4); E(lsls_imm, 1, 1, 31); E(b_cond, "pg_bw", "pl"); E(movs_imm, 2, C_DIM)
    a.label("pg_bw"); E(mov_reg, 0, 4); E(adds_imm8, 0, LED_TRK); E(lsls_imm, 0, 0, 1); E(raw, h(0x522A))
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "pg_b", "lo")
    E(movs_imm, 0, 2 * LED_DUP); E(movs_imm, 2, C_ON); E(raw, h(0x522A))
    a.label("ld_x"); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], pc=True))

    if END:
        # ---- c_pmend (at 0x0802C65E, ahead of patchain's c_pcend; r7 = the track, fp = its pattern ending, sl = a chain pending, r0 its chain
        #      entry): a track playing its list ends its chain with the list's last slot and not before (Z set, [r0, #1] = fp or 0xFF, the
        #      answer in RAM + R_END); a track without a list, or before its list's first slot: c_pcend
        a.label("c_pmend")
        E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
        E(mov_reg, 0, 10); E(cmp_imm, 0, 0); E(b_cond, "me_p", "ne")
        E(mov_reg, 4, 7); E(cmp_imm, 4, 8); E(b_cond, "me_p", "hs")
        E(movs_imm, 0, B_ACT); E(bl, "c_pmget"); E(lsrs_reg, 0, 4); E(lsls_imm, 0, 0, 31); E(b_cond, "me_p", "pl")
        E(bl, "c_pmram"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 5, 0, R_POS); E(cmp_imm, 5, 0xFF); E(b_cond, "me_p", "eq")
        E(mov_reg, 0, 4); E(bl, "c_pmchain"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pmlist")
        E(lsrs_imm, 0, 0, 24); E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(adds_imm8, 5, 1)
        E(cmp_reg, 5, 0); E(b_cond, "me_e", "eq"); E(movs_imm, 5, 0xFF); E(b, "me_n")
        a.label("me_e"); E(mov_reg, 5, 11)
        a.label("me_n")
        E(bl, "c_pmram"); E(strb_imm, 5, 0, R_END); E(adds_imm8, 0, R_END - 1)
        E(add_sp_imm, 4); E(pop_list, [1, 2, 3, 4, 5, 6, 7]); E(raw, POP_LR); E(cmp_reg, 0, 0); E(raw, RET)
        a.label("me_p"); E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7]); E(raw, POP_LR); E(b_w, prev["end"])
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import bl as bl_enc, b_w as bw_enc
    import fm8dest as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_gact=lab("sc17", "c_gact"))
    prev = dict(next=FD.bl_target(img, PC.NEXT_HOOK, BASE), ssave=FD.bl_target(img, PC.SC_SAVE, BASE), scopy=FD.bl_target(img, PC.SC_COPY, BASE),
                pad=u(PC.PV_VT) & ~1, mix=u(PC.MIX_VT) & ~1, btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), rel=MP.bw_target(img, JK.BTN_REL, BASE),
                led=FD.bl_target(img, PK.LED_CALLS[0], BASE), end=FD.bl_target(img, PC.END_HOOK, BASE))
    assert prev["next"] == lab("patchain", "c_pcnext") and prev["ssave"] == lab("patchain", "c_pcssave"), prev
    assert prev["scopy"] == lab("patchain", "c_pcscopy")
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["led"]
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, hex(len(img))
    img[PC.NEXT_HOOK - BASE:PC.NEXT_HOOK - BASE + 4] = bl_enc(PC.NEXT_HOOK, labels["c_pmnext"])
    img[PC.SC_SAVE - BASE:PC.SC_SAVE - BASE + 4] = bl_enc(PC.SC_SAVE, labels["c_pmssave"])
    img[PC.SC_COPY - BASE:PC.SC_COPY - BASE + 4] = bl_enc(PC.SC_COPY, labels["c_pmscopy"])
    struct.pack_into("<I", img, PC.PV_VT - BASE, labels["c_pmpad"] | 1)
    struct.pack_into("<I", img, PC.MIX_VT - BASE, labels["c_pmmix"] | 1)
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = bw_enc(MP.BTN_ENTRY, labels["c_pmbtn"])
    img[JK.BTN_REL - BASE:JK.BTN_REL - BASE + 4] = bw_enc(JK.BTN_REL, labels["c_pmrel"])
    for c in PK.LED_CALLS:
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_pmled"])
    if END:
        assert prev["end"] == lab("patchain", "c_pcend"), hex(prev["end"])
        img[PC.END_HOOK - BASE:PC.END_HOOK - BASE + 4] = bl_enc(PC.END_HOOK, labels["c_pmend"])
    return labels, code, prev
