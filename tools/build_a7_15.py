"""Circuit Tracks 4486 - Alpha 7.15 (marker "A7.15") = Alpha 7.14 + blackbox.use_safeclear() (a fix: clearing the black box from the app could
restart the device: it zeroed its LED head's live LR) + tools/bbwait.py (a fix: no false «lock-up» / violet Save while the panel waits for card
work: sample swaps, patch saves, project copies), both found by the in-unit stress runs (S714D2-S714D6)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import blackbox
    blackbox.use_safeclear()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "bbwait" not in report:
            import bbwait
            _add(img, report, "bbwait", bbwait)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_14 as A14
    src = Path(A14.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.14"') == 2, "A7.14 marker lines"
    src = src.replace('"A7.14"', '"A7.15"')
    sys.argv = [A14.__file__] + sys.argv[1:]
    exec(compile(src, A14.__file__, "exec"), {"__name__": "__main__", "__file__": A14.__file__})
