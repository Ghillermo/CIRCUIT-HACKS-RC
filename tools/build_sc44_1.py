"""Circuit Tracks 4486 - SC44.1 = SC44 + sampler_dsp.use_prefilter(): the captured sample of Master FX before the master filter (its capture and its
playback: the filter acts on the sample that plays; the capture records the mix before the filter) (the user, 2026-10-17: «pon el master sampler
detras del filtro» · «Todo antes del filtro»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44 as B  # noqa: E402
import sampler_dsp  # noqa: E402
sampler_dsp.use_prefilter()
import linein3  # noqa: E402

NAME = "SC44.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
