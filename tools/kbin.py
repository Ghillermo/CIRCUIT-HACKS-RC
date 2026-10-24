"""RC2.08 / SC46.3 (a fix, the RC and the beta; a user, brought by the user, 2026-10-24: «el teclado externo no reproduce notas en sintes MIDI (aunque
sí graba)»): an external keyboard plays the own synth of MIDI 1 / 2.

The stock: a note coming in on a MIDI track's channel goes from the MIDI-in dispatcher (0x08051720) to the listener (vtable 0x080592E0: [0] note-on
0x08034D10, [4] note-off 0x08034D56; (this, track, note, velocity), MIDI 1 / 2 = tracks 2 / 3) and on to the recorder, and never to the transmitter
(0x20011334, vtable 0x08059FC4 / 0x08059FC8): it is not echoed out.  The own engine takes its notes at the transmitter's entries (vcf21's c_vnon /
c_vnoff, with the heads of fmeng / modmx / retrig in front), so what is played from outside was recorded but did not sound.
  * heads of the listener's two entries (c_kbon / c_kboff): MIDI 1 / 2 with the engine on (vcf21's c_von), not an internal injection (bit 5 of
    [ctx] + 0x14): the note goes through the transmitter's chain with a marker set (RAM, 0xA5 | track << 8 | note << 16), then to the stock (which
    records it as before); a note-on with velocity 0 only through the note-off that follows it;
  * the tail jumps of c_vnon / c_vnoff (b.w to SC06's c_non / c_noff, the MIDI out) -> c_kbton / c_kbtoff: with the marker of that very note the
    chain ends there (the engine has it, nothing goes out: no echo); otherwise SC06's as always.
RAM: modmx.MXR + 0x4B0 (the marker word).  In the hole (no card, no settings).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   orrs_reg, pop_list, push_list, raw, str_imm, subs_imm8)
import modmx as MX  # noqa: E402

LIS_VT = 0x080592E0                                      # the MIDI-in listener: + 0 note-on, + 4 note-off
TX, TX_VT = 0x20011334, 0x08059FC4                       # the transmitter: + 0 note-on, + 4 note-off
CTX = 0x200069E4                                         # [CTX] = the receiver A; [A + 0x14] bit 5 = an internal injection
INJ = 0x20
MARK = 0xA5
FLAG = MX.MXR + 0x4B0


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    def mark(rd, rt):                                    # rd = MARK | r1 << 8 | r2 << 16; clobbers rt
        E(movs_imm, rd, MARK); E(lsls_imm, rt, 1, 8); E(orrs_reg, rd, rt); E(lsls_imm, rt, 2, 16); E(orrs_reg, rd, rt)

    # ---- c_kbon / c_kboff (the listener's note-on / note-off: this, track, note, velocity)
    for name, slot in (("c_kbon", 0), ("c_kboff", 4)):
        a.label(name)
        E(cmp_imm, 1, 2); E(b_cond, name + "_f", "lo"); E(cmp_imm, 1, 3); E(b_cond, name + "_f", "hi")
        E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
        imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, name + "_p", "eq")
        E(ldrb_imm, 0, 0, 0x14); E(movs_imm, 4, INJ); E(raw, h(0x4220))                  # tst r0, r4: an internal injection
        E(b_cond, name + "_p", "ne")
        if slot == 0: E(ldr_sp, 0, 12); E(cmp_imm, 0, 0); E(b_cond, name + "_p", "eq")              # velocity 0: the stock's note-off follows
        E(ldr_sp, 0, 4); E(subs_imm8, 0, 2); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, name + "_p", "eq")
        E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); mark(0, 3); imm32(3, FLAG); E(str_imm, 0, 3, 0)
        imm32(4, TX_VT + slot); E(ldr_imm, 4, 4, 0)
        imm32(0, TX); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(ldr_sp, 3, 12); E(blx_reg, 4)       # through the transmitter's chain (the engine)
        E(movs_imm, 0, 0); imm32(3, FLAG); E(str_imm, 0, 3, 0)
        a.label(name + "_p"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True))
        a.label(name + "_f"); E(b_w, prev["on" if slot == 0 else "off"])

    # ---- c_kbton / c_kbtoff (c_vnon / c_vnoff's tail, r0-r3 = tx, track, note, velocity): the marked note ends here (no MIDI out)
    for name, nxt in (("c_kbton", "non"), ("c_kbtoff", "noff")):
        a.label(name)
        E(push_list, [0, 3]); mark(0, 3); imm32(3, FLAG); E(ldr_imm, 3, 3, 0); E(cmp_reg, 0, 3); E(pop_list, [0, 3])
        E(b_cond, name + "_o", "ne"); E(raw, RET)
        a.label(name + "_o"); E(b_w, prev[nxt])
    return a.assemble()


def bw_decode(img, at, base):
    """the target of the b.w at `at`"""
    h1, h2 = struct.unpack_from("<HH", img, at - base)
    assert h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0x9000, hex(at)
    s = (h1 >> 10) & 1; imm10 = h1 & 0x3FF; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1; imm11 = h2 & 0x7FF
    i1 = 1 - (j1 ^ s); i2 = 1 - (j2 ^ s)
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s: off -= 1 << 25
    return at + 4 + off


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the listener's note-on / note-off entries, the tail jumps of vcf21's c_vnon / c_vnoff."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_von=lab("vcf20", "c_von"))
    t_on, t_off = lab("vcf20", "c_vnon_f") + 6, lab("vcf20", "c_vnoff_f") + 6
    prev = dict(on=u(LIS_VT) & ~1, off=u(LIS_VT + 4) & ~1, non=bw_decode(img, t_on, BASE), noff=bw_decode(img, t_off, BASE))
    assert prev["on"] == 0x08034D10 and prev["off"] == 0x08034D56, (hex(prev["on"]), hex(prev["off"]))
    assert prev["non"] == lab("sc06", "c_non") and prev["noff"] == lab("sc06", "c_noff"), (hex(prev["non"]), hex(prev["noff"]))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, LIS_VT - BASE, labels["c_kbon"] | 1)
    struct.pack_into("<I", img, LIS_VT + 4 - BASE, labels["c_kboff"] | 1)
    img[t_on - BASE:t_on - BASE + 4] = bw_enc(t_on, labels["c_kbton"])
    img[t_off - BASE:t_off - BASE + 4] = bw_enc(t_off, labels["c_kbtoff"])
    return labels, code, prev
