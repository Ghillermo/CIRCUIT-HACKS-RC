"""Circuit Tracks 4486 - Alpha 7.13 (marker "A7.13") = Alpha 7.11 + packsave.use_bbonly() + packio.use_pqexp() (the user, 2026-11-20: «Discard
the new save feature, we need the room»: Alpha 7.12 without Save + empty pack pad; its two fixes kept): no false violet Save from the black box
during a pack copy or delete, and the packs view's delete question forgotten once stale (it came back every 65.5 s)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import packio
    import packsave
    packsave.use_bbonly()
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "packsave" not in report:
            _add(img, report, "packsave", packsave)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    _pk2 = packio.use_pkled2
    def use_pkled2(*a, **k):
        r = _pk2(*a, **k); packio.use_pqexp(); return r
    packio.use_pkled2 = use_pkled2
    import build_a7_11 as A11
    src = Path(A11.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.11"') == 2, "A7.11 marker lines"
    src = src.replace('"A7.11"', '"A7.13"')
    sys.argv = [A11.__file__] + sys.argv[1:]
    exec(compile(src, A11.__file__, "exec"), {"__name__": "__main__", "__file__": A11.__file__})
