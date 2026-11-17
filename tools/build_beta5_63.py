"""Circuit Tracks 4486 - Beta 5.63 (marker "B5.63") = Beta 5.62 + the fixes of the 2026-11-14 bug hunt (tools/fixes563.py; see docs/NOTAS.md, «Beta 5.63»):
the extra lanes' and the chains' save to the right project (pack / slot were swapped: another project grew or a phantom file appeared), the
unaligned memsets (the crash recording VA knobs), edits while stopped kept, atomic tails, Clear + scene clears its chains, a freed sequenceable slot
plays nothing (the engine turned off), the step flip's pending jump / hung note / sample / counts, the arpeggio timed with an external clock, a kept
capture's STATE resent after a restart.

Room: tabpack.use_fm2() (the FM's exp / inc / bexp tables packed: +536 B in dspz's first gap, where the fixes' modules live).  A first plan reused two
«dead» stock functions: they are live (pc-relative addw): never reuse stock code.

Built on top of tools/build_beta5_62.py by import (its main block runs here with this marker and fixes563.extra_beta after its extra), so any later
change to it follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_62 as S  # noqa: E402
import linein3  # noqa: E402
import fixes563  # noqa: E402

NAME = "B5.63"
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
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_62.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
