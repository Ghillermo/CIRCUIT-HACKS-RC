"""Circuit Tracks 4486 — SC22.3 = SC22.2 + oscillator v3: the waveform is a continuous morph over sine - triangle - saw - square that the envelope and the LFO move, the shape (PW 0..100) acts on every wave.

Pad 27 of the Preset view of MIDI 1 / 2 opens the oscillator page of the knobs, pad 28 switches the source (line in <-> oscillator).  Page B: K1 tune / fine, K2 waveform / shape, K3 envelope -> pitch / LFO -> pitch
(semitones: +-24 / +-6), K4 envelope -> shape / LFO -> shape.  Mathematical oscillators; the shape is, per waveform: sine and triangle = wavefold, saw = the slope of the ramp (logarithmic / straight / parabolic), pulse = the pulse width.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc22 as b22  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.use_osc3()
vcf21.use_osc3()
vcf21.SIG_VAL = 0xAC                  # the oscillator page has 10 values now

NAME = "SC22.3"

if __name__ == "__main__":
    linein3.main(NAME, b22.b182.b18.b6.b5.build, b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b22.b214.b213.extra)
