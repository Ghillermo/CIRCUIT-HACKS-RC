"""S737D (diagnostic; the user, 2026-11-23: «Go» on counting the DSP program sends, to know whether the ITCM half dspz uses, 0x2000-0x3FFF, is
free after power-up for code): the stock's send of core 1's program (the bl at dspz.SITES[1], once per send of the two programs) counted in the
black box record's spare word (BB + 460: between the TCB copy and the stack copy; read with the box, python tools/bbread.py --raw / the app).
18 B at the end of the image."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b_w, bl, ldr_imm, movt, movw, str_imm  # noqa: E402
import blackbox as BBX  # noqa: E402
import dspz  # noqa: E402
import fxdiag as FD  # noqa: E402

CNT = BBX.BB + BBX.O.TCB + BBX.N_TCB                # 0x2004F1CC: 4 spare bytes of the record
assert CNT + 4 == BBX.BB + BBX.O.STK1


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    site = dspz.SITES[1]
    prev = FD.bl_target(img, site, BASE)
    a = Asm(base_addr)
    a.label("c_sendcnt")
    a.emit(movw, 2, CNT & 0xFFFF); a.emit(movt, 2, CNT >> 16); a.emit(ldr_imm, 3, 2, 0); a.emit(adds_imm8, 3, 1); a.emit(str_imm, 3, 2, 0); a.emit(b_w, prev)
    code, labels = a.assemble()
    img += code
    while len(img) % 4: img += bytes([0xFF])
    img[site - BASE:site - BASE + 4] = bl(site, labels["c_sendcnt"])
    report["sendcnt"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev=hex(prev), counter=hex(CNT), bytes=len(code))
    return labels, code, dict(send=prev)
