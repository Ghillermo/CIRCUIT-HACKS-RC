"""SC43: what a module writes into a drum pattern's step arrays must reach the stock's edit store of that drum, or the stock's next commit puts the
old arrays back (seen in emulation: a hit written by the rollers or the drum arpeggio vanished after a probability edit).

The stock (emulated): each drum has an edit store of its current pattern's four arrays (the probability view's context: [[0x200438DC + 0x3C d +
0xC]]); [store + 0x18] = that pattern + 0xA8 (it follows the drum's pattern); its parameters are words of 4 steps: 0..7 the velocities, 8..15 the
probabilities, 16..23 the micro steps, 24..31 the sample flips (raw: + 0, + 0x20, + 0x60, + 0x40); every edit commits the whole store into the
pattern.
  * emit_sync(a, name): name(r0 = the drum player, r1 = step, r2 = the pattern's base): the four raw words of that step;
  * emit_syncall(a, name): name(r0 = drum 0..3, r1 = the pattern's base): all 32 words;
into both copies of the store (read and write), when the store is that pattern's; r0-r3 clobbered.
"""
from __future__ import annotations
from thumb import adds_imm8, adds_reg, b_cond, bl, cmp_imm, cmp_reg, ldr_imm, lsrs_imm, lsls_imm, mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, subs_reg  # noqa: E402
from build_sc14 import udiv  # noqa: E402

PROB_VIEW0, PROB_SZ = 0x200438DC, 0x3C
DP0, DP_SZ = 0x20040810, 0x90
PARAM_GET, PARAM_WPTR = 0x0803542C, 0x080354FA
ARRAYS = ((0, 0x00), (8, 0x20), (16, 0x60), (24, 0x40))      # (the store's first parameter, the raw array)


def _store(a, name, from_player):
    """r0 = the drum player (from_player) or the drum, r7 = the base -> r4 = the store; to name_x when the store is another pattern's"""
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    if from_player:
        imm32(1, DP0); E(subs_reg, 0, 0, 1); E(movs_imm, 1, DP_SZ); E(raw, udiv(0, 0, 1))
    E(movs_imm, 1, PROB_SZ); E(muls, 0, 1); imm32(1, PROB_VIEW0); E(adds_reg, 0, 0, 1)
    E(ldr_imm, 0, 0, 0xC); E(ldr_imm, 4, 0, 0)
    E(ldr_imm, 0, 4, 0x18); E(mov_reg, 1, 7); E(adds_imm8, 1, 0xA8); E(cmp_reg, 0, 1); E(b_cond, name + "_x", "ne")


def emit_syncall(a, name):
    E = a.emit
    a.label(name)
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 1)
    _store(a, name, False)
    E(movs_imm, 5, 0)                                                                     # r5 = the store's parameter 0..31
    a.label(name + "_l")
    E(lsrs_imm, 0, 5, 3); E(cmp_imm, 0, 2); E(b_cond, name + "_a", "lo")                  # the raw array: groups 0 / 1 at 0x00 / 0x20, 2 / 3 at 0x60 / 0x40
    E(movs_imm, 1, 5); E(subs_reg, 0, 1, 0)
    a.label(name + "_a"); E(lsls_imm, 0, 0, 5)
    E(lsls_imm, 1, 5, 29); E(lsrs_imm, 1, 1, 27)                                          # (k & 7) x 4
    E(adds_reg, 0, 0, 1); E(adds_reg, 0, 0, 7); E(ldr_imm, 6, 0, 0)
    for fn in (PARAM_GET, PARAM_WPTR):
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, fn); E(str_imm, 6, 0, 0)
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 32); E(b_cond, name + "_l", "lo")
    a.label(name + "_x"); E(pop_list, [4, 5, 6, 7], pc=True)


def emit_sync(a, name):
    E = a.emit
    a.label(name)
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 2); E(lsrs_imm, 5, 1, 2)                                                # r7 = the base, r5 = the word (step / 4)
    _store(a, name, True)
    for k0, off in ARRAYS:
        E(lsls_imm, 0, 5, 2); E(adds_reg, 0, 0, 7)
        if off: E(adds_imm8, 0, off)
        E(ldr_imm, 6, 0, 0)                                                               # r6 = the raw word
        for fn in (PARAM_GET, PARAM_WPTR):
            E(mov_reg, 0, 4); E(mov_reg, 1, 5)
            if k0: E(adds_imm8, 1, k0)
            E(bl, fn); E(str_imm, 6, 0, 0)
    a.label(name + "_x"); E(pop_list, [4, 5, 6, 7], pc=True)
