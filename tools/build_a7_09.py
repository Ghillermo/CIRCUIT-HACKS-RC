"""Circuit Tracks 4486 - Alpha 7.09 (marker "A7.09") = Alpha 7.08b + fm8ui.use_p8alg() (the user, 2026-11-19: «what does pad 8 do now? can we
move shift+7 to 8?» -> «shift 7 no longer»): on the FM page of the MIDI 1 / 2 own synth, pad 8 held = the 56 algorithms' list while held (a
tap still opens the FM page); Shift + pad 7 does nothing."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import fm8ui
    fm8ui.use_p8alg()
    import build_a7_08b as A8b
    src = Path(A8b.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.08b"') == 2, "A7.08b marker lines"
    src = src.replace('"A7.08b"', '"A7.09"')
    sys.argv = [A8b.__file__] + sys.argv[1:]
    exec(compile(src, A8b.__file__, "exec"), {"__name__": "__main__", "__file__": A8b.__file__})
