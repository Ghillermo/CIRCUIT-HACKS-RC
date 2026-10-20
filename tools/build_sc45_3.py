"""Circuit Tracks 4486 - SC45.3 = SC45.2 + two fixes (smhold, recfix: also in RC2.04) + two changes of the arpeggiator (the user, 2026-10-20):
  * smhold (fix): in the own engine's sample picker a sample pad held and then a step pad = that step's flip (only step-then-sample did it);
  * recfix (fix): a note held longer than 16 steps while recording (the stock cuts it at 16) goes on, tied, 16 steps later: an arpeggiated chord
    held past step 16 keeps arpeggiating, a long note keeps sounding (Synth 1 / 2, MIDI 1 / 2);
  * arp.use_pressord(): the arpeggio in the order the notes were pressed; a note let go leaves its place empty (skipped) and the next note takes
    the lowest empty place; the orders walk the places;
  * arp.use_mutarp(): a step's chord with a random-mutate level mutates its arpeggio's notes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arp  # noqa: E402
import build_sc45_2 as B  # noqa: E402
arp.use_pressord()
arp.use_mutarp()
import smhold  # noqa: E402
import recfix  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC45.3"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "smhold", smhold)
    hole.add(img, report, "recfix", recfix)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
