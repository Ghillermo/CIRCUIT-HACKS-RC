"""Circuit Tracks 4486 — SC37.2 = SC37.1 + packio.use_fix2() (SC37.1 on the device, 2026-10-10: swaps between packs deleted or mixed up samples):
reading an item of another pack switches the storage task's current pack, so the loaded pack is now named explicitly (from the packs view), the
storage task is put back on it after every swap, and B is written back if copying into it fails.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2 as B2  # noqa: E402  (configures everything as SC36.2)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_fix2()

NAME = "SC37.2"
extra = B2.extra


if __name__ == "__main__":
    b5 = B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
