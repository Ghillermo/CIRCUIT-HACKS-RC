"""Circuit Tracks 4486 - RC0.8 = RC0.7 + one fix (vcf21.use_sdknobfix()): the pitch knobs of the step-drummer keep their value (since SC36.2 every knob event wrote only its own delta: the knobs did not move).  Marker "RC0.8"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_rc0_7 as B  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
vcf21.use_sdknobfix()

NAME = "RC0.8"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
