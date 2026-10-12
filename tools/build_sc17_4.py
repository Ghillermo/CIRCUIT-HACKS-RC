"""Circuit Tracks 4486 — SC17.4 = SC17.3 + full LED buffer in Master FX (knob LEDs).

The LED task reads 42 entries from the active view (32 pads, 2 buttons, 8 knobs); SC17.3's Master FX buffer
had 32, so the knob LEDs showed whatever followed it in RAM (knob 5 magenta).  Now: buttons 32/33 as in the
Mixer; knobs 1-4 (Digitise: 1-2) lit in the selected effect's colour, the others off.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import linein2  # noqa: E402

s17.use_mixer14()
s17.use_full_leds()
s17.DIAG = "--diag" in sys.argv
NAME = "SC174D" if s17.DIAG else "SC17.4"
linein2.install(s15, s16)

if __name__ == "__main__":
    linein2.main(NAME, s17.build, s15, [x for x in sys.argv[1:] if x != "--diag"])
