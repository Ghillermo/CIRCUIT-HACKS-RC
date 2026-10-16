"""SC42.9 ARM tests (drumarp.use_rec: the drums' arpeggio recorded), through the controller, the real LED task and the drum player's slot 2:
  * Drum 1's arpeggiator on (1/8, up), pads 1 and 4 held in its Preset view, playing with Record: the hits go into the pattern (steps 1 and 3:
    samples 0 and 3 alternating, each with its pad's velocity; the micro step's bit; probability 7 on an empty step);
  * without Record (or in the count-in): nothing written; at 1/32 two hits a step: both micro steps, the last sample.

    python tools/emu_sc42_9.py SC42.9.bin SC42.9_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import drumarp as D  # noqa: E402

MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["drumarp"]["labels"].items()}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    dp = D.DP0; ifc = e.r32(dp + 0x4C)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (e.r32(e.r32(ifc)) & ~1, e.r32(e.r32(ifc) + 4) & ~1): e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=f, end=f)
    def setp(k, v):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, D.TRANSPORT, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
    e.btn(4); e.btn(8); X.frame(e)
    pat = r0(lab["c_dapat"], 0)
    e.call(lab["c_daset"], 0, pat, 0x80 | 6 << 3)                                       # on, up, 1/8
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); X.frame(e)
    base = e.r32(dp + 0x48) + 0x6A8 * pat
    e.uc.mem_write(base, bytes(32) + bytes([3]) * 32 + bytes([0xFF]) * 32 + bytes(32))  # empty steps, probability 3, no flip, no micro steps
    slot2 = e.r32(D.DP_VT + 8) & ~1
    def run(steps):
        for stp in steps:
            for m in range(6): e.call(slot2, dp, pat, stp, m, maxins=3_000_000)
    pv = lambda s: (e.r8(base + s), e.r8(base + 0x20 + s), e.r8(base + 0x40 + s), e.r8(base + 0x60 + s))
    setp(0, 1); setp(1, 1); setp(2, 0)
    run(range(4))
    check({pv(0), pv(2)} == {(90, 7, 0, 1), (100, 7, 3, 1)} and pv(0) != pv(2) and pv(1) == pv(3) == (0, 3, 0xFF, 0),
          f"playing with Record, 1/8: steps 1 and 3 = samples 0 / 3 with their pads' velocity (90 / 100), micro step 1, probability 7 ({[pv(s) for s in range(4)]})")
    setp(1, 0); run(range(4, 8))
    check(all(pv(s) == (0, 3, 0xFF, 0) for s in range(4, 8)), "without Record: nothing written")
    setp(1, 1); setp(2, 1); run(range(8, 12))
    check(all(pv(s) == (0, 3, 0xFF, 0) for s in range(8, 12)), "in the count-in: nothing written")
    setp(2, 0)
    e.call(lab["c_daset"], 0, pat, 0x80 | 2 << 3)                                       # 1/32
    run([12])
    check(pv(12)[3] == 0b1001 and pv(12)[2] in (0, 3) and pv(12)[0] in (90, 100), f"1/32: two hits in the step, both micro steps, one sample ({pv(12)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
