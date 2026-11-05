"""S514D2 (diagnostic; the user, 2026-11-04: «diagnostic the 4k»): DSP core 1 started with OMR MS = 1, as the stock starts core 0.

The stock's loader (0x08029260) sends an 8-word stub (0x080296E0: OMR MS = 1, bit 22 = 1, then the bootstrap at $FFFFFE again) to core 0
only, then core 0's program, then core 1's: core 1 runs with MS = 0 and 2 K words of program RAM (SC35D.1), core 0 with 16 K.  Here the call that
sends core 1's program (0x080292A6, dspz's c_dspz) goes through c_c1ms, which first sends the same stub to core 1 (0x08029200(stub, 1)) and waits
as the stock waits between two sends (0x0801B394(1)).  granular_dsp.use_memdiag then reports core 1's OMR and which P / X / Y addresses hold a word.
ARM only, in dspz's gap (dspz.add).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_w, bl, h, mov_reg, movs_imm, movt, movw, pop_list, push_list  # noqa: E402

STUB, SEND, WAIT, SITE = 0x080296E0, 0x08029200, 0x0801B394, 0x080292A6


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    a.label("c_c1ms")                                                     # (r0 = core 1's program, r1 = 1)
    E(push_list, [0, 1], lr=True)
    E(movw, 0, STUB & 0xFFFF); E(movt, 0, STUB >> 16); E(movs_imm, 1, 1); E(bl, SEND)
    E(movs_imm, 0, 1); E(bl, WAIT)
    E(pop_list, [0, 1]); E(pop_list, [3]); E(mov_reg, 14, 3); E(b_w, prev)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    import fxdiag as FD
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    prev = FD.bl_target(img, SITE, BASE)
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SITE - BASE:SITE - BASE + 4] = bl_enc(SITE, labels["c_c1ms"])
    return labels, code, dict(send=prev)
