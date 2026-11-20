"""Circuit Tracks 4486 - Alpha 7.12 (marker "A7.12") = Alpha 7.11 + tools/packsave.py (the user, 2026-11-20: «saving the current pack to a new slot
with save->target pad, just like stock Rhythm» -> «2 and 3 are alright. do it»; and «add to next»: no false violet Save from the black box during
a pack copy or delete): in the packs view, Save then an empty pack pad = the loaded pack copied there with the loaded project's unsaved changes,
then the new pack loaded.  + packio.use_pqexp() (a fix: «pads flash again after a minute»).  packsave goes into the dspz gap just before outline (which must stay the build's last module)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "packsave" not in report:
            import packsave
            _add(img, report, "packsave", packsave)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import packio
    _pk2 = packio.use_pkled2
    def use_pkled2(*a, **k):
        r = _pk2(*a, **k); packio.use_pqexp(); return r
    packio.use_pkled2 = use_pkled2                      # (a fix: the delete question cleared when stale, see packio.use_pqexp)
    import build_a7_11 as A11
    src = Path(A11.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.11"') == 2, "A7.11 marker lines"
    src = src.replace('"A7.11"', '"A7.12"')
    sys.argv = [A11.__file__] + sys.argv[1:]
    exec(compile(src, A11.__file__, "exec"), {"__name__": "__main__", "__file__": A11.__file__})
