"""Circuit Tracks 4486 - SC43.4 = SC43.3 + sdpv.use_v4() (the step-drummer: every destination bipolar, centred and dim at no modulation) +
tools/scpat.py (Synth 1 / 2 and MIDI 1 / 2 patterns as side-chain sources: row 1 pads 1-4 of the Sidechain view) + tools/qmute.py (Mixer: Shift +
a track pad = its mute toggle on the next bar, blinking while pending) + persist19.use_clrbc() (Clear + K8 of a drum puts the bitcrush back to 0
too) + tools/clrtrk.py (Clear + a Drum button on its views = its knobs back to their defaults).

SC43.3 = SC43.2 + sdpv.use_v3() (MIDI step-drummer from each destination's point of no modulation; LEDs show the amount)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_3 as B  # noqa: E402
import sdpv  # noqa: E402
import persist19  # noqa: E402
sdpv.use_v4()
persist19.use_clrbc()
import scpat  # noqa: E402
import qmute  # noqa: E402
import clrtrk  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402

NAME = "SC43.4"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "scpat", scpat)
    B5.add(img, report, "qmute", qmute)
    B5.add(img, report, "clrtrk", clrtrk)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
