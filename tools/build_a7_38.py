"""Circuit Tracks 4486 - Alpha 7.38 (marker "A7.38") = Alpha 7.37 + tools/factcut.py (the user: «yes» to «a no-feature build that ignores the
factory-test messages and frees the 3.5 KB»): the stock's factory-test mode removed (its SysEx never matches, the DSP program send is always the
normal one), its two DSP programs' flash (0x08054F0C-0x08055CBA, 3 502 B) a new gap of dspz.add, and novasec (which never writes to the card nor
saves settings) moved into it from the end of the image.  No change in use."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import factcut
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name in ("novasec", "outline") and "factcut" not in report:
            dspz.GAP_OF["novasec"] = factcut.install(img, report)
        r = _add(img, report, name, mod, *a, **k)
        if name == "outline":                                   # the last module: the cut in place and novasec inside the freed range
            bad = factcut.check(img, report)
            assert not bad, bad
            lo, hi = (int(x, 16) for x in report["factcut"]["gap"])
            ns = report["dspz"].get("blocks", {}).get("novasec")
            assert ns and lo <= int(ns[0], 16) and int(ns[1], 16) <= hi, f"novasec is not in the freed range ({ns})"
        return r
    dspz.add = add
    import build_a7_37 as A37
    src = Path(A37.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.37"') == 2, "A7.37 marker strings"
    src = src.replace('"A7.37"', '"A7.38"')
    sys.argv = [A37.__file__] + sys.argv[1:]
    exec(compile(src, A37.__file__, "exec"), {"__name__": "__main__", "__file__": A37.__file__})
