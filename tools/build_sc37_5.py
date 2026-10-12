"""Circuit Tracks 4486 — SC37.5 = SC37.4 + granular_dsp.use_overload() (the user, 2026-10-10: the overload heard in the SC35DB test as a safe effect):
K4 of the Glitch above the middle = a simulated DSP overload (late blocks played again / caught up = clicks at the normal pitch, from K4 = 96 also
a brake = lower and slower), K4 below the middle = the chaos as before; packio.use_pkled(): the Clear LED in the packs view (SC37.4 on the device:
it never lit while deleting a pack) dim white, blinking red while a delete is armed or asked.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc37_4 as B4  # noqa: E402  (configures everything as SC37.4)
import granular_dsp  # noqa: E402
import packio  # noqa: E402
import linein3  # noqa: E402
granular_dsp.use_overload()
packio.use_pkled()

NAME = "SC37.5"
extra = B4.extra


if __name__ == "__main__":
    b5 = B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
