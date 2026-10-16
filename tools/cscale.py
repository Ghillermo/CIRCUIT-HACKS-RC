"""SC42.2 (the user, 2026-10-16): a custom scale for the note tracks.

«Shift + Scales; then on a chromatic keyboard the intervals (up to 7) and the root; the last note is the root of the next iteration (the iterations as
octave rows)».  Decisions: 1-7 notes of scale + one more for the period; the editor = a 2-octave keyboard like the stock's chromatic one (black keys
above, white keys below; a period of up to 24); saved with the project; the root is the stock's (the Scales view).  And: «if the period is four notes
or less, two iterations on the same row».

The stock (read in the firmware, emulated):
  * one keyboard object for the four note tracks, 0x20041044 ([track view + 0x38], vtable 0x0805C144): + 0xC the scale object of the quantiser
    0x080408C6 ({min, max, a 2-bit mask x 12}), + 0x14 the table index -> note (28 rows of 8; 0 = no note), + 0xF4 the reverse table note -> first
    index (140 B, 0xFF = none), + 0x180 the links between a row's root and the octave note of the row below (0xFF = none), + 0x260 1 = chromatic layout;
  * its slot 0 (0x0804C56E) builds the three tables: chromatic (scale 15) or the scale (0x0804C404: 13 rows an octave apart, each row = the degrees +
    the octave, the rest of the row 0); the values do not depend on the root (it is applied later); row 9 starts at 60;
  * the track view plays [keyboard + 0x14 + pad + 8 x (69 - its octave)] (Octave down / up = one row);
  * Scales = button 18: case 18 of the controller opens the Scales view with 0x0803390C(ctrl, 4, 18); with Shift the stock drops it (not in the mask);
    the Scales view 0x20044058 (vtable 0x0805B2E0): slot 0 the pads (0-15 the roots, 16-31 the 16 scales), slot 7 its 32 LEDs.

Ours:
  * the block in the session record's tail + 544 (saved with the project): "CSC1", a check byte, on, the keys pressed (bits 1..24 = the intervals;
    the highest = the period P, the others the degrees above the root); RAM only: + 556 the stamp of what the keyboard holds, + 560 the editor;
  * the keyboard's slot 0 -> c_csslot0: with the custom scale on, c_csbuild: the same tables, row 9 starting at 60, every row one iteration (the n
    degrees and the period note; n + 1 <= 8) or, with n <= 4, two (one in each half of the row, without the period note); links as the stock's (one
    iteration a row only);
  * the quantiser's first 4 bytes -> c_csq: for the keyboard's scale object, the nearest note of the custom scale (period P, ties down), clamped as
    the stock's; random-mutate (mutate39's c_mutscale) -> c_csmut: another degree of the same iteration;
  * Shift + Scales (head of the button chain) toggles the editor (opening the Scales view): pads = 2 octaves of a piano from the root (rows 3 / 1 the
    black keys, 4 / 2 the white ones: interval 0..12 below, 12..24 above); a key toggles its interval (7 at most); root white, degrees green, the
    period orange, the free keys dim; Scales again / another view leaves; a stock scale (pads 17-32 out of the editor) switches the custom scale off
    (the keys are kept: the editor switches it on again); the stock's selected scale is not shown while the custom scale is on;
  * the LED task: leaves the editor with the view; rebuilds the keyboard when what it holds differs from the project's (stamp); the Scales LED yellow
    with Shift held;
  * a project load / a new project: stamp unknown, editor off (a new project: no block).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg,
                   strh_imm, strh_reg, sub_sp_imm, add_sp_imm, subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402
from build_sc14 import udiv  # noqa: E402

MGR = 0x20040B10
BTN_ENTRY = MP.BTN_ENTRY
ID_SCALES = 18
OPEN_VIEW, SCALES_VIEW_ID = 0x0803390C, 4                  # (ctrl, 4, 18): case 18 of the controller
SCALES_VIEW, SCALES_VT = 0x20044058, 0x0805B2E0
KB, KB_VT = 0x20041044, 0x0805C144
KB_SLOT0 = 0x0804C56E
KB_CLEAR = 0x0804C334                                      # the three tables cleared (0 / 0xFF / 0xFF)
COMMIT, PARAM_GET = 0x080353C0, 0x0803542C
QUANT, QUANT_OLD, QUANT_BACK = 0x080408C6, bytes.fromhex("0b460246"), 0x080408CA   # mov r3, r1; mov r2, r0
MUT_OLD = bytes.fromhex("f0b50446")                        # c_mutscale: push {r4-r7, lr}; mov r4, r0
SESSION_OBJ, TAIL, O_BLK = 0x2003D71C, 0x27024, 544
B_SUM, B_ON, B_KEYS, B_STAMP, B_ED = 4, 5, 6, 12, 16       # (from the block)
MAGIC = 0x31435343                                         # "CSC1"
ANCHOR, ANCHOR_ROW, ROWS, VMAX = 60, 9, 28, 139
MAXKEYS = 7
COL_ROOT, COL_DEG, COL_PER, COL_FREE = 0x01, 0x17, 0x09, 0x02
MUTROOT = False                                            # SC42.6 (use_mutroot): random-mutate counts the degrees from the root


def use_mutroot():
    """SC42.6: c_csmut took the step's note as if the root were C (the keyboard's values are above the root): with another root random-mutate
    picked degrees of a shifted scale.  The note above the root is used, as the stock's c_mutscale does."""
    global MUTROOT
    MUTROOT = True
