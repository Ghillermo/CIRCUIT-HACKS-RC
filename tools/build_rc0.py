"""Circuit Tracks 4486 — RC0 = SC36.2 under the name of the first release candidate (the user, 2026-10-09): same code, marker "RC0"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2 as B  # noqa: E402  (configures everything as SC36.2)
import linein3  # noqa: E402

NAME = "RC0"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
