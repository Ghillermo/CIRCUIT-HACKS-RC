"""Circuit Tracks 4486 - RC0.9S = RC0.8S under the next name: the safer build writes nothing of its own to any memory, so it needs no guard.  Same code as RC0.8S; marker "RC0.9S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_8s as B  # noqa: E402
import linein3  # noqa: E402

NAME = "RC0.9S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
