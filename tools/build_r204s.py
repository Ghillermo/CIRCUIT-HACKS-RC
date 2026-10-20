"""Circuit Tracks 4486 - RC2.04S (files and marker R204S) = RC2.04 + rodisk.use_allpacks(): the safer build (as RC2.03S)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r203s as B  # noqa: E402
import smhold  # noqa: E402
import recfix  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "R204S"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "smhold", smhold)
    hole.add(img, report, "recfix", recfix)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
