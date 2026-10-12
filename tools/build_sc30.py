"""Circuit Tracks 4486 — SC30 = SC29 + Master FX kept across sessions, and the project save fixed (persist19 options):
  * persist19.SAVE_MASK: the stock save copies our settings (Master FX slot assignments, synth source modes, the signature) into the project again.
    Since SC20 the VCF tick keeps bit 3 of the Master FX block's flag byte set and the save skipped the copy whenever any bit was set: no project saved
    with SC20..SC29 carried the signature, so every load read the zone as empty (slots, drum values and modes cleared).
  * persist19.GFX_GLOBAL: the slot assignments come from the project only at power-up; loading another session or a new project keeps the current
    assignments (and, as before, the top-row parameters, which live in RAM); the effects and the song pointer are still switched off.  Every save
    stores the current assignments in the project, so the next power-up starts with the ones of the last project saved.
Everything up to SC29 is unchanged (tools/verify_builds.py).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.SAVE_MASK = True
persist19.GFX_GLOBAL = True
import build_sc29 as b29  # noqa: E402
import linein3  # noqa: E402

NAME = "SC30"
extra = b29.extra

if __name__ == "__main__":
    b5 = b29.b28.b27.b26.b25.b24.b223.b22.b182.b18.b6.b5
    linein3.main(NAME, b5.build, b5.s15, sys.argv[1:], extra=extra)
