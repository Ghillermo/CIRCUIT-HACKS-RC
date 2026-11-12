"""Circuit Tracks 4486 - SC56.6 = SC56.5 + tools/blackbox.py (the user, 2026-11-12: «Build it in the firmware and app»): a black box for a
panel that stops answering while the sound goes on (a tester, Beta 5.29): breadcrumbs of the inputs and the LED task, and a watchdog in the main
loop that, playing with no LED frame for 15 s, freezes the record (the panel task's saved stack and PC) and restarts the unit; read over USB."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56_5 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.6"
B = S.B


def extra(img, report):
    import dspz
    import blackbox
    S.extra(img, report)
    dspz.add(img, report, "blackbox", blackbox)


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    S.S.S.S.S.S.room()
    S.S.S.S.S.cpu()
    morphz.use_four()
    morphz.use_slow()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
