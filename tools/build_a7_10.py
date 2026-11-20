"""Circuit Tracks 4486 - Alpha 7.10 (marker "A7.10") = Alpha 7.09 + tools/laneclr.py (the user, 2026-11-19: «Clear knob clears lane» -> «Clear, all
patterns»): freeing a page-4 knob slot of the MIDI 1 / 2 own synth (Duplicate + knob) clears its automation lane in the track's 8 patterns.
laneclr goes into the dspz gap just before outline (which must stay the build's last module)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "laneclr" not in report:
            import laneclr
            _add(img, report, "laneclr", laneclr)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_09 as A9
    src = Path(A9.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.09"') == 2, "A7.09 marker lines"
    src = src.replace('"A7.09"', '"A7.10"')
    sys.argv = [A9.__file__] + sys.argv[1:]
    exec(compile(src, A9.__file__, "exec"), {"__name__": "__main__", "__file__": A9.__file__})
