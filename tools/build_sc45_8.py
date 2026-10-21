"""Circuit Tracks 4486 - SC45.8 = SC45.7 + RC2.06's fix (dupnote: two pads of the same note held together no longer leave it sounding) + splitknob
(the user, 2026-10-21: «Durante el modo split, aguantar un pad de track abre sus controles en la capa de potes»: with the split keyboard on, a track
button held = the knobs are that track's; a tap ends the split as before)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc45_7 as B  # noqa: E402
import dupnote  # noqa: E402
import splitknob  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC45.8"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "dupnote", dupnote)
    hole.add(img, report, "splitknob", splitknob)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
