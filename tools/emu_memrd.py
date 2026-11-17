"""S564D4 tests: blackbox.use_memrd (the read command with an address reads that memory; without one, the record as before), fmmap left out, the
MPU / DMA watches installed (their own tests: emu_mpuwatch.py / emu_dmawatch.py on this image).
    python tools/emu_memrd.py S564D4.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
import emu_sc48_8 as S
import rdiag as RD
import blackbox as BB
a = sys.argv[1:]; fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
man = json.loads(Path(a[1]).read_text()); R = man["report"]
drop = {"S564D4": "fmmap", "S564D5": "knobhold"}.get(man.get("marker"))
check(drop not in R and "mpuwatch" in R and "dmawatch" in R, f"{drop} out, the watches in")
e = S.ET(Path(a[0]).read_bytes(), man)
sent = []
def rt(uc, ad, s, d):
    p = uc.reg_read(UC_ARM_REG_R2); ptr, n = struct.unpack("<2I", bytes(uc.mem_read(p, 8))); sent.append(bytes(uc.mem_read(ptr, n)))
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
e.uc.hook_add(UC_HOOK_CODE, rt, begin=RD.ROUTER, end=RD.ROUTER)
sx = int(R["blackbox"]["labels"]["c_bbsx"], 16)
BUF, DESC = 0x2006E000, 0x2006E200
def req(c, addr):
    a7 = [(addr >> s) & 0x7F for s in (28, 21, 14, 7, 0)]
    m = bytes([0xF0, 0x7D, 0x43, 0x54, 0x01, 5, c, 0]) + bytes(a7) + bytes(123) + bytes([0xF7])
    e.uc.mem_write(BUF, m); e.uc.mem_write(DESC, struct.pack("<2I", BUF, len(m))); sent.clear()
    e.call(sx, 0, DESC, maxins=2_000_000)
    r = sent[-1]; n = r[8:-1]; return bytes(n[i] << 4 | n[i + 1] for i in range(0, 128, 2))
want = bytes(e.uc.mem_read(0x20042980, 64))
check(req(0, 0x20042980) == want, "address 0x20042980, chunk 0: those 64 bytes")
check(req(1, 0x20042980) == bytes(e.uc.mem_read(0x200429C0, 64)), "chunk 1: the next 64")
check(req(0, 0) == bytes(e.uc.mem_read(BB.BB, 64)), "no address: the record, as before")
print("S564D4 MEMRD RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
