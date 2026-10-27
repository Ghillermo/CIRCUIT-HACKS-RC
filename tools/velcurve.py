"""SC48 / Beta 3.37 (the user, 2026-10-27: «añade un atajo en advanced setup en K1 para cambiar la curva de respuesta de los pads (con centro por
defecto) al moverlo se muestra número y se ilumina velocity»): the pads' velocity curve.

  * Advanced Setup (the Setup view with + 0x24 set), K1: the curve, -8 .. +8, 2 clicks a step; the centre (0) = the stock's response (the default).
    Right = more sensitive (soft hits come out louder: v + c (127 - (127 - v)^2 / 127 - v) / 8), left = harder (v + |c| (v^2 / 127 - v) / 8),
    1 .. 127 kept.  Every move: its number on the pads (vcf21's c_ednum: green to the right, red to the left, white at the centre) and Velocity's
    LED (panel LED 42) lit, for 1.5 s after the last move.
  * the pads: the controller's pad entry (vtable 0x0805A100 + 0 -> 0x08033282: ctrl, pad, velocity) goes through c_vcpad first: every pad hit of
    every view with a velocity > 0 takes the curve.  The stock's fixed velocity (Shift + Velocity = 96) is applied later, in the views: untouched.
  * saved with the unit's settings: parameter 5 byte 2 of the settings record (gmdrum uses byte 1 of parameters 5..7): 0xA0 | (c + 8); anything
    else = 0 (the stock's).  Both copies of the store (no commit) and the save asked of lazysave (gmdrum's c_gmsave).
RAM: modmx.MXR + 0x1A90 (16 B, signed "VCV1": + 4 the knob's accumulator (s8), + 8 the time of the last move, 0 = none).  In the hole (no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import pgmch as PG  # noqa: E402
import gmdrum as G  # noqa: E402

CTRL_VT = 0x0805A100                                    # the controller's vtable: + 0 the pad entry (ctrl, pad, velocity)
PAD_ENTRY = 0x08033282
RAM = MX.MXR + 0x1A90                                   # + 0 "VCV1", + 4 the accumulator (s8), + 8 the time of the last move
RSIG = 0x31564356
PARAM, BYTE, TAG = 5, 2, 0xA0
CMAX, CLICKS = 8, 2
SHOW_MS = 1500
LED_VEL = 42                                            # the panel's Velocity button
COL_POS, COL_NEG, COL_ZERO, COL_VEL = 0x17, 0x45, 0x01, 0x17
HAL_TICK = 0x2000081C


def curve(v, c):
    """The model of c_vcpad (for the tests)."""
    if v <= 0 or c == 0: return v
    t = 127 - (127 - v) * (127 - v) * 258 // 32768 if c > 0 else v * v * 258 // 32768
    r = v + abs(c) * (t - v) // 8 if t >= v else v - (abs(c) * (v - t)) // 8
    return max(1, min(127, r))


def arm_code(base, prev, L):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_vcram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_vcram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "vr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("vr_x"); E(raw, RET)

    # ---- c_vcget() -> r0 = the curve + 8 (0 .. 16; 8 = the stock's); clobbers r1-r3
    a.label("c_vcget")
    E(raw, h(0xB500)); E(movs_imm, 0, PARAM); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, BYTE)
    E(subs_imm8, 0, TAG); E(cmp_imm, 0, 2 * CMAX); E(b_cond, "vg_x", "ls"); E(movs_imm, 0, CMAX)
    a.label("vg_x"); E(raw, h(0xBD00))

    # ---- c_vcpad (the controller's pad entry: ctrl, pad, velocity): the curve on the velocity, then the stock
    a.label("c_vcpad")
    E(cmp_imm, 2, 0); E(b_cond, "vp_f", "eq")
    E(push_list, [0, 1, 3, 4, 5], lr=True); E(mov_reg, 4, 2)                                     # r4 = v
    E(bl, "c_vcget"); E(subs_imm8, 0, CMAX); E(b_cond, "vp_p", "eq"); E(mov_reg, 5, 0)          # r5 = c (signed)
    E(movs_imm, 0, 127); E(subs_reg, 0, 0, 4)                                                   # r0 = 127 - v
    E(cmp_imm, 5, 0); E(b_cond, "vp_n", "lt")
    E(muls, 0, 0); E(movw, 1, 258); E(muls, 0, 1); E(lsrs_imm, 0, 0, 15); E(movs_imm, 1, 127); E(subs_reg, 0, 1, 0)   # t = 127 - (127 - v)^2 / 127
    E(subs_reg, 0, 0, 4); E(muls, 0, 5); E(lsrs_imm, 0, 0, 3); E(adds_reg, 4, 4, 0); E(b, "vp_c")   # v + c (t - v) / 8 (t >= v)
    a.label("vp_n")
    E(mov_reg, 0, 4); E(muls, 0, 0); E(movw, 1, 258); E(muls, 0, 1); E(lsrs_imm, 0, 0, 15)          # t = v^2 / 127
    E(subs_reg, 0, 4, 0); E(movs_imm, 1, 0); E(subs_reg, 1, 1, 5); E(muls, 0, 1); E(lsrs_imm, 0, 0, 3); E(subs_reg, 4, 4, 0)   # v - |c| (v - t) / 8
    a.label("vp_c")
    E(cmp_imm, 4, 1); E(b_cond, "vp_l", "ge"); E(movs_imm, 4, 1)
    a.label("vp_l"); E(cmp_imm, 4, 127); E(b_cond, "vp_p", "le"); E(movs_imm, 4, 127)
    a.label("vp_p"); E(mov_reg, 2, 4); E(pop_list, [0, 1, 3, 4, 5])
    E(raw, h(0xF85D) + h(0xEB04))                                                                  # ldr.w lr, [sp], #4
    a.label("vp_f"); E(b_w, prev["pad"])

    # ---- c_vcadv() -> r0 = 1 with Advanced Setup on the screen; clobbers r1-r3
    a.label("c_vcadv")
    E(raw, h(0xB500))
    imm32(0, PG.MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PG.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "va_0", "ne")
    imm32(0, PG.SETUP_OBJ); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "va_0", "eq")
    E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("va_0"); E(movs_imm, 0, 0); E(raw, h(0xBD00))

    # ---- c_vcknob (the Setup view's slot 4: view, knob, delta): Advanced Setup's K1 = the curve
    a.label("c_vcknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "vk_f", "eq")
    E(cmp_imm, 5, 0); E(b_cond, "vk_f", "ne")
    E(bl, "c_vcram"); E(mov_reg, 7, 0)
    E(ldrb_imm, 0, 7, 4); E(raw, h(0xB240)); E(adds_reg, 0, 0, 6)                                  # sxtb r0, r0: + delta
    E(movs_imm, 4, 0)                                                                              # r4 = the steps
    a.label("vk_a")
    E(cmp_imm, 0, CLICKS); E(b_cond, "vk_b", "lt"); E(subs_imm8, 0, CLICKS); E(adds_imm8, 4, 1); E(b, "vk_a")
    a.label("vk_b")
    E(mov_reg, 1, 0); E(adds_imm8, 1, CLICKS); E(cmp_imm, 1, 0); E(b_cond, "vk_c", "gt"); E(adds_imm8, 0, CLICKS); E(subs_imm8, 4, 1); E(b, "vk_b")
    a.label("vk_c"); E(strb_imm, 0, 7, 4)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "vk_t", "ne"); E(movs_imm, 0, 1)
    a.label("vk_t"); E(str_imm, 0, 7, 8)                                                           # shown from now
    E(cmp_imm, 4, 0); E(b_cond, "vk_x", "eq")
    E(bl, "c_vcget"); E(adds_reg, 0, 0, 4)
    E(cmp_imm, 0, 0); E(b_cond, "vk_l", "ge"); E(movs_imm, 0, 0)
    a.label("vk_l"); E(cmp_imm, 0, 2 * CMAX); E(b_cond, "vk_h", "le"); E(movs_imm, 0, 2 * CMAX)
    a.label("vk_h"); E(adds_imm8, 0, TAG); E(mov_reg, 5, 0)
    for cp in (0, 1):                                                                              # both copies, no commit
        E(movs_imm, 0, PARAM); E(movs_imm, 1, cp); E(bl, L["c_gmp"]); E(strb_imm, 5, 0, BYTE)
    E(bl, L["c_gmsave"])
    a.label("vk_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("vk_f"); E(raw, h(0xE8BD) + h(0x40F7)); E(b_w, prev["knob"])                          # pop.w {r0, r1, r2, r4-r7, lr}

    # ---- c_vcled (the LED task calls: ctrl, frame): the chain; Advanced Setup, 1.5 s after a move of K1: the number and Velocity's LED
    a.label("c_vcled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_vcram"); E(mov_reg, 7, 0); E(ldr_imm, 4, 7, 8); E(cmp_imm, 4, 0); E(b_cond, "vl_x", "eq")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 4); E(movw, 1, SHOW_MS); E(cmp_reg, 0, 1); E(b_cond, "vl_off", "hi")
    E(bl, "c_vcadv"); E(cmp_imm, 0, 0); E(b_cond, "vl_off", "eq")
    E(movw, 0, COL_VEL | 0x7F00); E(movs_imm, 1, 2 * LED_VEL); E(strh_reg, 0, 5, 1)
    E(bl, "c_vcget"); E(subs_imm8, 0, CMAX); E(mov_reg, 6, 0)                                     # r6 = c
    E(movs_imm, 2, COL_ZERO); E(cmp_imm, 6, 0); E(b_cond, "vl_d", "eq")
    E(movs_imm, 2, COL_POS); E(cmp_imm, 6, 0); E(b_cond, "vl_d", "gt")
    E(movs_imm, 2, COL_NEG); E(movs_imm, 1, 0); E(subs_reg, 6, 1, 6)                               # |c|
    a.label("vl_d"); E(mov_reg, 1, 6); E(mov_reg, 0, 5); E(bl, L["c_ednum"]); E(b, "vl_x")
    a.label("vl_off"); E(movs_imm, 0, 0); E(str_imm, 0, 7, 8)
    a.label("vl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the controller's pad entry, the Setup view's slot 4, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_ednum=lab("vcf20", "c_ednum"), c_gmp=lab("gmdrum", "c_gmp"), c_gmsave=lab("gmdrum", "c_gmsave"))
    prev = dict(pad=u(CTRL_VT) & ~1, knob=u(PG.SETUP_VT + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["pad"] == PAD_ENTRY, hex(prev["pad"])
    code, labels = arm_code(base_addr, prev, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, CTRL_VT - BASE, labels["c_vcpad"] | 1)
    struct.pack_into("<I", img, PG.SETUP_VT + 16 - BASE, labels["c_vcknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_vcled"])
    assert RAM + 16 <= MX.MXR + 0x1B00
    return labels, code, prev
