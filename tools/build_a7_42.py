"""Circuit Tracks 4486 - Alpha 7.42 (marker "A7.42") = Alpha 7.41 + tools/m2lanes.py + novasec.use_v9() (the user: «then keep working on
macros2»; chosen: «Like the macros», «Two: start and middle»): Synth 1 / 2's eight Macros 2 knobs get automation lanes (8 KB in the ITCM, a
section on the card after the scene chains).  Part A (the hooks) in factcut's gap; part H (the helpers, the playback, the knob's calls) and part B (the LED task's card work) at the end
of the image."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import novasec
    novasec.use_v9()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "m2lanes" not in report:
            import m2lanes
            m2lanes.H.install(img, report)
            _add(img, report, "m2lanes", m2lanes, gap=3)
            m2lanes.IO.install(img, report)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_41 as A41
    src = Path(A41.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.41"') == 2, "A7.41 marker strings"
    src = src.replace('"A7.41"', '"A7.42"')
    sys.argv = [A41.__file__] + sys.argv[1:]
    exec(compile(src, A41.__file__, "exec"), {"__name__": "__main__", "__file__": A41.__file__})
