"""Circuit Tracks 4486 - SC43.1 = SC43 + rollers.use_noteoff() / drumarp.use_noteoff() (the user, 2026-10-16: «en el roller, la fila inferior se ve
parcialmente blanca (pads 27 al 30)»: a drum's note-on lights its two boxes of the Note view white until the note-off; the hits of the rollers and of
the drum arpeggio with the transport stopped never got one; now they get it 100 ms later from the LED task).

SC43 = SC42.9 + tools/drumpat.py (the drums' dynamics, random-mutate of the sample and frequency, in their probability view: modes 1 / 2 as the note
tracks') + rollers.use_sync() / drumarp.use_sync() (the hits they record also go into the drum's edit store, drumstore.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43 as B  # noqa: E402
import rollers  # noqa: E402
import drumarp  # noqa: E402
rollers.use_noteoff()
drumarp.use_noteoff()
import linein3  # noqa: E402

NAME = "SC43.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
