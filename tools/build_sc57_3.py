"""Circuit Tracks 4486 - SC57.3 = SC57.2 + fm8ui.use_noinst() (the user, 2026-11-13: «drop the FM patches from the flash», «the 48 instruments»:
no built-in FM instruments, no fm8dest; room for the extra automation lanes) + p4dest.use_dup() (Duplicate + knob sends a knob to the
assigned-knob view / frees a slot there; no Shift + knob scroller, no p4ovl).

SC57.2 = SC57.1 + tools/jumprnd.py (the user, 2026-11-13: a step flip step with several notes jumps to one of their steps
at random) + tools/jsaflip.py (its stopped pre-listen on a drum target plays the step's sample flip)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_2 as S2  # noqa: E402
import build_sc57_1 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC57.3"
B = S.B


def extra(img, report):
    import dspz
    import xlanes
    S2.extra(img, report)
    dspz.add(img, report, "xlanes", xlanes)                                         # the outermost head of the save / load / LED task


if __name__ == "__main__":
    tabpack.use()
    import patmut
    patmut.use_v2()
    S.S.S.S.S.S.S.S.S.S.S.S.room()
    S.S.S.S.S.S.S.S.S.S.S.cpu()
    morphz.use_four()
    morphz.use_slow()
    morphz.use_rrfix()
    morphz.use_newstop()
    morphz.use_fastatk()
    import fmmap
    fmmap.use_lrram()
    patmut.use_lrram()
    import knobhold
    knobhold.use_freeze()
    import fm8ui
    import build_sc55_7
    fm8ui.use_noinst()
    build_sc55_7.FM8DEST = False
    import p4dest
    p4dest.use_dup()
    import blackbox
    blackbox.use_v2()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
