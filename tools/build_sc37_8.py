"""Circuit Tracks 4486 — SC37.8 = SC37.7 + packio.use_pkled2() (SC37.7 on the device, 2026-10-11): in the packs view the delete question is drawn on each
LED frame (the packs blink and come back; before, a dark blink phase was written into the view's own buffer and the packs stayed dark), and Clear is steady
white while the question is open (dim white otherwise)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_7 as B7  # noqa: E402  (configures everything as SC37.7)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_pkled2()

NAME = "SC37.8"
extra = B7.extra


if __name__ == "__main__":
    b5 = B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
