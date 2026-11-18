"""tools/icache.py: the stock's FPU set-up at reset (0x0805B790) with the I-cache hook returns to its caller within a few instructions and leaves
SCB CCR bit 17 (IC) set and ICIALLU written; the previous build returns without it.  (S702D2's bl hook never returned: e.call stops silently at
maxins, so the instruction count is the check.)

    python tools/emu_icache.py NEW.bin [PREV.bin]"""
from __future__ import annotations
import gc, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05 as S  # noqa: E402

FN, CCR, ICIALLU = 0x0805B790, 0xE000ED14, 0xE000EF50


def run(img):
    e = S.E(img)
    e.uc.mem_write(CCR, struct.pack("<I", 0x00040200))
    n, wr = [0], []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: n.__setitem__(0, n[0] + 1))
    e.uc.hook_add(UC_HOOK_MEM_WRITE, lambda uc, acc, a, s, v, d: wr.append(a), begin=ICIALLU, end=ICIALLU + 3)
    e.call(FN, maxins=200)
    pc = e.uc.reg_read(UC_ARM_REG_PC) & ~1
    return dict(pc=pc, n=n[0], ccr=struct.unpack("<I", e.uc.mem_read(CCR, 4))[0], inv=bool(wr))


def main(a):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(Path(a[0]).read_bytes()); gc.collect()
    check(r["pc"] == S.STOP and r["n"] < 60, f"returns to its caller ({r['n']} instructions, pc {r['pc']:#x})")
    check(r["ccr"] & (1 << 17) and r["ccr"] & ~(1 << 17) == 0x00040200, f"CCR {r['ccr']:#010x}: IC set, the rest kept")
    check(r["inv"], "ICIALLU written (the cache invalidated before it is on)")
    if len(a) > 1:
        o = run(Path(a[1]).read_bytes())
        check(o["pc"] == S.STOP and not o["ccr"] & (1 << 17), f"(the previous build: returns, CCR {o['ccr']:#010x})")
    print("ICACHE RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
