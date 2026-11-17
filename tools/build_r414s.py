"""Circuit Tracks 4486 - RC4.14S (marker "R414S") = RC4.13S + the RC fixes of the 2026-11-14 bug hunt (tools/fixes563.rc): the armed arpeggio notes timed
with the external clock's tempo when slaved (ARP-1) and a kept capture's STATE sent again after a restart that kept the RAM (CK-1)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r413s as S  # noqa: E402
import fixes563  # noqa: E402
import linein3  # noqa: E402

NAME = "R414S"
B = S.B
fixes563.rc()                                             # (before the build: use_tmext wraps cibpm's install)


def extra(img, report):
    S.extra(img, report)
    fixes563.extra_rc(img, report)                        # the tempo stub (the hole), c_artm's site re-pointed


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
