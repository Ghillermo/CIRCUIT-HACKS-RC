"""Circuit Tracks 4486 - S725D (diagnostic, marker "S725D") = Alpha 7.25 + tools/usbtrap.py (the USB drive's leftover code filled with UDF:
any execution there freezes the black box with its PC) + icache.use_bkp() (the backup SRAM probed at reset, its header and pattern at
0x40024000) + blackbox.use_memrd() (memory reads over USB) + tools/sxpanel.py (panel gestures over USB, for the stress runs)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz, blackbox, icache
    blackbox.use_memrd()
    icache.use_bkp()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "sxpanel" not in report:
            import sxpanel, usbtrap
            _add(img, report, "sxpanel", sxpanel)
            usbtrap.install(img, report)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_25 as A25
    src = Path(A25.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.25"') == 2, "A7.25 marker lines"
    src = src.replace('"A7.25"', '"S725D"')
    sys.argv = [A25.__file__] + sys.argv[1:]
    exec(compile(src, A25.__file__, "exec"), {"__name__": "__main__", "__file__": A25.__file__})
