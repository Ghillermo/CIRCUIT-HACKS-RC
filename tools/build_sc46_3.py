"""Circuit Tracks 4486 - SC46.3 = SC46.2 + the fix of RC2.08 (kbin: an external keyboard plays the own synth of MIDI 1 / 2) + gmdrum.use_v2() (K4 to
off closes the number view; with the mode off K5..K8 do nothing) + janko (the isomorphic Jankó layout, a case of the custom scale: Shift + pad 8 in
its editor) + chords (the chord screen of the expanded Note view: Shift + pad 8)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gmdrum  # noqa: E402
gmdrum.use_v2()
import build_sc46_2 as B  # noqa: E402
import kbin  # noqa: E402
import janko  # noqa: E402
import chords  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC46.3"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "kbin", kbin)
    hole.add(img, report, "janko", janko)
    hole.add(img, report, "chords", chords)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
