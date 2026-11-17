"""S564D tests (tools/dwtwatch.py), the parts Unicorn can run (it has no DWT): an LED frame arms DEMCR (TRCENA | MON_EN), unlocks the DWT and
writes COMP / MASK / FUNCTION of comparators 0 / 1 = the two corrupted words, 2, 6 (write); only once; the frame's LEDs are Beta 5.64's.
The DebugMonitor handler (vector 12 -> c_dwmon), entered with a stacked frame on the PSP: the black box frozen as a fault capture of vector 12 whose
PC / LR are the frame's (the writer), both comparators off, DFSR.DWTTRAP written, r4-r7 kept.

    python tools/emu_dwtwatch.py firmware/s564d/circuittracks-4486-S564D.bin firmware/s564d/manifest.json firmware/b5.64/circuittracks-4486-B5.64.bin firmware/b5.64/manifest.json
"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_PSP
import emu_sc48_8 as S
import blackbox as BB
import dwtwatch as DW
from emu_sc35 import MGR
from emu_sc05 import STOP


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
    return bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["dwtwatch"]["labels"].items()}
    check(struct.unpack_from("<I", img, DW.VEC_DEBUGMON - 0x08010000)[0] == L["c_dwmon"] | 1, "vector 12 -> c_dwmon")
    e = S.ET(img, man)
    e.uc.mem_write(DW.DW, bytes(8)); e.uc.mem_write(DW.DEMCR, bytes(4)); e.uc.mem_write(DW.DWT_COMP0, bytes(32))
    f = frame(e)
    rd = lambda x: e.r32(x)
    c = [(rd(DW.DWT_COMP0 + 16 * i), rd(DW.DWT_COMP0 + 16 * i + 4), rd(DW.DWT_COMP0 + 16 * i + 8)) for i in range(2)]
    check(rd(DW.DEMCR) & 0x01010000 == 0x01010000 and rd(DW.DWT_LAR) == 0xC5ACCE55 and c == [(w, 2, 6) for w in DW.WATCH] and e.r8(DW.DW + 4) == 1,
          f"an LED frame arms: DEMCR {rd(DW.DEMCR):#x}, comparators {[(hex(x), m, fn) for x, m, fn in c]}")
    e.uc.mem_write(DW.DWT_COMP0 + 8, struct.pack("<I", 0x77)); frame(e)
    check(rd(DW.DWT_COMP0 + 8) == 0x77, "only once (a second frame leaves the registers)")
    if len(a) > 3:
        p = S.ET(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())); fp = frame(p); del p
        check(f == fp, "the LED frame = Beta 5.64's")
    # the DebugMonitor handler: a frame on the PSP as the hardware stacks it
    psp = 0x2004FB40; fr = [0x11, 0x22, 0x33, 0x44, 0x55, 0x08070123, 0x0807456A, 0x21000000]
    e.uc.mem_write(psp, struct.pack("<8I", *fr)); e.uc.reg_write(UC_ARM_REG_PSP, psp)
    e.uc.mem_write(BB.BB + BB.O.ST, bytes([0]))
    for r, v in ((UC_ARM_REG_R4, 0x4444), (UC_ARM_REG_R5, 0x5555), (UC_ARM_REG_R6, 0x6666), (UC_ARM_REG_R7, 0x7777)): e.uc.reg_write(r, v)
    e.uc.mem_write(DW.DWT_COMP0 + 8, struct.pack("<I", 6)); e.uc.mem_write(DW.DWT_COMP0 + 24, struct.pack("<I", 6))
    e.uc.reg_write(UC_ARM_REG_LR, STOP | 1 | 4)                                   # (a return address with bit 2 set: the PSP path; real EXC_RETURN 0xFFFFFFFD)
    sp0 = 0x2006F000; e.uc.reg_write(13, sp0)
    e.uc.emu_start(L["c_dwmon"] | 1, 0xFFFFFFFF, count=20_000_000)
    st = e.r8(BB.BB + BB.O.ST)
    regs = [e.uc.reg_read(r) for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)]
    raw = bytes(e.uc.mem_read(BB.BB, BB.SIZE))
    check(st & (BB.ST_FROZEN | BB.ST_FAULT) == (BB.ST_FROZEN | BB.ST_FAULT), f"the black box frozen as a fault capture (state {st:#x})")
    check(struct.pack("<I", 0x0807456A) in raw and struct.pack("<I", 0x08070123) in raw, "the writer's PC / LR in the record")
    check(rd(DW.DWT_COMP0 + 8) == 0 and rd(DW.DWT_COMP0 + 24) == 0 and rd(DW.DFSR) == 4, "both comparators off, DFSR.DWTTRAP written")
    check(regs == [0x4444, 0x5555, 0x6666, 0x7777], f"r4-r7 kept ({[hex(x) for x in regs]})")
    print(f"{man.get('marker')} DWTWATCH RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
