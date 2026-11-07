"""Circuit Tracks 4486 - SC52.9 = SC52.8 + the flip view of the MIDI 1 / 2 Preset view (the user, 2026-11-07: «el modo patch flip (pad 26) ahora:
muestra los destinos de step flip en la fila 2 cuando se activa step flip. En la fila 3 permite elegir entre modos (excluyentes): patch flip (PGM seq),
Step flip»; pad 26 opens / closes the view, pad 17 PGM seq, pad 18 step flip, step flip without a target = the last one used): tools/flipview.py in the
hole, spliced in above jumpflip."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc52_8 as S  # noqa: E402
import linein3  # noqa: E402

NAME = "SC52.9"
B = S.B


def extra(img, report):
    S.extra(img, report)
    import hole
    import flipview
    hole.add(img, report, "flipview", flipview)          # above jumpflip in the template view's slots 0 / 7


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
