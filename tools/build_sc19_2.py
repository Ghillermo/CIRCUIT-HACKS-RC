"""Circuit Tracks 4486 — SC19.2 (EXPERIMENT) = SC19.1 + the deferred work of the saved settings waits after power-up.

SC19 / SC19.1 / SC20D froze at power-up on the hardware.  The only new work they do on their own at power-up is the deferred work of persist19.c_rs
(project settings -> RAM, Master FX and song pointer off, every drum parameter sent to the DSP as an absolute value).  SC19.2 staggers it so the
moment of a freeze tells what is guilty:
  * until 15 s after power-up: nothing (the three project hooks, the tick and the DSP code are the same as SC19.1);
  * 15 s (stage A): the settings -> RAM load, the validation and the Master FX / song pointer reset, with NO message to the DSP;
  * 30 s (stage B): the drum parameters are marked dirty and the tick sends them to the DSP (absolute mailbox values).
Everything else is SC19.1.  If it freezes at power-up again, the work is not the cause (DSP code, macro handlers, the new button / LED hooks).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.GUARD = True               # staged deferred work (must be set before persist19.install builds the code)
import build_sc19_1 as b191  # noqa: E402
import linein3  # noqa: E402

NAME = "SC19.2"
b182 = b191.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b191.extra)
