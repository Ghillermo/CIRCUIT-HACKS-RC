"""Circuit Tracks 4486 — SC22.1 = SC22 + an oscillator source for the VCF / VCA mode of the MIDI tracks.

Pad 27 of the Preset view of MIDI 1 / 2 (right of the mode pad) makes the audio input of the track an oscillator (sine / triangle / saw / pulse) at the pitch of the track's notes: the usual chain
(VCA with the envelope, FX, filter) follows.  Pad 28 switches the knobs to the oscillator page (K1 tune, Shift + K1 fine, K2 waveform, Shift + K2 pulse width, K3 vibrato depth).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc22 as b22  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.OSC = True
vcf21.use_osc()
vcf21.SIG_VAL = 0xAA                  # the values live at another stride now: the saved state of SC22 means other things

NAME = "SC22.1"

if __name__ == "__main__":
    linein3.main(NAME, b22.b182.b18.b6.b5.build, b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b22.b214.b213.extra)
