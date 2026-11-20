"""Circuit Tracks 4486 - Alpha 7.14 (marker "A7.14") = Alpha 7.13 + tools/cc27fix.py (a fix: CC 27 on the project channel, the master group's 13th
parameter, crashed the stock firmware and every build; a Circuit Rhythm sends it)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import cc27fix
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "cc27fix" not in report:
            cc27fix.patch(img, report)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_13 as A13
    src = Path(A13.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.13"') == 2, "A7.13 marker lines"
    src = src.replace('"A7.13"', '"A7.14"')
    sys.argv = [A13.__file__] + sys.argv[1:]
    exec(compile(src, A13.__file__, "exec"), {"__name__": "__main__", "__file__": A13.__file__})
