"""SC42.5 (the user, 2026-10-16): «preset again (when in drum preset mode) enables / disables chromatic (same behavior as shift preset)».

The stock (emulated): with a drum's Preset view on the screen ([ctrl + 0x6C] = the tracks' container, [ctrl + 0x152] = 36 + 8 d for drum d), the
Preset button again leaves it on the screen.  SC08's Shift + Preset (build_sc08.c_shbtn) toggles the flag at byte 0x51 of the drum's Preset view
([[ctrl + 0x2C] + 0x8C + 4 d], vtable 0x0805ABBC) = its chromatic / scale keyboard, and repaints the stock colours (c_dstock) when it goes off.

Ours: a head of the button chain: Preset without Shift, with a drum's Preset view on the screen = the same toggle; the press is taken.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_w, lsls_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, pop_list, push_list, raw, strb_w, subs_imm8)
import mpatch as MP  # noqa: E402
import build_sc08 as S8  # noqa: E402

MGR, CONT = 0x20040B10, 0x20040DB8
ID_PRESET = 8
SUB0, SUB_STEP = 36, 8                                     # [ctrl + 0x152] of drum d's Preset view = 36 + 8 d


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_pabtn (the head of the button chain: ctrl, id)
    a.label("c_pabtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, ID_PRESET); E(b_cond, "pa_f", "ne")
    E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pa_f", "ne")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(2, CONT); E(cmp_reg, 1, 2); E(b_cond, "pa_f", "ne")
    E(ldr_imm, 0, 4, 0x2C); E(cmp_imm, 0, 0); E(b_cond, "pa_f", "eq")
    E(bl, S8.TRACK_OF); E(subs_imm8, 0, 4); E(cmp_imm, 0, 3); E(b_cond, "pa_f", "hi"); E(mov_reg, 5, 0)        # r5 = the drum
    E(lsls_imm, 1, 5, 3); E(adds_imm8, 1, SUB0)
    imm32(0, MGR); E(ldrb_w, 2, 0, 0x152); E(cmp_reg, 1, 2); E(b_cond, "pa_f", "ne")                          # its Preset view on the screen
    E(ldr_imm, 0, 4, 0x2C); E(lsls_imm, 1, 5, 2); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 0x8C); E(ldr_imm, 0, 0, 0)
    E(cmp_imm, 0, 0); E(b_cond, "pa_f", "eq")
    E(ldr_imm, 1, 0, 0); imm32(2, S8.DP_VT); E(cmp_reg, 1, 2); E(b_cond, "pa_f", "ne")
    E(ldrb_w, 1, 0, S8.FLAG); E(movs_imm, 2, 1); E(eors_reg, 1, 2); E(strb_w, 1, 0, S8.FLAG)
    E(lsls_imm, 1, 1, 31); E(b_cond, "pa_x", "ne")                                                            # on: its slot 7 paints
    E(bl, L["c_dstock"])                                                                                     # off: the stock colours
    a.label("pa_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("pa_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the button chain."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_dstock=lab("sc08", "c_dstock"))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_pabtn"])
    return labels, code, prev
