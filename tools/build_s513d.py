"""Circuit Tracks 4486 - S513D (DIAGNOSTIC) = SC51.3 + granular_dsp.use_fmload (core 1 runs N dummy FM voices a block: does it have the time for the
FM voices?  The user, 2026-11-04: «¿Podemos mejorar el FM a seis operadores? ¿O mejorar la polifonía?» -> the study «las voces FM en el núcleo 1»
in docs/NOTAS.md -> «Si» to its diagnostic) + tools/rdiag.py with DSPX / DSPW (the PC sets N and reads the counters: tools/ctremote.py) +
tools/dspload.py (Save = core 0's time, Duplicate = the own synth's peak), both in the dspz gap.  See firmware/s513d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_3 as S  # noqa: E402
import granular_dsp  # noqa: E402
import rdiag  # noqa: E402
import linein3  # noqa: E402

NAME = "S513D"
B = S.B
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
granular_dsp.use_fmload()


class _RD:
    @staticmethod
    def install(img, report, base):
        labels, code = rdiag.install(img, report, base)
        return labels, code, {}


def extra(img, report):
    import dspz
    import dspload
    S.extra(img, report)
    dspz.add(img, report, "rdiag", _RD)
    dspz.add(img, report, "dspload", dspload)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
