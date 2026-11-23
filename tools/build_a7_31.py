"""Circuit Tracks 4486 - Alpha 7.31 (marker "A7.31") = Alpha 7.30 + tools/shiftview.py (the user: «shift + mixer should enter master fx too (all alt,
press twice, views also open with shift)»): Shift + Mixer = Master FX (the stock drops Shift + Mixer)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "shiftview" not in report:
            import shiftview
            _add(img, report, "shiftview", shiftview)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_30 as A30
    src = Path(A30.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.30"') == 2, "A7.30 marker lines"
    src = src.replace('"A7.30"', '"A7.31"')
    sys.argv = [A30.__file__] + sys.argv[1:]
    exec(compile(src, A30.__file__, "exec"), {"__name__": "__main__", "__file__": A30.__file__})
