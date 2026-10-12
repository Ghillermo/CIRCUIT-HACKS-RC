"""Circuit Tracks 4486 — RC0.5S = RC0.4S + sampler_dsp.PRE (the user, 2026-10-12: the Master FX effects did not process the sample that plays): the captured
sample is played, and the capture recorded, at the start of the Master FX chain: the effects process the sample; the capture no longer records them.
Marker "RC0.5S"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_4s as B  # noqa: E402  (configures everything as RC0.4S)
import sampler_dsp  # noqa: E402
import linein3  # noqa: E402
sampler_dsp.PRE = True

NAME = "RC0.5S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
