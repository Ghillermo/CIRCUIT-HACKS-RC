"""Circuit Tracks 4486 — SC23.6 = SC23.5 + (2026-10-06, after testing): the type knobs of the VCA-VCF / oscillator mode
  * FX type (Shift + K8) and filter type (Shift + K5): plain 0..127 knobs clamped at both ends (no wrap-around) with 7 zones of ~18 clicks each; the zone is the type, the position inside the
    zone is a parameter of the type: the FX 'morph' (FXMOD) and the key follow of the filter cutoff (`vcf21.use_typezones()`, `vcf21_dsp.use_typezones()`); Shift + K7 (FXMOD) has no function any more;
  * waveform (page B, K7): the morph position as before (pure waves 42 clicks apart);
  * LEDs of the three knobs: colour = the selected mode, brightness = the parameter inside the mode (morph / follow).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc23_5 as b235  # noqa: E402
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import linein3  # noqa: E402
vcf21.use_typezones()
vcf21_dsp.use_typezones()
b223 = b235.b223

NAME = "SC23.6"
extra = b235.extra

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
