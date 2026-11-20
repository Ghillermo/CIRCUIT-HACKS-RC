"""Circuit Tracks 4486 - Alpha 7.16 (marker "A7.16") = Alpha 7.15 + patchain.use_rangefix() (a fix, found on the device by S715D2 / S715D3: a
track playing outside its stock chain went to a pattern 8 that does not exist; the play step became 240 and the stock view code wrote past its
array: the Beta 5.63 / 5.64 crash) + tools/gmview.py (the global macro view: Mixer + Patterns together; knob Kn moves Kn on the tracks linked to
it, picked on pads 1-8; saved with the project)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import patchain
    patchain.use_rangefix()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "gmview" not in report:
            import gmview
            _add(img, report, "gmview", gmview)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_15 as A15
    src = Path(A15.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.15"') == 2, "A7.15 marker lines"
    src = src.replace('"A7.15"', '"A7.16"')
    sys.argv = [A15.__file__] + sys.argv[1:]
    exec(compile(src, A15.__file__, "exec"), {"__name__": "__main__", "__file__": A15.__file__})
