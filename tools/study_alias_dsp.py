"""Study (2026-10-26, «Estudia cómo reducir el aliasing y el ruido»): the own synth's oscillator rendered by the emulated DSP (core 0, vpre a block on
the interpreter, emu_poly3_dsp's harness), against study_alias.py's model of the same wave.

    python tools/study_alias_dsp.py BUILD.bin manifest.json

MIDI 1, one oscillator, the chain neutral (no filter, the VCA open): 128 blocks (4096 samples) of a plain saw (WAVE 84, SHAPE 0) at notes 96 and
72, and of a sine (WAVE 0) at note 60; the saw's ASR (aliasing / signal, whole band | below 8 kHz) next to the model's; the sine's noise floor
(everything but its harmonics, against the fundamental).
"""
from __future__ import annotations
import gc, json, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_smstereo_dsp as S  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402
import granular_dsp as GD  # noqa: E402
import poly as PL  # noqa: E402
import study_alias as SA  # noqa: E402
V = S.V
N, RING, OSB = S.N, S.RING, S.OSB
NB = 128


def bh(n):
    k = np.arange(n)
    return 0.35875 - 0.48829 * np.cos(2 * np.pi * k / n) + 0.14128 * np.cos(4 * np.pi * k / n) - 0.01168 * np.cos(6 * np.pi * k / n)


def asr(x, note, harmonics=True):
    n = len(x); x = np.asarray(x, dtype=np.float64); x = x - x.mean()
    p = np.abs(np.fft.rfft(x * bh(n))) ** 2
    f = np.fft.rfftfreq(n, 1 / SA.FS)
    f0 = 440 * 2 ** ((note - 69) / 12)
    sig = np.zeros_like(p, dtype=bool)
    for k in (range(1, int(SA.FS / 2 / f0) + 1) if harmonics else (1,)):
        sig |= np.abs(f - k * f0) < 4.5 * SA.FS / n
    rest = ~sig & ~(f < 4.5 * SA.FS / n)
    if not harmonics:                                         # the noise: everything but the fundamental and its harmonics
        for k in range(2, int(SA.FS / 2 / f0) + 1): rest &= ~(np.abs(f - k * f0) < 4.5 * SA.FS / n)
    lo = f < 8000
    return 10 * math.log10(p[rest].sum() / p[sig].sum() + 1e-30), 10 * math.log10(p[rest & lo].sum() / p[sig].sum() + 1e-30)


def asr_super(x, note, detune=SA.SS_DET if hasattr(SA, "SS_DET") else 0.0183):
    """the supersaw: the signal = the harmonics of each of the seven saws (study_alias.asr_super on any length)"""
    n = len(x); x = np.asarray(x, dtype=np.float64); x = x - x.mean()
    p = np.abs(np.fft.rfft(x * bh(n))) ** 2
    f = np.fft.rfftfreq(n, 1 / SA.FS)
    sig = np.zeros_like(p, dtype=bool)
    for d in (0, -1, 1, -3, 3, -6, 6):
        f0 = 440 * 2 ** ((note - 69) / 12) * (1 + d * detune)
        for k in range(1, int(SA.FS / 2 / f0) + 1): sig |= np.abs(f - k * f0) < 4.5 * SA.FS / n
    al = ~sig & ~(f < 4.5 * SA.FS / n); lo = f < 8000
    return 10 * math.log10(p[al].sum() / p[sig].sum() + 1e-30), 10 * math.log10(p[al & lo].sum() / p[sig].sum() + 1e-30)


def renderer(img, man, nb=NB):
    """render(note, wave, shape) -> (the ring's left samples past the first 8 blocks as floats, the median instructions a block, the raw words):
    MIDI 1's own synth, one oscillator, the chain neutral, nb blocks on the emulated core 0 (vpre)"""
    PL.adopt(man["report"])
    sp = dsp_program(img)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)

    def render(note, wave_, pw, extra=None):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127), (V.NOTE, note)):
            blk[k_] = v_
        osb = [0] * 144; osb[2], osb[3] = wave_, pw
        for k_, v_ in (extra or {}).items(): osb[k_] = v_                  # (e.g. two oscillators: DFLAGS, NOTE2)
        out, ins, raw = [], [], []
        for b in range(nb):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0])],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            ins.append(int(ran.split('ins=')[1].split()[0]))
            blk, osb = res[('x', V.VB0)], list(res[('x', OSB)])
            raw += res[('y', RING)][0::2]
            out += [s24(v) / (1 << 23) for v in res[('y', RING)][0::2]]
        gc.collect()
        return np.array(out[N * 8:]), int(np.median(ins)), raw     # past the first blocks (the VCA's ramp); the median instructions a block
    return render


def main(img, man):
    r_ = renderer(img, man)
    render = lambda *a: r_(*a)[:2]

    rows = []
    for kind, wave_, pw in (("saw", 84, 0), ("pulse", 126, 50), ("supersaw", 84, 100)):
        for note in (72, 96):
            x, ins = render(note, wave_, pw)
            if kind == "supersaw":
                m = SA.wave_from("supersaw", *SA.phase(note, n=len(x)), "naive", note); f = asr_super
            else:
                m = SA.wave_from(kind, *SA.phase(note, n=len(x)), "naive", note); f = asr
            a_, b_ = f(x, note), f(m, note)
            print(f"{kind:8s} note {note}: the DSP {a_[0]:6.1f} | {a_[1]:6.1f} dB   the naive model {b_[0]:6.1f} | {b_[1]:6.1f} dB   {ins:6d} instructions a block (peak {np.abs(x).max():.3f})")
    x, ins = render(60, 0, 50)
    nz = asr(x, 60, harmonics=False)
    print(f"sine note 60: noise (no harmonics) {nz[0]:6.1f} dB below the fundamental, {ins} instructions a block (peak {np.abs(x).max():.3f})")

if __name__ == "__main__":
    main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text()))
