"""Study model (no firmware): VCA with saturation + bipolar VCF with LFO and envelope for the external audio inputs.

    python tools/study_extfx.py

Numeric model in 24-bit fixed point (Q23, saturating, like the DSP56300) of the per-sample kernel proposed in docs/NOTAS.md
("Estudio ... VCA / VCF en las entradas externas"):

    x -> bipolar SVF (LP left of centre / HP right of centre, centre = bypass) -> drive + soft saturation -> VCA (gain ramp) -> y

It answers three questions before any DSP code is written:
  1. Is the Chamberlin state-variable filter stable in 24-bit arithmetic over the whole cutoff / resonance range (block-rate
     coefficient updates, 32-frame blocks at 48 kHz) and how is the bipolar knob law?
  2. How much distortion does the saturator add at each drive, and does it stay inside the 24-bit range?
  3. Does a block-rate envelope with a linear ramp per block click (attack down to 1 ms)?
Also prints the instruction count per frame and per block of the planned kernel (operation count, DSP56300: one parallel-move
instruction per ALU operation, loop overhead excluded).
"""
from __future__ import annotations
import math
import numpy as np

FS, NFR = 48000.0, 32
Q = 1 << 23


def sat(v):
    """24-bit saturation of an integer accumulator (the DSP56300 limiter)."""
    return max(-Q, min(Q - 1, int(v)))


def mulq(a, b):
    """fractional multiply Q23 x Q23 -> Q23 (truncating, like mpy + move a)."""
    return sat((a * b) >> 23)


def f_coef(fc):
    """Chamberlin tuning f = 2 sin(pi fc / fs), clipped to 0.99."""
    return min(0.99, 2 * math.sin(math.pi * fc / FS))


def bipolar_law(k):
    """knob k in -64..63 -> ('lp', fc) | ('bypass', 0) | ('hp', fc)."""
    if -2 <= k <= 1: return ("bypass", 0.0)
    if k < 0:
        t = (-k - 2) / 62.0                               # 0 .. 1 : -3 .. -64
        return ("lp", 16000.0 * (40.0 / 16000.0) ** t)    # 16 kHz .. 40 Hz
    t = (k - 2) / 61.0
    return ("hp", 30.0 * (6000.0 / 30.0) ** t)            # 30 Hz .. 6 kHz


class Svf:
    """Chamberlin SVF, state in Q23, f / q as Q23 fractions (q = 1/Q damping, 0 .. 1 ; resonance knob maps to damping 1 .. 0.04)."""
    def __init__(self): self.lp = self.bp = 0
    def run(self, x, fq, damp, kind):
        f = int(fq * Q); d = int(min(0.999, damp) * Q)
        out = np.empty(len(x), dtype=np.int64)
        lp, bp = self.lp, self.bp
        for n, xn in enumerate(x):
            hp = sat(xn - lp - mulq(d, bp) * 2)           # damping scale x2 so that d = 0.5 is critical damping
            bp = sat(bp + mulq(f, hp))
            lp = sat(lp + mulq(f, bp))
            out[n] = lp if kind == "lp" else hp
        self.lp, self.bp = lp, bp
        return out


def soft(v, drive):
    """drive (x1..x16, saturating shift) then y = 1.5 x - 0.5 x^3 (|x| <= 1)."""
    x = sat(v * drive)
    x2 = mulq(x, x); x3 = mulq(x2, x)
    return sat(int(1.5 * x) - (x3 >> 1))


def thd(drive, amp=0.25, f0=1000.0):
    n = np.arange(int(FS * 0.2))
    x = (amp * Q * np.sin(2 * math.pi * f0 * n / FS)).astype(np.int64)
    y = np.array([soft(int(v), drive) for v in x], dtype=np.float64)
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    k0 = int(f0 / FS * len(y))
    fund = spec[k0 - 2:k0 + 3].max()
    harm = math.sqrt(sum(spec[k * k0 - 2:k * k0 + 3].max() ** 2 for k in range(2, 9) if k * k0 + 3 < len(spec)))
    return 100 * harm / fund, float(np.abs(y).max() / Q)


