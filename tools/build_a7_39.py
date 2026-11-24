"""Circuit Tracks 4486 - Alpha 7.39 (marker "A7.39") = Alpha 7.38 + morphz.use_typefix() (fix; the user: «fix»): the Synth 1 / 2 patch morph
morphs every row of the patch again: its «packed field: left alone» test read the previous row's MIDI type, so it skipped the rows after a CC row
(3-44: the oscillators, the mixer, the filter, the amp envelope; 79-80; the macros' slot-1 destinations) and wrote the packed rows 61 / 73."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import morphz
    morphz.use_typefix()
    import build_a7_38 as A38
    src = Path(A38.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.38"') == 2, "A7.38 marker strings"
    src = src.replace('"A7.38"', '"A7.39"')
    sys.argv = [A38.__file__] + sys.argv[1:]
    exec(compile(src, A38.__file__, "exec"), {"__name__": "__main__", "__file__": A38.__file__})
