"""Circuit Tracks 4486 — SC36 = SC35 + the granular synth of MIDI 1 / 2 and the Glitch of Master FX on DSP core 1 (tools/granular_dsp.py) + the FX step sequencer.
  * drums2_dsp.COMPACT: TATK / TDEC stored as their useful halves (123 P words of core 0 freed, the sound identical: tools/emu_compact.py);
  * core 1 (granular_dsp.core1_code, P:$12A = jmp c1loop): the two granular voices (16 grains each, from the pack's samples or the capture) and the
    Glitch (a tape head on a stereo ring of the master in the external memory);
  * core 0: vcf21_dsp.GRAN (the voice plays core 1's block when DFLAGS bit 4; GNEW counted for core 1), sampler_dsp.TAIL (the copies for core 1,
    the Glitch replacing the master, the block counter);
  * ARM: vcf21.use_gran() (pad 27: oscillator -> VA-drum -> granular -> off; the granular knob page), build_sc17.use_glitch() (pad 31 of Master FX /
    FX = the Glitch, K1-K4), vcf21.use_fxseq() (the FX step sequencer).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc35 as B  # noqa: E402  (configures everything as SC35)
import drums2_dsp  # noqa: E402
import vcf21_dsp  # noqa: E402
import sampler_dsp  # noqa: E402
import granular_dsp  # noqa: E402
import linein3  # noqa: E402
import vcf21  # noqa: E402
import build_sc17  # noqa: E402
drums2_dsp.COMPACT = True
vcf21_dsp.GRAN = True
sampler_dsp.TAIL, sampler_dsp.TAIL_TABLE = granular_dsp.core0_tail, granular_dsp.core0_table
build_sc17.use_glitch()
vcf21.use_gran()
vcf21.use_fxseq()

NAME = "SC36"


def extra(img, report):
    B.extra(img, report)
    report["granular"] = granular_dsp.patch_core1(img)


if __name__ == "__main__":
    b5 = B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
