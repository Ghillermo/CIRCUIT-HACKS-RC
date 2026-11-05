"""The 8-operator FM of the own synth of MIDI 1 / 2 (the user, 2026-11-04: «one FM, up to 8 operators, on pad 24», «Discard old FM», «Old patches load
into the new one», «DX7 style» envelopes, DX7 .syx import on the card app): the ARM side of granular_dsp / vcf21_dsp.use_fm8 (part 1).

This file: the data model, the tables, the conversion of a 4-operator patch (fmeng's 16 parameters) and a reference model of the engine's tick
(the ARM code is tested against it).

Parameters of a track (PLEN bytes, native DX7 units where the DX7 has them):
  operator k (0..7) at 24 k:  + 0..3 R1-R4, + 4..7 L1-L4 (0..99), + 8 break point, + 9 / 10 left / right depth (0..99), + 11 / 12 left / right
                              curve (0..3: -LIN, -EXP, +EXP, +LIN), + 13 rate scaling (0..7), + 14 amp mod sens (0..3), + 15 velocity sens (0..7),
                              + 16 output level (0..99), + 17 mode (0 ratio, 1 fixed), + 18 coarse (0..31), + 19 fine (0..99), + 20 detune
                              (0..14, 7 = none), + 21..23 spare;
  the pitch envelope at 192:  R1-R4, L1-L4 (50 = no shift);
  globals at 200:             + 0 algorithm (0..47: 0-15 the 4-operator engine's, 16-47 the DX7's 1-32), + 1 feedback (0..127, the coefficient
                              ~ fb^2 as the 4-operator engine's), + 2 oscillator key sync (the phases from 0 at a new note), + 3 transpose
                              (0..48, 24 = none), + 4..10 the DX7 LFO (speed, delay, PMD, AMD, sync, wave, PMS: kept for the import), + 11 noise
                              (0..127), + 12 the noise's operator (0..7).

Units: an envelope / attenuation unit u = 1/256 octave of amplitude (0.0235 dB); a DX7 level step = 32 u (0.75 dB); envelope levels e = L x 32
(0..EMAX), with 8 fractional bits in the state.  AMP = AMP0 x 2^(-att / 256), att = (EMAX - e) + (99 - OL) x 32 + velocity + level scaling."""
from __future__ import annotations
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmeng as FE  # noqa: E402

OPS = 8
OPB = 24
PEG = 192
GLB = 200
PLEN = 216
(O_R, O_L, O_BP, O_LD, O_RD, O_LC, O_RC, O_RS, O_AMS, O_KVS, O_OL, O_MODE, O_CRS, O_FINE, O_DET) = (0, 4, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                                                                                                    18, 19, 20)
G_ALG, G_FB, G_SYNC, G_TRN, G_LFO, G_NZ, G_NZOP = 0, 1, 2, 3, 4, 11, 12
NALG = 48

EMAX = 99 * 32
STEP = 32                                       # u a DX7 level step
FLOOR = 1800                                    # a rising stage starts here at least (the DX7's attack jump)
ATT_MUL = 4                                     # a rising stage is that much faster
AMP0 = 126                                      # AMP = EXP[f] x AMP0 >> q (0x7E0000 at att 0: the 4-operator engine's full level)
EXP = [round(65535 * 2 ** (-f / 256)) for f in range(256)]
SLOPE = [round(256 * 0.04 * 2 ** (r / 6.75)) for r in range(128)]    # rate -> u / ms x 256 (rate 0: 79 s for the whole range; 99: ~3 ms)
VEL_K = 49                                      # att += KVS x (127 - velocity) x VEL_K >> 5 (KVS 7, velocity 0: ~32 dB)
LS_K = 7                                        # att += depth x semitones past the break point x LS_K >> 4 (linear curves; 99, 4 octaves: ~48 dB)
RS_K = 5                                        # rate += RS x (note - 24) x RS_K >> 6
PEG_C = 50 * 32                                 # the pitch envelope's centre
PEG_K = 1024 * 4096 // (49 * 32)               # 1/256 octave = (pe - PEG_C) x PEG_K >> 12 (L 99 = +4 octaves)
FIX = [round(10 ** (f / 100) * (1 << 40) / 48000 / 8) for f in range(100)]    # fixed mode: R = FIX[fine] x 8 x 10^c / inc ... (1 Hz base)
KW_CAR = 0x3FFFFF
M_FULL = 0x7FFFFF
THR = 16                                        # an AMP is sent again when its attenuation moved this much (the DSP smooths AMP)


