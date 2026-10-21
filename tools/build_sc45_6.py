"""Circuit Tracks 4486 - SC45.6 = SC45.5 + vcf21_dsp.use_fm() + tools/fmeng.py in the hole (the user, 2026-10-21: «can we have FM as another
variant for osc?», «4op, A/R with fixed sustain. Release could be velocity-dependant», «include some kick/noise percussive algos, some bell and
some strings along with the typical algorithms»): a 4-operator FM variant of the own engine's oscillator (MIDI 1 / 2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc45_5 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_fm()
import psave  # noqa: E402
import xpatch  # noqa: E402
psave.XLEN = xpatch.XLEN = 124                       # the exchange / the copy between packs carry FM (padding + 100..120)
import fmeng  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC45.6"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "fmeng", fmeng)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
