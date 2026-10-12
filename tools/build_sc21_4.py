"""Circuit Tracks 4486 — SC21.4 = SC21.3 + low-pass / high-pass filter types of 12 and 24 dB in the VCF list (Shift + K5).

Filter types (Shift + K5, one step per turn, wrapping): 0 DJ (the bipolar LP / HP of K5), 1 low-pass 12 dB, 2 high-pass 12 dB, 3 band-pass, 4 notch, 5 low-pass 24 dB, 6 high-pass 24 dB;
with the types 1-6 K5 is the cutoff.  The 24 dB filters are the same state-variable filter run twice (second stage with its own state).  Everything else is SC21.3.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc21_3 as b213  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.SLOPES = True
vcf21.FTYPE_N = 7
vcf21.SIG_VAL = 0xA8                  # another signature: the saved filter types of SC21.1-SC21.3 numbered the types differently

NAME = "SC21.4"
b182 = b213.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b213.extra)
