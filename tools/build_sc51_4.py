"""Circuit Tracks 4486 - SC51.4 = SC51.3 + the FM voices of the own synth on DSP core 1 (vcf21_dsp / granular_dsp / poly / fmeng / vguard: use_fmc1,
use_v10, use_wc12, use_c1late): six FM voices a track (12 in all, was 3 + 3 with both tracks in FM poly), core 0 freed of the FM loop (the user,
2026-11-04: «amplía el número de voces ahora», after S513D: core 1 runs ~10 FM voices, ~8 with the granular, and core 0 never waits)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_3 as S  # noqa: E402
import vcf21_dsp  # noqa: E402
import granular_dsp  # noqa: E402
import poly  # noqa: E402
import fmeng  # noqa: E402
import vguard  # noqa: E402
import linein3  # noqa: E402

NAME = "SC51.4"
B = S.B
extra = S.extra
vcf21_dsp.use_fmc1()
granular_dsp.use_fmc1()
poly.use_v10()
fmeng.use_wc12()
vguard.use_c1late()


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
