"""Circuit Tracks 4486 - SC45.1 = SC45 + tools/mutebank.py in the hole (the user, 2026-10-20: «ajuste: cuando el track está parado
(desactivado mediante pad en mixer) y el modo Record amarillo, tocar los steps durante la grabación los reproduce y envía, pero no los escribe en
la pista parada (sólo en la que está sonando). Esto permite usar la pista como Chord bank sin que se escriba nada en el banco»): with the
recording of the internal routes on (Record yellow in the Setup view), the recorder writes nothing into a note track muted in the Mixer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc45 as B  # noqa: E402
import mutebank  # noqa: E402
import hole  # noqa: E402
import linein3  # noqa: E402

NAME = "SC45.1"


def extra(img, report):
    B.extra(img, report)
    hole.add(img, report, "mutebank", mutebank)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
