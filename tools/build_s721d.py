"""Circuit Tracks 4486 - S721D (diagnostic, marker "S721D") = Alpha 7.21 (the USB drive cut) + tools/stocktrap.py (the stock's unreached runs filled with UDF: any
execution there freezes the black box with its PC) + blackbox.use_memrd() (memory reads over USB) + tools/sxpanel.py (panel gestures over
USB, for the stress runs), without tools/fxstep.py (room for the two)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import blackbox
    import stocktrap
    blackbox.use_memrd()
    stocktrap.EXTRA = [(0x0803B758, 36)]                                # the end of the cut disk handler
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "fxstep":
            return {}
        if name == "outline" and "sxpanel" not in report:
            import sxpanel, stocktrap
            _add(img, report, "sxpanel", sxpanel)
            stocktrap.install(img, report)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_21 as A21
    src = Path(A21.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.21"') == 2, "A7.21 marker lines"
    src = src.replace('"A7.21"', '"S721D"')
    sys.argv = [A21.__file__] + sys.argv[1:]
    exec(compile(src, A21.__file__, "exec"), {"__name__": "__main__", "__file__": A21.__file__})
