"""Circuit Tracks 4486 - SC47.7 = SC47.6 with the voice modes in the user's order and meaning (2026-10-26: «modes and order: retrigger (gate signal
resets whith each new note) legato (no gate reset, change to new pitch when two keys are held) glide: same as legato, but notes glide continuosuly
into the next (optional param: amount) uni retrig/legato/glide: same behavior with unison. Poly: plyphony»): poly.use_v6() (glide = a legato
glide: a detached note jumps), vmode.use_v3() (pads 17-23 in that order; the coefficient in glide / uni glide only; uni legato does not slide)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_6 as B  # noqa: E402
import poly  # noqa: E402
poly.use_v6()
import vmode  # noqa: E402
vmode.use_v3()
import linein3  # noqa: E402

NAME = "SC47.7"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
