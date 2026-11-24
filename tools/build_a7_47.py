"""Circuit Tracks 4486 - Alpha 7.47 (marker "A7.47") = Alpha 7.45 + gmview.use_page2col() (7.46 redone: page 2 = a grid, column n = knob n = track n, rows K5 / pan / K3 / K8 lit = moved) (the user, 2026-11-24, the roadmap: «a second page for the
global macro view», «One page, pads pick»): in the view, Octave up / down = page 2 / 1; on page 2 knob Kn = track n and pads 1-4 pick its
K5 (cutoff), pan, K3 (envelope) or K8 (FX)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import gmview
    gmview.use_page2col()
    import build_a7_45 as A45
    src = Path(A45.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.45"') == 2, "A7.45 marker strings"
    src = src.replace('"A7.45"', '"A7.47"')
    sys.argv = [A45.__file__] + sys.argv[1:]
    exec(compile(src, A45.__file__, "exec"), {"__name__": "__main__", "__file__": A45.__file__})
