"""Circuit Tracks 4486 - S714D (diagnostic, marker "S714D") = Alpha 7.14 + tools/patscan.py (the pattern scan that freezes the black box on an
impossible value, with the last 12 MIDI messages in) + blackbox.use_memrd() (live memory reads over USB: tools/bbread.py --mem)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import blackbox
    blackbox.use_memrd()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "patscan" not in report:
            import patscan
            _add(img, report, "patscan", patscan)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_14 as A14
    src = Path(A14.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.14"') == 2, "A7.14 marker lines"
    src = src.replace('"A7.14"', '"S714D"')
    sys.argv = [A14.__file__] + sys.argv[1:]
    exec(compile(src, A14.__file__, "exec"), {"__name__": "__main__", "__file__": A14.__file__})
