"""Circuit Tracks 4486 - SC48.7 = SC48.6 + vcf21.use_edlock() (issue #15; the user, 2026-10-28: «CC re-assign cannot be used during voice
modes», «Instead, knobs send their assigned custom CC and NRPNs», «The re-assign view pad is off when a voice is being used», «Unavailable pads
are off (no light at all)»): with the track's own synth on, its knobs send the own synth's CC / NRPN map, so the CC editor (which edits the
stock template) is closed: pad 25 dark and a press does nothing; an editor left open when the own synth comes on is left."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_6 as B  # noqa: E402
import vcf21  # noqa: E402
vcf21.use_edlock()                                  # no CC editor while the own synth is on
vcf21.use_vellock()                                 # pad 31 only with the VA-drum
import modesel  # noqa: E402
modesel.use_vdfix()                                 # the engine row: VA-drum + pad 31 = the VA-drum
import linein3  # noqa: E402

NAME = "SC48.7"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
