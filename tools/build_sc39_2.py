"""Circuit Tracks 4486 — SC39.2 = SC39.1 + sampler_dsp.PRE (the user, 2026-10-12: «en el trigger de sample de master fx, los efectos … no afectan al sample en
reproducción» -> «sample antes de efectos (efectos aplican a captura, no se graban)»): the captured sample is played (and the capture recorded) at the start
of the Master FX chain, so the effects process the sample that plays; the capture no longer records the effects."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_1 as B  # noqa: E402  (configures everything as SC39.1)
import sampler_dsp  # noqa: E402
import linein3  # noqa: E402
sampler_dsp.PRE = True

NAME = "SC39.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
