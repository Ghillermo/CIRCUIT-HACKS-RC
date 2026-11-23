"""Circuit Tracks 4486 - Alpha 7.35 (marker "A7.35") = Alpha 7.34 + novasec.use_v6() (the user: «The selected knob doesnt go to the free knob.
instead, it goes to the shift knobs»): Duplicate + knob takes a free macro before an extra knob that already holds the parameter (that extra knob
freed)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v6()
    import build_a7_34 as A34
    src = Path(A34.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.34"') == 2, "A7.34 marker strings"
    src = src.replace('"A7.34"', '"A7.35"')
    sys.argv = [A34.__file__] + sys.argv[1:]
    exec(compile(src, A34.__file__, "exec"), {"__name__": "__main__", "__file__": A34.__file__})
