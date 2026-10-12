"""Circuit Tracks 4486 — SC29 = SC28 + the VA-drum engine of the MIDI tracks (2026-10-07; inspired by other step-based percussive synthesizers):
  * a fourth state of pad 27: off -> line in -> oscillator -> VA-drum -> off.  VA-drum = the oscillator engine (one or two oscillators, FM, ring, sync, bitwise, the chain order) with:
      - the VCA envelope as a one-shot: ATK, then DEC down to silence; the length of the gate does not matter;
      - two more decay envelopes that restart with every note: the pitch one (its decay = the SUS knob) feeds ENVP, the filter one (its decay = the REL knob) feeds ENVF;
      - noise instead of the LFO: LRATE = the level of white noise added to the oscillator; LFOF / LFOV / LFOP / LFOW / LFOM = a random value per block to the cutoff / level / pitch / shape / morph;
  * pad 31 (VA-drum only): the velocity also sets the start level of the pitch and the filter envelopes (it always scales the level, as before).
No new RAM: the four bits (engine and pad 31, per track) live in the low nibble of the signature byte of the saved state (0xB0..0xBF); the DSP gets them in the ACT message.
The other engines sound exactly as before (the two new envelope words are copies of the envelope there)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vcf21_dsp  # noqa: E402
import build_sc28 as b28  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21_dsp.use_vadrum()
vcf21.use_vadrum()

NAME = "SC29"
extra = b28.extra

if __name__ == "__main__":
    b5 = b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
