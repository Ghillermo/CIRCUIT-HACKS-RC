"""Circuit Tracks 4486 - Alpha 7.32 (marker "A7.32") = Alpha 7.31 + novasec.use_v3() (the user, on the device with 7.31): pad 1 (Macros) in the
synth's colour; Clear + knob back to the stock's on Macros (nothing on the other pages); pad 1 held + knob = that knob freed (Macros 2: the extra
knob); a hint on every assignment / free (the knob blinks white / red, orange = no room; pad 1 blinks in the target page's colour)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v3()
    import build_a7_31 as A31
    src = Path(A31.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.31"') == 2, "A7.31 marker strings"
    src = src.replace('"A7.31"', '"A7.32"')
    sys.argv = [A31.__file__] + sys.argv[1:]
    exec(compile(src, A31.__file__, "exec"), {"__name__": "__main__", "__file__": A31.__file__})
