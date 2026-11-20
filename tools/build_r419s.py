"""Circuit Tracks 4486 - RC4.19S (marker "R419S") = RC4.18S + packio.use_pqexp() (a fix; the user, 2026-11-20: «When I press clear and don't
delete anything, pads flash for a while. Then after a minute or so, they flash again»): the packs view's delete question cleared once stale (its
8-bit age wrapped every 65.5 s: the pads blinked again and Clear then deleted the pack asked long before)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import packio
    _pk2 = packio.use_pkled2
    def use_pkled2(*a, **k):
        r = _pk2(*a, **k); packio.use_pqexp(); return r
    packio.use_pkled2 = use_pkled2
    import build_r418s as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('"R418S"', '"R419S"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
