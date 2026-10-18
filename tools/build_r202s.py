"""Circuit Tracks 4486 - RC2.02S (files and marker R202S) = RC2.02 + rodisk.use_allpacks(): the safer build (as RC2.01S): every write and delete the
mod starts is refused on every pack (the red Save LED), the stock's own saves pass."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rodisk  # noqa: E402
rodisk.use_allpacks()
import build_sc44_3 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R202S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
