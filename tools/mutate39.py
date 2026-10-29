"""SC39 (the user, 2026-10-11 / 12): random-mutate, in the stock probability view (Shift + button 12: the track views' submode 5, class 0x0805ACD4).
Row 3 stays the stock probability; row 4 (pads 25-32, which the stock ignores) sets the step's mutate level, in peach:

    pad 25 off | 26 octave 6 % | 27 scale 6 % | 28 octave 6 % + scale 6 % | 29 scale 12 % | 30 octave 12 % | 31 scale 25 % | 32 octave 25 % + scale 50 %

The level (0..7) is the step's byte [2] (bytes [2..3] of the 28 byte step are free: the stock writes them 0 in 0x0802B008 and they are 0 in every note
step of the 173 sessions of the user's SD card copy).  The view's store ([[view + 0xC] + 8]) holds a working copy of the selected step; 0x080354FA gives
its address and 0x080353C0 commits the whole 28 bytes to the pattern, so the level is written the way the stock writes the probability (byte [1]).

The player (found on the unit with the SEQWD diagnostic, 2026-10-12): 0x08040E5A(this, pattern, step, micro step) plays the notes of a step; for each unit
that starts it reads the note at 0x08040EFC (ldrb r5, [r4, #4]), the gate / tie ([r4, #5]) and the velocity ([r4, #7]) and calls the note-on 0x08040FA2,
which keeps the note it was given for the note-off.  c_mutnote replaces those two loads: with a level in the step's byte [2] it may swap the note for
another note of the project's scale in the same octave ("scale") and / or move it an octave up or down ("octave").  Chances are in sixteenths
(1 / 2 / 4 / 8 = 6 / 12 / 25 / 50 %), drawn from the stock's random generator 0x08049908.  A mutated note is left alone (the original plays) when
  * the unit is tied (bit 7 of [r4, #5]) or continues a tie (its bit in the table this + 0x128): the stock matches those by the note of the step;
  * the new note is already sounding (this + 0x9B + note != 0xFF): the stock releases a sounding note by the step's note, not by ours.
While recording (the transport store 0x20011034: parameters 0 and 1 set, 2 clear, the stock recorder gate's test) the mutated note is written into the
step (the user: «con Record la nota mutada se escribe en la secuencia; sin Record, suena una vez»).

The scale is the project's: one object for every track ([keyboard context 0x20041044 + 0xC] = {min, max, u32 mask of 2 bits per degree above the root,
0 = in the scale}, the root's byte at [[0x20041044 + 0x10]]), the same one the stock quantiser 0x080408C6 reads.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, ldrb_w, lsls_imm,  # noqa: E402
                   lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, nop, pop_list, push_list, raw, h, strb_imm, strh_reg, subs_imm8,
                   subs_reg)

PROB_VT = 0x0805ACD4                  # the probability view: slot 0 = its pads (0..7 row 3, 8..15 row 4), slot 8 = its store listener
PROB_VT2 = 0x0805AD00                 # its second vtable (this + 8): slot 0 = the listener's thunk (subs r0, #8)
PROB_PAD, PROB_LISTEN, PROB_THUNK, PROB_BUF = 0x0804D0BC, 0x0804D116, 0x0804D114, 0x08047592
NOTE_LOAD, NOTE_BACK = 0x08040EFC, 0x08040F02      # ldrb r5, [r4, #4]; ldrb.w sl, [r4, #7] in the player 0x08040E5A
NOTE_OLD = bytes.fromhex("257994f807a0")
PARAM_GET, PARAM_WPTR, PARAM_COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
RANDOM = 0x08049908                   # the stock's generator: r0 = 30 random bits
PLAY_STORE = 0x20011034               # the transport: parameter 0 playing, 1 recording, 2 the count-in
KB_CTX = 0x20041044                   # the keyboard context of the four note tracks: + 0xC the scale object, + 0x10 the root's address
O_HELD, O_SOUND = 0x128, 0x9B         # the player: notes that continue a tie (bit table), the sounding note's entry by note (0xFF = none)
STEP_LEVEL = 2                        # the step's byte
COL_LIT, COL_DIM = 0x6A, 0x6B         # peach bright / dim (steady codes; the FX view's pads 1-16)
# chances in sixteenths, octave | scale << 4, by level
CHANCE = (0x00, 0x01, 0x10, 0x11, 0x20, 0x02, 0x40, 0x84)


TRIMSL = False                        # SC49.3 (use_trimsl)


def use_trimsl():
    """SC49.3 (flash for the drums' extra lane, phase 2): stepmod (SC40.3) puts its own c_rfbuf / c_rfled on the probability view's slots 7 / 8
    and its thunk, going on to the stock's; c_mutbuf / c_mutled / c_mutled_t are called from nowhere: not emitted, the slots left to stepmod
    (c_mutrow stays: stepmod calls it)."""
    global TRIMSL
    TRIMSL = True

def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)


def arm_code(base):
    a = Asm(base)
    E = a.emit
    def get(k): E(movw, 0, PLAY_STORE & 0xFFFF); E(movt, 0, PLAY_STORE >> 16); E(movs_imm, 1, k); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)

    # ---- c_mutnote (from the player, in place of its two loads): r4 = the unit's address - 4, r7 = the unit (0..5), r0 = the player, r6 = [r4, #5]
    #      -> r5 = the note to play, sl = the velocity; everything else as it was
    a.label("c_mutnote")
    E(ldrb_imm, 5, 4, 4)
    E(raw, bytes.fromhex("94f807a0"))                                             # ldrb.w sl, [r4, #7]
    E(push_list, [0, 1, 2, 3, 4, 6, 7], lr=True)
    E(lsls_imm, 1, 7, 2); E(subs_reg, 1, 4, 1)                                   # r1 = the step
    E(ldrb_imm, 7, 1, STEP_LEVEL); E(movs_imm, 2, 7); E(ands_reg, 7, 2); E(b_cond, "mn_x", "eq")     # r7 = the level
    E(cmp_imm, 6, 0x80); E(b_cond, "mn_x", "hs")                                # a tied unit
    E(lsrs_imm, 2, 5, 5); E(lsls_imm, 2, 2, 2); E(adds_reg, 2, 2, 0); E(movw, 3, O_HELD); E(adds_reg, 2, 2, 3); E(ldr_imm, 3, 2, 0)
    E(movs_imm, 2, 31); E(ands_reg, 2, 5); E(lsrs_reg, 3, 2); E(lsls_imm, 3, 3, 31); E(b_cond, "mn_x", "mi")   # it continues a tie
    E(bl, RANDOM); E(lsrs_imm, 6, 0, 6)                                         # r6 = 24 random bits
    E(movw, 0, CHANCE[0] | CHANCE[1] << 8); E(movt, 0, CHANCE[2] | CHANCE[3] << 8)
    E(cmp_imm, 7, 4); E(b_cond, "mn_c", "lo")
    E(movw, 0, CHANCE[4] | CHANCE[5] << 8); E(movt, 0, CHANCE[6] | CHANCE[7] << 8)
    a.label("mn_c")
    E(movs_imm, 1, 3); E(ands_reg, 1, 7); E(lsls_imm, 1, 1, 3); E(lsrs_reg, 0, 1); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(mov_reg, 7, 0)   # r7 = the chances
    # the scale
    E(lsrs_imm, 0, 7, 4); E(movs_imm, 1, 15); E(ands_reg, 1, 6); E(lsrs_imm, 6, 6, 4); E(cmp_reg, 1, 0); E(b_cond, "mn_o", "hs")
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_mutscale"); E(mov_reg, 5, 0); E(lsrs_imm, 6, 6, 8)
    a.label("mn_o")                                                               # the octave
    E(movs_imm, 0, 15); E(ands_reg, 0, 7); E(movs_imm, 1, 15); E(ands_reg, 1, 6); E(lsrs_imm, 6, 6, 4); E(cmp_reg, 1, 0); E(b_cond, "mn_e", "hs")
    E(lsls_imm, 0, 6, 31); E(b_cond, "mn_d", "mi")
    E(adds_imm8, 5, 12); E(cmp_imm, 5, 127); E(b_cond, "mn_e", "ls"); E(subs_imm8, 5, 24); E(b, "mn_e")
    a.label("mn_d")
    E(subs_imm8, 5, 12); E(b_cond, "mn_e", "pl"); E(adds_imm8, 5, 24)
    a.label("mn_e")
    E(ldrb_imm, 0, 4, 4); E(cmp_reg, 0, 5); E(b_cond, "mn_x", "eq")              # no change
    E(ldr_sp, 0, 0); E(adds_reg, 0, 0, 5); E(ldrb_w, 0, 0, O_SOUND); E(cmp_imm, 0, 0xFF); E(b_cond, "mn_r", "ne")   # the new note already sounds
    for k, skip in ((0, "eq"), (1, "eq"), (2, "ne")):                             # recording: the mutated note stays in the step
        get(k); E(cmp_imm, 0, 0); E(b_cond, "mn_x", skip)
    E(strb_imm, 5, 4, 4)
    E(b, "mn_x")
    a.label("mn_r"); E(ldrb_imm, 5, 4, 4)
    a.label("mn_x"); E(pop_list, [0, 1, 2, 3, 4, 6, 7], pc=True)

    # ---- c_mutscale (r0 = a note, r1 = random bits) -> r0 = another note of the project's scale in the same octave above the root (the note itself
    #      when the scale has no other one)
    a.label("c_mutscale")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(movw, 0, KB_CTX & 0xFFFF); E(movt, 0, KB_CTX >> 16)
    E(ldr_imm, 1, 0, 0x10); E(ldrb_imm, 6, 1, 0)                                 # r6 = the root
    E(ldr_imm, 1, 0, 0xC); E(ldr_imm, 7, 1, 4)                                   # r7 = the mask
    E(movs_imm, 0, 120); E(adds_reg, 0, 0, 4); E(subs_reg, 0, 0, 6)
    E(movs_imm, 1, 12); E(raw, udiv(2, 0, 1)); E(muls, 2, 1); E(subs_reg, 6, 0, 2)   # r6 = the note's degree (0..11)
    E(movs_imm, 2, 0); E(movs_imm, 3, 0); E(mov_reg, 0, 7)                       # r2 = the other degrees of the scale
    a.label("ms_c")
    E(cmp_reg, 3, 6); E(b_cond, "ms_cn", "eq")
    E(movs_imm, 1, 3); E(ands_reg, 1, 0); E(b_cond, "ms_cn", "ne")
    E(adds_imm8, 2, 1)
    a.label("ms_cn")
    E(lsrs_imm, 0, 0, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, 12); E(b_cond, "ms_c", "lo")
    E(cmp_imm, 2, 0); E(b_cond, "ms_same", "eq")
    E(raw, udiv(1, 5, 2)); E(muls, 1, 2); E(subs_reg, 5, 5, 1)                   # r5 = which one
    E(movs_imm, 3, 0); E(mov_reg, 0, 7)
    a.label("ms_w")
    E(cmp_reg, 3, 6); E(b_cond, "ms_wn", "eq")
    E(movs_imm, 1, 3); E(ands_reg, 1, 0); E(b_cond, "ms_wn", "ne")
    E(cmp_imm, 5, 0); E(b_cond, "ms_f", "eq")
    E(subs_imm8, 5, 1)
    a.label("ms_wn")
    E(lsrs_imm, 0, 0, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, 12); E(b_cond, "ms_w", "lo")
    a.label("ms_same"); E(mov_reg, 0, 4); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ms_f")
    E(subs_reg, 0, 4, 6); E(adds_reg, 0, 0, 3)                                   # the note - its degree + the new degree
    E(cmp_imm, 0, 0); E(b_cond, "ms_p", "ge"); E(adds_imm8, 0, 12)
    a.label("ms_p")
    E(cmp_imm, 0, 127); E(b_cond, "ms_q", "le"); E(subs_imm8, 0, 12)
    a.label("ms_q"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mutpad (view, pad, velocity): row 4 (8..15) = the mutate level of the selected step, with the stock's conditions for the probability
    a.label("c_mutpad")
    E(cmp_imm, 1, 8); E(b_cond, "mp_s", "lo"); E(cmp_imm, 1, 15); E(b_cond, "mp_s", "hi")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(subs_imm8, 5, 8)
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 0x10); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mp_go", "ne")
    E(ldr_imm, 0, 4, 0x10); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mp_go", "eq")
    E(ldr_imm, 0, 4, 0x14); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mp_x", "eq")
    a.label("mp_go")
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 6, 0, 8)
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mp_x", "eq")   # a step without notes
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, PARAM_WPTR); E(strb_imm, 5, 0, STEP_LEVEL)
    E(mov_reg, 0, 6); E(bl, PARAM_COMMIT)
    a.label("mp_x"); E(pop_list, [4, 5, 6], pc=True)
    a.label("mp_s"); E(b_w, PROB_PAD)

    if not TRIMSL:
        # ---- c_mutled (view): the stock's listener, then row 4
        a.label("c_mutled_t"); E(subs_imm8, 0, 8)
        a.label("c_mutled")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, PROB_LISTEN)
        E(mov_reg, 0, 4); E(bl, "c_mutrow")
        E(pop_list, [4], pc=True)

        # ---- c_mutbuf (view) -> its LED buffer (slot 7, every LED pass): row 4 drawn first, so it is there before the store's first change
        a.label("c_mutbuf")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_mutrow")
        E(mov_reg, 0, 4); E(pop_list, [4]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, PROB_BUF)      # pop {r4}; ldr lr, [sp], #4

    # ---- c_mutrow (view): row 4 = the level as a bar in peach (dim above it; off when the step has no notes)
    a.label("c_mutrow")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, 0xC); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 0); E(bl, PARAM_GET)
    E(ldrb_imm, 5, 0, 0); E(ldrb_imm, 6, 0, STEP_LEVEL); E(movs_imm, 1, 7); E(ands_reg, 6, 1)
    E(ldr_imm, 0, 4, 4); E(ldr_imm, 7, 0, 0)
    E(movs_imm, 3, 0)
    a.label("ml_l")
    E(movs_imm, 2, 0); E(cmp_imm, 5, 0); E(b_cond, "ml_w", "eq")
    E(movs_imm, 2, COL_DIM); E(cmp_reg, 3, 6); E(b_cond, "ml_w", "hi")
    E(movs_imm, 2, COL_LIT)
    a.label("ml_w")
    E(mov_reg, 0, 3); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 7, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "ml_l", "lo")
    E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the player's two loads -> c_mutnote; the probability view's slot 0 -> c_mutpad, its listener (slot 8 and the thunk) -> c_mutled,
    its LED buffer getter (slot 7) -> c_mutbuf."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    put(NOTE_LOAD, bl(NOTE_LOAD, labels["c_mutnote"]) + nop(), NOTE_OLD)
    assert NOTE_LOAD + 6 == NOTE_BACK
    def slot(addr, new, old):
        assert struct.unpack_from("<I", img, addr - BASE)[0] == old | 1, hex(addr)
        struct.pack_into("<I", img, addr - BASE, new | 1)
    slot(PROB_VT, labels["c_mutpad"], PROB_PAD)
    if not TRIMSL:
        slot(PROB_VT + 8 * 4, labels["c_mutled"], PROB_LISTEN)
        slot(PROB_VT2, labels["c_mutled_t"], PROB_THUNK)
        slot(PROB_VT + 7 * 4, labels["c_mutbuf"], PROB_BUF)
    return labels, code
