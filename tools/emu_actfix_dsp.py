"""vcf21_dsp.use_actfix on core 0: MIDI 1's ACT message with each LFO shape, the oscillator engine: the ACT slot stays 2 (before the fix shapes 4-6 left $800000: no engine), DFLAGS holds the
shape in bits 5-7 and the LFO's value moves.

    python tools/emu_actfix_dsp.py BUILD.bin
"""
from __future__ import annotations
import gc, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc43_9_dsp as M  # noqa: E402

VB, OS = 0x3B80, 0x3900


def main(img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    for shape in range(7):
        sched = [[((b // 4 & 1) << 23 | 19 << 16 | 2 | shape << 13, M.MB[0])] if b % 4 == 0 else [] for b in range(300)]
        R, _ = M.dsp_run(img, sched, blocks=260, checks=(), every=((VB + 20, 1), (OS + 21, 1), (VB + 26, 1)), force=((VB + 12, 60),))
        gc.collect()
        v = [(a, x[0]) for sp, a, x in R if sp == "x"][-720:]
        act = {x for a, x in v if a == VB + 20}; fl = {x for a, x in v if a == OS + 21}; lv = {x for a, x in v if a == VB + 26}
        check(act == {2} and fl == {shape << 5} and len(lv) > 1, f"shape {shape}: ACT slot {sorted(hex(x) for x in act)}, DFLAGS {sorted(hex(x) for x in fl)}, {len(lv)} LFO values")
    print("ACT DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes()) else 0)
