"""Circuit Tracks 4486 - Beta 5.61 (marker "B5.61") = Beta 5.60 + arp.use_timed() + tools/capkeep.py (= SC57.6 with the beta's marker).

Built on top of tools/build_beta5_60.py by import (not a copy: its main block runs here, with this marker and capkeep after its extra), so any later change to
Beta 5.60 follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_beta5_60 as S  # noqa: E402  (its imports set the chain's options: arp's RATE and states' RAM)
import arp  # noqa: E402
import linein3  # noqa: E402

NAME = "B5.61"
B = S.B


def _add_capkeep(img, report):
    import dspz
    import capkeep
    dspz.add(img, report, "capkeep", capkeep)                                       # the capture kept through a load (dspz gap: 36 of 64 B)


if __name__ == "__main__":
    arp.use_timed()                                                                 # arpeggio notes between micro steps on time
    _main = linein3.main
    def _wrapped(name, build, s15, argv, extra=None):
        def ext(img, report):
            if extra: extra(img, report)
            _add_capkeep(img, report)
        return _main(NAME, build, s15, argv, extra=ext)
    linein3.main = _wrapped
    sys.argv = [str(Path(__file__).resolve().parent / "build_beta5_60.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
