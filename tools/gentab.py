"""SC49.7: room in the flash: six of the core-0 DSP's tables built at DSP start instead of loaded (the user, 2026-10-29: «Both»: fold the loops,
then the tables at boot).

The core-0 program is one bootstrap block from P:0 (build_sc16.relocate_dsp): every word of it is in the flash at 3 B.  The tables are octaves of
themselves, geometric or reciprocals, so they are made once, before the stock's init (P:$10B):
  * TINC (vcf21_dsp, 129 words): the phase increment of MIDI note n; TINC[n] = (TINC[n + 12] + 1) >> 1 for n = 116..0 from TINC[117..128];
  * TEXP (drums2_dsp, 49 words): 2^((i - 24) / 12) / 4, TEXP[48] clamped to $7FFFFF; TEXP[i] = (TEXP[i + 12] + 1) >> 1 for i = 36..0;
  * TLFO (drums2_dsp, 128 words; the drums' LFO, the own synth's LFO and chorus): 0.1 Hz x 200^(r / 127); TLFO[r + 1] = TLFO[r] x 200^(1 / 127)
    (mpy by the half ratio, asl, rnd) from TLFO[0];
  * TDEC (drums2_dsp COMPACT, 64 words; the drums' and the own synth's decays): exp(-NFR / (FS x 0.04 x 2^(v / 12))); TDEC[v] = TDEC[v + 12]^2
    (mpyr) for v = 51..0 from TDEC[52..63];
  * TATK (drums2_dsp COMPACT, 65 words; the attacks): C / (64 - i), TATK[64] = 0: (C / 128) / (n / 128) by div;
  * TF (drums2_dsp, 64 words; the filters' and the ring mod's coefficient): 2 sin(x), x = pi 30 Hz (7000 / 30)^(i / 63) / FS, x multiplied up as
    TLFO, the sine by its series to x^7.
TINC / TEXP are within 1 LSB of the exact tables (TINC[0] = 2 859: 0.6 cents at most, in the inaudible bottom octave; TEXP[36] = $400000 exact);
TLFO within 0.07 % (58 in 223 696 at the top); TDEC within 18 LSB (the time constants within 0.015 %); TATK within 0.002 %; TF within 0.009 %
(0.15 cents).  The tables go to P:GEN_TATK.. = the last 499 words of program RAM, past the program's end (build_sc16.CODE_P_END = GEN_TATK); their
users read them at those addresses (vcf21_dsp.GENTAB, drums2_dsp.GENTAB).  P:$10B calls init2 (build_sc16.INIT_LABEL): the tables, then
jmp sc_init (which leaves r0 = $2028, as the stock expects).
"""
from __future__ import annotations
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import drums2_dsp as DD  # noqa: E402

GEN_TATK, N_TATK = 0x3E0D, 65
GEN_TDEC, N_TDEC = GEN_TATK + N_TATK, 64
GEN_TF, N_TF = GEN_TDEC + N_TDEC, 64
GEN_TINC, N_TINC = GEN_TF + N_TF, 129
GEN_TEXP, N_TEXP = GEN_TINC + N_TINC, 49
GEN_TLFO, N_TLFO = GEN_TEXP + N_TEXP, 128
assert GEN_TLFO + N_TLFO == 0x4000 and VD.GEN_TINC == GEN_TINC and DD.GEN_TEXP == GEN_TEXP and DD.GEN_TLFO == GEN_TLFO
assert (DD.GEN_TATK, DD.GEN_TDEC, DD.GEN_TF) == (GEN_TATK, GEN_TDEC, GEN_TF)
Q = lambda v: int(round(v * (1 << 23)))
TLFO_QH = Q(200 ** (1 / 127) / 2)                          # the half ratio, a 24-bit fraction
TF_X0, TF_RH = Q(math.pi * DD.D1.FC0 / DD.FS), Q((DD.D1.FC1 / DD.D1.FC0) ** (1 / 63) / 2)
TF_C6, TF_C120, TF_C5040 = Q(1 / 6), Q(1 / 120), Q(1 / 5040)
TATK_C = Q(DD.NFR / (2 * DD.FS * DD.ATK_MAX))               # C / 128 (C = 64 NFR / (FS ATK_MAX)): TATK[64 - n] = (C / 128) / (n / 128)


def use():
    """The two modules' options (before the chain builds its DSP code)."""
    VD.GENTAB = DD.GENTAB = True


