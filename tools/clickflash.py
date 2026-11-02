"""SC50.4 / Beta 5.7 (the idea comes from Circuit Remix's visual metronome; the user, 2026-11-02: «Guarda el flash si queda sitio»): with the click's level at 0, the Clear LED
flashes orange 100 ms on each click that cannot be heard.

The click's level is K5 of the Tempo / Swing view, master parameter 0x21:9, which 0x08028FC2 sends to the DSP.  Every click comes from two places: the end of the stock's beat check
0x0802AB0E (b.w 0x0803BD58 at 0x0802AB48, when the metronome is on) and countin's call of the same function.  Both go through c_vmbeat, which keeps the hour and goes on.  The LED
task (c_vmled, a new head of its calls) paints the LED after everything else while the hour is fresh, the level is 0 and Shift is not held (countin's four colours on Clear stay).
RAM: modmx.MXR + 0x21E4 (the hour).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, h, ldr_imm, lsls_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, strh_reg, subs_reg, bl as bl_enc  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import modmx as MX  # noqa: E402

RAM = MX.MXR + 0x21E4
CLICK, GETTER, HAL_TICK = 0x0803BD58, 0x08036192, 0x2000081C
TAIL_AT = 0x0802AB48
GRP_MASTER, IDX_CLICK = 0x21, 9
FLASH_MS, COL, LED_CLEAR = 100, 0x45, 55                     # orange, steady


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_vmbeat (in place of 0x0803BD58: r0 - r2 its arguments): the hour of the click
    a.label("c_vmbeat")
    imm32(3, HAL_TICK); E(ldr_imm, 3, 3, 0); imm32(12, RAM); E(raw, h(0xF8CC) + h(3 << 12)); E(b_w, CLICK)     # str.w r3, [ip]
    # ---- c_vmled (the LED task calls: ctrl, frame)
    a.label("c_vmled")
    E(push_list, [3, 4, 5], lr=True); E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, RAM); E(ldr_imm, 4, 0, 0); imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 4); E(cmp_imm, 0, FLASH_MS); E(b_cond, "vl_x", "hs")
    E(movs_imm, 0, GRP_MASTER); E(movs_imm, 1, IDX_CLICK); E(bl, GETTER); E(lsls_imm, 0, 0, 25); E(b_cond, "vl_x", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "vl_x", "ne")
    E(movs_imm, 0, COL); E(movs_imm, 1, 2 * LED_CLEAR); E(strh_reg, 0, 5, 1)
    a.label("vl_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert bytes(img[TAIL_AT - BASE:TAIL_AT - BASE + 4]) == b_w(TAIL_AT, CLICK)
    img[TAIL_AT - BASE:TAIL_AT - BASE + 4] = b_w(TAIL_AT, labels["c_vmbeat"])
    site = int(report["countin"]["labels"]["ci_clk"], 16)
    assert bytes(img[site - BASE:site - BASE + 4]) == bl_enc(site, CLICK)
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_vmbeat"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_vmled"])
    return labels, code, prev
