"""Study (2026-10-26, the user: «Estudia cómo reducir el aliasing y el ruido»): the own synth's oscillator waves as the DSP computes them (vcf21_dsp:
the 24-bit phase u in -1..1, 2^24 a cycle, 48 kHz) and band-limited alternatives, measured with an FFT.

    python tools/study_alias.py

The metric: a Blackman-Harris window over 16384 samples; the signal = the bins around the harmonics below Nyquist; the aliasing = everything
else (but DC); ASR = aliasing / signal in dB, over the whole band and below 8 kHz (where it is heard most against the partials).  Methods:
  naive  the DSP's (saw = u, pulse = sign: +-0.5, triangle = 2|u| - 1, wavefold = the triangle x 7.9 folded, supersaw = 7 saws +-D, 3D, 6D)
  blep   2-sample polyBLEP at each step (saw: 1, pulse: 2) (cost ~12 instructions a step a sample)
  dpw    the differentiated parabola (saw: (u^2[n] - u^2[n-1]) / 4 dt; pulse = the difference of two) (~6 instructions a saw)
  os2    2x oversampling with a 31-tap half-band (the wave twice + ~16 macs)
Then (extra): the wavefold's largest drive by note under -40 dB, the sample mode's aliasing pitched up (linear / Hermite) and the filter's zipper
(the coefficient per 32-sample block).  tools/study_alias_dsp.py checks the model against the emulated DSP.
"""
from __future__ import annotations
import math
import numpy as np

FS, N = 48000, 16384
NOTES = (48, 60, 72, 84, 96, 108)


def inc_of(note):
    return int(round(440 * 2 ** ((note - 69) / 12) / FS * (1 << 24)))


def phase(note, n=N, os=1, start=0):
    inc = inc_of(note) / os
    k = np.arange(n * os, dtype=np.float64)
    ph = (start + k * inc) % (1 << 24)
    return np.where(ph >= 1 << 23, ph - (1 << 24), ph) / (1 << 23), inc / (1 << 24)


def polyblep(t, dt):
    y = np.zeros_like(t)
    m = t < dt; x = t[m] / dt; y[m] = x + x - x * x - 1
    m = t > 1 - dt; x = (t[m] - 1) / dt; y[m] = x * x + x + x + 1
    return y


def halfband(x):
    h = np.sinc(np.arange(-15, 16) / 2) * np.blackman(31) / 2
    return np.convolve(x, h, mode='same')[::2]


def fold(b):                                   # the DSP's fold of p: (1 - 2 |wrap(p - 0.5)|) / 2 on the -1..1 wrap
    p = (b - 0.5 + 1) % 2 - 1
    return (1 - 2 * np.abs(p)) / 2


def wave(kind, note, method, detune=0.0183):
    if method == "os2":
        u, dt = phase(note, os=2)
        return halfband(wave_from(kind, u, dt, "naive", note, os=2, detune=detune))
    u, dt = phase(note)
    return wave_from(kind, u, dt, method, note, detune=detune)


