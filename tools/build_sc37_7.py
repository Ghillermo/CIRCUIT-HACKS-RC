"""Circuit Tracks 4486 — SC37.7 = SC37.6 + packio.use_inplace() (the user, 2026-10-10): a sample copied from another pack goes into the replaced
sample's own place in the pack's sample memory when it fits (the free memory only as a temporary), and the free memory for imports starts again once no
sample of the table lies in it (after the pack is loaded again)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_6 as B6  # noqa: E402  (configures everything as SC37.6)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_inplace()

NAME = "SC37.7"
extra = B6.extra


if __name__ == "__main__":
    b5 = B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
