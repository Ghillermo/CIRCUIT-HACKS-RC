"""Emulate the three patched routines (stock vs patched) with Unicorn.

Uses the real 512 KB flash dump (bootloader + app) and the real 320 KB RAM dump
from userx14's repo, so helper functions (parameter store getters/setters) run
for real against the real settings store at 0x200111CC.  The app region of the
flash dump is replaced with the image under test.
"""

from __future__ import annotations

import itertools
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
FLASH = (ROOT / "ctre/Firmware-Analysis/dumpCT_flash_0x08000000.bin").read_bytes()
RAM = (ROOT / "ctre/Firmware-Analysis/dumpCT_ram_0x20000000.bin").read_bytes()
STORE = 0x200111CC
SCRATCH = 0x20060000          # extra RAM for synthetic objects (outside real SRAM)
STACK_TOP = 0x20070000
IDX = {0: 3, 1: 4, 2: 5, 3: 6, 0x10: 7}   # track id -> settings index
TRACKS = [0, 1, 2, 3, 0x10]
NAMES = {0: "S1", 1: "S2", 2: "M1", 3: "M2", 0x10: "DR"}


class Emu:
    def __init__(self, image: bytes):
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        flash = bytearray(FLASH)
        flash[0x10000:0x10000 + len(image)] = image
        uc.mem_map(0x08000000, 0x80000)
        uc.mem_write(0x08000000, bytes(flash))
        uc.mem_map(0x20000000, 0x50000)
        uc.mem_write(0x20000000, RAM)
        uc.mem_map(SCRATCH, 0x10000)
        self.stops = {}
        self.stubs = {}
        self.calls = []
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)

    def _unmapped(self, uc, access, addr, size, value, data):
        raise RuntimeError(f"unmapped access {addr:#x} at pc {uc.reg_read(UC_ARM_REG_PC):#x}")

    def _code(self, uc, addr, size, data):
        if addr in self.stubs:
            self.calls.append(self.stubs[addr])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        elif addr in self.stops:
            self.result = self.stops[addr]
            uc.emu_stop()

    def w32(self, a, v): self.uc.mem_write(a, struct.pack("<I", v))
    def r32(self, a): return struct.unpack("<I", self.uc.mem_read(a, 4))[0]
    def r8(self, a): return self.uc.mem_read(a, 1)[0]

    # settings store helpers (double buffered, 4 bytes per parameter)
    def set_channels(self, chans: dict):
        for buf in (self.r32(STORE + 0xC), self.r32(STORE + 0x10)):
            for tid, ch in chans.items():
                self.w32(buf + IDX[tid] * 4, ch)
        self.w32(STORE + 8, 0)                      # clear dirty mask

    def pending(self, tid):
        """value written (not yet committed) for a track, or None"""
        idx = IDX[tid]
        if not (self.r32(STORE + 8) >> idx) & 1:
            return None
        front = (self.r32(STORE + 4) >> idx) & 1
        buf = self.r32(STORE + 0xC + 4 * (front ^ 1))
        return self.r8(buf + idx * 4)

    def run(self, start, max_ins=20000):
        self.result = None
        self.uc.reg_write(UC_ARM_REG_SP, STACK_TOP - 0x100)
        self.uc.emu_start(start | 1, 0xFFFFFFFF, count=max_ins)
        if self.result is None:
            raise RuntimeError("did not reach a stop point")
        return self.result


def make_param_store(emu, base, values):
    """Synthetic single-buffer store: [4]=mask 0, [8]=dirty 0, [0xc]=buf, [0x10]=buf."""
    buf = base + 0x40
    emu.w32(base + 4, 0); emu.w32(base + 8, 0)
    emu.w32(base + 0xC, buf); emu.w32(base + 0x10, buf)
    for i, v in enumerate(values):
        emu.w32(buf + 4 * i, v)
    return base


# ---------------------------------------------------------------- A: pad handler
def pad_press(image, chans, sel_pad, ch):
    e = Emu(image)
    e.set_channels(chans)
    obj = SCRATCH
    sel = make_param_store(e, SCRATCH + 0x100, [sel_pad])
    e.uc.mem_write(obj, bytes(0x40))
    e.w32(obj + 0x0C, STORE); e.w32(obj + 0x10, sel); e.w32(obj + 0x20, 0xDEAD0000)
    e.stubs[0x080353C0] = "commit"
    e.stops = {0x080470EA: "refresh", 0x08046E66: "return"}
    e.uc.reg_write(UC_ARM_REG_R0, obj); e.uc.reg_write(UC_ARM_REG_R1, ch)
    e.uc.reg_write(UC_ARM_REG_LR, 0x08046E66 | 1)
    e.run(0x08046DF0)
    tid = sel_pad if sel_pad < 4 else 0x10
    return ("accepted" if "commit" in e.calls else "rejected"), e.pending(tid)


# ---------------------------------------------------------------- B: LED colours
def led_colours(image, chans, sel_tid):
    e = Emu(image)
    e.set_channels(chans)
    obj = SCRATCH
    palette = SCRATCH + 0x1000                      # palette[i] = i -> buffer holds colour index
    for i in range(0x100):
        e.uc.mem_write(palette + 2 * i, struct.pack("<H", i))
    leds = SCRATCH + 0x3000
    holder = SCRATCH + 0x2F00
    e.w32(holder, leds)
    e.w32(obj + 0x4, holder); e.w32(obj + 0xC, STORE)
    e.stops = {0x08047490: "done"}
    for r, v in ((UC_ARM_REG_R4, sel_tid), (UC_ARM_REG_R5, palette), (UC_ARM_REG_R7, obj), (UC_ARM_REG_R8, 0)):
        e.uc.reg_write(r, v)
    e.run(0x080473DC)
    return [struct.unpack("<H", e.uc.mem_read(leds + 2 * c, 2))[0] for c in range(16)]


