"""SC47.9 (the user, 2026-10-27: «on own's sampler, adding a flip step automatically adds a note step containing the last pressed note, with a
different color. Both note and flip steps are seen in the interface. Erasing a flipped step's note keeps the flip (only seen at flip view)»): the
own engine's sample picker (smpick: the expanded Note view of MIDI 1 / 2 in the sample mode) and the notes of its steps.

  * the last pressed note: a head of the track views' live note-on (0x0804B07A: view, note, velocity, pad; in front of arp's c_arlon): MIDI 1 / 2
    (the track = [[view + 0x18] + 0xC] = 2 / 3) -> the note kept in RAM (the pads, the chord screen, a note typed into a step);
  * a flip set with the picker's gestures (a step held + a sample: smpick's c_sppad; a sample held + a step: smhold's c_shpad; their bl c_spset ->
    c_snset): the flip as before, then, when the step has no note, a note there: the last pressed note (60 = the sample as recorded, before any),
    one step long, velocity 100, micro step 0 (unit 0 of the step's record, as the step-drummer writes it); the recorded tap (Record + Play) and
    Clear + step stay smpick's;
  * the picker's step pads (the tracks' container slot 7, a head in front of the chain): a step with a note and its flip = peach (as before), a note
    without a flip = cyan, a flip without a note = violet (it stays: the stock's erase of a step's notes leaves lane 8, where the flip lives, and
    only the picker shows it), none = the dim cyan background; the held step and the step playing keep their colours;
  * the stock's step clear (0x0803D1D4: Clear + step in the Note view: the step's notes, then its 12 lanes to 0xFF) keeps a flip: the head saves
    the step's lane-8 byte, runs the stock (a trampoline with the two displaced instructions) and, the byte being a flip (0x80..0xFE), writes it
    back into the six micro steps (the level automation, 0..127, is cleared as before); a note erased with the step held + its key keeps the flip
    already (the stock leaves the lanes).
RAM: modmx.MXR + 0x1A80 (8 B, signed: "SNT1", the last note of MIDI 1 / 2).  In the hole (no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrh_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg, ands_reg)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import fxdiag as FD  # noqa: E402
import smpick as SP  # noqa: E402
import vcf21 as V  # noqa: E402

LIVE_ON = 0x0804B07A                  # the track views' live note-on (view, note, velocity, pad)
STEP_CLR, STEP_CLR_OLD = 0x0803D1D4, bytes.fromhex("f8b50546")    # the stock's step clear (this); push {r3-r7, lr}; mov r5, r0
PARAM_GET = 0x0803542C
SNR = MX.MXR + 0x1A80                 # + 0 "SNT1", + 4 / + 5 the last note of MIDI 1 / 2
SIG = 0x31544E53
GATE, VEL = V.SD_LEN, 100             # one step (6 ticks)
COL_NOTE, COL_FONLY = 0x4D, 0x49      # a note without a flip: cyan; a flip without a note: violet (a flip with its note: smpick's peach)
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    RET = h(0x4770)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_snst() -> r0 = SNR, set up at the first use (60, 60, the signature); clobbers r1, r2
    a.label("c_snst")
    imm32(0, SNR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "ns_i", "ne"); E(raw, RET)
    a.label("ns_i"); E(movs_imm, 1, SP.ROOT); E(strb_imm, 1, 0, 4); E(strb_imm, 1, 0, 5); E(str_imm, 2, 0, 0); E(raw, RET)

    # ---- c_snrec(r0 = track 0 / 1, r1 = step) -> r0 = the step's record in the pattern it plays (its lane-8 bytes - lane + 22 x step); clobbers r1-r3
    a.label("c_snrec")
    E(push_list, [4], lr=True); E(mov_reg, 4, 1)
    E(bl, L["c_splb"]); imm32(1, SP.LANE); E(subs_reg, 0, 0, 1); E(movs_imm, 1, 22); E(muls, 1, 4); E(adds_reg, 0, 0, 1)
    E(pop_list, [4], pc=True)

    # ---- c_snlon (the head of 0x0804B07A: view, note, velocity, pad): MIDI 1 / 2's note kept, then the chain
    a.label("c_snlon")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(ldr_imm, 0, 0, 0x18); E(ldrb_imm, 0, 0, 0xC); E(subs_imm8, 0, 2); E(cmp_imm, 0, 1); E(b_cond, "lo_x", "hi")
    E(mov_reg, 3, 0); E(bl, "c_snst"); E(adds_reg, 0, 0, 3); E(ldr_sp, 1, 4); E(strb_imm, 1, 0, 4)
    a.label("lo_x"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev["lon"])

    # ---- c_snset(r0 = track, r1 = step, r2 = the sample or 0xFF): smpick's c_spset; a sample on a step with no note = a note there too
    a.label("c_snset")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, L["c_spset"])
    E(cmp_imm, 6, 0xFF); E(b_cond, "st_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_snrec"); E(mov_reg, 5, 0)                                   # r5 = the step's record
    E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "st_x", "ne")
    E(bl, "c_snst"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 4)
    E(strb_imm, 0, 5, 4); E(movs_imm, 0, GATE); E(strb_imm, 0, 5, 5); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 6); E(movs_imm, 0, VEL); E(strb_imm, 0, 5, 7)
    E(movs_imm, 0, 1); E(strb_imm, 0, 5, 0)
    a.label("st_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_snled (the tracks' container slot 7: obj -> its LED buffer): the chain; the picker's steps: note / flip / both
    a.label("c_snled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["led"]); E(mov_reg, 5, 0)
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); E(b_cond, "ld_x", "eq"); E(mov_reg, 7, 0)                        # r7 = the track
    E(bl, L["c_spst"]); E(cmp_imm, 0, 0); E(b_cond, "ld_x", "eq"); E(ldrb_imm, 6, 0, 0)                      # r6 = the state byte
    E(lsrs_imm, 6, 6, 2); E(movs_imm, 0, 1); E(ands_reg, 6, 0); E(lsls_imm, 6, 6, 4)                          # r6 = 16 x the half
    E(movs_imm, 4, 0)
    a.label("ld_l")
    E(lsls_imm, 0, 4, 1); E(raw, h(0x5A28)); E(cmp_imm, 0, SP.COL_STEP); E(b_cond, "ld_go", "eq")            # ldrh r0, [r5, r0]
    E(cmp_imm, 0, SP.COL_FLIP); E(b_cond, "ld_n", "ne")
    a.label("ld_go")
    E(mov_reg, 0, 7); E(adds_reg, 1, 6, 4); E(bl, L["c_splb"]); E(ldrb_imm, 3, 0, 0); E(push_list, [3])           # the flip byte
    E(mov_reg, 0, 7); E(adds_reg, 1, 6, 4); E(bl, "c_snrec"); E(ldrb_imm, 2, 0, 0); E(pop_list, [3])              # r2 = the notes, r3 = the flip
    E(movs_imm, 1, SP.COL_STEP); E(cmp_imm, 2, 0); E(b_cond, "ld_nn", "eq"); E(movs_imm, 1, COL_NOTE)
    a.label("ld_nn")
    E(cmp_imm, 3, SP.FLIP); E(b_cond, "ld_w", "lo"); E(cmp_imm, 3, 0xFF); E(b_cond, "ld_w", "eq")
    E(movs_imm, 1, COL_FONLY); E(cmp_imm, 2, 0); E(b_cond, "ld_w", "eq"); E(movs_imm, 1, SP.COL_FLIP)
    a.label("ld_w"); E(lsls_imm, 0, 4, 1); E(strh_reg, 1, 5, 0)
    a.label("ld_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "ld_l", "lo")
    a.label("ld_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_snclr (the head of the stock's step clear: this): the step's flip kept
    a.label("c_snclr")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, 0x18); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldr_imm, 5, 0, 0)                          # the pattern
    E(ldr_imm, 0, 4, 0x24); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)                         # the step
    E(movs_imm, 1, 6); E(muls, 0, 1); E(adds_reg, 5, 5, 0); imm32(1, SP.LANE); E(adds_reg, 5, 5, 1); E(ldrb_imm, 6, 5, 0)   # r6 = its lane-8 byte
    E(mov_reg, 0, 4); E(bl, "c_snclro")
    E(cmp_imm, 6, SP.FLIP); E(b_cond, "cl_x", "lo"); E(cmp_imm, 6, 0xFF); E(b_cond, "cl_x", "eq")
    E(movs_imm, 1, 0)
    a.label("cl_l"); E(raw, h(0x546E)); E(adds_imm8, 1, 1); E(cmp_imm, 1, 6); E(b_cond, "cl_l", "lo")        # strb r6, [r5, r1]
    a.label("cl_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("c_snclro"); E(raw, STEP_CLR_OLD); E(b_w, STEP_CLR + 4)                                           # the stock's two first instructions
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of 0x0804B07A, the container's slot 7, the two gestures' bl c_spset (smpick's, smhold's)."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    SPL = {k: int(v, 16) for k, v in report["smpick"]["labels"].items()}
    SHL = {k: int(v, 16) for k, v in report["smhold"]["labels"].items()}
    L = {k: SPL[k] for k in ("c_spset", "c_splb", "c_spk", "c_spst")}
    prev = dict(lon=MP.bw_target(img, LIVE_ON, BASE), led=u(SP.CONT_VT + 28) & ~1)
    sites = (SPL["pp_sel"] - 6, SHL["hp_f"] - 4)                                   # a step held + a sample (c_sppad), a sample held + a step (c_shpad)
    for s in sites: assert FD.bl_target(img, s, BASE) == L["c_spset"], hex(s)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert SNR + 8 <= MX.MXR + 0x1B00
    assert bytes(img[STEP_CLR - BASE:STEP_CLR - BASE + 4]) == STEP_CLR_OLD
    img[STEP_CLR - BASE:STEP_CLR - BASE + 4] = b_w(STEP_CLR, labels["c_snclr"])
    img[LIVE_ON - BASE:LIVE_ON - BASE + 4] = b_w(LIVE_ON, labels["c_snlon"])
    struct.pack_into("<I", img, SP.CONT_VT + 28 - BASE, labels["c_snled"] | 1)
    for s in sites:
        img[s - BASE:s - BASE + 4] = bl(s, labels["c_snset"])
    hole.rehash(img, report, sites[1])                                             # smhold lives in the hole
    return labels, code, prev
