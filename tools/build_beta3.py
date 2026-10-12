"""Circuit Tracks 4486 — BETA3 = SC39.2 under the name of the fourth beta: BETA2 + the fix of RC0.5 (the captured sample before the Master FX effects).
Same code as SC39.2, marker "BETA3"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_2 as B  # noqa: E402  (configures everything as SC39.2)
import linein3  # noqa: E402

NAME = "BETA3"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
