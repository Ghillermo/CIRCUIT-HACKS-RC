"""Circuit Tracks 4486 - S564D2 (diagnostic, marker "S564D2") = Beta 5.64 + tools/mpuwatch.py: an MPU read-only region over the 32 bytes holding the word
corrupted in the 5.63 / 5.64 crashes; the first write freezes the black box with the writer's PC / LR (read it with the app, Caja negra…)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_64 as S  # noqa: E402

NAME = "S564D2"
B = S.B


if __name__ == "__main__":
    S.options()
    import linein3
    _real = linein3.main
    def _named(name, build, s15, argv, extra=None):
        def ext(img, report):
            import dspz
            import mpuwatch
            if extra: extra(img, report)
            dspz.add(img, report, "mpuwatch", mpuwatch)
        return _real(NAME, build, s15, argv, extra=ext)
    linein3.main = _named
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_63.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
