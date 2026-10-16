"""Circuit Tracks 4486 - SC42.1 = SC42 + packio.use_playhold(): the ~4 s card rereads of the Preset views (c_pmode in Synth 1 / 2, mpatch in MIDI 1 / 2)
wait for the transport stopped (the delay stutter is Beta only, the user 2026-10-16; in emulation the Beta reads the card every ~4 s while playing in
those views, the RC never)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc42 as B  # noqa: E402
import linein3  # noqa: E402
import packio  # noqa: E402
packio.use_playhold()

NAME = "SC42.1"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
