"""Capture the ARM->DSP SHI word stream (on the running-firmware dump) and decode it into DSP memory writes.

The DSP core-0 SHI ISR (P:$156) protocol: with the command pin high a word is a command
(bit21 -> x:$12, bit22 read, bit19 -> 18-bit address keeping the space, else 15-bit address
with bit15 = Y space); with the pin low each word is data written to x/y:(x:$10)+.
"""
from __future__ import annotations
import sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc05 import E  # noqa: E402

CMD_ON, CMD_OFF, CS_ON, CS_OFF = 0x08029190, 0x080291A2, 0x080291B8, 0x080291CA
SPI_XFER = 0x08037960          # (spi, tx, rx, n): polled byte transfer; 3 bytes per DSP word
NOPS = (0x0803B9D8, 0x0803BAD6, 0x0803BADA)


class Shi:
    def __init__(self):
        self.st = {0: dict(cmd=False, x10=0, x11=0), 1: dict(cmd=False, x10=0, x11=0)}
        self.core = 0
        self.writes = []            # (core, space, addr, value)
        self.raw = []

    def word(self, w):
        c = self.st[self.core]; self.raw.append((self.core, c["cmd"], w))
        if c["cmd"]:
            if w & (1 << 21): self.writes.append((self.core, "x", 0x12, w))
            elif w & (1 << 22): pass
            elif w & (1 << 20): c["x10"] = ((w << 8) - 2) & 0xFFFFFF
            elif w & (1 << 19): c["x10"] = w & 0x3FFFF
            else: c["x11"] = w; c["x10"] = w & 0x7FFF
        else:
            sp = "y" if c["x11"] & 0x8000 else "x"
            self.writes.append((self.core, sp, c["x10"], w)); c["x10"] = (c["x10"] + 1) & 0xFFFFFF


def attach(e: E) -> Shi:
    s = Shi()
    for a, n in list(e.stubs.items()):
        if n == "sound": del e.stubs[a]        # let the note reach the DSP driver (keep the semaphore stub)
    def h(uc, a, sz, d):
        r0 = uc.reg_read(UC_ARM_REG_R0)
        if a in (CMD_ON, CMD_OFF, CS_ON, CS_OFF):
            s.core = 0 if r0 == 0 else 1
            if a == CMD_ON: s.st[s.core]["cmd"] = True
            elif a == CMD_OFF: s.st[s.core]["cmd"] = False
        elif a == SPI_XFER:
            tx, rx, n = uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3) & 0xFFFF
            b = bytes(uc.mem_read(tx, n))
            for i in range(0, n - 2, 3): s.word(int.from_bytes(b[i:i + 3], "big"))
            if rx: uc.mem_write(rx, bytes(n))
        elif a not in NOPS:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, h)
    return s
