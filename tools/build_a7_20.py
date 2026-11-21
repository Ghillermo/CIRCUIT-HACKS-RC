"""Circuit Tracks 4486 - Alpha 7.20 (marker "A7.20") = Alpha 7.19 with more flash room, nothing new in use (the user: «Keep going»): the black
box's four fault stubs share one body (blackbox.use_vecshare), the side-chain sources' four entries one body (scpat.use_srcshare), the FM map's
colour chain a table (fmmap.use_famtab)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import blackbox
    import scpat
    import fmmap
    blackbox.use_vecshare()
    scpat.use_srcshare()
    fmmap.use_famtab()
    import build_a7_19 as A19
    src = Path(A19.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.19"') == 2, "A7.19 marker lines"
    src = src.replace('"A7.19"', '"A7.20"')
    sys.argv = [A19.__file__] + sys.argv[1:]
    exec(compile(src, A19.__file__, "exec"), {"__name__": "__main__", "__file__": A19.__file__})
