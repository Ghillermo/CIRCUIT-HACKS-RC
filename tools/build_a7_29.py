"""Circuit Tracks 4486 - Alpha 7.29 (marker "A7.29") = Alpha 7.28 + novasec.use_v2() (Synth 1 / 2's alt page: Shift + pad 1 = Macros 2, 8 extra knobs
saved with the project; Duplicate + knob on a section page = that parameter to the first free macro, else the first free extra knob; Clear + knob
on Macros = that macro's first destination freed, on Macros 2 = that extra knob freed)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec, srcview
    novasec.use_v2()
    srcview.use_keepcd()
    import build_a7_28 as A28
    src = Path(A28.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.28"') == 2, "A7.28 marker lines"
    src = src.replace('"A7.28"', '"A7.29"')
    sys.argv = [A28.__file__] + sys.argv[1:]
    exec(compile(src, A28.__file__, "exec"), {"__name__": "__main__", "__file__": A28.__file__})
