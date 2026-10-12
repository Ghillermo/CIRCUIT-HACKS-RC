"""Circuit Tracks 4486 — BETA0 = SC38.7 under the name of the first beta: RC0.4's fixes plus the new features under test (the granular stretch, the MIDI Thru
Merge / Filter modes, Clear + pad 27 = the MIDI track engine back to its defaults).  Same code as SC38.7, marker "BETA0"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc38_7 as B  # noqa: E402  (configures everything as SC38.7)
import linein3  # noqa: E402

NAME = "BETA0"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
