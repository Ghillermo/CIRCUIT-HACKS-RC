"""SC52.8 (vcf21_dsp.use_osc1x + gentab.use_xtf): the one-oscillator sub / noise on the emulated core 0 (emu_wt_dsp's harness), against SC52.7.

    python tools/emu_osc1x_dsp.py SC52.8.bin manifest.json SC52.7.bin manifest.json

  * the program ends before the tables (TF in X now);
  * the sub / noise words at 0 = SC52.7 sample for sample (saw and sine, the filter on: TF read from X); two oscillators too;
  * the sub's level 127: a partial at half the note (as strong as the note's, within 6 dB); 64: about 6 dB less;
  * the noise's level 127: the energy off the note's harmonics up (> -20 dB of the total, the filter on), 0: none;
  * envelope -> sub with the level at 0: the sub there (the sustained envelope); LFO -> noise with the level at 0: the noise there.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_wt_dsp as W  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import gentab as G  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402

V, N, RING, OSB, GD, PL = W.V, W.N, W.RING, W.OSB, W.GD, W.PL


def tabs(xtf):
    t = G.tables()
    na, nd, ne = G.N_TATK, G.N_TDEC, G.N_TEXP
    if xtf:
        ta = 0x4000 - (na + nd + ne)
        at = dict(TATK=ta, TDEC=ta + na, TEXP=ta + na + nd)
        return [('p', at[k], t[k][1]) for k in at] + [('x', G.XT_TF, t["TF"][1]), ('x', G.XT_TINC, t["TINC"][1]), ('x', G.XT_TLFO, t["TLFO"][1])]
    ta = 0x4000 - (na + nd + G.N_TF + ne)
    at = dict(TATK=ta, TDEC=ta + na, TF=ta + na + nd, TEXP=ta + na + nd + G.N_TF)
    return [('p', at[k], t[k][1]) for k in at] + [('x', G.XT_TINC, t["TINC"][1]), ('x', G.XT_TLFO, t["TLFO"][1])]


def renderer(img, man, xtf, nb=136):
    PL.adopt(man["report"])
    gt = tabs(xtf)
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, w1, p1, om=None, blkx=None, extra=None):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note),
                       (V.P_FILT, -20 & 0xFFFFFF), (V.P_LRATE, 60)):
            blk[k_] = v_
        for k_, v_ in (blkx or {}).items(): blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = w1, p1
        for k_, v_ in (extra or {}).items(): osb[k_] = v_
        omw = [(v & 0xFFFFFF) for v in (om or [])]; omw += [0] * (2 * V.VBS - len(omw))
        out = []
        for b in range(nb):
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', VD.OM_T, omw)] + gt
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:])
    return render


def band(x, f, w=0.1):
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / 48000)
    return p[(fr > f * (1 - w)) & (fr < f * (1 + w))].sum()


def offharm(x, f0):
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / 48000)
    k = fr / f0; near = np.abs(k - np.round(k)) < 0.08
    return 10 * np.log10(p[~near & (fr > 20)].sum() / p.sum())


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dw = int(man["report"]["sc16"]["dsp_words"], 16)
    end = 0x4000 - (G.N_TATK + G.N_TDEC + G.N_TEXP)
    check(dw <= end, f"core 0 ends at P:${dw:x} (the tables from ${end:x})")
    old = renderer(prev, pman, False)
    VD.OSC1X = True; new = renderer(img, man, True)
    so = VD.SX_OFF
    def om(sub=0, sl=0, se=0, nz=0, nl=0, ne=0):
        w = [0] * 16; w[so], w[so + 1], w[so + 2], w[so + 4], w[so + 5], w[so + 6] = sub, sl, se, nz, nl, ne
        return w
    for w1, nm in ((84, "saw"), (0, "sine")):
        a, b = old(48, w1, 50), new(48, w1, 50, om())
        check(np.array_equal(a, b), f"{nm}, the words at 0: SC52.7's output ({np.abs(a - b).max():.2e})")
    O2 = VD.OS2B0 - VD.OSB0
    for nm, w, fm in (("saw + saw", 84, 64), ("sine + sine, FM 80", 0, 80)):
        ex = {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 48, O2 + 2: w, O2 + 3: 50, O2 + 6: fm, O2 + 4: 64}
        a, b = old(48, w, 50, extra=ex), new(48, w, 50, om(), extra=ex)
        check(np.array_equal(a, b), f"two oscillators, {nm}: SC52.7's output ({np.abs(a - b).max():.2e})")
    NT = 60; f0 = 440 * 2 ** ((NT - 69) / 12)
    x0 = new(NT, 0, 50, om())
    xs = new(NT, 0, 50, om(sub=127)); xh = new(NT, 0, 50, om(sub=64))
    s0, s1, s2, n1 = band(x0, f0 / 2), band(xs, f0 / 2), band(xh, f0 / 2), band(xs, f0)
    r = 10 * np.log10(s1 / n1); d = 10 * np.log10(s1 / s2)
    check(s1 > 1000 * max(s0, 1e-12) and abs(r) < 6, f"sub 127: half the note {r:+.1f} dB of the note (none before)")
    check(4 < d < 8, f"sub 64: {d:.1f} dB below 127")
    xn = new(NT, 0, 50, om(nz=127))
    check(offharm(xn, f0) > -20 and offharm(x0, f0) < -30, f"noise 127: off-harmonic energy {offharm(xn, f0):.1f} dB (none: {offharm(x0, f0):.1f})")
    g = {VD.GATE: 1, V.P_ATK: 0, V.P_SUS: 127}
    xe = new(NT, 0, 50, om(se=63), blkx=g); x0g = new(NT, 0, 50, om(), blkx=g)
    check(band(xe, f0 / 2) > 100 * max(band(x0g, f0 / 2), 1e-12), "envelope -> sub (level 0, the gate on): the sub")
    xl = new(NT, 0, 50, om(nl=63))
    check(offharm(xl, f0) > -25, f"LFO -> noise (level 0): the noise ({offharm(xl, f0):.1f} dB)")
    print(f"{man.get('marker', '?')} OSC1X DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) else 0)
