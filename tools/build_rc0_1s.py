"""Circuit Tracks 4486 — RC0.1S = RC0S (SC362S: nothing of ours writes the SD card) + what SC37.4 adds outside the SD card: vcf21_dsp.use_stglide()
(no click when the engine of pad 27 changes with a held note), vcf21.use_dualhide() (pad 28 only with oscillators), build_sc17.use_glitch3() (two
Glitch slots held together keep their knobs), build_sc17.use_vinyl_peach(), build_sc10.use_retcols() (the Setup return toggles in their colours).
Marker "RC0.1S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc362s as B  # noqa: E402  (configures everything as SC362S)
import build_sc10  # noqa: E402
import build_sc17  # noqa: E402
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.use_stglide()
vcf21.use_dualhide()
build_sc17.use_glitch3()
build_sc17.use_vinyl_peach()
build_sc10.use_retcols()

NAME = "RC0.1S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
