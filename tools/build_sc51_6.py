"""Circuit Tracks 4486 - SC51.6 = SC51.5 + tools/jumpflip.py (the user, 2026-11-04: the jump sequencer's destinations in the patch flip mode of the MIDI 1 / 2
Preset view: pads 17-24 with patch flip on, a destination = step flip, the lit one again = patch flip, pad 26 = all off; the engine row no longer points)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51_5 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC51.6"
B = S.B


def extra(img, report):
    import dspz
    import jumpflip
    S.extra(img, report)
    dspz.add(img, report, "jumpflip", jumpflip)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
