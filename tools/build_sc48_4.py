"""Circuit Tracks 4486 - SC48.4 = SC48.3 + new features (the user, 2026-10-28; the beta only): latched notes bright cyan while Shift is held
(arpx.use_latchcyan: «make hold notes bright cyan on shift layout», «latched notes», «only when shift held»); the chord screen's chords rebuilt
at once when its type / inversion / voicing changes, the arpeggiator following (chords.use_live: «make chords (and arpeggiator) in chord mode
change immediately instead of waiting for next press»); Shift + a root latches its whole chord (chords.use_slatch, latchclr.use_chords: «make
latch work on chord mode (it latches all the notes in the selected chord)»); Shift + a step in the Note view writes the track's latched notes
into that step (latchstep: «if shift +step in note view is available, current latched notes are added into selected step»); the
arpeggiator modifiers' octave spread (Shift + pads 1-4 of Pattern Settings) sand (arp.use_sand: «make pads 1-4 a different color (suggestion:
sand)»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arpx  # noqa: E402
arpx.use_latchcyan()                                # Shift: the latched notes' keys bright cyan (the others keep their colours)
import chords  # noqa: E402
chords.use_live()                                   # rows 1-2 of the chord screen rebuild the chords held / latched at once
chords.use_slatch()                                 # Shift + a root = its chord latched
import arp  # noqa: E402
arp.use_sand()                                      # the arpeggiator modifiers: the octave spread (pads 1-4) sand
import latchclr  # noqa: E402
latchclr.use_chords()                               # Clear + the track's button lets go of those chords too
import build_sc48_3 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC48.4"


def extra(img, report):
    import hole
    import latchstep
    B.extra(img, report)
    hole.add(img, report, "latchstep", latchstep)        # Shift + a step in the Note view: the latched notes into it
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
