"""Circuit Tracks 4486 - SC54 = SC53 + the patch morph of Synth 1 / 2 and of the own synth of MIDI 1 / 2 (tools/morphz.py in the hole; the user,
2026-11-07: patches held + Duplicate in the Preset view = the morph view: K1 the position in the chain, LFO / random / envelope on the others, pads 1 / 8
the envelope, pad 32 out, Octave = the initial patch's place; Preset = the patches, the chain's in white, a tap loads one and goes out, a hold makes
a new chain) + tools/extstep.py (with the Setup view's Note toggle on, external notes played while a step is held go into that step, as pads do)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc53 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC54"
MORPH = "morphz1"                                        # the first build's morph (SC54.1: tools/morphz.py)
B = S.B
import fm8ui  # noqa: E402
import build_sc17  # noqa: E402
fm8ui.use_nostrt()                                       # room: the FM starters' tables nothing reads (288 B)
build_sc17.use_gentab()                                  # room: Master FX's step / straight-line tables generated into RAM (mfxgen)
import velcurve  # noqa: E402
import latchstep  # noqa: E402
velcurve.use_trimpad()                                   # room: the pad curve nothing reaches since velglob
latchstep.use_trimany()                                  # room: c_lsany nothing calls with HELDCUE


def extra(img, report):
    S.extra(img, report)
    import hole
    import extstep
    hole.add(img, report, "extstep", extstep)            # the external keyboard into a held step (the Setup view's Note toggle on)
    import importlib
    importlib.import_module(MORPH).place(img, report)    # the outermost heads of the Preset views, the buttons, the knobs, the LED task


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
