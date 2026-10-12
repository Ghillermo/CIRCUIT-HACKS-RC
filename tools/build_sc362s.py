"""Circuit Tracks 4486 — SC362S = SC361S (nothing of ours writes the SD card) + vcf21.use_fxseq3() (the FX sequencer knob of SC36.2)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2  # noqa: E402,F401  (configures everything as SC36.2)
import build_sc361s as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC362S"
extra = S.extra


if __name__ == "__main__":
    b5 = S.B36.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
