"""Circuit Tracks 4486 - SC45 = SC44.9 + tools/autorel.py + tools/modesel.py in the hole («SC44.10» would be cut to «SC44.1»):
  * autorel (the user, 2026-10-19: «En velocity view, shift+pad hace que deje de aplicarse automatización (posición de knob + init en lugar de
    posición + valor previo de automatización)»; Synth 1 / 2 and MIDI 1 / 2, the 8 lanes): Velocity view, Shift + a step pad = the step lets go of
    the automation: no lane plays there and every lane that had played goes back to the value it had before (the knob's);
  * modesel («En selector de modo sinte midi (pad 27) tras un toque, abrir vista en row 3 con opciones (mantener colores) tocar el pad 27 otra vez
    cierra la vista y recupera lista de parches»; a mode chosen leaves the row open): pad 27 of the MIDI Preset view = the seven modes on pads
    17-23."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc44_9 as B  # noqa: E402
import autorel  # noqa: E402
import modesel  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC45"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "autorel", autorel)
    hole.add(img, report, "modesel", modesel)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
