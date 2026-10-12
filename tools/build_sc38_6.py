"""Circuit Tracks 4486 — SC38.6 = SC38.5 with packio.use_ffgap() in place of use_initgap() (the user, 2026-10-11: «déjalos vacíos como hasta ahora»): a copy into
an empty patch slot past the end of its bank fills the slots between with 0xFF, as the stock's own patch save does (0x0802FBCC): they stay empty."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_5 as B  # noqa: E402  (configures everything as SC38.5)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.INITGAP = False
packio.use_ffgap()

NAME = "SC38.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
