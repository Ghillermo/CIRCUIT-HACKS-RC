"""Circuit Tracks 4486 - SC46.9 = SC46.8 + recinst.use_sig() + fmeng.use_sig2() (the user, 2026-10-26): two RAM blocks that the power-up pattern
or an older build left behind: Record held + step (recinst) took every step pad of MIDI 1 / 2 for a snapshot until Record was pressed (manual
note input dead), and the FM's block of a version-1 beta was read as version 2's (attack 0 = percussive, the shortest decay: clicks, short
notes) until the power was cut."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_8 as B  # noqa: E402
import recinst  # noqa: E402
import fmeng  # noqa: E402
recinst.use_sig()
fmeng.use_sig2()
import linein3  # noqa: E402

NAME = "SC46.9"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
