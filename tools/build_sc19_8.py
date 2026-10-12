"""Circuit Tracks 4486 — SC19.8 = SC19.7 + the drum knobs follow the panel labels.

K1 Oscillator (pitch), K2 Osc mod, K3 Amp envelope, K4 Filter envelope, K5 Filter frequency, K6 Resonance, K7 Modulation, K8 FX.  The stock parameters (pitch, decay,
distortion, EQ) keep their id, their saved value and their MIDI (the knob only chooses which stock macro the stock handler is called with: the MIDI follows the parameter,
not the knob); our functions move to the knobs that match their label; the saved bytes are indexed by function, so saved projects are unaffected.  See persist19.REMAP_*.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist19  # noqa: E402
persist19.REMAP = True
import build_sc19_7 as b197  # noqa: E402
import linein3  # noqa: E402

NAME = "SC19.8"
b182 = b197.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b197.b196.b195.b191.extra)
