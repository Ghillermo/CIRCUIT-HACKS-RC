"""Circuit Tracks 4486 — RC0.4S = RC0.3S + the fixes of RC0.4 outside the SD card: build_sc17.use_armplay() / use_armplay2() (the armed capture from Play) and
use_latch7() (Shift + pad 7 = a latched loop).  The pack fixes (packio) stay out of the safer builds.  Marker "RC0.4S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_3s as B  # noqa: E402  (configures everything as RC0.3S)
import build_sc17  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_armplay(); build_sc17.use_armplay2(); build_sc17.use_latch7()

NAME = "RC0.4S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
