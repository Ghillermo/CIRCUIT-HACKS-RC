"""Circuit Tracks 4486 - SC42.6 = SC42.5 + tools/sdpv.py (the step-drummer: pad 32 = the pitch-vel toggle (page 1 also moves the notes in degrees of
the scale, page 2 also sets the velocity), page 2 with its own destination (pads 17-24 on page 2), pad 30 of the MIDI tracks dim when off) +
cscale.use_mutroot() (random-mutate with the custom scale counts from the root).

SC42.5 = SC42.4 + fixes from the device (the user, 2026-10-16): arp.use_gatecap() (an arpeggiated note at most an arpeggio
step), stepgate.use_v2() (pads 31 / 32 only in the Micro Step mode of the Gate view's object; the selector closes by a timestamp), rollers.use_v2()
(cleared by a timestamp; recorded with Record) + tools/presetagain.py (Preset again in a drum's Preset view = the chromatic view on / off) + arp.use_cols2() (with Shift the arpeggiator's pads keep their
Pattern Settings colours, the chosen ones green) + tools/scdrum.py (K1-K4 of the Sidechain view on the drum pages)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42_5 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import cscale  # noqa: E402
import sdpv  # noqa: E402
cscale.use_mutroot()

NAME = "SC42.6"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "sdpv", sdpv)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
