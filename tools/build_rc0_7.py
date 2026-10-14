"""Circuit Tracks 4486 - RC0.7 = RC0.6 + two fixes (the user, 2026-10-14: «fixes, si hay alguno, a RC»): vcf21.use_engfix() / build_sc17.use_engfix()
(the step-drummer, the FX sequencer, the stretch and the armed capture read the step and the ticks of their own track: they read another track's, unseen while
every track had the same length) and vcf21.use_fxseq4() (the selector knob of the FX sequencer three times slower).  Marker "RC0.7"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_6 as B  # noqa: E402  (configures everything as RC0.6)
import build_sc17 as S17  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
vcf21.use_engfix()
vcf21.use_fxseq4()
S17.use_engfix()

NAME = "RC0.7"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