# ---------------------------------------------------------------------------------------------------------------------------- the algorithms
# The DX7's 32 (modulation pairs (source, destination), carriers, feedback (source, destination)): the routing of the DX7 (as the msfa / Dexed
# table describes it, decoded to pairs); the 4-operator engine's 16 from fmeng.ALGS (op 4 of the "pitch" ones is not heard: the pitch envelope).
DX7 = [
    ([(6, 5), (5, 4), (4, 3), (2, 1)], [1, 3], (6, 6)), ([(6, 5), (5, 4), (4, 3), (2, 1)], [1, 3], (2, 2)),
    ([(6, 5), (5, 4), (3, 2), (2, 1)], [1, 4], (6, 6)), ([(6, 5), (5, 4), (3, 2), (2, 1)], [1, 4], (4, 6)),
    ([(6, 5), (4, 3), (2, 1)], [1, 3, 5], (6, 6)), ([(6, 5), (4, 3), (2, 1)], [1, 3, 5], (5, 6)),
    ([(6, 5), (5, 3), (4, 3), (2, 1)], [1, 3], (6, 6)), ([(6, 5), (5, 3), (4, 3), (2, 1)], [1, 3], (4, 4)),
    ([(6, 5), (5, 3), (4, 3), (2, 1)], [1, 3], (2, 2)), ([(6, 4), (5, 4), (3, 2), (2, 1)], [1, 4], (3, 3)),
    ([(6, 4), (5, 4), (3, 2), (2, 1)], [1, 4], (6, 6)), ([(6, 3), (5, 3), (4, 3), (2, 1)], [1, 3], (2, 2)),
    ([(6, 3), (5, 3), (4, 3), (2, 1)], [1, 3], (6, 6)), ([(6, 4), (5, 4), (4, 3), (2, 1)], [1, 3], (6, 6)),
    ([(6, 4), (5, 4), (4, 3), (2, 1)], [1, 3], (2, 2)), ([(6, 5), (4, 3), (5, 1), (3, 1), (2, 1)], [1], (6, 6)),
    ([(6, 5), (4, 3), (5, 1), (3, 1), (2, 1)], [1], (2, 2)), ([(6, 5), (5, 4), (4, 1), (3, 1), (2, 1)], [1], (3, 3)),
    ([(6, 5), (6, 4), (3, 2), (2, 1)], [1, 4, 5], (6, 6)), ([(6, 4), (5, 4), (3, 2), (3, 1)], [1, 2, 4], (3, 3)),
    ([(6, 5), (6, 4), (3, 2), (3, 1)], [1, 2, 4, 5], (3, 3)), ([(6, 5), (6, 4), (6, 3), (2, 1)], [1, 3, 4, 5], (6, 6)),
    ([(6, 5), (6, 4), (3, 2)], [1, 2, 4, 5], (6, 6)), ([(6, 5), (6, 4), (6, 3)], [1, 2, 3, 4, 5], (6, 6)),
    ([(6, 5), (6, 4)], [1, 2, 3, 4, 5], (6, 6)), ([(6, 4), (5, 4), (3, 2)], [1, 2, 4], (6, 6)),
    ([(6, 4), (5, 4), (3, 2)], [1, 2, 4], (3, 3)), ([(5, 4), (4, 3), (2, 1)], [1, 3, 6], (5, 5)),
    ([(6, 5), (4, 3)], [1, 2, 3, 5], (6, 6)), ([(5, 4), (4, 3)], [1, 2, 3, 6], (5, 5)),
    ([(6, 5)], [1, 2, 3, 4, 5], (6, 6)), ([], [1, 2, 3, 4, 5, 6], (6, 6)),
]
assert len(DX7) == 32
DX8 = [                                                              # (use_alg8) eight operators, algorithms 49-56
    ([(8, 7), (7, 6), (6, 5), (4, 3), (3, 2), (2, 1)], [1, 5], (8, 8)),                   # two 4-operator stacks
    ([(2, 1), (4, 3), (6, 5), (8, 7)], [1, 3, 5, 7], (8, 8)),                             # four 2-operator pairs
    ([(8, 7), (7, 6), (6, 5), (5, 4), (4, 3), (3, 2), (2, 1)], [1], (8, 8)),              # an 8-operator stack
    ([(k, 1) for k in range(2, 9)], [1], (8, 8)),                                         # seven modulators on one carrier
    ([], list(range(1, 9)), (8, 8)),                                                      # eight carriers (organ)
    ([(3, 2), (2, 1), (6, 5), (5, 4), (8, 7)], [1, 4, 7], (8, 8)),                        # three stacks: 3, 3, 2
    ([(2, 1), (4, 3), (8, 7), (7, 6), (6, 5)], [1, 3, 5], (8, 8)),                        # two pairs and a 4-operator stack
    (DX7[0][0] + [(8, 7)], DX7[0][1] + [7], DX7[0][2]),                                   # the DX7's algorithm 1 and a pair
]
ALG8 = False


