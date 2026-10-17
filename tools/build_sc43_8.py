"""Circuit Tracks 4486 - SC43.8 = SC43.7 + scpat.use_drums() (Synth 1 / 2 and MIDI 1 / 2 as the trigger of the drums' side-chain: row 1
pads 1-4 of the Sidechain view's drum pages; each pattern note of that track fires the drum's envelope) + vcf21.use_v2save() / tools/engsave.py
(the own engine's codes 27..34 (OSC 2, the granular's Shift knobs) and the toggles of pads 28 / 29 survive a power cycle).

SC43.7 = SC43.6 + dpitch.use_lane0() + clrtrk.use_autoclr() + tools/retrig.py + srcview.use_keepplay() / tools/sdkeep.py + rollers.use_mute()
+ arp.use_viewoff() + arp / drumarp use_rateflip() + tools/quant.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_7 as B  # noqa: E402
import scpat  # noqa: E402
scpat.use_drums()
import vcf21  # noqa: E402
vcf21.use_v2save()
import engsave  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402

NAME = "SC43.8"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "engsave", engsave)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
