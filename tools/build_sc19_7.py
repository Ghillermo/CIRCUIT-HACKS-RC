"""Circuit Tracks 4486 — SC19.7 = SC19.6 + the Master FX song pointer's instant jump mode: white pad, repeating step.

Master FX pad 7 is the jump mode (hold = momentary, Shift + pad 7 = sticky on / off): touching a step pad of the song pointer jumps there at the next step boundary.
SC19.7: pad 7 is white (dim white off, bright white on), and while the mode stays on (the pad held, or toggled on) the same step is repeated at every following step
boundary — the song resumes from there when the pad is released / toggled off.  A tap that ends before the boundary still jumps once.  Everything else is SC19.6.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_sc19_6 as b196  # noqa: E402
import build_sc17 as s17  # noqa: E402
import linein3  # noqa: E402
s17.use_jump(repeat=True, white=True)

NAME = "SC19.7"
b182 = b196.b182

if __name__ == "__main__":
    linein3.main(NAME, b182.b18.b6.b5.build, b182.b18.b6.b5.s15, sys.argv[1:], extra=b196.b195.b191.extra)
