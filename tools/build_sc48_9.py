"""Circuit Tracks 4486 - SC48.9 = SC48.8 + snapall (the user, 2026-10-28: «how do we save all changed parameters into automation step?», «is it
the same for stock synt/drums?» -> «yes»; «mixer and fx are already stored in scenes, keep them, don't add or subtract them»): Record held + a step
= the snapshot on Synth 1 / 2 (the macros that differ from the loaded patch) and the drums (pitch, decay, distortion, EQ that differ from their
defaults), as MIDI 1 / 2's own synth already had (recinst).  At the end of the image (the hole is full)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_8 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC48.9"


def extra(img, report):
    import hole
    import snapall
    import build_sc41_5
    B.extra(img, report)
    build_sc41_5.add(img, report, "snapall", snapall)    # Record held + step on Synth 1 / 2 and the drums
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
