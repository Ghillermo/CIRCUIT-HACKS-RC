"""Circuit Tracks 4486 - SC48.1 = SC48 + cueclk (the user, 2026-10-27: «Add metronome on Cue listen only (when metronome and Cue listen are
enabled)»): with the Mixer's cue mode on, the metronome's click (and the count-in's) sounds only on the right output, the cue.  DSP: the stock
click's loop with two pointers and a setup routine appended to core 0, which needs dsp56.use_shortmsb (the two-word `move #>$hh0000,D` of the
appended code in their one-word form: 18 words, the same operands).  See tools/cueclk.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48 as B  # noqa: E402
import build_sc16  # noqa: E402
import dsp56  # noqa: E402
import cueclk  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402
dsp56.use_shortmsb()
cueclk.install_dsp(build_sc16)

NAME = "SC48.1"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "cueclk", cueclk)
    cueclk.patch_dsp(img, report)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
