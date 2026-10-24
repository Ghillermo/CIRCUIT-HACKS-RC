"""Circuit Tracks 4486 - RC2.09S (files and marker R209S) = RC2.08S + a fix (persist19.use_startfix): Shift + K3's start point of the drums covers the
whole sample (it reached the end at a quarter of the knob and the rest left the hit silent)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r208s as B  # noqa: E402
import persist19  # noqa: E402
persist19.use_startfix()
import linein3  # noqa: E402

NAME = "R209S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
