"""Circuit Tracks 4486 - SC41.2 = SC41.1 + patchain.use_rulecheck(): the rule of a track / pattern outside 0..7 is «none» instead of an address past
the end of the RAM (found reviewing SC41.1 in emulation)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_1 as B  # noqa: E402
import linein3  # noqa: E402
import patchain  # noqa: E402
patchain.use_rulecheck()

NAME = "SC41.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
