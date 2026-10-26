"""Circuit Tracks 4486 - SC46.6 = SC46.5 + the FM engine improved (the user, 2026-10-24: «Mejora el motor FM»; the study's plan and the user's answers
of 2026-10-25): core 0 with the one-word immediates (vcf21_dsp.use_shortimm: 106 words, bit for bit the same); the FM voice's VCA open
(use_fmvca), R at full range (use_fmwide), the compact loop computed 4 to 1 (use_fmcompact / use_fmorder), the near-sine operators (use_fmsine),
the smoothed AMP (use_fmsmooth), the DX7 feedback (use_fbavg); fmeng's ARM side to match and the user's choices (fmeng.use_v2: the fixes,
velocity / keyboard scaling / brightness, Shift + K1-K4 centre-zero, the fine detune, the voicings, the algorithms on the pads under pad 7, Shift +
a patch pad without the audition); the matrix's zones with an amount 0 (modmx.use_zero: Clear + MIDI 1 / 2 zeroes the amounts)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc46_5 as B  # noqa: E402
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_shortimm()
vcf21_dsp.use_fmvca()
vcf21_dsp.use_fmwide()
vcf21_dsp.use_fmcompact()
vcf21_dsp.use_fmorder()
vcf21_dsp.use_fmsine()
vcf21_dsp.use_fmsmooth()
vcf21_dsp.use_fbavg()
import modmx  # noqa: E402
modmx.use_zero()
import fmeng  # noqa: E402
fmeng.use_v2()
import linein3  # noqa: E402

NAME = "SC46.6"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
