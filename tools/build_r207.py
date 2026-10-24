"""Circuit Tracks 4486 - RC2.07 (files and marker R207) = RC2.06 + a fix (the rule: every fix to the RC): the fixed length of step entry (stepgate.use_v4): the Micro Step view redrawn by the stock after the selector (its LEDs were left as the
selector had drawn them), and the length set as each note is added (all of a chord's notes, whatever pad is let go first)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_r206 as B  # noqa: E402
import stepgate  # noqa: E402
stepgate.use_v4()
import linein3  # noqa: E402

NAME = "R207"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
