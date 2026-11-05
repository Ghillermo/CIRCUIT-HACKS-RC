"""Circuit Tracks 4486 - S516D (DIAGNOSTIC) = SC51.6 + granular_dsp.use_novadump (core 1 copies a range of its external X, where the stock keeps the Nova
oscillator waves, to external Y for the PC: tools/novadump.py; the Glitch left out) + rdiag DSPX / DSPW in the dspz gap.  The dumps stay in re/ (not in git).
See firmware/s516d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_6 as S  # noqa: E402
import granular_dsp  # noqa: E402
import rdiag  # noqa: E402
import linein3  # noqa: E402

NAME = "S516D"
B = S.B
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
granular_dsp.use_novadump()


class _RD:
    @staticmethod
    def install(img, report, base):
        labels, code = rdiag.install(img, report, base)
        return labels, code, {}


def extra(img, report):
    import dspz
    S.extra(img, report)
    dspz.add(img, report, "rdiag", _RD)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
