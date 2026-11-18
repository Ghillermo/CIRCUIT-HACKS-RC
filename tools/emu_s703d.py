"""S703D tests: blackbox.use_memrdw (whole-word reads: n words, the rest zero; the byte reads and the record as before), icache.use_dwt (at the
FPU set-up: TRCENA, the DWT key, CYCCNTENA, the sampler's tables zeroed, the I-cache on, the routine returns), blackbox.use_samp (the SysTick
body counts the running task / a handler and rings the interrupted PC).
    python tools/emu_s703d.py S703D.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
import emu_sc48_8 as S
import emu_sc05 as S5
import rdiag as RD
import blackbox as BB
import icache as IC
a = sys.argv[1:]; fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
img = Path(a[0]).read_bytes(); man = json.loads(Path(a[1]).read_text()); R = man["report"]
check("fmmap" not in R, "the FM map out (room)")
e = S.ET(img, man)
r32 = lambda ad: struct.unpack("<I", bytes(e.uc.mem_read(ad, 4)))[0]
# ---- icache.use_dwt
e.uc.mem_write(IC.SAMP, bytes(range(256)) * 2); e.uc.mem_write(IC.CCR, struct.pack("<I", 0x00040200))
for ad in (IC.DEMCR, IC.DWT_LAR, IC.DWT_CTRL): e.uc.mem_write(ad, bytes(4))
n = [0]; h = e.uc.hook_add(UC_HOOK_CODE, lambda uc, ad, s, d: n.__setitem__(0, n[0] + 1))
e.call(0x0805B790, maxins=5000); e.uc.hook_del(h)
pc = e.uc.reg_read(UC_ARM_REG_PC) & ~1
check(pc == S5.STOP and n[0] < 1000, f"the FPU set-up returns ({n[0]} instructions)")
check(r32(IC.CCR) & (1 << 17) and r32(IC.DEMCR) & (1 << 24) and r32(IC.DWT_LAR) == 0xC5ACCE55 and r32(IC.DWT_CTRL) & 1,
      f"I-cache, TRCENA, the DWT key, CYCCNTENA ({r32(IC.CCR):#x} {r32(IC.DEMCR):#x} {r32(IC.DWT_LAR):#x} {r32(IC.DWT_CTRL):#x})")
check(bytes(e.uc.mem_read(IC.SAMP, IC.SAMP_LEN)) == bytes(IC.SAMP_LEN), "the sampler's tables zeroed")
# ---- memrdw
sent = []
def rt(uc, ad, s, d):
    p = uc.reg_read(UC_ARM_REG_R2); ptr, ln = struct.unpack("<2I", bytes(uc.mem_read(p, 8))); sent.append(bytes(uc.mem_read(ptr, ln)))
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
e.uc.hook_add(UC_HOOK_CODE, rt, begin=RD.ROUTER, end=RD.ROUTER)
sx = int(R["blackbox"]["labels"]["c_bbsx"], 16)
BUF, DESC = 0x2006E000, 0x2006E200
def req(c, addr, nw=0):
    a7 = [(addr >> s) & 0x7F for s in (28, 21, 14, 7, 0)]
    m = bytes([0xF0, 0x7D, 0x43, 0x54, 0x01, 5, c, 0]) + bytes(a7) + bytes([nw]) + bytes(122) + bytes([0xF7])
    e.uc.mem_write(BUF, m); e.uc.mem_write(DESC, struct.pack("<2I", BUF, len(m))); sent.clear()
    e.call(sx, 0, DESC, maxins=2_000_000)
    r = sent[-1]; q = r[8:-1]; return bytes(q[i] << 4 | q[i + 1] for i in range(0, 128, 2))
want = bytes(e.uc.mem_read(0x20042980, 64))
check(req(0, 0x20042980) == want, "byte reads: 64 bytes as before")
check(req(0, 0x20042980, 3) == want[:12] + bytes(52), "3 words: those 12 bytes, the rest zero")
check(req(0, 0x20042980, 16) == want, "16 words: the 64 bytes")
e.uc.mem_write(0x40023800, struct.pack("<4I", 0x11, 0x22, 0x33, 0x44))
check(req(0, 0x40023800, 4)[:16] == struct.pack("<4I", 0x11, 0x22, 0x33, 0x44), "a peripheral block by words")
check(req(0, 0) == bytes(e.uc.mem_read(BB.BB, 64)), "no address: the record, as before")
# ---- use_samp
sysc = int(R["blackbox"]["labels"]["c_bbsysc"], 16)
FR = 0x2006E400
e.uc.mem_write(IC.SAMP, bytes(IC.SAMP_LEN))
def tick(tcb, pc, exc_ret, ipsr=0):
    e.uc.mem_write(BB.CUR_TCB, struct.pack("<I", tcb)); e.uc.mem_write(FR, struct.pack("<8I", 0, 0, 0, 0, 0, 0, pc, 0x01000000 | ipsr))
    e.call(sysc, 0, exc_ret, FR, maxins=200_000)
for k in range(5): tick(0x20012340, 0x08020000 + 2 * k, 0xFFFFFFFD)
for k in range(2): tick(0x20012400, 0x08030000, 0xFFFFFFFD)
tick(0x20012340, 0x08040000, 0xFFFFFFF1, 0x2A)
tab = struct.unpack("<34I", bytes(e.uc.mem_read(IC.SAMP, 136)))
slots = {tab[2 + 2 * i]: tab[3 + 2 * i] for i in range(16) if tab[2 + 2 * i]}
check(tab[0] == 8 and tab[1] == 8, f"8 samples, the ring index 8 ({tab[0]}, {tab[1]})")
check(slots == {0x20012340: 5, 0x20012400: 2, 0x12A: 1}, f"per task / handler: {[(hex(x), y) for x, y in slots.items()]}")
ring = struct.unpack("<8I", bytes(e.uc.mem_read(IC.SAMP + 0x100, 32)))
check(list(ring) == [0x08020000 + 2 * k for k in range(5)] + [0x08030000] * 2 + [0x08040000], f"the PC ring {[hex(x) for x in ring]}")
print("S703D RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
