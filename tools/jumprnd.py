"""SC57.2 / Beta 5.57 (the user, 2026-11-13: «On step-flip, currently we have an option to add more than one note into the sequencer, but the
behavior is undefined. Can we get a randomized choice between both steps?»): when a step of a pointing MIDI 1 / 2 track (jumpseq, the step flip) holds
several notes, the jump goes to one of their steps at random, each with the same chance.

Before: every note-on of the step wrote the target's pending jump (jumpseq's c_jsnon: RAM + 4 + t = step + 1), so the last note the player sent won.
Now c_jsnon's store (`adds r1, r1, r4; strb r0, [r1, #3]`) is a call of c_jsrnd: a reservoir pick per target and step: the step instance's key = the
global tick − the pointing track's tick within its step (the same for every note of that step, new on the next one or the next loop); a new key = the
counts back to 0; the k-th note of the key replaces the pending jump with a chance of 1 / k (the stock's generator 0x08049908), the first always.  So
one note per step = as before, and the jump still lands on the target's next step.

RAM: jumpseq.RAM + 20 the key (word), + 24 + t the notes counted for target t (8 B): jumpseq's RAM + 20..31 was free (mixsolo starts at + 32).
In dspz's gap (dspz.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b_cond, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrh_imm, lsls_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   muls, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, subs_imm3, subs_reg)
import jumpseq as JS  # noqa: E402
import packio as PK  # noqa: E402

RAM = JS.RAM
O_KEY, O_CNT = 20, 24
RANDOM = 0x08049908                                           # the stock's generator: r0 = 30 random bits
SITE = bytes.fromhex("0919c870")                              # c_jsnon: adds r1, r1, r4; strb r0, [r1, #3]
V2 = False                                                    # SC57.8 / Beta 5.63 (use_v2)


def use_v2():
    """SC57.8 / Beta 5.63 (the 2026-11-14 bug hunt, JR-7 / XC-3): one key and one count per pointing track, not one key for both: RAM + 20 + 2 m
    the key's low half (m = the pointing track - 2), + 24 + m the notes counted (a note of the other track no longer restarts this one's count);
    and one jump per pointing step: a later note of a step whose pick the target has already taken (the pending byte back to 0 at the target's
    step start, in the same key) writes nothing (before: a note on a later micro-step of the same step could make a second jump on the target's
    next step).  The counts go back to 0 whenever the song position is set (a head on SET_TICKS 0x0802BFE0 in jumpseq's companion,
    jumpseq.FIX, which the build adds with dspz.add after this), so the first note after Play always counts as the first (before: the same key
    as the run before kept the old counts and the jump was skipped).  RAM + 26..31 are no longer jumprnd's (jumpseq.use_audrel: + 28..31)."""
    global V2
    V2 = True


def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)


