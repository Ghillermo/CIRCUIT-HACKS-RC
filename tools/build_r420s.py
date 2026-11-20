"""Circuit Tracks 4486 - RC4.20S (marker "R420S") = RC4.19S + tools/cc27fix.py (a fix: CC 27 on the project channel, the master group's 13th
parameter, crashed the stock firmware and every build; a Circuit Rhythm sends it)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dbtoggle
    import cc27fix
    _ap = dbtoggle.append
    def append(img, report):
        r = _ap(img, report); cc27fix.patch(img, report); return r
    dbtoggle.append = append
    import build_r419s as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('"R419S"', '"R420S"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
