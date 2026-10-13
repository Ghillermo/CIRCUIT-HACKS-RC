"""Circuit Tracks 4486 — RC0.6 = RC0.5 + two fixes (the user, 2026-10-14: «fixes a RC»): build_sc17.use_t0fix() (the LFO of the Auto-Filter and of the Phaser
starts when the effect comes on; before, only when the Gater came on with it) and the dim white of the Clear pads = 0x02 (0x03 pulses on the device).
Marker "RC0.6"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_5 as B  # noqa: E402  (configures everything as RC0.5)
import build_sc17 as S17  # noqa: E402
import linein3  # noqa: E402
S17.use_t0fix()
S17.CLR_DIM = 0x02
import packio as PK  # noqa: E402
PK.CLR_DIM = 0x02

NAME = "RC0.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
