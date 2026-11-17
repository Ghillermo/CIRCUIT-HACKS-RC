"""Circuit Tracks 4486 - RC4.12S (marker "R412S") = RC4.11S + arp.use_timed() (a fix; the user, 2026-11-14: «cuando la velocidad del arpegiador es
x4 la velocidad del patrón base en pattern settings, el arpegiador toca en tresillos / swing»): running, an arpeggio note that falls between two micro
steps (x4 on a 1/16 pattern = every 1.5 micro steps at 24 PPQN) is armed at the micro step before it and played at its time by the main loop (about
every ms), instead of on the next micro step (2, 1, 2, 1).  + tools/capkeep.py (a fix; «fix and beta»): a latched / armed capture of Master FX's sample
goes on through a project load."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arp  # noqa: E402
import build_r411s as S  # noqa: E402
import linein3  # noqa: E402

NAME = "R412S"
B = S.B
arp.use_timed()                                           # (the chain has set RATE and the states' RAM by now)


def extra(img, report):
    S.extra(img, report)
    import capkeep
    capkeep.install(img, report)                                                    # (the end of the image)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
