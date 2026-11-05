"""Circuit Tracks 4486 - S514D (DIAGNOSTIC) = SC51.4 + the memory budget (the user, 2026-11-04: «diagnostic the 4k», «diagnostic every remaining unknown
area, to make sure we know our budget»): granular_dsp.use_memdiag (core 1 reports its OMR, write tests of P / X / Y and the 64-word blocks of its X / Y
that change, into external Y at granular_dsp.MREP; the Glitch left out for room) + tools/rdiag.py with DSPX / DSPW / RAMCK (the PC reads core 0's X / Y
and the report, fills and checks ARM RAM with canaries: tools/memmap.py) + tools/dspload.py, in the dspz gap.  S514D2 = the same with core 1 started
with MS = 1 (tools/c1ms.py).  See firmware/s514d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_4 as S  # noqa: E402
import granular_dsp  # noqa: E402
import rdiag  # noqa: E402
import linein3  # noqa: E402

NAME = "S514D"
B = S.B
rdiag.DSPX = True
rdiag.DSPW = True
rdiag.DELETE = False
rdiag.RAMCK = True
granular_dsp.use_memdiag()
MS1 = False


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
    if MS1:
        import c1ms
        dspz.add(img, report, "c1ms", c1ms)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
