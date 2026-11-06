"""SC52.6 / Beta 5.29 (the user, 2026-11-06: «Knob 3 en advanced setup: gain de las entradas externas. Aumenta el volumen máximo de las señales»):
the gain of the two external audio inputs.

  * Advanced Setup (the Setup view with + 0x24 set), K3: 0 .. +24 dB in 1 dB steps (2 clicks a step); 0 = the stock's (the default).  Every move:
    the number of dB on the pads (vcf21's c_ednum, white at 0), for 1.5 s after the last move; K3's LED in Advanced Setup = the gain (dim at 0).
  * the DSP (vcf21_dsp.use_ingain): at the head of vpre (P:$23C, before anything reads them: the own synth's chain, the granular's live input, the
    mixer) both inputs of the block x G, clipped; X:GAIN = G / 16 (0 = untouched, the stock's arithmetic).
  * the ARM: a new head of the DSP service chain writes X:GAIN when it changes and every REFRESH ticks (one SPI write; the DSP's RAM is cleared
    by its init).
  * saved with the unit's settings: parameter 7 byte 2 = 0x40 + dB (0x41 .. 0x58); anything else = 0 dB.  Both copies (no commit) and the save
    asked of lazysave (gmdrum's c_gmsave).  (gmdrum: parameter 4 bytes 1-3, 5..7 byte 1; velcurve 5 byte 2; velglob 6 bytes 2 / 3.)
RAM: modmx.MXR + 0x1EE8 (16 B, signed "ING1": + 4 the knob's accumulator (s8), + 5 the dB last written (0xFF = none), + 6 the ticks to the
refresh, + 8 the time of the last move, 0 = none).  In the hole (no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, lsls_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import pgmch as PG  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402

GAIN = 0x3FF9                                           # X of core 0 (free: X $3FE8-$3FFF; $3FE8 vguard, $3FF0 cueclk)
RAM = MX.MXR + 0x1EE8
RSIG = 0x31474E49                                       # "ING1"
PARAM, BYTE, TAG = 7, 2, 0x40
DBMAX, CLICKS = 24, 2
KNOB = 2                                                # K3
SHOW_MS = 1500
REFRESH = 250
LED_K3 = 60 + KNOB
COL_NUM, COL_LED = 0x01, 0x01
HAL_TICK = 0x2000081C
DSP_WRITE = 0x080292F8


def gain_word(d):
    """X:GAIN for d dB: 10^(d / 20) / 16 in 24 bits; 0 dB = 0 (the DSP leaves the inputs alone)."""
    return 0 if d <= 0 else min(0x7FFFFF, round(10 ** (d / 20) * (1 << 19)))


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev, L, tab):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_igram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_igram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "ir_x", "eq")
    E(str_imm, 2, 0, 0); E(movw, 1, 0xFF00); E(str_imm, 1, 0, 4); E(movs_imm, 1, 0); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("ir_x"); E(raw, RET)

    # ---- c_igget() -> r0 = the gain in dB (0 .. DBMAX); clobbers r1-r3
    a.label("c_igget")
    E(raw, h(0xB500)); E(movs_imm, 0, PARAM); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, BYTE)
    E(subs_imm8, 0, TAG); E(cmp_imm, 0, DBMAX); E(b_cond, "ig_x", "ls"); E(movs_imm, 0, 0)
    a.label("ig_x"); E(raw, h(0xBD00))

    # ---- c_igknob (the Setup view's slot 4: view, knob, delta): Advanced Setup's K3 = the gain
    a.label("c_igknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "ik_f", "eq")
    E(cmp_imm, 5, KNOB); E(b_cond, "ik_f", "ne")
    E(bl, "c_igram"); E(mov_reg, 7, 0)
    E(ldrb_imm, 0, 7, 4); E(raw, h(0xB240)); E(adds_reg, 0, 0, 6)                                  # sxtb r0, r0: + delta
    E(movs_imm, 4, 0)                                                                              # r4 = the steps
    a.label("ik_a")
    E(cmp_imm, 0, CLICKS); E(b_cond, "ik_b", "lt"); E(subs_imm8, 0, CLICKS); E(adds_imm8, 4, 1); E(b, "ik_a")
    a.label("ik_b")
    E(mov_reg, 1, 0); E(adds_imm8, 1, CLICKS); E(cmp_imm, 1, 0); E(b_cond, "ik_c", "gt"); E(adds_imm8, 0, CLICKS); E(subs_imm8, 4, 1); E(b, "ik_b")
    a.label("ik_c"); E(strb_imm, 0, 7, 4)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "ik_t", "ne"); E(movs_imm, 0, 1)
    a.label("ik_t"); E(str_imm, 0, 7, 8)                                                           # shown from now
    E(cmp_imm, 4, 0); E(b_cond, "ik_x", "eq")
    E(bl, "c_igget"); E(adds_reg, 0, 0, 4)
    E(cmp_imm, 0, 0); E(b_cond, "ik_l", "ge"); E(movs_imm, 0, 0)
    a.label("ik_l"); E(cmp_imm, 0, DBMAX); E(b_cond, "ik_h", "le"); E(movs_imm, 0, DBMAX)
    a.label("ik_h"); E(adds_imm8, 0, TAG); E(mov_reg, 5, 0)
    for cp in (0, 1):                                                                              # both copies, no commit
        E(movs_imm, 0, PARAM); E(movs_imm, 1, cp); E(bl, L["c_gmp"]); E(strb_imm, 5, 0, BYTE)
    E(bl, L["c_gmsave"])
    a.label("ik_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("ik_f"); E(raw, h(0xE8BD) + h(0x40F7)); E(b_w, prev["knob"])                          # pop.w {r0, r1, r2, r4-r7, lr}

    # ---- c_igled (the LED task calls: ctrl, frame): the chain; in Advanced Setup K3's LED = the gain; 1.5 s after a move the number on the pads
    a.label("c_igled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, L["c_vcadv"]); E(cmp_imm, 0, 0); E(b_cond, "il_x", "eq")
    E(bl, "c_igget"); E(mov_reg, 6, 0)
    E(movs_imm, 0, 5); E(muls, 0, 6); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, COL_LED)   # brightness 6 + 5 dB (+ 2)
    E(movs_imm, 1, 2 * LED_K3); E(strh_reg, 0, 5, 1)
    E(bl, "c_igram"); E(mov_reg, 7, 0); E(ldr_imm, 4, 7, 8); E(cmp_imm, 4, 0); E(b_cond, "il_x", "eq")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(subs_reg, 0, 0, 4); E(movw, 1, SHOW_MS); E(cmp_reg, 0, 1); E(b_cond, "il_off", "hi")
    E(mov_reg, 1, 6); E(movs_imm, 2, COL_NUM); E(mov_reg, 0, 5); E(bl, L["c_ednum"]); E(b, "il_x")
    a.label("il_off"); E(movs_imm, 0, 0); E(str_imm, 0, 7, 8)
    a.label("il_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_ighead (the head of the DSP service chain): X:GAIN = the gain's word, when it changes and every REFRESH ticks
    a.label("c_ighead")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(bl, "c_igget"); E(mov_reg, 4, 0)
    E(bl, "c_igram"); E(mov_reg, 5, 0)
    E(ldrb_imm, 0, 5, 5); E(cmp_reg, 0, 4); E(b_cond, "ih_w", "ne")
    E(ldrb_imm, 0, 5, 6); E(subs_imm8, 0, 1); E(strb_imm, 0, 5, 6); E(b_cond, "ih_x", "ne")
    a.label("ih_w")
    E(strb_imm, 4, 5, 5); E(movs_imm, 0, REFRESH); E(strb_imm, 0, 5, 6)
    E(lsls_imm, 0, 4, 2); imm32(1, tab); E(adds_reg, 1, 1, 0); E(ldr_imm, 1, 1, 0)                  # the table at the code's start
    E(lsls_imm, 1, 1, 8); E(movw, 2, GAIN); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    a.label("ih_x")
    E(raw, popw([0, 1, 2, 3, 4, 5], lr=True)); E(b_w, prev["svc"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add; the gain table first); the Setup view's slot 4, the LED task calls, the head of the DSP service chain."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_ednum=lab("vcf20", "c_ednum"), c_gmp=lab("gmdrum", "c_gmp"), c_gmsave=lab("gmdrum", "c_gmsave"), c_vcadv=lab("velcurve", "c_vcadv"))
    prev = dict(knob=u(PG.SETUP_VT + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    tab = b"".join(struct.pack("<I", gain_word(d)) for d in range(DBMAX + 1))
    code, labels = arm_code(base_addr + len(tab), prev, L, base_addr)
    code = tab + code
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, PG.SETUP_VT + 16 - BASE, labels["c_igknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_igled"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_ighead"])
    assert RAM + 16 <= MX.MXR + 0x1F00 and base_addr % 4 == 0
    return labels, code, prev
