"""S715D2 tests (dwtwatch.use_filtered_many), the parts Unicorn can run (it has no DWT): after boot the two watched words hold their legit vtables;
an LED frame arms comparators 0 / 1 on them (MASK 2, FUNCTION 6) when FUNCTION0 is 0 and no record is frozen, else leaves them; the DebugMonitor
handler resumes when both words are legit (comparators kept, DFSR.DWTTRAP written) and otherwise freezes the black box as a fault capture of
vector 12 with the writer's PC / LR, comparators off, r4-r7 kept.

    python tools/emu_dwtmany.py firmware/s715d2/circuittracks-4486-S715D2.bin firmware/s715d2/manifest.json
"""
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_LR, UC_ARM_REG_PSP
import emu_sc48_8 as S
import blackbox as BB
import dwtwatch as DW
from emu_dwtwatch import frame
from emu_sc05 import STOP
from build_s715d2 import WATCH


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["dwtwatch"]["labels"].items()}
    check(struct.unpack_from("<I", img, DW.VEC_DEBUGMON - 0x08010000)[0] == L["c_dwmon"] | 1, "vector 12 -> c_dwmon")
    e = S.ET(img, man)
    rd = lambda x: e.r32(x)
    got = [rd(w) for w, _ in WATCH]
    check(got == [v for _, v in WATCH], f"after boot the watched words hold their legit vtables ({[hex(x) for x in got]})")
    comps = lambda: [(rd(DW.DWT_COMP0 + 16 * i), rd(DW.DWT_COMP0 + 16 * i + 4), rd(DW.DWT_COMP0 + 16 * i + 8)) for i in range(2)]
    e.uc.mem_write(DW.DEMCR, bytes(4)); e.uc.mem_write(DW.DWT_COMP0, bytes(32)); e.uc.mem_write(BB.BB + BB.O.ST, bytes([BB.ST_FROZEN]))
    frame(e)
    check(rd(DW.DWT_COMP0 + 8) == 0, "not armed while a record is frozen")
    e.uc.mem_write(BB.BB + BB.O.ST, bytes([0])); frame(e)
    check(rd(DW.DEMCR) & 0x01010000 == 0x01010000 and rd(DW.DWT_LAR) == 0xC5ACCE55 and comps() == [(w, 2, 6) for w, _ in WATCH],
          f"an LED frame arms both: {[(hex(x), m, fn) for x, m, fn in comps()]}")
    e.uc.mem_write(DW.DWT_COMP0 + 4, struct.pack("<I", 0x77)); frame(e)
    check(rd(DW.DWT_COMP0 + 4) == 0x77, "armed already (FUNCTION0 set): a second frame leaves the registers")

    def mon(words):
        for (w, _), v in zip(WATCH, words): e.uc.mem_write(w, struct.pack("<I", v))
        psp = 0x2004FB40; fr = [0x11, 0x22, 0x33, 0x44, 0x55, 0x08070123, 0x0807456A, 0x21000000]
        e.uc.mem_write(psp, struct.pack("<8I", *fr)); e.uc.reg_write(UC_ARM_REG_PSP, psp)
        e.uc.mem_write(BB.BB + BB.O.ST, bytes([0])); e.uc.mem_write(BB.BB + BB.O.PC, bytes(16)); e.uc.mem_write(DW.DFSR, bytes(4))
        for r, v in ((UC_ARM_REG_R4, 0x4444), (UC_ARM_REG_R5, 0x5555), (UC_ARM_REG_R6, 0x6666), (UC_ARM_REG_R7, 0x7777)): e.uc.reg_write(r, v)
        for i in range(2): e.uc.mem_write(DW.DWT_COMP0 + 16 * i + 8, struct.pack("<I", 6))
        e.uc.reg_write(UC_ARM_REG_LR, STOP | 1 | 4); e.uc.reg_write(13, 0x2006F000)
        e.uc.emu_start(L["c_dwmon"] | 1, 0xFFFFFFFF, count=20_000_000)
        regs = [e.uc.reg_read(r) for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)]
        return e.r8(BB.BB + BB.O.ST), bytes(e.uc.mem_read(BB.BB, BB.SIZE)), regs

    st, raw, regs = mon([v for _, v in WATCH])
    check(st == 0 and rd(DW.DWT_COMP0 + 8) == 6 and rd(DW.DWT_COMP0 + 24) == 6 and rd(DW.DFSR) == 4 and regs == [0x4444, 0x5555, 0x6666, 0x7777],
          f"both words legit: resume (state {st:#x}, comparators kept, DFSR {rd(DW.DFSR)})")
    for k, bad in ((0, 0x0805AD61), (1, 0x000F0009)):
        words = [v for _, v in WATCH]; words[k] = bad
        st, raw, regs = mon(words)
        check(st & (BB.ST_FROZEN | BB.ST_FAULT) == (BB.ST_FROZEN | BB.ST_FAULT) and struct.pack("<I", 0x0807456A) in raw
              and struct.pack("<I", 0x08070123) in raw, f"word {k} = {bad:#x}: frozen as a fault capture with the writer's PC / LR (state {st:#x})")
        check(rd(DW.DWT_COMP0 + 8) == 0 and rd(DW.DWT_COMP0 + 24) == 0 and rd(DW.DFSR) == 4 and regs == [0x4444, 0x5555, 0x6666, 0x7777],
              "  comparators off, DFSR.DWTTRAP written, r4-r7 kept")
    del e; gc.collect()
    print(f"{man.get('marker')} DWTMANY RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
