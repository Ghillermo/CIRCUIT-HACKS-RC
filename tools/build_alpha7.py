"""Circuit Tracks 4486 - Alpha 7 (marker "ALPHA7") = Beta 5.65 with this marker: the first public alpha (2026-11-17, the user: «release as alpha7»,
«Beta 5.65 as Alpha 7»): everything since Beta 5.56 (5.57-5.65), not tested on the device, published next to RC4.11 / RC4.11S and Beta 5.56.
Built on top of tools/build_beta5_65.py (its options, its chain) with this marker."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402

NAME = "ALPHA7"

if __name__ == "__main__":
    A.S.options()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            A.extra_565(img, report)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
