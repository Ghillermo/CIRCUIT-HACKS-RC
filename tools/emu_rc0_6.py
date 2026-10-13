"""RC0.6 ARM test (live RAM dump; the real pads of the Master FX view, the DSP service tick with the clock moved by hand): the two fixes over RC0.5.

    python tools/emu_rc0_6.py RC0.6.bin RC0.6_manifest.json RC0.5.bin RC0.5_manifest.json          (and the S builds)
  * the image: RC0.5 but for the mark, one branch of c_fxtick, and the dim white code of the Clear pads (0x02; RC0.5: 0x03, which pulses on the device);
  * the start time of the LFOs (build_sc17.use_t0fix): the Auto-Filter (pad 2) switched on alone: the start time of its set = the time of that tick
    (RC0.5: left as it was); the Phaser (pad 5) alone: the same; the Gater (pad 1) alone and the Gater with the Phaser: in both builds;
  * the playhead cache (set 2's word) and the sample's word (set 4's) are never written by this.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, TICK  # noqa: E402
import build_sc17 as S  # noqa: E402

B = 0x08010000


class ER(E35):
    def setup(self, man):
        self.L7 = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
        self.call(self.L7["c_gfst"]); self.blk7 = self.uc.reg_read(UC_ARM_REG_R0)
    def ftick(self, ms):
        self.w32(TICK, ms); self.call(self.L7["c_fxtick"], maxins=3_000_000)


def run(img, man):
    e = ER(img, man); e.setup(man); e.grid(); o = {}
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
    diff = [i for i in range(min(len(img), len(prev))) if img[i] != prev[i]]
    pk = "packio" in man["report"]
    dims = [i for i in diff if prev[i] == 0x03 and img[i] == 0x02]
    check(len(img) == len(prev) and len(diff) == (4 if pk else 3) and len(dims) == (2 if pk else 1),
          f"the image = the previous one but for {len(diff)} bytes: the mark, one branch of c_fxtick, the dim white 0x03 -> 0x02 ({[hex(B + i) for i in diff]})")
    n = run(img, man); gc.collect(); o = run(prev, prev_man)
    check(n["af"] == [True] and o["af"] == [False], "the Auto-Filter switched on alone: its LFO starts at that tick (the previous build: it did not)")
    check(n["ph"] == [True] and o["ph"] == [False], "the Phaser alone: the same")
    check(n["gate"] == [True] and o["gate"] == [True], "the Gater alone: its start time in both builds")
    check(n["gate_ph"] == [True, True] and o["gate_ph"] == [True, True], "the Gater and the Phaser in the same tick: both, in both builds")
    check(n["kept"] == (True, True), "the words of the playhead cache and of the sample are not written")
    print("RC0.6 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