def code(base, l, T, do_imm):
    a = D.Asm(base)
    e = lambda *ls: [a.emit(T(x)) for x in ls]
    a.label("init2")
    for seed, at, n in ((l["TINC_S"], GEN_TINC, N_TINC), (l["TEXP_S"], GEN_TEXP, N_TEXP), (l["TDEC_S"], GEN_TDEC, N_TDEC)):
        tag = "%x" % at
        e("move #>$%x,r1" % seed, "move #>$%x,r0" % (at + n - 12))              # the top octave copied
        a.emit(do_imm, 12, "gs" + tag)
        e("move p:(r1)+,a")
        a.label("gs" + tag); e("move a,p:(r0)+")
        e("move #>$%x,r1" % (at + n - 1), "move #>$%x,r0" % (at + n - 13))     # then downwards: each word from the one an octave up
        a.emit(do_imm, n - 12, "gh" + tag)
        if at == GEN_TDEC:                                                      # TDEC: its square
            e("move p:(r1)-,x0", "mpyr x0,x0,a")
        else:                                                                   # TINC / TEXP: (it + 1) >> 1
            e("move p:(r1)-,a", "add #>1,a", "asr a")
        a.label("gh" + tag); e("move a1,p:(r0)-")
    e("move #>$%x,r0" % GEN_TATK, "move #>$400000,b", "move #>$10000,y1", "move #>$%x,x1" % TATK_C)   # TATK: (C / 128) / (n / 128), n = 64..1
    a.emit(do_imm, N_TATK - 1, "ga")
    e("move b,x0", "move x1,a", "andi #$fe,ccr", "rep #24", "div x0,a", "sub y1,b")
    a.label("ga"); e("move a0,p:(r0)+")
    e("clr a", "move a,p:(r0)")                                                 # TATK[64] = 0
    e("move #>$%x,r0" % GEN_TF, "move #>$%x,y1" % TF_X0)                       # TF: x in y1, multiplied up; 2 sin x by its series
    a.emit(do_imm, N_TF, "gf")
    e("move y1,x0", "mpyr x0,x0,a", "move a,y0",                                # y0 = s = x^2
      "move #>$%x,x1" % TF_C5040, "mpyr x1,y0,a", "move #>$%x,b" % TF_C120, "sub a,b",   # 1/120 - s/5040
      "move b,x1", "mpyr x1,y0,a", "move #>$%x,b" % TF_C6, "sub a,b",          # 1/6 - s (1/120 - s/5040)
      "move b,x1", "mpyr x1,y0,a", "move a,x1", "mpyr x1,x0,a",               # x s (...)
      "move x0,b", "sub a,b", "asl b", "move b,p:(r0)+",                       # 2 (x - x s (...))
      "move #>$%x,x1" % TF_RH, "mpyr x1,x0,a", "asl a")
    a.label("gf"); e("move a,y1")
    e("move #>$%x,a" % DD.tables()["TLFO"][0], "move #>$%x,r0" % GEN_TLFO, "move #>$%x,y0" % TLFO_QH)   # TLFO: up from its first word
    a.emit(do_imm, N_TLFO - 1, "gl")
    e("move a1,p:(r0)+", "move a1,x0", "mpy y0,x0,a", "asl a")
    a.label("gl"); e("rnd a")
    e("move a1,p:(r0)")
    a.emit(D.jmp(l["sc_init"]))
    return a.assemble()


def install_dsp(s16):
    """The code after everything else (the last wrapper of the chain's DSP code); P:$10B -> init2; the program must end before the tables."""
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = code(base + len(w), l, s16.T, s16.do_imm)
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped
    s16.INIT_LABEL = "init2"
    s16.CODE_P_END = GEN_TATK


def tables():
    """The exact tables and the generated ones (for the tests)."""
    tinc = [int(round(440 * 2 ** ((n - 69) / 12) / 48000 * (1 << 24))) & 0xFFFFFF for n in range(N_TINC)]
    texp = DD.tables()["TEXP"]
    def gen(t):
        g = list(t)
        for i in range(len(t) - 13, -1, -1): g[i] = (g[i + 12] + 1) >> 1
        return g
    tlfo = DD.tables()["TLFO"]
    g, v = [tlfo[0]], tlfo[0]
    for _ in range(N_TLFO - 1):
        v = (v * TLFO_QH + (1 << 21)) >> 22; g.append(v)
    t = DD.tables()
    dec, atk = t["TDEC"][64:], t["TATK"][:65]
    gd = list(dec)
    for i in range(N_TDEC - 13, -1, -1): gd[i] = mpyr(gd[i + 12], gd[i + 12])
    ga = [(TATK_C << 23) // (n << 16) for n in range(64, 0, -1)] + [0]
    gf, x = [], TF_X0
    for _ in range(N_TF):
        s = mpyr(x, x)
        q = TF_C6 - mpyr(TF_C120 - mpyr(TF_C5040, s), s)
        gf.append(2 * (x - mpyr(mpyr(q, s), x)))
        x = 2 * mpyr(TF_RH, x)
    return dict(TINC=(tinc, gen(tinc)), TEXP=(texp, gen(texp)), TLFO=(tlfo, g), TDEC=(dec, gd), TATK=(atk, ga), TF=(t["TF"], gf))


def mpyr(a, b):
    """mpyr of two positive 24-bit fractions: the product rounded (convergent) to 24 bits."""
    q, r = divmod(a * b, 1 << 23)
    return q + (r > 1 << 22 or (r == 1 << 22 and q & 1))
