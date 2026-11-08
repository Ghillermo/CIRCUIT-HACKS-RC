"""Circuit Tracks 4486 - RC4.10S (marker "R410S") = RC4.09S without packio's voice-mode colouring of the synth Preset view (fix; the user,
2026-11-08: the init patch still loaded at random on RC4.09 / Beta 5.37 and the colours flickered; S552D, without the colouring: «patches dont
seem to go back to init»; «on RC, just remove the color and use stock magenta»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import packio  # noqa: E402
import build_r409s as B  # noqa: E402
import linein3  # noqa: E402

packio.PMODE = False                    # the voice-mode colouring removed (the stock's colours)
packio.PM3 = False
NAME = "R410S"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