def wave_from(kind, u, dt, method, note, os=1, detune=0.0183):
    t = (u + 1) / 2
    if kind == "saw":
        if method == "naive": return u
        if method == "blep": return u - polyblep(t, dt)
        if method == "dpw":
            s = u * u; return np.diff(s, prepend=s[0]) / (4 * dt)
    if kind == "pulse":
        if method == "naive": return np.where(u >= 0, -0.5, 0.5)
        if method == "blep":
            sq = np.where(u >= 0, -0.5, 0.5)
            t2 = (t + 0.5) % 1
            return sq + 0.5 * polyblep(t, dt) - 0.5 * polyblep(t2, dt)
        if method == "dpw":
            u2 = (u + 1 + 1) % 2 - 1
            a_ = u * u; b_ = u2 * u2
            return (np.diff(a_, prepend=a_[0]) - np.diff(b_, prepend=b_[0])) / (4 * dt) / 4
    if kind == "tri":
        return 2 * np.abs(u) - 1
    if kind == "fold":
        return fold((2 * np.abs(u) - 1) * 7.9)
    if kind == "supersaw":
        out = np.zeros_like(u)
        for k, d in enumerate((0, -1, 1, -3, 3, -6, 6)):
            ratio = 1 + d * detune
            uk, dtk = phase(note, n=len(u) // os, os=os, start=(k * 2654435) % (1 << 24))
            uk = ((uk + 1) * ratio + 0.0) % 2 - 1 if False else None or uk
            inc = inc_of(note) * ratio / os
            ph = ((k * 2654435) + np.arange(len(u)) * inc) % (1 << 24)
            uk = np.where(ph >= 1 << 23, ph - (1 << 24), ph) / (1 << 23)
            dtk = inc / (1 << 24)
            out += wave_from("saw", uk, dtk, method, note) / 7
        return out
    raise ValueError(kind)


def asr(x, note):
    x = x[-N:] - np.mean(x[-N:])
    w = np.blackman(N) if False else (0.35875 - 0.48829 * np.cos(2 * np.pi * np.arange(N) / N) + 0.14128 * np.cos(4 * np.pi * np.arange(N) / N)
                                      - 0.01168 * np.cos(6 * np.pi * np.arange(N) / N))
    p = np.abs(np.fft.rfft(x * w)) ** 2
    f = np.fft.rfftfreq(N, 1 / FS)
    f0 = 440 * 2 ** ((note - 69) / 12)
    sig = np.zeros_like(p, dtype=bool)
    for k in range(1, int(FS / 2 / f0) + 1):
        sig |= np.abs(f - k * f0) < 4.5 * FS / N
    dc = f < 4.5 * FS / N
    al = ~sig & ~dc
    tot = 10 * math.log10(p[al].sum() / p[sig].sum() + 1e-30)
    lo = f < 8000
    low = 10 * math.log10(p[al & lo].sum() / p[sig].sum() + 1e-30)
    return tot, low


def asr_super(x, note, detune=0.0183):
    """the supersaw: the signal = the harmonics of each of the seven saws."""
    x = x[-N:] - np.mean(x[-N:])
    w = 0.35875 - 0.48829 * np.cos(2 * np.pi * np.arange(N) / N) + 0.14128 * np.cos(4 * np.pi * np.arange(N) / N) - 0.01168 * np.cos(6 * np.pi * np.arange(N) / N)
    p = np.abs(np.fft.rfft(x * w)) ** 2
    f = np.fft.rfftfreq(N, 1 / FS)
    sig = np.zeros_like(p, dtype=bool)
    for d in (0, -1, 1, -3, 3, -6, 6):
        f0 = 440 * 2 ** ((note - 69) / 12) * (1 + d * detune)
        for k in range(1, int(FS / 2 / f0) + 1):
            sig |= np.abs(f - k * f0) < 4.5 * FS / N
    al = ~sig & ~(f < 4.5 * FS / N)
    lo = f < 8000
    return 10 * math.log10(p[al].sum() / p[sig].sum() + 1e-30), 10 * math.log10(p[al & lo].sum() / p[sig].sum() + 1e-30)


def main():
    rows = []
    for kind, methods in (("saw", ("naive", "blep", "dpw", "os2")), ("pulse", ("naive", "blep", "dpw", "os2")), ("tri", ("naive", "os2")),
                          ("fold", ("naive", "os2")), ("supersaw", ("naive", "dpw", "blep"))):
        for m in methods:
            vals = []
            for nt in NOTES:
                x = wave(kind, nt, m)
                vals.append(asr_super(x, nt) if kind == "supersaw" else asr(x, nt))
            rows.append((kind, m, vals))
    print("ASR in dB (aliasing / signal; whole band | below 8 kHz) by note: " + "  ".join("%d" % n for n in NOTES))
    for kind, m, vals in rows:
        print(f"{kind:9s} {m:6s} " + "  ".join(f"{a:6.1f}|{b:6.1f}" for a, b in vals))
    extra()


def fold_limit(target=-40.0):
    """the wavefold: the largest drive (1 .. 7.9) a note takes with its aliasing below 8 kHz under target dB (a drive limit by pitch)."""
    out = []
    for nt in NOTES:
        u, dt = phase(nt)
        best = 1.0
        for g in np.linspace(1.0, 7.9, 70):
            if asr(fold((2 * np.abs(u) - 1) * g), nt)[1] < target: best = g
            else: break
        out.append(best)
    return out


def sample_mode(st, kind, f_src=130.81):
    """the sample mode: a full-band saw sample of C3 (harmonics to 20 kHz) played st semitones up, linear (the DSP's) or 4-point Hermite."""
    t = np.arange(8 * N + 64) / FS
    src = sum(np.sin(2 * np.pi * k * f_src * t) / k for k in range(1, int(20000 / f_src) + 1))
    src /= np.abs(src).max()
    pos = (np.arange(N) + 4) * 2 ** (st / 12)
    i = pos.astype(int); fr = pos - i
    if kind == "linear": return src[i] * (1 - fr) + src[i + 1] * fr
    xm1, x0, x1, x2 = src[i - 1], src[i], src[i + 1], src[i + 2]
    c1 = 0.5 * (x1 - xm1); c2 = xm1 - 2.5 * x0 + 2 * x1 - 0.5 * x2; c3 = 0.5 * (x2 - xm1) + 1.5 * (x0 - x1)
    return ((c3 * fr + c2) * fr + c1) * fr + x0


def zipper():
    """the filter: a Chamberlin SVF low-pass (as the engine's) on a naive saw at note 48, the cutoff swept 200 Hz -> 6 kHz in 50 ms; the coefficient
    held per 32-sample block (the DSP) against per sample: the difference against the signal, in dB."""
    x = wave_from("saw", *phase(48, n=2400), "naive", 48)
    env = lambda n: 200 * (30 ** min(1.0, n / (0.05 * FS)))
    def svf(per_block):
        low = band = 0.0; y = np.zeros_like(x)
        for n in range(len(x)):
            F = 2 * math.sin(math.pi * env((n // 32) * 32 if per_block else n) / FS)
            low += F * band; band += F * (x[n] - low - 0.7 * band); y[n] = low
        return y
    ya, yb = svf(True), svf(False)
    return 10 * math.log10(((ya - yb) ** 2).sum() / (yb ** 2).sum())


def extra():
    print("wavefold: the largest drive with the aliasing below 8 kHz under -40 dB: " + "  ".join(f"{n}: x{g:.1f}" for n, g in zip(NOTES, fold_limit())))
    note = 48
    for st in (7, 12, 24, 36):
        a_, b_ = asr(sample_mode(st, "linear"), note + st), asr(sample_mode(st, "hermite"), note + st)
        print(f"sample mode, a full-band C3 sample +{st:2d} semitones: linear {a_[0]:6.1f}|{a_[1]:6.1f}   Hermite {b_[0]:6.1f}|{b_[1]:6.1f}")
    print(f"filter sweep 200 Hz -> 6 kHz in 50 ms, the coefficient per block against per sample: {zipper():.1f} dB")


if __name__ == "__main__":
    main()
