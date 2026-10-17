"""Circuit Tracks 4486 - SC43.7 = SC43.6 + dpitch.use_lane0() (K1 = the stock continuous pitch again; the chromatic pads on top, their recorded
steps tagged in the drum's own pitch lane: lane 7 is the drum's pan automation again) + clrtrk.use_autoclr() (Clear + Drum = its automation
deleted, then its knobs to their defaults) + tools/retrig.py (MIDI 1 / 2: Shift + pad 29 of the Preset view = gate retrigger on / off) + srcview.use_keepplay() / tools/sdkeep.py (the step-drummer of Synth 1 / 2: Play / Record keep
its view; the synth's button brings it back) + rollers.use_mute() (the rollers of a drum muted in the Mixer play) + arp.use_viewoff() (the first
note held stopped through its view: on MIDI 1 / 2 it stayed on under the arpeggio) + arp / drumarp use_rateflip() (the resolution pads in the stock's
sync rate order: slower to the left) + tools/quant.py (Shift + Play = the selected track's pattern quantized).

SC43.6 = SC43.5 + dpitch.use_rec() + tools/cue.py + vcf21.use_lastnote() / use_n2first() / use_osc2pg()."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_6 as B  # noqa: E402
import dpitch  # noqa: E402
dpitch.use_lane0()
import clrtrk  # noqa: E402
clrtrk.use_autoclr()
import retrig  # noqa: E402
import srcview  # noqa: E402
srcview.use_keepplay()
import sdkeep  # noqa: E402
import rollers  # noqa: E402
rollers.use_mute()
import arp  # noqa: E402
arp.use_viewoff()
arp.use_rateflip()
import drumarp  # noqa: E402
drumarp.use_rateflip()
import quant  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402

NAME = "SC43.7"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "retrig", retrig)
    B5.add(img, report, "sdkeep", sdkeep)
    B5.add(img, report, "quant", quant)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
