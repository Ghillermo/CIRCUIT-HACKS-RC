"""Circuit Tracks 4486 - SC56.1 = SC56 + vcf21_dsp.use_wskip() (the user, 2026-11-10: «build 1 and then 2», the CPU items): the own synth's
oscillator skips the waves whose morph weight is 0 (it computed all four, the supersaw's seven saws and their BLEP checks included, every sample);
the sound is the same bit for bit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56 as S  # noqa: E402
import linein3  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.1"
B = S.B
extra = S.extra


def cpu():
    import vcf21_dsp
    vcf21_dsp.use_wskip()


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    S.room()
    cpu()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
