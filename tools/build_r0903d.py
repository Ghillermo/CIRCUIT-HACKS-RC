"""Circuit Tracks 4486 - R0903D (diagnostic) = RC0.9.3 + the bench of S419D2 (tools/stutdiag.py with use_culprit(), granular_dsp.use_diagcnt()): the
RC does not stutter (the user, 2026-10-16); if it also shows Duplicate yellow while playing, those gaps are the stock's and harmless."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r0903 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import granular_dsp  # noqa: E402
import stutdiag  # noqa: E402
granular_dsp.use_diagcnt()
stutdiag.use_culprit()

NAME = "R0903D"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "stutdiag", stutdiag)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
