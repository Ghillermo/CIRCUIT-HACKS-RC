"""SC50.4 / RC4.06 (a fix): the count-in at an external clock's tempo.  countin takes the project's BPM; as a slave the music follows the incoming clock.

The clock object 0x20011364: 0x0802AD18 reads bit 1 of [clock + 0x54] as "slave"; its tick keeps the measured tempo as an increment at clock + 0x84 + 0xC (+ 0x90), and BPM =
the high word of 0x9C4 x that (0x0802A5EA).  c_cibpm takes the place of countin's read of the tempo: the measured one as a slave, else the project's.  The count stays timed from
the press in the LED task: the clicks get the right speed, not the master's bar.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, h, lsls_imm, movs_imm, movt, movw, raw, bl as bl_enc  # noqa: E402

CLOCK = 0x20011364
O_FLAGS, O_INC, K_BPM = 0x54, 0x90, 0x9C4


def arm_code(base, c_cip0):
    a = Asm(base)
    E = a.emit
    # ---- c_cibpm(r0 = the tempo store, r1 = 0) -> r0 = the BPM
    a.label("c_cibpm")
    E(movw, 2, CLOCK & 0xFFFF); E(movt, 2, CLOCK >> 16)
    E(raw, h(0xF892) + h(3 << 12 | O_FLAGS)); E(lsls_imm, 3, 3, 30); E(b_cond, "cb_e", "mi")   # ldrb.w r3, [r2, #0x54]
    E(b_w, c_cip0)
    a.label("cb_e")
    E(raw, h(0xF8D2) + h(0 << 12 | O_INC)); E(movw, 1, K_BPM)                            # ldr.w r0, [r2, #0x90]
    E(raw, h(0xFBA1) + h(1 << 12 | 0 << 8 | 0)); E(raw, h(0x4770))                       # umull r1, r0, r1, r0; bx lr
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = report["countin"]["labels"]
    cip0, site = int(L["c_cip0"], 16), int(L["ci_bpm"], 16)
    code, labels = arm_code(base_addr, cip0)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert bytes(img[site - BASE:site - BASE + 4]) == bl_enc(site, cip0)
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_cibpm"])
    return labels, code, dict(c_cip0=cip0)
