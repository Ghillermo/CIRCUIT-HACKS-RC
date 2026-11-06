"""Circuit Tracks 4486 - SC52.3 = SC52.2 + wtui.use_v3() (the user, 2026-11-05, on the device: pad 27 sand with the wavetable, the lists
from the engine row, a tap on a list sounds the tonic, K7 picks the frame a sample / a Shift + Nova tap replaces)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_2 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.3"
B = S.B
extra = S.extra
import wtui  # noqa: E402
wtui.use_v3()
import build_sc51_1  # noqa: E402
build_sc51_1.LC_GAP = 1                     # loopcarry into the second dspz gap: wtui grows


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