# ---------------------------------------------------------------- C: validator
def validate(image, chans):
    e = Emu(image)
    e.set_channels(chans)
    e.stops = {0x08046DA6: "reset", 0x08046DE2: "ok"}
    for r, v in ((UC_ARM_REG_R9, STORE), (UC_ARM_REG_R6, 0x8000), (UC_ARM_REG_R7, 0)):
        e.uc.reg_write(r, v)
    return e.run(0x08046D7A)


DEFAULT = {0: 0, 1: 1, 2: 2, 3: 3, 0x10: 9}
CH16_PAD_TOGGLES = False   # SC04+: pad 16 commits the Ch16 toggle (channel itself never changes)


def main(stock, patched):
    fails = 0

    def check(cond, msg):
        nonlocal fails
        if not cond:
            fails += 1
            print("FAIL:", msg)

    # A — exhaustive over 9 selected pads x 16 channels, default + a shared config
    configs = [DEFAULT, {0: 0, 1: 1, 2: 0, 3: 1, 0x10: 9}, {0: 5, 1: 6, 2: 5, 3: 5, 0x10: 14}]
    n = 0
    for chans in configs:
        for sel_pad, ch in itertools.product(range(9), range(16)):
            tid = sel_pad if sel_pad < 4 else 0x10
            got = pad_press(patched, chans, sel_pad, ch)
            if ch >= 15:
                exp = ("accepted", None) if CH16_PAD_TOGGLES else ("rejected", None)
            elif tid in (2, 3):
                exp = ("accepted", ch)
            elif ch in (chans[0], chans[1], chans[0x10]):
                exp = ("rejected", None)
            else:
                exp = ("accepted", ch)
            check(got == exp, f"A cfg={chans} pad={sel_pad} ch={ch}: got {got} expected {exp}")
            if chans is DEFAULT:            # stock reference: any used channel rejected
                s = pad_press(stock, chans, sel_pad, ch)
                s_exp = ("rejected", None) if ch >= 15 or ch in chans.values() else ("accepted", ch)
                check(s == s_exp, f"A-stock pad={sel_pad} ch={ch}: got {s} expected {s_exp}")
            n += 1
    print(f"A pad handler: {n} cases")

    # B — colours: patched must equal stock when channels are unique; shared shows selected bright
    bright = {0: 1, 1: 2, 2: 3, 3: 4, 0x10: 5}
    dim = {0: 9, 1: 10, 2: 11, 3: 12, 0x10: 13}
    for chans in (DEFAULT, {0: 4, 1: 7, 2: 0, 3: 12, 0x10: 9}):
        for tid in TRACKS:
            check(led_colours(stock, chans, tid) == led_colours(patched, chans, tid),
                  f"B unique cfg {chans} sel {NAMES[tid]} differs from stock")
    shared = {0: 0, 1: 1, 2: 0, 3: 1, 0x10: 9}
    for tid in TRACKS:
        cols = led_colours(patched, shared, tid)
        for ch in range(16):
            owners = [t for t in TRACKS if shared[t] == ch]
            if ch == 15:
                exp = 0xCF
            elif tid in owners:
                exp = bright[tid]
            elif owners:
                exp = dim[owners[0]]
            else:
                exp = dim[tid]                      # stock default for a free channel
            check(cols[ch] == exp, f"B shared sel {NAMES[tid]} ch{ch + 1}: {cols[ch]:#x} != {exp:#x}")
    print("B LED colours: checked")

    # C — validator
    cases = [
        (DEFAULT, "ok", "ok"),
        ({0: 0, 1: 1, 2: 0, 3: 3, 0x10: 9}, "reset", "ok"),     # M1 shares S1
        ({0: 0, 1: 1, 2: 0, 3: 1, 0x10: 9}, "reset", "ok"),     # M1=S1, M2=S2
        ({0: 0, 1: 1, 2: 9, 3: 9, 0x10: 9}, "reset", "ok"),     # both MIDI on drums
        ({0: 0, 1: 0, 2: 2, 3: 3, 0x10: 9}, "reset", "reset"),  # S1=S2 still invalid
        ({0: 0, 1: 1, 2: 2, 3: 3, 0x10: 0}, "reset", "reset"),  # drums=S1 still invalid
        ({0: 0, 1: 1, 2: 15, 3: 3, 0x10: 9}, "reset", "reset"),  # project channel
        ({0: 0, 1: 1, 2: 2, 3: 16, 0x10: 9}, "reset", "reset"),  # out of range
        ({0: 15, 1: 1, 2: 2, 3: 3, 0x10: 9}, "reset", "reset"),
    ]
    for chans, s_exp, p_exp in cases:
        check(validate(stock, chans) == s_exp, f"C stock {chans}")
        check(validate(patched, chans) == p_exp, f"C patched {chans}")
    print(f"C validator: {len(cases)} cases")
    print("RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    stock = Path(sys.argv[1]).read_bytes()
    patched = Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(stock, patched) else 0)
