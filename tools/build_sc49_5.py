"""Circuit Tracks 4486 - SC49.5 = SC49.4 + tools/slock.py (the user, 2026-10-29): the drums' extra lane, phase 2: per drum, the lane or the
state locks (Record held + 1-16/17-32): a step carries a state of the 14 drum values without a lane (4 bits each, a pool of 80 in bytes nothing
else uses) or sits inside a ramp between two states (played per micro step); recording keeps the start, the stops and the turns of a sweep; the
drum's Velocity view with Shift (or Velocity pressed again there) = its automation view, where holding a step and tapping another draws a ramp.
For the room: recinst.use_fold (its snapshot's unrolled lane loops folded); slock's helpers in the hole, the rest at the image's end."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc49_4 as B  # noqa: E402
import recinst  # noqa: E402
recinst.use_fold()                                   # its snapshot's lane loops as loops: room in the hole
import slock  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC49.5"


def extra(img, report):
    B.extra(img, report)
    import build_sc41_5
    hole.add(img, report, "slock", slock)                        # part a: the tables and the pool's helpers
    build_sc41_5.add(img, report, "slockb", slock.PartB)        # part b at the image's end: the rest and the hooks
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