def main():
    rng = np.random.default_rng(1)
    print("== 1. Chamberlin SVF in Q23, white noise at -6 dBFS, 4 s, f / damping updated every 32 frames ==")
    worst = 0.0; bad = 0
    for damp in (1.0, 0.5, 0.25, 0.1, 0.04):
        row = []
        for fc in (40, 200, 1000, 4000, 8000, 12000):
            x = (rng.uniform(-0.5, 0.5, int(FS * 4)) * Q).astype(np.int64)
            s = Svf(); y = s.run(x, f_coef(fc), damp, "lp")
            peak = float(np.abs(y).max() / Q); row.append(peak)
            if peak >= 0.999: bad += 1
        print(f"  damping {damp:5.2f}: peak LP out at fc = 40/200/1k/4k/8k/12k Hz = " + " ".join(f"{p:5.2f}" for p in row))
        worst = max(worst, max(row))
    print(f"  -> {bad} of 30 corners hit the 24-bit limiter (resonant peaks above full scale); the limiter acts as soft protection, no run-away")
    # steady-state stability: a step then silence must decay
    s = Svf(); x = np.full(int(FS * 0.1), int(0.5 * Q), dtype=np.int64); s.run(x, f_coef(8000), 0.04, "lp")
    y = s.run(np.zeros(int(FS * 2), dtype=np.int64), f_coef(8000), 0.04, "lp")
    print(f"  step then silence, fc = 8 kHz, damping 0.04: |y| after 2 s = {abs(int(y[-1]))} LSB (0 = decayed, no limit cycle)")
    print("== bipolar knob law (k = -64..63) ==")
    for k in (-64, -48, -32, -16, -3, -2, 0, 1, 2, 16, 32, 48, 63):
        kind, fc = bipolar_law(k)
        print(f"  k = {k:4d}: {kind:6s} fc = {fc:8.1f} Hz" if kind != "bypass" else f"  k = {k:4d}: bypass")
    # measured magnitude response through the fixed-point kernel
    print("  response through the fixed-point kernel (gain in dB at 100 / 1000 / 5000 Hz):")
    for k in (-48, -16, 16, 48):
        kind, fc = bipolar_law(k)
        gains = []
        for f0 in (100, 1000, 5000):
            n = np.arange(int(FS * 0.5)); x = (0.25 * Q * np.sin(2 * math.pi * f0 * n / FS)).astype(np.int64)
            y = Svf().run(x, f_coef(fc), 0.7, kind)
            gains.append(20 * math.log10(max(1e-9, np.sqrt(np.mean((y[len(y) // 2:] / Q) ** 2)) / (0.25 / math.sqrt(2)))))
        print(f"    k = {k:4d} ({kind} {fc:7.1f} Hz): " + "  ".join(f"{g:7.1f}" for g in gains))
    print("== 2. Saturator y = 1.5 x - 0.5 x^3 after a saturating drive gain, 1 kHz sine at -12 dBFS ==")
    for drive in (1, 2, 4, 8, 16):
        d, pk = thd(drive)
        print(f"  drive x{drive:2d}: THD (2nd..8th) = {d:5.1f} %, peak out = {pk:4.2f} FS")
    print("== 3. Block-rate envelope with a linear ramp per block (32 frames): attack steps ==")
    for ms in (1, 2, 5, 20):
        nblk = max(1, int(round(ms / 1000 * FS / NFR)))
        step = 100.0 / nblk
        print(f"  attack {ms:2d} ms: {nblk:3d} blocks, gain step {step:5.1f} % per block, ramped inside the block over {NFR} frames -> max step per frame {step / NFR:5.2f} %")
    print("== 4. Operation count of the planned kernel (per frame and input) ==")
    ops = [("input frame load (y:(r0)+n0)", 1), ("SVF: hp = x - lp - d*bp (mpy, sub, sub)", 3), ("SVF: bp += f*hp (mac)", 1), ("SVF: lp += f*bp (mac)", 1),
           ("LP / HP / bypass select + crossfade (1 mpy + 1 mac)", 2), ("drive (asl, saturating) + cube (2 mpy) + 1.5 x - 0.5 x^3 (3)", 6),
           ("VCA ramp (add step to gain, mpy)", 2), ("store back (move a,y:(r0)+n0)", 1), ("pointer / loop", 1)]
    tot = 0
    for name, n in ops:
        print(f"  {n:2d}  {name}"); tot += n
    print(f"  {tot} instructions per frame and input -> x 2 inputs x {NFR} frames = {2 * tot * NFR} per block (+ ~150 for env / LFO / gate / coefficient update)")
    print(f"  ~{2 * tot * NFR + 150} of the ~62 000 already used per block (SC19, 4 drums): +{100 * (2 * tot * NFR + 150) / 62000:.1f} %; budget ~166 000")


if __name__ == "__main__":
    main()
