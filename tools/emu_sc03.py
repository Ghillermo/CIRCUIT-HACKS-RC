"""Emulation tests for SC03 hooks (stock vs SC03), reusing the SC02 harness."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_shared_channels as base  # noqa: E402
from emu_shared_channels import Emu, STORE, SCRATCH, make_param_store  # noqa: E402
from unicorn.arm_const import *  # noqa: E402,F403

LR_SENTINEL = 0x0807FF00          # erased flash in the cave image area: never executed, used as stop


def pending_param(e, idx):
    if not (e.r32(STORE + 8) >> idx) & 1:
        return None
    front = (e.r32(STORE + 4) >> idx) & 1
    return e.r32(e.r32(STORE + 0xC + 4 * (front ^ 1)) + idx * 4)


def set_param(e, idx, val):
    for buf in (e.r32(STORE + 0xC), e.r32(STORE + 0x10)):
        e.w32(buf + idx * 4, val)
    e.w32(STORE + 8, 0)


P2 = 0x0003281E                     # param 2 as found in the RAM dump (all toggles on)


# ---- pads 0x10..0x1f
def pad_param2(image, pad, p2=P2):
    e = Emu(image)
    set_param(e, 2, p2)
    obj = SCRATCH
    sel = make_param_store(e, SCRATCH + 0x100, [0])
    e.uc.mem_write(obj, bytes(0x40))
    e.w32(obj + 0x0C, STORE); e.w32(obj + 0x10, sel); e.w32(obj + 0x20, 0xDEAD0000)
    e.stubs[0x080353C0] = "commit"
    e.stops = {0x080470EA: "refresh", 0x08046E66: "return"}
    e.uc.reg_write(UC_ARM_REG_R0, obj); e.uc.reg_write(UC_ARM_REG_R1, pad)
    e.uc.reg_write(UC_ARM_REG_LR, 0x08046E66 | 1)
    e.run(0x08046DF0)
    return pending_param(e, 2), ("commit" in e.calls)


# ---- settings -> MIDI flags
def apply_flags(image, p2):
    e = Emu(image)
    set_param(e, 2, p2)
    obj, rx, rxarr, rxx, tx, txarr = (SCRATCH + o for o in (0x0, 0x200, 0x300, 0x400, 0x500, 0x600))
    e.uc.mem_write(SCRATCH, bytes(0x800))
    e.w32(obj + 0x54, STORE); e.w32(obj + 0x18, rx); e.w32(obj + 0x1C, tx)
    e.w32(rx + 8, rxarr); e.w32(rx + 4, rxx)
    e.w32(tx + 0x0C, txarr)
    e.stops = {LR_SENTINEL: "done"}
    e.uc.reg_write(UC_ARM_REG_R0, obj); e.uc.reg_write(UC_ARM_REG_LR, LR_SENTINEL | 1)
    e.run(0x08034F68)
    return e.r8(rxarr + 0x14), e.r8(tx + 0x18), e.r8(tx + 0x19)


# ---- receive dispatcher
RX_STOPS = {0x080518A0: "cc->param", 0x08051884: "cc->drum-select", 0x080518C6: "pc",
            0x080517CC: "note-on", 0x080517F0: "note-off", 0x08051820: "all-notes-off",
            0x08051748: "realtime", 0x08051756: "realtime", 0x08051764: "realtime", 0x08051772: "realtime",
            0x08051780: "spp", 0x08051796: "song-select", 0x080518F0: "end"}


def receive(image, flags, msg):
    e = Emu(image)
    A = SCRATCH
    e.uc.mem_write(A, bytes(0x40))
    e.w32(A, SCRATCH + 0x100); e.w32(A + 0x10, SCRATCH + 0x200)
    e.uc.mem_write(A + 4, bytes([0, 1, 2, 3, 9, 0, 1, 9, 15, 15]))
    e.uc.mem_write(A + 0x14, bytes([flags]))
    m = SCRATCH + 0x300
    e.uc.mem_write(m, bytes(msg) + bytes(4))
    e.stops = RX_STOPS
    e.uc.reg_write(UC_ARM_REG_R0, A); e.uc.reg_write(UC_ARM_REG_R1, m)
    e.uc.reg_write(UC_ARM_REG_LR, LR_SENTINEL | 1)
    return e.run(0x08051720)


# ---- CC/NRPN transmit gate
def tx_gate(image, flags, track):
    e = Emu(image)
    t = SCRATCH
    e.uc.mem_write(t, bytes(0x40))
    e.uc.mem_write(t + 0x18, bytes([flags, 0x7F]))
    e.w32(t + 0x10, SCRATCH + 0x100)
    e.stops = {0x0803BF4C: "send", LR_SENTINEL: "skip"}
    e.uc.reg_write(UC_ARM_REG_R0, t); e.uc.reg_write(UC_ARM_REG_R1, 7)
    e.uc.reg_write(UC_ARM_REG_R2, track); e.uc.reg_write(UC_ARM_REG_R3, 5)
    e.uc.reg_write(UC_ARM_REG_LR, LR_SENTINEL | 1)
    sp = 0x2006F000
    e.uc.mem_write(sp, struct.pack("<I", 100))
    e.result = None
    e.uc.reg_write(UC_ARM_REG_SP, sp)
    e.uc.emu_start(0x0802A000 | 1, 0xFFFFFFFF, count=5000)
    return e.result


# ---- toggle LEDs
def toggle_leds(image, p2, pop_addr):
    e = Emu(image)
    set_param(e, 2, p2)
    view = SCRATCH
    pal = SCRATCH + 0x1000
    for i in range(0x200):
        e.uc.mem_write(pal + 2 * i, struct.pack("<H", i))
    leds = SCRATCH + 0x3000
    e.uc.mem_write(leds, bytes(0x80))
    e.w32(SCRATCH + 0x2F00, leds)
    e.w32(view + 4, SCRATCH + 0x2F00); e.w32(view + 0xC, STORE)
    e.stops = {pop_addr: "done"}
    e.uc.reg_write(UC_ARM_REG_R4, pal); e.uc.reg_write(UC_ARM_REG_R5, view)
    e.stubs[0x0804AA40] = "set-led"          # pad 24/25 helper (stock) — not under test
    e.run(0x080471C2)
    return [struct.unpack("<H", e.uc.mem_read(leds + 2 * i, 2))[0] for i in range(0x20)]


def main(stock, sc03, cave_pop):
    fails = 0

    def check(c, msg):
        nonlocal fails
        if not c:
            fails += 1
            print("FAIL:", msg)

    # 1) SC02 regression on SC03 image
    print("— SC02 regression —")
    fails += base.main(stock, sc03)

    # 2) pads 0x10..0x1f
    for pad in range(0x10, 0x20):
        s = pad_param2(stock, pad)
        p = pad_param2(sc03, pad)
        if pad in (0x15, 0x16):
            bit = 1 << (24 + pad - 0x15)
            check(s == (None, False), f"stock pad {pad:#x} should do nothing: {s}")
            check(p == (P2 ^ bit, True), f"SC03 pad {pad:#x}: {p}")
            p2 = pad_param2(sc03, pad, P2 ^ bit)              # second press toggles back
            check(p2 == (P2, True), f"SC03 pad {pad:#x} toggle back: {p2}")
        else:
            check(s == p, f"pad {pad:#x} differs: stock {s} sc03 {p}")
    print("pads 0x10-0x1f: checked")

    # 3) apply flags
    for extra in (0, 1 << 24, 1 << 25, 3 << 24):
        for p2 in (P2, 0, 0xFFFF & ~0):
            s = apply_flags(stock, p2 | extra)
            p = apply_flags(sc03, p2 | extra)
            exp_rx = s[0] | (0x10 if extra & (1 << 24) else 0)
            exp_tx = s[1] | (0x10 if extra & (1 << 25) else 0)
            check(p == (exp_rx, exp_tx, s[2]), f"apply p2={p2 | extra:#x}: stock {s} sc03 {p}")
    print("apply flags: checked")

    # 4) receive dispatcher
    msgs = [[0xB0, 74, 10], [0xBF, 74, 10], [0xBF, 99, 1], [0xCF, 3], [0xC0, 5], [0x9F, 60, 100], [0x90, 60, 100],
            [0x89, 60, 0], [0xB9, 8, 3], [0xEF, 0, 64], [0xBF, 123, 0], [0xF8], [0xFA], [0xF2, 1, 0], [0xBE, 74, 1]]
    for flags in (0x0F, 0x0B, 0x0D, 0x07):
        for m in msgs:
            s = receive(stock, flags, m)
            p_open = receive(sc03, flags, m)
            p_block = receive(sc03, flags | 0x10, m)
            check(s == p_open, f"rx open flags={flags:#x} {bytes(m).hex()}: stock {s} sc03 {p_open}")
            ch16_nonpc = 0x80 <= m[0] < 0xF0 and (m[0] & 0x0F) == 0x0F and (m[0] & 0xF0) != 0xC0
            exp = "end" if ch16_nonpc else s
            check(p_block == exp, f"rx blocked flags={flags:#x} {bytes(m).hex()}: got {p_block}, expected {exp}")
    print("receive dispatcher: checked")

    # 5) transmit gate
    for flags in (0x0F, 0x0D, 0x00):
        for track in (0, 1, 0x10, 0x20, 0x21):
            s = tx_gate(stock, flags, track)
            check(tx_gate(sc03, flags, track) == s, f"tx open flags={flags:#x} id={track:#x}")
            b = tx_gate(sc03, flags | 0x10, track)
            exp = "skip" if track in (0x20, 0x21) else s
            check(b == exp, f"tx blocked flags={flags:#x} id={track:#x}: {b} != {exp}")
    print("transmit gate: checked")

    # 6) LEDs
    for extra in (0, 1 << 24, 1 << 25, 3 << 24):
        s = toggle_leds(stock, P2 | extra, 0x080472E0)
        p = toggle_leds(sc03, P2 | extra, cave_pop)
        check(s[:0x15] == p[:0x15] and s[0x17:] == p[0x17:], f"LEDs other pads differ (extra={extra:#x})")
        exp22 = 0x1A // 2 if extra & (1 << 24) else 0x0A // 2
        exp23 = 0x1A // 2 if extra & (1 << 25) else 0x0A // 2
        check(p[0x15] == exp22 and p[0x16] == exp23, f"LEDs pads 22/23 extra={extra:#x}: {p[0x15]}, {p[0x16]}")
        check(p[0x1A] == 0x0A // 2, "CC Rx pad colour reference")       # P2 has CC Rx on -> same palette entry
    print("LEDs: checked")
    print("SC03 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    import json
    stock = Path(sys.argv[1]).read_bytes()
    sc03 = Path(sys.argv[2]).read_bytes()
    man = json.loads(Path(sys.argv[3]).read_text())
    lab = man["report"]["cave"]["labels"]
    listing = man["report"]["cave"]["listing"]
    # address of the pop.w inside c_led
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB | capstone.CS_MODE_MCLASS)
    c0 = int(man["report"]["cave"]["start"], 16)
    code = sc03[c0 - 0x08010000:c0 - 0x08010000 + man["report"]["cave"]["size"]]
    pop = [i.address for i in md.disasm(code, c0) if i.mnemonic == "pop.w"][0]
    sys.exit(1 if main(stock, sc03, pop) else 0)
