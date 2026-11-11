"""Circuit Tracks 4486 - SC56.2 = SC56.1 + tools/fwid.py (the user, 2026-11-11: «In the app, if the device is stock / an unknown custom build, support
only stock-compatible features» -> «Version query»): the device answers F0 7D 43 54 00 .. with the marker of the build it runs, so the SD apps can
tell this build (and every later one) from the stock firmware.  Nothing changes in use."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56_1 as S  # noqa: E402
import linein3  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.2"
B = S.B


def extra(img, report):
    import build_sc41_5 as B5
    import fwid
    S.extra(img, report)
    B5.add(img, report, "fwid", fwid)


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    S.S.room()
    S.cpu()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
