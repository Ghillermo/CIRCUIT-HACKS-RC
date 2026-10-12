"""Circuit Tracks 4486 — SC20.2 = SC19.9 + the SC20.1 changes WITHOUT the VCF / VCA mode (no vcf20 ARM or DSP code).

For bisecting the SC20 report "the external audio inputs do not work": SC19.9 + scale on three rows, Pitch knob as a note bias in the chromatic view (Shift = cents),
Clear on the drum knobs of ours (see build_sc20_1.py) and the yellow pad 7 of Master FX.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
import build_sc08  # noqa: E402
import build_sc12  # noqa: E402
persist19.CLEAR = True
build_sc08.ROWS3 = True
build_sc12.SWAP = True
import build_sc17  # noqa: E402
import build_sc19_9 as b199  # noqa: E402
import linein3  # noqa: E402
build_sc17.SP_PLAY = True
build_sc17.JMP_ON, build_sc17.JMP_OFF = 0x2D, 0x2E

NAME = "SC20.2"
b182 = b199.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b199.b198.b197.b196.b195.b191.extra)
