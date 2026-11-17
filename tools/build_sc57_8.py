"""Circuit Tracks 4486 - SC57.8 = SC57.7 + the fixes of the 2026-11-14 bug hunt (tools/fixes563.py; see docs/NOTAS.md, «Beta 5.63»; = Beta 5.63 with the
SC marker).

Room: tabpack.use_fm2() (the FM's exp / inc / bexp tables packed: +536 B in dspz's first gap).

Built on top of tools/build_sc57_7.py by import (its main block runs here with this marker and fixes563.extra_beta after its extra), so any later change
to it follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_7 as S  # noqa: E402
import linein3  # noqa: E402
import fixes563  # noqa: E402

NAME = "SC57.8"
B = S.B


if __name__ == "__main__":
    fixes563.beta()
    _main = linein3.main
    def _wrapped(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            fixes563.extra_beta(img, report)
        return _main(NAME, build, s15, argv, extra=ext)
    linein3.main = _wrapped
    sys.argv = [str(Path(__file__).resolve().parent / "build_sc57_7.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
