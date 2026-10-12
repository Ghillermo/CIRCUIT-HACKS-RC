"""Circuit Tracks 4486 — SC17D = SC17.2 + diagnostic LEDs (why does Master FX not open on the device?).

Synth 1/2 Preset view, hold Shift (pads 25-29 keep showing the line-input mode):
  pads 9-16  free heap bytes / 16 at this moment (binary, pad 9 = 128 ... pad 16 = 1; bright = 1)
  pad 17     Master FX state block available (c_gfst != 0)
  pad 18     Master FX mode on (S_MODE)
  pad 19     Shift + Mixer reached the SC17 code            (sticky since power-up)
  pad 20     Mixer (no Shift) reached the SC17 code         (sticky)
  pad 21     Mixer view pad handler wrapper was called      (sticky)
  pad 22     Mixer view LED wrapper was called              (sticky)
  pad 23     "Master FX showing" test was ever true           (sticky)
  pad 24     heap limit is the SC14/SC17 reservation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc17 as s17  # noqa: E402
import build_sc15 as s15  # noqa: E402
import build_sc16 as s16  # noqa: E402
import linein2  # noqa: E402

s17.ENTRY = "shift"
s17.DIAG = True
linein2.install(s15, s16)

if __name__ == "__main__":
    linein2.main("SC17D", s17.build, s15, sys.argv[1:])
