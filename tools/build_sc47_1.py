"""Circuit Tracks 4486 - SC47.1 = SC47 + granular_dsp.use_stripgain(): the sides of the stereo sample mode and of the granular follow the strip's own
gains (the user, 2026-10-26, on the device: «sigue mezclando los dos samples a los dos canales por igual»; S469D / S469D2: the sides reached the mix
~4.5 x weaker than the mid: S_COEF had been measured with the stock mixer's level ramp at 22 % of its value)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47 as B  # noqa: E402
import granular_dsp  # noqa: E402
granular_dsp.use_stripgain()
import linein3  # noqa: E402

NAME = "SC47.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
