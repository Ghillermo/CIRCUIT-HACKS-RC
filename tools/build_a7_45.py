"""Circuit Tracks 4486 - Alpha 7.45 (marker "A7.45") = Alpha 7.43 + tools/mixsolo5.py (= 7.44 with flip on top of a solo) (the user, 2026-11-24, the roadmap: «one solo mode on the
Mixer's pad 16; flip becomes a toggle on pad 15»): pad 16 tapped = solo armed, track taps put tracks in / out of the group, pad 16 again ends it;
pad 16 held + tracks = the group anew; pad 15 = flip on / off (a held track flips muted <-> sounding while held)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "mixsolo5" not in report:
            import mixsolo5
            _add(img, report, "mixsolo5", mixsolo5)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_43 as A43
    src = Path(A43.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.43"') == 2, "A7.43 marker strings"
    src = src.replace('"A7.43"', '"A7.45"')
    sys.argv = [A43.__file__] + sys.argv[1:]
    exec(compile(src, A43.__file__, "exec"), {"__name__": "__main__", "__file__": A43.__file__})
