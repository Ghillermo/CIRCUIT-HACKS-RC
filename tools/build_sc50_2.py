"""Circuit Tracks 4486 - SC50.2 = SC50.1 + vcf21_dsp.use_actfix (the LFO shapes sine, sample & hold and smoothed sample & hold silenced the engine's ACT slot) + vcf21.use_kslow / fmeng.use_kslow
(the user, 2026-11-01: type knobs need more action: at least 16 clicks a type) + vcf21.use_routedef (filter, VCA, FX by default)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc50_1 as B  # noqa: E402
import modmx  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_actfix()
import vcf21  # noqa: E402
vcf21.use_kslow(modmx.MXR + 0x21EC)
vcf21.use_routedef()
import modesel  # noqa: E402
modesel.use_bluedim()
import jumpseq  # noqa: E402
jumpseq.use_v2()
import fmeng  # noqa: E402
fmeng.use_kslow()
import linein3  # noqa: E402

NAME = "SC50.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
