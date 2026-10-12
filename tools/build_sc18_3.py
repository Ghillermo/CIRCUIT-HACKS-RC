"""Circuit Tracks 4486 — SC18.3 = SC18.2 with the FX view Octave colours taken from the FX view pads (user's choice):
Octave UP (delay) = the colour of pad 1 (code 0x6B), Octave DOWN (reverb) = the colour of pad 17 (code 0x2A).
Duplicate / "1-16 / 17-32" keep SC18.2's colours (anything but white).  Everything up to SC18.2 is unchanged.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import leds18  # noqa: E402
leds18.PEACH, leds18.CREAM = 0x6B, 0x2A   # FX view (reverb page): pad 1 / pad 17, not selected
import build_sc18_2 as b182  # noqa: E402
import linein3  # noqa: E402

NAME = "SC18.3"

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b182.extra)
