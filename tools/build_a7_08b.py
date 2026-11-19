"""Circuit Tracks 4486 - Alpha 7.08b (marker "A7.08b") = Alpha 7.08 + fxstep.use_smpcol() (the user, 2026-11-19: «Los pasos con sampler no se
pintan de amarillo, corrígelo y sube a 7.08»): the Master FX step sequencer's steps with the sample (pad 7) light yellow.  A new marker: a
rebuild under «A7.08» would not install over the published 7.08 (same version block)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import fxstep
    fxstep.use_smpcol()
    import build_a7_08 as A8
    src = Path(A8.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.08"') == 3, "A7.08 marker lines (docstring, NAME, assert)"
    src = src.replace('"A7.08"', '"A7.08b"')
    sys.argv = [A8.__file__] + sys.argv[1:]
    exec(compile(src, A8.__file__, "exec"), {"__name__": "__main__", "__file__": A8.__file__})
