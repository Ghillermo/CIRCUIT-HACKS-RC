"""Circuit Tracks 4486 - SC49.4 = SC49.3 without two features (the user, 2026-10-29: «Vinyl leftovers», «Drum comb filter mode»), for the drums'
extra lane's phase 2: masterfx_dsp.use_novinyl (the Vinyl's DSP routine, dropped in SC39.7, still ran and its off path zeroed Digitise's envelope
start: the K4 envelope works again), drums2_dsp / persist19 use_nocomb (the drums' comb filter mode out; mode 3 = the tilt EQ)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_3 as B  # noqa: E402
import masterfx_dsp  # noqa: E402
import drums2_dsp  # noqa: E402
import persist19  # noqa: E402
masterfx_dsp.use_novinyl()                           # the Vinyl's routine and its call
drums2_dsp.use_nocomb()                              # the comb filter mode (DSP)
persist19.use_nocomb()                               # Shift + K5 skips it
import linein3  # noqa: E402

NAME = "SC49.4"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
