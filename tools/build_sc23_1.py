"""Circuit Tracks 4486 — SC23.1 = SC23 + the editor scheme asked for after the first design: Octave v / ^ (buttons 19 / 20) cycle the fields of the selected knob (no save at the end),
the button of the track (MIDI 1 / MIDI 2) saves, and any button that changes the view (Synth, Drum, Preset, Mixer, FX, the other MIDI) or pad 25 / a template pad discards the unsaved changes.
The changes are applied live as before; before the first one the 8 records of the template are copied to the idle LED buffer of the Master FX block, and a discard puts them back.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import build_sc23 as b23  # noqa: E402
import linein3  # noqa: E402
vcf21.use_cced2()
b224 = b23.b224
b223 = b23.b223

NAME = "SC23.1"

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b223.b22.b214.b213.extra)
