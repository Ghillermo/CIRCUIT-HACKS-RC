"""The panel of the 8-operator FM (fm8arm's engine): the FM page's knobs, the operator pads, the LEDs, the overlays, the starters, the old
patches' conversion (c_fm8conv = fm8.convert4 byte for byte) and the patch hooks.

The FM page = pad 7 of the MIDI 1 / 2 Preset view (vcf21's page 6), with FM on (pad 24 of the engine row).  Pads 9-16 pick operator 1-8 (the
ones the algorithm uses lit: carriers green, modulators light blue, the picked one bright), pad 17 the pitch envelope (amber).  The knobs (the user,
2026-11-04: «Rates / levels split»):
  an operator:          K1 ratio (coarse 0.5, 1..31, then fixed 1 / 10 / 100 / 1000 Hz; 3 clicks a step), K2 fine (0..99), K3 output level (0..99),
                        K4 velocity sensitivity (0..7, 4 clicks), K5-K8 rates R1-R4 (0..99);
                Shift:  K1 algorithm (48: the 4-operator engine's 16, then the DX7's 32; 16 clicks, the type knobs' rule), K2 feedback (0..127), K3 rate scaling (0..7),
                        K4 level scaling (centre 0: right = higher notes softer, left = lower notes softer), K5-K8 levels L1-L4 (0..99);
  the pitch envelope:   K1 transpose (0..48, 24 = none; 2 clicks), K3 noise (0..127), K4 the noise's operator (1-8, 16 clicks), K5-K8 R1-R4; Shift: K1 / K2 as
                        above, K5-K8 L1-L4 (50 = no shift).
Clear + knob = the default (the converted 4-operator defaults); Clear + pad 7 = the algorithm's voicing; pad 7 held = the 4-operator engine's 16
algorithms on pads 9-24; Shift + K1 turning shows the algorithms 1.5 s (the old 16 on pads 9-24, the DX7's 32 on pads 1-32); pad 8 held = the 16
starters on pads 9-24."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fm8 as F  # noqa: E402
import fm8store as FS  # noqa: E402
from fm8arm import (B_ON, B_DIRTY, B_SEL, B_P7, B_OVK, B_STR, B_OVT, B_LEDT, B_KID, ldr_reg, udiv, negs, popw, pushw, RET)  # noqa: E402
import fmeng as FE  # noqa: E402
import vcf21 as V  # noqa: E402
import modesel as MS  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
from thumb import (adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   ldrh_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, muls, orrs_reg, pop_list, push_list, raw, str_imm,
                   strb_imm, strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg, tst_reg, ldr_sp, lsrs_reg, eors_reg)

PAGE, PADNO, ROWPAD = FE.PAGE, FE.PADNO, FE.ROWPAD
COL_CAR, COL_MOD, COL_PEG = (0x17, 0x18), (0x13, 0x14), (0x2B, 0x2C)
COL_FIX = 0x53
K_ABS, K_OP, K_CMB, K_LS, K_NONE = 0, 1, 2, 3, 4
POFS, PLEN_OLD = FE.POFS, FE.PLEN
# the knobs' descriptors: (offset, max, clicks | kind << 4, colour); [0] an operator, [1] the pitch envelope; 0..7 plain, 8..15 with Shift
FB_D = (F.GLB + F.G_FB, 127, 1 | K_ABS << 4, FE.COL_FB)
NONE = (0, 1, 1 | K_NONE << 4, 0)


def make_kd():
  global ALG_D, KD, DXDEF
  ALG_D = (F.GLB + F.G_ALG, F.NALG - 1, 0 | K_ABS << 4, 0x01)          # (clicks 0 = 16: a type knob, vcf21.use_kslow's rule)
  KD = [
    [(F.O_MODE, 35, 3 | K_CMB << 4, 0x17), (F.O_FINE, 99, 1 | K_OP << 4, 0x13), (F.O_OL, 99, 1 | K_OP << 4, FE.COL_LEV), (F.O_KVS, 7, 4 | K_OP << 4, 0x49)]
    + [(F.O_R + i, 99, 1 | K_OP << 4, 0x2B) for i in range(4)]
    + [ALG_D, FB_D, (F.O_RS, 7, 4 | K_OP << 4, 0x4D), (F.O_LD, 99, 1 | K_LS << 4, 0x13)]
    + [(F.O_L + i, 99, 1 | K_OP << 4, 0x01) for i in range(4)],
    [(F.GLB + F.G_TRN, 48, 2 | K_ABS << 4, 0x01), NONE, (F.GLB + F.G_NZ, 127, 1 | K_ABS << 4, FE.COL_NZ), (F.GLB + F.G_NZOP, 7, 0 | K_ABS << 4, 0x4D)]
    + [(F.O_R + i, 99, 1 | K_OP << 4, 0x2B) for i in range(4)]
    + [ALG_D, FB_D, NONE, NONE] + [(F.O_L + i, 99, 1 | K_OP << 4, 0x01) for i in range(4)],
  ]
  assert all(len(p) == 16 for p in KD)
  DXDEF = bytearray(F.DEFAULT)                                         # Clear + pad 7 on a DX7 algorithm: six operators (eight with use_alg8), ratio 1, held
  for _k in range(8 if F.ALG8 else 6):
      _b = F.OPB * _k
      DXDEF[_b:_b + F.OPB] = F.op_default(_k)
      DXDEF[_b + F.O_OL] = 99 if _k == 0 else 72
  DXDEF = bytes(DXDEF)


make_kd()
ALGF = bytes(b_ for x in F.OLD_DEF for b_ in (x[3], x[4] - 1))         # the old algorithms' pitch flag and noise operator
ROF = bytes(v & 0xFF for x in F.OLD_DEF for v in x[7])
FAMW = FE.FAM_COL[0] | FE.FAM_COL[1] << 8 | FE.FAM_COL[2] << 16 | FE.FAM_COL[3] << 24


HEADS = False                                                          # SC51.8 (use_heads)
V2 = False                                                             # SC51.8 (use_v2)
B_APG = 233                                                            # (V2) a track block: the page of pad 7's list
B_IPG = 234                                                            # (INST2) a track block: the page of pad 8's list
INST2 = False                                                          # (use_inst2)
IT_SIG, IT_TAB = 0x100, 0x104                                          # (INST2) the ITCM: the table's stamp, the 48 instruments unpacked


def use_inst2():
    """SC53 (the user, 2026-11-07: «Pon algunos parches demo del FM más largos, como strings y winds, también algún piano»; «Segunda página con
    Octave»): pad 8 held = the instruments' page 1 / 2 with Octave down / up (as pad 7's pages; lit when there is another page); page 2 = fm8inst's
    INST2 (pianos, strings, winds, long ones), page 1 the 24 with longer releases (fm8inst.use_v2).  The 48 records (6 048 B) are kept packed
    (fm8inst.lz, 2.3 KB: less than the 24 raw ones) and unpacked once into the ITCM (0x104, free: S494D2; dspz's window starts at 0x2000) by
    c_fminst the first time it is asked for an instrument (the stamp at 0x100 = the packed table's CRC: another build unpacks again)."""
    global INST2
    import fm8inst as FI
    FI.use_v2()
    INST2 = True
WTCOL = False                                                          # SC52.6 (the user: «Los parches de wt deben guardarse en sand, no verde»): a wavetable patch's slot in sand
ENGC = 0x2004E480                                                      # (V2) the engines of the 16 patch slots of mpatch's page (after fm8store's KEEP)
OCT_UP, OCT_DN = 52, 51


def use_v2():
    """SC51.8 / Beta 5.21, the user (2026-11-05), on Beta 5.20 in the device:
      * «classify like the original: Algos on pad 7, Instruments on pad 8» -> «Pages on Octave»: pad 7 held = the 56 algorithms on pads 9-32, 24 a
        page, Octave down / up while it is held (page 1: the 16 four-operator ones, then the 8 eight-operator ones; page 2: the DX7's 1-24; page 3: its
        25-32); colour = the operators: teal 4, white 6 (the DX7's), amber 8; the current one bright;
      * «A lot of pads are just bells? add more interesting instruments instead. Also give pads color for their type» -> «24 on pads 9-32», «Track-style
        palette»: pad 8 held = fm8inst's 24 instruments (keys orange, bass blue, leads red, pads green, plucks yellow, percussion white, bells / fx
        violet);
      * «The operator selection display should not display saved patches on row 3»: on the FM page (the engine row closed) pads 18-24 dark, their
        presses swallowed;
      * «saved patches must retain their mode color» -> «Engine colour», «empty: grey (dim white)»: mpatch's slots in their engine's colour (the
        engine row's, FM violet), bright = the last loaded; the empty ones dim white (psave's violet = FM's).
    With use_heads, use_nodual and fm8.use_alg8."""
    global V2
    V2 = True
    use_heads(); use_nodual()
    if not F.ALG8: F.use_alg8()
    FS.OCT = True
NODUAL = False                                                         # SC51.8 (use_nodual)
PEG3 = False                                                           # SC51.9 (use_peg3)
ROWOP = False                                                          # SC52 (use_rowop)


def use_rowop():
    """SC52 / Beta 5.23 (the user, 2026-11-05: «restore row 3 (voice modes) on operator selection view» -> «Engine mode (osc, fm, granular....)»): on
    the FM page with the engine row closed, pads 17-24 show modesel's engine row (dim, FM bright) and a tap picks that engine: the row is opened
    for this track around the press (modesel's RAM), FM goes off for any pad but 24, and the chain below (modesel) picks the mode; then it closes.
    And («pad 7 stays lit after I choose my algorithm, make it dim after selection/not pressed»): pad 7 bright only while held, dim otherwise."""
    global ROWOP
    assert PEG3 and MS.ROW2
    ROWOP = True


def use_peg3():
    """SC51.9 / Beta 5.22 (the user, 2026-11-05: «why is pad 17 yellow?» -> «put it on pad 3, purple (fm) color»): the pitch envelope moves from pad 17
    to pad 3 (the OSC 2 page's pad, dark with FM since use_nodual): with FM on, pad 3 = the FM page with the pitch envelope picked, in FM's violet
    (dim; bright while it is the one the knobs move); pad 17 joins the dark pads 18-24 of the operator page."""
    global PEG3
    assert V2
    PEG3 = True


def use_nodual():
    """SC51.8 / Beta 5.21 (the user, 2026-11-05: «the 2osc pad (28) is available on FM modes (and a second osc view displays) does this pad do anything
    on FM?» -> «Unlit, no effect»): the DSP takes the FM path before the two oscillators' flag, so with FM on pad 28 and the OSC 2 page (pad 3) did
    nothing, and a second note held went to OSC 2 (not heard).  With FM on: vcf21's c_vosc = 0 (pad 28 dark and ignored, its bit kept), pad 3 dark and
    ignored, and the note-on's paraphony reads the bit as 0 (c_f8dual at vcf21's no_dt)."""
    global NODUAL
    NODUAL = True


def use_heads():
    """SC51.8 / Beta 5.21 (the user, 2026-11-05: «when the operator selection (row2) is disabled, i cannot see fm presets on pad 8 menu row2 (only row3
    shows)»): jumpflip (SC51.6) sits ahead of this panel in slots 0 / 7 of the template view and, with the engine row open or a flip mode on, darkens
    pads 9-16 and swallows their presses.  Now two heads ahead of jumpflip: while the pad 7 / 8 list or the algorithms are shown on the FM page, pads
    9-24 go to c_fmpad and the list is painted again over jumpflip's LEDs."""
    global HEADS
    HEADS = True


def tables():
    return [("kd", bytes(v for page in KD for e in page for v in e)), ("rat", struct.pack("<24H", *F.RAT256)),
            ("det", struct.pack("<64H", *[v for row in F.DET4096 for v in row])), ("olt", bytes(F.OLT)), ("atk2r", bytes(F.ATK2R)),
            ("rel2r", bytes(F.REL2R)), ("kvsa", bytes(F.KVS_ALG)), ("ksa", bytes(FE.KS)), ("susm", bytes(F.SUSM)), ("algf", ALGF), ("rof", ROF),
            ("opdef", F.op_default(4)), ("dxdef", DXDEF), ("voic", bytes(v for row in FE.VOICINGS for v in row)),
            ("strt", bytes(v for _, row in FE.STARTERS for v in row)), ("stc", bytes(c_ for f in FE.ST_OF for c_ in FE.ST_FAM[f])),
            ("fam", bytes(x["fam"] for x in FE.ALGS)), ("famc", bytes(c_ for pair in FE.FAMC for c_ in pair))] + (v2_tables() if V2 else [])


def v2_tables():
    import fm8inst as FI
    ecode = bytes(0 if not f & 1 else {1: 1, 3: 2, 7: 3, 15: 3, 11: 4, 9: 5, 5: 6, 13: 6}[f] for f in range(16))
    scol = bytes(c_ for pair in list(MS.COLS) + [FE.COL_FM] + ([(0x6D, 0x69)] if WTCOL else []) for c_ in pair)      # (WTCOL) 8 = the wavetable: sand
    out = [("inst", FI.lz(FI.table()) if INST2 else FI.table()), ("icol", FI.colours()), ("ecode", ecode), ("scol", scol)]
    if ROWOP:                                                                             # the engine row's 8 pads on the FM page: dim, FM bright
        out.append(("rowc", bytes([MS.COLS[m][1] if m != 0xFF else 0 for m in MS.ROWMODE] + [FE.COL_FM[0]])))
    return out


def ui(c, T, L, prev):
    E, imm32, bc, lab = c.E, c.imm32, c.bc, c.L
    def tb(rd, name, idx_reg=None):                                                    # rd = T[name] (+ idx_reg)
        imm32(rd, T[name])
        if idx_reg is not None: E(adds_reg, rd, rd, idx_reg)
    def clamp(r_, lo_label, hi, tmp=None):                                             # r_ = min(r_, hi) (unsigned, hi < 256)
        c.zc += 1; n = f"_m{c.zc}"; E(cmp_imm, r_, hi); E(b_cond, n, "ls"); E(movs_imm, r_, hi); lab(n)
    def copy(dst, src, n, tmp, cnt):                                                   # n bytes src -> dst (registers kept)
        c.zc += 1; m = f"_cp{c.zc}"; E(movs_imm, cnt, 0)
        lab(m); E(ldrb_reg, tmp, src, cnt); E(strb_reg, tmp, dst, cnt); E(adds_imm8, cnt, 1); E(cmp_imm, cnt, n); E(b_cond, m, "lo")

    # ---- c_fm8conv(r0 = the 4-operator engine's 16 parameters, r1 = a block): the 8-operator parameters (fm8.convert4)
    lab("c_fm8conv")
    E(raw, pushw([4, 5, 6, 7, 8, 9, 10, 11], lr=True))
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(movs_imm, 0, 0); E(movs_imm, 1, 0)
    lab("cv_z"); E(strb_reg, 0, 5, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, F.PLEN); E(b_cond, "cv_z", "lo")
    E(ldrb_imm, 6, 4, 12); E(lsrs_imm, 6, 6, 3); E(movs_imm, 0, 15); E(ands_reg, 6, 0)          # r6 = the algorithm
    E(movs_imm, 7, 0)
    lab("cv_k")
    E(movs_imm, 0, F.OPB); E(muls, 0, 7); E(adds_reg, 0, 0, 5); E(mov_reg, 8, 0)              # r8 = the operator's bytes
    # the ratio: x = RAT256[idx] x DET[alg][k] >> 8 -> coarse, fine; the detune from the fine step
    E(ldrb_reg, 0, 4, 7); E(movs_imm, 1, 24); E(muls, 0, 1); E(movs_imm, 1, 127); E(ands_reg, 1, 0); E(lsrs_imm, 0, 0, 7)
    E(movs_imm, 2, 171); E(muls, 1, 2); E(lsrs_imm, 1, 1, 12); E(movs_imm, 2, 3); E(muls, 1, 2); E(lsrs_imm, 1, 1, 1); E(adds_imm8, 1, 7)
    clamp(1, None, 14); E(mov_reg, 2, 8); E(strb_imm, 1, 2, F.O_DET)
    E(lsls_imm, 0, 0, 1); tb(1, "rat"); E(ldrh_reg, 0, 1, 0)
    E(lsls_imm, 1, 6, 2); E(adds_reg, 1, 1, 7); E(lsls_imm, 1, 1, 1); tb(2, "det"); E(ldrh_reg, 1, 2, 1); E(muls, 0, 1); E(lsrs_imm, 0, 0, 8)
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 12); E(cmp_reg, 0, 1); E(b_cond, "cv_c1", "hs")
    E(movs_imm, 2, 0); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 11); E(cmp_reg, 0, 1); E(b_cond, "cv_fw", "lo")       # coarse 0 (0.5)
    E(subs_reg, 0, 0, 1); E(movs_imm, 2, 100); E(muls, 0, 2); E(lsrs_imm, 2, 1, 1); E(adds_reg, 0, 0, 2); E(raw, udiv(0, 0, 1))
    E(mov_reg, 2, 0); E(movs_imm, 1, 0); E(b, "cv_fc")
    lab("cv_c1")
    E(lsrs_imm, 1, 0, 12); clamp(1, None, 31); E(lsls_imm, 2, 1, 12); E(subs_reg, 0, 0, 2); E(movs_imm, 3, 100); E(muls, 0, 3)
    E(lsrs_imm, 3, 2, 1); E(adds_reg, 0, 0, 3); E(raw, udiv(2, 0, 2))
    lab("cv_fc"); E(cmp_imm, 2, 99); E(b_cond, "cv_fs", "ls"); E(movs_imm, 2, 99)
    lab("cv_fs"); E(mov_reg, 0, 8); E(strb_imm, 1, 0, F.O_CRS); E(b, "cv_fx")
    lab("cv_fw"); E(movs_imm, 1, 0); E(mov_reg, 0, 8); E(strb_imm, 1, 0, F.O_CRS)
    lab("cv_fx"); E(mov_reg, 0, 8); E(strb_imm, 2, 0, F.O_FINE)
    # the output level (op 4 of a pitch algorithm: 0)
    E(adds_reg, 0, 4, 7); E(ldrb_imm, 0, 0, 4); E(movs_imm, 1, 127); E(ands_reg, 0, 1); tb(1, "olt"); E(ldrb_reg, 0, 1, 0)
    E(cmp_imm, 7, 3); E(b_cond, "cv_ol", "ne"); E(lsls_imm, 1, 6, 1); tb(2, "algf"); E(ldrb_reg, 1, 2, 1); E(cmp_imm, 1, 0); E(b_cond, "cv_ol", "eq"); E(movs_imm, 0, 0)
    lab("cv_ol"); E(mov_reg, 1, 8); E(strb_imm, 0, 1, F.O_OL)
    # the release rate r4 = REL2R[rel >> 1 + ROF[alg][k]] (r9)
    E(ldrb_imm, 0, 4, 15); E(lsrs_imm, 0, 0, 1); E(lsls_imm, 1, 6, 2); E(adds_reg, 1, 1, 7); tb(2, "rof"); E(ldrb_reg, 1, 2, 1)
    E(lsls_imm, 1, 1, 24); E(raw, h(0x1609)); E(adds_reg, 0, 0, 1)                         # asrs r1, r1, #24
    E(cmp_imm, 0, 0); E(b_cond, "cv_r0", "ge"); E(movs_imm, 0, 0)
    lab("cv_r0"); clamp(0, None, 63); tb(1, "rel2r"); E(ldrb_reg, 0, 1, 0); E(mov_reg, 9, 0)
    # the attack / percussive: r1 = R1, r2 = perc, r3 = rd
    E(adds_reg, 0, 4, 7); E(ldrb_imm, 0, 0, 8); E(cmp_imm, 0, FE.CENTRE); E(b_cond, "cv_pk", "lo")
    E(subs_imm8, 0, FE.CENTRE); E(lsrs_imm, 0, 0, 1); tb(1, "atk2r"); E(ldrb_reg, 1, 1, 0)
    tb(2, "susm"); E(ldrb_reg, 2, 2, 6); E(lsrs_reg, 2, 7); E(movs_imm, 0, 1); E(ands_reg, 2, 0); E(eors_reg, 2, 0)   # perc = !sus
    E(mov_reg, 3, 9); E(b, "cv_pw")
    lab("cv_pk"); tb(1, "rel2r"); E(ldrb_reg, 3, 1, 0); E(movs_imm, 1, 99); E(movs_imm, 2, 1)
    lab("cv_pw")
    E(mov_reg, 0, 8); E(strb_imm, 1, 0, F.O_R)
    E(movs_imm, 1, 99); E(strb_imm, 1, 0, F.O_R + 2); E(strb_imm, 1, 0, F.O_L)
    E(cmp_imm, 2, 0); E(b_cond, "cv_sus", "eq")
    E(strb_imm, 3, 0, F.O_R + 1); E(mov_reg, 1, 9); E(cmp_reg, 3, 1); E(b_cond, "cv_mn", "hs"); E(mov_reg, 1, 3)
    lab("cv_mn"); E(strb_imm, 1, 0, F.O_R + 3); E(b, "cv_lv")                              # L2 = L3 = L4 = 0
    lab("cv_sus"); E(movs_imm, 1, 99); E(strb_imm, 1, 0, F.O_R + 1); E(strb_imm, 1, 0, F.O_L + 1); E(strb_imm, 1, 0, F.O_L + 2)
    E(mov_reg, 1, 9); E(strb_imm, 1, 0, F.O_R + 3)
    lab("cv_lv")
    # a carrier: no velocity / scaling; a modulator: the algorithm's
    E(movs_imm, 1, 39); E(strb_imm, 1, 0, F.O_BP)
    tb(1, "ksa"); E(ldrb_reg, 1, 1, 6); clamp(1, None, 7); E(strb_imm, 1, 0, F.O_RS)
    E(lsls_imm, 1, 6, 4); imm32(2, T["algs"] + F.A_CAR); E(ldrb_reg, 1, 2, 1); E(lsrs_reg, 1, 7); E(movs_imm, 2, 1); E(tst_reg, 1, 2)
    E(b_cond, "cv_nx", "ne")
    tb(1, "kvsa"); E(ldrb_reg, 1, 1, 6); E(strb_imm, 1, 0, F.O_KVS)
    tb(1, "ksa"); E(ldrb_reg, 1, 1, 6); E(lsls_imm, 1, 1, 2); clamp(1, None, 99); E(strb_imm, 1, 0, F.O_RD)
    lab("cv_nx"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); bc("cv_k", "lo")
    # operators 5-8: silent, ratio 1, held
    for k in range(4, 8):
        E(movs_imm, 0, F.OPB * k); E(adds_reg, 0, 0, 5); tb(1, "opdef"); copy(0, 1, F.OPB, 2, 3)
    # the pitch envelope: the drop of a pitch algorithm (op 4's depth, its release), else at rest
    E(movs_imm, 0, F.PEG); E(adds_reg, 0, 0, 5); E(movs_imm, 1, 99); E(strb_imm, 1, 0, 0); E(strb_imm, 1, 0, 2); E(strb_imm, 1, 0, 3)
    E(strb_imm, 1, 0, 1); E(movs_imm, 1, 50); E(strb_imm, 1, 0, 4); E(strb_imm, 1, 0, 5); E(strb_imm, 1, 0, 6); E(strb_imm, 1, 0, 7)
    E(lsls_imm, 1, 6, 1); tb(2, "algf"); E(ldrb_reg, 1, 2, 1); E(cmp_imm, 1, 0); E(b_cond, "cv_np", "eq")
    E(ldrb_imm, 1, 4, 7); E(movs_imm, 2, 36); E(muls, 1, 2); E(movs_imm, 2, 127); E(raw, udiv(1, 1, 2)); clamp(1, None, 49); E(adds_imm8, 1, 50)
    E(strb_imm, 1, 0, 4)
    E(ldrb_imm, 1, 4, 15); E(lsrs_imm, 1, 1, 1); E(lsls_imm, 2, 6, 2); E(adds_imm8, 2, 3); tb(3, "rof"); E(ldrb_reg, 2, 3, 2)
    E(lsls_imm, 2, 2, 24); E(raw, h(0x1612)); E(adds_reg, 1, 1, 2)                         # asrs r2, r2, #24
    E(cmp_imm, 1, 0); E(b_cond, "cv_p0", "ge"); E(movs_imm, 1, 0)
    lab("cv_p0"); clamp(1, None, 63); tb(2, "rel2r"); E(ldrb_reg, 1, 2, 1); E(strb_imm, 1, 0, 1)
    lab("cv_np")
    # the globals
    imm32(0, F.GLB); E(adds_reg, 0, 0, 5)
    E(strb_imm, 6, 0, F.G_ALG); E(ldrb_imm, 1, 4, 13); E(strb_imm, 1, 0, F.G_FB); E(ldrb_imm, 1, 4, 14); E(strb_imm, 1, 0, F.G_NZ)
    E(movs_imm, 1, 24); E(strb_imm, 1, 0, F.G_TRN)
    tb(1, "susm"); E(ldrb_reg, 1, 1, 6); E(movs_imm, 2, 0); E(cmp_imm, 1, 15); E(b_cond, "cv_sy", "eq"); E(movs_imm, 2, 1)
    lab("cv_sy"); E(strb_imm, 2, 0, F.G_SYNC)
    E(lsls_imm, 1, 6, 1); E(adds_imm8, 1, 1); tb(2, "algf"); E(ldrb_reg, 1, 2, 1); E(strb_imm, 1, 0, F.G_NZOP)
    E(raw, popw([4, 5, 6, 7, 8, 9, 10, 11], lr=True)); E(raw, RET)

    # ---- c_fmdefs(r0 = track, r1 = 0: the voicing of its algorithm / 1: the defaults): every FM parameter; clobbers r0-r3
    lab("c_fmdefs")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(cmp_imm, 5, 0); E(b_cond, "df_v", "eq")
    tb(1, "def8"); copy(4, 1, F.PLEN, 2, 3); E(b, "df_x")
    lab("df_v"); E(ldrb_w, 6, 4, F.GLB + F.G_ALG); E(cmp_imm, 6, 16); E(b_cond, "df_dx", "hs")
    E(lsls_imm, 0, 6, 4); tb(1, "voic"); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 4); E(bl, "c_fm8conv"); E(b, "df_x")
    lab("df_dx"); tb(1, "dxdef"); copy(4, 1, F.PLEN, 2, 3); E(strb_w, 6, 4, F.GLB + F.G_ALG)
    lab("df_x"); E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY); E(movs_imm, 0, 0xFF); E(strb_w, 0, 4, B_STR)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmvrst(r0 = track): Clear + MIDI 1 / 2 (psave's c_psbtn): vcf21's initial values, the FM's defaults, the matrix's amounts 0
    lab("c_fmvrst")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_vreset"]); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_fmdefs")
    if "c_mxzero" in L: E(mov_reg, 0, 4); E(bl, L["c_mxzero"])
    E(pop_list, [4], pc=True)

    # ---- c_fmpg(r0 = track) -> r0 = 1 when the FM page is the one the knobs move
    lab("c_fmpg")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); E(b_cond, "pg_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    lab("pg_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_fmpar(r0 = knob 0..7) -> r0 = the descriptor's index (with Shift: + 8); clobbers r1-r3
    lab("c_fmpar")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(mov_reg, 0, 4); E(b_cond, "pa_x", "eq"); E(adds_imm8, 0, 8)
    lab("pa_x"); E(pop_list, [4], pc=True)

    # ---- c_fmkd(r0 = block, r1 = index) -> r0 = the descriptor (offset | max << 8 | clicks / kind << 16 | colour << 24), r1 = the value's address
    lab("c_fmkd")
    E(ldrb_w, 2, 0, B_SEL); E(cmp_imm, 2, 8); E(b_cond, "kd_s", "ls"); E(movs_imm, 2, 0)
    lab("kd_s"); E(movs_imm, 3, 0); E(cmp_imm, 2, 8); E(b_cond, "kd_p", "ne"); E(movs_imm, 3, 64)
    lab("kd_p"); E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 1, 3); tb(3, "kd"); E(raw, ldr_reg(1, 3, 1)); E(mov_reg, 3, 0)    # r1 = the descriptor
    E(lsls_imm, 0, 1, 24); E(lsrs_imm, 0, 0, 24); E(adds_reg, 3, 3, 0)                   # r3 = block + offset
    E(lsls_imm, 0, 1, 8); E(lsrs_imm, 0, 0, 28); E(cmp_imm, 0, K_ABS); E(b_cond, "kd_a", "eq")    # op-relative: + 24 sel
    E(movs_imm, 0, F.OPB); E(muls, 0, 2); E(adds_reg, 3, 3, 0)
    lab("kd_a"); E(mov_reg, 0, 1); E(mov_reg, 1, 3); E(raw, RET)

    # ---- c_fmovl(r0 = block, r1 = kind): the overlay from now; c_fmovk(r0 = block) -> r0 = its kind while shown, else 0; clobber r1-r3
    lab("c_fmovl")
    E(strb_w, 1, 0, B_OVK); c.now(1); E(raw, h(0xF8C0) + h(1 << 12 | B_OVT)); E(raw, RET)       # str.w r1, [r0, #B_OVT]
    lab("c_fmovk")
    E(ldrb_w, 1, 0, B_OVK); E(cmp_imm, 1, 0); E(b_cond, "ok_0", "eq")
    E(raw, h(0xF8D0) + h(2 << 12 | B_OVT)); c.now(3); E(subs_reg, 3, 3, 2); imm32(2, FE.OVL_MS); E(cmp_reg, 3, 2); E(b_cond, "ok_0", "hs")
    E(mov_reg, 0, 1); E(raw, RET)
    lab("ok_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_fmknob (slot 4 of the macro handlers: obj, knob, delta): the FM page of MIDI 1 / 2, else the previous slot
    lab("c_fmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(bl, "c_fmpar"); E(mov_reg, 5, 0)          # r5 = the index
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(mov_reg, 1, 5); E(bl, "c_fmkd"); E(mov_reg, 6, 0); E(mov_reg, 7, 1)                 # r6 = the descriptor, r7 = the value's address
    E(lsls_imm, 0, 6, 8); E(lsrs_imm, 0, 0, 28); E(cmp_imm, 0, K_NONE); bc("kn_x", "eq")
    E(ldr_sp, 0, 0); E(bl, L["c_vclr"]); E(cmp_imm, 0, 0); E(b_cond, "kn_add", "eq")
    # Clear: the default (the combined ratio: mode 0 and the default's coarse; the level scaling: none)
    E(subs_reg, 0, 7, 4); tb(1, "def8"); E(ldrb_reg, 2, 1, 0); E(adds_imm8, 0, 1); E(ldrb_reg, 3, 1, 0)       # r2 / r3 = the defaults here / next
    E(lsls_imm, 0, 6, 8); E(lsrs_imm, 0, 0, 28)
    E(cmp_imm, 0, K_LS); E(b_cond, "kc_n", "ne"); E(movs_imm, 2, 0); E(movs_imm, 3, 0)
    lab("kc_n"); E(strb_imm, 2, 7, 0)
    E(cmp_imm, 0, K_CMB); E(b_cond, "kc_c", "eq"); E(cmp_imm, 0, K_LS); E(b_cond, "kn_d", "ne")
    lab("kc_c"); E(strb_imm, 3, 7, 1); E(b, "kn_d")
    lab("kn_add")                                                                         # another knob (or operator) than the last: the steps' remainder 0
    E(ldrb_w, 0, 4, B_SEL); E(lsls_imm, 0, 0, 4); E(orrs_reg, 0, 5); E(ldrb_w, 1, 4, B_KID); E(cmp_reg, 0, 1); E(b_cond, "kn_k", "eq")
    E(strb_w, 0, 4, B_KID); imm32(1, V.KSLOW); E(movs_imm, 0, 0); E(strb_imm, 0, 1, 0)
    lab("kn_k")
    E(ldr_sp, 0, 8); E(lsls_imm, 1, 6, 12); E(lsrs_imm, 1, 1, 28); E(cmp_imm, 1, 1); E(b_cond, "kn_d1", "eq")
    E(cmp_imm, 1, 0); E(b_cond, "kn_d2", "ne"); E(movs_imm, 1, 16)                       # 0 = 16 clicks
    lab("kn_d2"); E(bl, L["c_kslow"])
    lab("kn_d1"); E(mov_reg, 2, 0)                                                        # r2 = the steps
    E(lsls_imm, 0, 6, 8); E(lsrs_imm, 0, 0, 28)
    E(cmp_imm, 0, K_CMB); E(b_cond, "kn_cmb", "eq"); E(cmp_imm, 0, K_LS); E(b_cond, "kn_ls", "eq")
    E(ldrb_imm, 0, 7, 0); E(adds_reg, 0, 0, 2); E(cmp_imm, 0, 0); E(b_cond, "kn_c0", "ge"); E(movs_imm, 0, 0)
    lab("kn_c0"); E(lsls_imm, 1, 6, 16); E(lsrs_imm, 1, 1, 24); E(cmp_reg, 0, 1); E(b_cond, "kn_c1", "le"); E(mov_reg, 0, 1)
    lab("kn_c1"); E(strb_imm, 0, 7, 0); E(b, "kn_d")
    lab("kn_cmb")                                                                         # v = mode ? 32 + (coarse & 3) : coarse
    E(ldrb_imm, 1, 7, 1); E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, 0); E(b_cond, "cm_r", "eq"); E(movs_imm, 0, 3); E(ands_reg, 1, 0); E(adds_imm8, 1, 32)
    lab("cm_r"); E(adds_reg, 1, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "cm_0", "ge"); E(movs_imm, 1, 0)
    lab("cm_0"); clamp(1, None, 35); E(movs_imm, 0, 0); E(cmp_imm, 1, 32); E(b_cond, "cm_w", "lo"); E(subs_imm8, 1, 32); E(movs_imm, 0, 1)
    lab("cm_w"); E(strb_imm, 0, 7, 0); E(strb_imm, 1, 7, 1); E(b, "kn_d")
    lab("kn_ls")                                                                          # v = RD ? RD : -LD, then RD / LD, BP 39, curves -LIN
    E(ldrb_imm, 1, 7, 1); E(cmp_imm, 1, 0); E(b_cond, "ls_r", "ne"); E(ldrb_imm, 1, 7, 0); E(raw, negs(1, 1))
    lab("ls_r"); E(adds_reg, 1, 1, 2); E(movs_imm, 0, 99); E(cmp_reg, 1, 0); E(b_cond, "ls_1", "le"); E(mov_reg, 1, 0)
    lab("ls_1"); E(raw, negs(0, 0)); E(cmp_reg, 1, 0); E(b_cond, "ls_2", "ge"); E(mov_reg, 1, 0)
    lab("ls_2"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 2); E(strb_imm, 0, 7, 3); E(movs_imm, 0, 39); E(subs_imm8, 7, 1); E(strb_imm, 0, 7, 0); E(adds_imm8, 7, 1)
    E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "ls_l", "lt"); E(strb_imm, 0, 7, 0); E(strb_imm, 1, 7, 1); E(b, "kn_d")
    lab("ls_l"); E(strb_imm, 0, 7, 1); E(raw, negs(1, 1)); E(strb_imm, 1, 7, 0)
    lab("kn_d")
    E(movs_imm, 0, 1); E(strb_w, 0, 4, B_DIRTY); E(movs_imm, 0, 0xFF); E(strb_w, 0, 4, B_STR)
    E(cmp_imm, 5, 8); E(b_cond, "kn_x", "ne"); E(mov_reg, 0, 4); E(movs_imm, 1, 5); E(bl, "c_fmovl")     # the algorithm: its overlay
    lab("kn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    lab("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_fmkleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: on the FM page the descriptors' values
    lab("c_fmkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
    E(movs_imm, 6, 0)
    lab("kl_l")
    E(mov_reg, 0, 6); E(bl, "c_fmpar"); E(mov_reg, 7, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_fmkd"); E(mov_reg, 3, 0)                 # r3 = the descriptor, r1 = the value's address
    E(lsls_imm, 2, 3, 8); E(lsrs_imm, 2, 2, 28)
    E(movs_imm, 0, 0); E(cmp_imm, 2, K_NONE); bc("kl_w", "eq")
    E(cmp_imm, 2, K_CMB); E(b_cond, "kl_ncm", "ne")
    E(ldrb_imm, 0, 1, 1); E(ldrb_imm, 2, 1, 0)
    E(movs_imm, 3, 0x17); E(cmp_imm, 2, 0); E(b_cond, "kl_cm", "eq"); E(movs_imm, 3, COL_FIX); E(movs_imm, 2, 3); E(ands_reg, 0, 2); E(adds_imm8, 0, 32)
    lab("kl_cm"); E(movs_imm, 1, 35); E(b, "kl_lv")
    lab("kl_ncm"); E(cmp_imm, 2, K_LS); E(b_cond, "kl_nls", "ne")
    E(ldrb_imm, 0, 1, 1); E(movs_imm, 3, 0x13); E(cmp_imm, 0, 0); E(b_cond, "kl_ls", "ne"); E(ldrb_imm, 0, 1, 0); E(movs_imm, 3, COL_FIX)
    E(cmp_imm, 0, 0); E(b_cond, "kl_ls", "ne"); E(movs_imm, 3, 0x13)
    lab("kl_ls"); E(movs_imm, 1, 99); E(b, "kl_lv")
    lab("kl_nls"); E(ldrb_imm, 0, 1, 0)
    E(cmp_imm, 7, 8); E(b_cond, "kl_na", "ne")                                            # the algorithm: its family's colour (the DX7's: white)
    E(movs_imm, 3, 0x01); E(cmp_imm, 0, 16); E(b_cond, "kl_na2", "hs"); tb(2, "fam"); E(ldrb_reg, 2, 2, 0); E(lsls_imm, 2, 2, 3)
    imm32(3, FAMW); E(lsrs_reg, 3, 2); E(movs_imm, 2, 0xFF); E(ands_reg, 3, 2)
    lab("kl_na2"); E(movs_imm, 1, F.NALG - 1); E(b, "kl_lv")
    lab("kl_na"); E(lsrs_imm, 1, 3, 8); E(movs_imm, 2, 0xFF); E(ands_reg, 1, 2); E(lsrs_imm, 3, 3, 24)
    lab("kl_lv")                                                                          # level = 20 + v x 100 / max
    E(movs_imm, 2, 100); E(muls, 0, 2); E(raw, udiv(0, 0, 1)); E(adds_imm8, 0, 20 + 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 3)
    lab("kl_w"); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); bc("kl_l", "lo")
    lab("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmrow(r0 = track) -> r0 = 1 while modesel's engine row is open for it; clobbers r1
    lab("c_fmrow")
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm8, 0, 1); E(cmp_reg, 1, 0); E(b_cond, "rw_1", "eq")
    E(movs_imm, 0, 0); E(raw, RET)
    lab("rw_1"); E(movs_imm, 0, 1); E(raw, RET)

    # ---- c_fmaud(r0 = track): the tonic while the pad is held (psave's audition); not with Shift
    lab("c_fmaud")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "au_x", "ne")
    E(bl, L["c_psaoff"]); E(bl, L["c_sdtonic"]); E(mov_reg, 5, 0)
    E(bl, L["c_psst"]); E(cmp_imm, 0, 0); E(b_cond, "au_x", "eq")
    E(movs_imm, 1, 0x80); E(orrs_reg, 1, 5); E(strb_imm, 1, 0, 6); E(strb_imm, 4, 0, 7)
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(movs_imm, 2, 100); E(mov_reg, 3, 5); E(bl, L["c_sdio"])
    lab("au_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_fmqsd (psave's audition, vcf21.c_sdio: track, on, velocity, note): with Shift a patch loads without it
    lab("c_fmqsd")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(cmp_imm, 1, 0); E(b_cond, "qs_go", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "qs_go", "eq")
    E(bl, L["c_psst"]); E(cmp_imm, 0, 0); E(b_cond, "qs_x", "eq"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 6)
    lab("qs_x"); E(pop_list, [0, 1, 2, 3], pc=True)
    lab("qs_go"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, L["c_sdio"])

    # ---- c_fmpad (slot 0 of the template view: view, pad, velocity): pad 7 = the FM page (held: the old algorithms; Clear: the voicing), pad 8
    #      held = the starters; on the FM page pads 9-16 = the operators, pad 17 = the pitch envelope; pad 24 of the engine row = FM
    if HEADS:
        # ---- c_f8hpad (slot 0 of the template view, the head, ahead of jumpflip): the pad 7 / 8 list or the algorithms shown = pads 9-24 to c_fmpad
        lab("c_f8hpad")
        E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 5, 1)
        E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("hp_p", "hi"); E(mov_reg, 4, 0)
        if V2:                                                                            # pad 32, Shift + pad 29: only with a voice that takes them
            E(cmp_imm, 5, 31); E(b_cond, "hp_v", "eq"); E(cmp_imm, 5, 28); E(b_cond, "hp_n", "ne")
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "hp_n", "eq")
            lab("hp_v"); E(mov_reg, 0, 4); E(bl, "c_f8vok"); E(cmp_imm, 0, 0); E(b_cond, "hp_n", "ne")
            E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
            lab("hp_n")
        E(cmp_imm, 5, 8); bc("hp_p", "lo"); E(cmp_imm, 5, 31 if V2 else 23); bc("hp_p", "hi")
        E(mov_reg, 0, 4); E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("hp_p", "eq")
        E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 6, 0)
        E(ldrb_w, 0, 6, B_P7); E(cmp_imm, 0, 0); bc("hp_f", "ne")
        E(mov_reg, 0, 6); E(bl, "c_fmovk"); E(cmp_imm, 0, 5); bc("hp_f", "eq")
        lab("hp_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["tpad"])
        lab("hp_f"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True))
    lab("c_fmpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pd_prev", "hi"); E(mov_reg, 4, 0)
    if NODUAL:                                                                            # pad 3 (the OSC 2 page) with FM on: nothing
        if PEG3:                                                                          # (PEG3) pad 3 = the FM page, the pitch envelope picked
            E(cmp_imm, 5, 2); E(b_cond, "pd_nd", "ne"); E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(mov_reg, 0, 4); bc("pd_nd", "eq")
            E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
            E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 8); E(strb_w, 1, 0, B_SEL); E(b, "pd_x")
        else:
            E(cmp_imm, 5, 2); E(b_cond, "pd_nd", "ne"); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_x", "ne"); E(mov_reg, 0, 4)
        lab("pd_nd")
    E(cmp_imm, 5, PADNO + 1); E(b_cond, "pd_n8", "ne")                                    # pad 8: the FM page, held = the starters
    E(mov_reg, 0, 4); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 2); E(strb_w, 1, 0, B_P7); E(b, "pd_x")
    lab("pd_n8")
    E(cmp_imm, 5, PADNO); bc("pd_n7", "ne")
    E(mov_reg, 0, 4); E(bl, "c_fmact"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(bl, L["c_mxclrh"]); E(cmp_imm, 0, 0); E(b_cond, "pd_pg", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_fmdefs"); E(b, "pd_x")                  # Clear + pad 7: the algorithm's voicing
    lab("pd_pg"); E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_P7); E(b, "pd_x")
    lab("pd_n7")
    E(cmp_imm, 5, 8); bc("pd_row", "lo"); E(cmp_imm, 5, 31); bc("pd_row", "hi")
    E(mov_reg, 0, 4); E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("pd_row", "eq")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 6, 0)
    E(ldrb_w, 0, 6, B_P7); E(cmp_imm, 0, 0)
    if V2: bc("pd_ov", "eq")
    else: E(b_cond, "pd_ov", "eq")
    E(cmp_imm, 5, 31 if V2 else 23); bc("pd_row", "hi")
    E(cmp_imm, 0, 2); E(b_cond, "pd_alg", "ne")                                           # pad 8 + pad: the starter (V2: the instrument)
    if V2:
        E(mov_reg, 0, 5); E(subs_imm8, 0, 8)
        if INST2:                                                                         # (INST2) + 24 x pad 8's page
            E(ldrb_w, 1, 6, B_IPG); E(cmp_imm, 1, 1); E(b_cond, "pd_ip", "ne"); E(adds_imm8, 0, 24)
            lab("pd_ip")
        E(mov_reg, 7, 0); E(mov_reg, 1, 6); E(bl, "c_fminst")
    else:
        E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(mov_reg, 7, 0); E(lsls_imm, 0, 0, 4); tb(1, "strt"); E(adds_reg, 0, 0, 1); E(mov_reg, 1, 6); E(bl, "c_fm8conv")
    E(strb_w, 7, 6, B_STR); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY); E(b, "pd_au")
    lab("pd_alg")                                                                         # pad 7 + pad: the algorithm (V2: of the page)
    if V2:
        E(ldrb_w, 0, 6, B_APG); E(mov_reg, 1, 5); E(subs_imm8, 1, 8); E(bl, "c_fmapal"); E(cmp_imm, 0, 0xFF); bc("pd_x", "eq")
    else:
        E(mov_reg, 0, 5); E(subs_imm8, 0, 8)
    E(strb_w, 0, 6, F.GLB + F.G_ALG); E(movs_imm, 0, 1); E(strb_w, 0, 6, B_DIRTY)
    lab("pd_au"); E(mov_reg, 0, 4); E(bl, "c_fmaud"); E(b, "pd_x")
    lab("pd_ov")
    E(mov_reg, 0, 6); E(bl, "c_fmovk"); E(cmp_imm, 0, 5); E(b_cond, "pd_op", "ne")       # the algorithms shown: their pads swallowed
    E(ldrb_w, 0, 6, F.GLB + F.G_ALG); E(cmp_imm, 0, 16); bc("pd_x", "hs"); E(cmp_imm, 5, 23); bc("pd_row", "hi"); E(b, "pd_x")
    lab("pd_op")                                                                          # pad 17 (the engine row closed): the pitch envelope
    if not PEG3:                                                                          # (PEG3: on pad 3; pad 17 dark like 18-24)
        E(cmp_imm, 5, 16); E(b_cond, "pd_o1", "ne")
        E(mov_reg, 0, 4); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("pd_row", "ne")
        E(movs_imm, 0, 8); E(strb_w, 0, 6, B_SEL); E(b, "pd_x")
    lab("pd_o1")
    if V2:                                                                                # pads 18-24 (the engine row closed): nothing
        E(cmp_imm, 5, 15); bc("pd_o3", "ls"); E(cmp_imm, 5, 23); bc("pd_row", "hi")
        E(mov_reg, 0, 4); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("pd_row", "ne")
        if ROWOP:                                                                         # (ROWOP) the engine row on pads 17-24
            E(cmp_imm, 5, FE.ROWPAD); bc("pd_x", "eq")                                    #   pad 24 = FM: already
            E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_ON)
            imm32(6, MS.RAM); E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, 0)  #   open for this track
            E(raw, h(0x9800)); E(mov_reg, 1, 5); E(raw, h(0x9A02)); E(bl, prev["pad"])     #   modesel picks it
            E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "pd_x")                          #   closed again
        else:
            bc("pd_x", "eq")
        lab("pd_o3")
    else:
        E(cmp_imm, 5, 15); bc("pd_row", "hi")                                             # pads 9-16: an operator the algorithm uses
    E(mov_reg, 0, 6); E(bl, "c_fmalg"); E(ldrb_imm, 0, 0, F.A_USED); E(mov_reg, 1, 5); E(subs_imm8, 1, 8); E(lsrs_reg, 0, 1); E(movs_imm, 2, 1)
    E(tst_reg, 0, 2); bc("pd_x", "eq"); E(strb_w, 1, 6, B_SEL); E(b, "pd_x")
    lab("pd_row")
    E(mov_reg, 0, 4); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(bl, L["c_msheld"]); E(cmp_imm, 0, 0); bc("pd_prev", "ne")
    E(cmp_imm, 5, ROWPAD); E(b_cond, "pd_ofm", "ne")
    E(raw, h(0x9800)); E(movs_imm, 1, MS.ROW + 2); E(raw, h(0x9A02)); E(bl, prev["pad"])     # the oscillator (modesel), then FM on
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 1); E(strb_w, 1, 0, B_ON); E(strb_w, 1, 0, B_DIRTY); E(b, "pd_x")
    lab("pd_ofm")
    E(cmp_imm, 5, MS.ROW); bc("pd_prev", "lo"); E(cmp_imm, 5, MS.ROW + 6); bc("pd_prev", "hi")
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_ON)
    lab("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])
    lab("pd_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)

    # ---- c_fmrel (slot 1 of the template view: view, pad): pad 7 / 8 let go = the lists off the pads
    lab("c_fmrel")
    E(cmp_imm, 1, PADNO); E(b_cond, "rl_g", "eq"); E(cmp_imm, 1, PADNO + 1); E(b_cond, "rl_p", "ne")
    lab("rl_g")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "rl_x", "hi")
    E(bl, "c_fmblk"); E(movs_imm, 1, 0); E(strb_w, 1, 0, B_P7)
    lab("rl_x"); E(raw, popw([0, 1, 2, 4], lr=True))
    lab("rl_p"); E(b_w, prev["rel"])

    # ---- c_fmleds (slot 7 of the template view: view) -> r0 = the LED buffer: pad 24 of the row, pad 27, pads 7 / 8 with FM on; the operators;
    #      the overlays
    lab("c_fmleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("le_x", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmact"); E(mov_reg, 7, 0)
    E(mov_reg, 0, 6); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); E(b_cond, "le_nr", "eq")
    E(movs_imm, 1, FE.COL_FM[1]); E(cmp_imm, 7, 0); E(b_cond, "le_r1", "eq"); E(movs_imm, 1, FE.COL_FM[0])
    E(movs_imm, 2, MS.COLS[2][1]); E(strh_imm, 2, 5, 2 * (MS.ROW + 2))
    lab("le_r1"); E(strh_imm, 1, 5, 2 * ROWPAD)
    lab("le_nr")
    E(cmp_imm, 7, 0); bc("le_x", "eq")
    if NODUAL: E(movs_imm, 1, FE.COL_FM[1] if PEG3 else 0); E(strh_imm, 1, 5, 2 * 2)        # pad 3 (the OSC 2 page): dark with FM on (PEG3: the pitch envelope, dim)
    E(movs_imm, 1, FE.COL_FM[0]); E(strh_imm, 1, 5, 2 * 26)
    if ROWOP:                                                                             # (ROWOP) pad 7 bright only while held (its list shown)
        E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(ldrb_w, 0, 0, B_P7); E(movs_imm, 1, FE.COL_FM[1]); E(cmp_imm, 0, 1); E(b_cond, "le_p", "ne"); E(movs_imm, 1, FE.COL_FM[0])
    else:
        E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(movs_imm, 1, FE.COL_FM[1]); E(cmp_imm, 0, PAGE); E(b_cond, "le_p", "ne"); E(movs_imm, 1, FE.COL_FM[0])
    lab("le_p"); E(strh_imm, 1, 5, 2 * PADNO)
    E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)                                 # a hold of pad 7 / 8 seen before a pause of the view: gone
    c.now(0); E(raw, h(0xF8D4) + h(1 << 12 | B_LEDT)); E(raw, h(0xF8C4) + h(0 << 12 | B_LEDT)); E(subs_reg, 0, 0, 1)
    E(cmp_imm, 0, FE.STALE_MS); E(b_cond, "le_f", "ls"); E(movs_imm, 0, 0); E(strb_w, 0, 4, B_P7)
    lab("le_f")
    E(ldrb_w, 0, 4, B_P7); E(movs_imm, 1, 0x02); E(cmp_imm, 0, 2); E(b_cond, "le_8", "ne"); E(movs_imm, 1, 0x01)
    lab("le_8"); E(strh_imm, 1, 5, 2 * (PADNO + 1))
    E(mov_reg, 0, 6); E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("le_x", "eq")
    E(ldrb_w, 0, 4, B_P7); E(cmp_imm, 0, 2); bc("le_st", "eq"); E(cmp_imm, 0, 1); bc("le_al", "eq")
    E(mov_reg, 0, 4); E(bl, "c_fmovk"); E(cmp_imm, 0, 5); E(b_cond, "le_op", "ne")
    lab("le_ov"); E(ldrb_w, 0, 4, F.GLB + F.G_ALG); E(cmp_imm, 0, 16); bc("le_al", "lo")
    if F.ALG8:                                                                            # 49-56 on pads 1-8: dim white, the current bright
        E(cmp_imm, 0, 48); E(b_cond, "le_d8x", "lo")
        E(subs_imm8, 0, 48); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
        lab("le_8l"); E(movs_imm, 1, 0); E(cmp_imm, 6, 8); E(b_cond, "le_8w", "hs"); E(movs_imm, 1, 0x02); E(cmp_reg, 6, 7); E(b_cond, "le_8w", "ne"); E(movs_imm, 1, 0x01)
        lab("le_8w"); E(lsls_imm, 0, 6, 1); E(strh_reg, 1, 5, 0); E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "le_8l", "lo"); E(b, "le_x")
        lab("le_d8x")
    # the DX7's 32 on pads 1-32: dim white, the current bright
    E(subs_imm8, 0, 16); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
    lab("le_dl"); E(movs_imm, 1, 0x02); E(cmp_reg, 6, 7); E(b_cond, "le_dw", "ne"); E(movs_imm, 1, 0x01)
    lab("le_dw"); E(lsls_imm, 0, 6, 1); E(strh_reg, 1, 5, 0); E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "le_dl", "lo"); E(b, "le_x")
    lab("le_op")                                                                          # the operators on pads 9-16, the pitch envelope on 17
    E(mov_reg, 0, 4); E(bl, "c_fmalg"); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
    lab("le_ol")
    E(movs_imm, 1, 0); E(ldrb_imm, 0, 7, F.A_USED); E(lsrs_reg, 0, 6); E(movs_imm, 2, 1); E(tst_reg, 0, 2); E(b_cond, "le_ow", "eq")
    E(ldrb_imm, 0, 7, F.A_CAR); E(lsrs_reg, 0, 6); E(movs_imm, 1, COL_MOD[1]); E(tst_reg, 0, 2); E(b_cond, "le_oc", "eq"); E(movs_imm, 1, COL_CAR[1])
    lab("le_oc"); E(ldrb_w, 0, 4, B_SEL); E(cmp_reg, 0, 6); E(b_cond, "le_ow", "ne"); E(subs_imm8, 1, 1)                # bright = dim - 1
    lab("le_ow"); E(lsls_imm, 0, 6, 1); E(adds_imm8, 0, 16); E(strh_reg, 1, 5, 0); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "le_ol", "lo")
    if PEG3:                                                                              # pad 3 bright while the pitch envelope is picked
        E(ldrb_w, 0, 4, B_SEL); E(cmp_imm, 0, 8); E(b_cond, "le_p3", "ne"); E(movs_imm, 1, FE.COL_FM[0]); E(strh_imm, 1, 5, 2 * 2)
        lab("le_p3")
    E(mov_reg, 0, 6); E(bl, "c_fmrow"); E(cmp_imm, 0, 0); bc("le_x", "ne")                # pad 17: with the engine row closed
    if not PEG3:
        E(movs_imm, 1, COL_PEG[1]); E(ldrb_w, 0, 4, B_SEL); E(cmp_imm, 0, 8); E(b_cond, "le_pg", "ne"); E(movs_imm, 1, COL_PEG[0])
        lab("le_pg"); E(strh_imm, 1, 5, 2 * 16)
    if ROWOP:                                                                             # pads 17-24: the engine row (FM bright)
        tb(2, "rowc"); E(movs_imm, 0, 0)
        lab("le_r3"); E(ldrb_reg, 1, 2, 0); E(lsls_imm, 3, 0, 1); E(adds_imm8, 3, 2 * 16); E(strh_reg, 1, 5, 3)
        E(adds_imm8, 0, 1); E(cmp_imm, 0, 8); E(b_cond, "le_r3", "lo")
    elif V2:                                                                              # pads 18-24: dark (no patches on the operator page)
        E(movs_imm, 1, 0); E(movs_imm, 0, 2 * (16 if PEG3 else 17))
        lab("le_r3"); E(strh_reg, 1, 5, 0); E(adds_imm8, 0, 2); E(cmp_imm, 0, 2 * 24); E(b_cond, "le_r3", "lo")
    E(b, "le_x")
    lab("le_al")                                                                          # the old algorithms on pads 9-24: the family's colour, the current one bright
    if V2:                                                                                # (V2) the page's 24 on pads 9-32: teal 4 operators, white 6, amber 8
        E(ldrb_w, 7, 4, B_APG); E(movs_imm, 6, 0)
        lab("la_l"); E(mov_reg, 0, 7); E(mov_reg, 1, 6); E(bl, "c_fmapal"); E(movs_imm, 1, 0); E(cmp_imm, 0, 0xFF); E(b_cond, "la_w", "eq")
        E(movs_imm, 1, 0x4D); E(cmp_imm, 0, 16); E(b_cond, "la_c", "lo"); E(movs_imm, 1, 0x01); E(cmp_imm, 0, 48); E(b_cond, "la_c", "lo"); E(movs_imm, 1, 0x2B)
        lab("la_c"); E(ldrb_w, 2, 4, F.GLB + F.G_ALG); E(cmp_reg, 0, 2); E(b_cond, "la_w", "eq"); E(adds_imm8, 1, 1)
        lab("la_w"); E(mov_reg, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 24); E(b_cond, "la_l", "lo"); E(b, "le_x")
    E(ldrb_w, 7, 4, F.GLB + F.G_ALG); E(movs_imm, 6, 0)
    lab("le_ap")
    tb(1, "fam"); E(ldrb_reg, 1, 1, 6); E(lsls_imm, 1, 1, 1); E(cmp_reg, 6, 7); E(b_cond, "le_ab", "eq"); E(adds_imm8, 1, 1)
    lab("le_ab"); tb(2, "famc"); E(ldrb_reg, 1, 2, 1)
    E(mov_reg, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "le_ap", "lo"); E(b, "le_x")
    lab("le_st")                                                                          # the starters on pads 9-24: the family's colour, bright = the one loaded
    E(ldrb_w, 7, 4, B_STR); E(movs_imm, 6, 0)                                             # (V2: the 24 instruments on pads 9-32)
    if INST2:                                                                             # (INST2) r6 = 24 x the page .. + 23
        E(ldrb_w, 0, 4, B_IPG); E(cmp_imm, 0, 1); E(b_cond, "le_s0", "ne"); E(movs_imm, 6, 24)
        lab("le_s0")
    lab("le_sl"); E(lsls_imm, 1, 6, 1); E(cmp_reg, 6, 7); E(b_cond, "le_sk", "eq"); E(adds_imm8, 1, 1)
    lab("le_sk"); tb(2, "icol" if V2 else "stc"); E(ldrb_reg, 1, 2, 1)
    E(mov_reg, 0, 6)
    if INST2:
        E(cmp_imm, 0, 24); E(b_cond, "le_sp", "lo"); E(subs_imm8, 0, 24)
        lab("le_sp")
    E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 6, 1)
    if INST2: E(cmp_imm, 6, 24); E(b_cond, "le_sz", "eq"); E(cmp_imm, 6, 48); E(b_cond, "le_sz", "eq"); E(b, "le_sl"); lab("le_sz")   # (one page: 24 pads)
    else: E(cmp_imm, 6, 24 if V2 else 16); E(b_cond, "le_sl", "lo")
    lab("le_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    if V2:
        # ---- c_f8vok(r0 = track) -> r0 = 1 when its engine is a voice the voice modes fit (oscillator, FM, VA-drum, sample); clobbers r1-r3
        #      (the user: «hide mono/poly selector when voices aren't being used or compatible»: no voice, VCA / VCF / FX only, granular, FX sequencer)
        lab("c_f8vok")
        E(push_list, [4], lr=True); E(bl, L["c_msmode"]); E(movs_imm, 1, 1)
        E(cmp_imm, 0, 2); E(b_cond, "vk_x", "eq"); E(cmp_imm, 0, 3); E(b_cond, "vk_x", "eq"); E(cmp_imm, 0, 5); E(b_cond, "vk_x", "eq"); E(movs_imm, 1, 0)
        lab("vk_x"); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)
        # ---- c_fmapal(r0 = page, r1 = 0..23) -> r0 = the algorithm on that pad, 0xFF none (a page past 2 = 0); clobbers r1
        lab("c_fmapal")
        E(cmp_imm, 0, 1); E(b_cond, "ap_1", "eq"); E(cmp_imm, 0, 2); E(b_cond, "ap_2", "eq")
        E(mov_reg, 0, 1); E(cmp_imm, 1, 16); E(b_cond, "ap_r", "lo"); E(adds_imm8, 0, 32); E(raw, RET)       # page 1: the 16, then 48-55
        lab("ap_1"); E(mov_reg, 0, 1); E(adds_imm8, 0, 16); E(raw, RET)                                       # page 2: 16-39
        lab("ap_2"); E(movs_imm, 0, 0xFF); E(cmp_imm, 1, 8); E(b_cond, "ap_r", "hs"); E(mov_reg, 0, 1); E(adds_imm8, 0, 40)
        lab("ap_r"); E(raw, RET)
        # ---- c_fminst(r0 = 0..23, r1 = block): fm8inst's instrument unpacked into the 216 parameters (fm8inst.inst_full, byte for byte)
        import fm8inst as FI
        lab("c_fminst")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
        if INST2:                                                                         # (INST2) the table unpacked into the ITCM the first time
            import zlib
            stamp = zlib.crc32(FI.lz(FI.table())) & 0xFFFFFFFF
            E(mov_reg, 4, 0)
            E(movs_imm, 1, IT_SIG >> 2); E(lsls_imm, 1, 1, 2); E(ldr_imm, 2, 1, 0); imm32(3, stamp); E(cmp_reg, 2, 3); E(b_cond, "fi_u", "eq")
            tb(0, "inst"); E(movs_imm, 1, IT_TAB >> 2); E(lsls_imm, 1, 1, 2); imm32(2, IT_TAB + len(FI.table())); E(bl, "c_fiun")
            E(movs_imm, 1, IT_SIG >> 2); E(lsls_imm, 1, 1, 2); imm32(3, stamp); E(str_imm, 3, 1, 0)
            lab("fi_u"); E(mov_reg, 0, 4)
            E(movs_imm, 2, FI.ISZ); E(muls, 0, 2); E(movs_imm, 4, IT_TAB >> 2); E(lsls_imm, 4, 4, 2); E(adds_reg, 4, 4, 0)
        else:
            E(movs_imm, 2, FI.ISZ); E(muls, 0, 2); tb(4, "inst"); E(adds_reg, 4, 4, 0)
        E(movs_imm, 0, 0); E(movs_imm, 2, 0)
        lab("fi_z"); E(strb_reg, 0, 5, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, F.PLEN); E(b_cond, "fi_z", "lo")
        E(movs_imm, 6, 0)
        lab("fi_o")
        E(movs_imm, 0, F.OPB); E(muls, 0, 6); E(adds_reg, 7, 5, 0)
        E(movs_imm, 0, FI.OPB_C); E(muls, 0, 6); E(adds_reg, 1, 4, 0)
        E(movs_imm, 2, 0)
        lab("fi_e"); E(ldrb_reg, 3, 1, 2); E(strb_reg, 3, 7, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "fi_e", "lo")
        for src, dst in ((8, F.O_OL), (9, F.O_CRS), (10, F.O_FINE), (11, F.O_DET), (13, F.O_RD)):
            E(ldrb_imm, 3, 1, src); E(strb_imm, 3, 7, dst)
        E(ldrb_imm, 3, 1, 12); E(movs_imm, 0, 7); E(ands_reg, 0, 3); E(strb_imm, 0, 7, F.O_KVS)
        E(lsrs_imm, 2, 3, 3); E(movs_imm, 0, 7); E(ands_reg, 0, 2); E(strb_imm, 0, 7, F.O_RS)
        E(lsrs_imm, 2, 3, 6); E(strb_imm, 2, 7, F.O_MODE)
        E(movs_imm, 3, 39); E(strb_imm, 3, 7, F.O_BP)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "fi_o", "lo")
        E(mov_reg, 1, 4); E(adds_imm8, 1, 8 * FI.OPB_C); E(mov_reg, 7, 5); E(adds_imm8, 7, F.PEG); E(movs_imm, 2, 0)
        lab("fi_p"); E(ldrb_reg, 3, 1, 2); E(strb_reg, 3, 7, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "fi_p", "lo")
        E(adds_imm8, 1, 8); E(mov_reg, 7, 5); E(adds_imm8, 7, F.GLB)
        for i, g in enumerate((F.G_ALG, F.G_FB, F.G_SYNC, F.G_TRN, F.G_NZ, F.G_NZOP)):
            E(ldrb_imm, 3, 1, i); E(strb_imm, 3, 7, g)
        E(pop_list, [4, 5, 6, 7], pc=True)
        if INST2:
            # ---- c_fiun(r0 = the packed table, r1 = the output, r2 = its end): fm8inst.unlz
            lab("c_fiun")
            E(push_list, [4, 5, 6, 7], lr=True)
            lab("fu_b"); E(cmp_reg, 1, 2); E(b_cond, "fu_x", "hs")
            E(ldrb_imm, 3, 0, 0); E(adds_imm8, 0, 1); E(movs_imm, 4, 8)
            lab("fu_i"); E(cmp_reg, 1, 2); E(b_cond, "fu_x", "hs")
            E(lsrs_imm, 3, 3, 1); E(b_cond, "fu_m", "cs")
            E(ldrb_imm, 5, 0, 0); E(adds_imm8, 0, 1); E(strb_imm, 5, 1, 0); E(adds_imm8, 1, 1); E(b, "fu_n")
            lab("fu_m"); E(ldrb_imm, 5, 0, 0); E(ldrb_imm, 6, 0, 1); E(adds_imm8, 0, 2)
            E(lsrs_imm, 7, 6, 4); E(lsls_imm, 7, 7, 8); E(orrs_reg, 5, 7)
            E(movs_imm, 7, 15); E(ands_reg, 6, 7); E(adds_imm8, 6, 3)
            E(subs_reg, 5, 1, 5)
            lab("fu_c"); E(ldrb_imm, 7, 5, 0); E(strb_imm, 7, 1, 0); E(adds_imm8, 5, 1); E(adds_imm8, 1, 1); E(subs_imm8, 6, 1); E(b_cond, "fu_c", "ne")
            lab("fu_n"); E(subs_imm8, 4, 1); E(b_cond, "fu_i", "ne"); E(b, "fu_b")
            lab("fu_x"); E(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_f8btn (the controller's button press, the head): Octave down / up while pad 7 is held = the page of its list
        lab("c_f8btn")
        E(cmp_imm, 1, 19); bc("bt_p", "lo"); E(cmp_imm, 1, 20); bc("bt_p", "hi")
        E(push_list, [0, 1, 4, 5, 6], lr=True); E(mov_reg, 5, 1); E(movs_imm, 4, 0)
        lab("bt_t"); E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(ldrb_w, 1, 0, B_P7); E(cmp_imm, 1, 1); E(b_cond, "bt_g", "eq")
        if INST2: E(cmp_imm, 1, 2); E(b_cond, "bt_i", "eq")
        E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "bt_t", "lo")
        E(raw, popw([0, 1, 4, 5, 6], lr=True)); E(b, "bt_p")
        lab("bt_g"); E(ldrb_w, 1, 0, B_APG); E(cmp_imm, 1, 2); E(b_cond, "bt_k", "ls"); E(movs_imm, 1, 0)
        lab("bt_k"); E(cmp_imm, 5, 20); E(b_cond, "bt_dn", "ne"); E(cmp_imm, 1, 0); E(b_cond, "bt_e", "eq"); E(subs_imm8, 1, 1); E(b, "bt_s")
        lab("bt_dn"); E(cmp_imm, 1, 2); E(b_cond, "bt_e", "hs"); E(adds_imm8, 1, 1)
        lab("bt_s"); E(strb_w, 1, 0, B_APG)
        lab("bt_e"); E(pop_list, [0, 1, 4, 5, 6], pc=True)
        if INST2:                                                                         # (INST2) pad 8 held: Octave down = page 2, up = page 1
            lab("bt_i"); E(movs_imm, 1, 1); E(cmp_imm, 5, 20); E(b_cond, "bt_is", "ne"); E(movs_imm, 1, 0)
            lab("bt_is"); E(strb_w, 1, 0, B_IPG); E(pop_list, [0, 1, 4, 5, 6], pc=True)
        lab("bt_p"); E(b_w, prev["btn8"])
        # ---- c_fmoct(r0 = the LED frame): pad 7 held = Octave down / up lit when there is a next / previous page
        lab("c_fmoct")
        E(push_list, [4, 5, 6], lr=True); E(mov_reg, 5, 0); E(movs_imm, 4, 0)
        lab("oc_t"); E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(ldrb_w, 1, 0, B_P7); E(cmp_imm, 1, 1); E(b_cond, "oc_g", "eq")
        if INST2: E(cmp_imm, 1, 2); E(b_cond, "oc_i", "eq")
        E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "oc_t", "lo"); E(pop_list, [4, 5, 6], pc=True)
        lab("oc_g"); E(ldrb_w, 1, 0, B_APG); E(cmp_imm, 1, 2); E(b_cond, "oc_k", "ls"); E(movs_imm, 1, 0)
        lab("oc_k"); E(movs_imm, 2, 0); E(cmp_imm, 1, 0); E(b_cond, "oc_u", "eq"); E(movs_imm, 2, 0x01)
        lab("oc_u"); E(movs_imm, 0, 2 * OCT_UP); E(strh_reg, 2, 5, 0)
        E(movs_imm, 2, 0); E(cmp_imm, 1, 2); E(b_cond, "oc_d", "hs"); E(movs_imm, 2, 0x01)
        lab("oc_d"); E(movs_imm, 0, 2 * OCT_DN); E(strh_reg, 2, 5, 0)
        E(pop_list, [4, 5, 6], pc=True)
        if INST2:                                                                         # (INST2) pad 8 held: Octave up lit on page 2, down on page 1
            lab("oc_i"); E(ldrb_w, 1, 0, B_IPG); E(movs_imm, 2, 0x01); E(movs_imm, 3, 0); E(cmp_imm, 1, 1); E(b_cond, "oc_ip", "eq"); E(movs_imm, 2, 0); E(movs_imm, 3, 0x01)
            lab("oc_ip"); E(movs_imm, 0, 2 * OCT_UP); E(strh_reg, 2, 5, 0); E(movs_imm, 0, 2 * OCT_DN); E(strh_reg, 3, 5, 0)
            E(pop_list, [4, 5, 6], pc=True)
        # ---- c_f8mpr (in place of the bl c_mpr of mpatch's c_mprefresh: r0 = bank, r2 = the shared buffer): the read, then the engines of its 8
        #      records into ENGC (8 x (bank & 1)): ecode[flags & 15], the oscillator with "FM" on = 7; not a patch = 0xFF
        lab("c_f8mpr")
        E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
        E(bl, L["c_mpr"]); E(mov_reg, 5, 0); E(mov_reg, 7, 1)
        E(cmp_imm, 5, 0); E(b_cond, "mr_x", "ne")
        E(movs_imm, 0, 1); E(ands_reg, 4, 0); E(lsls_imm, 4, 4, 3); imm32(0, ENGC); E(adds_reg, 4, 4, 0)
        E(movs_imm, 6, 0)
        lab("mr_l")
        E(movs_imm, 2, 0xFF)
        E(lsls_imm, 0, 6, 9); imm32(1, MP.OFF + 104); E(adds_reg, 0, 0, 1); E(cmp_reg, 0, 7); E(b_cond, "mr_w", "hi")
        E(lsls_imm, 0, 6, 9); imm32(1, PK.BUF + MP.OFF); E(adds_reg, 0, 0, 1)
        E(ldr_imm, 1, 0, 0); imm32(3, MP.MAGIC4); E(cmp_reg, 1, 3); E(b_cond, "mr_w", "ne")
        E(ldrb_imm, 1, 0, 4); E(movs_imm, 3, 15); E(ands_reg, 1, 3); tb(3, "ecode"); E(ldrb_reg, 2, 3, 1)
        E(cmp_imm, 2, 2); E(b_cond, "mr_w", "ne")
        E(adds_imm8, 0, 100); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, ord("F")); E(b_cond, "mr_wt" if WTCOL else "mr_w", "ne")
        E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, ord("M")); E(b_cond, "mr_wt" if WTCOL else "mr_w", "ne")
        E(ldrb_imm, 1, 0, 3); E(movs_imm, 3, 1); E(tst_reg, 1, 3); E(b_cond, "mr_wt" if WTCOL else "mr_w", "eq"); E(movs_imm, 2, 7)
        if WTCOL:                                                                       # (SC52.6) not FM: the wavetable's record on (wtui, + 150: 0xB7, on) = 8
            E(b, "mr_w")
            lab("mr_wt"); E(adds_imm8, 0, 50); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0xB7); E(b_cond, "mr_w", "ne")
            E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0); E(b_cond, "mr_w", "eq"); E(movs_imm, 2, 8)
        lab("mr_w"); E(strb_reg, 2, 4, 6)
        E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "mr_l", "lo")
        lab("mr_x"); E(mov_reg, 0, 5); E(mov_reg, 1, 7); E(pop_list, [4, 5, 6, 7], pc=True)
        # ---- c_f8scol (in mpatch's c_mpleds, a slot in use: r3 = its pad 0..15, r4 = the last one's + 1) -> r2 = its engine's colour, bright = the
        #      last one; an unknown engine = mpatch's peach; r0 / r2 clobbered
        lab("c_f8scol")
        E(push_list, [1], lr=True)
        imm32(1, ENGC); E(ldrb_reg, 2, 1, 3); E(cmp_imm, 2, 8 if WTCOL else 7); E(b_cond, "sc_k", "ls")
        E(movs_imm, 2, MP.COL_DIM); E(mov_reg, 0, 3); E(adds_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "sc_x", "ne"); E(movs_imm, 2, MP.COL_LIT); E(b, "sc_x")
        lab("sc_k"); E(lsls_imm, 2, 2, 1); E(mov_reg, 0, 3); E(adds_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "sc_b", "eq"); E(adds_imm8, 2, 1)
        lab("sc_b"); tb(1, "scol"); E(ldrb_reg, 2, 1, 2)
        lab("sc_x"); E(pop_list, [1], pc=True)
    if NODUAL:
        # ---- c_f8vosc (vcf21's c_vosc, its first 4 bytes: push {r4, lr}; mov r4, r0): with FM on no oscillators (pad 28 dark, ignored)
        lab("c_f8vosc")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(bl, "c_fmact"); E(cmp_imm, 0, 0); E(b_cond, "vs_c", "eq")
        E(movs_imm, 0, 0); E(pop_list, [4], pc=True)
        lab("vs_c"); E(mov_reg, 0, 4); E(b_w, prev["vosc4"])
        # ---- c_f8dual (vcf21's no_dt in c_vnote_on: r4 = track, r5 = the RT block) -> r3 = the two oscillators' bit, 0 with FM on; Z set by it
        lab("c_f8dual")
        E(ldrb_imm, 3, 5, V.RT_VEL); E(lsrs_imm, 3, 3, 7); E(b_cond, "du_r", "eq")
        E(push_list, [0, 1, 2], lr=True)
        E(mov_reg, 0, 4); E(bl, "c_fmact"); E(movs_imm, 3, 1); E(cmp_imm, 0, 0); E(b_cond, "du_1", "eq"); E(movs_imm, 3, 0)
        lab("du_1"); E(cmp_imm, 3, 0); E(pop_list, [0, 1, 2], pc=True)
        lab("du_r"); E(raw, RET)
    if HEADS:
        # ---- c_f8hled (slot 7 of the template view, the head, ahead of jumpflip): the pad 7 / 8 list or the algorithms painted again over its LEDs
        lab("c_f8hled")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(bl, prev["tled"]); E(mov_reg, 5, 0)
        E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("le_x", "hi"); E(mov_reg, 6, 0)
        if V2:                                                                            # no voice that takes them: pad 32 dark, pad 29 dark with Shift
            E(bl, "c_f8vok"); E(cmp_imm, 0, 0); E(b_cond, "hl_v", "ne")
            E(movs_imm, 1, 0); E(strh_imm, 1, 5, 2 * 31); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "hl_v", "eq")
            E(movs_imm, 1, 0); E(strh_imm, 1, 5, 2 * 28)
            lab("hl_v"); E(mov_reg, 0, 6)
        E(bl, "c_fmpg"); E(cmp_imm, 0, 0); bc("le_x", "eq")
        E(mov_reg, 0, 6); E(bl, "c_fmblk"); E(mov_reg, 4, 0)
        E(ldrb_w, 0, 4, B_P7); E(cmp_imm, 0, 2); bc("le_st", "eq"); E(cmp_imm, 0, 1); bc("le_al", "eq")
        E(mov_reg, 0, 4); E(bl, "c_fmovk"); E(cmp_imm, 0, 5); bc("le_x", "ne"); E(b, "le_ov")

    # ---- c_fmsum(r0 = 21 bytes) -> r0 = 0x5A + the first 20, & 0xFF; clobbers r1-r3
    lab("c_fmsum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    lab("su_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, PLEN_OLD - 1); E(b_cond, "su_l", "lo")
    E(movs_imm, 0, 0xFF); E(ands_reg, 0, 2); E(raw, RET)

    # ---- c_fmgath(r0 = track) in c_mpsave (r5 = the slot there): p4dest's gather, then "FM" version 3 (on) at padding + 100; the parameters in
    #      the slot's FM record (fm8store.c_fsput: the bank past its 8 records)
    lab("c_fmgath")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    imm32(1, FS.SLOT); E(strb_imm, 5, 1, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 5, 0); imm32(6, PK.BUF + POFS)
    E(movs_imm, 0, ord("F")); E(strb_imm, 0, 6, 0); E(movs_imm, 0, ord("M")); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 3); E(strb_imm, 0, 6, 2)
    E(ldrb_w, 0, 5, B_ON); E(strb_imm, 0, 6, 3)
    E(movs_imm, 0, 0); E(movs_imm, 7, 4)
    lab("ga_l"); E(strb_reg, 0, 6, 7); E(adds_imm8, 7, 1); E(cmp_imm, 7, PLEN_OLD - 1); E(b_cond, "ga_l", "lo")
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(strb_imm, 0, 6, PLEN_OLD - 1)
    E(mov_reg, 0, 5); imm32(1, FS.SLOT); E(ldrb_imm, 1, 1, 0); E(bl, "c_fsput")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_fmappl(r0 = track) in c_mpload (r5 = the slot there): p4dest's apply, then the patch's FM: the 4-operator versions 1 / 2 converted,
    #      version 3 = on / off and the slot's FM record (none or damaged: the parameters stay); none: FM off (the parameters stay)
    lab("c_fmappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    imm32(1, FS.SLOT); E(strb_imm, 5, 1, 0)
    E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, PLEN_OLD); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + POFS); E(mov_reg, 5, 0); E(mov_reg, 7, 1)
    E(mov_reg, 0, 4); E(bl, "c_fmblk"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(strb_w, 0, 1, B_ON); E(movs_imm, 0, 1); E(strb_w, 0, 1, B_DIRTY)
    E(mov_reg, 4, 1)
    E(cmp_imm, 5, 0); bc("ap_x", "ne"); E(cmp_imm, 7, PLEN_OLD); bc("ap_x", "ne")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, ord("F")); bc("ap_x", "ne"); E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, ord("M")); bc("ap_x", "ne")
    E(ldrb_imm, 0, 6, 2); E(subs_imm8, 0, 1); E(cmp_imm, 0, 2); bc("ap_x", "hi")
    E(mov_reg, 0, 6); E(bl, "c_fmsum"); E(ldrb_imm, 1, 6, PLEN_OLD - 1); E(cmp_reg, 0, 1); bc("ap_x", "ne")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 3); bc("ap_on", "eq")
    E(movs_imm, 7, 4)                                                                     # versions 1 / 2: the 16 parameters, at most 127
    lab("ap_l"); E(ldrb_reg, 0, 6, 7); E(cmp_imm, 0, 127); E(b_cond, "ap_v", "ls"); E(movs_imm, 0, 127)
    lab("ap_v"); E(strb_reg, 0, 6, 7); E(adds_imm8, 7, 1); E(cmp_imm, 7, 20); E(b_cond, "ap_l", "lo")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 2); E(b_cond, "ap_cv", "eq")
    # version 1: the attacks to the right half, the ratios to their exact click, the feedback's square root
    E(movs_imm, 7, 0)
    lab("ap_c")
    E(adds_reg, 1, 6, 7); E(ldrb_imm, 0, 1, 4 + FE.P_ATK); E(lsrs_imm, 0, 0, 1); E(adds_imm8, 0, FE.CENTRE); E(strb_imm, 0, 1, 4 + FE.P_ATK)
    E(ldrb_imm, 0, 1, 4 + FE.P_RAT); E(movs_imm, 2, 24); E(muls, 0, 2); E(lsrs_imm, 0, 0, 7); E(lsls_imm, 0, 0, 7); E(adds_imm8, 0, 23); E(raw, udiv(0, 0, 2))
    E(strb_imm, 0, 1, 4 + FE.P_RAT)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "ap_c", "lo")
    E(ldrb_imm, 1, 6, 4 + FE.P_FB); E(lsls_imm, 1, 1, 7); E(movs_imm, 0, 0)
    lab("ap_q"); E(adds_imm8, 0, 1); E(mov_reg, 2, 0); E(muls, 2, 0); E(cmp_reg, 2, 1); E(b_cond, "ap_q", "ls")
    E(subs_imm8, 0, 1); E(strb_imm, 0, 6, 4 + FE.P_FB)
    lab("ap_cv"); E(mov_reg, 0, 6); E(adds_imm8, 0, 4); E(mov_reg, 1, 4); E(bl, "c_fm8conv")
    lab("ap_on")
    E(ldrb_imm, 0, 6, 3); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(strb_w, 0, 4, B_ON)
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 3); E(b_cond, "ap_x", "ne")
    E(mov_reg, 0, 4); imm32(1, FS.SLOT); E(ldrb_imm, 1, 1, 0); E(bl, "c_fsget")
    lab("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    FS.code(c, T, L, prev)
