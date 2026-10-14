"""Circuit Tracks 4486 — SC39.7 = SC39.6 + build_sc17.use_mech() (the user, 2026-10-12): the Vinyl effect is gone; its pad is a "mechanical" gesture
on the Glitch engine (tape stop, baby / tear scratch, back spin, rattle, mixed continuously): pressed = the stop, let go = the start."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_6 as B  # noqa: E402  (configures everything as SC39.6)
import build_sc17 as S17  # noqa: E402
import linein3  # noqa: E402

NAME = "SC39.7"
S17.use_mech()
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
