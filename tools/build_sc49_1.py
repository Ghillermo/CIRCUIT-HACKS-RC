"""Circuit Tracks 4486 - SC49.1 = SC49 + autorel.use_v3() + tools/projinit.py (the user, 2026-10-29, on RC4 and Beta 3.45):
  * a marked step (Velocity view, Shift + step) brings its lanes back to Project init: Synth 1 / 2 = the macros of the synth's patch in the
    session record, MIDI 1 / 2 = the own synth saved with the project (projsyn; else its defaults) («the cleared automation must go to Project init,
    not current pad»);
  * Shift + a yellow step: the knobs it moves light yellow, brightness = the value («the updated leds should be yellow»);
  * Clear + step in the Velocity view = the step's knob automation erased, its notes kept («clear+pad in this view must keep the note and erase
    automation only»);
  * Shift + Preset = the voice on the screen back to Project init («shift+preset takes current voice to project init»), Preset yellow with Shift.
autorel goes to the end of the image (build_sc45.AUTOREL_END: it no longer fits the hole); projinit in the hole."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import autorel  # noqa: E402
autorel.use_v3()
import build_sc45  # noqa: E402
build_sc45.AUTOREL_END = True
import build_sc49 as B  # noqa: E402
import projinit  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC49.1"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "projinit", projinit)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
