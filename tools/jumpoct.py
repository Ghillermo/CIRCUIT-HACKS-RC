"""SC50.3 / Beta 5.6 (the user, 2026-11-01: «Podemos forzar la octava en cuanto se entra en este modo para que sólo se muestren los 32 pasos y nada por encima o por debajo?»):
a pointing track's octave is 64 (steps 1-16) or 65 (17-32).

  * c_joled, the head of the LED task's calls, for each of MIDI 1 / 2: pointing that was not pointing (Jankó's RAM + 29, a bit per track, so a load counts too) = its octave to 64;
    pointing = its octave within 64..65: a press past the ends comes back the frame after;
  * then the chain; a pointing track's Note view on the screen: Octave ▼ dark at 64, Octave ▲ dark at 65, both dark in the expanded view, where Octave does nothing.
In the bytes semitab frees (no card, no settings)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, b, b_cond, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg,  # noqa: E402
                   pop_list, push_list, raw, strb_imm, strh_imm)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import janko as JK  # noqa: E402
import jumpseq as J  # noqa: E402

O_PREV = 29                                                                         # Jankó's RAM: free in V3, cleared with the word of O_LONG2
LOW, HIGH = 64, 65
LED_DOWN = 51


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_joled")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True); E(movs_imm, 4, 0)
    a.label("jo_l")
    E(mov_reg, 0, 4); E(bl, J.CAVE); E(mov_reg, 5, 0)                                # r5 = the target + 1
    E(bl, L["c_jkram"]); E(mov_reg, 6, 0)
    E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 6, O_PREV); E(mov_reg, 7, 2); E(bics_reg, 2, 1)   # lsls r1, r4: the track's bit; r7 = the bits before
    E(cmp_imm, 5, 0); E(b_cond, "jo_w", "eq"); E(orrs_reg, 2, 1)
    a.label("jo_w"); E(strb_imm, 2, 6, O_PREV); E(cmp_imm, 5, 0); E(b_cond, "jo_n", "eq")
    E(raw, h(0x400F)); E(adds_imm3, 0, 4, 2); E(bl, L["c_jkoct"])                     # ands r7, r1: 0 = it starts pointing
    E(movs_imm, 1, LOW); E(cmp_imm, 7, 0); E(b_cond, "jo_s", "eq"); E(cmp_imm, 0, LOW); E(b_cond, "jo_s", "lo")
    E(movs_imm, 1, HIGH); E(cmp_imm, 0, HIGH); E(b_cond, "jo_n", "ls")
    a.label("jo_s")
    E(cmp_reg, 0, 1); E(b_cond, "jo_n", "eq"); E(mov_reg, 5, 1)
    E(adds_imm3, 0, 4, 2); imm32(1, JK.VIEW_SZ); E(muls, 0, 1); imm32(1, JK.VIEW0); E(adds_reg, 0, 0, 1); E(ldr_imm, 7, 0, 0x34)
    E(mov_reg, 0, 7); E(movs_imm, 1, JK.V_OCT); E(bl, J.PARAM_WPTR); E(strb_imm, 5, 0, 0); E(mov_reg, 0, 7); E(bl, J.COMMIT)
    a.label("jo_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "jo_l", "lo")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(bl, prev["ledtask"])
    E(bl, L["c_jkram"]); E(ldrb_imm, 0, 0, JK.O_JUMP); E(cmp_imm, 0, 0); E(b_cond, "jo_x", "eq")
    E(bl, L["c_jktrk"]); E(mov_reg, 4, 0); E(bl, L["c_jkoct"]); E(mov_reg, 5, 0)
    imm32(1, J.MGR + J.S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 2, 9); E(muls, 2, 4); E(adds_imm8, 2, 6)
    E(ldr_sp, 3, 4); E(adds_imm8, 3, 2 * LED_DOWN); E(movs_imm, 0, 0)
    E(cmp_reg, 1, 2); E(b_cond, "jo_b", "eq")                                         # the expanded view: both
    E(cmp_imm, 5, LOW); E(b_cond, "jo_u", "hi")
    E(strh_imm, 0, 3, 0); E(b, "jo_x")
    a.label("jo_b"); E(strh_imm, 0, 3, 0)
    a.label("jo_u"); E(strh_imm, 0, 3, 2)
    a.label("jo_x"); E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """In the bytes semitab frees (centab.add): the LED task's calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    lab = lambda k: int(report["janko"]["labels"][k], 16)
    L = dict(c_jkram=lab("c_jkram"), c_jkoct=lab("c_jkoct"), c_jktrk=lab("c_jktrk"))
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_joled"])
    return labels, code, prev
