"""Circuit Tracks 4486 - SC44.6 = SC44.5 + mfbyp.use_hold() (the user, 2026-10-19: «cuando se desactiva el filtro con s25, mantener desactivado
aunque se mueva. Recuperar posición actual del filtro al togglear s25 otra vez»): while the master filter is off (FX view, Shift + pad 25) the DSP
gets the centre whatever the knob does; switching it on again gives the knob's current position."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mfbyp  # noqa: E402
mfbyp.use_hold()
import build_sc44_5 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
