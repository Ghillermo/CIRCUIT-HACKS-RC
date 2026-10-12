"""Circuit Tracks 4486 — SC19.3 = SC19.1 with the power-up freeze fixed.

SC19 / SC19.1 / SC20D froze at power-up and SC19.2 (the experiment that staggered the work) froze exactly when its stage A ran.  Cause:
persist19.c_xm_load runs in the DSP service tick and marked the Audio In group dirty with the stock MARK_DIRTY (0x0803BDCC), whose first step is to take
the service semaphore (0x08021064: waits while the count at [ptr + 0xC] is 0).  The main loop takes that same semaphore around the whole service
(0x0801D5D4 .. 0x0801D5DC), so the tick waited for itself for ever.  SC19.3 calls the dirty-bit setter 0x08021FDC directly (what MARK_DIRTY does between
taking and giving the semaphore) from the tick.  Everything else is SC19.1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True            # must be set before persist19.install builds the code
import build_sc19_1 as b191  # noqa: E402
import linein3  # noqa: E402

NAME = "SC19.3"
b182 = b191.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b191.extra)
