"""Circuit Tracks 4486 - SC44.7 = SC44.6 + granular_dsp.use_stereo() + vcf21.use_grbip() (the user, 2026-10-19: «haz que la dispersion granular sea
stereo», «el valor de paneo de pista controla la proporción / probabilidad de izquierda / derecha», «mantén sk2 dispersión de la posición (centro) y
sk4 dispersion stereo», «junta en sk3 bipolar dispersion tono (+-24) y probabilidad reverse»): the granular engine of MIDI 1 / 2 in stereo (mid /
side: each grain left or right by the track's pan, the width on Shift + K4); Shift + K3 bipolar: left reverse, right pitch spray."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import granular_dsp  # noqa: E402
granular_dsp.use_stereo()
import sampler_dsp  # noqa: E402
sampler_dsp.PRE_HOOK = granular_dsp.core0_sides
import vcf21  # noqa: E402
vcf21.use_grbip()
import build_sc44_6 as B  # noqa: E402
import linein3  # noqa: E402

NAME = "SC44.7"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
