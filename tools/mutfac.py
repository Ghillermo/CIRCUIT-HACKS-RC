"""SC50 / Beta 5.3 (the user, 2026-11-01: «Mientras esta vista está abierta, los pads octave up/down añaden o disminuyen a un factor de multiplicación que
incrementa o disminuye globalmente la posibilidad de cambios»; on the drums too): the factor of mode 2 of the probability view (mutate39.use_mut2).

  * c_mfview: the track 0..7 whose probability view is on the screen in mode 2: a note track's [ctrl + 0x152] = 9 t + 5 with stepmod's mode, a drum's
    41 + 8 d with drumpat's;
  * the head of the button chain: Octave ▼ / ▲ there (no Shift) = the track's factor - 1 / + 1, 0..8; 1 by default; saved with the project (the record's
    tail + 536 + track, mutate39's byte); the stock's press goes no further;
  * the LED task: in that view Octave in peach while it can still move, dark at the ends (unavailable = no light); for 1.5 s after a change the 32 pads
    show the factor (vcf21's c_ednum, the number of the tempo).
RAM: modmx.MXR + 0x21E8: the tick of the last change (no signature: garbage there shows the number for 1.5 s at the very worst).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg, tst_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import mutate39 as MU  # noqa: E402

RAM = MX.MXR + 0x21E8
MGR, S_CUR, HAL_TICK = 0x20040B10, 0x152, 0x2000081C
ID_DOWN, ID_UP, LED_DOWN, LED_UP = 19, 20, 51, 52
SUB_PROB, DRUM_PROB = 5, 41
COL, SHOW_MS = MU.COL_LIT, 1500


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_mfview() -> r0 = the track 0..7 whose probability view is on the screen in mode 2, or 0xFF; clobbers r1-r3
    a.label("c_mfview")
    E(push_list, [4], lr=True)
    imm32(1, MGR + S_CUR); E(ldrb_imm, 2, 1, 0); E(movs_imm, 4, 0)
    a.label("vw_l"); E(movs_imm, 0, 9); E(muls, 0, 4); E(adds_imm8, 0, SUB_PROB); E(cmp_reg, 0, 2); E(b_cond, "vw_n", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "vw_l", "lo")
    E(mov_reg, 0, 2); E(subs_imm8, 0, DRUM_PROB); E(b_cond, "vw_0", "mi"); E(lsls_imm, 1, 0, 29); E(b_cond, "vw_0", "ne")
    E(lsrs_imm, 0, 0, 3); E(cmp_imm, 0, 4); E(b_cond, "vw_0", "hs"); E(adds_imm8, 0, 4); E(mov_reg, 4, 0)
    E(bl, L["c_dqui"]); E(cmp_imm, 0, 0); E(b_cond, "vw_0", "eq"); E(ldrb_imm, 0, 0, 0); E(b, "vw_m")
    a.label("vw_n"); E(bl, L["c_rfst"]); E(cmp_imm, 0, 0); E(b_cond, "vw_0", "eq"); E(ldrb_imm, 0, 0, 1)
    a.label("vw_m"); E(lsls_imm, 0, 0, 31); E(b_cond, "vw_0", "pl"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("vw_0"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_mfbtn (the head of the button chain: ctrl, id): Octave in that view = the factor
    a.label("c_mfbtn")
    E(cmp_imm, 1, ID_DOWN); E(b_cond, "mb_f", "lo"); E(cmp_imm, 1, ID_UP); E(b_cond, "mb_f", "hi")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mb_p", "ne")
    E(bl, "c_mfview"); E(cmp_imm, 0, 0xFF); E(b_cond, "mb_p", "eq")
    E(bl, L["c_mgget"]); E(cmp_imm, 1, 0); E(b_cond, "mb_x", "eq")
    E(movs_imm, 2, 15); E(mov_reg, 3, 0); E(ands_reg, 3, 2); E(bics_reg, 0, 2)
    E(cmp_imm, 5, ID_UP); E(b_cond, "mb_d", "ne")
    E(cmp_imm, 3, MU.FAC_MAX); E(b_cond, "mb_w", "hs"); E(adds_imm8, 3, 1); E(b, "mb_w")
    a.label("mb_d"); E(cmp_imm, 3, 0); E(b_cond, "mb_w", "eq"); E(subs_imm8, 3, 1)
    a.label("mb_w"); E(orrs_reg, 0, 3); E(strb_imm, 0, 1, 0)
    imm32(0, RAM); imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(str_imm, 1, 0, 0)
    a.label("mb_x"); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("mb_p"); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("mb_f"); E(b_w, prev["btn"])

    # ---- c_mfled (the LED task calls: ctrl, frame): the chain; in that view Octave and, after a change, the factor on the pads
    a.label("c_mfled")
    E(push_list, [3, 4, 5, 6], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "ne")
    E(bl, "c_mfview"); E(cmp_imm, 0, 0xFF); E(b_cond, "ml_x", "eq")
    E(bl, L["c_mgfac"]); E(mov_reg, 6, 0)
    E(movs_imm, 1, 0); E(cmp_imm, 6, 0); E(b_cond, "ml_a", "eq"); E(movs_imm, 1, COL)
    a.label("ml_a"); E(movs_imm, 2, 2 * LED_DOWN); E(strh_reg, 1, 5, 2)
    E(movs_imm, 1, 0); E(cmp_imm, 6, MU.FAC_MAX); E(b_cond, "ml_b", "hs"); E(movs_imm, 1, COL)
    a.label("ml_b"); E(movs_imm, 2, 2 * LED_UP); E(strh_reg, 1, 5, 2)
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 1); E(movw, 1, SHOW_MS); E(cmp_reg, 0, 1); E(b_cond, "ml_x", "hs")
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(movs_imm, 2, COL); E(bl, L["c_ednum"])
    a.label("ml_x"); E(pop_list, [3, 4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """At the image's end: the head of the button chain, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc, b_w as bw_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_mgget=lab("mutate39", "c_mgget"), c_mgfac=lab("mutate39", "c_mgfac"), c_rfst=lab("stepmod", "c_rfst"),
             c_dqui=lab("drumpat", "c_dqui"), c_ednum=lab("vcf20", "c_ednum"))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, f"mutfac: the image is full ({len(img):#x})"
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = bw_enc(MP.BTN_ENTRY, labels["c_mfbtn"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_mfled"])
    return labels, code, prev
