"""Circuit Tracks 4486 - SC47 = SC46.9 + vcf21_dsp.use_scalemac() + vcf21_dsp.use_poly() + tools/poly.py (the user, 2026-10-25: «Polifonía: todos
los modos de MIDI, 4 voces si es posible. Voice stealing idealmente en la más antigua de su propio canal. En caso de vcavcf compartidos, nueva nota
abre Gate de nuevo. Noteoff desactiva el pitch correspondiente y cierra Gate cuando no quedan pitchs activos»), phase 1: 4 voices per track in the
plain oscillator and the sample mode of MIDI 1 / 2 (Shift + pad 29: retrigger -> legato -> poly); + use_smswap (the stereo sample's
first sample on the left, the whole width at the far right).  «SC46.10» would be cut to «SC46.1»."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_9 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_scalemac()
vcf21_dsp.use_poly()
vcf21_dsp.use_smswap()
import poly  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC47"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "poly", poly)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
