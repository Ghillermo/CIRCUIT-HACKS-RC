"""SC55 (vcf21_dsp.use_fmcap): the own synth's OSC 1 under FM, its BLEP's effective increment held to 3 x its own, on the emulated core 0
(emu_osc1x_dsp's harness without the filter), against SC54.

    python tools/emu_fmcap_dsp.py SC55.bin manifest.json SC54.bin manifest.json [NB]

  * the program ends before the tables;
  * no FM (a saw alone, two oscillators mixed, ring): SC55 = SC54 sample for sample (the cap never acts without FM);
  * the level by note (ideal: flat; FM is in the phase): a saw under FM from a sine OSC 2 an octave up (FM 90, MIX 0), and a pulse under FM,
    the fundamental at C6 / C7 against C4: SC54 down to -4.3 dB at C7, SC55 within 1.5 dB;
  * the energy off the note's harmonics (study_interact's measure, OSC 2 at the same note): no worse than SC54's by more than 1 dB.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_wt_dsp as W  # noqa: E402
import emu_osc1x_dsp as X  # noqa: E402
import study_alias_dsp as SD  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import gentab as G  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402

V, N, RING, OSB, GD, PL = W.V, W.N, W.RING, W.OSB, W.GD, W.PL
O2 = VD.OS2B0 - VD.OSB0


def renderer(img, man, nb):
    PL.adopt(man["report"])
    gt = X.tabs(True)
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, w1, p1, extra):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 127), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note)):
            blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = w1, p1
        for k_, v_ in extra.items(): osb[k_] = v_
        out = []
        for b in range(nb):
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]),
                   ('x', VD.OM_T, [0] * (2 * V.VBS))] + gt
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=40_000_000)
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:])
    return render


def fund(x, note):
    x = x - x.mean(); n = len(x)
    p = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2; f = np.fft.rfftfreq(n, 1 / 48000)
    f0 = 440 * 2 ** ((note - 69) / 12)
    return 10 * np.log10(p[np.abs(f - f0) < 3 * 48000 / n].sum())


def two(note, w2, p2, fm=64, mix=0, ring=0, n2=None):
    return {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: note if n2 is None else n2, O2 + 2: w2, O2 + 3: p2, O2 + 4: mix, O2 + 6: fm, O2 + 7: ring}


def main(img, man, prev, pman, nb=40):
    fails = 0

    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m, flush=True); fails += 0 if c else 1
    dw = int(man["report"]["sc16"]["dsp_words"], 16)
    end = 0x4000 - (G.N_TATK + G.N_TDEC + G.N_TEXP)
    check(dw <= end, f"core 0 ends at P:${dw:x} (the tables from ${end:x}; SC54 ${int(pman['report']['sc16']['dsp_words'], 16):x})")
    new, old = renderer(img, man, nb), renderer(prev, pman, nb)
    same = []
    for what, note, w1, p1, ex in (("a saw alone", 96, 84, 0, {}), ("saw + saw, mix 64", 84, 84, 0, two(84, 84, 0, mix=64)),
                                   ("saw x sine, ring 100", 84, 84, 0, two(84, 0, 50, ring=100))):
        same.append((what, np.array_equal(new(note, w1, p1, ex), old(note, w1, p1, ex))))
    check(all(s for _, s in same), "no FM: SC55 = SC54 sample for sample (" + ", ".join(f"{w} {'=' if s else 'differs'}" for w, s in same) + ")")
    rows, ok = [], True
    for what, w1, p1 in (("saw <- sine", 84, 0), ("pulse 60 <- sine", 126, 60)):
        lv = {}
        for note in (60, 84, 96):
            ex = two(note, 0, 50, fm=90, n2=note + 12)
            lv[note] = (fund(old(note, w1, p1, ex), note), fund(new(note, w1, p1, ex), note))
        d = {n: (lv[n][0] - lv[60][0], lv[n][1] - lv[60][1]) for n in (84, 96)}
        ok &= all(abs(d[n][1]) < 1.5 for n in d)
        rows.append(f"{what}: C6 {d[84][0]:+.1f} -> {d[84][1]:+.1f} dB, C7 {d[96][0]:+.1f} -> {d[96][1]:+.1f} dB")
    check(ok, "the fundamental against C4 under FM 90 (SC54 -> SC55): " + "; ".join(rows))
    rows, ok = [], True
    for what, w1, p1, w2, p2, fm in (("FM 90, saw <- sine", 84, 0, 0, 50, 90), ("FM 127, saw <- sine", 84, 0, 0, 50, 127),
                                     ("FM 80, sine <- saw", 0, 50, 84, 0, 80), ("FM 90, pulse <- sine", 126, 60, 0, 50, 90)):
        for note in (84, 96):
            a0, b0 = SD.asr(old(note, w1, p1, two(note, w2, p2, fm=fm)), note)
            a1, b1 = SD.asr(new(note, w1, p1, two(note, w2, p2, fm=fm)), note)
            ok &= a1 < a0 + 1 and b1 < b0 + 1
            rows.append(f"{what} note {note}: {a0:.1f} -> {a1:.1f} dB (below 8 kHz {b0:.1f} -> {b1:.1f})")
    check(ok, "off the harmonics, OSC 2 at the note (SC54 -> SC55): " + "; ".join(rows))
    return fails


if __name__ == "__main__":
    G.use_xtab()
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()),
                       *(int(v) for v in a[4:])) else 0)
