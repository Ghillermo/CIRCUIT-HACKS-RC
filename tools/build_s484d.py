"""Circuit Tracks 4486 - S484D (DIAGNOSTIC) = SC48.4 + tools/dspload.py: two live meters on the panel, to tell why FM chords with long releases
rattle (the user, 2026-10-28: «Some FM patches still produce crackling when you hold more than 5 notes»; «the main issue comes when using notes
with long releases»; «we can make a diag build if you need»): Save = how close core 0 of the DSP runs to its time (its output buffer's margin),
Duplicate = the peak of the own synth of MIDI 1 / 2 (clipping).  ARM only: the DSP program is SC48.4's.  See firmware/s484d/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_4 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "S484D"


def extra(img, report):
    import hole
    import dspload
    B.extra(img, report)
    hole.add(img, report, "dspload", dspload)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
