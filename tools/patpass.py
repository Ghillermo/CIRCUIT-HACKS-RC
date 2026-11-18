"""Alpha 7.02: drumpat.use_patpass()'s reset of the per-pattern pass counts (drumpat.CNT, 64 B), called from the LED task while the transport is
stopped (drumpat's c_dqledtask leaves a 4-byte site, lt_cz, with r1 = 0: the end of the image has no room for the loop).  In dspz's second gap
(dspz.add(..., gap=1)): 12 B + one literal."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, bl, h, movs_imm, movt, movw, raw, subs_imm8  # noqa: E402
import drumpat as DQ  # noqa: E402


def arm_code(base):
    a = Asm(base)
    E = a.emit
    a.label("c_dqcz")                                                                   # (r1 = 0) CNT's 64 bytes to 0; clobbers r0, r2
    E(movw, 0, DQ.CNT & 0xFFFF); E(movt, 0, DQ.CNT >> 16); E(movs_imm, 2, 64)
    a.label("cz_l"); E(subs_imm8, 2, 4); E(raw, h(0x5081)); E(b_cond, "cz_l", "ne")     # str r1, [r0, r2]
    E(raw, h(0x4770))                                                                    # bx lr
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    site = int(report["drumpat"]["labels"]["lt_cz"], 16)
    assert bytes(img[site - BASE:site - BASE + 4]) == h(0xBF00) * 2, hex(site)
    code, labels = arm_code(base_addr)
    img += code
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_dqcz"])
    return labels, code, {}