COL_SHIFT = 0x2D
# the editor's keyboard: pad -> interval (0xFF none); rows 1 / 2 = the upper octave (black / white), rows 3 / 4 the lower one
PIANO = bytes([0xFF, 13, 15, 0xFF, 18, 20, 22, 0xFF,  12, 14, 16, 17, 19, 21, 23, 24,
               0xFF, 1, 3, 0xFF, 6, 8, 10, 0xFF,       0, 2, 4, 5, 7, 9, 11, 12])
INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}
LED_SCALES = 50                                            # the Scales button's LED (dim 0x02 out of its view, 0x13 in it: emulated)


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_c{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- data: the editor's keyboard
    E(raw, PIANO)
    t_piano = base

    # ---- c_csblk() -> r0 = the block (the record's tail + 544), or 0; clobbers r1
    a.label("c_csblk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("bk_x"); E(raw, h(0x4770))

    # ---- c_cskp(r0 = keys) -> r0 = the highest bit (the period), r1 = how many, r2 = the keys; clobbers r3
    a.label("c_cskp")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 3, 0); E(mov_reg, 2, 4)
    a.label("kp_l"); E(cmp_imm, 2, 0); E(b_cond, "kp_x", "eq")
    E(lsrs_imm, 2, 2, 1); E(b_cond, "kp_n", "cc"); E(adds_imm8, 1, 1); E(mov_reg, 0, 3)
    a.label("kp_n"); E(adds_imm8, 3, 1); E(b, "kp_l")
    a.label("kp_x"); E(mov_reg, 2, 4); E(pop_list, [4], pc=True)

    # ---- c_cskeys(r0 = the block) -> r0 = its keys (bits 1..24); clobbers r1, r2
    a.label("c_cskeys")
    E(ldrb_imm, 1, 0, B_KEYS + 2); E(lsls_imm, 1, 1, 8); E(raw, h(0x7800 | (B_KEYS + 1) << 6 | 0 << 3 | 2))   # ldrb r2, [r0, #7]
    E(orrs_reg, 1, 2); E(lsls_imm, 1, 1, 8); E(ldrb_imm, 2, 0, B_KEYS); E(orrs_reg, 1, 2); E(lsls_imm, 0, 1, 1); E(raw, h(0x4770))

    # ---- c_csget() -> r0 = the period (0: the custom scale is off), r1 = the degrees' bits (1..23), r2 = the notes of an iteration (1..7);
    #      clobbers r3
    a.label("c_csget")
    E(push_list, [4], lr=True)
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); E(b_cond, "cg_0", "eq"); E(mov_reg, 4, 0)
    E(ldr_imm, 1, 4, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "cg_0", "ne")
    E(ldrb_imm, 1, 4, B_ON); E(ldrb_imm, 2, 4, B_KEYS); E(eors_reg, 1, 2); E(ldrb_imm, 2, 4, B_KEYS + 1); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 4, B_KEYS + 2); E(eors_reg, 1, 2); E(movs_imm, 2, 0x5A); E(eors_reg, 1, 2); E(ldrb_imm, 2, 4, B_SUM); E(cmp_reg, 1, 2)
    E(b_cond, "cg_0", "ne")
    E(ldrb_imm, 1, 4, B_ON); E(cmp_imm, 1, 1); E(b_cond, "cg_0", "ne")
    E(mov_reg, 0, 4); E(bl, "c_cskeys"); E(cmp_imm, 0, 0); E(b_cond, "cg_0", "eq")
    E(bl, "c_cskp")                                                                    # r0 = P, r1 = keys pressed, r2 = the keys
    E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(bics_reg, 2, 3); E(mov_reg, 3, 1); E(mov_reg, 1, 2); E(mov_reg, 2, 3)
    E(pop_list, [4], pc=True)
    a.label("cg_0"); E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 2, 1); E(pop_list, [4], pc=True)

    # ---- c_csput(r0 = on, r1 = keys): the block written with its check byte; clobbers r2, r3
    a.label("c_csput")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 0); E(mov_reg, 6, 1)
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); E(b_cond, "cp_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, MAGIC); E(str_imm, 0, 4, 0)
    E(strb_imm, 5, 4, B_ON); E(lsrs_imm, 0, 6, 1); E(strb_imm, 0, 4, B_KEYS); E(lsrs_imm, 0, 6, 9); E(strb_imm, 0, 4, B_KEYS + 1)
    E(lsrs_imm, 0, 6, 17); E(strb_imm, 0, 4, B_KEYS + 2)
    E(ldrb_imm, 1, 4, B_ON); E(ldrb_imm, 2, 4, B_KEYS); E(eors_reg, 1, 2); E(ldrb_imm, 2, 4, B_KEYS + 1); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 4, B_KEYS + 2); E(eors_reg, 1, 2); E(movs_imm, 2, 0x5A); E(eors_reg, 1, 2); E(strb_imm, 1, 4, B_SUM)
    a.label("cp_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_cspat(r0 = buffer of 8): the offsets of a row from its base (0xFF = no note) -> r0 = the row's span (P or 2P), r1 = n
    a.label("c_cspat")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0)
    E(movs_imm, 0, 0xFF); E(movs_imm, 1, 0)
    a.label("pt_f"); E(strb_reg, 0, 7, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, "pt_f", "lo")
    E(bl, "c_csget"); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)            # r4 = P, r5 = degrees, r6 = n
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 0); E(movs_imm, 2, 1)                       # r2 = the column
    E(movs_imm, 3, 1)                                                                  # r3 = the interval
    a.label("pt_d"); E(cmp_imm, 3, 24); E(b_cond, "pt_e", "hs")
    E(movs_imm, 0, 1); E(lsls_reg, 0, 3); E(raw, h(0x4205))                                     # tst r5, r0
    E(b_cond, "pt_dn", "eq"); E(strb_reg, 3, 7, 2); E(adds_imm8, 2, 1)
    a.label("pt_dn"); E(adds_imm8, 3, 1); E(b, "pt_d")
    a.label("pt_e")
    E(cmp_imm, 6, 4); E(b_cond, "pt_h", "ls")
    E(strb_reg, 4, 7, 6); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(pop_list, [4, 5, 6, 7], pc=True)     # one iteration a row: + the period note
    a.label("pt_h")                                                                    # two: the degrees again from P in the right half
    E(movs_imm, 2, 0)
    a.label("pt_hl"); E(ldrb_reg, 0, 7, 2); E(adds_reg, 0, 0, 4); E(adds_imm8, 2, 4); E(strb_reg, 0, 7, 2); E(subs_imm8, 2, 3)
    E(cmp_reg, 2, 6); E(b_cond, "pt_hl", "lo")
    E(lsls_imm, 0, 4, 1); E(mov_reg, 1, 6); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_csbuild(r0 = the keyboard): its three tables for the custom scale (on)
    #      frame: [sp + 0..7] the row's offsets, [sp + 8] the span, [sp + 12] n
    a.label("c_csbuild")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
    E(mov_reg, 4, 0)
    E(bl, KB_CLEAR)
    E(mov_reg, 0, 13); E(bl, "c_cspat"); E(raw, h(0x9002))                                    # str r0, [sp, #8]
    E(raw, h(0x9103))                                                                  # str r1, [sp, #12]
    E(movs_imm, 6, 0)                                                                  # r6 = the row
    a.label("bd_r")
    E(movs_imm, 0, ANCHOR_ROW); E(subs_reg, 0, 0, 6); E(raw, h(0x9902)); E(muls, 0, 1)   # ldr r1, [sp, #8]; (9 - row) x span
    E(adds_imm8, 0, ANCHOR); E(mov_reg, 5, 0)                                          # r5 = the row's base (signed)
    E(movs_imm, 7, 0)                                                                  # r7 = the column
    a.label("bd_c")
    E(mov_reg, 1, 13); E(ldrb_reg, 0, 1, 7); E(cmp_imm, 0, 0xFF); E(b_cond, "bd_n", "eq")
    E(adds_reg, 0, 0, 5); E(cmp_imm, 0, 1); E(b_cond, "bd_n", "lt"); E(cmp_imm, 0, VMAX); E(b_cond, "bd_n", "gt")
    E(lsls_imm, 1, 6, 3); E(adds_reg, 1, 1, 7)                                         # r1 = the index
    E(adds_reg, 2, 4, 1)
    E(raw, h(0x7000 | 0x14 << 6 | 2 << 3 | 0))                                        # strb r0, [r2, #0x14]
    E(adds_reg, 2, 4, 0); E(movs_imm, 3, 0xF4); E(adds_reg, 2, 2, 3); E(ldrb_imm, 3, 2, 0); E(cmp_imm, 3, 0xFF); E(b_cond, "bd_n", "ne")
    E(strb_imm, 1, 2, 0)
    a.label("bd_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "bd_c", "lo")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, ROWS); bc("bd_r", "lo")
    # links (one iteration a row): the root of row r <-> the period note of row r + 1, both present
    E(raw, h(0x9803)); E(cmp_imm, 0, 4); E(b_cond, "bd_e", "ls")                      # ldr r0, [sp, #12] = n
    E(movs_imm, 6, 0)
    a.label("bd_l")
    E(lsls_imm, 1, 6, 3); E(adds_reg, 2, 4, 1); E(raw, h(0x7800 | 0x14 << 6 | 2 << 3 | 3))   # ldrb r3, [r2, #0x14]
    E(cmp_imm, 3, 0); E(b_cond, "bd_ln", "eq")
    E(raw, h(0x9803)); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 8)                       # r0 = the period note of the next row
    E(adds_reg, 2, 4, 0); E(raw, h(0x7800 | 0x14 << 6 | 2 << 3 | 3)); E(cmp_imm, 3, 0); E(b_cond, "bd_ln", "eq")
    E(movs_imm, 3, 0xC0); E(lsls_imm, 3, 3, 1); E(adds_reg, 2, 4, 3)                   # r2 = the links (+ 0x180)
    E(strb_reg, 0, 2, 1); E(strb_reg, 1, 2, 0)
    a.label("bd_ln"); E(adds_imm8, 6, 1); E(cmp_imm, 6, ROWS - 1); E(b_cond, "bd_l", "lo")
    a.label("bd_e")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0x98); E(lsls_imm, 1, 1, 2); E(adds_reg, 1, 4, 1); E(strb_imm, 0, 1, 0)   # + 0x260 = 0
    E(ldr_imm, 0, 4, 4); E(bl, COMMIT)
    E(add_sp_imm, 16); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_csslot0 (the keyboard's slot 0): the custom scale when on, else the stock's
    a.label("c_csslot0")
    E(push_list, [0, 4], lr=True)
    imm32(1, KB); E(cmp_reg, 0, 1); E(b_cond, "s0_s", "ne")
    E(bl, "c_csget"); E(cmp_imm, 0, 0); E(b_cond, "s0_s", "eq")
    E(pop_list, [0, 4]); E(raw, h(0xF85D) + h(0xEB04))                                          # pop {lr} (ldr lr, [sp], #4)
    E(b_w, "c_csbuild")
    a.label("s0_s"); E(pop_list, [0, 4]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, KB_SLOT0)

    # ---- c_csnear(r0 = a note, r1 = the scale object or 0) -> r0 = the nearest note of the custom scale (P, ties down), clamped to the object's
    #      min / max; r0 unchanged when the custom scale is off -> r1 = 0 (off) / 1
    a.label("c_csnear")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 4, 0); E(raw, h(0x9100))                                                # str r1, [sp]
    E(bl, "c_csget"); E(cmp_imm, 0, 0); bc("cn_off", "eq")
    E(mov_reg, 5, 0); E(mov_reg, 6, 1)                                                 # r5 = P, r6 = the degrees
    E(lsls_imm, 0, 5, 8); E(adds_reg, 0, 0, 4); E(subs_imm8, 0, ANCHOR)                # t = note - 60 + 256 P (> 0)
    E(raw, udiv(1, 0, 5)); E(muls, 1, 5); E(subs_reg, 7, 0, 1)                         # r7 = m = t mod P
    E(movs_imm, 0, 0); E(mov_reg, 1, 7)                                                # best = 0, its distance = m
    E(movs_imm, 2, 1)
    a.label("cn_l"); E(cmp_reg, 2, 5); E(b_cond, "cn_e", "hi")
    E(cmp_reg, 2, 5); E(b_cond, "cn_c", "eq")                                          # P itself is a candidate
    E(movs_imm, 3, 1); E(lsls_reg, 3, 2); E(raw, h(0x4233 | 0))                        # tst r6, r3 -> (0x4233 = tst r3, r6)
    E(b_cond, "cn_n", "eq")
    a.label("cn_c")
    E(subs_reg, 3, 2, 7); E(b_cond, "cn_ab", "pl"); E(subs_reg, 3, 7, 2)
    a.label("cn_ab"); E(cmp_reg, 3, 1); E(b_cond, "cn_n", "hs"); E(mov_reg, 1, 3); E(mov_reg, 0, 2)
    a.label("cn_n"); E(adds_imm8, 2, 1); E(b, "cn_l")
    a.label("cn_e")
    E(subs_reg, 4, 4, 7); E(adds_reg, 4, 4, 0)                                         # the note - m + the best
    E(raw, h(0x9800)); E(cmp_imm, 0, 0); E(b_cond, "cn_r", "eq")                       # ldr r0, [sp]: the scale object
    E(ldrb_imm, 1, 0, 0); E(cmp_reg, 4, 1); E(b_cond, "cn_mx", "ge"); E(mov_reg, 4, 1)
    a.label("cn_mx"); E(ldrb_imm, 1, 0, 1); E(cmp_reg, 4, 1); E(b_cond, "cn_r", "le"); E(mov_reg, 4, 1)
    a.label("cn_r"); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("cn_off"); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_csq (the quantiser's first 4 bytes: r0 = the scale object, r1 = the note): the keyboard's object with the custom scale on -> ours
    a.label("c_csq")
    E(push_list, [0, 1, 2, 3], lr=True)
    imm32(2, KB); E(ldr_imm, 2, 2, 0xC); E(cmp_reg, 0, 2); E(b_cond, "cq_s", "ne")
    E(mov_reg, 2, 0); E(mov_reg, 0, 1); E(mov_reg, 1, 2); E(bl, "c_csnear"); E(cmp_imm, 1, 0); E(b_cond, "cq_s", "eq")
    E(raw, h(0xB004))                                                                  # add sp, #16
    E(raw, h(0xBD00))                                                                  # pop {pc}
    a.label("cq_s")
    E(pop_list, [0, 1, 2, 3]); E(raw, h(0xF85D) + h(0xEB04))
    E(raw, QUANT_OLD); E(b_w, QUANT_BACK)

    # ---- c_csmut (c_mutscale's first 4 bytes: r0 = a note, r1 = random bits) -> another degree of the same iteration (custom scale on)
    a.label("c_csmut")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_csget"); E(cmp_imm, 0, 0); bc("cm_off", "eq")
    E(raw, h(0x9000)); E(raw, h(0x9101)); E(mov_reg, 7, 2)                             # [sp] P, [sp + 4] the degrees, r7 = n
    E(cmp_imm, 7, 2); bc("cm_same", "lo")
    E(lsls_imm, 1, 0, 8); E(adds_reg, 1, 1, 4)
    if MUTROOT: imm32(2, KB); E(ldr_imm, 2, 2, 0x10); E(ldrb_imm, 2, 2, 0); E(subs_reg, 1, 1, 2)   # (SC42.6) the note above the root
    E(subs_imm8, 1, ANCHOR); E(raw, udiv(2, 1, 0)); E(muls, 2, 0); E(subs_reg, 6, 1, 2)   # r6 = m
    # which other degree: k = random % (n - 1), counted over the degrees (0 and the bits) that are not m
    E(subs_imm8, 7, 1); E(raw, udiv(1, 5, 7)); E(muls, 1, 7); E(subs_reg, 5, 5, 1)     # r5 = k
    E(movs_imm, 2, 0)                                                                  # r2 = the degree tried
    a.label("cm_l")
    E(raw, h(0x9800)); E(cmp_reg, 2, 0); bc("cm_same", "hs")
    E(cmp_imm, 2, 0); E(b_cond, "cm_in", "eq")
    E(movs_imm, 3, 1); E(lsls_reg, 3, 2); E(raw, h(0x9801))
    E(raw, h(0x4203))                                                                  # tst r3, r0
    E(b_cond, "cm_nx", "eq")
    a.label("cm_in")
    E(cmp_reg, 2, 6); E(b_cond, "cm_nx", "eq")
    E(cmp_imm, 5, 0); E(b_cond, "cm_got", "eq"); E(subs_imm8, 5, 1)
    a.label("cm_nx"); E(adds_imm8, 2, 1); E(b, "cm_l")
    a.label("cm_got")
    E(subs_reg, 0, 4, 6); E(adds_reg, 0, 0, 2)
    E(cmp_imm, 0, 0); E(b_cond, "cm_p", "ge"); E(movs_imm, 0, 0)
    a.label("cm_p"); E(cmp_imm, 0, 127); E(b_cond, "cm_r", "le"); E(movs_imm, 0, 127)
    a.label("cm_r"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("cm_same"); E(mov_reg, 0, 4); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("cm_off")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7])
    E(raw, h(0xF85D) + h(0xEB04))
    E(raw, MUT_OLD); E(b_w, L["c_mutscale"] + 4)

    # ---- c_csbtn (the head of the button chain: ctrl, id): Shift + Scales = the editor on / off (opening the Scales view); Scales alone leaves it
    a.label("c_csbtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, ID_SCALES); bc("cb_f", "ne")
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); bc("cb_f", "eq"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "cb_sh", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, B_ED); E(b, "cb_f")                          # Scales alone: out of the editor, the stock's press
    a.label("cb_sh")
    E(ldrb_imm, 0, 4, B_ED); E(cmp_imm, 0, 0); E(b_cond, "cb_on", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, B_ED); E(b, "cb_x")
    a.label("cb_on")
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, B_ED)
    E(mov_reg, 0, 4); E(ldr_imm, 1, 0, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "cb_v", "ne")   # keys kept: the custom scale on again
    E(bl, "c_cskeys"); E(cmp_imm, 0, 0); E(b_cond, "cb_v", "eq"); E(mov_reg, 1, 0); E(movs_imm, 0, 1); E(bl, "c_csput")
    a.label("cb_v")
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(2, SCALES_VIEW); E(cmp_reg, 1, 2); E(b_cond, "cb_x", "eq")
    E(movs_imm, 1, SCALES_VIEW_ID); E(movs_imm, 2, ID_SCALES); E(bl, OPEN_VIEW)
    a.label("cb_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("cb_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_cspad (the Scales view's slot 0: view, pad, velocity): the editor's keys; out of it a stock scale switches the custom scale off
    a.label("c_cspad")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); bc("cd_s", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, B_ED); E(cmp_imm, 0, 0); E(b_cond, "cd_ed", "ne")
    E(cmp_imm, 5, 16); bc("cd_s", "lo")
    E(ldr_imm, 1, 4, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); bc("cd_s", "ne")
    E(mov_reg, 0, 4); E(bl, "c_cskeys"); E(mov_reg, 1, 0); E(movs_imm, 0, 0); E(bl, "c_csput")   # a stock scale: the custom one off (keys kept)
    E(b, "cd_s")
    a.label("cd_ed")
    E(cmp_imm, 5, 32); bc("cd_x", "hs")
    imm32(0, t_piano); E(ldrb_reg, 6, 0, 5); E(cmp_imm, 6, 0); bc("cd_x", "eq"); E(cmp_imm, 6, 0xFF); bc("cd_x", "eq")   # r6 = the interval
    E(ldr_imm, 1, 4, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "cd_z", "ne")
    E(mov_reg, 0, 4); E(bl, "c_cskeys"); E(b, "cd_k")
    a.label("cd_z"); E(movs_imm, 0, 0)
    a.label("cd_k"); E(mov_reg, 5, 0)                                                  # r5 = the keys
    E(movs_imm, 1, 1); E(lsls_reg, 1, 6)
    E(raw, h(0x420D))                                                                  # tst r5, r1
    E(b_cond, "cd_add", "eq")
    E(bics_reg, 5, 1); E(b, "cd_w")
    a.label("cd_add")
    E(mov_reg, 0, 5); E(bl, "c_cskp"); E(cmp_imm, 1, MAXKEYS); bc("cd_x", "hs")
    E(movs_imm, 1, 1); E(lsls_reg, 1, 6); E(orrs_reg, 5, 1)
    a.label("cd_w")
    E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "cd_p", "eq"); E(movs_imm, 0, 1)
    a.label("cd_p"); E(mov_reg, 1, 5); E(bl, "c_csput")
    a.label("cd_x"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("cd_s"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["pad"])

    # ---- c_csleds (the Scales view's slot 7: view) -> r0 = its LED buffer: the editor's keyboard; out of it, with the custom scale on, the stock's
    #      selected scale like the others
    a.label("c_csleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 7, 0)
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); bc("cl_x", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, B_ED); E(cmp_imm, 0, 0); bc("cl_st", "eq")
    E(movs_imm, 6, 0)                                                                  # the keys (0 when no block)
    E(ldr_imm, 1, 4, 0); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "cl_k", "ne")
    E(mov_reg, 0, 4); E(bl, "c_cskeys"); E(mov_reg, 6, 0)
    a.label("cl_k")
    E(mov_reg, 0, 6); E(bl, "c_cskp"); E(mov_reg, 4, 0)                                # r4 = the period (0 with no keys)
    E(movs_imm, 5, 0)                                                                  # r5 = the pad
    a.label("cl_l")
    imm32(0, t_piano); E(ldrb_reg, 1, 0, 5); E(movs_imm, 2, 0); E(cmp_imm, 1, 0xFF); E(b_cond, "cl_w", "eq")
    E(movs_imm, 2, COL_ROOT); E(cmp_imm, 1, 0); E(b_cond, "cl_w", "eq")
    E(movs_imm, 2, COL_FREE); E(movs_imm, 3, 1); E(lsls_reg, 3, 1); E(raw, h(0x4233))   # tst r6, r3 (0x4233: tst r3, r6)
    E(b_cond, "cl_w", "eq")
    E(movs_imm, 2, COL_DEG); E(cmp_reg, 1, 4); E(b_cond, "cl_w", "ne"); E(movs_imm, 2, COL_PER)
    a.label("cl_w"); E(lsls_imm, 0, 5, 1); E(strh_reg, 2, 7, 0)
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, "cl_l", "lo")
    E(b, "cl_x")
    a.label("cl_st")                                                                   # out of the editor
    E(bl, "c_csget"); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "eq")
    imm32(0, KB); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)    # the stock's scale
    E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(adds_imm8, 1, 1); E(adds_imm8, 1, 1)                   # r1 = 17 (16 + 1)
    E(adds_reg, 1, 0, 1); E(movs_imm, 2, 15); E(subs_imm8, 1, 16); E(ands_reg, 1, 2); E(adds_imm8, 1, 16)   # another scale's pad
    E(lsls_imm, 1, 1, 1); E(raw, h(0x5A79))                                                     # ldrh r1, [r7, r1]
    E(adds_imm8, 0, 16); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 7, 0)
    a.label("cl_x"); E(mov_reg, 0, 7); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_csledtask (the LED task calls: ctrl, frame): the chain; the editor ends with the view; the keyboard rebuilt when the project's custom
    #      scale differs from what it holds; the Scales LED yellow with Shift
    a.label("c_csledtask")
    E(push_list, [3, 4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); bc("ct_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(2, SCALES_VIEW); E(cmp_reg, 1, 2); E(b_cond, "ct_v", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, B_ED)
    a.label("ct_v")
    E(bl, "c_csget"); E(cmp_imm, 0, 0); E(b_cond, "ct_w", "eq")
    E(lsls_imm, 0, 0, 24); E(orrs_reg, 0, 1)                                          # wanted = P << 24 | the degrees
    a.label("ct_w")
    E(ldr_imm, 1, 4, B_STAMP); E(cmp_reg, 0, 1); E(b_cond, "ct_l", "eq")
    E(str_imm, 0, 4, B_STAMP); imm32(0, KB); E(bl, "c_csslot0")
    a.label("ct_l")
    if LED_SCALES is not None:
        E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ct_x", "eq")
        E(movs_imm, 0, COL_SHIFT); E(movs_imm, 1, LED_SCALES * 2); E(strh_reg, 0, 5, 1)
    a.label("ct_x"); E(pop_list, [3, 4, 5, 6], pc=True)

    # ---- c_csload / c_csnew (the end of the stock's "apply session" / of a new project): the keyboard's stamp unknown, the editor off; a new
    #      project has no custom scale.  c_cszero(r2 = 1: the block too); clobbers r0, r1
    a.label("c_cszero")
    E(raw, h(0xB500))                                                                  # push {lr}
    E(bl, "c_csblk"); E(cmp_imm, 0, 0); E(b_cond, "cz_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, B_ED); E(subs_imm8, 1, 1); E(str_imm, 1, 0, B_STAMP)
    E(cmp_imm, 2, 0); E(b_cond, "cz_x", "eq"); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)
    a.label("cz_x"); E(raw, h(0xBD00))                                                 # pop {pc}
    a.label("c_csload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 2, 0); E(bl, "c_cszero"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    a.label("c_csnew")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 2, 1); E(bl, "c_cszero"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["new"])
    return a.assemble()


def vt_get(img, vt, slot, base):
    import struct
    return struct.unpack_from("<I", img, vt + 4 * slot - base)[0]


def install(img, report, base_addr):
    """Append the code; the keyboard's slot 0, the quantiser and c_mutscale's first 4 bytes, the Scales view's slots 0 / 7, the head of the button
    chain, the LED task calls, the ends of a load and of a new project."""
    import ct_fw, struct
    from thumb import bl as bl_enc, b_w as bw_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_mutscale=lab("mutate39", "c_mutscale"))
    prev = dict(btn=MP.bw_target(img, BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                load=MP.bw_target(img, P19.LOAD_END, BASE), new=MP.bw_target(img, P19.NEW_TAIL, BASE),
                pad=vt_get(img, SCALES_VT, 0, BASE) & ~1, leds=vt_get(img, SCALES_VT, 7, BASE) & ~1)
    assert prev["pad"] == 0x08043F30 and prev["leds"] == 0x08043F4E, (hex(prev["pad"]), hex(prev["leds"]))
    assert vt_get(img, KB_VT, 0, BASE) == KB_SLOT0 | 1
    assert bytes(img[QUANT - BASE:QUANT - BASE + 4]) == QUANT_OLD
    assert bytes(img[L["c_mutscale"] - BASE:L["c_mutscale"] - BASE + 4]) == MUT_OLD
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data): img[addr - BASE:addr - BASE + len(data)] = data
    put(BTN_ENTRY, bw_enc(BTN_ENTRY, labels["c_csbtn"]))
    put(P19.LOAD_END, bw_enc(P19.LOAD_END, labels["c_csload"]))
    put(P19.NEW_TAIL, bw_enc(P19.NEW_TAIL, labels["c_csnew"]))
    put(QUANT, bw_enc(QUANT, labels["c_csq"]))
    put(L["c_mutscale"], bw_enc(L["c_mutscale"], labels["c_csmut"]))
    put(SCALES_VT, struct.pack("<I", labels["c_cspad"] | 1)); put(SCALES_VT + 28, struct.pack("<I", labels["c_csleds"] | 1))
    put(KB_VT, struct.pack("<I", labels["c_csslot0"] | 1))
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        put(c, bl_enc(c, labels["c_csledtask"]))
    return labels, code, prev
