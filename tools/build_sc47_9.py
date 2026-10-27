"""Circuit Tracks 4486 - SC47.9 = SC47.8 + stpair (the user, 2026-10-24 / 2026-10-27: «modo sample stereo … implement stereo pair as planned»):
stereo drum pairs.  Drum 1 held + Drum 2 (or Drum 3 + Drum 4): Drum 1 / 3 plays its sample on the left and Drum 2 / 4 the next one on the right,
both driven by Drum 1 / 3's controls and pattern; Drum 2 / 4's knobs = the pan spread (K2), the detune in cents (K1) and deviations; saved with the
project; the same gesture = two drums again.  See tools/stpair.py.
+ smnote (the user, 2026-10-27: «on own's sampler, adding a flip step automatically adds a note step containing the last pressed note …»): in the
own engine's sample picker a flip on a step with no note adds the last pressed note there; the step pads show note / flip / both.  See tools/smnote.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_8 as B  # noqa: E402
import stpair  # noqa: E402
import smnote  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC47.9"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "stpair", stpair)
    hole.add(img, report, "smnote", smnote)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
