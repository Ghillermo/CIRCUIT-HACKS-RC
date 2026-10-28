"""Circuit Tracks 4486 - SC48.2 = SC48.1 + janko.use_v2() (a tester, brought by the user, 2026-10-28: the Jankó layout like the stock's chromatic
one, the row above a semitone lower; the user: «replace pad 8 with their implementation, and maybe add the old one … to pad 24. Root note is still
the stock scale's root (with a different color)», and a short Octave press = a semitone, a long one = an octave): Shift + pad 8 in the custom
scale's editor = the new layout, Shift + pad 24 = the old one; the root's pads in the root's colour with either; Octave held = an octave."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import janko  # noqa: E402
janko.use_v2()
import build_sc48_1 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC48.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
