"""Circuit Tracks 4486 — SC17.8 = SC17.7 with the synth source modes back in Shift + Preset, + a clear pad in the Master FX view.

  * The modes of the synth source (noise / inputs / inverted inputs / delay / reverb returns) are again selected with Shift + the
    pads 25-31 of the synth Preset view (SC15's view, as in SC17.5 / SC17.6).  The Shift + Scales view of SC17.7 is not used (it did not show).
  * Master FX view, pad 8 (top row, last pad): switches off every effect that is latched (Shift + pad): the top row, the assigned
    slots and the SC14 effects of the bottom row.
  * Master FX view and FX view, any latched effect pad: a tap without Shift switches that effect off.
  * Song pointer, delay / reverb capture gain: as SC17.7.
See build_sc17.use_clearpad.  Everything up to SC17.7 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17_6 as b6  # noqa: E402  (use_slots, fxkeys.CLEAR_RESET; imports build_sc17_5: use_mixer14, use_full_leds, linein3.install)
import build_sc17 as s17  # noqa: E402
import linein3  # noqa: E402

NAME = "SC17.8"
s17.use_songptr()
s17.use_clearpad()
linein3.FX_GAIN_SHIFT = 3

if __name__ == "__main__":
    linein3.main(NAME, b6.b5.build, b6.b5.s15, sys.argv[1:])
