"""Circuit Tracks 4486 - Alpha 7.33 (marker "A7.33") = Alpha 7.32 + novasec.use_v4() (the user: «erase now erases all macro destinations (not just
1)»): pad 1 held + knob on Synth 1 / 2's Macros page resets all four slots of that macro."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v4()
    import build_a7_32 as A32
    src = Path(A32.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.32"') == 2, "A7.32 marker strings"
    src = src.replace('"A7.32"', '"A7.33"')
    sys.argv = [A32.__file__] + sys.argv[1:]
    exec(compile(src, A32.__file__, "exec"), {"__name__": "__main__", "__file__": A32.__file__})
