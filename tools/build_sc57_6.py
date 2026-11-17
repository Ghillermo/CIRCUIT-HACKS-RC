"""Circuit Tracks 4486 - SC57.6 = SC57.5 + arp.use_timed() + tools/capkeep.py (fixes, also in RC4.12 / RC4.12S; the user, 2026-11-14): an arpeggio note
that falls between two micro steps (1/32 on a 1/8 track: swing) played at its time by the main loop; a latched / armed capture of Master FX's sample
goes on through a project load («fix and beta»).

Built on top of tools/build_sc57_5.py by import (not a copy: its main block runs here, with this marker and capkeep after its extra), so any later change to
SC57.5 follows."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc57_5 as S  # noqa: E402  (its imports set the chain's options: arp's RATE and states' RAM)
import arp  # noqa: E402
import linein3  # noqa: E402

NAME = "SC57.6"
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
    sys.argv = [str(Path(__file__).resolve().parent / "build_sc57_5.py")] + sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
