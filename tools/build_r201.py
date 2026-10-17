"""Circuit Tracks 4486 - RC2.01 (files and marker R201, the scheme of RC0.9.1 = R0901) = SC44.1 under the name of the release candidate
(the user, 2026-10-18: «release as rc2.01»): RC2 + the captured sample before the master filter."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_1 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "R201"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
