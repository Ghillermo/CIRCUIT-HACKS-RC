"""Circuit Tracks 4486 — SC38.4 = SC38.3 + fixes after SC37.4-SC38.2 on the device (the user, 2026-10-11): build_sc17.use_armplay2() (the armed capture starts
on the transport's start, SET_TICKS from 0x0802BD3C: SC38.2 still began a bar late), packio.use_pkled3() (Clear steady white in the packs view from the
start) and packio.use_empty() (Duplicate between packs copies into an empty sample / patch slot too)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_3 as B  # noqa: E402  (configures everything as SC38.3)
import build_sc17  # noqa: E402
import packio  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_armplay2()
packio.use_pkled3()
packio.use_empty()

NAME = "SC38.4"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
