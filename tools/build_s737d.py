"""Circuit Tracks 4486 - S737D (DIAGNOSTIC, marker "S737D") = Alpha 7.37 + tools/sendcnt.py: every send of the DSP programs counted in the black
box record's spare word (0x2004F1CC).  See firmware/s737d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "sendcnt" not in report:
            import sendcnt
            _add(img, report, "sendcnt", sendcnt)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_37 as A37
    src = Path(A37.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.37"') == 2, "A7.37 marker strings"
    src = src.replace('"A7.37"', '"S737D"')
    sys.argv = [A37.__file__] + sys.argv[1:]
    exec(compile(src, A37.__file__, "exec"), {"__name__": "__main__", "__file__": A37.__file__})
