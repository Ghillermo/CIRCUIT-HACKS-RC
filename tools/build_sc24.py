"""Circuit Tracks 4486 — SC24 = SC23.6 + (2026-10-07, from the conversation about the VCA-VCF mode):
  * pad 27 of the MIDI Preset view = off -> line in with VCA / VCF (orange) -> oscillator with VCA / VCF (green) -> off; with the mode off the knobs are the stock macros;
  * with the mode on, pads 1-8 select the knob page (1 VCA / VCF, 2 OSC1, 3 OSC2); pad 28 = one / two oscillators, pad 29 = the chain order (VCA, FX, VCF / VCF, VCA, FX);
  * the second oscillator (own tune, fine, wave, shape; the modulation depths are shared) with MIX, FM (OSC2 -> OSC1), RING, soft (phase reversing) sync of OSC2 by OSC1 and the bitwise zones (xor, or, nor, and, nand);
  * paraphony: one note = unison, two notes = one per oscillator (the third replaces the older).
The second oscillator's values (16 B) live in the Master FX block, which grows by 16 bytes (reservation 236 B, 4 B of margin below the heap pointer of the unit): they are not saved."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc23_6 as b236  # noqa: E402
import build_sc14 as s14  # noqa: E402
import build_sc17 as B17  # noqa: E402
import vcf21  # noqa: E402
import vcf21_dsp  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.use_dual()
vcf21.use_dualui()
assert B17.GFX_SIZE == vcf21.V2_OFF == 180
B17.GFX_SIZE += 16                    # the block still ends at the stock heap limit
s14.ST -= 16
b223 = b236.b223

NAME = "SC24"
extra = b236.extra

if __name__ == "__main__":
    linein3.main(NAME, b223.b22.b182.b18.b6.b5.build, b223.b22.b182.b18.b6.b5.s15, sys.argv[1:], extra=extra)
