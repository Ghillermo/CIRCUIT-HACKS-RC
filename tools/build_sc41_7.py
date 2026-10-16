"""Circuit Tracks 4486 - SC41.7 = SC41.6 + K3 of the drums split (the user, 2026-10-15): left = the stock decay, right past its maximum = an amp attack, the
middle neutral; Shift + K3: left = the start point, right = a cut from the end, the middle the whole sample (persist19 / drums2_dsp / nrpn28 use_k3split)
+ playmode.use_clrmod(): Clear + pad 25 of Pattern Settings = the pattern's random-mutate and dynamics to 0."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc41_6 as B  # noqa: E402
import linein3  # noqa: E402
import drums2_dsp  # noqa: E402
import nrpn28  # noqa: E402
import persist19  # noqa: E402
import playmode  # noqa: E402
drums2_dsp.use_k3split()
persist19.use_k3split()
nrpn28.use_k3split()
playmode.use_clrmod()

NAME = "SC41.7"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
