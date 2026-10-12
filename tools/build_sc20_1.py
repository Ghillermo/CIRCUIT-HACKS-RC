"""Circuit Tracks 4486 — SC20.1 = SC20 + scale keyboard on three rows, Pitch knob as a note bias in the chromatic view, Clear on the drum knobs of ours.

* Drum Preset view, scale mode: only the three bottom rows play / light (build_sc08.ROWS3); the top row was always the same maximum pitch.  The chromatic piano keeps its two strips (four rows).
* Chromatic view: the plain Pitch knob (K1) adds a semitone bias to every pad (SC11: Pitch + bias, the sum is clamped to 0..127 by the pad handler); Shift + K1 is the fine tune in cents
  (build_sc12.SWAP; before it was the other way round).
* Clear + a drum knob of ours: right = back to the default value (blue LED), left = red LED (they have no recorded automation to delete); the stock-routed knobs (pitch, decay, distortion, EQ)
  keep the stock Clear and now show its red / blue LED at the right knob (persist19.CLEAR).
* Master FX pad 7 (step jump) in yellow (0x2D bright, 0x2E dim) instead of white.
* The VCF state in the settings tail has a signature (vcf20.SIGNED): a tail without it (garbage, 0xFF) is re-initialised instead of read as "modes on".
Everything else is SC20.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import build_sc08  # noqa: E402
import build_sc12  # noqa: E402
persist19.CLEAR = True
build_sc08.ROWS3 = True
build_sc12.SWAP = True
import vcf20  # noqa: E402
import build_sc17  # noqa: E402
vcf20.SIGNED = True                                   # the VCF state in the settings tail is validated (signature)
import build_sc20 as b20  # noqa: E402
import linein3  # noqa: E402
build_sc17.SP_PLAY = True                              # the song pointer playhead only while the transport runs
build_sc17.JMP_ON, build_sc17.JMP_OFF = 0x2D, 0x2E    # Master FX pad 7 (step jump) in yellow: bright / dim (RGB table of 0x0803423C: 0x2D = 255, 255, 25, 0x2E = 41, 41, 4)

NAME = "SC20.1"
b182 = b20.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b20.extra)
