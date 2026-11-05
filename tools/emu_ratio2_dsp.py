"""SC52.2 / Beta 5.25 DSP test (vcf21_dsp.use_ratio2): OSC 2's TUNE word in 1/256 semitone = a ratio of its note (the ARM sends
round(12 log2 r x 256), vcf21.use_ratio2), FINE = the detune (1/128 semitone).  On core 0 (emu_wt_dsp's renderer, MIDI 1, two oscillators, OSC 2
alone in the mix (MIX 127), a sine, its note = OSC 1's note 60):
  * TUNE 0 = PREV (Beta 5.24) bit for bit;
  * each ratio r (0.25, 0.5 on note 84; 1, 2, 3, 5, 7, 11, 31 on 60): the strongest frequency = f(60) x r (within 2 cents of the DFT's grid);
  * FINE 32 = +25 cents.

    python tools/emu_ratio2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_wt_dsp as W  # noqa: E402
import vcf21_dsp as VD  # noqa: E402

O2 = W.O2


def peak(x, lo, hi):
    """the frequency (Hz) of the strongest component between lo and hi (a fine DFT scan)"""
    n = np.arange(len(x)); w = np.hanning(len(x))
    fs = np.linspace(lo, hi, 2001)
    a = [abs(np.sum(x * w * np.exp(-2j * np.pi * f / 48000 * n))) for f in fs]
    return fs[int(np.argmax(a))]


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    base = {VD.DFLAGS_OFF: 2, VD.NOTE2_OFF: 60, O2 + 2: 0, O2 + 3: 50, O2 + 4: 127}
    new, old = W.renderer(img, man, nb=24), W.renderer(prev, pman, nb=24)
    _, _, ra = new(60, 0, 50, base); _, _, rb = old(60, 0, 50, base)
    check(ra == rb, "TUNE 0: Beta 5.24 bit for bit")
    f60 = 440 * 2 ** (-9 / 12)
    for r in (0.25, 0.5, 1, 2, 3, 5, 7, 11, 31):
        nt = 84 if r < 1 else 60                                                    # (the low ratios a note higher: enough cycles in the window)
        ex = dict(base); ex[O2 + 0] = round(12 * math.log2(r) * 256); ex[VD.NOTE2_OFF] = nt
        x, _, _ = new(nt, 0, 50, ex)
        want = f60 * 2 ** ((nt - 60) / 12) * r
        got = peak(x, want * 0.97, want * 1.03)
        cents = 1200 * math.log2(got / want)
        check(abs(cents) < 3, f"ratio {r}: {got:.2f} Hz (want {want:.2f}, {cents:+.2f} cents)")
    ex = dict(base); ex[O2 + 1] = 32
    x, _, _ = new(60, 0, 50, ex)
    got = peak(x, f60 * 0.97, f60 * 1.05); cents = 1200 * math.log2(got / f60)
    check(abs(cents - 25) < 3, f"FINE 32: {cents:+.2f} cents (want +25)")
    print(f"{man.get('marker', '?')} RATIO2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    import gentab
    gentab.use_xtab()
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
