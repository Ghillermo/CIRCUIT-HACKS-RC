"""Circuit Tracks 4486 - S714D5 (diagnostic, marker "S714D5") = S714D3 + tools/dwtwatch.py in filtered mode: every write to 0x2004FAC0 (patmut's LR
slot) is checked by the DebugMonitor; patmut's own (the value 0x08067BBB, its caller's return in the black box's LED head) resumes, anything else
freezes the black box with the writer's PC / LR.  (S714D4's value watch never fired: the zero is not a CPU word write of 0.)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import dwtwatch
    dwtwatch.use_filtered(0x2004FAC0, 0x08067BBB)
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "dwtwatch" not in report:
            _add(img, report, "dwtwatch", dwtwatch)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_s714d3 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S714D3"') == 2, "S714D3 marker lines"
    src = src.replace('"S714D3"', '"S714D5"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
