"""SC10 ARM tests (live RAM dump): FX-return toggles in Setup, DSP flag write, LEDs, save mask."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc05 import E, STOP  # noqa: E402

SETUP = 0x20044958
PALETTE = 0x08056464
PERSIST = 0x2003974C
FLAGS = 0xEC                # SC10 flag address in DSP X memory (SC14.2: 0x3A00)


class E10(E):
    def store(self): return self.r32(self.r32(self.r32(0x200069E4)) + 0x54)

    def p2(self):
        self.call(0x0803542C, self.store(), 2); return self.r32(self.uc.reg_read(UC_ARM_REG_R0))

    def set_p2(self, v):
        st = self.store(); self.call(0x080354FA, st, 2); self.w32(self.uc.reg_read(UC_ARM_REG_R0), v); self.call(0x080353C0, st)


def h9(image, p2bits):
    e = E10(image); e.set_p2(e.p2() & ~(3 << 28) | p2bits << 28); w = []
    def h(uc, a, s, d):
        if a == 0x080292F8:
            w.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1) >> 8))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, h); e.call(0x08028EA4)
    return w, e.uc.reg_read(UC_ARM_REG_PC)


def main(stock, img):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    ws, _ = h9(stock, 0)
    for bits in (0, 1, 2, 3):
        w, pc = h9(img, bits)
        check(w[:4] == ws and w[4:] == [(FLAGS, bits)] and pc == STOP, f"H9 bits={bits}: stock writes + X:${FLAGS:X}={bits} {w[4:]}")
    pad_fn = struct.unpack("<I", bytes(E10(img).uc.mem_read(0x0805A98C, 4)))[0] & ~1
    for pad, bit in ((0x15, 28), (0x16, 29)):
        e = E10(img); p0 = e.p2(); marks = []
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: marks.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))) if a == 0x0803BDCC else None)
        e.call(pad_fn, SETUP, pad, 100); p1 = e.p2()
        e.call(pad_fn, SETUP, pad, 100); p2 = e.p2()
        check(p1 == p0 ^ (1 << bit) and p2 == p0 and marks == [(0x20, 48)] * 2, f"Setup pad {pad}: bit {bit} toggles, Audio In group resent ({hex(p0)}->{hex(p1)}->{hex(p2)})")
    for pad in (0x14, 0x17, 0x1F):
        es, e9 = E10(stock), E10(img)
        es.call(pad_fn if False else struct.unpack("<I", bytes(es.uc.mem_read(0x0805A98C, 4)))[0] & ~1, SETUP, pad, 100)
        e9.call(pad_fn, SETUP, pad, 100)
        check(es.p2() == e9.p2(), f"Setup pad {pad}: same param 2 as stock")
    on = struct.unpack("<H", stock[PALETTE + 2 - 0x08010000:PALETTE + 4 - 0x08010000])[0]
    off = struct.unpack("<H", stock[PALETTE + 0x12 - 0x08010000:PALETTE + 0x14 - 0x08010000])[0]
    for bits in (0, 1, 2, 3):
        e = E10(img); e.set_p2(e.p2() & ~(3 << 28) | bits << 28)
        e.call(0x0804758C, SETUP); buf = e.uc.reg_read(UC_ARM_REG_R0)
        l = struct.unpack("<2H", bytes(e.uc.mem_read(buf + 0x2A, 4)))
        exp = (on if bits & 1 else off, on if bits & 2 else off)
        check(l == exp and buf == e.r32(e.r32(SETUP + 4)), f"Setup LEDs pads 22/23 for bits={bits}: {l}")
    def changed(image, xor):
        e = E10(image); cur = e.p2()
        e.call(0x0802D2AC, PERSIST); e.w32(PERSIST + 0x10, cur ^ xor)
        e.call(0x0802D300, PERSIST); return e.uc.reg_read(UC_ARM_REG_R0)
    for xor, exp in ((1 << 28, 1), (1 << 29, 1), (1 << 26, 1), (1 << 30, 0), (1 << 20, 0)):
        check(changed(img, xor) == exp, f"save detector bit {xor.bit_length()-1}: {exp}")
    print("SC10 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()) else 0)
