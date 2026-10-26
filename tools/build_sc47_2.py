"""Circuit Tracks 4486 - SC47.2 = SC47.1 + tools/arpx.py + arp.use_bpm0(): issues #13 / #14 of the public repository (the user, 2026-10-26: «user wants
arpeggiator to work with external midi input. Also, when you press a step and arpeggiator is active, the step pre-listen runs through the arp» ·
«additional feature: with shift+note (if available) the note is latched until next press of such note»): the held step's audition and an external
keyboard (Advanced Setup pad 22, off by default) through the arpeggiator's input, Shift + a key = latch; and a fix (also RC2.10): the arpeggiator's
stopped stepping at the project's BPM (p0 of 0x20011404, not p1)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_1 as B  # noqa: E402
import arp  # noqa: E402
arp.use_bpm0()
import arpx  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC47.2"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "arpx", arpx)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