def arm_code(base):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    if V2: return arm_code2(a, E, imm32)

    # ---- c_jsrnd (from c_jsnon: r0 = the step + 1, r4 = the target + 1; [sp + 4] = the pointing track, c_jsnon's r1): the pending jump, a reservoir pick
    a.label("c_jsrnd")
    E(raw, h(0x9901))                                                                # ldr r1, [sp, #4]: the pointing track (2 / 3)
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 6, 0); E(mov_reg, 7, 1)
    imm32(0, JS.ENG + 0x30); E(lsls_imm, 1, 7, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 5, 0, 0)                      # r5 = its tick within the step
    imm32(0, JS.ENG + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(subs_reg, 5, 0, 5)                                                             # the key: the global tick at the step's start
    imm32(3, RAM); E(ldr_imm, 2, 3, O_KEY); E(cmp_reg, 2, 5); E(b_cond, "rn_s", "eq")
    E(str_imm, 5, 3, O_KEY); E(movs_imm, 2, 0); E(str_imm, 2, 3, O_CNT); E(str_imm, 2, 3, O_CNT + 4)
    a.label("rn_s")
    E(adds_reg, 2, 3, 4); E(ldrb_imm, 1, 2, O_CNT - 1); E(adds_imm8, 1, 1); E(strb_imm, 1, 2, O_CNT - 1)   # the target's count + 1
    E(cmp_imm, 1, 1); E(b_cond, "rn_w", "eq")
    E(mov_reg, 5, 1); E(bl, RANDOM); E(raw, udiv(1, 0, 5)); E(muls, 1, 5); E(subs_reg, 0, 0, 1)
    E(cmp_imm, 0, 0); E(b_cond, "rn_x", "ne")                                        # chance 1 / k
    a.label("rn_w")
    imm32(3, RAM); E(adds_reg, 3, 3, 4); E(strb_imm, 6, 3, 3)                        # RAM + 4 + t = the step + 1 (as c_jsnon wrote it)
    a.label("rn_x")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def arm_code2(a, E, imm32):
    # ---- c_jsrnd v2 (from c_jsnon: r0 = the step + 1, r4 = the target + 1; [sp + 4] = the pointing track 2 / 3)
    a.label("c_jsrnd")
    E(raw, h(0x9901))                                                                # ldr r1, [sp, #4]: the pointing track (2 / 3)
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 6, 0); E(subs_imm3, 7, 1, 2)     # r6 = the step + 1, r7 = m
    imm32(0, JS.ENG + 0x38); E(lsls_imm, 1, 7, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 2); E(bl, PK.PARAM_GET); E(ldr_imm, 5, 0, 0)                      # r5 = its tick within the step
    imm32(0, JS.ENG + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(subs_reg, 5, 0, 5); E(raw, h(0xB2AD))                                          # uxth r5, r5: the key, the global tick at the step's start
    imm32(3, RAM); E(lsls_imm, 2, 7, 1); E(adds_reg, 2, 2, 3); E(ldrh_imm, 0, 2, O_KEY); E(cmp_reg, 0, 5); E(b_cond, "rn_s", "eq")
    E(strh_imm, 5, 2, O_KEY); E(adds_reg, 2, 3, 7); E(movs_imm, 0, 0); E(strb_imm, 0, 2, O_CNT)   # a new step of this track: its count only
    a.label("rn_s")
    E(adds_reg, 2, 3, 7); E(ldrb_imm, 1, 2, O_CNT); E(adds_imm8, 1, 1); E(strb_imm, 1, 2, O_CNT)
    E(cmp_imm, 1, 1); E(b_cond, "rn_w", "eq")
    E(adds_reg, 0, 3, 4); E(ldrb_imm, 0, 0, 3); E(cmp_imm, 0, 0); E(b_cond, "rn_x", "eq")   # the target took this step's pick already: no second jump
    E(mov_reg, 5, 1); E(bl, RANDOM); E(raw, udiv(1, 0, 5)); E(muls, 1, 5); E(subs_reg, 0, 0, 1)
    E(cmp_imm, 0, 0); E(b_cond, "rn_x", "ne")                                        # chance 1 / k
    a.label("rn_w")
    imm32(3, RAM); E(adds_reg, 3, 3, 4); E(strb_imm, 6, 3, 3)                        # RAM + 4 + t = the step + 1
    a.label("rn_x")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); jumpseq's store in c_jsnon becomes a call."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    code, labels = arm_code(base_addr)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    on = int(report["jumpseq"]["labels"]["c_jsnon"], 16)
    seg = bytes(img[on - BASE:on - BASE + 0x40])
    k = seg.find(SITE); assert k >= 0 and seg.find(SITE, k + 1) < 0, "c_jsnon's store not found once"
    at = on + k
    img[at - BASE:at - BASE + 4] = bl(at, labels["c_jsrnd"])
    assert RAM + O_CNT + (2 if V2 else 8) <= RAM + 32
    return labels, code, dict(site=at)
