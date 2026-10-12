"""Circuit Tracks 4486 — SC37.9 = SC37.8 + (SC37.8 on the device, 2026-10-11) persist19.use_blue7(): the blue of Clear + knob on the drums is the stock's 0x07
(0x46 showed a dim red-orange) + build_sc17.use_gclear(): Clear + knob in Master FX (right = the default of the selected effect's knob; while Clear is held its
knob LEDs are blue at the default, red elsewhere)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_8 as B8  # noqa: E402  (configures everything as SC37.8)
import persist19  # noqa: E402
import build_sc17  # noqa: E402
import linein3  # noqa: E402
persist19.use_blue7()
build_sc17.use_gclear()

NAME = "SC37.9"
extra = B8.extra


if __name__ == "__main__":
    b5 = B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
