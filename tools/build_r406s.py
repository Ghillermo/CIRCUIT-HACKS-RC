"""Circuit Tracks 4486 - RC4.06S (marker "R406S") = RC4.05S + the fixes of SC50.4: arpmute, chords.use_shared, cibpm, rollers / drumarp use_bpm0."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chords  # noqa: E402
chords.use_shared()
import rollers  # noqa: E402
rollers.use_bpm0()
import drumarp  # noqa: E402
drumarp.use_bpm0()
import build_r405s as B  # noqa: E402
import build_sc41_5 as A  # noqa: E402
import arpmute  # noqa: E402
import cibpm  # noqa: E402
import linein3  # noqa: E402

NAME = "R406S"


def extra(img, report):
    B.extra(img, report)
    A.add(img, report, "arpmute", arpmute)
    A.add(img, report, "cibpm", cibpm)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
