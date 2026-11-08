"""Circuit Tracks 4486 - SC55 = SC54.1 + vcf21_dsp.use_fmcap() (the user, 2026-11-07, from RYTHM's RD44: the own synth's FM quieter on high
notes since the polyBLEP with FM: OSC 1's effective increment held to 3 x its own for its BLEP).  firmware/sc55/PRUEBA.md."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc54_1 as S  # noqa: E402   (SC54.1: the morph's second version; build_sc54 = the first, which resets the device)
import linein3  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_fmcap()

NAME = "SC55"
B = S.B
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
