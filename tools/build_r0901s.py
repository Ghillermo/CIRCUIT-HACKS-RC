"""Circuit Tracks 4486 - RC0.9.1S (files and marker R0901S) = RC0.9S + persist19.use_fselstock(): the drums' default filter is the stock tilt EQ (stored 0 <-> 4), so a new or untouched project sounds as on a stock Circuit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_9s as B  # noqa: E402
import linein3  # noqa: E402
import persist19  # noqa: E402
persist19.use_fselstock()

NAME = "R0901S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
