"""Circuit Tracks 4486 - RC4.22S (marker "R422S") = RC4.21S + build_sc17.use_spfix() (a fix: every jump of the song pointer (phrase loop, held
step) lost a clock: the stock's set-position routine marks the engine repositioned and the next clock replayed the position instead of
ticking; the start step played late and the clock fell behind; the step after the end flashed for one clock)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import patchain, build_sc17
    patchain.use_rangefix()                            # (RC4.21S)
    build_sc17.use_spfix()
    import build_r420s as R
    src = Path(R.__file__).read_text(encoding="utf-8").replace('"R420S"', '"R422S"')
    sys.argv = [R.__file__] + sys.argv[1:]
    exec(compile(src, R.__file__, "exec"), {"__name__": "__main__", "__file__": R.__file__})
