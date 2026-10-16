"""Circuit Tracks 4486 - SC41.8 = SC41.7 + tools/countin.py: Shift + Clear walks four metronome states (none, metronome, count-in only, count-in and
metronome); with the count-in, Play from stopped with Record armed clicks one bar at the project's tempo and then starts (the user, 2026-10-15, issue #2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_7 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import countin  # noqa: E402

NAME = "SC41.8"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "countin", countin)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
