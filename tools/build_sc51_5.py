"""Circuit Tracks 4486 - SC51.5 = SC51.4 + DSP core 1 started with OMR MS = 1 (tools/c1ms.py: the stub the stock sends to core 0 only, also to
core 1) and the FM slots' blocks of core 1 moved under X:$2000 (granular_dsp.use_c1ms): core 1 has P 8 K / X 8 K / Y 8 K instead of 2 K / 12 K / 10 K
(S514D2 on the device, 2026-11-04): 6 K words more of program for the next engines.  Nothing changes in use."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_4 as S  # noqa: E402
import granular_dsp  # noqa: E402
import linein3  # noqa: E402

NAME = "SC51.5"
B = S.B
granular_dsp.use_c1ms()


def extra(img, report):
    import dspz
    import c1ms
    S.extra(img, report)
    dspz.add(img, report, "c1ms", c1ms)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
