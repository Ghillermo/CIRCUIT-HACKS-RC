"""SC45.3 / RC2.04 (a fix; the user, 2026-10-20: «el arpegiador en compases de más de 16 pasos no recuerda qué notas estaban pulsadas después del
16 (hay que volver a poner las notas en el paso 17 para que siga arpegiando)», «extiende este fix a notas mantenidas durante la grabación aunque no
fuera arpegio»): a note held longer than 16 steps while recording goes on in the step 16 later.

The stock's recorder (the note tracks' recorder objects, vtable 0x0805A5B4) writes a note when it is let go with 0x0803F7BE: gate = the steps
held (udiv at 0x0803F856, lr = the steps, r2 = the ticks held, ip = the ticks a step) and from 16 steps on a flat 96 (0x0803F85A): the rest of the
note is lost, so an arpeggiated chord held 20 steps plays for 16 and stops, and a long note is cut.
  * 0x0803F856 (udiv lr, r2, ip) -> bl c_rfdiv: the same udiv (lr returned through the stack), and the ticks held / the ticks a step kept in RAM;
  * 0x0803F89E (ldrb r0, [r6]; movs r2, #7: r2 = the unit written - 4, r6 = its step, r4 = the note's entry word: bits 3-7 the step, the
    pattern base = r6 - 28 step) -> bl c_rlong: when the unit's gate is 96 and the note was held longer, it gets the tie bit and the same note
    (micro step, velocity) is written 16 steps later (wrapping within the pattern's first .. last step) with what is left (at most 96, tied
    again while more is left); a unit of that note there is reused, else a free one; none free, or back at the start step (a pattern of 16
    steps or less: nothing), it stops (the last tie taken back).  The stock's tie carries the note over without a new note-on; the arpeggiator
    sees the step's units as a new chord, so it goes on.
Synth 1 / 2 and MIDI 1 / 2 (the four note tracks share the code).  RAM: modmx.MXR + 0x1E0 (8 B, scratch).  In the hole (RAM only).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsls_reg,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, push_list, raw, str_imm, str_sp, strb_imm, sub_sp_imm, add_sp_imm,
                   subs_imm8, subs_reg)
from build_sc14 import udiv  # noqa: E402
import modmx as MX  # noqa: E402

DIV_AT, DIV_OLD = 0x0803F856, bytes.fromhex("b2fbfcfe")     # udiv lr, r2, ip
WR_AT, WR_OLD = 0x0803F89E, bytes.fromhex("30780722")       # ldrb r0, [r6]; movs r2, #7
SCR = MX.MXR + 0x1E0                                         # + 0 the ticks held, + 4 the ticks a step
GATE_MAX, TIE, SPAN = 96, 0x80, 16
SET = 0x380                                                   # a note pattern's settings: + 0 the last step, + 1 the first


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_rfdiv (in place of udiv lr, r2, ip): lr = r2 / ip on return, r2 / ip kept; nothing else changed
    a.label("c_rfdiv")
    E(sub_sp_imm, 4); E(push_list, [0, 1]); E(mov_reg, 0, 14); E(str_sp, 0, 8)                    # [sp + 8] = the return address
    E(raw, udiv(14, 2, 12))
    imm32(0, SCR); E(str_imm, 2, 0, 0); E(mov_reg, 1, 12); E(str_imm, 1, 0, 4)
    E(raw, h(0xBD03))                                                                               # pop {r0, r1, pc}

    # ---- c_rlong (in place of ldrb r0, [r6]; movs r2, #7): the rest of a note held past 16 steps, 16 steps later
    a.label("c_rlong")
    E(push_list, [1, 3, 4, 5, 6, 7], lr=True); E(sub_sp_imm, 24)
    E(str_sp, 2, 16); E(mov_reg, 5, 2)                                                             # [sp + 16] = the unit (- 4), r5 = the last one
    E(ldrb_imm, 0, 5, 5); E(cmp_imm, 0, GATE_MAX); E(b_cond, "rl_x", "ne")
    imm32(1, SCR); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 6); E(muls, 0, 2); E(ldr_imm, 1, 1, 4); E(cmp_imm, 1, 0); E(b_cond, "rl_x", "eq")
    E(raw, udiv(0, 0, 1)); E(subs_imm8, 0, GATE_MAX); E(b_cond, "rl_x", "le"); E(str_sp, 0, 0)       # [sp] = the micro steps left
    E(ldr_imm, 0, 4, 0); E(lsrs_imm, 0, 0, 3); E(movs_imm, 1, 31); E(ands_reg, 0, 1); E(str_sp, 0, 8); E(str_sp, 0, 12)   # the start step
    E(movs_imm, 1, 28); E(muls, 1, 0); E(subs_reg, 7, 6, 1); E(str_sp, 7, 4)                       # [sp + 4] = the pattern
    imm32(1, SET); E(adds_reg, 1, 7, 1); E(ldrb_imm, 0, 1, 0); E(ldrb_imm, 2, 1, 1)
    E(cmp_reg, 0, 2); E(b_cond, "rl_x", "lo"); E(subs_reg, 3, 0, 2); E(adds_imm8, 3, 1)
    E(cmp_imm, 3, SPAN); E(b_cond, "rl_x", "ls"); E(str_sp, 3, 20)                                 # [sp + 20] = the length
    E(ldr_sp, 0, 16); E(ldrb_imm, 4, 0, 4)                                                         # r4 = the note
    a.label("rl_l")
    E(ldr_sp, 0, 12); E(adds_imm8, 0, SPAN)
    E(ldr_sp, 7, 4); imm32(1, SET); E(adds_reg, 1, 7, 1); E(ldrb_imm, 1, 1, 0); E(cmp_reg, 0, 1); E(b_cond, "rl_w", "ls")
    E(ldr_sp, 2, 20); E(subs_reg, 0, 0, 2)
    a.label("rl_w"); E(ldr_sp, 1, 8); E(cmp_reg, 0, 1); E(b_cond, "rl_x", "eq"); E(str_sp, 0, 12)
    E(ldrb_imm, 1, 5, 5); E(movs_imm, 2, TIE); E(orrs_reg, 1, 2); E(strb_imm, 1, 5, 5)             # the last one tied
    E(movs_imm, 1, 28); E(muls, 1, 0); E(adds_reg, 6, 7, 1); E(ldrb_imm, 7, 6, 0)                  # r6 = the step, r7 = its mask
    E(movs_imm, 3, 0)
    a.label("rl_s")                                                                                # a unit of the note there
    E(movs_imm, 1, 1); E(lsls_reg, 1, 3); E(mov_reg, 2, 7); E(ands_reg, 2, 1); E(b_cond, "rl_sn", "eq")
    E(lsls_imm, 2, 3, 2); E(adds_reg, 2, 2, 6); E(ldrb_imm, 2, 2, 4); E(cmp_reg, 2, 4); E(b_cond, "rl_u", "eq")
    a.label("rl_sn"); E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "rl_s", "lo")
    E(movs_imm, 3, 0)
    a.label("rl_f")                                                                                # else a free one
    E(movs_imm, 1, 1); E(lsls_reg, 1, 3); E(mov_reg, 2, 7); E(ands_reg, 2, 1); E(b_cond, "rl_u", "eq")
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "rl_f", "lo")
    E(ldrb_imm, 1, 5, 5); E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2); E(strb_imm, 1, 5, 5); E(b, "rl_x")   # none: no tie
    a.label("rl_u")                                                                                # r3 = the unit
    E(lsls_imm, 2, 3, 2); E(adds_reg, 2, 2, 6); E(strb_imm, 4, 2, 4)
    E(ldr_sp, 0, 0); E(cmp_imm, 0, GATE_MAX); E(b_cond, "rl_g", "ls"); E(movs_imm, 0, GATE_MAX)
    a.label("rl_g"); E(strb_imm, 0, 2, 5)
    E(ldr_sp, 1, 16); E(ldrb_imm, 0, 1, 6); E(strb_imm, 0, 2, 6); E(ldrb_imm, 0, 1, 7); E(strb_imm, 0, 2, 7)
    E(movs_imm, 1, 1); E(lsls_reg, 1, 3); E(orrs_reg, 7, 1); E(strb_imm, 7, 6, 0); E(movs_imm, 1, 7); E(strb_imm, 1, 6, 1)
    E(mov_reg, 5, 2)
    E(ldr_sp, 0, 0); E(subs_imm8, 0, GATE_MAX); E(str_sp, 0, 0); E(b_cond, "rl_x", "le"); E(b, "rl_l")
    a.label("rl_x"); E(add_sp_imm, 24); E(raw, popw([1, 3, 4, 5, 6, 7], lr=True))
    E(ldrb_imm, 0, 6, 0); E(movs_imm, 2, 7); E(raw, RET)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the two sites of the recorder's note writer."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for at, old, lab in ((DIV_AT, DIV_OLD, "c_rfdiv"), (WR_AT, WR_OLD, "c_rlong")):
        assert bytes(img[at - BASE:at - BASE + 4]) == old, hex(at)
        img[at - BASE:at - BASE + 4] = bl(at, labels[lab])
    return labels, code, {}
