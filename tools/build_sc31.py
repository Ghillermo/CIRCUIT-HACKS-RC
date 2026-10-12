"""Circuit Tracks 4486 — SC31 = SC30 + the step-drummer keeps the notes (vcf21.use_keepnote):
  * opening the view / editing no longer turns every note into the tonic: each step keeps the pitch of its first note (still one note per step:
    a chord keeps its first note);
  * a new note (Shift + step, or the velocity of an empty pair) takes the note of its pair, else of the nearest earlier note, else the tonic;
  * the audition of a step plays that same note.
Everything up to SC30 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc30 as b30  # noqa: E402
import vcf21  # noqa: E402
import linein3  # noqa: E402
vcf21.use_keepnote()

NAME = "SC31"
extra = b30.extra

if __name__ == "__main__":
    b5 = b30.b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
