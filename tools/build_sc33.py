"""Circuit Tracks 4486 — SC33 = SC32 + the captured sample in Master FX (build_sc17.use_sampler, tools/sampler_dsp.py):
  * pad 32 (red) records the output of the unit WITH the effects (after the Master FX chain), mono, up to 3.46 s, into the DSP's external memory (Y:$600000, outside
    the stock zone map; SC32D2 showed it writable and unused): held = records while held; a short press = starts, the next press stops; Shift + pad 32 = armed
    (blinking): records the next bar (from Play / the next bar line to the end of that bar);
  * pad 7 (yellow) plays it: one-shot / gate / loop (K2), Shift + pad 7 = loop whatever the mode (again = stop); K1 pitch (-24..+23 semitones), K3 start, K4 end
    (end < start = reverse); the knobs are remembered in the 4 bytes of the slot of pad 32 (no longer an assignable slot), saved with the project like the slots;
  * pad 6 stays Vinyl; pad 8 also stops the sample and cancels a latched / armed recording;
  * step-drummer (vcf21.use_rtrec): while the unit records, a step pad (no Shift) also writes its note into the step that plays, with the micro step of the moment.
Everything up to SC32 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc32 as b32  # noqa: E402
import build_sc16  # noqa: E402
import build_sc17  # noqa: E402
import sampler_dsp  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
build_sc17.use_sampler()
vcf21.use_rtrec()
sampler_dsp.install_dsp(build_sc16)

NAME = "SC33"


def extra(img, report):
    b32.extra(img, report)
    sampler_dsp.patch_dsp(img, report)


if __name__ == "__main__":
    b5 = b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
