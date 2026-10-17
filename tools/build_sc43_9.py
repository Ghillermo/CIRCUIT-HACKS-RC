"""Circuit Tracks 4486 - SC43.9 = SC43.8 + dsp56.use_shortx() (the core-0 code appended after the stock program with the one-word
move x:(Rn+d): the same program, 441 words shorter) + vcf21_dsp / vcf21 / mpatch use_lfoshape / use_lshape (six LFO shapes for the own engine:
page 5, Shift + K8; per project and per patch).

SC43.8 = SC43.7 + scpat.use_drums() + vcf21.use_v2save() / tools/engsave.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56  # noqa: E402
dsp56.use_shortx()
import build_sc43_8 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_lfoshape()
import vcf21  # noqa: E402
vcf21.use_lfoshape()
import mpatch  # noqa: E402
mpatch.use_lshape()
import linein3  # noqa: E402

NAME = "SC43.9"


def extra(img, report):
    B.extra(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
