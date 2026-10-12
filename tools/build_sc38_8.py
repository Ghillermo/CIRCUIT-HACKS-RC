"""Circuit Tracks 4486 — SC38.8 = SC38.7 + packio.use_pmode() (the user, 2026-10-11: «en la vista del selector de patch de synth stock se muestra el pad
en color azul oscuro si el patch es mono, purple si es glide e inalterado si es poly»): the synth Preset view colours each patch by its voice mode;
+ build_sc10.use_advleds() (the user, 2026-10-11: «dos pads se encienden durante el reinicio en modo setup avanzado»): pads 22 / 23 left to the stock
in the Advanced Setup view."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_7 as B  # noqa: E402  (configures everything as SC38.7)
import packio  # noqa: E402
import build_sc10  # noqa: E402
import linein3  # noqa: E402
packio.use_pmode()
build_sc10.use_advleds()

NAME = "SC38.8"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
