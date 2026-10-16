"""Circuit Tracks 4486 - SC42.4 = SC42.3 + vcf21.use_clrauto() (the own synth of MIDI 1 / 2: Clear + knob right = default, lavender; left = its
automation cleared, red) + build_sc17.use_gclear2() (Master FX: only the lavender of a knob at its default) + tools/rollers.py (micro-step rollers in
rows 1-3 of the drums' Note view) (the user, 2026-10-16)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42_3 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
import build_sc17  # noqa: E402
import rollers  # noqa: E402
vcf21.use_clrauto()
build_sc17.use_gclear2()

NAME = "SC42.4"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "rollers", rollers)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
