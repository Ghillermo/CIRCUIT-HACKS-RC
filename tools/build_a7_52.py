"""Circuit Tracks 4486 - Alpha 7.52 (marker "A7.52") = Alpha 7.51 + novasec.use_v12() + m2lanes.use_x2() (the user, 2026-11-24: «2 destinations on all
8 knobs», «Like the macro slots»): each Macros 2 knob of Synth 1 / 2 gets a second destination, moved with the first (knob and lane playback)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec, m2lanes
    novasec.use_v12()
    m2lanes.use_x2()
    import build_a7_51 as A51
    src = Path(A51.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.51"') == 2, "A7.51 marker strings"
    src = src.replace('"A7.51"', '"A7.52"')
    sys.argv = [A51.__file__] + sys.argv[1:]
    exec(compile(src, A51.__file__, "exec"), {"__name__": "__main__", "__file__": A51.__file__})
