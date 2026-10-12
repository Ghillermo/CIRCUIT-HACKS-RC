"""Circuit Tracks 4486 — SC38.2 = SC38.1 + build_sc17.use_armplay() (the user, 2026-10-11): a capture armed with Shift + pad 32 while stopped starts at Play and
ends at the end of that bar (it began a bar late: the stock plays the downbeat of a start outside the tick function)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_1 as B  # noqa: E402  (configures everything as SC38.1)
import build_sc17  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_armplay()

NAME = "SC38.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
