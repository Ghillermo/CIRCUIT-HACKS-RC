"""Circuit Tracks 4486 - SC50.1 = SC50 + mutate39.use_mut3 (the user, 2026-11-01: pads 21 / 22 of the random-mutate = octave up, low / high; 23 / 24 = both, low / high) + fxres.use_v2
(the master filter's resonance shown on Octave with Shift in the FX view, as the stock's Octave shows the octave)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc50 as B  # noqa: E402
import mutate39  # noqa: E402
mutate39.use_mut3()
import fxres  # noqa: E402
fxres.use_v2()
import linein3  # noqa: E402

NAME = "SC50.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
