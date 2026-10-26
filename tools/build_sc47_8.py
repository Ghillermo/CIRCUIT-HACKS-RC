"""Circuit Tracks 4486 - SC47.8 = SC47.7 with less aliasing in the MIDI 1 / 2 own synth's oscillator (the user, 2026-10-26: «Estudia cómo reducir el
aliasing y el ruido», then «Ok a todo» to the study's option 1): vcf21_dsp.use_blep() (2-sample polyBLEP on the saw, the six side saws of the supersaw
and the pulse's two edges: a check a sample, a 24-step division at each step) + vcf21_dsp.use_foldlim() (the wavefold's extra drive at most
FOLD_K / the increment: x6.7 at note 72, x3.9 at 84, x2.4 at 96)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_7 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_blep()
vcf21_dsp.use_foldlim()
import linein3  # noqa: E402

NAME = "SC47.8"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
