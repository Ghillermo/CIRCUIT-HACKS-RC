"""Circuit Tracks 4486 - Alpha 7.36 (marker "A7.36") = Alpha 7.35 + novasec.use_v7() (the user: «make duplicate (assign) work outside the
alt-page, when playing regularly with a view opened»; «Section page follows»): the section page picked on Synth 1 / 2's alt page stays on that
synth's knobs in its other views, with Duplicate + knob."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import novasec
    novasec.use_v7()
    import build_a7_35 as A35
    src = Path(A35.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.35"') == 2, "A7.35 marker strings"
    src = src.replace('"A7.35"', '"A7.36"')
    sys.argv = [A35.__file__] + sys.argv[1:]
    exec(compile(src, A35.__file__, "exec"), {"__name__": "__main__", "__file__": A35.__file__})
