"""Circuit Tracks 4486 - S714D4 (diagnostic, marker "S714D4") = S714D3 + tools/dwtwatch.py in value mode: a hardware watchpoint that fires only on a
write of 0 to 0x2004FAC0 (patmut's LR slot, found 0 in the stress run's crash: UsageFault at PC 0); the black box keeps the writer's PC / LR."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import dwtwatch
    dwtwatch.use_value(0x2004FAC0, 0)
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "dwtwatch" not in report:
            _add(img, report, "dwtwatch", dwtwatch)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_s714d3 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S714D3"') == 2, "S714D3 marker lines"
    src = src.replace('"S714D3"', '"S714D4"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
