"""Circuit Tracks 4486 — SC20D.1 (DIAGNOSTIC) = SC20D with the power-up freeze fixed (see build_sc19_3.py).

The capture meter of SC20D (modes 5 / 6 + bars of the delay and reverb captures in the source view); the deferred work of the saved settings no longer
takes the DSP service semaphore from inside the service tick.  Use with a test project.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import build_sc20d as b20  # noqa: E402  (applies the SC19 / SC19.1 / SC20D options)
import linein3  # noqa: E402
persist19.FIX_LOCK = True            # before persist19.install builds the code (main time)

NAME = "SC20D.1"
b182 = b20.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b20.extra)
