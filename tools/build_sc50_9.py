"""Circuit Tracks 4486 - SC50.9 = SC50.8 + mixsolo v2 (pad 16 of the Mixer: solo latched until tapped again, or a tap alone = flip mode, where held track
pads sound alone until let go; the user, 2026-11-03), the first module placed in the flash dspz freed (dspz.add) + drumpat.use_dyn4 (the mutate's dynamics:
notes off / ghost / accent staccato / length, drums off / lo with a roller / hi; the factor 0, 1, 2, 4, 8)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc50_8 as B  # noqa: E402
import drumpat  # noqa: E402
drumpat.use_dyn4()                                   # after the chain's use_mut2 / use_roll2
import dspz  # noqa: E402
import mixsolo  # noqa: E402
import linein3  # noqa: E402

NAME = "SC50.9"


def extra(img, report):
    B.extra(img, report)                             # SC50.8: dspz last of the DSP work
    dspz.add(img, report, "mixsolo2", mixsolo.V2)    # ARM only: into the freed flash


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
