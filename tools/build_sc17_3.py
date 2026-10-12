"""Circuit Tracks 4486 — SC17.3 = SC17.1 with Master FX on the REAL Mixer button (14).

SC17-SC17.2 hooked button 13 / view 1, which is not the Mixer (SC17D on the device: the hook never ran).
  Mixer from another view -> normal Mixer;  Mixer while in the Mixer -> Master FX;  again -> Mixer.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import linein2  # noqa: E402

s17.use_mixer14()
s17.DIAG = "--diag" in sys.argv
NAME = "SC173D" if s17.DIAG else "SC17.3"
linein2.install(s15, s16)

if __name__ == "__main__":
    linein2.main(NAME, s17.build, s15, [x for x in sys.argv[1:] if x != "--diag"])
