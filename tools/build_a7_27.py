"""Circuit Tracks 4486 - Alpha 7.27 (marker "A7.27") = Alpha 7.26 + build_sc17.use_spfix() (a fix: the song pointer's loop and jumps lost a clock
each time, the start step played late, the clock fell behind; the step after the end flashed for one clock)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import build_sc17
    build_sc17.use_spfix()
    import build_a7_26 as A26
    src = Path(A26.__file__).read_text(encoding="utf-8")
    assert src.count('"A7.26"') == 2, "A7.26 marker lines"
    src = src.replace('"A7.26"', '"A7.27"')
    sys.argv = [A26.__file__] + sys.argv[1:]
    exec(compile(src, A26.__file__, "exec"), {"__name__": "__main__", "__file__": A26.__file__})
