"""Circuit Tracks 4486 - S717D (diagnostic, marker "S717D") = Alpha 7.17 + blackbox.use_memrd() (memory reads over USB) + tools/sxpanel.py
(panel gestures over SysEx), without tools/fxstep.py (the Master FX step sequencer: room for the two; the test does not use it): the global
macro view's rows driven and read on the device (tools/gmview_dev.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import blackbox
    blackbox.use_memrd()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "fxstep":
            return {}
        if name == "outline" and "sxpanel" not in report:
            import sxpanel
            _add(img, report, "sxpanel", sxpanel)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_17 as A17
    src = Path(A17.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.17"') == 2, "A7.17 marker lines"
    src = src.replace('"A7.17"', '"S717D"')
    sys.argv = [A17.__file__] + sys.argv[1:]
    exec(compile(src, A17.__file__, "exec"), {"__name__": "__main__", "__file__": A17.__file__})
