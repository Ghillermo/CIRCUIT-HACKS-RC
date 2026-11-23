"""Circuit Tracks 4486 - Alpha 7.34 (marker "A7.34") = Alpha 7.33 + novasec.use_v5(): on Synth 1 / 2's alt page, Macros' knob LEDs drawn every
frame in the synth's colour, bright as each macro (the stock does not redraw them while the transport runs: a section page's colours stayed)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v5()
    import build_a7_33 as A33
    src = Path(A33.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.33"') == 2, "A7.33 marker strings"
    src = src.replace('"A7.33"', '"A7.34"')
    sys.argv = [A33.__file__] + sys.argv[1:]
    exec(compile(src, A33.__file__, "exec"), {"__name__": "__main__", "__file__": A33.__file__})
