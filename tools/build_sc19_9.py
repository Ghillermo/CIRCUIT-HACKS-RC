"""Circuit Tracks 4486 — SC19.9 = SC19.8 + a distortion type (Shift + FX) per drum, Master FX knob LEDs with the value as brightness, and the step jump that repeats while its pad is held.

Distortion type (0 stock, 1 soft, 2 hard, 3 fold): a second shaper after the stock distortion, driven by the same knob (drive = 1 + 8 x the stock distortion value).
The filter slope (12 / 24 dB, Shift + Resonance) was built and then discarded by the user (persist19.EXTRAS_SLOPE / drums2_dsp.SLOPE_PASS stay as off options).  The type is saved
with the project (bits of the byte 8 of the drums, see persist19.XT_BITS) and travels to the DSP in the bits 8-9 of the extended-values word; an old project reads 0 = the behaviour before.
Step jump (Master FX pad 7, held or sticky, then a step pad 1-16): the step plays at the next step and is repeated at every step while that step pad stays pressed; released = it stops.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import drums2_dsp  # noqa: E402
persist19.EXTRAS = True              # the distortion type (the filter slope stays off: persist19.EXTRAS_SLOPE / drums2_dsp.SLOPE_PASS)
drums2_dsp.XTRA = True
import build_sc19_8 as b198  # noqa: E402
import build_sc17  # noqa: E402
import linein3  # noqa: E402
build_sc17.KNOB_BRIGHT = True        # the Master FX knob LEDs show their value as brightness (needs the converter hook of persist19.KNOB_LEVELS, on since SC19.6)
build_sc17.use_jump(white=True, hold=True)   # after the chain (it needs use_songptr / use_slots); SC19.7 / SC19.8 keep the repeat-while-pad-7 variant

NAME = "SC19.9"
b182 = b198.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b198.b197.b196.b195.b191.extra)
