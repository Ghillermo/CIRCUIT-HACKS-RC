"""Circuit Tracks 4486 — SC26 = SC25 + the step-drummer of the MIDI tracks (2026-10-07; inspired by other step-based percussive synthesizers, on top of the stock pattern):
  * pad 30 of the MIDI Preset view (mode on) opens / closes the step-drummer view (dim = enabled with the view closed, Shift + pad 30 = disabled);
  * pads 1-16 = the steps of the half shown (button 1-16 / 17-32): bright = a note, white = the step that sounds; a tap auditions the step, Shift + tap adds / removes its note;
  * the 8 knobs = the 8 pairs of steps: page pitch (Octave ^) = the value of the pair in lane 0 (64 = centre), page velocity (Octave v) = the velocity of its notes (0 = no note);
  * pads 17-24 = the destination of the pitch row: pitch of both oscillators, pitch of OSC2, WAVE, FM, MIX, env -> filter, SHAPE, DEC;
  * while it is enabled the pitch row is an OFFSET on the destination (the knob of the normal pages stays the base): +-12 semitones on the pitch destinations, +-64 steps on the others; the
    value is read from the pattern at the step that plays when the value goes to the DSP (no RAM for it); every note of the pattern becomes the root of the scale in octave 2.
State: one nibble per track in the two tail bytes the CC editor used (the editor derives its view from its track bit), 3 bits of the flags byte, 1 byte of the Master FX block: no new RAM."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc25 as b25  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_sdrum()

NAME = "SC26"
extra = b25.extra

if __name__ == "__main__":
    b5 = b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
