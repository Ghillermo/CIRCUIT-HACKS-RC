"""Circuit Tracks 4486 - SC43.3 = SC43.2 + sdpv.use_v3() (the user, 2026-10-16: on MIDI the step-drummer knobs start at the point of no modulation of their destination: the centre for the bipolar ones, 0 for the unipolar ones; their LEDs show the amount, dim = none).

SC43.2 = SC43.1 + arp.use_recoff() (the user, 2026-10-16: «al grabar un patrón con arpegiador de 32 pasos, sólo se aplica el
arpegiador a la página donde se pulsó grabar»: the chord's second and later notes reached the recorder's note-on but never its note-off, so the
recorder kept them held and ignored them when played again; now letting go of them calls the recorder's note-off gate too).

SC43.1 = SC43 + rollers.use_noteoff() / drumarp.use_noteoff() (the hits of the rollers and of the drum arpeggio with the transport stopped get their
note-off 100 ms later: the drum's boxes of the Note view no longer stay white)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc43_2 as B  # noqa: E402
import sdpv  # noqa: E402
sdpv.use_v3()
import linein3  # noqa: E402

NAME = "SC43.3"
extra = B.extra


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
