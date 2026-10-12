"""Circuit Tracks 4486 — SC23 = SC22.4 + the on-device editor of the CC assignments of the MIDI macros (pad 25 of the MIDI Preset view).

Pad 25 switches the editor on / off for the track of the Preset view.  With the editor on, the first touch of a knob selects it and shows (on the 32 pads, with the digits of the tempo display) the CC of that macro
in the current template; the next turns change it; the button of the track (MIDI 1 / MIDI 2) steps CC -> start -> end of the range -> save (NRPN / RPN: MSB, LSB, then start and end, in two halves when the value
is 14 bit).  Everything else is SC22.4.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import build_sc22_4 as b224  # noqa: E402
import linein3  # noqa: E402
vcf21.use_cced()
b223 = b224.b223

NAME = "SC23"

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=b223.b22.b214.b213.extra)
