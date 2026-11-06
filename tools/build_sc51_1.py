"""Circuit Tracks 4486 - SC51.1 = SC51 + loopcarry (the captured sample's latched loop survives a project / pack load; Play waits for the end of the
loop, then starts the new project and discards the loop; the user, 2026-11-03, option A)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc51 as S  # noqa: E402
import dspz  # noqa: E402
import loopcarry  # noqa: E402
import linein3  # noqa: E402

NAME = "SC51.1"
B = S.B
LC_GAP = 0                                   # SC52.3: 1 (the second dspz gap: wtui.use_v3 needs the first)


def extra(img, report):
    S.extra(img, report)
    dspz.add(img, report, "loopcarry", loopcarry, gap=LC_GAP)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
