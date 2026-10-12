"""Circuit Tracks 4486 — SC37 = RC0 (= SC36.2) + packio.use_cross() (the user, 2026-10-10): swap samples between packs.
Duplicate + pad A copies sample A (it stays copied while you load another pack); Duplicate + pad B in another pack swaps the two files and the new B
sounds at once (loaded into free external memory of the DSP).  sampler_dsp.CLIP: the DSP clears the clip word at power-up.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2 as B2  # noqa: E402  (configures everything as SC36.2)
import packio  # noqa: E402
import linein3  # noqa: E402
packio.use_cross()

NAME = "SC37"
extra = B2.extra


if __name__ == "__main__":
    b5 = B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
