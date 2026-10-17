"""SC43.4 (the user, 2026-10-16: «Clear + drum / synth: back to init knob settings»): Clear + a Drum button, with that drum's view on the screen,
puts its eight knobs (both layers) back to their defaults, as Clear + each knob to the right does.

The stock (emulated): Clear + a knob to the right puts a stock drum knob back to its default only after a sustained turn (between 7 and 46 events
of the knob; one or five do nothing); our drum knobs (persist19's handler, slot 4 of the drum macro handlers) go back at the first event, their Shift
layer with them (CLEAR_BOTH), K3's attack / start / cut and K8's bitcrush too.  The MIDI tracks already have this (psave's c_psbtn, c_vreset).

Ours: in front of the controller's button chain (0x08033320): Clear held (Duplicate not) + Drum 1-4 (ids 4-7) while one of that drum's views shows
([ctrl + 0x152] = 36 + 8 d .. 36 + 8 d + 7, the track views' container on the screen) = 48 events of +1 for each of its 8 knobs through its handler's
slot 4 (persist19's: the stock's Clear for the stock knobs, ours for the others); the press goes no further.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, muls, pop_list, push_list, raw, subs_imm8, subs_reg, ands_reg)
import mpatch as MP  # noqa: E402

MGR, PARAM_GET = 0x20040B10, 0x0803542C
SYNTH = False                                   # SC43.5 (use_synth)
CONT, SYN_VT = 0x20040DB8, 0x0805AC9C           # (SYNTH) the tracks' container; [CONT + 0x78 + 4 s] = Synth s's Preset view (vtable checked)
SYN_SUBS = 9                                    # [ctrl + 0x152] = 9 s (Preset) / 9 s + 1 (track view) for Synth s
MACRO_P0, MACRO_STEP, PATCH_OFF = 174, 17, 30   # macro m's position = parameter 174 + 17 m = byte 30 + parameter of the patch record


def use_synth():
    """SC43.5 (the user, 2026-10-16: «Clear + Synth 1 / 2: the macros back to the values saved in the loaded patch»: yes): Clear + Synth 1 / 2 with
    that synth's view on the screen = the patch it plays read again from the pack's bank (its 340-byte record, by the content API as the patch save
    writes it: mpatch.c_mpr into the shared buffer under its lock) and its eight macro positions set again as a received NRPN (macroed.c_mcset: the
    patch in RAM, the macro offsets, the DSP).  The stock has nothing for it: choosing the patch that is already chosen does not load it again
    (0x0804D242 only stops the preview note, 0x0804D504)."""
    global SYNTH
    SYNTH = True
AUTOCLR = False                                 # SC43.7 (use_autoclr)


def use_autoclr():
    """SC43.7 (the user, 2026-10-17: «clear+drum# to clear all automations and back to init»): Clear + a Drum button first turns each of its eight
    knobs 48 clicks to the left (the stock's Clear + knob left: after 40 the knob's automation lane of the pattern is deleted; the mod's own knobs
    only show red), then 48 to the right as before (the defaults)."""
    global AUTOCLR
    AUTOCLR = True
S_CUR, DRUM_SUB0, DRUM_SUBS = 0x152, 36, 8
EVENTS = 48


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_crbtn (the controller's button press: ctrl, id): Clear + Drum 1-4 on that drum's views = its knobs back to their defaults
    a.label("c_crbtn")
    if SYNTH: E(cmp_imm, 1, 1); E(b_cond, "cb_syn", "ls")
    E(cmp_imm, 1, 4); E(b_cond, "cb_f", "lo"); E(cmp_imm, 1, 7); E(b_cond, "cb_f", "hi")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
    E(subs_imm8, 1, 4); E(mov_reg, 4, 1)                                                                 # r4 = the drum
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(cmp_imm, 0, 1); E(b_cond, "cb_p", "ne")                       # Clear held, Duplicate not
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "cb_p", "ne")
    E(ldrb_w, 1, 0, S_CUR); E(subs_imm8, 1, DRUM_SUB0); E(lsls_imm, 2, 4, 3); E(subs_reg, 1, 1, 2); E(cmp_imm, 1, DRUM_SUBS - 1); E(b_cond, "cb_p", "hi")
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "cb_p", "eq"); E(mov_reg, 5, 0)          # r5 = its macro handler
    E(movs_imm, 6, 0)
    a.label("cb_k")
    if AUTOCLR:                                                                                          # left first: the automation deleted
        E(movs_imm, 7, EVENTS)
        a.label("cb_m")
        E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(movs_imm, 2, 1); E(raw, h(0x4252)); E(ldr_imm, 3, 5, 0); E(ldr_imm, 3, 3, 16); E(raw, h(0x4798))   # negs r2, r2; blx r3
        E(subs_imm8, 7, 1); E(b_cond, "cb_m", "ne")
    E(movs_imm, 7, EVENTS)
    a.label("cb_n")
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(movs_imm, 2, 1); E(ldr_imm, 3, 5, 0); E(ldr_imm, 3, 3, 16); E(raw, h(0x4798))   # blx r3: slot 4
    E(subs_imm8, 7, 1); E(b_cond, "cb_n", "ne")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "cb_k", "lo")
    E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
    a.label("cb_p"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True))
    a.label("cb_f"); E(b_w, prev["btn"])
    if SYNTH:
        import packio as PK
        # ---- Clear + Synth 1 / 2 on its views: the eight macro positions of the loaded patch's record again
        a.label("cb_syn")
        E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 1)                                                                                 # r4 = the synth
        imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
        E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(cmp_imm, 0, 1); E(b_cond, "cs_p", "ne")                   # Clear held, Duplicate not
        imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "cs_p", "ne")
        E(ldrb_w, 1, 0, S_CUR); E(movs_imm, 2, SYN_SUBS); E(muls, 2, 4); E(subs_reg, 1, 1, 2); E(cmp_imm, 1, 1); E(b_cond, "cs_p", "hi")
        imm32(0, CONT + 0x78); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 5, 0, 0)            # r5 = its Preset view
        E(ldr_imm, 0, 5, 0); imm32(1, SYN_VT); E(cmp_reg, 0, 1); E(b_cond, "cs_p", "ne")
        E(ldr_imm, 0, 5, 0x14); E(movs_imm, 1, 10); E(bl, PARAM_GET); E(ldrb_imm, 6, 0, 0)               # r6 = the patch it plays
        E(cmp_imm, 6, 127); E(b_cond, "cs_p", "hi")
        E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
        E(lsrs_imm, 0, 6, 3); E(lsls_imm, 1, 6, 29); E(lsrs_imm, 1, 1, 20); imm32(2, PK.BUF); imm32(3, PK.PATCH_SZ); E(bl, L["c_mpr"])
        E(cmp_imm, 0, 0); E(b_cond, "cs_u", "ne")
        E(movs_imm, 7, 0)
        a.label("cs_m")
        E(movs_imm, 0, MACRO_STEP); E(muls, 0, 7); E(adds_imm8, 0, MACRO_P0); E(mov_reg, 1, 0)             # r1 = the parameter
        imm32(2, PK.BUF + PATCH_OFF); E(adds_reg, 2, 2, 1); E(ldrb_imm, 2, 2, 0)                          # r2 = its byte in the record
        E(mov_reg, 0, 4); E(bl, L["c_mcset"])
        E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "cs_m", "lo")
        a.label("cs_u"); E(bl, PK.BUF_UNLOCK)
        E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
        a.label("cs_p"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True)); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the controller's button chain."""
    import ct_fw
    from thumb import b_w as bw
    BASE = ct_fw.APP_BASE
    L = dict(c_mh=int(report["sc18"]["labels"]["c_mh"], 16))
    if SYNTH: L.update(c_mpr=int(report["mpatch"]["labels"]["c_mpr"], 16), c_mcset=int(report["macroed"]["labels"]["c_mcset"], 16))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = bw(MP.BTN_ENTRY, labels["c_crbtn"])
    return labels, code, prev
