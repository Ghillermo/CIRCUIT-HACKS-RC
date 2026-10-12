"""Circuit Tracks 4486 — SC37.4 = SC37.3 + vcf21_dsp.use_stglide() (the user, 2026-10-10: a click when switching the engine of pad 27):
the sustain stage of the VCA envelope glides towards SUS instead of jumping (VA-drum sets SUS to 0, the oscillator brings it back),
so switching engines with a held note or turning SUS no longer steps the level; vcf21.use_dualhide(): pad 28 (one / two oscillators) is dark and
inactive unless the engine plays oscillators; packio.use_copyx(): Duplicate between packs copies (the first pack untouched; inside a pack it swaps);
packio.use_dupmask(): Duplicate lit and held in the synth / drum Preset views (SC37.3 on the device: it did nothing with synth patches);
build_sc17.use_glitch3(): two bottom pads with the Glitch held together no longer copy one's knobs into the other; build_sc17.use_vinyl_peach();
build_sc10.use_retcols(): the Setup toggles «reverb -> strip 3» / «delay -> strip 4» in the reverb / delay colours (cream / peach).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc36_2 as B2  # noqa: E402  (configures everything as SC36.2)
import packio  # noqa: E402
import vcf21_dsp  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
import build_sc17  # noqa: E402
import build_sc10  # noqa: E402
packio.use_copyx()
build_sc10.use_retcols()
packio.use_dupmask()
build_sc17.use_glitch3()
build_sc17.use_vinyl_peach()
vcf21_dsp.use_stglide()
vcf21.use_dualhide()

NAME = "SC37.4"
extra = B2.extra


if __name__ == "__main__":
    b5 = B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
