"""Circuit Tracks 4486 — SC21.1 = SC21 without the tilt EQ filter type and with feedback of the FX returns.

Feedback: while the Setup sends the reverb return to strip 3 / the delay return to strip 4, the ring samples of that input (zeroed by SC10) now carry the capture of the PREVIOUS block's
return (linein3.fx_cap, taken after our VCF / FX / VCA of the voice processed it), at the level of a line input: the sends of the strip feed the FX again (vcf21_dsp.pmfb).  With the
strip's level (dry) at 0 only the feedback is heard (the direct return path of SC10 is unchanged).  The synths keep reading the returns as before.  The filter types are DJ, band-pass,
notch (the tilt EQ is gone).  Everything else is SC21.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.TILT = False
vcf21_dsp.FB = True
vcf21.FTYPE_N = 3
vcf21.SIG_VAL = 0xA7                  # another signature than SC21 (0xA6): a saved filter type 3 (tilt) must not survive
import build_sc21 as b21  # noqa: E402
import linein3  # noqa: E402

NAME = "SC21.1"
b182 = b21.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b21.extra)
