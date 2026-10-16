"""Circuit Tracks 4486 - SC41.6 = SC41.5 with pgmch.use_pf(): the patch flip of MIDI 1 / 2 stays on the MIDI track's channel (its internal injection is not sent again on the general PGM output channel; the user, 2026-10-15)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_5 as B  # noqa: E402
import linein3  # noqa: E402
import pgmch  # noqa: E402
pgmch.use_pf()

NAME = "SC41.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
