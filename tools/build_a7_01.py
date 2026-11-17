"""Circuit Tracks 4486 - Alpha 7.01 (marker "A7.01") = Alpha 7 / Beta 5.65 + blackbox.use_showall(): Save blinks violet for as long as a black box
record waits to be read (a crash, a lock-up, a watchdog restart or a skipped value), until the app's Clear; before, only for 30 s after a restart, and
a skipped value (paintguard) showed nothing (2026-11-17, the user: «we need users to know when they need to dump the blackbox», «Use alpha 7.01 as name»).
Built on top of tools/build_beta5_65.py (its options, its chain) with this marker."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_65 as A  # noqa: E402

NAME = "A7.01"

if __name__ == "__main__":
    A.S.options()
    import blackbox
    blackbox.use_showall()
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
