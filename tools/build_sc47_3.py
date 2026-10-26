"""Circuit Tracks 4486 - SC47.3 = SC47.2 + dsp56.use_shortbr() (the jumps of the code added to DSP core 0 in their one-word relative form when the
target is near: -331 words, the core as SC47.2's block by block) + vcf21_dsp.use_poly2() + poly.use_v2(): the polyphony of the own synth of
MIDI 1 / 2 also with two oscillators and in the VA-drum (each hit its own pitch and amplitude envelopes and noise); the user, 2026-10-26: «add
polyphony to the remaing voices», «VA-drum: por voz».  FM next (4 voices in total between the two tracks)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc47_2 as B  # noqa: E402
import dsp56  # noqa: E402
dsp56.use_shortbr()
import vcf21_dsp  # noqa: E402
vcf21_dsp.use_poly2()
import poly  # noqa: E402
poly.use_v2()
import linein3  # noqa: E402

NAME = "SC47.3"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
