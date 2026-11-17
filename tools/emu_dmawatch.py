"""S564D3 tests (tools/dmawatch.py): intact word = nothing, the frame count goes up, the LED frame = Beta 5.64's; the word changed = the next frame
freezes the black box (state MANUAL | 0x80) and writes at BB + O.STK1: the frame count, the word, then the 16 DMA streams' NDTR, M0AR, CR, PAR (fake
registers here); once.
    python tools/emu_dmawatch.py S564D3.bin manifest.json B5.64.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R4
import emu_sc48_8 as S
import dmawatch as DW
import blackbox as BB
from emu_sc35 import MGR
from emu_sc05 import STOP


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
    return bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))


a = sys.argv[1:]; fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
man = json.loads(Path(a[1]).read_text())
DW.DM = {"S564D4": 0x2004FB00, "S564D5": 0x2004F900}.get(man.get("marker"), DW.DM)              # (S564D4 moves it: dspz.add keeps only the labels in the report)
e = S.ET(Path(a[0]).read_bytes(), man)
e.uc.mem_write(DW.DM, bytes(12)); e.uc.mem_write(BB.BB + BB.O.ST, bytes([0]))
for ctl in (DW.DMA1, DW.DMA2):
    for s in range(8):
        base = ctl + 0x10 + 0x18 * s; tag = (ctl >> 8 & 0xF) << 4 | s
        e.uc.mem_write(base, struct.pack("<4I", 0xC0000 | tag, 0x100 + tag, 0x40000000 | tag, 0x20000000 | tag))   # CR, NDTR, PAR, M0AR
f = frame(e); frame(e)
check(e.r32(DW.DM + 8) == 2 and e.r8(BB.BB + BB.O.ST) == 0, f"intact: nothing, frames counted ({e.r32(DW.DM + 8)})")
p = S.ET(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()))
check(f == frame(p), "the LED frame = Beta 5.64's")
e.w32(DW.WATCH[0][0], 0x000F0009); frame(e)
o = bytes(e.uc.mem_read(DW.OUT, 8 + 256))
st = e.r8(BB.BB + BB.O.ST)
ent = [struct.unpack_from("<4I", o, 8 + 16 * i) for i in range(16)]
exp = [(0x100 + t, 0x20000000 | t, 0xC0000 | t, 0x40000000 | t) for ctl in (DW.DMA1, DW.DMA2) for t in [((ctl >> 8 & 0xF) << 4 | s) for s in range(8)]]
check(st == DW.STATE and struct.unpack_from("<2I", o) == (3, 0x000F0009) and ent == exp, f"changed: frozen ({st:#x}), frame 3, the word, the 16 streams ({ent[0]}, {ent[15]})")
e.w32(DW.WATCH[0][0], 0x11111111); e.uc.mem_write(BB.BB + BB.O.ST, bytes([0])); frame(e)
check(e.r8(BB.BB + BB.O.ST) == 0, "once")
print("S564D3 DMAWATCH RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
