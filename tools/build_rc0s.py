"""Circuit Tracks 4486 — RC0S = SC362S (the safer build: nothing of ours writes the SD card) under the name of the first release candidate: same code, marker "RC0S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc362s as B  # noqa: E402  (configures everything as SC362S)
import linein3  # noqa: E402

NAME = "RC0S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
