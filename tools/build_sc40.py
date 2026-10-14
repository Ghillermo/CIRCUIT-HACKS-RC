"""Circuit Tracks 4486 — SC40 = SC39.9 + build_sc17.use_t0fix() (the user, 2026-10-12: «arregla el lfo»): the LFO of the Auto-Filter and of the
Phaser starts when the effect comes on, whether or not the Gater comes on with it.  (The name: "SC39.10" would be cut to "SC39.1", an older build.)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc39_9 as B  # noqa: E402  (configures everything as SC39.9)
import build_sc17 as S17  # noqa: E402
import linein3  # noqa: E402

NAME = "SC40"
S17.use_t0fix()
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
