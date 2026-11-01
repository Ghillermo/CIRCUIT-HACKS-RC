"""Circuit Tracks 4486 - RC4.03 (marker "R403") = RC4.02 + savedefer.use_toggle (the user, 2026-10-30: «Make the delayed save a toggle in advanced setup (stock save
by default)»: the project save is the stock's unless Advanced Setup's pad 22 is on)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import savedefer  # noqa: E402
savedefer.use_toggle()
import build_r402 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R403"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
