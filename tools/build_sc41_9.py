"""Circuit Tracks 4486 - SC41.9 = SC41.8 + tools/arp.py: an arpeggiator on the note tracks (the user, 2026-10-15): Shift + pad 25 of Pattern Settings
turns it on for the pattern, Shift + pads 27-32 choose its order; chords of the sequence and notes held together on the pads play one note a step."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_8 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import arp  # noqa: E402

NAME = "SC41.9"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "arp", arp)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
