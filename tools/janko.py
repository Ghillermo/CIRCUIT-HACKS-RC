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

SC48.2 / Beta 3.39 (use_v2; a tester, brought by the user, 2026-10-28: «I would prefer consistency, and since the chromatic scale is quite common
(lower pitch on top), I would make Janko the same way … B0 C#1 D#1 F1 G1 A1 B1 C#2 / C1 D1 E1 F#1 G#1 A#1 C2 D2»; the user: «replace pad 8 with
their implementation, and maybe add the old one … to pad 24. Root note is still the stock scale's root (with a different color)», and short press =
semitone, long press = octave):
  * B_ON = 3 = the new layout (Shift + pad 8 in the editor), B_ON = 2 = the old one (Shift + pad 24; projects saved with the old layout keep it):
    rows in pairs, d = R - k: the row's base = 60 + w + 12 (d >> 1) - (d & 1) (the row above a semitone lower, the pair above an octave higher), + 2
    a column; links (k, c) <-> (k - 2, c - 6) for c = 6, 7 (the same notes) on the screen's rows;
  * the root's colour: the stock colours a pad with a link as a root (0x0804AD78: [keyboard + 0x180 + index] != 0xFF); with Jankó (either layout)
    its ldrb.w at 0x0804AE1E -> c_jkroot: root = the value % 12 = 0 (the values are above the root, 60 = the root), whatever the links;
  * Octave: the press = w ± 1 at once; still held HOLD_MS later (the LED task) = w0 ± 12 (an octave from where it started), clamped; the release
    (the head of 0x0803381A) cancels it;
  * RAM "JNK2": + 16 the press's time, + 20 its track, + 21 the w of the long press, + 22 its button (0 = none), + 23 the layout being built.

SC49.9 / Beta 5.2 (use_v3; the user, 2026-11-01: «Rediseña el modo Janko. Descarta el antiguo y quédate solo con el nuevo»; «Descarta pad 24 (solo pad
8). Por defecto repite sin octava, pero al mantener pulsada una nota y pulsar el botón de octave up/down (sube o baja medio tono) sólo se suben o
bajan las dos filas a las que no pertenece la nota pulsada»): one layout, Shift + pad 8 (B_ON 3; a project saved with 2, the first layout, gets it too):
  * rows in pairs: the row above a semitone lower, + 2 a column; the upper pair (d >= 2) repeats the lower one, each pair with its own offset per track:
    the lower + 4 + t (w), the upper + 24 + t;
  * Octave with no key held, or in the 2-row Note view, or on the chord screen (its rows 1-2 are not keys) = both pairs, as before;
  * Octave in the expanded Note view with keys held ([MGR + 0x84] = the pads held, bit = pad): only the pair with no key held moves; keys held in both
    pairs: nothing moves.  The long press the same way: that pair an octave from where it started;
  * the links: any pad of the lower pair <-> the pad of the upper pair with its note, whatever the offset (at most one: the notes of a pair differ);
  * RAM "JNK3": as "JNK2" without + 23, + 24..27 the upper pair's offsets, + 28 the long press's upper offset.  Not saved, as w.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg,  # noqa: E402
                   ldrh_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm,
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
V2 = False                                               # SC48.2 (use_v2): the new layout on pad 8, the old one on pad 24, root colour, long press
JK3 = 3                                                  # (V2) B_ON = the new layout
RSIG2 = 0x324B4E4A                                       # "JNK2"
V3 = False                                               # SC49.9 (use_v3): one layout, two pairs of rows that move apart
RSIG3 = 0x334B4E4A                                       # "JNK3"
HELD = MGR + 0x84                                        # the pads held, bit = pad: pads 1-16 the upper pair, pads 17-32 the lower one
CH_FLAGS, CH_ON = MX.MXR + 0x520 + 4, 1                  # chords' flags[track], bit 0 = the chord screen on (chords comes after us in the hole)
O_UP, O_LONG2 = 24, 28                                   # (V3) the upper pair's offset[track]; the long press's
PAD_JK2 = 23                                             # (V2) pad 24 = the old layout
HAL_TICK = 0x2000081C                                    # 1 ms
HOLD_MS = 400
BTN_REL = 0x0803381A                                     # the button release (ctrl, id): a b.w to the chain of heads
COLOUR_AT, COLOUR_OLD = 0x0804AE1E, bytes.fromhex("91f88011")   # in 0x0804AD78: ldrb.w r1, [r1, #0x180] (the link: a root's colour)


