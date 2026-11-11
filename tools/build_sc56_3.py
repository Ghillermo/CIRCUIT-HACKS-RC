"""Circuit Tracks 4486 - SC56.3 = SC56.2 + tools/fmmap.py (the user, 2026-11-11: «cómo podemos mostrar de forma más clara qué hace un algoritmo FM?
… algo con pads y colores que el usuario pueda mover»): the FM page's algorithm map (pad 7 held / tapped): each row a chain read left (modulator)
to right (carrier), a gap = no interaction, the ratio's harmonic class in colour, the picked operator pulsing; tap = pick, Shift = mute, one held
+ another = a link on / off (a custom algorithm saved with the patch)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc56_2 as S  # noqa: E402
import linein3  # noqa: E402
import patmut  # noqa: E402
import tabpack  # noqa: E402

NAME = "SC56.3"
B = S.B


def extra(img, report):
    import dspz
    import fmmap
    S.extra(img, report)
    dspz.add(img, report, "fmmap", fmmap)


if __name__ == "__main__":
    tabpack.use()
    patmut.use_v2()
    S.S.S.room()
    S.S.cpu()
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
