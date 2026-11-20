"""Circuit Tracks 4486 - Alpha 7.18 (marker "A7.18") = Alpha 7.17 + gmview.use_dimled() (the global macro view's knob LEDs: a linked knob that is
not the picked one in its track's dim colour, clearly darker than the picked one; the user: «Clearer states only»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import gmview
    gmview.use_dimled()
    import build_a7_17 as A17
    src = Path(A17.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.17"') == 2, "A7.17 marker lines"
    src = src.replace('"A7.17"', '"A7.18"')
    sys.argv = [A17.__file__] + sys.argv[1:]
    exec(compile(src, A17.__file__, "exec"), {"__name__": "__main__", "__file__": A17.__file__})
