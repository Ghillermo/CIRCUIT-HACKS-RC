"""SC43.7 (the user, 2026-10-17: «Shift+play: quantize current pattern»): Shift + Play = the pattern the selected track plays, quantized to its
steps.

The stock: a note recorded live lands on the step it was played in, with its micro step (0..5, the sixths of a step: unit byte 2) after the
step's start; a drum hit is a bit of the step's micro step mask (the fourth array of the drum pattern, + 0x60; bit k = micro step k).

Ours (the head of the button chain): Play with Shift held (not the count-in's own press) does not reach the stock; instead, over the pattern's
first..last step:
  * a note track: a unit on micro steps 1-2 goes to micro step 0 of its step; on micro steps 3-5 it goes to micro step 0 of the next step (the
    last step's to the first), into a free unit of that step (an empty step also gets the probability of the old one); the same note there
    already = the moved one is dropped; no free unit = micro step 0 of its own step;
  * a drum: a step with one hit on micro steps 1-2 = micro step 0; on 3-5 = micro step 0 of the next step (an empty one gets its velocity,
    probability and sample flip; the old step is emptied); a step with several hits (a roll) stays; then the drum's edit store
    (drumstore.py), or the stock's next commit puts the old arrays back.
The Play LED while Shift is held: yellow (available), green once the pattern was quantized (until Shift is let go: the record's tail + 939 =
0xD1 meanwhile, 0 after).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp,  # noqa: E402
                   ldrb_imm, ldrb_reg, lsls_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_sp, strb_imm,
                   strb_reg, sub_sp_imm, add_sp_imm, subs_imm3, subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import countin as CI  # noqa: E402
import drumstore  # noqa: E402

ID_PLAY, LED_PLAY = 17, 49
SESSION_OBJ, TAIL, O_Q, Q_DONE = 0x2003D71C, 0x27024, 939, 0xD1
COL_AV, COL_DONE = 0x2D, 0x17                                  # yellow (available), green (done)
STEP_SZ, SET_OFF, D_SET_OFF = 28, 0x380, 0x80                 # a note step; the pattern's settings from its start (note / drum)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w_(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_qzt() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_qzt")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "qt_x", "eq")
    imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("qt_x"); E(raw, h(0x4770))

    # ---- c_qzstep(r0 = a note step, r1 = the next step, or 0): its units quantized
    a.label("c_qzstep")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 6, 0)
    a.label("us_l")
    E(ldrb_imm, 0, 4, 0); E(raw, h(0x40F0)); E(lsls_imm, 0, 0, 31); E(b_cond, "us_n", "pl")      # lsrs r0, r6: unit i used
    E(lsls_imm, 7, 6, 2); E(adds_reg, 7, 7, 4); E(adds_imm8, 7, 4)                                 # r7 = the unit
    E(ldrb_imm, 0, 7, 2); E(cmp_imm, 0, 0); E(b_cond, "us_n", "eq")
    E(cmp_imm, 0, 3); E(b_cond, "us_z", "lo"); E(cmp_imm, 5, 0); E(b_cond, "us_z", "eq")
    E(ldrb_imm, 1, 7, 0); E(movs_imm, 3, 0)                                                        # r1 = the note
    a.label("us_s")                                                                                # the same note there: dropped
    E(ldrb_imm, 0, 5, 0); E(raw, h(0x40D8)); E(lsls_imm, 0, 0, 31); E(b_cond, "us_s2", "pl")      # lsrs r0, r3
    E(lsls_imm, 2, 3, 2); E(adds_reg, 2, 2, 5); E(ldrb_imm, 2, 2, 4); E(cmp_reg, 2, 1); E(b_cond, "us_d", "eq")
    a.label("us_s2"); E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "us_s", "lo")
    E(movs_imm, 3, 0)
    a.label("us_f")                                                                                # a free unit there
    E(ldrb_imm, 0, 5, 0); E(raw, h(0x40D8)); E(lsls_imm, 0, 0, 31); E(b_cond, "us_m", "pl")
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "us_f", "lo")
    E(b, "us_z")                                                                                   # no room: its own step
    a.label("us_m")
    E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "us_m2", "ne"); E(ldrb_imm, 2, 4, 1); E(strb_imm, 2, 5, 1)   # an empty step: the probability
    a.label("us_m2"); E(movs_imm, 2, 1); E(raw, h(0x409A)); E(orrs_reg, 0, 2); E(strb_imm, 0, 5, 0)              # lsls r2, r3
    E(lsls_imm, 2, 3, 2); E(adds_reg, 2, 2, 5); E(adds_imm8, 2, 4)
    E(strb_imm, 1, 2, 0); E(ldrb_imm, 0, 7, 1); E(strb_imm, 0, 2, 1); E(movs_imm, 0, 0); E(strb_imm, 0, 2, 2); E(ldrb_imm, 0, 7, 3); E(strb_imm, 0, 2, 3)
    a.label("us_d")                                                                                # the unit out of its step
    E(ldrb_imm, 0, 4, 0); E(movs_imm, 2, 1); E(raw, h(0x40B2)); E(bics_reg, 0, 2); E(strb_imm, 0, 4, 0)          # lsls r2, r6
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 0); E(strb_imm, 0, 7, 1); E(strb_imm, 0, 7, 2); E(movs_imm, 0, 0x60); E(strb_imm, 0, 7, 3)
    E(b, "us_n")
    a.label("us_z"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 2)
    a.label("us_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 6); E(b_cond, "us_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_qzhit(r0 = a drum pattern, r1 = step, r2 = the next step, or 0xFF): its hit quantized
    a.label("c_qzhit")
    E(push_list, [4, 5, 6], lr=True)
    E(adds_reg, 4, 0, 1); E(movs_imm, 3, 0x60); E(ldrb_reg, 5, 4, 3)                               # r4 = the step's velocity byte, r5 = its micro steps
    E(cmp_imm, 5, 1); E(b_cond, "qh_x", "ls")
    E(subs_imm3, 6, 5, 1); E(ands_reg, 6, 5); E(cmp_imm, 6, 0); E(b_cond, "qh_x", "ne")           # several hits: kept
    E(cmp_imm, 5, 8); E(b_cond, "qh_m", "hs")
    a.label("qh_z"); E(movs_imm, 1, 1); E(strb_reg, 1, 4, 3); E(b, "qh_x")
    a.label("qh_m"); E(cmp_imm, 2, 0xFF); E(b_cond, "qh_z", "eq")
    E(adds_reg, 6, 0, 2); E(ldrb_reg, 1, 6, 3); E(cmp_imm, 1, 0); E(b_cond, "qh_d", "ne")          # r6 = the next step's velocity byte
    E(movs_imm, 3, 0)
    a.label("qh_c"); E(ldrb_reg, 1, 4, 3); E(strb_reg, 1, 6, 3); E(adds_imm8, 3, 0x20); E(cmp_imm, 3, 0x60); E(b_cond, "qh_c", "lo")   # velocity, probability, sample flip
    E(movs_imm, 1, 1); E(b, "qh_w")
    a.label("qh_d"); E(movs_imm, 3, 1); E(orrs_reg, 1, 3); E(movs_imm, 3, 0x60)
    a.label("qh_w"); E(strb_reg, 1, 6, 3)
    E(movs_imm, 1, 0); E(strb_imm, 1, 4, 0); E(strb_reg, 1, 4, 3); E(movs_imm, 1, 0xFF); E(movs_imm, 3, 0x40); E(strb_reg, 1, 4, 3)   # the old step emptied
    a.label("qh_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_qzdo(): the pattern the selected track plays, quantized
    a.label("c_qzdo")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(bl, L["c_pmtp"]); E(str_sp, 0, 0); E(cmp_imm, 0, 7); E(b_cond, "qd_x", "hi")
    E(bl, L["c_pcrule"]); E(cmp_imm, 0, 0); E(b_cond, "qd_x", "eq")
    E(subs_imm8, 0, 4); E(ldrb_imm, 6, 0, 1); E(ldrb_imm, 7, 0, 0)                                 # r6 = the first step, r7 = the last
    E(cmp_imm, 6, 31); E(b_cond, "qd_x", "hi"); E(cmp_imm, 7, 31); E(b_cond, "qd_x", "hi")
    E(cmp_reg, 6, 7); E(b_cond, "qd_o", "ls"); E(mov_reg, 1, 6); E(mov_reg, 6, 7); E(mov_reg, 7, 1)
    a.label("qd_o")
    E(ldr_sp, 1, 0); E(cmp_imm, 1, 4); E(b_cond, "qd_dr", "hs")
    imm32(1, SET_OFF); E(subs_reg, 4, 0, 1); E(mov_reg, 5, 6)                                      # r4 = the pattern
    a.label("qd_l")
    E(movs_imm, 2, STEP_SZ); E(mov_reg, 0, 5); E(muls, 0, 2); E(adds_reg, 0, 0, 4)
    E(cmp_reg, 5, 7); E(b_cond, "qd_n1", "ne"); E(mov_reg, 1, 6); E(b, "qd_n2")
    a.label("qd_n1"); E(adds_imm3, 1, 5, 1)
    a.label("qd_n2"); E(movs_imm, 3, 0); E(cmp_reg, 1, 5); E(b_cond, "qd_n3", "eq")
    E(movs_imm, 2, STEP_SZ); E(muls, 1, 2); E(adds_reg, 3, 1, 4)
    a.label("qd_n3"); E(mov_reg, 1, 3); E(bl, "c_qzstep")
    E(adds_imm8, 5, 1); E(cmp_reg, 5, 7); E(b_cond, "qd_l", "ls")
    E(b, "qd_x")
    a.label("qd_dr")
    E(movs_imm, 1, D_SET_OFF); E(subs_reg, 4, 0, 1); E(mov_reg, 5, 6)
    a.label("qd_dl")
    E(cmp_reg, 5, 7); E(b_cond, "qd_d1", "ne"); E(mov_reg, 2, 6); E(b, "qd_d2")
    a.label("qd_d1"); E(adds_imm3, 2, 5, 1)
    a.label("qd_d2"); E(cmp_reg, 2, 5); E(b_cond, "qd_d3", "ne"); E(movs_imm, 2, 0xFF)
    a.label("qd_d3"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_qzhit")
    E(adds_imm8, 5, 1); E(cmp_reg, 5, 7); E(b_cond, "qd_dl", "ls")
    E(ldr_sp, 0, 0); E(subs_imm8, 0, 4); E(mov_reg, 1, 4); E(bl, "c_qzdsync")
    a.label("qd_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    drumstore.emit_syncall(a, "c_qzdsync")

    # ---- c_qzbtn (the head of the button chain: ctrl, id): Shift + Play = quantize
    a.label("c_qzbtn")
    E(cmp_imm, 1, ID_PLAY); E(b_cond, "qb_f", "ne")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(bl, "c_qzt"); E(cmp_imm, 0, 0); E(b_cond, "qb_p", "eq"); E(mov_reg, 4, 0)
    E(raw, ldrb_w_(0, 4, CI.O_PASS)); E(cmp_imm, 0, 0); E(b_cond, "qb_p", "ne")                   # the count-in's own press
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "qb_p", "eq")
    E(bl, "c_qzdo")
    E(movs_imm, 0, Q_DONE); E(raw, strb_w_(0, 4, O_Q))
    E(pop_list, [0, 1, 2, 3, 4], pc=True)
    a.label("qb_p"); E(raw, popw([0, 1, 2, 3, 4], lr=True))
    a.label("qb_f"); E(b_w, prev["btn"])

    # ---- c_qzled (the LED task calls: ctrl, frame): the chain; with Shift the Play LED yellow / green
    a.label("c_qzled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_qzt"); E(cmp_imm, 0, 0); E(b_cond, "ql_x", "eq"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ql_s", "ne")
    E(raw, ldrb_w_(0, 4, O_Q)); E(cmp_imm, 0, Q_DONE); E(b_cond, "ql_x", "ne")
    E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, O_Q)); E(b, "ql_x")
    a.label("ql_s")
    E(movs_imm, 1, COL_AV); E(raw, ldrb_w_(0, 4, O_Q)); E(cmp_imm, 0, Q_DONE); E(b_cond, "ql_w", "ne"); E(movs_imm, 1, COL_DONE)
    a.label("ql_w"); E(movs_imm, 0, 2 * LED_PLAY); E(raw, h(0x5229))                                # strh r1, [r5, r0]
    a.label("ql_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the button chain, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_pmtp=lab("playmode", "c_pmtp"), c_pcrule=lab("patchain", "c_pcrule"))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_qzbtn"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_qzled"])
    return labels, code, prev
