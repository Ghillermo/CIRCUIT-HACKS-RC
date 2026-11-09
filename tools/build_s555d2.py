"""Circuit Tracks 4486 - S555D2 (DIAGNOSTIC) = S555D + clkdiag.use_seqcul(): Play in the colour of what ran long before a late sequencer tick (the user: «play violet sometimes when loading new patches», «Custom patches»). S555D = SC55.5 / Beta 5.40 + tools/clkdiag.py (the user, 2026-11-09: «Clock seems unstable, specially when
loading new FM patches or using morph with FM/custom patches»): Save = core 0 of the DSP's time margin (white = the output ring ran dry),
Duplicate = the ARM main loop late and what ran meanwhile (white = a card access from the mod, blue = the stock's, peach = the DSP service, orange
= the LED task, red = a knob, green = a pad, yellow = none), Play violet = the sequencer's tick late.  ARM only: the DSP programs are SC55.5's.
See firmware/s555d2/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55_5 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "S555D2"
B = S.B


def extra(img, report):
    import build_sc41_5 as B5
    import clkdiag
    clkdiag.use_seqcul()
    S.extra(img, report)
    B5.add(img, report, "clkdiag", clkdiag)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
