"""Circuit Tracks 4486 — SC19.6 = SC19.5 + the new drum knobs show their value as LED brightness.

The stock drum knobs (K2 / K4 / K6 / K8) light their LED with the colour of the drum scaled by the value of the stock parameter (dynamic LED codes, converter
0x0803423C); K1 / K3 / K5 / K7 (envelope, ring mod frequency, LFO amount, envelope -> cutoff) had a fixed colour.  Now they use the same scaling, taken from our own
values (the bytes saved with the project): unipolar values (ring mod frequency) = brightness, bipolar values = twice the distance from the centre (dark in the middle,
like the stock bipolar knobs), and with Shift held they show the Shift layer (pitch envelope, ring mod amount, LFO speed; the filter mode = 5 steps).
persist19.KNOB_LEVELS: the brightness travels in the high byte of the LED halfword and the converter's knob loop is hooked to split it again.  Everything else is SC19.5.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import build_sc19_5 as b195  # noqa: E402
import linein3  # noqa: E402
persist19.KNOB_LEVELS = True

NAME = "SC19.6"
b182 = b195.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b195.b191.extra)
