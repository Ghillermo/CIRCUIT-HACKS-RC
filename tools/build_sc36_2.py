"""Circuit Tracks 4486 — SC36.2 = SC36.1 + vcf21.use_fxseq3() (the user, 2026-10-09, on the device: SC36.1's FX sequencer knob only went between nothing and pad 31):
a knob turn sends many events, so the pair now keeps a position 0..96 (16 knob units per value) and plays / shows the nearest of 0..6 (0 = nothing, 1..6 = pads 26..31).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_1 as B1  # noqa: E402  (configures everything as SC36.1)
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_fxseq3()

NAME = "SC36.2"
extra = B1.extra


if __name__ == "__main__":
    b5 = B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
