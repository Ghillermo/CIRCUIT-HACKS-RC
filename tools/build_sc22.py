"""Circuit Tracks 4486 — SC22 = SC21.4 + the FX types ring mod, comb and chorus in the VCF mode list (Shift + K8), the DSP program allowed to reach P:$3FFF, and the fix of the register save area.

SC21D showed on the hardware that the core-0 program RAM is 16 K words (P:$0000-$3FFF); the old limit $3800 was ours.  FX types (Shift + K8, one step per turn, wrapping): 0 soft, 1 hard, 2 fold,
3 wavefold, 4 ring mod (K8 = depth, Shift + K7 = modulator frequency), 5 comb (K8 = feedback, Shift + K7 = pitch), 6 chorus (K8 = mix, Shift + K7 = rate).  The registers of the voices are saved at
X:$38C0.. (SC21.4 saved r2 at X:$3BEA, where the return buffer pointer also lives: in the FX return path r2 came back wrong).  The envelope -> VCA (K3) and the LFO -> VCA (Shift + K3) are bipolar now (-64..63, 0 = no send, negative = inverted: an inverted envelope closes the VCA, an inverted LFO is the tremolo upside down).
Everything else is SC21.4.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import build_sc21_4 as b214  # noqa: E402
import build_sc16  # noqa: E402
import linein3  # noqa: E402
build_sc16.CODE_P_END = 0x4000
vcf21_dsp.PLIMIT = 0x4000
vcf21_dsp.FXMORE = True
vcf21_dsp.VFF = True                  # the chain is VCA -> FX -> filter
vcf21.FXTYPE_N = 7
vcf21_dsp.BISEND = True               # the envelope -> VCA (K3) and the LFO -> VCA (Shift + K3) are bipolar like the filter ones (K4): -64..63, 0 = no send
vcf21.BIPOLAR_MASK |= (1 << 11) | (1 << 14)    # codes 12 (LFOV) and 15 (ENVA)
vcf21.SIG_VAL = 0xA9                  # another signature: the FX type has 7 values now

NAME = "SC22"
b182 = b214.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b214.b213.extra)
