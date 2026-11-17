"""Beta 5.65 tests (tools/paintguard.py), against Beta 5.64:
  * MIDI 2's probability view, its listener through the vtable (stepmod's c_rfled): a selected step with notes and probability 255 / 40: no write past
    its 16-pad buffer (5.64: the 16 colours caught on the device); probabilities 0..7: the buffer and everything around it as in 5.64;
  * Drum 4's velocity bar (class C) listener with the store's velocity 200: nothing past its buffer (5.64: overrun); velocities 0..127: as in 5.64.
    python tools/emu_paintguard.py B5.65.bin manifest.json B5.64.bin manifest.json"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R0
import emu_sc48_8 as S
import packio as PK

V, C3 = 0x20042944, 0x200435c4                          # MIDI 2's probability view; Drum 3's velocity bar (its buffer ends at Drum 4's object)


def run(img, man):
    e = S.ET(img, man); out = {}
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    st = e.r32(e.r32(V + 0xC) + 8); p = r0(PK.PARAM_GET, st, 0); arr = e.r32(e.r32(V + 4))
    slot8 = e.r32(e.r32(V) + 32) & ~1
    around = lambda a: bytes(e.uc.mem_read(a, 96))
    orig = bytes(e.uc.mem_read(p, 2)); base = around(arr)
    for prob in (255, 40, 0, 3, 7):
        e.uc.mem_write(arr, base); e.uc.mem_write(p, bytes([1, prob])); r0(slot8, V, st); out[("prob", prob)] = around(arr)
    e.uc.mem_write(p, orig); e.uc.mem_write(arr, base)
    # the velocity bar: its listener thunk (slot 0 of the listener vtable at + 8) with store1 = [bar + 0xC], the velocity = param 1 of store1
    STEP = 5
    s1 = e.r32(C3 + 0xC); vp = r0(0x0803542C, s1, STEP >> 2) + (STEP & 3); varr = e.r32(e.r32(C3 + 4)); vbase = around(varr); vorig = e.r8(vp)
    R = man["report"]; ent = int(R["paintguard"]["labels"]["c_vg"], 16) if "paintguard" in R else 0x0804EF0E   # the painter's entry (guarded / stock)
    for vel in (200, 129, 0, 64, 127):
        e.uc.mem_write(varr, vbase); e.uc.mem_write(vp, bytes([vel])); r0(ent, C3, STEP); out[("vel", vel)] = around(varr)
    e.uc.mem_write(vp, bytes([vorig]))
    return out


a = sys.argv[1:]; fails = 0
def check(c, m):
    global fails
    print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
new = run(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()))
old = run(Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()))
for k in (("prob", 255), ("prob", 40), ("vel", 200), ("vel", 129)):
    check(new[k][32:] == old[("prob" if k[0] == "prob" else "vel", 0)][32:] and old[k][32:] != old[(k[0], 0)][32:],
          f"{k}: nothing past the 16-pad buffer (5.64 overran: {old[k][32:48].hex()})")
for k in (("prob", 0), ("prob", 3), ("prob", 7), ("vel", 0), ("vel", 64), ("vel", 127)):
    check(new[k] == old[k], f"{k}: painted as in 5.64")
print("B5.65 PAINTGUARD RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES"); sys.exit(1 if fails else 0)
