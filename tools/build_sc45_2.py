"""Circuit Tracks 4486 - SC45.2 = SC45.1 + patchain.use_iterled() (the user, 2026-10-20, on the Circuit Rhythm port: «during scene repeat, i want
a led to point the current iteration inside shift view», «port this feature back to tracks»): in the Mixer view with Shift held, while a
scene with 2 repeats or more plays, the pad of the repeat now playing is white (pad 9 = the first time); on the last one the green pad blinks
white / green."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc45_1 as B  # noqa: E402
import patchain  # noqa: E402
patchain.use_iterled()
import linein3  # noqa: E402

NAME = "SC45.2"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
