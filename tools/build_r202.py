"""Circuit Tracks 4486 - RC2.02 (files and marker R202, the scheme of RC2.01 = R201) = SC44.3 under the name of the release candidate
(the user, 2026-10-18: «Upload to RC2.xx and RC2.xxS»): RC2.01 + Beta 1.31 / 1.32 (the mod matrix, the split keyboard of any two note tracks,
the LFO's triangle by default and slewed sample & hold, the compacted ARM)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_3 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R202"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
