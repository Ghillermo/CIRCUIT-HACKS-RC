"""Circuit Tracks 4486 - Beta 5.65 (marker "B5.65") = Beta 5.64 + tools/paintguard.py: the stock probability / velocity-bar painters skip a step value
they cannot draw (the 5.63 / 5.64 crashes: a pad painter ran past its 16-pad LED buffer and trampled the next object; caught on the device by S564D5).
Built on top of tools/build_beta5_64.py (its options, its chain) with this marker."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_64 as S  # noqa: E402

NAME = "B5.65"
B = S.B


def extra_565(img, report):
    import dspz
    import paintguard
    paintguard.FREEZE = "auto"                                     # a skip freezes the black box once: the gestures that made the bad step
    dspz.add(img, report, "paintguard", paintguard)


if __name__ == "__main__":
    S.options()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            extra_565(img, report)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
