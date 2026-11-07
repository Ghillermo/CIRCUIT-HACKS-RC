"""Circuit Tracks 4486 - SC52.8 = SC52.7 + the one-oscillator mode's own functions (the user, 2026-11-07: «el modo 1 oscilador no debe incluir
modos de interacción con el segundo ... debería tener funciones propias»; chosen: sub-oscillator and noise, knob = amount, Shift = envelope, the
spare knob = LFO, Shift = LFO to the other): OSC 1's K5 / K6 = sub / noise level, Shift = envelope -> them, K8 = LFO -> sub, Shift + K8 = LFO ->
noise (oscmod.use_solo, vcf21_dsp.use_osc1x); the project's block from padding + 142 (wtui.use_pj2); TF into core 0's X for the room
(gentab.use_xtf); the page row's exchange left alone while an FM overlay shows (rowswap.use_fmov)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_7 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.8"
B = S.B
extra = S.extra
import gentab  # noqa: E402
import vcf21_dsp  # noqa: E402
import oscmod  # noqa: E402
import wtui  # noqa: E402
import rowswap  # noqa: E402
gentab.use_xtf()
vcf21_dsp.use_osc1x()
oscmod.use_solo()
wtui.use_pj2()
rowswap.use_fmov()


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
