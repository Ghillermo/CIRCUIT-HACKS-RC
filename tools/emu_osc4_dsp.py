"""SC52.4 (vcf21_dsp.use_osc4): the two oscillators on the emulated core 0 (emu_wt_dsp's harness, OSC 2 at the same note), against SC52.3.

    python tools/emu_osc4_dsp.py SC52.4.bin manifest.json SC52.3.bin manifest.json

  * FM at its centre (64) = SC52.3 with FM 0, sample for sample past the first blocks (saw + saw, sine + sine);
  * the hard sync: the output's partials on the note's harmonics (energy off them < -25 dB; SC52.3's sync: about -5 dB), its sweep raises the
    brightness;
  * FM right of the centre: the same amount as SC52.3's (64 + 16 = its 32) with far less energy off the harmonics below 8 kHz (the polyBLEP with
    FM); left of the centre (OSC 1 -> OSC 2): OSC 1 alone (MIX 0) is the unmodulated one, OSC 2 alone (MIX 127) is modulated; the far end
    (50 / 50): both;
  * the bitwise smoothing: less energy above 8 kHz than SC52.3's xor;
  * the depths at OM_T: env -> MIX moves the output towards OSC 2, LFO -> FM changes it (both 0: nothing).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_wt_dsp as W  # noqa: E402
import study_alias_dsp as SD  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402

V, N, RING, OSB, GD, PL = W.V, W.N, W.RING, W.OSB, W.GD, W.PL
O2 = VD.OS2B0 - VD.OSB0


def renderer(img, man, nb=24, xtab=True):
    PL.adopt(man["report"])
    gt = W.gentabs(xtab)
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, w1, p1, extra, om=None, blkx=None):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note)):
            blk[k_] = v_
        for k_, v_ in (blkx or {}).items(): blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = w1, p1
        for k_, v_ in extra.items(): osb[k_] = v_
        omw = [(v & 0xFFFFFF) for v in (om or [0] * 7)] + [0] * (2 * V.VBS - 7)
        out = []
        for b in range(nb):
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0])] + gt
            if hasattr(VD, "OM_T") and VD.OSC4: mem.append(('x', VD.OM_T, omw))
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:])
    return render


def hi(x, f=8000):
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / 48000)
    return 10 * np.log10(p[fr > f].sum() / p.sum())


def centroid(x):
    p = np.abs(np.fft.rfft(x * np.hanning(len(x)))); fr = np.fft.rfftfreq(len(x), 1 / 48000)
    return float((p * fr).sum() / p.sum())


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import gentab as G
    dw = int(man["report"]["sc16"]["dsp_words"], 16)
    check(dw <= G.GEN_TATK, f"core 0 ends at P:${dw:x} (the tables from ${G.GEN_TATK:x})")
    VD.OSC4 = False; old = renderer(prev, pman, nb=24)
    VD.OSC4 = True; new = renderer(img, man, nb=24)
    note = 84
    base = lambda w2, p2, **k: {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: note, O2 + 2: w2, O2 + 3: p2, **{O2 + int(a[1:]): v for a, v in k.items()}}
    for nm, w1, p1, w2, p2 in (("saw + saw", 84, 0, 84, 0), ("sine + sine", 0, 50, 0, 50)):
        a = new(note, w1, p1, base(w2, p2, o4=64, o6=64)); b = old(note, w1, p1, base(w2, p2, o4=64, o6=0))
        d = float(np.abs(a - b).max())
        check(d < 1e-6, f"{nm}, MIX 64, FM at the centre = SC52.3's FM 0 (largest difference {d:.2e})")
    s_new = new(note, 84, 0, base(84, 0, o4=127, o5=1, o8=40, o6=64)); s_old = old(note, 84, 0, base(84, 0, o4=127, o5=1, o8=40))
    an, ao = SD.asr(s_new, note), SD.asr(s_old, note)
    check(an[0] < -25 and an[0] < ao[0] - 10, f"the sync: off the harmonics {an[0]:.1f} dB (SC52.3 {ao[0]:.1f})")
    s0 = new(note, 84, 0, base(84, 0, o4=127, o5=1, o8=0, o6=64)); s80 = new(note, 84, 0, base(84, 0, o4=127, o5=1, o8=80, o6=64))
    check(centroid(s80) > 1.3 * centroid(s0), f"the sync's sweep: brighter ({centroid(s0):.0f} -> {centroid(s80):.0f} Hz)")
    fn = new(note, 84, 0, base(0, 50, o6=80)); fo = old(note, 84, 0, base(0, 50, o6=32))
    a1, a2 = SD.asr(fn, note), SD.asr(fo, note)
    check(a1[1] < a2[1] - 15, f"FM right (64 + 16 = SC52.3's 32), saw <- sine: below 8 kHz {a1[1]:.1f} dB (SC52.3 {a2[1]:.1f})")
    ref1 = new(note, 0, 50, base(0, 50, o4=0, o6=64)); l1 = new(note, 0, 50, base(0, 50, o4=0, o6=48))
    check(float(np.abs(l1 - ref1).max()) < 1e-6, "FM left, MIX 0: OSC 1 unmodulated")
    ref2 = new(note, 0, 50, base(0, 50, o4=127, o6=64)); l2 = new(note, 0, 50, base(0, 50, o4=127, o6=48))
    check(float(np.abs(l2 - ref2).max()) > 0.05, "FM left, MIX 127: OSC 2 modulated")
    r1 = new(note, 0, 50, base(0, 50, o4=0, o6=127)); r2 = new(note, 0, 50, base(0, 50, o4=127, o6=127))
    check(float(np.abs(r1 - ref1).max()) > 0.05 and float(np.abs(r2 - ref2).max()) > 0.05, "FM at the far right: both oscillators modulated")
    xn = new(note, 84, 0, base(0, 50, o5=2, o8=100, o6=64)); xo = old(note, 84, 0, base(0, 50, o5=2, o8=100))
    xa, xb = SD.asr(xn, note), SD.asr(xo, note)
    check(xa[0] < xb[0] - 4, f"xor smoothed: off the harmonics {xa[0]:.1f} dB (SC52.3 {xb[0]:.1f}); above 8 kHz {hi(xn):.1f} dB of the total (SC52.3 {hi(xo):.1f})")
    g = {VD.GATE: 1, VD.P_ATK: 0, VD.P_SUS: 127}
    m0 = new(note, 84, 0, base(0, 50, o4=0, o6=64), blkx=g); me = new(note, 84, 0, base(0, 50, o4=0, o6=64), om=[0, 63, 0, 0, 0, 0, 0], blkx=g)
    o2only = new(note, 84, 0, base(0, 50, o4=127, o6=64), blkx=g)
    check(np.abs(me - o2only).mean() < np.abs(m0 - o2only).mean(), "env -> MIX: towards OSC 2")
    lf0 = new(note, 84, 0, base(0, 50, o4=0, o6=64), blkx={VD.P_LRATE: 100}); lf = new(note, 84, 0, base(0, 50, o4=0, o6=64), om=[0, 0, 0, 0, 63, 0, 0], blkx={VD.P_LRATE: 100})
    ef = new(note, 84, 0, base(0, 50, o4=0, o6=64), om=[0, 0, 0, 0, 0, 63, 0], blkx=g)
    check(float(np.abs(ef - m0).max()) > 1e-2, f"env -> FM: the output moves ({float(np.abs(ef - m0).max()):.3f})")
    lm = new(note, 84, 0, base(0, 50, o4=0, o6=64), om=[63, 0, 0, 0, 0, 0, 0], blkx={VD.P_LRATE: 100})
    print(f"info: LFO -> FM {float(np.abs(lf - lf0).max()):.3f}, LFO -> MIX {float(np.abs(lm - lf0).max()):.3f} (0 = the harness's LFO still)")
    print(f"{man.get('marker', '?')} OSC4 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    import gentab
    gentab.use_xtab()
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
