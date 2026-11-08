"""Circuit Tracks 4486 - SC55.5 = SC55.4 + packio.use_bassblue (the user, 2026-11-08: «a different color for bass» → «steel blue»: Bass = 0x12)
+ packio.use_palfix (fix: the category palette written on every call; after an install the previous build's stayed in RAM)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_4 as S  # noqa: E402
import linein3  # noqa: E402
import packio  # noqa: E402

packio.use_bassblue()
packio.use_palfix()
NAME = "SC55.5"
B = S.B
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
