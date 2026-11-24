"""Circuit Tracks 4486 - Alpha 7.48 (marker "A7.48") = Alpha 7.47 + tools/gmgrid.py (the user, 2026-11-24: «A»): the global macro view's page-2
grid saved with the project (rows 1-3 in MIDI 1's pattern 8 settings bytes 4..6, row 4 in MIDI 2's pattern 8 settings byte 6)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "gmgrid" not in report:
            import gmgrid
            _add(img, report, "gmgrid", gmgrid, gap=3)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_47 as A47
    src = Path(A47.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.47"') == 2, "A7.47 marker strings"
    src = src.replace('"A7.47"', '"A7.48"')
    sys.argv = [A47.__file__] + sys.argv[1:]
    exec(compile(src, A47.__file__, "exec"), {"__name__": "__main__", "__file__": A47.__file__})
