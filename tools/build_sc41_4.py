"""Circuit Tracks 4486 - SC41.4 = SC41.3 + persist19.use_fselstock(): the drums' default filter is the stock tilt EQ (stored 0 <-> 4), so a new or untouched project sounds as on a stock Circuit (+ typeleds: its colours)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_3 as B  # noqa: E402
import linein3  # noqa: E402
import persist19  # noqa: E402
import typeleds  # noqa: E402
typeleds.use_fselstock()
persist19.use_fselstock()

NAME = "SC41.4"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
