"""Circuit Tracks 4486 — SC37.1 = SC37 + packio.use_cross2() (the user, 2026-10-10): synth patches swapped between packs the same way (synth Preset view:
Duplicate + pad A copies the patch, Duplicate + pad B in another pack swaps them; B is chosen again so the new patch sounds), and a sample or patch
copied in another pack blinks yellow (Synth 1 is magenta).  sampler_dsp.CLIP2: the DSP clears the patch clip word at power-up.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2 as B2  # noqa: E402  (configures everything as SC36.2)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_cross2()

NAME = "SC37.1"
extra = B2.extra


if __name__ == "__main__":
    b5 = B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
