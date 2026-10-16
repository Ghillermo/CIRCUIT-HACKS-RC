"""SC43 (the user, 2026-10-16): «incluir también el resto de funciones de pattern settings (dynamics, pitch mutate, each N iterations…) [en los
drums]; en vez de modificar el pitch, modifica el sample elegido»; with 8 bits a step: «C. Random-mutate con 4 niveles: 12 y 25 % de saltar a otra
fila (índice ± 8) y 12, 25 % de saltar dentro de la fila (índice ± 1)»; four states with «none», the user then: «25 % ± 1, 25 % ± 8, 12 % de
ambas» (MUT).

The stock (emulated):
  * the drums' probability view (Pattern Settings twice: subview 41 + 8 d; class 0x0805AB14, objects 0x200438DC + 0x3C d): [view + 0xC] = the
    context ([ctx] = the edit store of the drum's arrays, [store + 0x18] = its pattern + 0xA8; [ctx + 8] p1 = the selected step), [view + 4] -> the
    16 LEDs (pads 17-32), slot 0 = its pads (0..7 the probability of the step, 8..15 nothing), slot 8 = the listener that redraws row 3
    (0x0804F322; the thunk 0x0804F320), 0x0804A2C8(store, step) = the step has a hit;
  * a drum pattern's settings bytes 8..39 (+ 0x88..0xA7) are not used and survive the stock's edits (its edit store holds only the four arrays).

Ours:
  * a byte a step at the pattern + 0x88 + step: bits 0-2 the dynamics, 3-5 the frequency - 1, 6-7 the mutate; read only in a project marked
    "DQ" in the record's tail + 998 (saved with it): the first value set marks the project and clears the bytes 8..39 of its 32 drum patterns (a
    factory pack keeps garbage there);
  * the drum's Pattern Settings: pad 25 (peach; green while the drum's arpeggiator is on) = the probability view in mode 2 (a tap of Pattern
    Settings asked for it); the probability view: mode 1 row 4 = the frequency (the step plays on the last of each n passes of its pattern), mode 2
    row 3 = the dynamics (the note tracks' DYN2: the velocity, and later in the step by micro steps; a drum cannot play earlier), row 4 pads
    25-28 = the mutate (the sample of the hit moves: ± 1 inside its row of 8, ± 8 to another row, as MUT says);
  * the drum players' stock hit (0x08041252, called from rollers' c_rlplay) -> c_dqplay: the passes counted per drum (from the pattern's first
    step; a new pattern = 0; stopped = 0), the frequency, the dynamics (a later hit kept until its micro step), the mutate (the sample set through
    the player's [+ 0x50], as a sample flip; the next step's flip / selection puts it back).
RAM: the tail + 570..593 (6 a drum: the passes, the pattern + 1, a pending hit's micro step + 1 / velocity / sample + 1), + 594..595 the view's
state (bit 0 mode 2, bit 1 row 3 to be redrawn, bit 2 mode 2 asked, bits 4-5 LED passes left; a tag).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm,  # noqa: E402
                   ldrb_reg, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm,
                   str_sp, strb_imm, strb_reg, strh_imm, strh_reg, subs_imm8, subs_reg, tst_reg, sub_sp_imm, add_sp_imm)
from build_sc14 import udiv  # noqa: E402

MGR, BTN_PRESS, BTN_RELEASE, BTN_PS = 0x20040B10, 0x08033320, 0x0803381A, 12
PS_VT = 0x0805AB4C
PROB_VT, PROB_LISTEN, PROB0, PROB_SZ = 0x0805AB14, 0x0804F322, 0x200438DC, 0x3C
HASHIT, HIT, DP_PLAY, RANDOM = 0x0804A2C8, 0x0804AA08, 0x08041252, 0x08049908
DP0, DP_SZ = 0x20040810, 0x90
TRANSPORT, PARAM_GET = 0x20011034, 0x0803542C
SESSION_OBJ, TAIL, O_PLAY, O_UI, O_FLAG = 0x2003D71C, 0x27024, 570, 594, 998
UI_TAG = 0x5E
DQ_OFF = 0x88                                                # the step bytes inside a drum pattern
PS_PAD = 24                                                  # pad 25
COL_TOGGLE, COL_FREQ, COL_DYN, COL_MUT, COL_DIM = 0x6A, 0x2D, 0x17, 0x6A, 0x02
# the note tracks' dynamics (stepmod.DYN2): micro steps low / high, velocity low / high
DYN = ((0, 0, 0, 0), (-2, 2, 0, 0), (-2, 2, 0, 32), (0, 0, 0, 32), (-1, 3, 0, 32), (-1, 3, 0, 0), (0, 0, -32, 32), (0, 0, -32, 64))
# the mutate by level (the user: «25 % ± 1, 25 % ± 8, 12 % de ambas»): (chance in sixteenths of ± 8 to another row, of ± 1 inside the row)
MUT = ((0, 0), (0, 4), (4, 0), (2, 2))


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def mls_(rd, rn, rm, ra): return h(0xFB00 | rn) + h(ra << 12 | rd << 8 | 0x10 | rm)      # rd = ra - rn * rm


def tables():
    t = b""
    for ml, mh, vl, vh in DYN: t += bytes([ml + 8, mh + 8, vl + 64, vh + 64])
    for r_, c_ in MUT: t += bytes([r_, c_])
    return t


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    zc = [0]
    INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi", "ge": "lt", "lt": "ge", "gt": "le", "le": "gt"}
    def bc(target, cond):
        zc[0] += 1; n = f"_q{zc[0]}"; E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    RET = h(0x4770)
    E(raw, tables()); t_dyn, t_mut = base, base + 4 * len(DYN)

    # ---- c_dqtail() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_dqtail")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "tl_x", "eq"); imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("tl_x"); E(raw, RET)

    # ---- c_dqon() -> r0 = 1 when the project is marked; clobbers r1
    a.label("c_dqon")
    E(raw, h(0xB500)); E(bl, "c_dqtail"); E(cmp_imm, 0, 0); E(b_cond, "on_x", "eq")
    imm32(1, O_FLAG); E(adds_reg, 0, 0, 1); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x44); E(b_cond, "on_0", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x51); E(b_cond, "on_0", "ne")
    E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("on_0"); E(movs_imm, 0, 0)
    a.label("on_x"); E(raw, h(0xBD00))

    # ---- c_dqmark(): the project marked; the first time the bytes 8..39 of its 32 drum patterns cleared; clobbers r0-r3
    a.label("c_dqmark")
    E(push_list, [4, 5], lr=True)
    E(bl, "c_dqon"); E(cmp_imm, 0, 0); bc("mk_x", "ne")
    E(bl, "c_dqtail"); E(cmp_imm, 0, 0); bc("mk_x", "eq"); imm32(1, O_FLAG); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 0x44); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0x51); E(strb_imm, 1, 0, 1)
    E(movs_imm, 4, 0)
    a.label("mk_d")                                                                     # r4 = drum x 8 + pattern
    E(lsrs_imm, 0, 4, 3); E(movs_imm, 1, DP_SZ); E(muls, 0, 1); imm32(1, DP0 + 0x48); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 7); E(ands_reg, 1, 4); E(movw, 2, 0x6A8); E(muls, 1, 2); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, DQ_OFF)
    E(movs_imm, 1, 0); E(movs_imm, 2, 0)
    a.label("mk_z"); E(strb_reg, 1, 0, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, 32); E(b_cond, "mk_z", "lo")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 32); E(b_cond, "mk_d", "lo")
    a.label("mk_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_dqbyte(r0 = a pattern's base, r1 = step) -> r0 = its byte (0 in a project not marked); clobbers r1-r3
    a.label("c_dqbyte")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_dqon"); E(cmp_imm, 0, 0); E(b_cond, "by_x", "eq")
    E(adds_reg, 0, 4, 5); E(adds_imm8, 0, DQ_OFF); E(ldrb_imm, 0, 0, 0)
    a.label("by_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_dqui() -> r0 = the view's state byte (made with its tag when missing), or 0; clobbers r1
    a.label("c_dqui")
    E(raw, h(0xB500)); E(bl, "c_dqtail"); E(cmp_imm, 0, 0); E(b_cond, "ui_x", "eq"); imm32(1, O_UI); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, UI_TAG); E(b_cond, "ui_x", "eq")
    E(movs_imm, 1, UI_TAG); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    a.label("ui_x"); E(raw, h(0xBD00))

    # ---- c_dqrnd(r0 = n) -> r0 = 0..n - 1 at random; clobbers r1-r3
    a.label("c_dqrnd")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, RANDOM); E(lsrs_imm, 0, 0, 4); E(raw, udiv(1, 0, 4)); E(raw, mls_(0, 1, 4, 0)); E(pop_list, [4], pc=True)

    # ---- c_dqsmp(r0 = player) -> r0 = the sample its hit plays now: the step's flip (from r1 = base, r2 = step), else the selection; clobbers r1-r3
    a.label("c_dqsmp")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, 0x40); E(ldrb_imm, 0, 1, 0); E(cmp_imm, 0, 0xFF); E(b_cond, "sm_x", "ne")
    E(ldr_imm, 0, 4, 0x5C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    a.label("sm_x"); E(pop_list, [4], pc=True)

    # ---- c_dqmut(r0 = sample, r1 = level 1..3) -> r0 = the sample, moved as MUT says (± 1 wraps inside its row of 8, ± 8 around the 64); clobbers r1-r3
    a.label("c_dqmut")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(lsls_imm, 1, 1, 1); imm32(2, t_mut); E(adds_reg, 5, 2, 1)         # r5 = the level's chances
    E(bl, RANDOM); E(mov_reg, 6, 0)                                                      # r6 = random bits
    E(movs_imm, 0, 15); E(ands_reg, 0, 6); E(ldrb_imm, 1, 5, 1); E(cmp_reg, 0, 1); E(b_cond, "mu_r", "hs")   # inside the row
    E(movs_imm, 0, 7); E(ands_reg, 0, 4); E(movs_imm, 1, 1); E(lsls_imm, 2, 6, 27); E(b_cond, "mu_p", "pl"); E(movs_imm, 1, 7)   # bit 4: down
    a.label("mu_p"); E(adds_reg, 0, 0, 1); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(bics_reg, 4, 1); E(orrs_reg, 4, 0)
    a.label("mu_r")
    E(lsrs_imm, 0, 6, 5); E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(ldrb_imm, 1, 5, 0); E(cmp_reg, 0, 1); E(b_cond, "mu_x", "hs")   # another row
    E(movs_imm, 1, 8); E(lsls_imm, 2, 6, 22); E(b_cond, "mu_q", "pl"); E(movs_imm, 1, 56)    # bit 9: down (+ 56 = - 8 mod 64)
    a.label("mu_q"); E(adds_reg, 4, 4, 1); E(movs_imm, 1, 63); E(ands_reg, 4, 1)
    a.label("mu_x"); E(mov_reg, 0, 4); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dqhit(r0 = player, r1 = velocity, r2 = sample + 1 or 0): the hit through its interface (the sample set first); clobbers r0-r3
    a.label("c_dqhit")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 6, 1)
    E(cmp_imm, 2, 0); E(b_cond, "ht_n", "eq"); E(subs_imm8, 2, 1)
    E(ldr_imm, 0, 4, 0x50); E(ldr_imm, 1, 4, 0x54); E(ldrb_imm, 1, 1, 8); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0); E(raw, h(0x4798))   # the sample: blx r3
    a.label("ht_n")
    E(movs_imm, 1, 0x59); E(ldrb_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "ht_on", "eq")
    E(ldr_imm, 0, 4, 0x4C); E(movs_imm, 1, 0x58); E(ldrb_reg, 1, 4, 1); E(movs_imm, 2, 0); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 4); E(raw, h(0x4798))
    a.label("ht_on")
    E(ldr_imm, 0, 4, 0x4C); E(movs_imm, 1, 0x58); E(ldrb_reg, 1, 4, 1); E(mov_reg, 2, 6); E(movs_imm, 3, 0); E(ldr_imm, 5, 0, 0); E(ldr_imm, 5, 5, 0); E(raw, h(0x47A8))
    E(movs_imm, 0, 1); E(movs_imm, 1, 0x59); E(strb_reg, 0, 4, 1)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dqplay (in place of the stock's hit 0x08041252: player, pattern, step, micro step)
    a.label("c_dqplay")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], lr=True))
    E(mov_reg, 4, 0); E(movw, 0, 0x6A8); E(muls, 0, 1); E(ldr_imm, 5, 4, 0x48); E(adds_reg, 5, 5, 0)   # r4 = player, r5 = base
    imm32(1, DP0); E(subs_reg, 0, 4, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(6, 0, 1))                  # r6 = drum
    E(bl, "c_dqtail"); E(cmp_imm, 0, 0); bc("pl_stock", "eq")
    E(movs_imm, 1, 6); E(muls, 1, 6); E(adds_reg, 0, 0, 1); E(movw, 1, O_PLAY); E(adds_reg, 7, 0, 1)    # r7 = its play state
    # a pass begins: the first step's micro step 0 (a new pattern from 0)
    E(ldr_sp, 2, 8); E(movs_imm, 1, 0x81); E(ldrb_reg, 0, 5, 1); E(cmp_reg, 0, 2); E(b_cond, "pl_pd", "ne"); E(ldr_sp, 0, 12); E(cmp_imm, 0, 0); E(b_cond, "pl_pd", "ne")
    E(ldr_sp, 0, 4); E(adds_imm8, 0, 1); E(ldrb_imm, 1, 7, 2); E(cmp_reg, 0, 1); E(b_cond, "pl_c", "eq")
    E(strb_imm, 0, 7, 2); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 0); E(strb_imm, 0, 7, 1)
    a.label("pl_c")
    E(ldrb_imm, 0, 7, 0); E(ldrb_imm, 1, 7, 1); E(lsls_imm, 1, 1, 8); E(orrs_reg, 0, 1); E(adds_imm8, 0, 1); E(movw, 1, 840); E(cmp_reg, 0, 1); E(b_cond, "pl_w", "lo"); E(movs_imm, 0, 0)
    a.label("pl_w"); E(strb_imm, 0, 7, 0); E(lsrs_imm, 0, 0, 8); E(strb_imm, 0, 7, 1)
    # a hit kept for a later micro step
    a.label("pl_pd")
    E(ldrb_imm, 0, 7, 3); E(cmp_imm, 0, 0); E(b_cond, "pl_h", "eq"); E(ldr_sp, 1, 12); E(adds_imm8, 1, 1); E(cmp_reg, 0, 1); E(b_cond, "pl_h", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3); E(mov_reg, 0, 4); E(ldrb_imm, 1, 7, 4); E(ldrb_imm, 2, 7, 5); E(bl, "c_dqhit")
    a.label("pl_h")
    E(mov_reg, 0, 5); E(ldr_sp, 1, 8); E(ldr_sp, 2, 12); E(ldr_imm, 3, 4, 4); E(bl, HIT); E(cmp_imm, 0, 0); bc("pl_x", "eq")
    E(mov_reg, 0, 5); E(ldr_sp, 1, 8); E(bl, "c_dqbyte"); E(mov_reg, 8, 0)               # r8 = our byte
    E(ldr_sp, 1, 8); E(ldrb_reg, 6, 5, 1)                                                # r6 = the velocity
    E(mov_reg, 0, 8); E(cmp_imm, 0, 0); bc("pl_plain", "eq")
    # the frequency: pass % n = 0
    E(lsrs_imm, 1, 0, 3); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "pl_dy", "eq"); E(adds_imm8, 1, 1)
    E(ldrb_imm, 0, 7, 0); E(ldrb_imm, 2, 7, 1); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2); E(raw, udiv(2, 0, 1)); E(raw, mls_(0, 2, 1, 0)); E(cmp_imm, 0, 0); bc("pl_x", "ne")
    # the dynamics: the velocity, a later micro step
    a.label("pl_dy")
    E(movs_imm, 0, 0); E(mov_reg, 9, 0)                                                  # r9 = the micro steps later
    E(mov_reg, 0, 8); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); bc("pl_mu", "eq")
    E(lsls_imm, 0, 0, 2); imm32(1, t_dyn); E(adds_reg, 0, 0, 1); E(mov_reg, 2, 0); E(push_list, [2])
    E(ldrb_imm, 1, 2, 3); E(ldrb_imm, 0, 2, 2); E(subs_reg, 0, 1, 0); E(adds_imm8, 0, 1); E(bl, "c_dqrnd")
    E(pop_list, [2]); E(push_list, [2]); E(ldrb_imm, 1, 2, 2); E(adds_reg, 6, 6, 0); E(adds_reg, 6, 6, 1); E(subs_imm8, 6, 64)
    E(cmp_imm, 6, 1); E(b_cond, "pl_v1", "ge"); E(movs_imm, 6, 1)
    a.label("pl_v1"); E(cmp_imm, 6, 127); E(b_cond, "pl_v2", "le"); E(movs_imm, 6, 127)
    a.label("pl_v2")
    E(pop_list, [2]); E(ldrb_imm, 1, 2, 1); E(ldrb_imm, 0, 2, 0); E(push_list, [0]); E(subs_reg, 0, 1, 0); E(adds_imm8, 0, 1); E(bl, "c_dqrnd")
    E(pop_list, [1]); E(adds_reg, 0, 0, 1); E(subs_imm8, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "pl_mu", "le")      # later only
    E(ldr_sp, 1, 12); E(adds_reg, 1, 1, 0); E(cmp_imm, 1, 5); E(b_cond, "pl_m5", "le"); E(movs_imm, 1, 5)
    a.label("pl_m5"); E(ldr_sp, 2, 12); E(subs_reg, 0, 1, 2); E(mov_reg, 9, 0)
    # the mutate: the sample
    a.label("pl_mu")
    E(movs_imm, 0, 0); E(push_list, [0])                                                 # [sp] = the sample + 1 (0: as it is)
    E(mov_reg, 0, 8); E(lsrs_imm, 0, 0, 6); E(cmp_imm, 0, 0); E(b_cond, "pl_go", "eq"); E(mov_reg, 3, 0)
    E(push_list, [3]); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(ldr_sp, 2, 8 + 8); E(bl, "c_dqsmp"); E(pop_list, [1])
    E(cmp_imm, 0, 63); E(b_cond, "pl_go", "hi"); E(bl, "c_dqmut"); E(adds_imm8, 0, 1); E(str_sp, 0, 0)
    a.label("pl_go")
    E(mov_reg, 0, 9); E(cmp_imm, 0, 0); E(b_cond, "pl_now", "eq")
    E(ldr_sp, 1, 12 + 4); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 1); E(strb_imm, 0, 7, 3); E(strb_imm, 6, 7, 4); E(ldr_sp, 0, 0); E(strb_imm, 0, 7, 5)
    E(add_sp_imm, 4); E(b, "pl_x")
    a.label("pl_now"); E(pop_list, [2]); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_dqhit"); E(b, "pl_x")
    a.label("pl_plain"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(movs_imm, 2, 0); E(bl, "c_dqhit"); E(b, "pl_x")
    a.label("pl_stock"); E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(ldr_sp, 3, 12); E(bl, DP_PLAY)
    a.label("pl_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])); E(raw, h(0xBD00))

    # ---- the views
    # c_dqps: the drum's Pattern Settings pad 25 (no Shift) = the probability view in mode 2
    a.label("c_dqpspad")
    E(cmp_imm, 1, PS_PAD); E(b_cond, "pp_f", "ne")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "ne")
    E(bl, L["c_pmtp"]); E(cmp_imm, 0, 4); E(b_cond, "pp_p", "lo")
    E(bl, "c_dqui"); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "eq"); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 4); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, 0)
    imm32(0, MGR); E(movs_imm, 1, BTN_PS); E(bl, BTN_PRESS); imm32(0, MGR); E(movs_imm, 1, BTN_PS); E(bl, BTN_RELEASE)
    E(raw, h(0xB003)); E(pop_list, [4], pc=True)
    a.label("pp_p"); E(raw, popw([0, 1, 2, 4], lr=True))
    a.label("pp_f"); E(b_w, prev["pspad"])
    a.label("c_dqpsbuf")
    E(push_list, [4, 5], lr=True)
    E(bl, prev["psbuf"]); E(mov_reg, 5, 0)
    E(bl, L["c_pmtp"]); E(cmp_imm, 0, 4); E(b_cond, "pb_x", "lo")
    E(movs_imm, 0, 2 * PS_PAD); E(raw, h(0x5A29)); E(cmp_imm, 1, 0); E(b_cond, "pb_x", "ne")    # ldrh r1, [r5, r0]: green (the arpeggiator) stays
    E(movs_imm, 1, COL_TOGGLE); E(strh_reg, 1, 5, 0)
    a.label("pb_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)

    # c_dqview(r0 = view) -> r0 = drum 0..3, r1 = the edited pattern's base, r2 = the selected step; r0 = 0xFF when no store
    a.label("c_dqview")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); imm32(1, PROB0); E(subs_reg, 0, 0, 1); E(movs_imm, 1, PROB_SZ); E(raw, udiv(5, 0, 1))
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 2, 0, 0)
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 0); E(ldr_imm, 1, 0, 0x18); E(subs_imm8, 1, 0xA8)
    E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)

    # c_dqhas(r0 = view) -> r0 = 1 when the selected step has a hit; clobbers r1-r3
    a.label("c_dqhas")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0)
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 0); E(bl, HASHIT); E(pop_list, [4], pc=True)

    # c_dqpad (the drums' probability view slot 0: view, pad 0..15, velocity)
    a.label("c_dqpad")
    E(cmp_imm, 1, 15); bc("dp_f", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 1)
    E(bl, "c_dqui"); E(movs_imm, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "dp_m", "eq"); E(ldrb_imm, 6, 0, 0); E(movs_imm, 0, 1); E(ands_reg, 6, 0)   # r6 = mode 2
    a.label("dp_m")
    E(cmp_imm, 6, 0); E(b_cond, "dp_2", "ne")
    E(cmp_imm, 7, 8); bc("dp_p", "lo")                                                  # mode 1: row 3 the stock's
    E(subs_imm8, 7, 8); E(movs_imm, 5, 3); E(b, "dp_s")                                 # row 4: the frequency (bits 3-5)
    a.label("dp_2")
    E(cmp_imm, 7, 8); E(b_cond, "dp_d", "lo")
    E(subs_imm8, 7, 8); E(cmp_imm, 7, 3); bc("dp_t", "hi"); E(movs_imm, 5, 6); E(b, "dp_s")   # pads 25-28: the mutate (bits 6-7)
    a.label("dp_d"); E(movs_imm, 5, 0)                                                  # row 3: the dynamics (bits 0-2)
    a.label("dp_s")
    E(ldr_sp, 0, 0); E(bl, "c_dqhas"); E(cmp_imm, 0, 0); bc("dp_t", "eq")             # a step without a hit
    E(bl, "c_dqmark")
    E(ldr_sp, 0, 0); E(bl, "c_dqview"); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, DQ_OFF); E(mov_reg, 4, 1)   # r4 = our byte's address
    E(ldrb_imm, 0, 4, 0); E(movs_imm, 1, 7); E(cmp_imm, 5, 6); E(b_cond, "dp_k", "ne"); E(movs_imm, 1, 3)
    a.label("dp_k"); E(lsls_reg, 1, 5); E(bics_reg, 0, 1); E(lsls_reg, 7, 5); E(orrs_reg, 0, 7); E(strb_imm, 0, 4, 0)
    a.label("dp_t"); E(raw, h(0xB003)); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dp_p"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.label("dp_f"); E(b_w, prev["ppad"])

    # c_dqrows(r0 = view): our rows into its 16 LEDs
    a.label("c_dqrows")
    E(raw, pushw([4, 5, 6, 7, 8], lr=True))
    E(mov_reg, 4, 0); E(ldr_imm, 0, 4, 4); E(ldr_imm, 5, 0, 0)                           # r5 = the LEDs
    E(bl, "c_dqui"); E(movs_imm, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "rw_m", "eq"); E(ldrb_imm, 6, 0, 0); E(movs_imm, 0, 1); E(ands_reg, 6, 0)
    a.label("rw_m")
    E(mov_reg, 0, 4); E(bl, "c_dqhas"); E(mov_reg, 8, 0)                                 # r8 = a hit
    E(mov_reg, 0, 4); E(bl, "c_dqview"); E(mov_reg, 0, 1); E(mov_reg, 1, 2); E(bl, "c_dqbyte"); E(mov_reg, 7, 0)   # r7 = our byte
    E(cmp_imm, 6, 0); bc("rw_2", "ne")
    # mode 1: row 4 = the frequency as a yellow bar
    E(lsrs_imm, 7, 7, 3); E(movs_imm, 0, 7); E(ands_reg, 7, 0); E(movs_imm, 3, 0)
    a.label("rw_f"); E(movs_imm, 2, 0); E(mov_reg, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "rw_fw", "eq")
    E(movs_imm, 2, COL_DIM); E(cmp_reg, 3, 7); E(b_cond, "rw_fw", "hi"); E(movs_imm, 2, COL_FREQ)
    a.label("rw_fw"); E(mov_reg, 0, 3); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "rw_f", "lo")
    E(b, "rw_x")
    a.label("rw_2")                                                                     # mode 2: row 3 = the dynamics (the chosen one green), pads 25-28 = the mutate bar
    E(movs_imm, 3, 0)
    a.label("rw_d"); E(movs_imm, 2, 0); E(mov_reg, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "rw_dw", "eq")
    E(movs_imm, 2, COL_DIM); E(movs_imm, 0, 7); E(ands_reg, 0, 7); E(cmp_reg, 0, 3); E(b_cond, "rw_dw", "ne"); E(movs_imm, 2, COL_DYN)
    a.label("rw_dw"); E(lsls_imm, 0, 3, 1); E(strh_reg, 2, 5, 0); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "rw_d", "lo")
    E(lsrs_imm, 7, 7, 6); E(movs_imm, 3, 0)
    a.label("rw_u"); E(movs_imm, 2, 0); E(mov_reg, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "rw_uw", "eq"); E(cmp_imm, 3, 4); E(b_cond, "rw_uw", "hs")
    E(movs_imm, 2, COL_DIM); E(cmp_reg, 3, 7); E(b_cond, "rw_uw", "hi"); E(movs_imm, 2, COL_MUT)
    a.label("rw_uw"); E(mov_reg, 0, 3); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "rw_u", "lo")
    a.label("rw_x"); E(raw, popw([4, 5, 6, 7, 8])); E(raw, h(0xBD00))

    # c_dqbuf (that view's slot 7: view) -> its LEDs: the view on the screen (a view that opens takes the mode asked, else mode 1; row 3 back to
    # the stock's after mode 2), then our rows
    a.label("c_dqbuf")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 4, 0)
    E(bl, "c_dqui"); E(cmp_imm, 0, 0); E(b_cond, "bf_r", "eq")
    E(mov_reg, 5, 0); E(ldrb_imm, 1, 5, 0)
    E(lsrs_imm, 2, 1, 4); E(b_cond, "bf_o", "ne")
    E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "bf_a", "eq"); E(movs_imm, 2, 2); E(orrs_reg, 1, 2)    # it was in mode 2: row 3 to be redrawn
    a.label("bf_a"); E(lsrs_imm, 2, 1, 2); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(movs_imm, 3, 0x0D); E(bics_reg, 1, 3); E(orrs_reg, 1, 2)   # mode = asked, asked off
    a.label("bf_o"); E(movs_imm, 2, 0x30); E(orrs_reg, 1, 2)
    E(movs_imm, 2, 1); E(tst_reg, 1, 2); E(b_cond, "bf_s", "ne")                       # mode 1 with row 3 to redraw: the stock's listener
    E(movs_imm, 2, 2); E(tst_reg, 1, 2); E(b_cond, "bf_s", "eq")
    E(bics_reg, 1, 2); E(strb_imm, 1, 5, 0); E(mov_reg, 0, 4); E(bl, PROB_LISTEN); E(b, "bf_r")
    a.label("bf_s"); E(strb_imm, 1, 5, 0)
    a.label("bf_r")
    E(mov_reg, 0, 4); E(bl, "c_dqrows")
    E(mov_reg, 0, 4); E(pop_list, [3, 4, 5]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, prev["pbuf"])   # ldr lr, [sp], #4

    # c_dqledtask (the LED task calls): the chain; one LED pass less to "on the screen"; stopped: the passes and the pending hits to 0
    a.label("c_dqledtask")
    E(push_list, [3, 4], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_dqui"); E(cmp_imm, 0, 0); E(b_cond, "lt_t", "eq")
    E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 4); E(b_cond, "lt_t", "eq"); E(subs_imm8, 1, 0x10); E(strb_imm, 1, 0, 0)
    a.label("lt_t")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "ne")
    E(bl, "c_dqtail"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq"); E(movw, 1, O_PLAY); E(adds_reg, 0, 0, 1)
    E(movs_imm, 1, 0); E(movs_imm, 2, 0)
    a.label("lt_z"); E(strb_reg, 1, 0, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, 24); E(b_cond, "lt_z", "lo")
    a.label("lt_x"); E(pop_list, [3, 4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; rollers' call of the stock's hit, the Pattern Settings view slots 0 / 7, the drums' probability view slots 0 / 7, the LED task calls."""
    import ct_fw
    import packio as PK, fxdiag as FD
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_pmtp=lab("playmode", "c_pmtp"))
    prev = dict(pspad=u(PS_VT) & ~1, psbuf=u(PS_VT + 28) & ~1, ppad=u(PROB_VT) & ~1, pbuf=u(PROB_VT + 28) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    rl = lab("rollers", "c_rlplay")
    sites = [x for x in range(rl, rl + 64, 2) if bytes(img[x - BASE:x - BASE + 4]) == bl(x, DP_PLAY)]
    assert len(sites) == 1, sites
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[sites[0] - BASE:sites[0] - BASE + 4] = bl(sites[0], labels["c_dqplay"])
    for vt, k, nm in ((PS_VT, 0, "c_dqpspad"), (PS_VT, 7, "c_dqpsbuf"), (PROB_VT, 0, "c_dqpad"), (PROB_VT, 7, "c_dqbuf")):
        struct.pack_into("<I", img, vt + 4 * k - BASE, labels[nm] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_dqledtask"])
    prev["play_site"] = sites[0]
    return labels, code, prev
