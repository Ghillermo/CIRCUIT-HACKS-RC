"""Circuit Tracks 4486 - RC2.08 (files and marker R208) = RC2.07 + a fix (kbin): an external keyboard plays the own synth of MIDI 1 / 2 (its notes
went only to the recorder: the engine takes its notes at the transmitter, which the stock never calls for a note coming in)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r207 as B  # noqa: E402
import kbin  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "R208"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "kbin", kbin)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
