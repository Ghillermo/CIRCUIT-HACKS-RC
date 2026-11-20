"""Circuit Tracks 4486 - Alpha 7.11 (marker "A7.11") = Alpha 7.10 + packio.use_delled() (a fix; the user, 2026-11-20: «When I delete a pack, I want
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
    import build_a7_10 as A10
    src = Path(A10.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.10"') == 2, "A7.10 marker lines"
    src = src.replace('"A7.10"', '"A7.11"')
    sys.argv = [A10.__file__] + sys.argv[1:]
    exec(compile(src, A10.__file__, "exec"), {"__name__": "__main__", "__file__": A10.__file__})
