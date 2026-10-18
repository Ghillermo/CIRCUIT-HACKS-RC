"""Circuit Tracks 4486 - SC44.3 = SC44.2 + vcf21_dsp / vcf21 use_lfoshape2() (the own engine's LFO: the triangle by default, a seventh shape
= slewed sample & hold) + modmx.use_v2() (the matrix's LFO 2: slewed sample & hold as a fifth shape, the engine LFO's colours) (the user,
2026-10-18: «Fix: set triangle as default waveshape for the lfo, add s&h (stepped random) and slewed s&h (glided random) as waveshapes»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21_dsp  # noqa: E402
import vcf21  # noqa: E402
import build_sc44_2 as B  # noqa: E402
vcf21_dsp.use_lfoshape2()
vcf21.use_lfoshape2()
import modmx  # noqa: E402
modmx.use_v2()
import linein3  # noqa: E402

NAME = "SC44.3"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
