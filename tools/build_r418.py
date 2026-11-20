"""Circuit Tracks 4486 - RC4.18 (marker "R418") = RC4.17 + packio.use_delled() (a fix; the user, 2026-11-20: «When I delete a pack, I want
that pack's led to turn off. Right now, it won't signal the deletion until reboot»): a deleted pack's pad goes dark at once in the packs view."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import packio
    _f2 = packio.use_fix2
    def use_fix2(*a, **k):
        r = _f2(*a, **k); packio.use_delled(); return r
    packio.use_fix2 = use_fix2
    import build_r417 as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('"R417"', '"R418"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
