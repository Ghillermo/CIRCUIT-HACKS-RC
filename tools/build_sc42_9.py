"""Circuit Tracks 4486 - SC42.9 = SC42.8 + drumarp.use_rec() (the drums' arpeggio recorded while playing with Record: micro step, sample flip,
velocity on an empty step).

SC42.8 = SC42.7 + tools/drumarp.py (the arpeggiator on the drums: Shift + pads 25 / 27-32 / 17-24 of a drum's Pattern
Settings; in its Preset view the samples held are arpeggiated, as the notes held on the note tracks).

SC42.7 = SC42.6 + sdpv.use_v2() (the step-drummer: a synth's empty pair starts from 0, the transposition one degree every 8
knob units, with the toggle page 1's pitch destinations left to the note) + rollers.use_free() (the rollers with the transport stopped, at the tempo) +
vcf21.use_routecol() (pad 29 of the MIDI Preset view in the VCA / VCF page's colour) + stepgate.use_v3() (pads 31 / 32 of the Micro Step view: the
same toggle again = off, the other one = off and the new one on; pad 31 off = the selector, a length chosen = on).

SC42.6 = SC42.5 + tools/sdpv.py (the step-drummer: pad 32 = the pitch-vel toggle (page 1 also moves the notes in degrees of
the scale, page 2 also sets the velocity), page 2 with its own destination (pads 17-24 on page 2), pad 30 of the MIDI tracks dim when off) +
cscale.use_mutroot() (random-mutate with the custom scale counts from the root).

SC42.5 = SC42.4 + fixes from the device (the user, 2026-10-16): arp.use_gatecap() (an arpeggiated note at most an arpeggio
step), stepgate.use_v2() (pads 31 / 32 only in the Micro Step mode of the Gate view's object; the selector closes by a timestamp), rollers.use_v2()
(cleared by a timestamp; recorded with Record) + tools/presetagain.py (Preset again in a drum's Preset view = the chromatic view on / off) + arp.use_cols2() (with Shift the arpeggiator's pads keep their
Pattern Settings colours, the chosen ones green) + tools/scdrum.py (K1-K4 of the Sidechain view on the drum pages)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42_8 as B  # noqa: E402
import drumarp  # noqa: E402
drumarp.use_rec()
import linein3  # noqa: E402

NAME = "SC42.9"


def extra(img, report):
    B.extra(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
