"""Circuit Tracks 4486 — RC0.4 = RC0.3 (SC38) + the fixes found on the device (2026-10-11), no new features: build_sc17.use_armplay() / use_armplay2() (an armed
capture from a stop starts on the first beat of Play: SC38.4), use_latch7() (Shift + pad 7 = a latched loop again: SC38.5), packio.use_empty() /
use_ffgap() (Duplicate between packs into an empty sample / patch slot; the patch slots between stay empty, as the stock: SC38.4 / SC38.6) and
use_pkled3() (Clear steady white in the packs view: SC38.4).  Marker "RC0.4"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_3 as B  # noqa: E402  (configures everything as RC0.3 = SC38)
import build_sc17  # noqa: E402
import packio  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_armplay(); build_sc17.use_armplay2(); build_sc17.use_latch7()
packio.use_empty(); packio.use_ffgap(); packio.use_pkled3()

NAME = "RC0.4"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
