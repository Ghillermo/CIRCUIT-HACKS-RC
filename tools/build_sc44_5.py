"""Circuit Tracks 4486 - SC44.5 = SC44.4 + tools/mfbyp.py (the user, 2026-10-19: «add shift25 on FX view: master filter disable/enable»): in
the FX view, Shift + pad 25 switches the master filter off (its position kept, the filter at the centre) and on again; while off the filter knob's
LED is red; pad 25 yellow / red with Shift."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_4 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import mfbyp  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.5"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "mfbyp", mfbyp)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
