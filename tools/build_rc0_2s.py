"""Circuit Tracks 4486 — RC0.2S = RC0.1S + granular_dsp.use_overload() (the simulated DSP overload of the Glitch, K4 above the middle).  The Clear LED
of SC37.5 belongs to the pack management (packio), which the safer builds leave out.  Marker "RC0.2S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_1s as B  # noqa: E402  (configures everything as RC0.1S)
import granular_dsp  # noqa: E402
import linein3  # noqa: E402
granular_dsp.use_overload()

NAME = "RC0.2S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
