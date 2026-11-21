"""Circuit Tracks 4486 - Alpha 7.21 (marker "A7.21") = Alpha 7.20 + tools/msdcut.py (the user: «Cut unused stock features» -> «Easy Start
USB drive»: the stock's USB drive mode removed; the Tracks is always USB MIDI; Easy Start's Setup LED dark) and its freed 1 206 B (the disk
command handler, 0x0803B27C-0x0803B732) used for the global macro view (gmview), which leaves the end of the image."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import msdcut
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name in ("gmview", "outline") and "msdcut" not in report:
            dspz.GAP_OF["gmview"] = msdcut.install(img, report)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_20 as A20
    src = Path(A20.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.20"') == 2, "A7.20 marker lines"
    src = src.replace('"A7.20"', '"A7.21"')
    sys.argv = [A20.__file__] + sys.argv[1:]
    exec(compile(src, A20.__file__, "exec"), {"__name__": "__main__", "__file__": A20.__file__})
