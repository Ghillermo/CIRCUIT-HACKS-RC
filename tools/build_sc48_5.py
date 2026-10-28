"""Circuit Tracks 4486 - SC48.5 = SC48.4 + (the user, 2026-10-28; the beta only): MIDI 1 / 2 pressed with its own Note view on the screen = its
Preset view, no double-tap window (midipre.use_v2: «midi second press is not working. it activates on a short double tap, but i want the view to
open if the midi note view is opened and we tap midi once again»); a voice limiter on the DSP's time (vguard: S484D on the device «save goes
white when crackling», «up until red the sound was OK», «red is pretty much ok, so push towards the red-white limit»: near the ring running dry,
the quietest released voice freed, else the oldest held one); the poly level rule relaxed to sqrt(2 / n) (poly.use_v8: «the clear button only ever
reaches green, so you can relax the volume limiter»); poly the voice mode of a project that never set one (poly.use_polydef: «also polyphony
shold be default mode»); the limiter's cap and the level rule in the unison too (poly.use_v9: «also extend your findings and voice limiting to
unison»)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import midipre  # noqa: E402
midipre.use_v2()                                    # MIDI 1 / 2 with its own Note view on the screen = its Preset view
import build_sc48_4 as B  # noqa: E402
import poly  # noqa: E402
poly.use_v8()                                       # poly: sqrt(2 / n) (two voices at full level)
poly.use_polydef()                                  # a project with no voice mode set = poly
poly.use_v9()                                       # vguard's voice choice and cap (poly and unison); the unison's level by sqrt(2 / n) too
import linein3  # noqa: E402

NAME = "SC48.5"


def extra(img, report):
    import hole
    import vguard
    B.extra(img, report)
    hole.add(img, report, "vguard", vguard)              # the voice limiter (the head of the DSP service chain)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
