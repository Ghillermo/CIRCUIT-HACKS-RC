"""Circuit Tracks 4486 - Alpha 7.25 (marker "A7.25") = Alpha 7.24 + persist19.use_fold() (flash room, nothing new in use: c_mhleds19's Clear
feedback as a loop, c_dk19's three knob -> code chains as one table)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import persist19
    persist19.use_fold()
    import build_a7_24 as A24
    src = Path(A24.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.24"') == 2, "A7.24 marker lines"
    src = src.replace('"A7.24"', '"A7.25"')
    sys.argv = [A24.__file__] + sys.argv[1:]
    exec(compile(src, A24.__file__, "exec"), {"__name__": "__main__", "__file__": A24.__file__})
