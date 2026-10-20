"""SC45.3 / RC2.04 (a fix; the user, 2026-10-20: «en la pista sample flip del sampler propio, elegir sample+paso no programa el sample (elegir el
paso primero y luego el sample sí lo hace)»): in the own engine's sample picker (smpick: the expanded Note view of MIDI 1 / 2 in the sample mode)
a sample pad held and then a step pad = that step's flip, as a step held and then a sample.

The sample pad held (its place in the page + 1) is kept in bits 3-7 of smpick's state byte (SC16's block + 14: bits 0-1 the page, bit 2 the half;
nobody else uses that byte); a step pad pressed while one is held (Clear not held) writes the flip with smpick's c_spset (sample = 16 page + the
place); both pads then go on to smpick as before (the press selects the sample and sounds it, the step pad is the held step).  The release of that
sample pad clears it, with the picker on the screen or not (a release after leaving the view must not leave it held).
Heads of the tracks' container slots 0 / 1 (0x0805A62C), in front of smpick's c_sppad / c_sprel.  In the hole (RAM only, no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, strb_imm, subs_imm8, ands_reg, orrs_reg)
import smpick as SP  # noqa: E402

SHIFT_BITS = 3                                                # the held sample's place + 1 in bits 3-7 of the state byte


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_shpad (the container's slot 0: obj, pad, velocity)
    a.label("c_shpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); E(b_cond, "hp_f", "eq"); E(mov_reg, 7, 0)                         # r7 = the track
    E(bl, L["c_spst"]); E(cmp_imm, 0, 0); E(b_cond, "hp_f", "eq"); E(mov_reg, 6, 0)                           # r6 = the state byte
    E(ldr_sp, 5, 4); E(ldrb_imm, 4, 6, 0)                                                                     # r5 = the pad, r4 = the byte
    E(cmp_imm, 5, 16); E(b_cond, "hp_st", "lo")
    E(movs_imm, 0, 7); E(ands_reg, 4, 0); E(mov_reg, 0, 5); E(subs_imm8, 0, 15); E(lsls_imm, 0, 0, SHIFT_BITS); E(orrs_reg, 4, 0)
    E(strb_imm, 4, 6, 0); E(b, "hp_f")                                                                        # a sample pad: held
    a.label("hp_st")                                                                                          # a step pad
    E(lsrs_imm, 0, 4, SHIFT_BITS); E(b_cond, "hp_f", "eq")
    imm32(1, SP.MGR); E(ldr_imm, 1, 1, SP.HELD); E(ldr_imm, 0, 1, 0xC); E(movs_imm, 1, 0); E(bl, SP.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(lsls_imm, 0, 0, 31); E(b_cond, "hp_f", "mi")                                                           # Clear + step: smpick's
    E(lsrs_imm, 2, 4, SHIFT_BITS); E(subs_imm8, 2, 1); E(movs_imm, 0, 3); E(ands_reg, 0, 4); E(lsls_imm, 0, 0, 4); E(adds_reg, 2, 2, 0)   # the sample
    E(lsrs_imm, 1, 4, 2); E(movs_imm, 0, 1); E(ands_reg, 1, 0); E(lsls_imm, 1, 1, 4); E(adds_reg, 1, 1, 5)                               # the step
    E(mov_reg, 0, 7); E(bl, L["c_spset"])
    a.label("hp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_shrel (the container's slot 1: obj, pad): the held sample pad let go
    a.label("c_shrel")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(cmp_imm, 1, 16); E(b_cond, "hr_f", "lo"); E(mov_reg, 5, 1)
    E(bl, L["c_spst"]); E(cmp_imm, 0, 0); E(b_cond, "hr_f", "eq")
    E(ldrb_imm, 4, 0, 0); E(lsrs_imm, 1, 4, SHIFT_BITS); E(subs_imm8, 5, 15); E(cmp_reg, 1, 5); E(b_cond, "hr_f", "ne")
    E(movs_imm, 1, 7); E(ands_reg, 4, 1); E(strb_imm, 4, 0, 0)
    a.label("hr_f"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["rel"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the container's slots 0 / 1."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = {k: int(report["smpick"]["labels"][k], 16) for k in ("c_spk", "c_spst", "c_spset")}
    prev = dict(pad=u(SP.CONT_VT) & ~1, rel=u(SP.CONT_VT + 4) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, SP.CONT_VT - BASE, labels["c_shpad"] | 1)
    struct.pack_into("<I", img, SP.CONT_VT + 4 - BASE, labels["c_shrel"] | 1)
    return labels, code, prev
