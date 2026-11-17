"""Circuit Tracks 4486 - S579D (diagnostic, marker "S579D") = Beta 5.63 + both slot-7 guards (fixes563.vtguard: the 5.63 crash can no longer reset the
device) + tools/cwatch.py: a head of the LED task that freezes the black box the moment one of the four drum velocity-bar objects loses its vtable
words (the one-byte corruption behind the crash), so the record's ring shows the gesture that writes there.  Read it with the app (Caja negra…).
Without the mute step of Beta 5.64 (flash)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_63 as S  # noqa: E402
import fixes563  # noqa: E402
import linein3  # noqa: E402

NAME = "S579D"
B = S.B


if __name__ == "__main__":
    fixes563.beta(); fixes563.vtguard()
    _main = linein3.main
    def _wrapped(name, build, s15, argv, extra=None):
        def ext(img, report):
            import dspz
            import cwatch
            if extra: extra(img, report)
            fixes563.extra_beta(img, report)
            dspz.add(img, report, "cwatch", cwatch)
        return _main(NAME, build, s15, argv, extra=ext)
    linein3.main = _wrapped
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_62.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
