"""Circuit Tracks 4486 - SC51.7 = SC51.6 + the 8-operator FM in place of the 4-operator one (the user, 2026-11-04: «one FM, up to 8 operators, on
pad 24», «Discard old FM», «Old patches load into the new one», DX7-style envelopes, the panel «Rates / levels split», pad 17 = the pitch
envelope): vcf21_dsp / granular_dsp.use_fm8 (the DSP: N of 8 operators on core 1, only the ones the algorithm uses), fmeng.use_fm8 (its code
gone; trampolines in the hole), poly.use_v11 (the voices through fm8), fm8 in dspz's gap (tools/fm8.py, fm8arm.py, fm8ui.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_6 as S  # noqa: E402
import fmeng  # noqa: E402
import granular_dsp  # noqa: E402
import linein3  # noqa: E402
import poly  # noqa: E402
import vcf21_dsp  # noqa: E402

NAME = "SC51.7"
B = S.B
vcf21_dsp.use_fm8()
granular_dsp.use_fm8()
fmeng.use_fm8()
poly.use_v11()


def extra(img, report):
    import dspz
    import fm8
    S.extra(img, report)
    dspz.add(img, report, "fm8", fm8)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
