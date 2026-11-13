"""Circuit Tracks 4486 - SC56.7 = SC56.6 + tools/knobhold.py (the user, 2026-11-12: «Al mover un knob mientras se cambia de vista, el knob retiene
su asignación anterior hasta que se deja de tocar durante un segundo»): knob hold, switched on / off with Preset in the Setup view (off at the factory); + fmmap / patmut use_lrram() (fix, issue #22: Beta 5.48-5.51
reset the unit in MIDI 1 / 2's Preset view, the LED task's stack)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56_6 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.7"
B = S.B


def extra(img, report):
    import dspz
    import knobhold
    S.extra(img, report)
    dspz.add(img, report, "knobhold", knobhold)


if __name__ == "__main__":
    tabpack.use()
    import patmut
    patmut.use_v2()
    S.S.S.S.S.S.S.room()
    S.S.S.S.S.S.cpu()
    morphz.use_four()
    morphz.use_slow()
    import fmmap
    fmmap.use_lrram()
    patmut.use_lrram()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
