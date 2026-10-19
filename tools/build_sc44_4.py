"""Circuit Tracks 4486 - SC44.4 = SC44.3 + tools/fxres.py (the user, 2026-10-19: «cambia master reso a shift+octave up/down, saltos de 16 en 16»,
«sin ciclar en max/min»): in the FX view, Shift + Octave UP / DOWN = the master filter resonance +16 / -16, stopping at 127 / 0 (Octave yellow
with Shift); the "1-16 / 17-32" button is stock again."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_3 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import fxres  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.4"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "fxres", fxres)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
