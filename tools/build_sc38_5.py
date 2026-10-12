"""Circuit Tracks 4486 — SC38.5 = SC38.4 + build_sc17.use_latch7() (the user, 2026-10-11): Shift + pad 7 of Master FX (or Shift + a slot of the sample) is a
latched loop again, whatever the mode, until pad 7 / the slot is pressed again (SC34.1 had made it a held loop like the loop mode); packio.use_initgap():
a copy into an empty patch slot fills the empty slots before it with the stock's Initial Patch, not with copies."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_4 as B  # noqa: E402  (configures everything as SC38.4)
import build_sc17  # noqa: E402
import packio  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_latch7()
packio.use_initgap()

NAME = "SC38.5"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
