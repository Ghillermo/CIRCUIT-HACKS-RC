"""Circuit Tracks 4486 — SC37.6 = SC37.5 + packio.use_srcguard() (a review, 2026-10-10): with Duplicate held before SC19.1's source view of the synth
opens, the pads of that view no longer copy / swap synth patches (SC37.4 / SC37.5 did); packio.use_impguard(): when the free memory for imported
samples is full, a copy never goes back over a sample the table still plays (nothing changes instead); drumrep.use_clearrep(): the drum replaced by
the capture with Clear + pad (twice) instead of Shift + pad (the user, 2026-10-10: Shift + pad is the stock's silent selection)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_5 as B5  # noqa: E402  (configures everything as SC37.5)
import packio  # noqa: E402
import drumrep  # noqa: E402
import linein3  # noqa: E402
packio.use_srcguard()
packio.use_impguard()
drumrep.use_clearrep()

NAME = "SC37.6"
extra = B5.extra


if __name__ == "__main__":
    b5 = B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
