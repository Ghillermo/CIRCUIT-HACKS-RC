"""Emulation tests for SC04 (stock vs SC04)."""
from __future__ import annotations
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_shared_channels as base  # noqa: E402
import emu_sc03 as t3  # noqa: E402
from emu_shared_channels import Emu, STORE, SCRATCH  # noqa: E402
from unicorn.arm_const import *  # noqa: E402,F403

P2 = t3.P2
BOTH = 3 << 24


def ch_leds(image, p2, sel=0):
    e = Emu(image)
    t3.set_param(e, 2, p2)
    e.set_channels(base.DEFAULT)
    obj = SCRATCH
    pal = SCRATCH + 0x1000
    for i in range(0x100):
        e.uc.mem_write(pal + 2 * i, struct.pack("<H", i))
    leds = SCRATCH + 0x3000
    e.w32(SCRATCH + 0x2F00, leds)
    e.w32(obj + 4, SCRATCH + 0x2F00); e.w32(obj + 0xC, STORE)
    e.stops = {0x08047490: "done"}
    for r, v in ((UC_ARM_REG_R4, sel), (UC_ARM_REG_R5, pal), (UC_ARM_REG_R7, obj), (UC_ARM_REG_R8, 0)):
        e.uc.reg_write(r, v)
    e.run(0x080473DC)
    return [struct.unpack("<H", e.uc.mem_read(leds + 2 * c, 2))[0] for c in range(16)]


def main(stock, sc04):
    fails = 0
    def check(c, m):
        nonlocal fails
        if not c:
            fails += 1; print("FAIL:", m)
    print("— SC02 regression —"); base.CH16_PAD_TOGGLES = True; fails += base.main(stock, sc04)
    # pads 0x10..0x1f identical to stock (22/23 back to nothing)
    import os
    skip = {int(x, 16) for x in os.environ.get("SKIP_PADS", "").split(",") if x}   # SC10+: 0x15,0x16 are FX toggles
    for pad in range(0x10, 0x20):
        if pad in skip:
            continue
        check(t3.pad_param2(stock, pad) == t3.pad_param2(sc04, pad), f"pad {pad:#x} differs from stock")
    # pad 16 (index 15)
    check(t3.pad_param2(stock, 0x0F) == (None, False), "stock pad 16 should do nothing")
    for before, after in ((P2, P2 | BOTH), (P2 | BOTH, P2), (P2 | 1 << 24, P2), (P2 | 1 << 25, P2 | BOTH)):
        got = t3.pad_param2(sc04, 0x0F, before)
        check(got == (after, True), f"pad16 {before:#x}: {got} expected {after:#x}")
    print("pads: checked")
    # LEDs of channel pads: ch16 red when enabled, unlit when blocked; others identical to stock
    for sel in (0, 2, 0x10):
        s = ch_leds(stock, P2, sel)
        for p2, exp16 in ((P2, 0xCF), (P2 | BOTH, 0x00)):
            p = ch_leds(sc04, p2, sel)
            check(p[:15] == s[:15], f"channel LEDs 1-15 differ sel={sel} p2={p2:#x}")
            check(p[15] == exp16, f"ch16 LED sel={sel} p2={p2:#x}: {p[15]:#x} != {exp16:#x}")
    print("channel LEDs: checked")
    # apply flags: one toggle sets both
    for p2 in (P2, P2 | BOTH):
        s = t3.apply_flags(stock, p2); p = t3.apply_flags(sc04, p2)
        ex = 0x10 if p2 & BOTH else 0
        check(p == (s[0] | ex, s[1] | ex, s[2]), f"apply {p2:#x}: {s} {p}")
    print("apply flags: checked")
    # receive / transmit gates (unchanged from SC03)
    for m in ([0xBF, 74, 10], [0xCF, 3], [0xB0, 74, 10], [0x90, 60, 100], [0xF8]):
        s = t3.receive(stock, 0x0F, m)
        check(t3.receive(sc04, 0x0F, m) == s, f"rx open {bytes(m).hex()}")
        exp = "end" if m[0] in (0xBF,) else s
        check(t3.receive(sc04, 0x1F, m) == exp, f"rx blocked {bytes(m).hex()}")
    for tr in (0, 1, 0x10, 0x20, 0x21):
        s = t3.tx_gate(stock, 0x0F, tr)
        check(t3.tx_gate(sc04, 0x0F, tr) == s, f"tx open {tr:#x}")
        check(t3.tx_gate(sc04, 0x1F, tr) == ("skip" if tr >= 0x20 else s), f"tx blocked {tr:#x}")
    print("rx/tx gates: checked")
    print("SC04 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()) else 0)
