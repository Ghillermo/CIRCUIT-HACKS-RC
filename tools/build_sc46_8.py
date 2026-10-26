"""Circuit Tracks 4486 - SC46.8 = SC46.7 + vcf21_dsp.use_smstereo2() + tools/smst.py (the user, 2026-10-25): the stereo sample mode lasts as long as the
longer sample (the shorter one silent after its end); the second sample chosen in the picker (Shift + the chosen sample = choose the second, Shift + a
sample = silent), at a distance kept when the first changes, saved with the patch / the project."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_7 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_smstereo2()
import smst  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC46.8"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "smst", smst)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
