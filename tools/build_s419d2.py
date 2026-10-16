"""Circuit Tracks 4486 - S419D2 (diagnostic) = SC419D + stutdiag.use_culprit(): on each gap of the main loop (the user saw Duplicate yellow with the
stutter) Duplicate lights 1 s in the colour of what ran during it: white an SD access from the mod, blue one from the stock, peach the DSP service
itself, orange the LED task, red a knob event, green a pad event (each >= 5 ms), yellow none of them.  ("SC419D2" would be cut to "SC419D".)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc419d as B  # noqa: E402
import linein3  # noqa: E402
import stutdiag  # noqa: E402
stutdiag.use_culprit()

NAME = "S419D2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
