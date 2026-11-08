"""Circuit Tracks 4486 - SC54.1 = SC54 with the patch morph's second version (tools/morphz.py; the user, 2026-11-07 / 08: SC54 reset the device in the
MIDI 1 / 2 Preset view, entering needs two held patches, the synths' morph view = their alternative view, Preset twice = that view, the track's button
brings the morph view back, pad 32 leaves it as the stock draws it; the LED hooks keep nothing on the stack and draw into their own copies).  A new
name because the bootloader skips an image whose version block equals the installed one: the rebuilt SC54 never reached the device."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc54 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC54.1"
B = S.B
S.MORPH = "morphz"
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
