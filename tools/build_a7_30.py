"""Circuit Tracks 4486 - Alpha 7.30 (marker "A7.30") = Alpha 7.29 + novasec.use_fix(): the extra knobs (Macros 2) saved in bytes 4 / 5 of Synth 1 / 2's
patterns 0..4 settings (7.29 used bytes 38 / 39, which are fm8store's FM project block: a save overwrote them and they broke the FM's sum); c_nsval
through c_nsget and the macro's four fields written in a loop (smaller)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec, srcview
    novasec.use_v2(); novasec.use_fix()
    srcview.use_keepcd()
    import build_a7_28 as A28
    s28 = Path(A28.__file__).read_text(encoding="utf-8")
    assert s28.count('"A7.28"') == 2, "A7.28 marker lines"
    s28 = s28.replace('"A7.28"', '"A7.30"')
    sys.argv = [A28.__file__] + sys.argv[1:]
    exec(compile(s28, A28.__file__, "exec"), {"__name__": "__main__", "__file__": A28.__file__})
