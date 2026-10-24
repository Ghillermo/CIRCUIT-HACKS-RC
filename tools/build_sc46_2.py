"""Circuit Tracks 4486 - SC46.2 = SC46.1 + gmdrum (the user, 2026-10-24: «New function on Beta for General MIDI with a toggle on setup memory/setup
view.  A user selected value per drum Channel (ranging 35 to 81) sets the target note»): the GM mode of the drums' MIDI out; in the Setup view K4 =
the mode, K5..K8 = the GM note of Drum 1..4 (it sounds, its number on the pads until Shift or leaving the Setup view confirms); saved with the unit's
settings."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_1 as B  # noqa: E402
import gmdrum  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC46.2"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "gmdrum", gmdrum)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
