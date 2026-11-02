"""Circuit Tracks 4486 - RC4.05S (marker "R405S") = RC4.04S + vcf21_dsp.use_actfix (the LFO shapes sine, sample & hold and smoothed sample & hold silenced the engine's ACT slot)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r404s as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_actfix()
import modesel  # noqa: E402
modesel.use_bluedim()
import linein3  # noqa: E402

NAME = "R405S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
