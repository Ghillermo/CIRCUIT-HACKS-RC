"""Circuit Tracks 4486 - SC52.2 = SC52.1 + latchstep.use_heldcue() (the user, 2026-11-05: «simplemente no les cambies el color. En su lugar,
mientras se mantiene el pad con shift (para escribir en él) se pone del mismo color que el latch (turquesa) …»): in the Note view, Shift no longer
turns the steps yellow; the step a Shift press wrote the latched notes into lights cyan (0x4D) until it is released.  + vcf21.use_osc2pg2() (the
OSC 2 page re-laid out: «k1: pitch, k2: pitch fino. k3: shape k4: mezcla. K5: FM, 6,7,8 iguales») + vcf21.use_ratio2() / vcf21_dsp.use_ratio2() (OSC 2's coarse tune = a ratio of OSC 1, the fine = detune) + wtui.use_smpcyc / use_rowfix + tools/ovltop.py (the destination overlays
painted last: the engine row hid them)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_1 as S  # noqa: E402
import latchstep  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.2"
B = S.B


def extra(img, report):
    S.extra(img, report)
    import dspz
    import ovltop
    dspz.add(img, report, "ovltop", ovltop, gap=1)    # the destination overlays on top of the engine row / the flips (the last head of the template view)
latchstep.use_heldcue()
import vcf21  # noqa: E402
vcf21.use_osc2pg2()                          # the OSC 2 page: K1 pitch, K2 fine, K3 shape, K4 mix, K5 FM (K6-K8 as before)
vcf21.use_ratio2()                           # K1 = a ratio of OSC 1 (0.25, 0.5, 1..31), K2 = the detune
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_ratio2()
import wtui  # noqa: E402
wtui.use_smpcyc()                            # pad 8's sample cycles really copied (core 1's sample job)
wtui.use_rowfix()                            # the engine row open: pads 7 / 8 nothing with FM off


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
