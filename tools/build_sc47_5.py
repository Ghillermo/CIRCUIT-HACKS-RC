"""Circuit Tracks 4486 - SC47.5 = SC47.4 + the voice modes of the own synth of MIDI 1 / 2 on pad 32 (the user, 2026-10-26: «implementa portamento.
asigna el toggle al pad 32, sin shift: retrig/legato/portamento/poly/unison. con un desplegable como el modo de voz»): tools/vmode.py (the row, K1
the portamento's time, K2 the unison's detune, saved with the patches at padding + 126..129), poly.use_v4() (the modes in retrig's byte, unison),
vcf21_dsp.use_glide() (the pitch offset: the glide, the unison's detune); and less SPI traffic for FM poly («tengo la sensación de que el clock se
vuelve inestable al usar FM poly»): fmeng.use_wcache() (a DSP word written only when it changes; the shape read once a track a tick), poly's
refresh every 4 ticks and the FM voices' zeroing at their first use only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_4 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_glide()
import fmeng  # noqa: E402
fmeng.use_wcache()
import poly  # noqa: E402
poly.use_v4()
import psave  # noqa: E402
import xpatch  # noqa: E402
psave.XLEN = xpatch.XLEN = 130                      # the exchange / the copy between packs carry the voice mode (padding + 126..129)
import vmode  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC47.5"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "vmode", vmode)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
