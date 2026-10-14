"""Circuit Tracks 4486 - SC41.1 = SC41 + (the user, 2026-10-14, on the unit):
  * build_sc17.use_ledbuf(): the LED buffer of the Master FX view no longer overwrites the idle memory other modules keep their state in (with the view on
    the screen and much playing: Synth 2 stopped, the chains and the fractal order restarted, the step frequencies miscounted);
  * vcf21.use_fxseqrand() + build_sc17.use_fxseqrand(): a seventh value of the FX sequencer = one of the assigned slots at random."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41 as B  # noqa: E402
import build_sc17  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
build_sc17.use_ledbuf()
build_sc17.use_fxseqrand()
vcf21.use_fxseqrand()

NAME = "SC41.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
