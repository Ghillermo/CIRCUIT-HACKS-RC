"""Circuit Tracks 4486 — SC17.2 = SC17.1 with the Master FX view on Shift + Mixer.

The Mixer double press of SC17/SC17.1 never toggled on the device.  SC17.2 drops the toggle:
  Mixer          -> normal Mixer (always; also leaves Master FX)
  Shift + Mixer  -> stock Mixer selection, then Master FX mode on (pressing it again keeps Master FX)
The stock Shift + Mixer function (store 0x20039DE0, no visible effect) is no longer reachable.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import linein2  # noqa: E402

s17.ENTRY = "shift"
linein2.install(s15, s16)

if __name__ == "__main__":
    linein2.main("SC17.2", s17.build, s15, sys.argv[1:])
