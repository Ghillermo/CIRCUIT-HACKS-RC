"""Circuit Tracks 4486 — SC27 = SC26 + the rest of the step-drummer (2026-10-07):
  * the step-drummer on Synth 1 / 2: pad 30 of the source view (press the Synth button twice) opens / closes it; pads 17-24 choose which of the 8 macros the pitch row writes (the lane of that macro in the
    pattern, as the macro position: the stock engine plays it); a pair with no value starts from the present position of the macro; the audition is an internal note;
  * in the view Octave v / ^ and 1-16 / 17-32 are lit (the page, the half) and the knob of the pair that plays is white;
  * the rows 2 and 3 go dark when the view is closed (SC26 left the steps and the destinations lit);
  * two more knob pages for the MIDI tracks (pads 4 / 5 of the page row; the same values in another layout): the 8 values the sequencer automates, and the modulation (ADSR on the top row, LFO on the bottom row).
No new RAM (the second tail byte of the nibbles: bits 1-3 the macro of the synth, bit 0 the third bit of the knob page of the MIDI track with the same index)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc26 as b26  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_sdrum2()
vcf21.use_pages5()

NAME = "SC27"
extra = b26.extra

if __name__ == "__main__":
    b5 = b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
