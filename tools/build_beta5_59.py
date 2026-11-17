"""Circuit Tracks 4486 - Beta 5.59 (marker "B5.59") = SC57.4 with the beta's marker."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_2 as S2  # noqa: E402
import build_sc57_1 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import tabpack  # noqa: E402

NAME = "B5.59"
B = S.B


def extra(img, report):
    import dspz
    import xlanes
    S2.extra(img, report)
    dspz.add(img, report, "xlanes", xlanes)                                         # the outermost head of the save / load / LED task
    import scrules
    dspz.add(img, report, "scrules", scrules)                                       # chain rules per scene: the outermost heads now
    scrules.IO.install(img, report)                                                 # ... and its card work in the LED task, at the end


if __name__ == "__main__":
    tabpack.use()
    import patchain
    patchain.use_groups()                                                           # chains of pattern groups (scrules keeps them)
    import vcf21
    vcf21.use_trimpad()                                                             # (flash: the pad handlers nothing reaches)
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
