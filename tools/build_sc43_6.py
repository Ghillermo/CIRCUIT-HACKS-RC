"""Circuit Tracks 4486 - SC43.6 = SC43.5 + dpitch.use_rec() (the chromatic view's steps recorded again: lane 7 of the drum pattern, the stock's
drum pan automation, unused) + tools/cue.py (the Mixer's cue mode: the main mix mono on the left, a cue send per track on the right) +
vcf21.use_lastnote() / use_n2first() / use_osc2pg() (one oscillator: last-note priority; code 14 before the gate: the granular's first grain at
the right pitch; the OSC 2 page on the eight plain knobs).

SC43.5 = SC43.4 + tools/dpitch.py + clrtrk.use_synth()."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_5 as B  # noqa: E402
import dpitch  # noqa: E402
dpitch.use_rec()
import vcf21  # noqa: E402
vcf21.use_lastnote(); vcf21.use_n2first(); vcf21.use_osc2pg()
import cue  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402

NAME = "SC43.6"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "cue", cue)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
