"""Circuit Tracks 4486 - SC46.5 = SC46.4 + persist19.use_startfix() (the fix of RC2.09: Shift + K3's start point over the whole sample) +
drums2_dsp.use_lfoscan() (the drums' K7 to the left = a scan of the start point instead of the vibrato)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_4 as B  # noqa: E402
import persist19  # noqa: E402
import drums2_dsp  # noqa: E402
persist19.use_startfix()
drums2_dsp.use_lfoscan()
import linein3  # noqa: E402

NAME = "SC46.5"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
