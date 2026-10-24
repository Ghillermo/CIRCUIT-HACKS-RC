"""Circuit Tracks 4486 - SC46.4 = SC46.3 + usbmerge (issue #10 of the public repository: the DIN In merged into the USB MIDI out; Advanced Setup,
pad 23) + gmdrum.use_v3() (K4 keeps the other bits of the flags byte)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gmdrum  # noqa: E402
gmdrum.use_v3()
import build_sc46_3 as B  # noqa: E402
import usbmerge  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC46.4"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "usbmerge", usbmerge)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
