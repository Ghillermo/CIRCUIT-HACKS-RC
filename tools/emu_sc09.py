"""SC09 tests: drum Pitch DSP word = 0x10000 * 2^((v-64)/12) for all 4 drums, rest of the handler unchanged."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc05 import E  # noqa: E402
import build_sc09 as b9  # noqa: E402

HANDLERS = (0x080287DE, 0x0802887A, 0x0802890E, 0x080289A2)
PITCH_ADDR = (0xA4, 0xAE, 0xB8, 0xC2)
GETTER = 0x08036192


def dsp_writes(image, drum, v):
    e = E(image); w = []
    def h(uc, a, s, d):
        if a == 0x080292F8:
            w.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        elif a == GETTER and uc.reg_read(UC_ARM_REG_R0) == 0x10 and uc.reg_read(UC_ARM_REG_R1) == 2 + 7 * drum:
            uc.reg_write(UC_ARM_REG_R0, v); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, h)
    e.call(HANDLERS[drum])
    return w


def main(stock, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c: fails += 1; print("FAIL:", m)
        else: print("ok  :", m)
    tab = b9.table()
    for drum in range(4):
        bad = []
        for v in (0, 1, 2, 3, 52, 63, 64, 65, 66, 76, 88, 100, 127):
            ws, w9 = dsp_writes(stock, drum, v), dsp_writes(img, drum, v)
            ps = [x for a, x in ws if a == PITCH_ADDR[drum]]; p9 = [x for a, x in w9 if a == PITCH_ADDR[drum]]
            other_s = [x for x in ws if x[0] != PITCH_ADDR[drum]]; other_9 = [x for x in w9 if x[0] != PITCH_ADDR[drum]]
            if ps != [b9.stock_word(v)] or p9 != [tab[v]] or other_s != other_9:
                bad.append((v, [hex(x) for x in ps], [hex(x) for x in p9]))
        check(not bad, f"drum {drum+1}: stock word = linear formula, SC09 word = semitone table, other writes equal {bad[:2]}")
    check(tab[64] == 0x10000 and tab[76] == 0x20000 and tab[52] == 0x8000 and tab[88] == 0x40000, "64 = original, +-12 = x2 / /2, +24 = x4")
    r = lambda v: b9.stock_word(v) / 0x10000
    import math
    print(f"     stock: v=76 -> x{r(76):.3f} ({12*math.log2(r(76)):+.2f} st), v=127 -> x{r(127):.3f}, v=0 -> x{r(0):.3f}")
    print("SC09 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()) else 0)
