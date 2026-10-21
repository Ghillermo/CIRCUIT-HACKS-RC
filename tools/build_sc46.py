"""Circuit Tracks 4486 - SC46 = SC45.9 + projsyn (the user, 2026-10-21: «each project should save its sound and bring it back when loaded (today it
is global)»): the own synth of MIDI 1 / 2 saved with the project (in bytes 8..39 of MIDI 1 / 2's patterns 0..4) and restored by its load.
(«SC45.10» would be cut to «SC45.1»: SC46.)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc45_9 as B  # noqa: E402
import projsyn  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC46"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "projsyn", projsyn)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
