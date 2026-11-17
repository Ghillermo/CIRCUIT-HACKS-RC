"""Circuit Tracks 4486 - RC4.13 (marker "R413") = RC4.12 + arp.use_tmfix() (a fix; the user, 2026-11-14, on Beta 5.61: «if I press play it plays for a fraction of a second and hangs»): use_timed's armed arpeggio notes played by the main loop right after it gives the DSP service's lock back, not inside it (the note's sound path takes that lock again: the unit hung)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arp  # noqa: E402
import build_r412 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "R413"
B = S.B
arp.use_tmfix()                                           # (the chain has set use_timed by now)
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
