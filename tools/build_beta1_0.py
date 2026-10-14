"""Circuit Tracks 4486 - Beta 1.0 = SC40.9 under the name of the beta the user asked to publish (2026-10-14: «Sube como beta 1.0»).  Same code as SC40.9;
marker "B1.0" (the marker keeps 6 characters: "BETA1.0" would be cut to "BETA1." and a later "BETA1.1" could not be installed over it)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc40_9 as B  # noqa: E402  (configures everything as SC40.9)
import linein3  # noqa: E402

NAME = "B1.0"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
