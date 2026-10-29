"""Circuit Tracks 4486 - SC49.2 = SC49.1 + tools/lanex.py (the user, 2026-10-28 / 29): one more automation lane per drum, in the spare bits of
each step (probability bits 3-7 + micro step bits 6-7: 7 bits); per drum it carries the chromatic pitch (default) or one of the drum knobs
without a stock lane (Record held + that knob; Record held + a chromatic pad = the chromatic pitch); recorded live, written by Record held +
step, erased by Clear + its knob to the left, the assigned knob white while Record is held (the chromatic pitch: Preset blinking).  lanex's helpers in
the hole, its knob / LED / snapshot heads at the image's end."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_1 as B  # noqa: E402
import drumarp  # noqa: E402
import quant  # noqa: E402
drumarp.use_keepbits()                               # a recorded hit on an empty step keeps the lane's bits
quant.use_keepbits()                                 # Shift + Play moves the hits alone
import lanex  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC49.2"


def extra(img, report):
    B.extra(img, report)
    import build_sc41_5
    hole.add(img, report, "lanex", lanex)                       # part a: the helpers, the stock's setters, dpitch's spots
    build_sc41_5.add(img, report, "lanexb", lanex.PartB)       # part b at the image's end: the knobs, the LEDs, the snapshot
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
