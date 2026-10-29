"""Circuit Tracks 4486 - SC48.8 = SC48.7 + (the user, 2026-10-28; the beta only for now):
  * trigled (at the end of the image: the hole has 634 B left and autorel grows): with Shift held, in every view, the eight track buttons light white while their track has a note sounding («When you
    hold shift, you can see on each channel's top pad light (white) whenever they trigger and back off when gate is no longer held»; «top pad
    labeled synth, midi, drum... lights on all views while shift is held»);
  * autorel.use_v2(): the de-automation view (Velocity view + Shift) keeps the stock's step colours, yellow only on the steps with automation, the
    marks red; Shift + a yellow step = its automation values on the knobs and in the sound until Shift is let go («yellow on steps with
    automation.  touching the step in this view (and only this view) allows to preview, on yellow, the automation value on the knob.  yellow
    goes away and knob back to normal when shift is released»; a tap on a yellow step previews only, the others still toggle the mark)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc48_7 as B  # noqa: E402
import autorel  # noqa: E402
autorel.use_v2()                                    # yellow = the steps with automation; Shift + a yellow step = their values until Shift is let go
import linein3  # noqa: E402

NAME = "SC48.8"


def extra(img, report):
    import hole
    import trigled
    import build_sc41_5
    B.extra(img, report)
    build_sc41_5.add(img, report, "trigled", trigled)    # the track buttons white while their gate is on (Shift held)
    hole.check(img, report)


if __name__ == "__main__":
    b5 = B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B.B9.B8.B7.B6.B5.B4.B2.B1.B.B.b33.b32.b31.b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
