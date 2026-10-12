"""Circuit Tracks 4486 — SC23.4 = SC23.3 + the corrections asked after testing (2026-10-06):
  * CC editor v2 (`vcf21.use_edv2()`): the CC number picks the type (99 / 98 / 6 = NRPN with a 7-bit value, 38 = NRPN with a 14-bit value), a save step after the last field with the Save pad (the pad
    next to pad 25) blinking and one more Octave v saving, the Save pad saves at any time, the button of the track discards like every view button;
  * Master FX: the pad 8 is white, song pointer ranges are normalised (the earlier step is the start whatever the order of the touches) and a loop end the playhead has passed jumps to the start,
    the target of a step jump is lit, touching a latched pad 7 unlatches it;
  * drum Note view: pads 25-28 mirror the drums (25 = drum 4 ... 28 = drum 1, next to 29 = drum 1).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc23_3 as b233  # noqa: E402
import vcf21  # noqa: E402
import build_sc17 as B17  # noqa: E402
import drumnote  # noqa: E402
import linein3  # noqa: E402
vcf21.use_edv2()
B17.use_sp_norm()
B17.use_jump_led()
B17.use_jump_unstick()
B17.CLR_ON, B17.CLR_DIM = 0x01, 0x03          # pad 8: white (bright when something is latched, dim otherwise)
drumnote.MIRROR = True
b223 = b233.b223

NAME = "SC23.4"
extra = b233.extra

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
