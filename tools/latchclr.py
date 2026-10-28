"""SC48.3 / Beta 3.40 (the user, 2026-10-28: «have clear + channel also clear latches on such channel»): Clear held + the button of a note track
(Synth 1 / 2, MIDI 1 / 2) also lets go of that track's latched notes (arpx's Shift + key latch): every pad of its track view that still holds a
latched note gets its live note-off (0x0804AF5A: the arpeggiator's held list follows, c_arloff), and the track's latch bits go to 0.  Then the
press goes on as before (Clear + Synth = its macros, Clear + MIDI = its initial values).

A head of the button chain (0x08033320), in front of the others; Clear held = bit 0 of p0 of [[ctrl + 0x20] + 0xC], without Shift.  In the hole.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, bics_reg, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, raw, strb_imm, tst_reg)
import mpatch as MP  # noqa: E402
import arp as A  # noqa: E402
import janko as J  # noqa: E402

BTN_ENTRY = MP.BTN_ENTRY
PARAM_GET = 0x0803542C
HELD = 0x20                                                   # [ctrl + 0x20]: the held buttons' object; p0 of its [+ 0xC] bit 0 = Clear
CHORDS = False                                                # SC48.4 (use_chords)


def use_chords():
    """SC48.4 / Beta 3.41 (with chords.use_slatch, the user: «make latch work on chord mode»): Clear + the track's button also lets go of the
    chords latched with Shift + a root in its chord screen (chords' c_chslclr)."""
    global CHORDS
    CHORDS = True


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_lcbtn (the head of the button chain: ctrl, id): Clear + a note track's button = its latched notes let go, then the chain
    a.label("c_lcbtn")
    E(cmp_imm, 1, 3); E(b_cond, "lc_f", "hi")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(mov_reg, 4, 1)                                                                   # r4 = the track
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "lc_x", "ne")
    E(raw, h(0x9800)); E(ldr_imm, 0, 0, HELD); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET)   # ldr r0, [sp]: ctrl
    E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "lc_x", "eq")   # Clear held?
    imm32(5, J.VIEW_SZ); E(muls, 5, 4); imm32(0, J.VIEW0); E(adds_reg, 5, 5, 0)        # r5 = the track's view
    E(movs_imm, 6, 0)
    a.label("lc_p")
    E(adds_reg, 0, 5, 6); E(raw, ldrb_w(7, 0, 0x40)); E(cmp_imm, 7, 0); E(b_cond, "lc_n", "eq")   # r7 = the note the pad holds
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, L["c_ltbit"]); E(ldrb_imm, 2, 0, 0); E(tst_reg, 2, 1); E(b_cond, "lc_n", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 0, 0)
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, A.LIVE_OFF)                             # latched: its note-off
    a.label("lc_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "lc_p", "lo")
    E(movs_imm, 6, 0)                                                                  # the rest of the track's latch bits
    a.label("lc_z"); E(mov_reg, 0, 4); E(lsls_imm, 1, 6, 3); E(bl, L["c_ltbit"]); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "lc_z", "lo")
    if CHORDS: E(mov_reg, 0, 4); E(bl, L["c_chslclr"])                                  # (CHORDS) its Shift-latched chords too
    a.label("lc_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    a.label("lc_f"); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the button chain."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_ltbit=lab("arpx", "c_ltbit"))
    if CHORDS: L["c_chslclr"] = lab("chords", "c_chslclr")
    prev = dict(btn=MP.bw_target(img, BTN_ENTRY, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = bw_enc(BTN_ENTRY, labels["c_lcbtn"])
    return labels, code, prev
