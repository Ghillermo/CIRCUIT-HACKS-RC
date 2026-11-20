"""Circuit Tracks 4486 - S715D2 (diagnostic, marker "S715D2") = S715D + tools/dwtwatch.py on the two words of the Beta 5.63 / 5.64 corruption
(dwtwatch.use_filtered_many): 0x20043610 (Drum 4's velocity-bar listener, legit 0x0805ADA8; S715D's scene stress run found it 0x0805AD61 after
~25 min and hung) and 0x20042988 (Synth 1's Preset view listener, legit 0x0805ACC8).  A CPU write that leaves either word wrong freezes the black
box with the writer's PC / LR (vector 12)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

WATCH = [(0x20043610, 0x0805ADA8), (0x20042988, 0x0805ACC8)]

if __name__ == "__main__":
    import dspz
    import dwtwatch
    dwtwatch.use_filtered_many(WATCH)
    _add = dspz.add
    def add(img, report, name, mod, *a, **k):
        if name == "outline" and "dwtwatch" not in report:
            _add(img, report, "dwtwatch", dwtwatch)
        return _add(img, report, name, mod, *a, **k)
    dspz.add = add
    import build_s715d as S
    src = Path(S.__file__).read_text(encoding="utf-8")
    assert src.count('"S715D"') == 2, "S715D marker lines"
    src = src.replace('"S715D"', '"S715D2"')
    sys.argv = [S.__file__] + sys.argv[1:]
    exec(compile(src, S.__file__, "exec"), {"__name__": "__main__", "__file__": S.__file__})
