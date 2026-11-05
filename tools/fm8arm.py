"""The ARM code of the 8-operator FM (fm8.py's data model): the engine (envelopes, the DSP writes and their cache), the tick, the note-on and
poly's voices.  The panel (knobs, pads, LEDs, patches) is fm8ui.py; fm8.install puts both in dspz's gap and points fmeng's trampolines at them."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402
from fm8 import (OPB, PEG, GLB, PLEN, O_R, O_L, O_BP, O_LD, O_RD, O_RS, O_KVS, O_OL, O_MODE, O_CRS, O_FINE, O_DET,  # noqa: E402
                 G_ALG, G_FB, G_SYNC, G_TRN, G_NZ, G_NZOP, NALG, EMAX, FLOOR, AMP0, VEL_K, LS_K, RS_K, PEG_C, PEG_K, KW_CAR, M_FULL, THR,
                 A_N, A_CAR, A_FBS, A_FBD, A_USED, A_MASK)
import fmeng as FE  # noqa: E402
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   ldrh_imm, ldrh_reg, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list,
                   raw, str_imm, strb_imm, strb_reg, strb_w, strh_imm, subs_imm8, subs_reg, tst_reg, ldr_sp)

FM8R = 0x2004C600                       # RAM (free: S514D, 0x2004A3C0-0x2004FC00): + 0 "FM81", + 8 the cache's refresh (index, "FM81"), + 0x40 the
SIG8 = 0x31384D46                       # run's context, + 0x100 + 0x100 t the tracks' blocks, + 0x300 + 0x80 t the tracks' own voices, + 0x400 +
CTX8 = FM8R + 0x40                      # 0x80 s poly's twelve slots' voices (to + 0xA00)
TB0, TBS = 0x100, 0x100
VT0, VP0, VSS = 0x300, 0x400, 0x80
WC8 = 0x2004A400                        # the write cache: the 14 slots x 128 words, then poly's records (2128 words, to 0x2004C540)
# a track block after the parameters
B_ON, B_DIRTY, B_SENT, B_SEL, B_P7, B_OVK, B_CNT, B_STR, B_OVT, B_LEDT, B_KID = 216, 217, 218, 219, 220, 221, 222, 223, 224, 228, 232
# a voice: + 0 e[9] (u32, 8 fractional bits), + 36 st[9] (0-3 the stages, 4 sustained, 5 done), + 45 gate, + 46 note, + 47 velocity, + 48 the
# attenuations sent [8] (u16), + 64 the last tick's time, + 68 new, + 69 the phase resets, + 70 the routing counter, + 71 dirty, + 72 poly's TRIG
# seen (u16), + 74 the slot's first use done, + 76 the noise sent (the track's own: not in the cache)
V_E, V_ST, V_GATE, V_NOTE, V_VEL, V_LAST, V_T, V_NEW, V_PHR, V_CNT, V_DIRTY, V_SEEN, V_USE, V_NZL = 0, 36, 45, 46, 47, 48, 64, 68, 69, 70, 71, 72, 74, 76
# the context: + 0 the slot (DSP X), + 4 track, + 8 the increment (0: OSC1 + 11), + 12 the noise's address (0: OSC1 + NZ_OFF), + 16 gate, + 20 dt,
# + 24 G (the brightness x 256), + 28 pf (x 4096), + 32 the feedback's coefficient, + 36 poly (the shape read once a tick), + 40 the rate
# scaling's notes, + 44 (127 - velocity) x VEL_K, + 48 N
C_SLOT, C_TRK, C_INC, C_NZ, C_GATE, C_DT, C_G, C_PF, C_FB, C_POLY, C_RSN, C_VELA, C_N = 0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48
E_OFF = 868                             # a poly voice whose envelopes are all below this (about -51 dB) is free
NWC = 14 * 128
INCS = [round((1 << 24) * 440 * 2 ** ((n - 69) / 12) / 48000) for n in range(128)]
DSP_WRITE, DSP_READ = 0x080292F8, 0x08029344
S8 = 16                                 # an operator's words on core 0


def ldr_w(rt, rn, imm): return h(0xF8D0 | rn) + h(rt << 12 | imm)
def str_w(rt, rn, imm): return h(0xF8C0 | rn) + h(rt << 12 | imm)
def ldrh_w(rt, rn, imm): return h(0xF8B0 | rn) + h(rt << 12 | imm)
def strh_w(rt, rn, imm): return h(0xF8A0 | rn) + h(rt << 12 | imm)
def umull(lo, hi, rn, rm): return h(0xFBA0 | rn) + h(lo << 12 | hi << 8 | rm)
def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def asrs_imm(rd, rm, imm): return h(0x1000 | imm << 6 | rm << 3 | rd)
def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def negs(rd, rm): return h(0x4240 | rm << 3 | rd)
def bics(rdn, rm): return h(0x4380 | rm << 3 | rdn)
RET = h(0x4770)
MRS7, CPSID, MSR7 = bytes([0xEF, 0xF3, 0x10, 0x87]), bytes([0x72, 0xB6]), bytes([0x87, 0xF3, 0x10, 0x88])


def wc_ranges():
    """The cached ranges: (first word, words, block size, the ARM-owned words' mask, the first index)."""
    om = sum(1 << w for w in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15))           # R, AMP, K, M1-M8, HC
    rs = ((VD.FV0, NWC, S8, om), (VD.PV_REC0, 2 * VD.PV_N * VD.PV_RS, VD.PV_RS, FE.REC_MASK))
    r, i = [], 0
    for base, ln, mod, mask in rs:
        r.append((base, ln, mod, mask, i)); i += ln
    return r, i


class Ctx:
    def __init__(s, base):
        s.a = Asm(base); s.base = base; s.zc = 0
    def E(s, *x, **k): s.a.emit(*x, **k)
    def L(s, n): s.a.label(n)
    def imm32(s, rd, v): s.E(movw, rd, v & 0xFFFF); s.E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(s, target, cond):
        s.zc += 1; n = f"_g{s.zc}"
        s.E(b_cond, n, V.INV[cond]); s.E(b, target); s.L(n)
    def now(s, rd): s.imm32(rd, V.HAL_TICK); s.E(ldr_imm, rd, rd, 0)
    def clamp24(s, r_, tmp):
        s.zc += 1; n = f"_k{s.zc}"
        s.imm32(tmp, 0x7FFFFF); s.E(cmp_reg, r_, tmp); s.E(b_cond, n, "ls"); s.E(mov_reg, r_, tmp); s.L(n)


def data(c, T, extra=()):
    """The tables, emitted first: T[name] = their addresses."""
    d = bytearray()
    def put(name, bs):
        while len(d) % 4: d.append(0)
        T[name] = c.base + len(d); d.extend(bs)
    put("exp", struct.pack("<256H", *F.EXP))
    put("slope", struct.pack("<128I", *F.SLOPE))
    put("fix", struct.pack("<100I", *F.FIX))
    put("inc", struct.pack("<128I", *INCS))
    put("algs", F.algs())
    put("bexp", struct.pack("<64H", *FE.BEXP))
    put("def8", F.DEFAULT)
    for name, bs in extra:
        put(name, bs)
    while len(d) % 4: d.append(0)
    return bytes(d)


