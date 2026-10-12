"""Circuit Tracks 4486 — SC18.1 = SC18 with the reworked drum knobs (tools/drums2_dsp.py) + Master FX pad 8 clears the song pointer.

  K1 envelope shape (attack <- -> decay), Shift + K1 envelope -> pitch;  K3 ring-mod frequency, Shift + K3 ring-mod amount;
  Shift + K7 filter mode (DJ, band-pass, notch, comb, stock tilt EQ);  K8 / Shift + K8 frequency / resonance (comb: feedback);
  K5 / Shift + K5 LFO amount / speed, K7 envelope -> filter, K4 / K6 left past 0 start point / bitcrush (as SC18).
  Drum Preset view in chromatic / scale mode: rows 1-2 dark.  Master FX pad 8 also switches the song pointer off.
  Master FX pad 7 = jump mode (hold, or Shift + pad 7 = sticky): touching a step pad jumps the playback there at the next step.
Everything up to SC18 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import drums18  # noqa: E402
drums18.V2 = True
import build_sc17 as s17  # noqa: E402
s17.CLEAR_SP = True
import build_sc18 as b18  # noqa: E402  (applies the SC17.8 options and installs the drum DSP code, now drums2_dsp)
s17.use_jump()
import linein3  # noqa: E402

NAME = "SC18.1"

if __name__ == "__main__":
    linein3.main(NAME, b18.b6.b5.build, b18.b6.b5.s15, sys.argv[1:], extra=b18.extra)
