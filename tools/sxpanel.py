"""S714D2 (diagnostic, 2026-11-20; the user: «keep the stress test, focus on in-unit operations»): panel gestures from the PC, for a random stress run
(tools/panelstress_dev.py) under patscan's watch.  The incoming SysEx dispatcher (0x0801EB30) runs in the panel's own task (the black box's records:
the input and main tasks are the same, and the dispatcher is called before the main loop takes the DSP service lock), so a gesture from here takes
the same road as a real one, through the controller's entries (and the black box's ring of gestures).

Request  F0 7D 43 54 05 seq kind id val 00 00 00 00 F7   (14 B)
  kind 1 = button press 0x08033320(MGR, id), 2 = button release 0x0803381A(MGR, id), 3 = pad press 0x08033282(MGR, id, val), 4 = pad release
  0x080332FE(MGR, id), 5 = knob 0x08033848(MGR, id, val - 64), 6 = Shift held (val 1) / let go (0): p0 of [MGR + 0xC]
Reply    F0 7D 43 54 45 seq kind id val 00 00 00 00 F7
In front of what holds the dispatcher's first 4 bytes (the black box, then fwid, then rdiag); in dspz's first gap."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw,  # noqa: E402
                   strb_imm, subs_imm8)
import rdiag as RD  # noqa: E402

CMD, LEN = 0x05, 14
MGR = 0x20040B10
ENTRY = {1: 0x08033320, 2: 0x0803381A, 3: 0x08033282, 4: 0x080332FE, 5: 0x08033848}
WPTR, COMMIT = 0x080354FA, 0x080353C0


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (0x4000 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (0x4000 if lr else 0))


def arm_code(base, cont, router_ptr):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_spx")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(ldr_imm, 4, 1, 0); E(ldr_imm, 5, 1, 4); E(mov_reg, 6, 0)
    for i, v in enumerate(RD.SIG):
        E(ldrb_imm, 3, 4, i); E(cmp_imm, 3, v); E(b_cond, "px_fwd", "ne")
    E(ldrb_imm, 3, 4, 4); E(cmp_imm, 3, CMD); E(b_cond, "px_fwd", "ne"); E(cmp_imm, 5, LEN); E(b_cond, "px_fwd", "ne")
    E(ldrb_imm, 3, 4, 6); E(ldrb_imm, 1, 4, 7); E(ldrb_imm, 2, 4, 8); imm32(0, MGR)
    for k in (1, 2, 4):
        E(cmp_imm, 3, k); E(b_cond, f"px_n{k}", "ne"); E(bl, ENTRY[k]); E(b, "px_ok"); a.label(f"px_n{k}")
    E(cmp_imm, 3, 3); E(b_cond, "px_n3", "ne"); E(bl, ENTRY[3]); E(b, "px_ok"); a.label("px_n3")
    E(cmp_imm, 3, 5); E(b_cond, "px_n5", "ne"); E(subs_imm8, 2, 64); E(bl, ENTRY[5]); E(b, "px_ok"); a.label("px_n5")
    E(cmp_imm, 3, 6); E(b_cond, "px_ok", "ne")
    E(ldr_imm, 5, 0, 0xC); E(mov_reg, 0, 5); E(movs_imm, 1, 0); E(bl, WPTR); E(ldrb_imm, 2, 4, 8); E(strb_imm, 2, 0, 0); E(mov_reg, 0, 5); E(bl, COMMIT)
    a.label("px_ok")                                                               # the reply: the request with 0x45
    E(movs_imm, 3, 0x45); E(strb_imm, 3, 4, 4); E(movs_imm, 5, LEN)
    E(raw, h(0xB082)); E(raw, h(0x9400)); E(raw, h(0x9501))                         # sub sp, #8; str r4, [sp]; str r5, [sp, #4]
    imm32(0, router_ptr); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 1); E(raw, h(0x40B1))                                            # lsls r1, r6 -> 1 << port
    E(raw, h(0xAA00)); E(bl, RD.ROUTER)                                             # add r2, sp, #0
    E(raw, h(0xB002))
    E(pop_list, [0, 1, 2, 3, 4, 5, 6], pc=True)
    a.label("px_fwd")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, cont)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    old = bytes(img[RD.HOOK - BASE:RD.HOOK - BASE + 4])
    h1, h2 = struct.unpack("<HH", old)
    assert h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0x9000, old.hex()     # b.w (the black box's)
    s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1; i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
    if off & (1 << 24): off -= 1 << 25
    cont = RD.HOOK + 4 + off
    router_ptr = struct.unpack_from("<I", img, RD.ROUTER_LIT - BASE)[0]
    code, labels = arm_code(base_addr, cont, router_ptr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[RD.HOOK - BASE:RD.HOOK - BASE + 4] = RD.b_w(RD.HOOK, labels["c_spx"])
    return labels, code, dict(cont=cont)
