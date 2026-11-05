"""Circuit Tracks 4486 - SC52 = SC51.9 + the engine row on pads 17-24 of the FM operator page (fm8ui.use_rowop; the user: «restore row 3»: «Engine mode»).
SC51.9 = SC51.8 + the pitch envelope on pad 3 in FM's violet (fm8ui.use_peg3; the user: «put it on pad 3, purple (fm) color»).
SC51.8 = SC51.7 + what the user asked on Beta 5.20 in the device (2026-11-05): the FM's pad 7 / 8 lists over the step-flip
row (fm8ui.use_heads), pad 28 / the OSC 2 page off with FM (use_nodual), eight 8-operator algorithms (fm8.use_alg8), pad 7 = the 56 algorithms in
pages on Octave, pad 8 = 24 instruments in their type's colour (fm8inst.py), row 3 dark on the operator page, the patch slots in their engine's
colour and the empty ones dim white, pad 32 / Shift + pad 29 only with a voice (fm8ui.use_v2), the engine row without the FX sequencer (now pad 31
with no voice) and with the wavetable's place (modesel.use_row2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_7 as S  # noqa: E402
import fm8ui  # noqa: E402
import linein3  # noqa: E402
import modesel  # noqa: E402

NAME = "SC52"
B = S.B
modesel.use_row2()
fm8ui.use_v2()
fm8ui.use_peg3()
fm8ui.use_rowop()
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
