"""Circuit Tracks 4486 - S485D (DIAGNOSTIC) = SC48.5 + tools/dspload.py (S484D's meters on SC48.5): Save = core 0's time margin (white = the
ring ran dry: the crackle), Duplicate = the own synth's peak; to check that vguard keeps Save out of white and how loud the relaxed level rule
(poly.use_v8) gets.  ARM only.  See firmware/s485d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_5 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "S485D"


def extra(img, report):
    import hole
    import dspload
    B.extra(img, report)
    hole.add(img, report, "dspload", dspload)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
