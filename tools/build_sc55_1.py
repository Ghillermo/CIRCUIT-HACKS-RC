"""Circuit Tracks 4486 - SC55.1 = SC55 + morphz.use_clr2() (the user, 2026-11-08: «clear + knob debe seguir funcionando, pero clear no debe salir
de la vista», «clear+synth1 en esta vista debe devolver el morph al estado inicial (knobs a 0/centro)»), use_sus («the envelope pad on morph should have sustain as you hold it»), use_nocur («discard the current patch
from the patch morph selection»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc55 as S  # noqa: E402
import linein3  # noqa: E402
import morphz  # noqa: E402
morphz.use_clr2()
morphz.use_sus()                         # pads 1 / 8 held = the envelope sustains
morphz.use_nocur()                       # the chain = the held patches only

NAME = "SC55.1"
B = S.B
extra = S.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