V4 = False                                               # SC52.6 (use_v4): rows 1 / 3 move with keys held in rows 2 and 4
RSIG4 = 0x344B4E4A                                       # "JNK4"
INNER = MX.MXR + 0x1EE0                                  # (V4) + t = the offset of rows 1 / 3 (the upper row of each pair) of track t (s8)
O_LONG3 = 23                                             # (V4) the long press's inner offset (+ 23: free in V3; + 29 is jumpoct's O_PREV)
ROW13 = 0x00FF00FF                                       # (V4) the pads of rows 1 / 3 in [MGR + 0x84]


def use_v4():
    """SC52.6 / Beta 5.29 (the user, 2026-11-06: «Nueva característica en Jankó: al aguantar un pad en las filas 2 y 4 simultáneamente, los
    botones up y down mueven las filas 1 y 3»): in the expanded Note view, keys held in rows 2 and 4 (one or more in each, none in rows 1 / 3) =
    Octave moves rows 1 and 3 (the upper row of each pair): a third offset per track (INNER, RAM, not saved, as the others) added to those rows'
    − 1; the short press ± 1 semitone, the long one an octave from where it started, clamped ± WMAX; the tables rebuilt (the stamp's bits 18-23).
    Keys in both pairs otherwise: nothing moves, as before."""
    global V4
    assert V3
    V4 = True


JUMP = False                                             # SC50 (use_jump): RAM + O_JUMP = jumpseq's flags (a pointing track's Note view on the screen; its clock)
O_JUMP = 30                                              # (free in V3, cleared by c_jkram with the word of O_LONG2)


def use_jump():
    """SC50 / Beta 5.3 (the user, 2026-11-01: «algunas configuraciones de Janko contienen pads con todo notas distintas … hacer que se aplique automáticamente sin
    romper el Janko original»): while jumpseq's flags are on, c_jkon answers "the layout" whatever the project's block says, so a pointing MIDI track gets these
    tables and the quantiser leaves its notes; Octave there is the stock's (jumpseq takes the page from the octave)."""
    global JUMP
    assert V3
    JUMP = True


def use_v2():
    """SC48.2: the tester's layout (the row above a semitone lower) on Shift + pad 8, the first one on Shift + pad 24, the root in its colour, a
    long Octave press = an octave."""
    global V2
    V2 = True


