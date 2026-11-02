"""Circuit Tracks 4486 - SC50.4 = SC50.3 + the chord screen with the arpeggiator on (the user, 2026-11-02): arpmute (the arpeggio goes on with the track muted in the Mixer),
chords.use_shared (notes two chords share are not lost when one is let go), chords.use_inverse (pad 16: the latch gone, the chord mirrored downwards) + cibpm (the count-in at an
external clock's tempo) + rollers / drumarp use_bpm0 (stopped, they took p1, not the tempo) + clickflash (with the click at 0, Clear flashes on each click)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chords  # noqa: E402
chords.use_live(); chords.use_slatch()                   # (the chain sets them too, later: they only set flags)
import chshare  # noqa: E402
chords.use_shared(chshare.AT)
chords.use_inverse()
import rollers  # noqa: E402
rollers.use_bpm0()
import drumarp  # noqa: E402
drumarp.use_bpm0()
import build_sc50_3 as B  # noqa: E402
import centab  # noqa: E402
import arpmute  # noqa: E402
import cibpm  # noqa: E402
import clickflash  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC50.4"


def extra(img, report):
    B.extra(img, report)
    centab.add(img, report, "chshare", chshare, "semitab")
    centab.add(img, report, "arpmute", arpmute, "semitab")
    centab.add(img, report, "cibpm", cibpm, "semitab")
    centab.add(img, report, "clickflash", clickflash, "semitab")
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