def use_alg8():
    """SC51.8 / Beta 5.21 (the user, 2026-11-05: «how do I create or load more operators?» -> «Add 8 new»): no algorithm used operators 7-8; now
    eight more, 49-56 (DX8), with N = 8: two 4-operator stacks, four pairs, an 8-operator stack, seven modulators on one carrier, eight carriers, three
    stacks 3 / 3 / 2, two pairs and a 4-operator stack, the DX7's algorithm 1 and a pair (the question said «two 3-op stacks + 2 pairs»: ten
    operators; this one is in its place)."""
    global ALG8, NALG
    ALG8, NALG = True, 56
    import fm8arm
    import fm8ui
    fm8arm.NALG = NALG
    fm8ui.make_kd()
OLD_DEF = [  # the 4-operator engine's ALGS as (mods, carriers, feedback op or 0, pitch, noise op, sus, det, relofs)
    (((4, 3), (3, 2), (2, 1)), (1,), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 2), (3, 2), (2, 1)), (1,), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 1), (3, 2), (2, 1)), (1,), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 3), (3, 1), (2, 1)), (1,), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 3), (2, 1)), (1, 3), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 1), (4, 2), (4, 3)), (1, 2, 3), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((4, 3),), (1, 2, 3), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    ((), (1, 2, 3, 4), 4, 0, 1, (1, 1, 1, 1), (1, 1, 1, 1), (0, 0, 0, 0)),
    (((2, 1),), (1,), 2, 1, 1, (0, 0, 0, 0), (1, 1, 1, 1), (0, -8, 0, -10)),
    (((2, 1),), (1,), 2, 1, 3, (0, 0, 0, 0), (1, 1, 1, 1), (0, -6, 0, -8)),
    (((2, 1), (3, 1), (4, 1)), (1,), 4, 0, 1, (0, 0, 0, 0), (1, 1.414, 2.71, 3.49), (0, -4, -4, -4)),
    (((3, 2), (2, 1)), (1,), 3, 1, 1, (0, 0, 0, 0), (1, 1, 1, 1), (0, -6, -6, 0)),
    (((2, 1), (4, 3)), (1, 3), 4, 0, 1, (0, 0, 0, 0), (1, 3.5, 2.0, 2.76), (6, 0, 6, 0)),
    (((2, 1), (3, 1)), (1, 4), 4, 0, 1, (0, 0, 0, 0), (1, 2.76, 5.4, 2.0), (8, 0, -4, 8)),
    (((2, 1), (4, 3)), (1, 3), 4, 0, 1, (1, 1, 1, 1), (1.0, 1.0, 1.007, 1.007), (0, 0, 0, 0)),
    (((4, 1), (4, 2), (4, 3)), (1, 2, 3), 4, 0, 1, (1, 1, 1, 1), (0.994, 1.0, 1.006, 1.0), (0, 0, 0, 0)),
]
for _i, _x in enumerate(FE.ALGS):                                   # the same routing as fmeng's table
    _m, _c, _fb = OLD_DEF[_i][:3]
    _b = _x["b"]
    _mask = sum(1 << (4 * (d - 1) + (s - 1)) for s, d in _m) | ((1 << (5 * (_fb - 1))) if _fb else 0)
    assert struct.unpack_from("<H", _b, 0)[0] == _mask and _b[2] == sum(1 << (c - 1) for c in _c), _x["name"]
