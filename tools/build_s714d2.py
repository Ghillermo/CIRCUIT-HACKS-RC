"""Circuit Tracks 4486 - S714D2 (diagnostic, marker "S714D2") = S714D + tools/sxpanel.py (panel gestures from the PC over SysEx, for
tools/panelstress_dev.py: a random in-unit stress run under patscan's watch)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "sxpanel" not in report:
            import sxpanel
            _add(img, report, "sxpanel", sxpanel)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_s714d as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S714D"') == 2, "S714D marker lines"
    src = src.replace('"S714D"', '"S714D2"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
