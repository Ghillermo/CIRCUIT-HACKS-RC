"""SC48.4 / Beta 3.41 (the user, 2026-10-28: «also, if shift +step in note view is available, current latched notes are added into selected step»;
the stock's Shift + step in the Note view writes nothing: checked in emulation, the step's record does not change): in the Note view of a note
track (Synth 1 / 2, MIDI 1 / 2), with Shift held and notes latched on that track (arpx's Shift + key latch, the chords latched with Shift + a root
or with the chord screen's latch: chords' c_chlat), a step pad writes the latched notes into that step: each one not there yet goes into a free
unit (6 at most), one step long (6 ticks), velocity 100, micro step 0; then the stock is told (the step editor's pattern store, as smnote does)
so the step lights at once.  The press and its release are swallowed.  Without latched notes Shift + step stays the stock's.  While Shift is
held in that Note view with notes latched, the 16 step pads light yellow (the user's Shift convention; asked: «Yellow steps with Shift»).

Heads of slots 0 / 1 of the step objects (class 0x0805ADB4: 0x20041EB0 + 0x170 t; the step = pad + 16 on the 17-32 page), in front of autorel
(Shift + step in the Velocity view); the LED task calls (in front of the chain).  The pattern = autorel's c_arpat (the step-drummer's c_sdpat: the pattern the track plays / shows).
RAM: modmx.MXR + 0x1E70 (8 B, signed "LST1": + 4 the swallowed pad + 1).  In the hole (no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsls_reg,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, tst_reg, ands_reg)
import modmx as MX  # noqa: E402
import recinst as RI  # noqa: E402
import vcf21 as V  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

RAM = MX.MXR + 0x1E70
SIG = 0x3154534C                                              # "LST1"
MGR, CONT, SUB_NOTE = 0x20040B10, 0x20040DB8, 1               # the Note view: [ctrl + 0x6C] = the tracks' container, [ctrl + 0x152] = 9 t + 1
EDITOR, ED_SZ = 0x20039E50, 0x3A0                             # the note tracks' step editors (track id): [+ 0x18] the pattern store
STORE_W, COMMIT = 0x08035456, 0x080353C0
GATE, VEL, UNITS = V.SD_LEN, 100, 6
BUF = 96                                                      # the chords' latched notes (16 slots x 6) on the stack
COL_AV = 0x2D                                                 # with Shift: the step pads yellow


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev, chords):
    a = Asm(base)
    E = a.emit
    RET = h(0x4770)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_lsst() -> r0 = our RAM (signed, the swallowed pad cleared the first time); clobbers r1, r2
    a.label("c_lsst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "ss_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4)
    a.label("ss_x"); E(raw, RET)

    # ---- c_lsadd(r0 = the step's record, r1 = a note): into a free unit when it is not there yet; clobbers r0-r3
    a.label("c_lsadd")
    E(push_list, [4], lr=True)
    E(ldrb_imm, 2, 0, 0); E(movs_imm, 3, 0)                                            # r2 = the units' mask
    a.label("la_s"); E(movs_imm, 4, 1); E(lsls_reg, 4, 3); E(tst_reg, 2, 4); E(b_cond, "la_sn", "eq")
    E(lsls_imm, 4, 3, 2); E(adds_reg, 4, 4, 0); E(ldrb_imm, 4, 4, 4); E(cmp_reg, 4, 1); E(b_cond, "la_x", "eq")   # there already
    a.label("la_sn"); E(adds_imm8, 3, 1); E(cmp_imm, 3, UNITS); E(b_cond, "la_s", "lo")
    E(movs_imm, 3, 0)
    a.label("la_f"); E(movs_imm, 4, 1); E(lsls_reg, 4, 3); E(tst_reg, 2, 4); E(b_cond, "la_fn", "ne")
    E(orrs_reg, 2, 4); E(strb_imm, 2, 0, 0)
    E(lsls_imm, 4, 3, 2); E(adds_reg, 4, 4, 0); E(strb_imm, 1, 4, 4); E(movs_imm, 1, GATE); E(strb_imm, 1, 4, 5)
    E(movs_imm, 1, 0); E(strb_imm, 1, 4, 6); E(movs_imm, 1, VEL); E(strb_imm, 1, 4, 7); E(b, "la_x")
    a.label("la_fn"); E(adds_imm8, 3, 1); E(cmp_imm, 3, UNITS); E(b_cond, "la_f", "lo")                    # full: nothing
    a.label("la_x"); E(pop_list, [4], pc=True)

    # ---- c_lspad (slot 0 of the step objects: obj, pad, velocity)
    #      r4 = the track, r5 = the pad, r6 = the object / the loop, r7 = the latch bits, r8 = the chords' notes, r9 = the step's record
    a.label("c_lspad")
    E(cmp_imm, 1, 15); E(b_cond, "lp_f", "hi")
    E(raw, pushw([0, 1, 2, 4, 5, 6, 7, 8, 9], lr=True))
    E(mov_reg, 5, 1); E(mov_reg, 6, 0)
    E(bl, L["c_artrk"]); E(cmp_imm, 0, 3); E(b_cond, "lp_p", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "lp_p", "eq")
    imm32(1, MGR); E(ldr_imm, 2, 1, 0x6C); imm32(3, CONT); E(cmp_reg, 2, 3); E(b_cond, "lp_p", "ne")        # its Note view on the screen
    E(raw, h(0xF891) + h(2 << 12 | 0x152)); E(movs_imm, 3, 9); E(muls, 3, 4); E(adds_imm8, 3, SUB_NOTE); E(cmp_reg, 2, 3); E(b_cond, "lp_p", "ne")
    E(raw, h(0xB080 | BUF >> 2))                                                       # sub sp, #BUF
    E(movs_imm, 0, 0)
    if chords: E(mov_reg, 0, 4); E(mov_reg, 1, 13); E(bl, L["c_chlat"])                # the chords' latched notes on the stack
    E(mov_reg, 8, 0)
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_ltbit"]); E(mov_reg, 7, 0)          # r7 = the track's 16 latch bytes
    E(mov_reg, 1, 8); E(movs_imm, 2, 0)
    a.label("lp_any"); E(ldrb_reg, 3, 7, 2); E(orrs_reg, 1, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "lp_any", "lo")
    E(cmp_imm, 1, 0); E(b_cond, "lp_none", "eq")
    E(mov_reg, 0, 6); E(bl, L["c_arpage"]); E(adds_reg, 6, 5, 0)                       # r6 = the step
    E(mov_reg, 0, 4); E(bl, L["c_arpat"]); E(movs_imm, 1, 28); E(muls, 1, 6); E(adds_reg, 0, 0, 1); E(mov_reg, 9, 0)
    E(movs_imm, 6, 0)
    a.label("lp_b")                                                                    # the latched keys
    E(lsrs_imm, 0, 6, 3); E(ldrb_reg, 0, 7, 0); E(movs_imm, 1, 7); E(ands_reg, 1, 6); E(movs_imm, 2, 1); E(lsls_reg, 2, 1); E(tst_reg, 0, 2)
    E(b_cond, "lp_bn", "eq"); E(mov_reg, 0, 9); E(mov_reg, 1, 6); E(bl, "c_lsadd")
    a.label("lp_bn"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 128); E(b_cond, "lp_b", "lo")
    E(movs_imm, 6, 0)
    a.label("lp_c"); E(mov_reg, 0, 8); E(cmp_reg, 6, 0); E(b_cond, "lp_ce", "hs")      # the latched chords' notes
    E(mov_reg, 1, 13); E(ldrb_reg, 1, 1, 6); E(mov_reg, 0, 9); E(bl, "c_lsadd"); E(adds_imm8, 6, 1); E(b, "lp_c")
    a.label("lp_ce")
    imm32(0, EDITOR); E(movw, 1, ED_SZ); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(ldr_imm, 6, 0, 0x18)   # the stock told: the step lights
    E(mov_reg, 0, 6); E(bl, STORE_W); E(mov_reg, 0, 6); E(bl, COMMIT)
    E(raw, h(0xB000 | BUF >> 2))                                                       # add sp, #BUF
    E(bl, "c_lsst"); E(adds_imm8, 5, 1); E(strb_imm, 5, 0, 4)                          # swallowed: its release too
    E(raw, popw([0, 1, 2, 4, 5, 6, 7, 8, 9], lr=True)); E(raw, RET)
    a.label("lp_none"); E(raw, h(0xB000 | BUF >> 2))
    a.label("lp_p"); E(raw, popw([0, 1, 2, 4, 5, 6, 7, 8, 9], lr=True))
    a.label("lp_f"); E(b_w, prev["spad"])

    # ---- c_lsnote() -> r0 = the track 0..3 whose Note view is on the screen, or 0xFF; clobbers r1-r3
    a.label("c_lsnote")
    imm32(1, MGR); E(ldr_imm, 2, 1, 0x6C); imm32(3, CONT); E(cmp_reg, 2, 3); E(b_cond, "ln_n", "ne")
    E(raw, h(0xF891) + h(2 << 12 | 0x152)); E(movs_imm, 0, 0)
    a.label("ln_l"); E(movs_imm, 3, 9); E(muls, 3, 0); E(adds_imm8, 3, SUB_NOTE); E(cmp_reg, 2, 3); E(b_cond, "ln_x", "eq")
    E(adds_imm8, 0, 1); E(cmp_imm, 0, 4); E(b_cond, "ln_l", "lo")
    a.label("ln_n"); E(movs_imm, 0, 0xFF)
    a.label("ln_x"); E(raw, RET)

    # ---- c_lsany(r0 = track) -> r0 != 0 when it has latched notes (keys or chords); clobbers r1-r3
    a.label("c_lsany")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(raw, h(0xB080 | BUF >> 2)); E(movs_imm, 0, 0)
    if chords: E(mov_reg, 0, 4); E(mov_reg, 1, 13); E(bl, L["c_chlat"])
    E(push_list, [0]); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_ltbit"]); E(pop_list, [1])
    E(movs_imm, 2, 0)
    a.label("ly_l"); E(ldrb_reg, 3, 0, 2); E(orrs_reg, 1, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 16); E(b_cond, "ly_l", "lo")
    E(raw, h(0xB000 | BUF >> 2)); E(mov_reg, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_lsled (the LED task calls: ctrl, frame): the chain; then Shift + a Note view whose track has latched notes = the steps yellow
    a.label("c_lsled")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "le_x", "eq")
    E(bl, "c_lsnote"); E(cmp_imm, 0, 3); E(b_cond, "le_x", "hi")
    E(bl, "c_lsany"); E(cmp_imm, 0, 0); E(b_cond, "le_x", "eq")
    E(movs_imm, 1, COL_AV); E(movs_imm, 0, 0)
    a.label("le_l"); E(raw, h(0x5229)); E(adds_imm8, 0, 2); E(cmp_imm, 0, 32); E(b_cond, "le_l", "lo")   # strh r1, [r5, r0]
    a.label("le_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_lsrel (slot 1 of the step objects: obj, pad): the release of a swallowed press swallowed too
    a.label("c_lsrel")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(bl, "c_lsst"); E(ldrb_imm, 2, 0, 4); E(cmp_imm, 2, 0); E(b_cond, "lr_p", "eq")
    E(raw, h(0x9901)); E(adds_imm8, 1, 1); E(cmp_reg, 2, 1); E(b_cond, "lr_p", "ne")   # ldr r1, [sp, #4]: the pad
    E(movs_imm, 2, 0); E(strb_imm, 2, 0, 4); E(pop_list, [0, 1, 2, 3], pc=True)
    a.label("lr_p"); E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, prev["srel"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of slots 0 / 1 of the step objects."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_artrk=lab("autorel", "c_artrk"), c_arpat=lab("autorel", "c_arpat"), c_arpage=lab("autorel", "c_arpage"),
             c_shift=lab("sc15", "c_shift"), c_ltbit=lab("arpx", "c_ltbit"))
    chords = "c_chlat" in report.get("chords", {}).get("labels", {})
    if chords: L["c_chlat"] = lab("chords", "c_chlat")
    prev = dict(spad=u(RI.STEP_VT) & ~1, srel=u(RI.STEP_VT + 4) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev, chords)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, RI.STEP_VT - BASE, labels["c_lspad"] | 1)
    struct.pack_into("<I", img, RI.STEP_VT + 4 - BASE, labels["c_lsrel"] | 1)
    from thumb import bl as bl_enc
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_lsled"])
    assert RAM + 8 <= MX.MXR + 0x1F00
    return labels, code, prev
