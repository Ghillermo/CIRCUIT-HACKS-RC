"""Circuit Tracks 4486 - Alpha 7.40 (marker "A7.40") = Alpha 7.39 + morphz.use_smooth() (the user, on 7.39: the morph's K2 LFO «hace un poco de
ruido, suena como aliasing o ruido blanco», only on the oscillators -> «Smoother steps»): the oscillator rows written every frame."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import morphz
    morphz.use_smooth()
    import build_a7_39 as A39
    src = Path(A39.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.39"') == 2, "A7.39 marker strings"
    src = src.replace('"A7.39"', '"A7.40"')
    sys.argv = [A39.__file__] + sys.argv[1:]
    exec(compile(src, A39.__file__, "exec"), {"__name__": "__main__", "__file__": A39.__file__})
