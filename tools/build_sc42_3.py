"""Circuit Tracks 4486 - SC42.3 = SC42.2 + arp.use_rate() (the arpeggiator's own resolution: Shift + pads 17-24 of Pattern Settings; the chord's
notes with their own gates) + tools/stepgate.py (step entry: the time a pad is held = the note's gate; on / off per track with pad 32 of the Micro
Step view) + countin.use_cols2() (the metronome's states in red / green / magenta / cyan) (the user, 2026-10-16)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42_2 as B  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402
import arp  # noqa: E402
import countin  # noqa: E402
import stepgate  # noqa: E402
arp.use_rate()
countin.use_cols2()

NAME = "SC42.3"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "stepgate", stepgate)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