def engine(c, T, L, prev):
    """c_fmst, c_fmblk, c_fmvs, c_fmalg, c_fmact, c_fmw, c_fmref, c_fmosc, c_fmexp, c_fmsw, c_fm8run, c_fmflag, c_fmtick, c_fmnon, c_fm8poly,
    c_fmloud.  T = the tables' addresses."""
    E, imm32, bc = c.E, c.imm32, c.bc
    lab = c.L

    # ---- c_fmst() -> r0 = FM8R, set up at the first use (the tracks' defaults, the voices silent); clobbers r1-r3
    lab("c_fmst")
    imm32(0, FM8R); E(ldr_imm, 1, 0, 0); imm32(2, SIG8); E(cmp_reg, 1, 2); E(b_cond, "st_i", "ne"); E(raw, RET)
    lab("st_i")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0); imm32(3, (VP0 + 12 * VSS) // 4)
    lab("st_z"); E(str_imm, 1, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 3, 1); E(b_cond, "st_z", "ne")
    for t in (0, 1):
        imm32(2, FM8R + TB0 + TBS * t); imm32(5, T["def8"]); E(movs_imm, 3, 0)
        lab(f"st_d{t}"); E(ldrb_reg, 1, 5, 3); E(strb_reg, 1, 2, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, PLEN); E(b_cond, f"st_d{t}", "lo")
        E(movs_imm, 1, 0xFF); E(strb_w, 1, 2, B_SENT); E(movs_imm, 1, 1); E(strb_w, 1, 2, B_DIRTY)
    E(movs_imm, 2, 0)
    lab("st_v"); imm32(0, FM8R + VT0); E(lsls_imm, 1, 2, 7); E(adds_reg, 0, 0, 1); E(bl, "c_fmvz")
    E(adds_imm8, 2, 1); E(cmp_imm, 2, 14); E(b_cond, "st_v", "lo")
    imm32(1, SIG8); E(str_imm, 1, 4, 0); E(mov_reg, 0, 4)
    E(pop_list, [4, 5], pc=True)

    # ---- c_fmvz(r0 = voice): silent: e 0 (the pitch envelope at its centre), the stages done, nothing sent; clobbers r1, r3
    lab("c_fmvz")
    E(push_list, [5]); E(movs_imm, 1, 0)
    lab("vz_e"); E(movs_imm, 3, 0); E(lsls_imm, 5, 1, 2); E(adds_reg, 5, 5, 0); E(str_imm, 3, 5, V_E)
    E(movs_imm, 3, 5); E(adds_reg, 5, 0, 1); E(strb_w, 3, 5, V_ST); E(adds_imm8, 1, 1); E(cmp_imm, 1, 9); E(b_cond, "vz_e", "lo")
    imm32(3, PEG_C << 8); E(str_imm, 3, 0, V_E + 32)
    imm32(3, 0xFFFF); E(movs_imm, 1, 0)
    lab("vz_l"); E(adds_reg, 5, 0, 1); E(strh_imm, 3, 5, V_LAST); E(adds_imm8, 1, 2); E(cmp_imm, 1, 16); E(b_cond, "vz_l", "lo")
    E(movs_imm, 3, 1); E(strb_w, 3, 0, V_DIRTY); E(movs_imm, 3, 0); E(subs_imm8, 3, 1); E(str_imm, 3, 0, V_NZL); E(pop_list, [5]); E(raw, RET)

    # ---- c_fmblk(r0 = track) -> r0 = its block; c_fmvs(r0 = track) -> its own voice; clobbers r1-r3
    lab("c_fmblk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_fmst")
    E(lsls_imm, 1, 4, 8); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 255); E(adds_imm8, 0, 1); E(pop_list, [4], pc=True)
    lab("c_fmvs")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_fmst")
    E(lsls_imm, 1, 4, 7); E(adds_reg, 0, 0, 1); imm32(1, VT0); E(adds_reg, 0, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_fmalg(r0 = block) -> r0 = its algorithm's entry; clobbers r1
    lab("c_fmalg")
    E(ldrb_w, 0, 0, GLB + G_ALG); E(cmp_imm, 0, NALG); E(b_cond, "al_ok", "lo"); E(movs_imm, 0, 0)
    lab("al_ok"); E(lsls_imm, 0, 0, 4); imm32(1, T["algs"]); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_fmact(r0 = track) -> r0 = 1 while FM sounds; clobbers r1-r3
    lab("c_fmact")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmblk"); E(mov_reg, 5, 0); E(ldrb_w, 0, 5, B_ON); E(cmp_imm, 0, 0); E(b_cond, "ac_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ac_off", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 2); E(b_cond, "ac_off", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    lab("ac_off"); E(movs_imm, 0, 0); E(strb_w, 0, 5, B_ON)
    lab("ac_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_fmw(r0 = DSP X address, r1 = value): the write, skipped when an ARM-owned word already holds the value; clobbers r0-r3
    lab("c_fmw")
    R_, WN = wc_ranges()
    E(push_list, [4, 5], lr=True)
    for i, (rb, ln, mod, mask, i0) in enumerate(R_):
        imm32(2, rb); E(subs_reg, 3, 0, 2); imm32(4, ln); E(cmp_reg, 3, 4); E(b_cond, "fw_r%d" % i, "lo")
    E(b, "fw_wr")
    for i, (rb, ln, mod, mask, i0) in enumerate(R_):
        lab("fw_r%d" % i)
        E(movs_imm, 4, mod); E(raw, udiv(5, 3, 4)); E(muls, 5, 4); E(subs_reg, 5, 3, 5)
        if i0: imm32(4, i0); E(adds_reg, 3, 3, 4)
        imm32(4, mask); E(b, "fw_t")
    lab("fw_t"); E(lsrs_reg, 4, 5); E(lsrs_imm, 4, 4, 1); E(b_cond, "fw_wr", "lo")
    E(lsls_imm, 4, 1, 8); E(lsrs_imm, 4, 4, 8); E(movs_imm, 5, 1); E(lsls_imm, 5, 5, 31); E(orrs_reg, 4, 5)
    imm32(5, WC8); E(lsls_imm, 3, 3, 2); E(adds_reg, 5, 5, 3); E(ldr_imm, 3, 5, 0); E(cmp_reg, 3, 4); E(b_cond, "fw_s", "eq"); E(str_imm, 4, 5, 0)
    lab("fw_wr")
    E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(raw, popw([4, 5], lr=True)); E(b_w, DSP_WRITE)
    lab("fw_s"); E(pop_list, [4, 5], pc=True)

    # ---- c_fmref(): one cached word written again a tick (the 2128 in ~2 s: a reloaded DSP never stays stale); clobbers r0-r3
    lab("c_fmref")
    E(push_list, [4], lr=True)
    imm32(4, FM8R + 8); E(ldr_imm, 0, 4, 4); imm32(1, SIG8); E(cmp_reg, 0, 1); E(b_cond, "rf_ok", "eq")
    E(str_imm, 1, 4, 4); imm32(2, WC8); E(movs_imm, 0, 0); imm32(3, WN)
    lab("rf_z"); E(str_imm, 0, 2, 0); E(adds_imm8, 2, 4); E(subs_imm8, 3, 1); E(b_cond, "rf_z", "ne"); E(str_imm, 0, 4, 0)
    lab("rf_ok")
    E(ldr_imm, 0, 4, 0); E(adds_imm8, 0, 1); imm32(1, WN); E(cmp_reg, 0, 1); E(b_cond, "rf_w", "lo"); E(movs_imm, 0, 0)
    lab("rf_w"); E(str_imm, 0, 4, 0)
    imm32(2, WC8); E(lsls_imm, 1, 0, 2); E(raw, ldr_reg(1, 2, 1)); E(cmp_imm, 1, 0); E(b_cond, "rf_x", "ge")
    for i, (rb, ln, mod, mask, i0) in enumerate(R_):
        imm32(3, i0 + ln); E(cmp_reg, 0, 3); E(b_cond, "rf_%d" % i, "lo")
    E(b, "rf_x")
    for i, (rb, ln, mod, mask, i0) in enumerate(R_):
        lab("rf_%d" % i); imm32(2, rb - i0); E(b, "rf_a")
    lab("rf_a"); E(adds_reg, 2, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    lab("rf_x"); E(pop_list, [4], pc=True)

    # ---- c_fmosc(r0 = track, r1 = word of the OSC1 block) -> r0 = its address; clobbers r1, r2
    lab("c_fmosc")
    E(movs_imm, 2, 48); E(muls, 0, 2); imm32(2, VD.OSB0); E(adds_reg, 0, 0, 2); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_fmexp(r0 = attenuation in u) -> r0 = EXP[f] >> q (65535 at 0); clobbers r1, r2
    lab("c_fmexp")
    E(lsrs_imm, 1, 0, 8); E(cmp_imm, 1, 24); E(b_cond, "ex_0", "hs")
    E(movs_imm, 2, 255); E(ands_reg, 0, 2); E(lsls_imm, 0, 0, 1); imm32(2, T["exp"]); E(ldrh_reg, 0, 2, 0); E(lsrs_reg, 0, 1); E(raw, RET)
    lab("ex_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_fmamp(r0 = attenuation in u) -> r0 = EXP[f] x AMP0 >> q; clobbers r1, r2
    lab("c_fmamp")
    E(lsrs_imm, 1, 0, 8); E(cmp_imm, 1, 24); E(b_cond, "ex_0", "hs")
    E(movs_imm, 2, 255); E(ands_reg, 0, 2); E(lsls_imm, 0, 0, 1); imm32(2, T["exp"]); E(ldrh_reg, 0, 2, 0); E(movs_imm, 2, AMP0); E(muls, 0, 2)
    E(lsrs_reg, 0, 1); E(raw, RET)

    # ---- c_fmsw(r0 = word of the context's slot, r1 = value): c_fmw; clobbers r0-r3
    lab("c_fmsw")
    imm32(2, CTX8); E(ldr_imm, 2, 2, C_SLOT); E(adds_reg, 0, 0, 2); E(b, "c_fmw")

    # ---- c_fm8run(r0 = voice, r1 = block; the context filled): the envelopes, then R / AMP of the N operators, the noise, the feedback, and
    #      (dirty or every 64 ticks) K / M / HC / N and the flag
    lab("c_fm8run")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 0, 5); E(bl, "c_fmalg"); E(mov_reg, 6, 0); imm32(7, CTX8)
    E(ldrb_imm, 0, 6, A_N); E(str_imm, 0, 7, C_N)
    # a new note: every stage from 1, the phases reset with the key sync; the gate let go: every stage to the release
    E(ldrb_w, 0, 4, V_NEW); E(cmp_imm, 0, 0); E(b_cond, "rn_r", "eq")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, V_NEW); E(movs_imm, 1, 1); E(strb_w, 1, 4, V_DIRTY)
    lab("rn_z"); E(adds_reg, 2, 4, 0); E(movs_imm, 1, 0); E(strb_w, 1, 2, V_ST); E(adds_imm8, 0, 1); E(cmp_imm, 0, 9); E(b_cond, "rn_z", "lo")
    E(ldrb_w, 0, 5, GLB + G_SYNC); E(cmp_imm, 0, 0); E(b_cond, "rn_g", "eq"); E(movs_imm, 0, 0xFF); E(strb_w, 0, 4, V_PHR); E(b, "rn_g")
    lab("rn_r")
    E(ldrb_w, 0, 4, V_GATE); E(cmp_imm, 0, 0); E(b_cond, "rn_g", "eq"); E(ldr_imm, 0, 7, C_GATE); E(cmp_imm, 0, 0); E(b_cond, "rn_g", "ne")
    E(movs_imm, 0, 0)
    lab("rn_rl"); E(adds_reg, 2, 4, 0); E(ldrb_w, 1, 2, V_ST); E(cmp_imm, 1, 5); E(b_cond, "rn_rn", "eq"); E(movs_imm, 1, 3); E(strb_w, 1, 2, V_ST)
    lab("rn_rn"); E(adds_imm8, 0, 1); E(cmp_imm, 0, 9); E(b_cond, "rn_rl", "lo")
    lab("rn_g"); E(ldr_imm, 0, 7, C_GATE); E(strb_w, 0, 4, V_GATE)
    E(ldrb_w, 0, 4, V_NOTE); E(subs_imm8, 0, 24); E(b_cond, "rn_s", "ge"); E(movs_imm, 0, 0)
    lab("rn_s"); E(str_imm, 0, 7, C_RSN)
    E(ldrb_w, 0, 4, V_VEL); E(cmp_imm, 0, 127); E(b_cond, "rn_v", "ls"); E(movs_imm, 0, 127)
    lab("rn_v"); E(movs_imm, 1, 127); E(subs_reg, 1, 1, 0); E(movs_imm, 0, VEL_K); E(muls, 1, 0); E(str_imm, 1, 7, C_VELA)
    # ---- the nine envelopes (r8 = i, r9 = the parameters 24 i, r10 = e's address, r11 = the target)
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)
    lab("ev_l")
    E(mov_reg, 0, 8); E(adds_reg, 1, 4, 0); E(ldrb_w, 2, 1, V_ST); E(cmp_imm, 2, 4); bc("ev_n", "hs")
    E(movs_imm, 3, OPB); E(muls, 3, 0); E(adds_reg, 3, 3, 5); E(mov_reg, 9, 3)
    E(lsls_imm, 1, 0, 2); E(adds_reg, 1, 1, 4); E(mov_reg, 10, 1)
    E(adds_reg, 0, 3, 2); E(ldrb_imm, 1, 0, O_L); E(lsls_imm, 1, 1, 13); E(mov_reg, 11, 1)
    E(ldrb_imm, 0, 0, O_R)
    E(mov_reg, 1, 8); E(cmp_imm, 1, 8); E(b_cond, "ev_rs", "eq")
    E(mov_reg, 1, 9); E(ldrb_imm, 1, 1, O_RS); E(ldr_imm, 3, 7, C_RSN); E(muls, 1, 3); E(movs_imm, 3, RS_K); E(muls, 1, 3); E(lsrs_imm, 1, 1, 6)
    E(adds_reg, 0, 0, 1); E(cmp_imm, 0, 127); E(b_cond, "ev_rs", "ls"); E(movs_imm, 0, 127)
    lab("ev_rs")
    E(lsls_imm, 0, 0, 2); imm32(1, T["slope"]); E(raw, ldr_reg(0, 1, 0)); E(ldr_imm, 1, 7, C_DT); E(muls, 0, 1)
    E(mov_reg, 1, 10); E(ldr_imm, 1, 1, V_E); E(mov_reg, 3, 11)
    E(cmp_reg, 3, 1); E(b_cond, "ev_dn", "ls")
    E(mov_reg, 2, 8); E(cmp_imm, 2, 8); E(b_cond, "ev_up", "eq")
    imm32(2, FLOOR << 8); E(cmp_reg, 1, 2); E(b_cond, "ev_f", "hs"); E(mov_reg, 1, 2)
    lab("ev_f"); E(lsls_imm, 0, 0, 2)
    lab("ev_up"); E(adds_reg, 1, 1, 0); E(cmp_reg, 1, 3); E(b_cond, "ev_st", "lo"); E(mov_reg, 1, 3); E(b, "ev_st")
    lab("ev_dn"); E(subs_reg, 2, 1, 3); E(cmp_reg, 2, 0); E(b_cond, "ev_d2", "hi"); E(mov_reg, 1, 3); E(b, "ev_st")
    lab("ev_d2"); E(subs_reg, 1, 1, 0)
    lab("ev_st"); E(mov_reg, 2, 10); E(str_imm, 1, 2, V_E)
    E(cmp_reg, 1, 3); E(b_cond, "ev_n", "ne")
    E(mov_reg, 0, 8); E(adds_reg, 0, 0, 4); E(ldrb_w, 1, 0, V_ST); E(adds_imm8, 1, 1); E(cmp_imm, 1, 3); E(b_cond, "ev_s2", "ne"); E(movs_imm, 1, 4); E(b, "ev_sw")
    lab("ev_s2"); E(cmp_imm, 1, 4); E(b_cond, "ev_sw", "ne"); E(movs_imm, 1, 5)
    lab("ev_sw"); E(strb_w, 1, 0, V_ST)
    lab("ev_n"); E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(cmp_imm, 0, 9); bc("ev_l", "lo")
    # ---- the pitch factor (x 4096): the pitch envelope and the transpose
    E(ldr_imm, 0, 4, V_E + 32); E(lsrs_imm, 0, 0, 8); imm32(1, PEG_C); E(subs_reg, 0, 0, 1); imm32(1, PEG_K); E(muls, 0, 1); E(raw, asrs_imm(0, 0, 12))
    E(ldrb_w, 1, 5, GLB + G_TRN); E(subs_imm8, 1, 24); E(movs_imm, 2, 85); E(muls, 1, 2); E(raw, asrs_imm(1, 1, 2)); E(adds_reg, 0, 0, 1)
    E(raw, asrs_imm(3, 0, 8)); E(movs_imm, 1, 255); E(ands_reg, 0, 1)
    E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 12); E(cmp_imm, 0, 0); E(b_cond, "pf_q", "eq")
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 8); E(subs_reg, 0, 1, 0); E(lsls_imm, 0, 0, 1); imm32(1, T["exp"]); E(ldrh_reg, 2, 1, 0)
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 13); E(muls, 2, 1); E(lsrs_imm, 2, 2, 16)
    lab("pf_q"); E(cmp_imm, 3, 0); E(b_cond, "pf_n", "lt"); E(lsls_reg, 2, 3); E(b, "pf_w")
    lab("pf_n"); E(raw, negs(3, 3)); E(lsrs_reg, 2, 3)
    lab("pf_w"); E(str_imm, 2, 7, C_PF)
    # ---- the brightness G (OSC1 + 14, the shape; poly: read once a tick) and the increment
    E(ldr_imm, 0, 7, C_POLY); E(cmp_imm, 0, 0); E(b_cond, "br_r", "eq")
    imm32(0, FE.SHC); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "br_h", "ne")
    lab("br_r")
    E(ldr_imm, 0, 7, C_TRK); E(movs_imm, 1, 14); E(bl, "c_fmosc"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(bl, DSP_READ)
    E(ldr_imm, 1, 7, C_POLY); E(cmp_imm, 1, 0); E(b_cond, "br_h", "eq"); imm32(1, FE.SHC); E(str_imm, 0, 1, 0)
    lab("br_h"); E(raw, asrs_imm(0, 0, 26)); E(adds_imm8, 0, 32); E(lsls_imm, 0, 0, 1); imm32(1, T["bexp"]); E(ldrh_reg, 0, 1, 0); E(str_imm, 0, 7, C_G)
    E(ldr_imm, 0, 7, C_INC); E(cmp_imm, 0, 0); E(b_cond, "in_h", "ne")
    E(ldr_imm, 0, 7, C_TRK); E(movs_imm, 1, 11); E(bl, "c_fmosc"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8)
    E(str_imm, 0, 7, C_INC)
    lab("in_h")
    E(ldrb_w, 0, 5, GLB + G_FB); E(muls, 0, 0); E(ldr_imm, 1, 7, C_G); E(muls, 0, 1); c.clamp24(0, 1); E(str_imm, 0, 7, C_FB)
    # ---- the operators (r8 = k, r9 = its parameters, r10 = R, r11 = the attenuation)
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)
    lab("op_l")
    E(mov_reg, 0, 8); E(movs_imm, 1, OPB); E(muls, 1, 0); E(adds_reg, 1, 1, 5); E(mov_reg, 9, 1)
    E(ldrb_imm, 0, 1, O_MODE); E(cmp_imm, 0, 0); E(b_cond, "op_rt", "eq")             # fixed: FIX[fine] x 8 / inc x 10^c >> 3
    E(ldrb_imm, 0, 1, O_FINE); E(cmp_imm, 0, 99); E(b_cond, "op_f1", "ls"); E(movs_imm, 0, 99)
    lab("op_f1"); E(lsls_imm, 0, 0, 2); imm32(2, T["fix"]); E(raw, ldr_reg(0, 2, 0)); E(lsls_imm, 0, 0, 3)
    E(ldr_imm, 2, 7, C_INC); E(cmp_imm, 2, 0); E(b_cond, "op_f2", "ne"); E(movs_imm, 2, 1)
    lab("op_f2"); E(raw, udiv(0, 0, 2)); E(ldrb_imm, 2, 1, O_CRS); E(movs_imm, 3, 3); E(ands_reg, 2, 3)
    lab("op_f3"); E(cmp_imm, 2, 0); E(b_cond, "op_f4", "eq"); E(movs_imm, 3, 10); E(muls, 0, 3); E(subs_imm8, 2, 1); E(b, "op_f3")
    lab("op_f4"); E(lsrs_imm, 0, 0, 3); E(b, "op_pf")
    lab("op_rt")                                                                         # ratio: (coarse or 0.5) x (100 + fine) / 100 x detune
    E(ldrb_imm, 0, 1, O_CRS); E(lsls_imm, 0, 0, 12); E(cmp_imm, 0, 0); E(b_cond, "op_c", "ne"); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 11)
    lab("op_c"); E(ldrb_imm, 2, 1, O_FINE); E(adds_imm8, 2, 100); E(muls, 0, 2); E(movs_imm, 2, 100); E(raw, udiv(0, 0, 2))
    E(ldrb_imm, 2, 1, O_DET); E(subs_imm8, 2, 7); E(lsls_imm, 2, 2, 2); E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 12); E(adds_reg, 2, 2, 3)
    E(muls, 0, 2); E(lsrs_imm, 0, 0, 12); E(lsls_imm, 0, 0, 4)
    lab("op_pf"); E(ldr_imm, 1, 7, C_PF); E(raw, umull(0, 2, 0, 1)); E(lsrs_imm, 0, 0, 12); E(lsls_imm, 2, 2, 20); E(orrs_reg, 0, 2)
    c.clamp24(0, 1); E(mov_reg, 10, 0)
    E(ldrb_w, 2, 4, V_PHR); E(mov_reg, 0, 8); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(tst_reg, 2, 3); E(b_cond, "op_np", "eq")   # the phase from 0
    E(ldrb_w, 2, 4, V_PHR); E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(raw, bics(2, 3)); E(strb_w, 2, 4, V_PHR)
    E(lsls_imm, 0, 0, 4); E(adds_imm8, 0, VD.F_PH); E(movs_imm, 1, 0); E(bl, "c_fmsw")
    lab("op_np")
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 4); E(adds_imm8, 0, VD.F_R); E(mov_reg, 1, 10); E(bl, "c_fmsw")
    # the attenuation (0xFFFF = silent: not heard nor modulating, OL 0, the envelope at 0)
    imm32(0, 0xFFFF); E(mov_reg, 11, 0)
    E(ldrb_imm, 0, 6, A_USED); E(mov_reg, 1, 8); E(lsrs_reg, 0, 1); E(movs_imm, 2, 1); E(tst_reg, 0, 2); bc("op_aw", "eq")
    E(mov_reg, 1, 9); E(ldrb_imm, 2, 1, O_OL); E(cmp_imm, 2, 0); bc("op_aw", "eq")
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 2); E(raw, ldr_reg(0, 4, 0)); E(lsrs_imm, 0, 0, 8); E(cmp_imm, 0, 0); bc("op_aw", "eq")
    imm32(3, EMAX); E(subs_reg, 3, 3, 0)
    E(movs_imm, 0, 99); E(subs_reg, 0, 0, 2); E(lsls_imm, 0, 0, 5); E(adds_reg, 3, 3, 0)
    E(ldrb_imm, 0, 1, O_KVS); E(ldr_imm, 2, 7, C_VELA); E(muls, 0, 2); E(lsrs_imm, 0, 0, 5); E(adds_reg, 3, 3, 0)
    E(ldrb_w, 0, 4, V_NOTE); E(ldrb_imm, 2, 1, O_BP); E(adds_imm8, 2, 21); E(subs_reg, 0, 0, 2); E(b_cond, "op_ls", "eq")
    E(b_cond, "op_lr", "gt"); E(raw, negs(0, 0)); E(ldrb_imm, 2, 1, O_LD); E(b, "op_lm")
    lab("op_lr"); E(ldrb_imm, 2, 1, O_RD)
    lab("op_lm"); E(muls, 0, 2); E(movs_imm, 2, LS_K); E(muls, 0, 2); E(lsrs_imm, 0, 0, 4); E(adds_reg, 3, 3, 0)
    lab("op_ls"); E(mov_reg, 11, 3)
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 4); E(ldrh_imm, 1, 0, V_LAST); E(subs_reg, 1, 3, 1); E(b_cond, "op_ab", "ge"); E(raw, negs(1, 1))
    lab("op_ab"); E(cmp_imm, 1, THR); E(b_cond, "op_aw", "hs")                          # moved less than THR while moving: not sent again
    E(mov_reg, 0, 8); E(adds_reg, 0, 0, 4); E(ldrb_w, 0, 0, V_ST); E(cmp_imm, 0, 4); bc("op_nx", "lo")
    lab("op_aw")
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 4); E(mov_reg, 1, 11); E(strh_imm, 1, 0, V_LAST)
    imm32(1, 0xFFFF); E(mov_reg, 0, 11); E(cmp_reg, 0, 1); E(b_cond, "op_a0", "eq")
    E(bl, "c_fmamp")
    E(ldr_imm, 1, 7, C_INC); E(mov_reg, 2, 10); E(raw, umull(1, 3, 1, 2)); E(lsrs_imm, 1, 1, 16); E(lsls_imm, 3, 3, 16); E(orrs_reg, 1, 3)
    imm32(2, FE.NY); E(cmp_reg, 1, 2); E(b_cond, "op_a0", "hs")                          # f = inc x R >> 16 past 0.45 fs: muted
    E(ldrb_imm, 2, 6, A_CAR); E(mov_reg, 3, 8); E(lsrs_reg, 2, 3); E(movs_imm, 3, 1); E(tst_reg, 2, 3); E(b_cond, "op_a1", "ne")
    E(ldr_imm, 2, 7, C_G); E(muls, 0, 2); E(lsrs_imm, 0, 0, 8); c.clamp24(0, 2)        # a modulator: x G, its index capped
    E(lsrs_imm, 2, 1, 11); E(b_cond, "op_a1", "eq")
    imm32(3, FE.NY); E(subs_reg, 3, 3, 1); E(lsrs_imm, 3, 3, 11); imm32(1, FE.AACAP); E(muls, 3, 1); E(raw, udiv(3, 3, 2))
    E(cmp_reg, 0, 3); E(b_cond, "op_a1", "ls"); E(mov_reg, 0, 3); E(b, "op_a1")
    lab("op_a0"); E(movs_imm, 0, 0)
    lab("op_a1"); E(mov_reg, 1, 0); E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 4); E(adds_imm8, 0, VD.F_AMP); E(bl, "c_fmsw")
    lab("op_nx"); E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(ldr_imm, 1, 7, C_N); E(cmp_reg, 0, 1); bc("op_l", "lo")
    # ---- the noise: noise^2 x 4 x the noise operator's envelope (0..32767) >> 9
    E(ldrb_w, 0, 5, GLB + G_NZOP); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 2); E(raw, ldr_reg(0, 4, 0)); E(lsrs_imm, 0, 0, 8)
    E(movs_imm, 1, 0); E(mov_reg, 9, 1); E(cmp_imm, 0, 0); E(b_cond, "nz_w", "eq")
    imm32(1, EMAX); E(subs_reg, 0, 1, 0); E(bl, "c_fmexp"); E(lsrs_imm, 0, 0, 1)
    E(ldrb_w, 1, 5, GLB + G_NZ); E(muls, 1, 1); E(lsls_imm, 1, 1, 2); E(muls, 0, 1); E(lsrs_imm, 0, 0, 9); E(mov_reg, 9, 0)
    lab("nz_w")
    E(ldr_imm, 0, 7, C_NZ); E(cmp_imm, 0, 0); E(b_cond, "nz_a", "ne"); E(ldr_imm, 0, 7, C_TRK); E(movs_imm, 1, VD.NZ_OFF); E(bl, "c_fmosc")
    lab("nz_a"); E(mov_reg, 1, 9); E(ldr_imm, 2, 4, V_NZL); E(cmp_reg, 1, 2); E(b_cond, "nz_s", "eq"); E(str_imm, 1, 4, V_NZL); E(bl, "c_fmw")
    lab("nz_s")
    # ---- the feedback (every tick: G moves it): M[d][s] (twice a self feedback's half for a loop), HC of a self feedback
    E(ldrb_imm, 0, 6, A_FBS); E(cmp_imm, 0, 7); E(b_cond, "fb_x", "hi")
    E(ldrb_imm, 1, 6, A_FBD); E(lsls_imm, 1, 1, 4); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, VD.F8_M); E(ldr_imm, 1, 7, C_FB)
    E(ldrb_imm, 2, 6, A_FBS); E(ldrb_imm, 3, 6, A_FBD); E(cmp_reg, 2, 3); E(b_cond, "fb_s", "eq"); E(lsls_imm, 1, 1, 1); c.clamp24(1, 2)
    lab("fb_s"); E(bl, "c_fmsw")
    E(ldrb_imm, 2, 6, A_FBS); E(ldrb_imm, 3, 6, A_FBD); E(cmp_reg, 2, 3); E(b_cond, "fb_x", "ne")
    E(lsls_imm, 0, 3, 4); E(adds_imm8, 0, VD.F8_HC); E(ldr_imm, 1, 7, C_FB); E(bl, "c_fmsw")
    lab("fb_x")
    # ---- the routing: K, M1..M_N, HC of the N operators and N (dirty: the block's or the voice's; or every 64 ticks), then the flag
    E(ldrb_w, 0, 4, V_CNT); E(adds_imm8, 0, 1); E(strb_w, 0, 4, V_CNT); E(movs_imm, 1, 63); E(tst_reg, 0, 1); E(b_cond, "rt_go", "eq")
    E(ldrb_w, 0, 4, V_DIRTY); E(ldrb_w, 1, 5, B_DIRTY); E(orrs_reg, 0, 1); E(cmp_imm, 0, 0); bc("rn_x", "eq")
    lab("rt_go")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, V_DIRTY)
    E(ldrb_imm, 0, 6, A_CAR); E(movs_imm, 1, 0)                                           # r1 = the carriers
    lab("rt_pc"); E(cmp_imm, 0, 0); E(b_cond, "rt_pd", "eq"); E(lsrs_imm, 0, 0, 1); E(b_cond, "rt_pc", "cc"); E(adds_imm8, 1, 1); E(b, "rt_pc")
    lab("rt_pd"); E(cmp_imm, 1, 0); E(b_cond, "rt_p1", "ne"); E(movs_imm, 1, 1)
    lab("rt_p1"); imm32(0, KW_CAR); E(raw, udiv(0, 0, 1)); E(mov_reg, 11, 0)
    E(movs_imm, 0, 0); E(mov_reg, 8, 0)
    lab("rt_k")
    E(movs_imm, 1, 0); E(ldrb_imm, 2, 6, A_CAR); E(mov_reg, 0, 8); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(tst_reg, 2, 3); E(b_cond, "rt_kw", "eq")
    E(mov_reg, 1, 11)
    lab("rt_kw"); E(lsls_imm, 0, 0, 4); E(adds_imm8, 0, VD.F_K); E(bl, "c_fmsw")
    E(movs_imm, 0, 0); E(mov_reg, 9, 0)
    lab("rt_m")
    E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 3); E(mov_reg, 1, 9); E(adds_reg, 0, 0, 1)        # bit 8 k + j: j modulates k
    E(movs_imm, 2, A_MASK); E(cmp_imm, 0, 32); E(b_cond, "rt_lo", "lo"); E(subs_imm8, 0, 32); E(movs_imm, 2, A_MASK + 4)
    lab("rt_lo"); E(raw, ldr_reg(2, 6, 2)); E(lsrs_reg, 2, 0); E(movs_imm, 3, 1); E(movs_imm, 1, 0); E(tst_reg, 2, 3); E(b_cond, "rt_fb", "eq")
    imm32(1, M_FULL)
    lab("rt_fb")
    E(ldrb_imm, 2, 6, A_FBD); E(cmp_reg, 2, 8); E(b_cond, "rt_mw", "ne"); E(ldrb_imm, 2, 6, A_FBS); E(cmp_reg, 2, 9); E(b_cond, "rt_mw", "ne")
    E(ldr_imm, 1, 7, C_FB); E(ldrb_imm, 3, 6, A_FBD); E(cmp_reg, 2, 3); E(b_cond, "rt_mw", "eq"); E(lsls_imm, 1, 1, 1); c.clamp24(1, 2)
    lab("rt_mw"); E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 4); E(mov_reg, 2, 9); E(adds_reg, 0, 0, 2); E(adds_imm8, 0, VD.F8_M); E(bl, "c_fmsw")
    E(mov_reg, 0, 9); E(adds_imm8, 0, 1); E(mov_reg, 9, 0); E(ldr_imm, 1, 7, C_N); E(cmp_reg, 0, 1); E(b_cond, "rt_m", "lo")
    E(movs_imm, 1, 0); E(ldrb_imm, 2, 6, A_FBD); E(cmp_reg, 2, 8); E(b_cond, "rt_h", "ne"); E(ldrb_imm, 3, 6, A_FBS); E(cmp_reg, 2, 3); E(b_cond, "rt_h", "ne")
    E(ldr_imm, 1, 7, C_FB)
    lab("rt_h"); E(mov_reg, 0, 8); E(lsls_imm, 0, 0, 4); E(adds_imm8, 0, VD.F8_HC); E(bl, "c_fmsw")
    E(mov_reg, 0, 8); E(adds_imm8, 0, 1); E(mov_reg, 8, 0); E(ldr_imm, 1, 7, C_N); E(cmp_reg, 0, 1); bc("rt_k", "lo")
    E(movs_imm, 0, VD.F8_N); E(ldr_imm, 1, 7, C_N); E(bl, "c_fmsw")
    E(ldr_imm, 0, 7, C_TRK); E(movs_imm, 1, VD.FM_FLAG); E(bl, "c_fmosc"); E(movs_imm, 1, 1); E(bl, "c_fmw")
    lab("rn_x")
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)

    # ---- c_fmctx(r0 = slot address, r1 = track, r2 = increment (0: read), r3 = the noise's address (0: OSC1's)): the context (gate, dt and poly
    #      written by the caller)
    lab("c_fmctx")
    imm32(12, CTX8)
    E(raw, str_w(0, 12, C_SLOT)); E(raw, str_w(1, 12, C_TRK)); E(raw, str_w(2, 12, C_INC)); E(raw, str_w(3, 12, C_NZ)); E(raw, RET)

    # ---- c_fmflag(r0 = track, r1 = 0 / 1): the OSC1 block's flag word, when it changes (B_SENT); clobbers r0-r3
    lab("c_fmflag")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_fmblk"); E(mov_reg, 6, 0); E(ldrb_w, 0, 6, B_SENT); E(cmp_reg, 0, 5); E(b_cond, "fl_x", "eq")
    E(strb_w, 5, 6, B_SENT); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY)
    E(mov_reg, 0, 4); E(movs_imm, 1, VD.FM_FLAG); E(bl, "c_fmosc"); E(mov_reg, 1, 5); E(bl, "c_fmw")
    lab("fl_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_fmz8(r0 = the slot's address): the DSP's smoothed AMP and y[n - 2] of the 8 operators 0; clobbers r0-r3
    lab("c_fmz8")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(movs_imm, 5, 0)
    lab("z8_l"); E(lsls_imm, 0, 5, 4); E(adds_reg, 0, 0, 4); E(adds_imm8, 0, VD.F8_AS); E(movs_imm, 1, 0); E(bl, "c_fmw")
    E(lsls_imm, 0, 5, 4); E(adds_reg, 0, 0, 4); E(adds_imm8, 0, VD.F8_O2); E(movs_imm, 1, 0); E(bl, "c_fmw")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "z8_l", "lo")
    E(pop_list, [4, 5], pc=True)

    # ---- c_fmtick: the head of the DSP service chain (the tick holds the DSP semaphore: RAM and DSP writes / reads only, no MARK_DIRTY)
    lab("c_fmtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    E(bl, "c_fmref")
    E(movs_imm, 7, 0)
    lab("tk_l")
    E(mov_reg, 0, 7); E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "tk_on", "ne")
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_fmflag")
    E(mov_reg, 0, 7); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_P7)
    E(mov_reg, 0, 7); E(bl, L["c_vpage"]); E(cmp_imm, 0, FE.PAGE); bc("tk_n", "ne")      # the FM page without FM: back to OSC 1
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_vsetpage"]); E(b, "tk_n")
    lab("tk_on")
    E(mov_reg, 0, 7); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(mov_reg, 0, 7); E(bl, "c_fmvs"); E(mov_reg, 5, 0)
    E(ldrb_w, 0, 4, B_SENT); E(cmp_imm, 0, 1); E(b_cond, "tk_e", "eq")
    E(mov_reg, 0, 5); E(bl, "c_fmvz"); E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY)       # off -> on: the voice silent, the DSP's states 0
    E(lsls_imm, 0, 7, 7); imm32(1, VD.FMB0); E(adds_reg, 0, 0, 1); E(bl, "c_fmz8")
    lab("tk_e")
    c.now(0); E(ldr_imm, 1, 5, V_T); E(subs_reg, 6, 0, 1); bc("tk_n", "eq"); E(str_imm, 0, 5, V_T)
    E(cmp_imm, 6, 50); E(b_cond, "tk_dt", "ls"); E(movs_imm, 6, 50)
    lab("tk_dt")
    import poly as PL                                                                    # the track in poly: its voices are poly's (the flag still)
    imm32(0, PL.PY); E(ldr_imm, 1, 0, 0); imm32(2, PL.SIG); E(cmp_reg, 1, 2); E(b_cond, "tk_np", "ne")
    E(adds_imm8, 0, 4 + PL.O_ACT); E(lsls_imm, 1, 7, PL.TBS.bit_length() - 1); E(ldrb_reg, 0, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "tk_np", "eq")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_fmflag"); E(b, "tk_n")
    lab("tk_np")
    E(movs_imm, 0, 1); E(ldrb_w, 1, 5, V_NEW); E(cmp_imm, 1, 0); E(b_cond, "tk_gs", "ne")  # the gate: a new note, or the engine's held notes
    imm32(0, V.TAIL + V.O_RT + V.RT_CNT); E(lsls_imm, 1, 7, 3); E(ldrb_reg, 0, 0, 1); E(movs_imm, 1, 15); E(ands_reg, 0, 1)
    E(cmp_imm, 0, 0); E(b_cond, "tk_gs", "eq"); E(movs_imm, 0, 1)
    lab("tk_gs")
    imm32(3, CTX8); E(str_imm, 0, 3, C_GATE); E(str_imm, 6, 3, C_DT); E(movs_imm, 0, 0); E(str_imm, 0, 3, C_POLY)
    E(lsls_imm, 0, 7, 7); imm32(1, VD.FMB0); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 7); E(movs_imm, 2, 0); E(movs_imm, 3, 0); E(bl, "c_fmctx")
    E(mov_reg, 0, 5); E(mov_reg, 1, 4); E(bl, "c_fm8run")
    E(movs_imm, 0, 0); E(strb_w, 0, 4, B_DIRTY)
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_fmflag")
    lab("tk_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 2); bc("tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["svc"])

    # ---- c_fmnon (the note vtable's slot: this, track id, note, velocity): a new note (legato with the retrigger off: only the note)
    lab("c_fmnon")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(mov_reg, 4, 1); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc("nn_x", "hi")
    E(cmp_imm, 3, 0); bc("nn_x", "eq"); E(mov_reg, 5, 3)
    E(mov_reg, 0, 4); E(bl, L["c_rtoff"]); E(cmp_imm, 0, 0); E(b_cond, "nn_n", "eq")
    imm32(0, V.TAIL + V.O_RT); E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, V.RT_CNT); E(lsls_imm, 1, 1, 28); E(b_cond, "nn_n", "eq")
    E(ldrb_imm, 1, 0, V.RT_VEL); E(lsls_imm, 1, 1, 24); E(b_cond, "nn_n", "mi")
    E(mov_reg, 0, 4); E(bl, "c_fmvs"); E(ldr_sp, 1, 8); E(strb_w, 1, 0, V_NOTE); E(b, "nn_x")    # ldr r1, [sp, #8]
    lab("nn_n")
    E(mov_reg, 0, 4); E(bl, "c_fmvs"); E(strb_w, 5, 0, V_VEL); E(movs_imm, 1, 1); E(strb_w, 1, 0, V_NEW); E(ldr_sp, 1, 8); E(strb_w, 1, 0, V_NOTE)
    lab("nn_x")
    E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["non"])

    # ---- c_fm8poly (poly's c_pyfm1: r0 = slot, r1 = the voice's RAM, r2 = voice, r3 = 1: not its tick, r4 = track, r9 = the track's block,
    #      r10 = now): a new TRIG while sounding = a new note; every second tick (a new one at once) the voice's run; let go and quiet: freed
    lab("c_fm8poly")
    import poly as PL
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 5, 0); E(mov_reg, 6, 1); E(mov_reg, 8, 3); E(mov_reg, 11, 2)               # r5 slot, r6 RAM, r8 not its tick, r11 voice
    imm32(7, FM8R + VP0); E(lsls_imm, 0, 5, 7); E(adds_reg, 7, 7, 0)                      # r7 = the slot's voice
    E(bl, "c_fmst")
    E(ldrb_imm, 2, 6, PL.VS); E(ldrh_imm, 3, 6, PL.VG); E(raw, ldrh_w(0, 7, V_SEEN)); E(movs_imm, 1, 0); E(cmp_reg, 0, 3); E(b_cond, "py_o", "eq")
    E(raw, strh_w(3, 7, V_SEEN)); E(movs_imm, 0, PL.SND); E(tst_reg, 2, 0); E(b_cond, "py_o", "eq"); E(movs_imm, 1, 1)
    lab("py_o"); E(push_list, [1, 2])                                                    # [sp] new, [sp + 4] state
    E(cmp_imm, 1, 0); E(b_cond, "py_g", "ne")
    E(movs_imm, 0, PL.SND); E(tst_reg, 2, 0); bc("py_x", "eq")                           # not sounding: nothing
    E(mov_reg, 0, 8); E(cmp_imm, 0, 0); bc("py_x", "ne")                                 # not its tick
    lab("py_g")
    E(ldr_imm, 0, 7, V_T); E(mov_reg, 1, 10); E(str_imm, 1, 7, V_T); E(subs_reg, 0, 1, 0)
    E(cmp_imm, 0, 50); E(b_cond, "py_d", "ls"); E(movs_imm, 0, 50)
    lab("py_d"); E(cmp_imm, 0, 0); E(b_cond, "py_d1", "eq"); E(ldr_sp, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "py_d2", "eq")
    lab("py_d1"); E(movs_imm, 0, 1)
    lab("py_d2"); E(mov_reg, 8, 0)                                                       # r8 = dt
    E(ldrb_imm, 0, 6, PL.VN); E(strb_w, 0, 7, V_NOTE)
    E(ldr_sp, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "py_n", "eq")                            # a new note: its velocity, the stages from 1
    E(ldrb_imm, 0, 6, PL.VV); E(strb_w, 0, 7, V_VEL); E(movs_imm, 0, 1); E(strb_w, 0, 7, V_NEW)
    E(ldrb_w, 0, 7, V_USE); E(cmp_imm, 0, 0); E(b_cond, "py_n", "ne"); E(movs_imm, 0, 1); E(strb_w, 0, 7, V_USE)     # the slot's first use
    E(lsls_imm, 0, 5, 7); imm32(1, VD.FV0); E(adds_reg, 0, 0, 1); E(bl, "c_fmz8")
    lab("py_n")
    E(movs_imm, 0, 1); E(ldr_sp, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "py_gt", "ne")        # the gate: new, or held
    E(ldr_sp, 1, 4); E(movs_imm, 2, PL.HELD); E(tst_reg, 1, 2); E(b_cond, "py_gt", "ne"); E(movs_imm, 0, 0)
    lab("py_gt")
    imm32(3, CTX8); E(str_imm, 0, 3, C_GATE); E(mov_reg, 0, 8); E(str_imm, 0, 3, C_DT); E(movs_imm, 0, 1); E(str_imm, 0, 3, C_POLY)
    E(ldrb_w, 2, 7, V_NOTE); E(lsls_imm, 2, 2, 2); imm32(1, T["inc"]); E(raw, ldr_reg(2, 1, 2))      # r2 = its increment
    E(movs_imm, 3, VD.PV_N); E(muls, 3, 4)
    E(mov_reg, 0, 11); E(adds_reg, 3, 3, 0); E(movs_imm, 0, VD.PV_RS); E(muls, 3, 0); imm32(0, VD.PV_REC0 + VD.NZ_OFF - 28); E(adds_reg, 3, 3, 0)   # its noise
    E(lsls_imm, 0, 5, 7); imm32(1, VD.FV0); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 4); E(bl, "c_fmctx")
    E(mov_reg, 0, 7); E(mov_reg, 1, 9); E(bl, "c_fm8run")
    E(ldr_sp, 0, 0); E(cmp_imm, 0, 0); bc("py_x", "ne")                                  # let go and its envelopes down: freed
    E(ldr_sp, 0, 4); E(movs_imm, 1, PL.HELD | PL.PEND); E(tst_reg, 0, 1); bc("py_x", "ne")
    E(mov_reg, 0, 9); E(bl, "c_fmalg"); E(ldrb_imm, 0, 0, A_USED); E(movs_imm, 1, 0)         # the operators the algorithm uses
    lab("py_e"); E(lsrs_imm, 0, 0, 1); E(b_cond, "py_en", "cc")
    E(lsls_imm, 2, 1, 2); E(raw, ldr_reg(2, 7, 2)); E(lsrs_imm, 2, 2, 8); imm32(3, E_OFF); E(cmp_reg, 2, 3); bc("py_x", "hs")
    lab("py_en"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, "py_e", "lo")
    E(mov_reg, 1, 6); E(raw, MRS7); E(raw, CPSID)
    E(ldrb_imm, 0, 1, PL.VS); E(movs_imm, 2, PL.HELD | PL.PEND); E(tst_reg, 0, 2); E(b_cond, "py_f", "ne")
    E(movs_imm, 2, PL.SND); E(raw, bics(0, 2)); E(movs_imm, 2, PL.DIRTY); E(orrs_reg, 0, 2); E(strb_imm, 0, 1, PL.VS); E(movs_imm, 0, 0); E(strb_imm, 0, 1, PL.VO)
    lab("py_f"); E(raw, MSR7)
    lab("py_x"); E(raw, h(0xB002)); E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)    # add sp, #8

    # ---- c_fmloud(r0 = slot) -> r0 = its voice's loudness (the sum of the 8 operators' e, < 0x20000: poly's shed); clobbers r1-r3
    lab("c_fmloud")
    imm32(1, FM8R + VP0); E(lsls_imm, 0, 0, 7); E(adds_reg, 1, 1, 0); E(movs_imm, 0, 0); E(movs_imm, 2, 8)
    lab("ld_l"); E(ldr_imm, 3, 1, 0); E(lsrs_imm, 3, 3, 8); E(adds_reg, 0, 0, 3); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "ld_l", "ne")
    E(raw, RET)


def build(base, L, prev, ui=None):
    """-> (code, labels, T): the tables, the engine and (ui(c, T, L, prev)) the panel."""
    c = Ctx(base); T = {}
    import fm8ui
    c.E(raw, data(c, T, fm8ui.tables() if ui else ()))
    engine(c, T, L, prev)
    if ui: ui(c, T, L, prev)
    code, labels = c.a.assemble()
    return code, labels, T
