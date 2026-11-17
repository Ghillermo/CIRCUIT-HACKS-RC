"""Circuit Tracks 4486 - Beta 5.62 (marker "B5.62") = Beta 5.61 + arp.use_tmfix() (a fix; the user, 2026-11-14, on Beta 5.61: «if I press play it plays for a fraction of a second and hangs»): use_timed's armed arpeggio notes played by the main loop right after it gives the DSP service's lock back, not inside it (the note's sound path takes that lock again: the unit hung).

Built on top of tools/build_beta5_61.py by import (not a copy: its main block runs here with this marker), so any later change to it follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_61 as S  # noqa: E402
import arp  # noqa: E402
import linein3  # noqa: E402

NAME = "B5.62"
B = S.B


if __name__ == "__main__":
    _main = linein3.main
    def _wrapped(name, build, s15, argv, extra=None):
        arp.use_tmfix()                                                             # (use_timed is set by now)
        return _main(NAME, build, s15, argv, extra=extra)
    linein3.main = _wrapped
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_61.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
