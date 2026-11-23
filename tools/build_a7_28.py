"""Circuit Tracks 4486 - Alpha 7.28 (marker "A7.28") = Alpha 7.27 + tools/novasec.py (Synth 1 / 2's alt page: pads 1-8 = section pages of the Nova
parameters, like the own synth's page row; macro assign on pad 25, the knob sequencer on pad 32) + icache.use_bkpon() (its state in the backup SRAM)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz, icache
    icache.use_bkpon()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "novasec" not in report:
            import novasec
            _add(img, report, "novasec", novasec)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_27 as A27
    src = Path(A27.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.27"') == 2, "A7.27 marker lines"
    src = src.replace('"A7.27"', '"A7.28"')
    sys.argv = [A27.__file__] + sys.argv[1:]
    exec(compile(src, A27.__file__, "exec"), {"__name__": "__main__", "__file__": A27.__file__})
