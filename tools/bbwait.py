"""Alpha 7.15 (2026-11-20; found by the in-unit stress runs, S714D3): the black box's stall check (the main loop not run for 1.5 s, v2) fired on card
work the panel waits for: a sample swap / copy between drum slots (packio), a patch save, a project copy (each a synchronous request to the storage
task, 1-2 s on the internal pack's memory): Save blinked violet and, until a restart, the record held a «lock-up» that was not one (the pack copy /
delete had the same, packsave.use_bbonly).  Here, generally: the content API's post 0x0803CA34(request) waits (0x08022A46) when the request has no
callback ([request + 0x3C] = 0); its two calls (0x0803CAD6, 0x0803CB02) -> c_bbwt: when the task waiting is the main loop's (pxCurrentTCB = the
black box's MTCB), the black box's heartbeat is put to 0 first (its stall check skips until the main loop runs again), then the post as always.
Another task's request (the LED task's patch reads) leaves it alone.  In dspz's first gap."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, h, ldr_imm, movs_imm, movt, movw, raw, str_imm  # noqa: E402

POST = 0x0803CA34
SITES = (0x0803CAD6, 0x0803CB02)
CUR_TCB = 0x20006138


def arm_code(base, bb):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_bbwt")                                                    # (r0 = the request; r1-r3 free: the post's own first use)
    E(ldr_imm, 1, 0, 0x3C); E(cmp_imm, 1, 0); E(b_cond, "bw_x", "ne")    # a callback: no wait
    imm32(1, CUR_TCB); E(ldr_imm, 1, 1, 0); imm32(2, bb.BB); E(raw, bb.ldr_w(3, 2, bb.O2.MTCB)); E(raw, h(0x4299)); E(b_cond, "bw_x", "ne")   # cmp r1, r3
    E(movs_imm, 1, 0); E(str_imm, 1, 2, bb.O.NOW)
    a.label("bw_x"); E(b_w, POST)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    import blackbox as bb
    BASE = ct_fw.APP_BASE
    assert bb.V2, "bbwait: the black box v2 (its main task's TCB)"
    for s in SITES:
        assert bytes(img[s - BASE:s - BASE + 4]) == bl(s, POST), hex(s)
    code, labels = arm_code(base_addr, bb)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for s in SITES:
        img[s - BASE:s - BASE + 4] = bl(s, labels["c_bbwt"])
    return labels, code, {}
