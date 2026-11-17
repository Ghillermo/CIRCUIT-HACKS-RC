"""Circuit Tracks 4486 - S564D5 (diagnostic, marker "S564D5") = Beta 5.64 without knob hold (S564D4, without the FM algorithm map, bootlooped: a project with a custom FM algorithm needs it; the user, 2026-11-15: «can we do a more
extensive diagnostic by dropping an existing feature?» -> «Knob hold») + blackbox.use_memrd (live memory reads over USB: tools/bbread.py
--mem) + tools/mpuwatch.py (the MPU trap on 0x20042980..9F) + tools/dmawatch.py (the DMA streams at the first change of 0x20042988)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_64 as S  # noqa: E402
import build_sc56_7  # noqa: E402
import blackbox  # noqa: E402

NAME = "S564D5"
B = S.B


if __name__ == "__main__":
    S.options()
    build_sc56_7.DROP_KNOBHOLD = True
    blackbox.use_memrd()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            import dspz
            import mpuwatch
            import dmawatch
            dmawatch.DM = 0x2004F900                                     # knob hold's RAM (it is left out); mpuwatch keeps 0x2004FAF0
            if extra: extra(img, report)
            dspz.add(img, report, "mpuwatch", mpuwatch)
            dspz.add(img, report, "dmawatch", dmawatch)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
