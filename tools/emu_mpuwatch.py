"""S564D2 tests (tools/mpuwatch.py), the parts Unicorn runs (it has no MPU): the first LED frame sets SHCSR.MEMFAULTENA, MPU region 0 = 0x20042980
read-only (RASR), MPU_CTRL = ENABLE | PRIVDEFENA, once; the LED frame = Beta 5.64's.
    python tools/emu_mpuwatch.py S564D2.bin manifest.json B5.64.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R4
import emu_sc48_8 as S
import mpuwatch as MW
from emu_sc35 import MGR
from emu_sc05 import STOP


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
    return bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))


a = sys.argv[1:]
fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
e = S.ET(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()))
e.uc.mem_write(MW.MW, bytes(8))
for r in (MW.MPU_CTRL, MW.MPU_RNR, MW.MPU_RBAR, MW.MPU_RASR): e.uc.mem_write(r, bytes(4))
e.uc.mem_write(MW.SHCSR, struct.pack("<I", 0x60000))
f = frame(e)
rd = e.r32
check(rd(MW.SHCSR) == 0x70000 and rd(MW.MPU_RNR) == 0 and rd(MW.MPU_RBAR) == MW.REGION and rd(MW.MPU_RASR) == MW.RASR and rd(MW.MPU_CTRL) == 5,
      f"armed: SHCSR {rd(MW.SHCSR):#x}, RBAR {rd(MW.MPU_RBAR):#x}, RASR {rd(MW.MPU_RASR):#x}, CTRL {rd(MW.MPU_CTRL)}")
e.uc.mem_write(MW.MPU_CTRL, bytes(4)); frame(e)
check(rd(MW.MPU_CTRL) == 0, "only once")
p = S.ET(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()))
check(f == frame(p), "the LED frame = Beta 5.64's")
print("S564D2 MPUWATCH RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
