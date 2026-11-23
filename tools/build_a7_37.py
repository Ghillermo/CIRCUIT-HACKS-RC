"""Circuit Tracks 4486 - Alpha 7.37 (marker "A7.37") = Alpha 7.36 + novasec.use_v8() (the user: «Pads 1, 9, 17 and 25 are now macro slots 1-4 ...
Holding any of these pads while moving a knob selects the slot to be assigned next ... The new assignment with duplicate copies destination and
range»): the slot pads, a picked slot written by Duplicate + knob (depth by the parameter's span), Clear + slot pad, the macro editor on pad 26."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v4(); novasec.use_v8()
    import build_a7_36 as A36
    src = Path(A36.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.36"') == 2, "A7.36 marker strings"
    src = src.replace('"A7.36"', '"A7.37"')
    sys.argv = [A36.__file__] + sys.argv[1:]
    exec(compile(src, A36.__file__, "exec"), {"__name__": "__main__", "__file__": A36.__file__})
