"""Circuit Tracks 4486 - S715D3 (diagnostic, marker "S715D3") = S715D2 + tools/stepcatch.py: S715D2's DWT watch caught the writer of the 5.63 /
5.64 corruption (the stock per-step flags write 0x0804E736 with Drum 4's play position = 240); here a play position >= 32 written by the stock
advance (0x0802CE46) or seen by that listener (0x0804EB8E) freezes the black box with the advance's live frame (track, new pattern, settings) and
the chain / mutate state, and is clamped (& 31) / skipped.  Without S715D's patscan (no room)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import dspz
    import stepcatch
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "patscan":                    # no room: patscan never fired; its scan is not needed for this question
            return {}
        if name == "outline" and "stepcatch" not in report:
            _add(img, report, "stepcatch", stepcatch)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_s715d2 as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S715D2"') == 2, "S715D2 marker lines"
    src = src.replace('"S715D2"', '"S715D3"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