def use_v3():
    """SC49.9 / Beta 5.2: one layout, the upper pair repeats the lower one and each pair has its own offset (the module's docstring)."""
    global V3
    V3 = True


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
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG4 if V4 else RSIG3 if V3 else RSIG2 if V2 else RSIG); E(cmp_reg, 1, 2); E(b_cond, "jr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    if V4: imm32(2, INNER); E(str_imm, 1, 2, 0)
    if V2: E(str_imm, 1, 0, 16); E(str_imm, 1, 0, 20)
    if V3: E(str_imm, 1, 0, O_UP); E(str_imm, 1, 0, O_LONG2)
    a.label("jr_x"); E(raw, RET)

    # ---- c_jkon() -> r0 = 1 with Jankó on (the custom scale's block valid, B_ON = 2); clobbers r1-r3
    a.label("c_jkon")
    E(push_list, [4], lr=True)
    if JUMP:
        E(bl, "c_jkram"); E(ldrh_imm, 0, 0, O_JUMP); E(cmp_imm, 0, 0); E(b_cond, "jo_j", "eq"); E(movs_imm, 0, JK3); E(pop_list, [4], pc=True)
        a.label("jo_j")
    E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); E(b_cond, "jo_0", "eq"); E(mov_reg, 4, 0)
    E(ldr_imm, 1, 4, 0); imm32(2, CS.MAGIC); E(cmp_reg, 1, 2); E(b_cond, "jo_0", "ne")
    E(ldrb_imm, 1, 4, CS.B_ON); E(cmp_imm, 1, JK)
    if V2: E(b_cond, "jo_2", "eq"); E(cmp_imm, 1, JK3)
    E(b_cond, "jo_0", "ne")
    if V2: a.label("jo_2")                                                             # (r1 = B_ON: the check byte holds it)
    for k in range(3): E(ldrb_imm, 2, 4, CS.B_KEYS + k); E(raw, h(0x4051))              # eors r1, r2
    E(movs_imm, 2, 0x5A); E(raw, h(0x4051)); E(ldrb_imm, 2, 4, CS.B_SUM); E(cmp_reg, 1, 2); E(b_cond, "jo_0", "ne")
    if V2: E(ldrb_imm, 0, 4, CS.B_ON); E(pop_list, [4], pc=True)                      # (V2) r0 = the layout, 2 or 3
    else: E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
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
    if V2 and not V3: E(bl, "c_jkon"); E(mov_reg, 5, 0); E(bl, "c_jkram"); E(strb_imm, 5, 0, 23)   # (V2) the layout being built
    E(bl, "c_jkram"); E(ldr_imm, 1, 0, 12); E(mov_reg, 7, 1); E(adds_reg, 0, 0, 1); E(ldrb_imm, 5, 0, 4)
    E(raw, h(0xB26D))                                                                  # sxtb r5, r5: w
    E(mov_reg, 0, 7); E(bl, "c_jkoct"); E(movs_imm, 6, rowbase + 3); E(subs_reg, 6, 6, 0)   # R = 69 - octave + 3
    if V2: E(adds_imm8, 5, 60)                                                          # (V2) r5 = the bottom-left pad's value
    else: E(adds_imm8, 5, 60); E(adds_reg, 5, 5, 6)                                    # row 0's base
    E(movs_imm, 7, 0)
    a.label("jb_r")
    if V2: E(subs_reg, 0, 6, 7); E(bl, "c_jkrowf"); E(adds_reg, 0, 0, 5); E(movs_imm, 1, 0)   # the row's base = r5 + f(R - k)
    else: E(subs_reg, 0, 5, 7); E(movs_imm, 1, 0)                                      # r0 = the row's base, r1 = the column
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
    if V3:
        # the links: each pad of the lower pair <-> the pad of the upper pair with its note (r5, r7 = the two indices, r6 = (R, 0))
        E(cmp_imm, 6, 3); bc("jb_ld", "lt")
        E(lsls_imm, 6, 6, 3); E(mov_reg, 5, 6); E(subs_imm8, 5, 8)                     # r5 = (R - 1, 0)
        a.label("jb_lp")
        E(adds_reg, 0, 4, 5); E(raw, h(0x7800 | 0x14 << 6 | 0 << 3 | 0)); E(cmp_imm, 0, 0); E(b_cond, "jb_lx", "eq")   # ldrb r0, [r0, #0x14]
        E(mov_reg, 7, 6); E(subs_imm8, 7, 24)                                          # r7 = (R - 3, 0)
        a.label("jb_lq")
        E(adds_reg, 1, 4, 7); E(raw, h(0x7800 | 0x14 << 6 | 1 << 3 | 1)); E(cmp_reg, 0, 1); E(b_cond, "jb_ly", "ne")   # ldrb r1, [r1, #0x14]
        E(movs_imm, 1, 0xC0); E(lsls_imm, 1, 1, 1); E(adds_reg, 1, 1, 4)              # + 0x180 = the links
        E(strb_reg, 7, 1, 5); E(strb_reg, 5, 1, 7); E(b, "jb_lx")
        a.label("jb_ly"); E(adds_imm8, 7, 1); E(mov_reg, 1, 6); E(subs_imm8, 1, 8); E(cmp_reg, 7, 1); E(b_cond, "jb_lq", "lo")
        a.label("jb_lx"); E(adds_imm8, 5, 1); E(mov_reg, 1, 6); E(adds_imm8, 1, 8); E(cmp_reg, 5, 1); E(b_cond, "jb_lp", "lo")
        a.label("jb_ld")
    else:
        # the links: (R, c) <-> (R - 2, c - 1), (R - 1, c) <-> (R - 3, c - 1), both with a note
        #   (V2: the old layout as before; the new one (R, c) <-> (R - 2, c - 6) and (R - 1, c) <-> (R - 3, c - 6), c = 6, 7)
        for mode, co in (((JK, 1), (JK3, 6)) if V2 else ((None, 1),)):
            sfx = f"m{mode}" if V2 else ""
            if V2: imm32(0, RAM); E(ldrb_imm, 0, 0, 23); E(cmp_imm, 0, mode); bc(f"jb_lm{mode}", "ne")
            for dk in (0, 1):
                E(subs_imm3, 0, 6, dk) if dk else E(mov_reg, 0, 6)
                E(cmp_imm, 0, 3); bc(f"jb_le{dk}{sfx}", "lt")
                E(lsls_imm, 0, 0, 3); E(movs_imm, 1, co)
                a.label(f"jb_l{dk}{sfx}")
                E(adds_reg, 2, 0, 1); E(adds_reg, 3, 4, 2); E(raw, h(0x7800 | 0x14 << 6 | 3 << 3 | 3)); E(cmp_imm, 3, 0); E(b_cond, f"jb_ln{dk}{sfx}", "eq")
                E(mov_reg, 3, 2); E(subs_imm8, 3, 16 + co)                                 # (k - 2, c - co)
                E(push_list, [0]); E(adds_reg, 0, 4, 3); E(raw, h(0x7800 | 0x14 << 6 | 0 << 3 | 0)); E(cmp_imm, 0, 0); E(pop_list, [0])   # ldrb r0, [r0, #0x14]
                E(b_cond, f"jb_ln{dk}{sfx}", "eq")
                E(push_list, [0, 1]); E(movs_imm, 0, 0xC0); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 4)    # + 0x180 = the links
                E(strb_reg, 3, 0, 2); E(strb_reg, 2, 0, 3); E(pop_list, [0, 1])
                a.label(f"jb_ln{dk}{sfx}"); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, f"jb_l{dk}{sfx}", "lo")
                a.label(f"jb_le{dk}{sfx}")
            if V2: a.label(f"jb_lm{mode}")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0x98); E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 4, 1); E(strb_imm, 0, 1, 0)   # + 0x260 = 0
    E(ldr_imm, 0, 4, 4); E(bl, COMMIT)
    E(pop_list, [4, 5, 6, 7], pc=True)

    if V3:
        # ---- c_jkrowf(r0 = d = R - k) -> r0 = the row's offset from the bottom-left pad: - (d & 1), + the upper pair's offset from the lower for
        #      d >= 2; clobbers r1, r2
        a.label("c_jkrowf")
        E(movs_imm, 1, 1); E(ands_reg, 1, 0)
        if V4:                                                                         # (V4) an upper row of a pair: - 1 + its offset
            E(cmp_imm, 1, 0); E(b_cond, "jf_o", "eq"); E(push_list, [3])
            imm32(3, RAM); E(ldr_imm, 3, 3, 12); imm32(2, INNER); E(adds_reg, 2, 2, 3); E(ldrb_imm, 2, 2, 0); E(raw, h(0xB252))   # sxtb r2, r2
            E(movs_imm, 1, 1); E(subs_reg, 1, 1, 2); E(pop_list, [3])
            a.label("jf_o")
        E(cmp_imm, 0, 2); E(b_cond, "jf_l", "lt")
        imm32(0, RAM); E(ldr_imm, 2, 0, 12); E(adds_reg, 2, 2, 0); E(ldrb_imm, 0, 2, O_UP); E(raw, h(0xB240))   # sxtb r0, r0
        E(ldrb_imm, 2, 2, 4); E(raw, h(0xB252)); E(subs_reg, 0, 0, 2); E(subs_reg, 0, 0, 1); E(raw, RET)        # sxtb r2, r2
        a.label("jf_l"); E(movs_imm, 0, 0); E(subs_reg, 0, 0, 1); E(raw, RET)
    elif V2:
        # ---- c_jkrowf(r0 = d = R - k) -> r0 = the row's offset from the bottom-left pad: d (the old layout), 12 (d >> 1) - (d & 1) (the new);
        #      clobbers r1, r2
        a.label("c_jkrowf")
        imm32(1, RAM); E(ldrb_imm, 1, 1, 23); E(cmp_imm, 1, JK3); E(b_cond, "jf_x", "ne")
        E(raw, h(0x1041))                                                              # asrs r1, r0, #1
        E(movs_imm, 2, 12); E(muls, 1, 2); E(movs_imm, 2, 1); E(ands_reg, 2, 0); E(subs_reg, 0, 1, 2)
        a.label("jf_x"); E(raw, RET)

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

    if not V2:
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

    else:
        # ---- c_jkclamp(r0 = w) -> r0 within -WMAX..WMAX; clobbers r3
        a.label("c_jkclamp")
        E(cmp_imm, 0, WMAX); E(b_cond, "jc_l", "le"); E(movs_imm, 0, WMAX)
        a.label("jc_l"); E(movs_imm, 3, 0); E(subs_imm8, 3, WMAX); E(cmp_reg, 0, 3); E(b_cond, "jc_x", "ge"); E(mov_reg, 0, 3)
        a.label("jc_x"); E(raw, RET)

        if V3:
            # ---- c_jkmove(r0 = an offset's address, r2 = the step): offset = clamp(offset + step) -> r0 = clamp(the old offset + 12 steps); clobbers r1, r3
            a.label("c_jkmove")
            E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 2)
            E(ldrb_imm, 1, 4, 0); E(raw, h(0xB249)); E(adds_reg, 0, 1, 2); E(bl, "c_jkclamp"); E(strb_imm, 0, 4, 0)   # sxtb r1, r1
            E(movs_imm, 0, 12); E(muls, 0, 5); E(adds_reg, 0, 0, 1); E(bl, "c_jkclamp"); E(pop_list, [4, 5], pc=True)

            # ---- c_jkbtn (the head of the button chain: ctrl, id): Octave in a note track's Note views with Jankó: the pairs that move (r7: bit 0 the
            #      lower, bit 1 the upper) ± 1 now; the long press (the LED task, HOLD_MS later) = their offsets of the press ± 12
            a.label("c_jkbtn")
            E(cmp_imm, 1, ID_DOWN); E(b_cond, "jk_f", "lo"); E(cmp_imm, 1, ID_UP); E(b_cond, "jk_f", "hi")
            E(push_list, [0, 1, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
            E(bl, "c_jkon"); E(cmp_imm, 0, 0); bc("jk_p", "eq")
            if JUMP: E(bl, "c_jkram"); E(ldrb_imm, 0, 0, O_JUMP); E(cmp_imm, 0, 0); bc("jk_p", "ne")
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("jk_p", "ne")
            E(bl, "c_jktrk"); E(cmp_imm, 0, 0xFF); bc("jk_p", "eq"); E(mov_reg, 4, 0)
            E(movs_imm, 7, 3)
            imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 0, 9); E(muls, 0, 4); E(adds_imm8, 0, 6); E(cmp_reg, 0, 1); E(b_cond, "jk_m", "ne")   # the expanded view
            imm32(0, CH_FLAGS); E(ldrb_reg, 0, 0, 4); E(movs_imm, 1, CH_ON); E(raw, h(0x4208)); E(b_cond, "jk_m", "ne")   # tst r0, r1: the chord screen on
            imm32(0, HELD); E(ldr_imm, 0, 0, 0)
            E(lsls_imm, 1, 0, 16); E(b_cond, "jk_u", "eq"); E(movs_imm, 7, 1)             # a key of the upper pair held: only the lower one moves
            a.label("jk_u"); E(lsrs_imm, 0, 0, 16); E(b_cond, "jk_v", "eq"); E(movs_imm, 1, 1); E(bics_reg, 7, 1)   # a key of the lower pair: not the lower one
            a.label("jk_v"); E(cmp_imm, 7, 0)
            if V4:                                                                     # (V4) keys of both, only in rows 2 / 4: rows 1 / 3 move
                E(b_cond, "jk_m", "ne")
                imm32(0, HELD); E(ldr_imm, 0, 0, 0); imm32(1, ROW13); E(raw, h(0x4208)); E(b_cond, "jk_x", "ne")   # tst r0, r1
                E(movs_imm, 7, 4)
            else:
                E(b_cond, "jk_x", "eq")                                                # keys of both: nothing moves
            a.label("jk_m")
            E(bl, "c_jkram"); E(mov_reg, 6, 0)
            E(strb_imm, 4, 6, 20); E(strb_imm, 5, 6, 22)
            E(movs_imm, 2, 1); E(cmp_imm, 5, ID_UP); E(b_cond, "jk_s", "eq"); E(movs_imm, 2, 0); E(subs_imm8, 2, 1)
            a.label("jk_s"); E(mov_reg, 5, 2)                                             # r5 = the step, +- 1
            for bit, off, tgt in ((1, 4, 21), (2, O_UP, O_LONG2)):
                E(adds_reg, 0, 6, 4); E(adds_imm8, 0, off)
                E(movs_imm, 1, bit); E(raw, h(0x420F)); E(b_cond, f"jk_n{bit}", "eq")      # tst r7, r1
                E(mov_reg, 2, 5); E(bl, "c_jkmove"); E(b, f"jk_w{bit}")
                a.label(f"jk_n{bit}"); E(ldrb_imm, 0, 0, 0)
                a.label(f"jk_w{bit}"); E(strb_imm, 0, 6, tgt)
            if V4:
                imm32(0, INNER); E(adds_reg, 0, 0, 4)
                E(movs_imm, 1, 4); E(raw, h(0x420F)); E(b_cond, "jk_n4", "eq")             # tst r7, r1
                E(mov_reg, 2, 5); E(bl, "c_jkmove"); E(b, "jk_w4")
                a.label("jk_n4"); E(ldrb_imm, 0, 0, 0)
                a.label("jk_w4"); E(strb_imm, 0, 6, O_LONG3)
            imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 6, 16)
            a.label("jk_x"); E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
            a.label("jk_p"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True))
            a.label("jk_f"); E(b_w, prev["btn"])
        else:
            # ---- c_jkbtn (the head of the button chain: ctrl, id): Octave in a note track's Note views with Jankó = its w ± 1 now; the long press
            #      (the LED task, HOLD_MS later) = the w of the press ± 12
            a.label("c_jkbtn")
            E(cmp_imm, 1, ID_DOWN); E(b_cond, "jk_f", "lo"); E(cmp_imm, 1, ID_UP); E(b_cond, "jk_f", "hi")
            E(push_list, [0, 1, 4, 5, 6], lr=True); E(mov_reg, 5, 1)
            E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jk_p", "eq")
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "jk_p", "ne")
            E(bl, "c_jktrk"); E(cmp_imm, 0, 0xFF); E(b_cond, "jk_p", "eq"); E(mov_reg, 4, 0)
            E(bl, "c_jkram"); E(mov_reg, 6, 0); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, 4); E(raw, h(0xB249))   # sxtb r1, r1: w0
            E(movs_imm, 2, 1); E(cmp_imm, 5, ID_UP); E(b_cond, "jk_s", "eq"); E(movs_imm, 2, 0); E(subs_imm8, 2, 1)   # r2 = the step, +- 1
            a.label("jk_s")
            E(adds_reg, 0, 1, 2); E(bl, "c_jkclamp"); E(adds_reg, 3, 6, 4); E(strb_imm, 0, 3, 4)           # w = w0 +- 1
            E(movs_imm, 0, 12); E(muls, 0, 2); E(adds_reg, 0, 0, 1); E(bl, "c_jkclamp"); E(strb_imm, 0, 6, 21)   # the long press's w0 +- 12
            E(strb_imm, 4, 6, 20); E(strb_imm, 5, 6, 22)
            imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 6, 16)
            E(pop_list, [0, 1, 4, 5, 6], pc=True)
            a.label("jk_p"); E(raw, popw([0, 1, 4, 5, 6], lr=True))
            a.label("jk_f"); E(b_w, prev["btn"])

        # ---- c_jkrel (the head of the button release: ctrl, id): the release of the Octave button pressed cancels its long press
        a.label("c_jkrel")
        E(push_list, [0, 1], lr=True)
        E(bl, "c_jkram"); E(ldrb_imm, 2, 0, 22); E(ldr_sp, 1, 4); E(cmp_reg, 2, 1); E(b_cond, "jr2_x", "ne")
        E(movs_imm, 2, 0); E(strb_imm, 2, 0, 22)
        a.label("jr2_x"); E(pop_list, [0, 1]); E(raw, POP_LR); E(b_w, prev["rel"])

        # ---- c_jkroot (0x0804AE1E in the pad colour 0x0804AD78: r1 = keyboard + index) -> r1 = its link (0xFF = not a root's colour); with
        #      Jankó a root = the value % 12 = 0 (r1 = 0) whatever the links; clobbers r0, r2, r3
        a.label("c_jkroot")
        E(push_list, [1], lr=True)
        E(bl, "c_jkon"); E(pop_list, [1]); E(cmp_imm, 0, 0); E(b_cond, "jo2_s", "eq")
        E(raw, h(0x7800 | 0x14 << 6 | 1 << 3 | 0))                                     # ldrb r0, [r1, #0x14]: the value
        E(movs_imm, 2, 12); E(raw, udiv(3, 0, 2)); E(muls, 3, 2); E(subs_reg, 0, 0, 3)
        E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "jo2_x", "eq"); E(movs_imm, 1, 0xFF)
        a.label("jo2_x"); E(raw, h(0xBD00))                                             # pop {pc}
        a.label("jo2_s"); E(movs_imm, 0, 0xC0); E(lsls_imm, 0, 0, 1); E(ldrb_reg, 1, 1, 0); E(raw, h(0xBD00))   # the stock's link

        if V3:
            # ---- c_jkpad (the Scales view's slot 0: view, pad, velocity): in the editor Shift + pad 8 = Jankó on / off
            a.label("c_jkpad")
            E(push_list, [0, 1, 2, 4, 5], lr=True)
            E(cmp_imm, 1, PAD_JK); bc("jp_f", "ne")
            E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); bc("jp_f", "eq"); E(mov_reg, 4, 0)
            E(ldrb_imm, 0, 4, CS.B_ED); E(cmp_imm, 0, 0); bc("jp_f", "eq")
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("jp_f", "eq")
            E(movs_imm, 5, 0)                                                              # r5 = the keys (0 without a block)
            E(ldr_imm, 1, 4, 0); imm32(2, CS.MAGIC); E(cmp_reg, 1, 2); E(b_cond, "jp_k", "ne")
            E(mov_reg, 0, 4); E(bl, L["c_cskeys"]); E(mov_reg, 5, 0)
            a.label("jp_k")
            E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jp_on", "eq")
            E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "jp_w", "eq"); E(movs_imm, 0, 1); E(b, "jp_w")    # off: the custom scale again (if any keys)
            a.label("jp_on"); E(movs_imm, 0, JK3)
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
        else:
            # ---- c_jkpad (the Scales view's slot 0: view, pad, velocity): in the editor Shift + pad 8 = the new layout on / off, Shift + pad 24 =
            #      the old one
            a.label("c_jkpad")
            E(push_list, [0, 1, 2, 4, 5], lr=True)
            E(cmp_imm, 1, PAD_JK); E(b_cond, "jp_y", "eq"); E(cmp_imm, 1, PAD_JK2); bc("jp_f", "ne")
            a.label("jp_y")
            E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); bc("jp_f", "eq"); E(mov_reg, 4, 0)
            E(ldrb_imm, 0, 4, CS.B_ED); E(cmp_imm, 0, 0); bc("jp_f", "eq")
            E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("jp_f", "eq")
            E(movs_imm, 5, 0)                                                              # r5 = the keys (0 without a block)
            E(ldr_imm, 1, 4, 0); imm32(2, CS.MAGIC); E(cmp_reg, 1, 2); E(b_cond, "jp_k", "ne")
            E(mov_reg, 0, 4); E(bl, L["c_cskeys"]); E(mov_reg, 5, 0)
            a.label("jp_k")
            E(movs_imm, 4, JK3); E(ldr_sp, 1, 4); E(cmp_imm, 1, PAD_JK); E(b_cond, "jp_m", "eq"); E(movs_imm, 4, JK)   # r4 = the layout of the pad
            a.label("jp_m")
            E(bl, "c_jkon"); E(cmp_reg, 0, 4); E(b_cond, "jp_on", "ne")
            E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "jp_w", "eq"); E(movs_imm, 0, 1); E(b, "jp_w")    # off: the custom scale again (if any keys)
            a.label("jp_on"); E(mov_reg, 0, 4)
            a.label("jp_w"); E(mov_reg, 1, 5); E(bl, L["c_csput"])
            E(pop_list, [0, 1, 2, 4, 5], pc=True)
            a.label("jp_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])

            # ---- c_jkleds (the Scales view's slot 7: view) -> r0 = its LED buffer: in the editor pad 8 / 24 cyan with their layout, yellow with
            #      Shift
            a.label("c_jkleds")
            E(push_list, [4, 5, 6], lr=True)
            E(bl, prev["leds"]); E(mov_reg, 5, 0)
            E(bl, L["c_csblk"]); E(cmp_imm, 0, 0); E(b_cond, "jl_x", "eq"); E(ldrb_imm, 0, 0, CS.B_ED); E(cmp_imm, 0, 0); E(b_cond, "jl_x", "eq")
            E(bl, "c_jkon"); E(mov_reg, 6, 0)
            for pad, mode in ((PAD_JK, JK3), (PAD_JK2, JK)):
                E(movs_imm, 4, COL_ON); E(cmp_imm, 6, mode); E(b_cond, f"jl_w{pad}", "eq")
                E(movs_imm, 4, 0); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, f"jl_w{pad}", "eq"); E(movs_imm, 4, COL_SHIFT)
                a.label(f"jl_w{pad}"); E(strh_imm, 4, 5, 2 * pad)
            a.label("jl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_jkledtask (the LED task calls: ctrl, frame): the chain; the tables rebuilt when Jankó / the track / its w / its octave change
    a.label("c_jkledtask")
    E(push_list, [3, 4, 5, 6], lr=True)
    E(bl, prev["ledtask"])
    E(bl, "c_jkram"); E(mov_reg, 4, 0)
    if V2:
        # a long press: HOLD_MS after it, still held = the w of the press +- 12
        E(ldrb_imm, 0, 4, 22); E(cmp_imm, 0, 0); E(b_cond, "jh_x", "eq")
        imm32(1, HAL_TICK); E(ldr_imm, 1, 1, 0); E(ldr_imm, 0, 4, 16); E(subs_reg, 1, 1, 0)
        imm32(0, HOLD_MS); E(cmp_reg, 1, 0); E(b_cond, "jh_x", "lo")
        E(ldrb_imm, 0, 4, 20); E(adds_reg, 0, 4, 0); E(ldrb_imm, 1, 4, 21); E(strb_imm, 1, 0, 4)
        if V3: E(ldrb_imm, 1, 4, O_LONG2); E(strb_imm, 1, 0, O_UP)
        if V4: E(ldrb_imm, 1, 4, O_LONG3); E(ldrb_imm, 0, 4, 20); imm32(2, INNER); E(strb_reg, 1, 2, 0)
        E(movs_imm, 0, 0); E(strb_imm, 0, 4, 22)
        a.label("jh_x")
    imm32(0, CONT); E(bl, SEL_TRACK); E(cmp_imm, 0, 3); E(b_cond, "jx_t", "hi"); E(str_imm, 0, 4, 12)
    a.label("jx_t")
    E(movs_imm, 5, 0)                                                                  # r5 = the stamp wanted
    E(bl, "c_jkon"); E(cmp_imm, 0, 0); E(b_cond, "jx_c", "eq")
    if V2:
        if V3:                                                                         # (0x80 | the upper pair's offset) << 24
            E(ldr_imm, 6, 4, 12)
            E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_UP); E(movs_imm, 5, 0x7F); E(ands_reg, 5, 0); E(movs_imm, 0, 0x80); E(orrs_reg, 5, 0); E(lsls_imm, 5, 5, 24)
            E(mov_reg, 0, 6); E(bl, "c_jkoct"); E(orrs_reg, 5, 0)                      # octave
        else:
            E(lsls_imm, 5, 0, 24)                                                      # the layout << 24
            E(ldr_imm, 6, 4, 12); E(mov_reg, 0, 6); E(bl, "c_jkoct"); E(orrs_reg, 5, 0)    # octave
        E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, 4); E(lsls_imm, 0, 0, 8); E(orrs_reg, 5, 0)   # w << 8
        E(lsls_imm, 0, 6, 16); E(orrs_reg, 5, 0)
        if V4:                                                                         # (V4) the inner offset & 63 << 18
            imm32(0, INNER); E(adds_reg, 0, 0, 6); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 0x3F); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 18); E(orrs_reg, 5, 0)
    else:
        E(ldr_imm, 6, 4, 12); E(mov_reg, 0, 6); E(bl, "c_jkoct"); E(mov_reg, 5, 0)    # octave
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
    if V2: prev["rel"] = MP.bw_target(img, BTN_REL, BASE)
    assert prev["slot0"] == L["c_csslot0"] and prev["quant"] == L["c_csq"] and prev["mut"] == L["c_csmut"], prev
    assert prev["pad"] == L["c_cspad"] and prev["leds"] == L["c_csleds"], prev
    assert V2 or not V3
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
    if V2:
        put(BTN_REL, bw_enc(BTN_REL, labels["c_jkrel"]))
        assert bytes(img[COLOUR_AT - BASE:COLOUR_AT - BASE + 4]) == COLOUR_OLD
        put(COLOUR_AT, bl_enc(COLOUR_AT, labels["c_jkroot"]))
    return labels, code, prev
