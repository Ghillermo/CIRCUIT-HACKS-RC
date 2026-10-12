"""Circuit Tracks 4486 — SC32 = SC31 + the Master FX song pointer reworked (build_sc17.use_sp2), first step of the captured sample:
  * pad 7 (jump mode) removed: dark, does nothing (it will be the capture pad);
  * one step held = retrigger (the step plays at the next step and repeats while held); two steps held = a phrase loop between them;
  * Shift + a step = the start of a latched phrase, Shift + a second step = its end; a latched phrase lights pad 9 white, touching pad 9 removes it.
Pad 6 is still Vinyl until the sample player replaces it.  Everything up to SC31 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc31 as b31  # noqa: E402
import build_sc17  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_sp2()

NAME = "SC32"
extra = b31.extra

if __name__ == "__main__":
    b5 = b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
