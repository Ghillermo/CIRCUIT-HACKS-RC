"""Circuit Tracks 4486 - S715D (diagnostic, marker "S715D") = Alpha 7.15 + the stress-run tools of S714D6: tools/patscan.py (an impossible step
value freezes the black box), blackbox.use_memrd() (memory reads over USB), tools/sxpanel.py (panel gestures over SysEx, for panelstress_dev.py /
scenestress_dev.py) and blackbox.use_keepstall(400) (a main-loop pause > 400 ms is kept, with PC samples).  Alpha 7.15's own fixes (safeclear,
bbwait) are in, so a run also checks them on the device: card waits should no longer record a pause."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import blackbox
    blackbox.use_memrd()
    blackbox.use_keepstall(400)
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline":
            for nm in ("patscan", "sxpanel"):
                if nm not in report:
                    _add(img, report, nm, __import__(nm))
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_a7_15 as A15
    src = Path(A15.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.15"') == 2, "A7.15 marker lines"
    src = src.replace('"A7.15"', '"S715D"')
    sys.argv = [A15.__file__] + sys.argv[1:]
    exec(compile(src, A15.__file__, "exec"), {"__name__": "__main__", "__file__": A15.__file__})
