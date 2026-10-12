"""Circuit Tracks 4486 — SC17.6 = SC17.5 + the FX view's bottom row in the Master FX view, with assignable slots.

  * Master FX view: pads 25-32 (row 4) are the FX view's bottom row (stock "reverb and delay off" + the 7 SC14
    Gater / Auto-Filter pads), same behaviour, LEDs and latch (Shift + pad) as in the FX view.
  * Hold a top effect pad (1-6) and a bottom pad 26-32 at the same time: the bottom pad now runs that top effect
    (its mode and a copy of its 4 parameters).  Pressing it loads the copy into the effect and starts it.
    Not saved: power-up restores the SC14 effects.
  * FX view: the reset is now the Clear button (the stock Clear function still runs); button 1-16 / 17-32 steps the master
    filter resonance by 32 (0, 32, 64, 96, 127, then 0).
See build_sc17.slots_code.  Everything up to SC17.5 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17_5 as b5  # noqa: E402  (use_mixer14, use_full_leds, linein3.install, fxkeys)
import build_sc17 as s17  # noqa: E402
import fxkeys  # noqa: E402

NAME = "SC17.6"
s17.use_slots()
fxkeys.CLEAR_RESET = True            # FX view: Clear = reset, button 1-16 / 17-32 = master filter resonance + 32

if __name__ == "__main__":
    b5.linein3.main(NAME, b5.build, b5.s15, sys.argv[1:])