ALEN = 16
A_N, A_CAR, A_FBS, A_FBD, A_NZ, A_FAM, A_USED, A_MASK = 0, 1, 2, 3, 4, 5, 6, 8     # an entry: N, carriers, feedback source / destination (0xFF
                                                                          # none), the noise's operator, the family (overlay colour), the operators
                                                                          # heard or modulating, the mask (bit 8 d + s: s modulates d)


def alg_entry(mods, car, fb, nz=0, fam=0):
    n = max([s for s, d in mods] + [d for s, d in mods] + list(car) + ([fb[0], fb[1]] if fb else []))
    n = 4 if n <= 4 else 6 if n <= 6 else 8
    mask = sum(1 << (8 * (d - 1) + (s - 1)) for s, d in mods)
    fs, fd = (fb[0] - 1, fb[1] - 1) if fb else (0xFF, 0xFF)
    used = sum(1 << (o - 1) for o in set([s for s, d in mods] + list(car)))
    return struct.pack("<7BxQ", n, sum(1 << (c - 1) for c in car), fs, fd, nz, fam, used, mask)


def algs():
    out = bytearray()
    for i, (m, c, fb, pitch, nz, sus, det, rof) in enumerate(OLD_DEF):
        out += alg_entry(m, c, (fb, fb) if fb else None, nz - 1, FE.ALGS[i]["fam"])
    for m, c, fb in DX7 + (DX8 if ALG8 else []):
        out += alg_entry(m, c, fb, 0, 4)
    assert len(out) == NALG * ALEN
    return bytes(out)


def alg_of(table, i):
    n, car, fs, fd, nz, fam, used, mask = struct.unpack_from("<7BxQ", table, ALEN * i)
    return dict(n=n, car=car, fs=fs, fd=fd, nz=nz, fam=fam, used=used, mask=mask)


# ---------------------------------------------------------------------------------------------------------------------------- 4-op -> 8-op
def rate_of_slope(s):                                                # u / ms -> the nearest rate
    return max(0, min(99, round(6.75 * math.log2(max(s, 1e-9) / 0.04))))


ATK2R = [99 if FE.ATK_MS[i] == 0 else rate_of_slope((EMAX - FLOOR) / FE.ATK_MS[i] / ATT_MUL) for i in range(32)]
REL2R = [rate_of_slope(369.3 / FE.REL_TAU[i]) for i in range(64)]   # an exponential decay of time constant tau = 8.686 / tau dB / ms


RAT256 = [round(256 * r) for r in FE.RATIOS]                       # fmeng's "rat" table
OLT = [0 if lev == 0 else max(0, min(99, round(99 + 40 * math.log10(lev / 127) / 0.75))) for lev in range(128)]   # level (amp ~ lev^2) -> OL
DET4096 = [[round(4096 * d) for d in x[6]] for x in OLD_DEF]
KVS_ALG = [min(7, round(FE.VS[i] / 48)) for i in range(16)]
SUSM = [sum(1 << k for k in range(4) if x[5][k]) for x in OLD_DEF]


