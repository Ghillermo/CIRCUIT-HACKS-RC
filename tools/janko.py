"""SC46.3 / Beta 3.20 (a request from a user, brought by the user; decisions of the user, 2026-10-24: «janko puede ser un caso especifico de scales
(ajustado al root note de stock)» · «shift+8 … (en vista custom scale)» · «con janko, octave subiría medio tono»): the isomorphic Jankó layout of the
note tracks' keyboard, a case of the custom scale (cscale).

  * the custom scale's block (the project's tail + 544, saved with the project) with B_ON = 2 = Jankó (its keys kept; cscale reads only 1 as its
    own scale on, so older builds take a Jankó project as the stock's scale);
  * in the custom scale's editor (Shift + Scales), Shift + pad 8 (a pad the editor's piano does not use) = Jankó on / off; pad 8 cyan while on,
    yellow with Shift while off; a key of the editor (cscale) or a stock scale switches it off;
  * the keyboard's tables (its slot 0, in front of cscale's c_csslot0) for the selected note track: row k = the root (the stock's) + w + (R - k)
    semitones, + 2 a column; R = the bottom row on the screen (the stock's row offset 69 - octave + 3: the bottom-left pad = the root + w); the
    lookup of the inverse table = the occurrence on the screen (the bottom rows first), the links = the other one ((k, c) <-> (k - 2, c - 1));
  * Octave down / up in the Note and the expanded Note view of a note track (not the sample picker, not the split keyboard, not with Shift: that
    is the stock's transpose of the pattern) = w - 1 / + 1 semitone, -36..+36, per track (RAM, 0 at power-up); the stock's octave stays;
  * the LED task: the tables rebuilt when Jankó, the selected track, its w or its octave change (and once when Jankó goes off);
  * the quantiser (in front of cscale's c_csq) = the note itself (all twelve notes are in the scale: the notes that sound light on their pads);
    random-mutate (in front of cscale's c_csmut) = another of the twelve notes of its octave (above the root).
RAM: modmx.MXR + 0x500 (16 B with a signature).  In the hole (no card, no settings).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm,
                   subs_imm3, subs_imm8, subs_reg)
import modmx as MX  # noqa: E402
import cscale as CS  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
from build_sc14 import udiv  # noqa: E402

KB, KB_VT, KB_CLEAR, COMMIT, PARAM_GET = CS.KB, CS.KB_VT, CS.KB_CLEAR, CS.COMMIT, CS.PARAM_GET
QUANT = CS.QUANT
SCALES_VT = CS.SCALES_VT
MGR, S_CUR = 0x20040B10, 0x152
CONT, SEL_TRACK = 0x20040DB8, 0x0805011E                # the track views' container; (cont) -> the selected track
VIEW0, VIEW_SZ, V_OCT = 0x200412E0, 0x2F4, 8            # the note tracks' views; [view + 0x34] p8 = the octave
ROWLIT = 0x0804B1EC                                      # the literal of 0x0804B174: row offset = s8 [K] + [K + 2] - octave
ID_DOWN, ID_UP = 19, 20
JK = 2                                                   # B_ON of the custom scale's block = Jankó
RAM = MX.MXR + 0x500                                     # + 0 "JNK1", + 4..7 w per track (s8), + 8 the stamp, + 12 the selected track
RSIG = 0x314B4E4A
WMAX = 36
PAD_JK = 7
COL_ON, COL_SHIFT = 0x4D, 0x2D
ROWS, VMAX = CS.ROWS, CS.VMAX
INV = CS.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
POP_LR = h(0xF85D) + h(0xEB04)                           # ldr lr, [sp], #4


def arm_code(base, L, prev, rowbase):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_j{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    RET = h(0x4770)

    # ---- c_jkram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_jkram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "jr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("jr_x"); E(raw, RET)

    # ---- c_jkon() -> r0 = 1 with Jankó on (the custom scale's block valid, B_ON = 2); clobbers r1-r3
    a.label("c_jkon")
    E(push_list, [4], lr=True)
    E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); E(b_cond, "jo_0", "eq"); E(mov_reg, 4, 0)
    E(ldr_imm, 1, 4, 0); imm32(2, CS.MAGIC); E(cmp_reg, 1, 2); E(b_cond, "jo_0", "ne")
    E(ldrb_imm, 1, 4, CS.B_ON); E(cmp_imm, 1, JK); E(b_cond, "jo_0", "ne")
    for k in range(3): E(ldrb_imm, 2, 4, CS.B_KEYS + k); E(raw, h(0x4051))              # eors r1, r2
    E(movs_imm, 2, 0x5A); E(raw, h(0x4051)); E(ldrb_imm, 2, 4, CS.B_SUM); E(cmp_reg, 1, 2); E(b_cond, "jo_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("jo_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_jktrk() -> r0 = the note track 0..3 whose Note / expanded Note view is on the screen (not the sample picker, not the split), or 0xFF
    a.label("c_jktrk")
    E(push_list, [4], lr=True)
    imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 4, 0)
    a.label("jt_l")
    E(movs_imm, 0, 9); E(muls, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 1, 0); E(b_cond, "jt_y", "eq")
    E(adds_imm8, 0, 5); E(cmp_reg, 1, 0); E(b_cond, "jt_y", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "jt_l", "lo"); E(b, "jt_n")
    a.label("jt_y")
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); E(b_cond, "jt_n", "ne")
    E(bl, L["c_s4on"]); E(cmp_imm, 0, 0); E(b_cond, "jt_n", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("jt_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_jkoct(r0 = track) -> r0 = the stock's octave of its view; clobbers r1-r3
    a.label("c_jkoct")
    E(raw, h(0xB500))
    imm32(1, VIEW_SZ); E(muls, 0, 1); imm32(1, VIEW0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x34)
    E(movs_imm, 1, V_OCT); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(raw, h(0xBD00))

    # ---- c_jkbuild(r0 = the keyboard): the three tables of the Jankó layout for the selected track
    #      r4 = kbd, r5 = the base of row 0 (root + w + R), r6 = R, r7 = the row; [sp] = the inverse table
    a.label("c_jkbuild")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, KB_CLEAR)
    E(bl, "c_jkram"); E(ldr_imm, 1, 0, 12); E(mov_reg, 7, 1); E(adds_reg, 0, 0, 1); E(ldrb_imm, 5, 0, 4)
    E(raw, h(0xB26D))                                                                  # sxtb r5, r5: w
    E(mov_reg, 0, 7); E(bl, "c_jkoct"); E(movs_imm, 6, rowbase + 3); E(subs_reg, 6, 6, 0)   # R = 69 - octave + 3
    E(adds_imm8, 5, 60); E(adds_reg, 5, 5, 6)                                          # row 0's base
    E(movs_imm, 7, 0)
    a.label("jb_r")
    E(subs_reg, 0, 5, 7); E(movs_imm, 1, 0)                                            # r0 = the row's base, r1 = the column
    a.label("jb_c")
    E(cmp_imm, 0, 1); E(b_cond, "jb_n", "lt"); E(cmp_imm, 0, VMAX); E(b_cond, "jb_n", "gt")
    E(lsls_imm, 2, 7, 3); E(adds_reg, 2, 2, 1); E(adds_reg, 2, 2, 4); E(raw, h(0x7000 | 0x14 << 6 | 2 << 3 | 0))   # strb r0, [r2, #0x14]
    a.label("jb_n"); E(adds_imm8, 0, 2); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, "jb_c", "lo")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, ROWS); bc("jb_r", "lo")
    # the inverse table: the rows on the screen first (R, R - 1, R - 2, R - 3), then all of them
    E(movs_imm, 7, 0)
    a.label("jb_i")
    E(cmp_imm, 7, 4); E(b_cond, "jb_ia", "hs"); E(subs_reg, 0, 6, 7); E(b, "jb_ir")
    a.label("jb_ia"); E(subs_imm3, 0, 7, 4)                                            # (then the rows 0..27)
    a.label("jb_ir"); E(cmp_imm, 0, ROWS); E(b_cond, "jb_in", "hs")
    E(lsls_imm, 0, 0, 3); E(movs_imm, 1, 0)
    a.label("jb_ic")
    E(adds_reg, 2, 0, 1); E(adds_reg, 3, 4, 2); E(raw, h(0x7800 | 0x14 << 6 | 3 << 3 | 3))   # ldrb r3, [r3, #0x14]
    E(cmp_imm, 3, 0); E(b_cond, "jb_ix", "eq")
    E(adds_reg, 3, 3, 4); E(push_list, [0]); E(movs_imm, 0, 0xF4); E(adds_reg, 3, 3, 0); E(pop_list, [0])
    E(push_list, [0]); E(ldrb_imm, 0, 3, 0); E(cmp_imm, 0, 0xFF); E(pop_list, [0]); E(b_cond, "jb_ix", "ne")
    E(strb_imm, 2, 3, 0)
    a.label("jb_ix"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, "jb_ic", "lo")
    a.label("jb_in"); E(adds_imm8, 7, 1); E(cmp_imm, 7, ROWS + 4); bc("jb_i", "lo")
    # the links: (R, c) <-> (R - 2, c - 1), (R - 1, c) <-> (R - 3, c - 1), both with a note
    for dk in (0, 1):
        E(subs_imm3, 0, 6, dk) if dk else E(mov_reg, 0, 6)
        E(cmp_imm, 0, 3); bc(f"jb_le{dk}", "lt")
        E(lsls_imm, 0, 0, 3); E(movs_imm, 1, 1)
        a.label(f"jb_l{dk}")
        E(adds_reg, 2, 0, 1); E(adds_reg, 3, 4, 2); E(raw, h(0x7800 | 0x14 << 6 | 3 << 3 | 3)); E(cmp_imm, 3, 0); E(b_cond, f"jb_ln{dk}", "eq")
        E(mov_reg, 3, 2); E(subs_imm8, 3, 17)                                          # (k - 2, c - 1)
        E(push_list, [0]); E(adds_reg, 0, 4, 3); E(raw, h(0x7800 | 0x14 << 6 | 0 << 3 | 0)); E(cmp_imm, 0, 0); E(pop_list, [0])   # ldrb r0, [r0, #0x14]
        E(b_cond, f"jb_ln{dk}", "eq")
        E(push_list, [0, 1]); E(movs_imm, 0, 0xC0); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 4)    # + 0x180 = the links
        E(strb_reg, 3, 0, 2); E(strb_reg, 2, 0, 3); E(pop_list, [0, 1])
        a.label(f"jb_ln{dk}"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, f"jb_l{dk}", "lo")
        a.label(f"jb_le{dk}")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0x98); E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 4, 1); E(strb_imm, 0, 1, 0)   # + 0x260 = 0
    E(ldr_imm, 0, 4, 4); E(bl, COMMIT)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_jkslot0 (the keyboard's slot 0): Jankó when on, else the chain (cscale's / the stock's)
    a.label("c_jkslot0")
    E(push_list, [0, 4], lr=True)
    imm32(1, KB); E(cmp_reg, 0, 1); E(b_cond, "j0_f", "ne")
    E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "j0_f", "eq")
    E(pop_list, [0, 4]); E(raw, POP_LR); E(b_w, "c_jkbuild")
    a.label("j0_f"); E(pop_list, [0, 4]); E(raw, POP_LR); E(b_w, prev["slot0"])

    # ---- c_jkq (the quantiser: r0 = the scale object, r1 = the note): the keyboard's object with Jankó = the note (clamped as the stock's)
    a.label("c_jkq")
    E(push_list, [0, 1, 4], lr=True)
    imm32(2, KB); E(ldr_imm, 2, 2, 0xC); E(cmp_reg, 0, 2); E(b_cond, "jq_f", "ne")
    E(bl, "c_jkon"); E(mov_reg, 4, 0); E(pop_list, [0, 1]); E(cmp_imm, 4, 0); E(b_cond, "jq_g", "eq")
    E(ldrb_imm, 2, 0, 0); E(cmp_reg, 1, 2); E(b_cond, "jq_l", "ge"); E(mov_reg, 1, 2)
    a.label("jq_l"); E(ldrb_imm, 2, 0, 1); E(cmp_reg, 1, 2); E(b_cond, "jq_h", "le"); E(mov_reg, 1, 2)
    a.label("jq_h"); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)
    a.label("jq_f"); E(pop_list, [0, 1])
    a.label("jq_g"); E(pop_list, [4]); E(raw, POP_LR); E(b_w, prev["quant"])

    # ---- c_jkmut (c_mutscale: r0 = a note, r1 = random bits) -> with Jankó another of the twelve notes of its octave (above the root)
    a.label("c_jkmut")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(bl, "c_jkon"); E(mov_reg, 4, 0); E(pop_list, [0, 1]); E(cmp_imm, 4, 0); E(b_cond, "jm_f", "eq")
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(2, KB); E(ldr_imm, 2, 2, 0x10); E(ldrb_imm, 2, 2, 0); E(subs_reg, 0, 4, 2); E(adds_imm8, 0, 120)   # note - root + 120
    E(movs_imm, 1, 12); E(raw, udiv(2, 0, 1)); E(muls, 2, 1); E(subs_reg, 2, 0, 2)    # r2 = m
    E(movs_imm, 1, 11); E(raw, udiv(3, 5, 1)); E(muls, 3, 1); E(subs_reg, 3, 5, 3)    # r3 = k = bits % 11
    E(cmp_reg, 3, 2); E(b_cond, "jm_k", "lo"); E(adds_imm8, 3, 1)
    a.label("jm_k"); E(subs_reg, 0, 4, 2); E(adds_reg, 0, 0, 3)
    E(cmp_imm, 0, 0); E(b_cond, "jm_p", "ge"); E(movs_imm, 0, 0)
    a.label("jm_p"); E(cmp_imm, 0, 127); E(b_cond, "jm_r", "le"); E(movs_imm, 0, 127)
    a.label("jm_r"); E(pop_list, [4, 5], pc=True)
    a.label("jm_f"); E(pop_list, [4, 5]); E(raw, POP_LR); E(b_w, prev["mut"])

    # ---- c_jkbtn (the head of the button chain: ctrl, id): Octave in a note track's Note views with Jankó = its w - 1 / + 1
    a.label("c_jkbtn")
    E(cmp_imm, 1, ID_DOWN); E(b_cond, "jk_f", "lo"); E(cmp_imm, 1, ID_UP); E(b_cond, "jk_f", "hi")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jk_p", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "jk_p", "ne")
    E(bl, "c_jktrk"); E(cmp_imm, 0, 0xFF); E(b_cond, "jk_p", "eq"); E(mov_reg, 4, 0)
    E(bl, "c_jkram"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, 4); E(raw, h(0xB249))     # sxtb r1, r1
    E(cmp_imm, 5, ID_UP); E(b_cond, "jk_d", "ne")
    E(cmp_imm, 1, WMAX); E(b_cond, "jk_w", "ge"); E(adds_imm8, 1, 1); E(b, "jk_w")
    a.label("jk_d"); E(movs_imm, 2, 0); E(subs_imm8, 2, WMAX); E(cmp_reg, 1, 2); E(b_cond, "jk_w", "le"); E(subs_imm8, 1, 1)
    a.label("jk_w"); E(strb_imm, 1, 0, 4); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("jk_p"); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("jk_f"); E(b_w, prev["btn"])

    # ---- c_jkpad (the Scales view's slot 0: view, pad, velocity): in the editor Shift + pad 8 = Jankó on / off
    a.label("c_jkpad")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, PAD_JK); bc("jp_f", "ne")
    E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); bc("jp_f", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, CS.B_ED); E(cmp_imm, 0, 0); bc("jp_f", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("jp_f", "eq")
    E(movs_imm, 5, 0)                                                                  # r5 = the keys (0 without a block)
    E(ldr_imm, 1, 4, 0); imm32(2, CS.MAGIC); E(cmp_reg, 1, 2); E(b_cond, "jp_k", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_cskeys"]); E(mov_reg, 5, 0)
    a.label("jp_k")
    E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jp_on", "eq")
    E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "jp_w", "eq"); E(movs_imm, 0, 1); E(b, "jp_w")    # off: the custom scale again (if any keys)
    a.label("jp_on"); E(movs_imm, 0, JK)
    a.label("jp_w"); E(mov_reg, 1, 5); E(bl, L["c_csput"])
    E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("jp_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

    # ---- c_jkleds (the Scales view's slot 7: view) -> r0 = its LED buffer: in the editor pad 8 cyan with Jankó, yellow with Shift
    a.label("c_jkleds")
    E(push_list, [4, 5], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); E(b_cond, "jl_x", "eq"); E(ldrb_imm, 0, 0, CS.B_ED); E(cmp_imm, 0, 0); E(b_cond, "jl_x", "eq")
    E(movs_imm, 4, COL_ON); E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jl_w", "ne")
    E(movs_imm, 4, 0); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "jl_w", "eq"); E(movs_imm, 4, COL_SHIFT)
    a.label("jl_w"); E(strh_imm, 4, 5, 2 * PAD_JK)
    a.label("jl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)

    # ---- c_jkledtask (the LED task calls: ctrl, frame): the chain; the tables rebuilt when Jankó / the track / its w / its octave change
    a.label("c_jkledtask")
    E(push_list, [3, 4, 5, 6], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_jkram"); E(mov_reg, 4, 0)
    imm32(0, CONT); E(bl, SEL_TRACK); E(cmp_imm, 0, 3); E(b_cond, "jx_t", "hi"); E(str_imm, 0, 4, 12)
    a.label("jx_t")
    E(movs_imm, 5, 0)                                                                  # r5 = the stamp wanted
    E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jx_c", "eq")
    E(ldr_imm, 6, 4, 12); E(mov_reg, 0, 6); E(bl, "c_jkoct"); E(mov_reg, 5, 0)        # octave
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, 4); E(lsls_imm, 0, 0, 8); E(orrs_reg, 5, 0)   # w << 8
    E(lsls_imm, 0, 6, 16); E(orrs_reg, 5, 0); E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 24); E(orrs_reg, 5, 0)
    a.label("jx_c")
    E(ldr_imm, 0, 4, 8); E(cmp_reg, 0, 5); E(b_cond, "jx_x", "eq")
    E(str_imm, 5, 4, 8)
    imm32(1, KB_VT); E(ldr_imm, 1, 1, 0); imm32(0, KB); E(blx_reg, 1)                  # the keyboard's slot 0 (ours first)
    a.label("jx_x"); E(pop_list, [3, 4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the keyboard's slot 0, the quantiser / c_mutscale jumps (cscale's), the Scales view's slots 0 / 7, the head
    of the button chain, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc, b_w as bw_enc
    from kbin import bw_decode
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("cscale", k) for k in ("c_csblk", "c_cskeys", "c_csput", "c_csq", "c_csmut", "c_csslot0", "c_cspad", "c_csleds")}
    L["c_shift"] = lab("sc15", "c_shift"); L["c_spk"] = lab("smpick", "c_spk"); L["c_s4on"] = lab("split4", "c_s4on")
    mut = lab("mutate39", "c_mutscale")
    k = u(ROWLIT)
    rowbase = struct.unpack("b", bytes(img[k - BASE:k - BASE + 1]))[0] + img[k + 2 - BASE]
    assert rowbase == 69, rowbase
    prev = dict(slot0=u(KB_VT) & ~1, quant=bw_decode(img, QUANT, BASE), mut=bw_decode(img, mut, BASE), pad=u(SCALES_VT) & ~1,
                leds=u(SCALES_VT + 28) & ~1, btn=MP.bw_target(img, CS.BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["slot0"] == L["c_csslot0"] and prev["quant"] == L["c_csq"] and prev["mut"] == L["c_csmut"], prev
    assert prev["pad"] == L["c_cspad"] and prev["leds"] == L["c_csleds"], prev
    code, labels = arm_code(base_addr, L, prev, rowbase)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    def put(addr, data): img[addr - BASE:addr - BASE + len(data)] = data
    put(KB_VT, struct.pack("<I", labels["c_jkslot0"] | 1))
    put(QUANT, bw_enc(QUANT, labels["c_jkq"]))
    put(mut, bw_enc(mut, labels["c_jkmut"]))
    put(SCALES_VT, struct.pack("<I", labels["c_jkpad"] | 1)); put(SCALES_VT + 28, struct.pack("<I", labels["c_jkleds"] | 1))
    put(CS.BTN_ENTRY, bw_enc(CS.BTN_ENTRY, labels["c_jkbtn"]))
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        put(c, bl_enc(c, labels["c_jkledtask"]))
    return labels, code, prev
