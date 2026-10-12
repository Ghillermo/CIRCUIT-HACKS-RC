"""Circuit Tracks 4486 — SC19.5 = SC19.4 + the Setup's FX returns also reach the synth's line inputs.

Setup pad 22 / 23 (SC10) send the reverb return to mixer strip 3 / the delay return to strip 4 in place of audio inputs 1 / 2 (X:$3A00 bit 0 / bit 1).  Now,
while one of those is on, the synth source "input 1" / "input 1 inverted" (modes 1 / 3) reads the reverb return and "input 2" / "input 2 inverted" (modes 2 / 4)
the delay return (the inverted ones negated); with the flags off they read the line inputs as always.  The capture of the returns (linein3.fx_cap, x8) runs whenever
a flag is on.  The synth source modes stay 0..4 (noise, inputs 1 / 2, inverted): the delay / reverb return modes 5 / 6 are not offered (the user dropped them; the
DSP code that serves them stays in linein3 for the older builds).  Everything else is SC19.4.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.FIX_LOCK = True            # SC19.3: no stock lock from the service tick
persist19.REC_RESTORE = True         # SC19.4: the 65 bytes come back from the session record
persist19.BLOB_KEEP = True           # SC19.4: a synth patch change keeps them
import build_sc19_1 as b191  # noqa: E402
import linein3  # noqa: E402
linein3.FX_GAIN_SHIFT = 3            # x8 on the captured L + R (as SC17.7 / SC20D.1)
linein3.SETUP_RET = True             # the Setup's FX returns are what the synth's inputs 1 / 2 read while they are on

NAME = "SC19.5"
b182 = b191.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b191.extra)
