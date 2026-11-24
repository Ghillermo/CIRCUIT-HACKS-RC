"""Circuit Tracks 4486 - Alpha 7.41 (marker "A7.41") = Alpha 7.40 + morphz.use_lfsync() (the user: «Make the lfo behave like the other lfos
(right: free / left: synced). limit the maximum speed ~75%»): the morph's K3 (the two LFOs' rate) bipolar."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import morphz
    morphz.use_lfsync()
    import build_a7_40 as A40
    src = Path(A40.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.40"') == 2, "A7.40 marker strings"
    src = src.replace('"A7.40"', '"A7.41"')
    sys.argv = [A40.__file__] + sys.argv[1:]
    exec(compile(src, A40.__file__, "exec"), {"__name__": "__main__", "__file__": A40.__file__})
