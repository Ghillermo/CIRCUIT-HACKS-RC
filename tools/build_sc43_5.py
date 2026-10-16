"""Circuit Tracks 4486 - SC43.5 = SC43.4 + tools/dpitch.py (drum pitch: K1 = a chromatic value of ours, saved with the project; Shift + K6 = the
stock Pitch, continuous and linear as the original; the stock's saved / automated / CC pitch is the continuous one; the chromatic view plays the
chromatic value) + clrtrk.use_synth() (Clear + Synth 1 / 2 = its eight macros back to the loaded patch's).

SC43.4 = SC43.3 + sdpv.use_v4() + tools/scpat.py + tools/qmute.py + persist19.use_clrbc() + tools/clrtrk.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_4 as B  # noqa: E402
import clrtrk  # noqa: E402
clrtrk.use_synth()
import dpitch  # noqa: E402
import build_sc41_5 as B5  # noqa: E402
import linein3  # noqa: E402

NAME = "SC43.5"


def extra(img, report):
    B.extra(img, report)
    B5.add(img, report, "dpitch", dpitch)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
