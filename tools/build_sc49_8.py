"""Circuit Tracks 4486 - SC49.8 = SC49.7 + trigled.use_flash (the user, 2026-10-30: «Trigger flash: with Shift held, each track button flashes white for
100 ms on every note that track plays, from the sequence, pads, arpeggio or MIDI») + savedefer.use_toggle (the delayed save = Advanced Setup's pad 22,
the stock's save by default)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigled  # noqa: E402
trigled.use_flash()
import savedefer  # noqa: E402
savedefer.use_toggle()
import build_sc49_7 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC49.8"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
