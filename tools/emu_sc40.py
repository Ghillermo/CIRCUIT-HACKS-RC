"""SC40 ARM test (live RAM dump; the real pads of the Master FX view, the DSP service tick with the clock moved by hand): the start time of the LFOs
(build_sc17.use_t0fix).

    python tools/emu_sc40.py SC40.bin SC40_manifest.json SC39.9.bin SC39.9_manifest.json
  * the Auto-Filter (pad 2) switched on alone: the start time of its set = the time of that tick (the previous build: left as it was);
  * the Phaser (pad 5) alone: the same; the Gater (pad 1) alone: the same in both builds;
  * the Gater and the Phaser in the same tick: both, in both builds;
  * the playhead cache (set 2's word) and the sample's word (set 4's) are never written by this.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_9 as T9  # noqa: E402
import build_sc17 as S  # noqa: E402


def run(img, man):
    e = T9.E9(img, man); e.setup(man); e.grid(); o = {}
    t0 = lambda s: e.r32(e.blk7 + S.S_T0 + 4 * s)
    t = 900000
    e.ftick(t); w2, w4 = t0(2), t0(4)
    for name, pads, sets in (("af", (1,), (1,)), ("ph", (4,), (3,)), ("gate", (0,), (0,)), ("gate_ph", (0, 4), (0, 3))):
        t += 5000
        for p in pads: e.pad(p)
        e.ftick(t + 1); o[name] = [t0(s) == t + 1 for s in sets]
        for p in pads: e.rel(p)
        e.ftick(t + 2)
    o["kept"] = (t0(2) == w2, t0(4) == w4)
    del e; gc.collect(); return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    n = run(img, man); gc.collect(); o = run(prev, prev_man)
    check(n["af"] == [True] and o["af"] == [False], "the Auto-Filter switched on alone: its LFO starts at that tick (the previous build: it did not)")
    check(n["ph"] == [True] and o["ph"] == [False], "the Phaser alone: the same")
    check(n["gate"] == [True] and o["gate"] == [True], "the Gater alone: its start time in both builds")
    check(n["gate_ph"] == [True, True] and o["gate_ph"] == [True, True], "the Gater and the Phaser in the same tick: both, in both builds")
    check(n["kept"] == (True, True), "the words of the playhead cache and of the sample are not written")
    print("SC40 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
