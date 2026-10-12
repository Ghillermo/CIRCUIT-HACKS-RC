"""Circuit Tracks 4486 — SC38.9 = SC38.8 + srcview.use_split() (the user, 2026-10-11: «pulsar synth1 y synth2 a la vez abre una vista de pads para tocar
donde la fila superior es synth 1 y la inferior synth 2»): Synth 1 + Synth 2 pressed together = a split keyboard, pads 1-16 play Synth 1 and pads
17-32 Synth 2, each through its own Note view (scale, octave, velocity)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_8 as B  # noqa: E402  (configures everything as SC38.8)
import srcview  # noqa: E402
import linein3  # noqa: E402
srcview.use_split()

NAME = "SC38.9"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
