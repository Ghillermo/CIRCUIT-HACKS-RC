"""Circuit Tracks 4486 - RC4.17 (marker "R417") = RC4.16 + tools/dbtoggle.py (a fix; the user, 2026-11-18: «Pages (shift+tracks 1-4) exit wrong
when they are opened and shift+any track is pressed again» -> «Toggle: exit»): Shift + Synth 1 / 2 / MIDI 1 / 2 with that track's page on the
screen = back to its Note view (it used to open the page again)."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dbtoggle
    import build_r416 as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('NAME = "R416"', 'NAME = "R417"')
    k = "        fixes704.extra_rc(img, report)"
    assert k in src
    src = src.replace(k, k + "\n        dbtoggle.append(img, report)")
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__, "dbtoggle": dbtoggle})