def ratio_cf(x):                                                     # a ratio x 4096 -> (coarse, fine) (integers: the ARM's)
    if x < 4096:
        return 0, max(0, min(99, ((x - 2048) * 100 + 1024) // 2048))
    c = min(31, x >> 12)
    return c, max(0, min(99, ((x - c * 4096) * 100 + c * 2048) // (c * 4096)))


def op_default(k):                                                   # an operator 5-8 of a converted patch: silent, ratio 1, held
    b = bytearray(OPB)
    b[O_R:O_R + 8] = bytes((99, 99, 99, 60, 99, 99, 99, 0))
    b[O_BP], b[O_CRS], b[O_DET] = 39, 1, 7
    return bytes(b)


def convert4(p16):
    """fmeng's 16 parameters (V2) -> PLEN bytes (the ARM's c_fm8conv, byte for byte)."""
    rat, lev, atk, alg, fb, nz, rel = p16[0:4], p16[4:8], p16[8:12], (p16[12] >> 3) & 15, p16[13], p16[14], p16[15]
    m, c, fbop, pitch, nzop, sus, det, rof = OLD_DEF[alg]
    out = bytearray(PLEN)
    for k in range(4):
        b = OPB * k
        idx, step = (rat[k] * 24) >> 7, (((rat[k] * 24) & 127) * 171) >> 12
        out[b + O_CRS], out[b + O_FINE] = ratio_cf(RAT256[idx] * DET4096[alg][k] >> 8)
        out[b + O_DET] = min(14, 7 + (step * 3 >> 1))
        out[b + O_OL] = 0 if pitch and k == 3 else OLT[lev[k]]
        r4 = REL2R[max(0, min(63, (rel >> 1) + rof[k]))]
        a_ = atk[k]
        if a_ >= FE.CENTRE:
            r1, perc, rd = ATK2R[(a_ - FE.CENTRE) >> 1], not (SUSM[alg] >> k & 1), r4
        else:
            r1, perc, rd = 99, True, REL2R[a_]
        out[b + O_R:b + O_R + 4] = bytes((r1, rd if perc else 99, 99, min(r4, rd) if perc else r4))
        out[b + O_L:b + O_L + 4] = bytes((99, 0 if perc else 99, 0 if perc else 99, 0))
        car = (k + 1) in c
        out[b + O_KVS] = 0 if car else KVS_ALG[alg]
        out[b + O_BP], out[b + O_RD] = 39, 0 if car else min(99, FE.KS[alg] * 4)
        out[b + O_RS] = min(7, FE.KS[alg])
    for k in range(4, 8):
        out[OPB * k:OPB * k + OPB] = op_default(k)
    if pitch:                                                        # op 4 = the drop: L1 = 50 + its depth, back to 50 at its release
        d = min(49, lev[3] * 36 // 127)
        out[PEG:PEG + 8] = bytes((99, REL2R[max(0, min(63, (rel >> 1) + rof[3]))], 99, 99, 50 + d, 50, 50, 50))
    else:
        out[PEG:PEG + 8] = bytes((99, 99, 99, 99, 50, 50, 50, 50))
    g = GLB
    out[g + G_ALG], out[g + G_FB], out[g + G_SYNC], out[g + G_TRN] = alg, fb, 0 if SUSM[alg] == 15 else 1, 24
    out[g + G_NZ], out[g + G_NZOP] = nz, nzop - 1
    return bytes(out)


DEFAULT = convert4(FE.DEFAULTS2)


# ---------------------------------------------------------------------------------------------------------------------------- DX7 -> 8-op
# The DX7 import of the card app (tools/sd_app.html, dx7Parse / dx7ToFm8 / fm8Rec, byte for byte; the user, 2026-11-05: «do dx7 import via app»).
# A bulk dump (F0 43 0n 09 20 00, 32 voices x 128 packed bytes, a check byte, F7) or a single voice (F0 43 0n 00 01 1B, 155 bytes, a check byte,
# F7); the DX7 stores operator 6 first.  Every field masked to its bits, then limited to its range (dumps with garbage exist).  Operators 7-8:
# op_default (silent); no noise; the LFO kept in G_LFO for later.
FB_DX7 = [0, 16, 23, 32, 45, 64, 90, 127]           # the DX7's feedback 0..7 -> fm8's (as fm8inst)
VOP = ("r1", "r2", "r3", "r4", "l1", "l2", "l3", "l4", "bp", "ld", "rd", "lc", "rc", "rs", "ams", "kvs", "ol", "mode", "crs", "fine", "det")
VMAX = dict(r1=99, r2=99, r3=99, r4=99, l1=99, l2=99, l3=99, l4=99, bp=99, ld=99, rd=99, lc=3, rc=3, rs=7, ams=3, kvs=7, ol=99, mode=1, crs=31,
            fine=99, det=14)
VGLB = ("pr1", "pr2", "pr3", "pr4", "pl1", "pl2", "pl3", "pl4", "alg", "fb", "oks", "lfs", "lfd", "pmd", "amd", "lks", "lfw", "pms", "trn")
GMAX = dict(pr1=99, pr2=99, pr3=99, pr4=99, pl1=99, pl2=99, pl3=99, pl4=99, alg=31, fb=7, oks=1, lfs=99, lfd=99, pmd=99, amd=99, lks=1, lfw=5,
            pms=7, trn=48)


def dx7_unpack(v):
    """128 packed bytes (VMEM) -> ({op 1..6: fields}, globals, name)."""
    ops = {}
    for i in range(6):
        b = v[17 * i:17 * i + 17]
        o = dict(zip(VOP[:11], b[:11]))
        o.update(lc=b[11] & 3, rc=b[11] >> 2 & 3, rs=b[12] & 7, det=b[12] >> 3 & 15, ams=b[13] & 3, kvs=b[13] >> 2 & 7, ol=b[14], mode=b[15] & 1,
                 crs=b[15] >> 1 & 31, fine=b[16])
        ops[6 - i] = o
    g = dict(zip(VGLB[:8], v[102:110]))
    g.update(alg=v[110] & 31, fb=v[111] & 7, oks=v[111] >> 3 & 1, lfs=v[112], lfd=v[113], pmd=v[114], amd=v[115], lks=v[116] & 1,
             lfw=v[116] >> 1 & 7, pms=v[116] >> 4 & 7, trn=v[117])
    return ops, g, v[118:128]


def dx7_vced(v):
    """155 unpacked bytes (VCED, a single voice) -> the same."""
    ops = {6 - i: dict(zip(VOP, v[21 * i:21 * i + 21])) for i in range(6)}
    return ops, dict(zip(VGLB, v[126:145])), v[145:155]


def dx7_name(b):
    return "".join(chr(c) if 32 <= c < 127 else " " for c in (x & 127 for x in b)).rstrip()


def dx7_voices(data):
    """A .syx (one or more messages; a bare 4096-byte bank too) -> [(name, ops, globals)], bad check bytes accepted."""
    out = []
    if len(data) == 4096 and data[0] != 0xF0:
        return [(dx7_name(u[2]),) + u[:2] for u in (dx7_unpack(data[128 * k:128 * k + 128]) for k in range(32))]
    i = 0
    while True:
        s = data.find(b"\xF0", i)
        if s < 0: return out
        e = data.find(b"\xF7", s)
        if e < 0: return out
        m, i = data[s:e + 1], e + 1
        if len(m) >= 4104 and m[1] == 0x43 and m[3] == 9:
            for k in range(32):
                u = dx7_unpack(m[6 + 128 * k:6 + 128 * k + 128])
                out.append((dx7_name(u[2]),) + u[:2])
        elif len(m) >= 163 and m[1] == 0x43 and m[3] == 0:
            u = dx7_vced(m[6:6 + 155])
            out.append((dx7_name(u[2]),) + u[:2])


def from_dx7(ops, g):
    """A DX7 voice -> PLEN bytes: DX7 operator k + 1 = fm8's operator k, its fields in fm8's native units."""
    out = bytearray(PLEN)
    for k in range(6):
        o, b = {f: min(VMAX[f], ops[k + 1][f] & 127) for f in VOP}, OPB * k
        out[b + O_R:b + O_R + 8] = bytes(o[f] for f in VOP[:8])
        for at, f in ((O_BP, "bp"), (O_LD, "ld"), (O_RD, "rd"), (O_LC, "lc"), (O_RC, "rc"), (O_RS, "rs"), (O_AMS, "ams"), (O_KVS, "kvs"),
                      (O_OL, "ol"), (O_MODE, "mode"), (O_CRS, "crs"), (O_FINE, "fine"), (O_DET, "det")):
            out[b + at] = o[f]
    for k in range(6, 8):
        out[OPB * k:OPB * k + OPB] = op_default(k)
    q = {f: min(GMAX[f], g[f] & 127) for f in VGLB}
    out[PEG:PEG + 8] = bytes(q[f] for f in VGLB[:8])
    G = GLB
    out[G + G_ALG], out[G + G_FB], out[G + G_SYNC], out[G + G_TRN] = 16 + q["alg"], FB_DX7[q["fb"]], q["oks"], q["trn"]
    out[G + G_LFO:G + G_LFO + 7] = bytes(q[f] for f in ("lfs", "lfd", "pmd", "amd", "lks", "lfw", "pms"))
    return bytes(out)


REC_HDR, REC_SUM0, REC_N = b"FM8\x01", 0x5A38, 224   # fm8store's HDR / SUM0 / RECN (asserted there)


def record(params):
    """An own slot's FM record (fm8store.c_fsput): "FM8" 1, the parameters, their 16-bit sum, 0xFF to 224."""
    s = (REC_SUM0 + sum(params)) & 0xFFFF
    return REC_HDR + bytes(params) + s.to_bytes(2, "little") + b"\xFF" * (REC_N - 6 - PLEN)


# ---------------------------------------------------------------------------------------------------------------------------- reference model
class Voice:
    def __init__(s):
        s.e = [0] * 9                    # x 256
        s.st = [5] * 9
        s.gate = 0
        s.last = [0xFFFF] * 8
        s.e[8] = PEG_C << 8


def ref_tick(P, v, gate, note, vel, dt, new):
    """One tick of a voice: the envelopes, then {op: (att or None, R)} and the pitch factor (x 4096)."""
    g = GLB
    if new:
        for i in range(9): v.st[i] = 0
    elif v.gate and not gate:
        for i in range(9): v.st[i] = 3
    v.gate = gate
    rs_note = max(0, note - 24)
    for i in range(9):
        b = OPB * i if i < 8 else PEG - O_R
        if v.st[i] in (4, 5): continue
        s_ = v.st[i]
        T = P[b + O_L + s_] * STEP << 8
        r = P[b + O_R + s_] + ((P[b + O_RS] * rs_note * RS_K) >> 6 if i < 8 else 0)
        sl = SLOPE[min(127, r)] * dt
        e = v.e[i]
        if T > e:
            if i < 8:
                if e < FLOOR << 8: e = FLOOR << 8
                sl *= ATT_MUL
            e = min(T, e + sl)
        else:
            e = max(T, e - sl)
        v.e[i] = e
        if e == T:
            v.st[i] = 4 if s_ == 2 else 5 if s_ == 3 else s_ + 1
    pu = ((v.e[8] >> 8) - PEG_C) * PEG_K >> 12
    pu += (P[g + G_TRN] - 24) * 85 >> 2
    q, f = pu >> 8, pu & 255
    pf = 4096 if f == 0 else (EXP[256 - f] * 8192) >> 16
    pf = pf << q if q >= 0 else pf >> -q
    out = {}
    for k in range(OPS):
        b = OPB * k
        if P[b + O_OL] == 0 or v.e[k] < 256:
            att = None
        else:
            att = (EMAX - (v.e[k] >> 8)) + (99 - P[b + O_OL]) * STEP + (P[b + O_KVS] * (127 - vel) * VEL_K >> 5)
            dist = note - (P[b + O_BP] + 21)
            if dist > 0: att += P[b + O_RD] * dist * LS_K >> 4
            elif dist < 0: att += P[b + O_LD] * (-dist) * LS_K >> 4
        out[k] = att
    return out, pf


def amp_of(att):
    if att is None: return 0
    q, f = att >> 8, att & 255
    return 0 if q >= 24 else (EXP[f] * AMP0) >> q


def ratio_r(P, k, inc):
    """R (ratio x 2^16) of operator k before the pitch factor."""
    b = OPB * k
    if P[b + O_MODE]:
        c = P[b + O_CRS] & 3
        return min(0x7FFFFF, ((FIX[P[b + O_FINE]] * 8 // max(1, inc)) * 10 ** c) >> 3)
    x = 2048 if P[b + O_CRS] == 0 else P[b + O_CRS] * 4096
    x = x * (100 + P[b + O_FINE]) // 100
    x = x * (4096 + (P[b + O_DET] - 7) * 4) >> 12
    return x << 4


def install(img, report, base_addr):
    """dspz.add (at the end of the build, after fmeng.use_fm8 left its trampolines in the hole): the engine and the panel at base_addr; every
    trampoline pointed at its label."""
    import ct_fw
    import fm8arm
    import fm8ui
    import fmeng
    import hole
    from thumb import b_w
    BASE = ct_fw.APP_BASE
    L = {k: int(v, 16) for k, v in report["fm8_L"].items()}
    prev = {k: int(v, 16) for k, v in report["fmeng"]["prev"].items()}
    import fm8store
    for k in ("c_mpsz", "c_mpw", "c_mpr"): L[k] = int(report["mpatch"]["labels"][k], 16)
    for k in ("c_curpack", "c_resel"): L[k] = int(report["packio"]["labels"][k], 16)
    prev.update(fm8store.prev_of(img, report))
    import mpatch as MP
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    if fm8ui.HEADS:                                                  # slots 0 / 7 of the template view: jumpflip's heads, ours ahead
        prev["tpad"], prev["tled"] = u(MP.TMPL_VT) & ~1, u(MP.TMPL_VT + 28) & ~1
        assert (prev["tpad"], prev["tled"]) == tuple(int(report["jumpflip"]["labels"][k], 16) for k in ("c_jfpad", "c_jfled"))
    vl = lambda k: int(report["vcf20"]["labels"][k], 16)
    h16 = lambda a_: struct.unpack_from("<H", img, a_ - BASE)[0]
    if fm8ui.NODUAL:                                                 # vcf21's c_vosc head / the note-on's paraphony test
        assert (h16(vl("c_vosc")), h16(vl("c_vosc") + 2)) == (0xB510, 0x4604) and (h16(vl("no_dt")), h16(vl("no_dt") + 2)) == (0x78AB, 0x09DB)
        prev["vosc4"] = vl("c_vosc") + 4
    if fm8ui.V2:
        prev["btn8"] = MP.bw_target(img, MP.BTN_ENTRY, BASE)
    code, labels, T = fm8arm.build(base_addr, L, prev, ui=fm8ui.ui)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for k in fmeng.EXPORTS8:
        at = int(report["fmeng"]["labels"][k], 16)
        assert bytes(img[at - BASE:at - BASE + 4]) == b_w(at, at), k
        img[at - BASE:at - BASE + 4] = b_w(at, labels[k])
        hole.rehash(img, report, at)
    fm8store.hooks(img, report, labels, (base_addr, base_addr + len(code)))
    if fm8ui.HEADS:
        for at, k in ((MP.TMPL_VT, "c_f8hpad"), (MP.TMPL_VT + 28, "c_f8hled")):
            struct.pack_into("<I", img, at - BASE, labels[k] | 1); hole.rehash(img, report, at)
    from thumb import bl as t_bl
    def put(at, enc):
        img[at - BASE:at - BASE + len(enc)] = enc; hole.rehash(img, report, at)
    if fm8ui.NODUAL:
        put(vl("c_vosc"), b_w(vl("c_vosc"), labels["c_f8vosc"]))
        put(vl("no_dt"), t_bl(vl("no_dt"), labels["c_f8dual"]))
    if fm8ui.V2:
        import fm8store as FS_
        ml = lambda k: int(report["mpatch"]["labels"][k], 16)
        put(MP.BTN_ENTRY, b_w(MP.BTN_ENTRY, labels["c_f8btn"]))
        sites = [a_ for a_ in FS_.find_bl(img, BASE, ml("c_mpr")) if ml("mf_c") <= a_ < ml("mf_kn")]
        assert len(sites) == 1, sites
        put(sites[0], t_bl(sites[0], labels["c_f8mpr"]))
        at = ml("ml_l") + 10                                         # mpatch's c_mpleds: movs r2, #COL_DIM ... movs r2, #COL_LIT -> bl c_f8scol + nops
        assert h16(at) == 0x2200 | MP.COL_DIM and ml("ml_w") - at == 12 and h16(ml("ml_w") - 2) == 0x2200 | MP.COL_LIT
        put(at, t_bl(at, labels["c_f8scol"]) + bytes.fromhex("00bf") * 4)
        px = int(report["psave"]["labels"]["c_psxleds"], 16)        # psave's empty slots: violet (FM's colour) -> dim white
        ats = [px + i for i in range(0, 0x80, 2) if h16(px + i) == 0x2200 | 0x49]
        assert len(ats) == 1, ats
        put(ats[0], struct.pack("<H", 0x2202))
    labels.update({f"t_{k}": v for k, v in T.items()})
    return labels, code, {}


if __name__ == "__main__":
    t = algs()
    for i in (0, 8, 16, 19, 47):
        print(i, alg_of(t, i))
    print("ATK2R", ATK2R)
    print("REL2R", REL2R)
    print("DEFAULT", list(DEFAULT[:24]), list(DEFAULT[PEG:]))
