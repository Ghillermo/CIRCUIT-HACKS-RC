"""Circuit Tracks 4486 - SC44.2 = SC44.1 with thumb.COMPACT (the ARM's movw + movt pairs as loads from literal pools: 3 132 B of flash back) +
tools/modmx.py (the user, 2026-10-18: a light mod matrix for the own synth of MIDI 1 / 2: pad 6 = its knob page, K1..K8 = velocity, note,
random, LFO 2, envelope 2, drum hit, pattern position, step random; the knob's position = the destination (every parameter of the knob pages,
one zone each, the page's colour) and, inside the zone, the amount; slow knobs) + psave.XLEN = 88 (the exchange / the copy between packs of an
own-synth patch carry its matrix, padding + 64..87) + tools/split4.py (the split keyboard of any two note tracks: Synth 1, Synth 2, MIDI 1,
MIDI 2; the one held first plays pads 1-16)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thumb  # noqa: E402
thumb.COMPACT = True
import psave  # noqa: E402
psave.XLEN = 88
import build_sc44_1 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import modmx  # noqa: E402
import split4  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.2"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "modmx", modmx)
    B5.add(img, report, "split4", split4)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
