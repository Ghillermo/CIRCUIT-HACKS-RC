"""Circuit Tracks 4486 - S421D (diagnostic) = SC42.1 + the bench of SC419D / S419D2 (tools/stutdiag.py with use_culprit(), granular_dsp.use_diagcnt()):
the same indicators on the build that should not stutter any more (Save red = DSP blocks late, Duplicate = a main-loop gap in the culprit's colour,
Play orange = the sequencer's tick late)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42_1 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import granular_dsp  # noqa: E402
import stutdiag  # noqa: E402
granular_dsp.use_diagcnt()
stutdiag.use_culprit()

NAME = "S421D"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "stutdiag", stutdiag)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
