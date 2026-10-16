"""SC42.6 (the user, 2026-10-16): the step-drummer's second page gets its own destination, and a pitch-vel toggle.

The user, on SC42.5: «On step-drummer Mode: pitch-vel mode seem to do nothing on pitch. There's no way to route Page 2 to any parameter»; then:
«Además de su envío asignado, el toggle envía el primer parámetro a pitch y el segundo a vel»; «Pad 32 on step-drummer view. B: on scale c: yes»
(pitch = the notes transposed in degrees of the project's scale; with the toggle off page 2 does not touch the velocity); and «el pad 6
(activador step-drummer) debe mostrarse tenue al principio de la vista (ahora está apagado, aunque funciona)».

vcf21's step-drummer (SC26 / SC27): tracks 0 / 1 = MIDI 1 / 2, 2 / 3 = Synth 1 / 2; page 1 (Octave ^) = the pitch row: 12 bytes of a lane per pair of
steps (MIDI: lane 0, its offset value - 64 goes to the destination of pads 17-24 of the own synth through c_sdfx; synth: the lane of the macro the
pads chose, played by the stock engine); page 2 (Octave v) = the velocity of the pair's notes.  On a MIDI track to external gear the pitch row did
nothing (the destinations are the own synth's), and page 2 had no destination.

Ours (a block in the session record's tail + 988, saved with the project: "PV", a byte per track (bit 7 = the toggle, bit 3 = page 2 has a
destination, bits 0-2 = which of the 8), a check byte; + 7 / + 8 = the auditioned note, + 9 = pad 32 was lit in the MIDI view (RAM)):
  * pad 32 of the step-drummer view (in front of slot 0 of the MIDI template view and of the synth Preset view) = the toggle (green / dim green);
  * page 2: pads 17-24 = its destination (the same pad again = none); the knobs write the page-2 lane of the pair (MIDI: lane 1, the REL lane, which
    the step-drummer then owns: not played / recorded as REL while it is enabled; synth: the lane of the macro chosen) and, with the toggle, the
    velocity as before; LEDs: the page-2 value in the destination's colour (the toggle on: the velocity, as before);
  * c_sdfx (what the own synth's values get on the way to the DSP) sums the offsets of both pages for their destinations;
  * the toggle on: every note of the track (the player's note load at 0x08040EFC, after stepmod) moves by (page-1 value - 64) degrees of the scale
    (the stock's or the custom one of cscale), clamped 0..127; the audition of a step too (its note-off finds the same note);
  * MIDI tracks: pad 30 dim when the step-drummer is off (it was dark), bright when it is on.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm,  # noqa: E402
                   ldr_sp, ldrb_imm, ldrb_reg, ldrb_w, ldrh_reg, lsls_imm, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg,
                   pop_list, push_list, raw, str_sp, strb_imm, strh_imm, strh_reg, subs_imm8, subs_reg, tst_reg)
import vcf21 as V  # noqa: E402
import mutate39 as MU  # noqa: E402
from build_sc14 import udiv  # noqa: E402

SESSION_OBJ, TAIL, O_BLK = 0x2003D71C, 0x27024, 988
B_TRK, B_SUM, B_AUD, B_AUDN, B_LED = 2, 6, 7, 8, 9
F_PV, F_D2 = 0x80, 0x08
KB = 0x20041044
TMPL_VT, SYN_VT = 0x0805AE5C, 0x0805AC9C
PAD_PV = 31                                    # pad 32
COL_PV = (0x17, 0x18)                          # the toggle on / off: green / dim green
HEAD_LED = V.SD_HEAD | (127 + 2) << 8          # the knob of the pair that plays (white)
HEADS = dict(c_sdknob="f0b50446", c_sdpad="f0b50446", c_sdfx="f4b50446", c_sdmark="022800d3", c_sdkleds="2de9f043", c_sdio="f0b50446",
             c_vapply="f0b50446", c_vcc_rec="f0b50446")


V2 = False                                     # SC42.7 (use_v2)
DEG_UNITS = 8                                  # (V2) knob units per degree of the transposition


def use_v2():
    """SC42.7 (the user, 2026-10-16: «en step-drummer: poner los knobs por defecto a cero (ahora mismo están al máximo). el modo pitch/vel no parece
    funcionar correctamente»): on Synth 1 / 2 an empty pair started from the macro's position (127 on a patch with macro 1 at the top: all the knobs
    lit at the top, and with the toggle +63 degrees): it starts from 0 now (both pages); the transposition is one degree every 8 knob units (MIDI:
    (value - 64) / 8, -8..+8; synths, from 0: value / 8, 0..+16), as the pitch destination's octave over the knob; with the toggle on, page 1's pitch
    destinations (the pitch of both oscillators / of OSC2) no longer move the own synth too (the note already moves: the two together left the scale)."""
    global V2
    V2 = True


V3 = False                                     # SC43.3 (use_v3)
BIP_CODES = (17, 27, 3)                        # (V3) the bipolar destinations: the pitch of both oscillators, of OSC 2, envelope -> filter


def use_v3():
    """SC43.3 (the user, 2026-10-16, on a MIDI track of a fresh project: «los knobs de step drummer siguen estando al máximo por defecto … Set centre
    for bipolar parameters and 0 for unipolar, both with dimmer = no modulation, brighter = positive or negative modulation»): on MIDI 1 / 2 the
    point of no modulation follows the destination of the page (pads 17-24): 64 for the bipolar ones (BIP_CODES, as vcf21.BIPOLAR_MASK), 0 for the
    unipolar ones (WAVE, FM, MIX, SHAPE, decay: their offset only adds); an empty pair starts there, the offset is value - that point (both pages),
    the pitch-vel transposition counts from it, and the knob LEDs show the amount: brightness |value - point| (x 2 for the bipolar ones), dim at no
    modulation.  Synth 1 / 2 (absolute macro positions from 0) and the FX sequencer as before."""
    global V3
    assert V2
    V3 = True


V4 = False                                     # SC43.4 (use_v4)


def use_v4():
    """SC43.4 (the user, 2026-10-16: «For the step drummer, I was mistaken. Make all knobs bipolar (so they add / subtract to the manually set value
    on parameter view) centered and dim, with positive / negative modulation making them brighter»): use_v3 with every destination bipolar: on
    MIDI 1 / 2 an empty pair = 64 for all of them, the offset value - 64 is added to (or taken from) the value set on the engine's page, and the LED
    is dim at the centre and brighter the further it goes either way."""
    global V4
    use_v3()
    V4 = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi", "ge": "lt", "lt": "ge", "gt": "le", "le": "gt"}

    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    def clamp(r, lo, hi, tmp, tag):                                                  # r = max(lo, min(hi, r)) (signed)
        E(cmp_imm, r, hi); E(b_cond, tag + "h", "le"); E(movs_imm, r, hi)
        a.label(tag + "h")
        if lo >= 0:
            E(cmp_imm, r, lo); E(b_cond, tag + "l", "ge"); E(movs_imm, r, lo)
        else:
            E(movs_imm, tmp, 0); E(subs_imm8, tmp, -lo); E(cmp_reg, r, tmp); E(b_cond, tag + "l", "ge"); E(mov_reg, r, tmp)
        a.label(tag + "l")

    RET = h(0x4770)
    tab = bytes(V.SD_DEST) + bytes(V.SD_DCOL) + (bytes(64 if V4 or c in BIP_CODES else 0 for c in V.SD_DEST) if V3 else b"")
    for i in range(0, len(tab), 2): E(raw, tab[i:i + 2])
    t_dest, t_col, t_bip = base, base + 8, base + 16

    if V3:
        # ---- c_pvbip(r0 = a destination 0..7) -> r0 = its point of no modulation (64 bipolar, 0 unipolar); clobbers r1
        a.label("c_pvbip")
        imm32(1, t_bip); E(ldrb_reg, 0, 1, 0); E(raw, h(0x4770))
        # ---- c_pvamt(r0 = a value, r1 = its point) -> r0 = the brightness of the amount: |value - point|, x 2 when the point is 64, at most 127
        a.label("c_pvamt")
        E(subs_reg, 0, 0, 1); E(b_cond, "am_p", "pl"); E(raw, h(0x4240))                         # negs r0, r0
        a.label("am_p"); E(cmp_imm, 1, 0); E(b_cond, "am_k", "eq"); E(lsls_imm, 0, 0, 1)
        a.label("am_k"); E(cmp_imm, 0, 127); E(b_cond, "am_x", "ls"); E(movs_imm, 0, 127)
        a.label("am_x"); E(raw, h(0x4770))

    # ---- c_pvblk() -> r0 = our block, or 0; clobbers r1
    a.label("c_pvblk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("bk_x"); E(raw, RET)

    # ---- c_pvok(r0 = the block) -> r0 = 1 when it holds ours; clobbers r1, r2
    a.label("c_pvok")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x50); E(b_cond, "ok_n", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x56); E(b_cond, "ok_n", "ne")
    E(ldrb_imm, 1, 0, B_TRK)
    for k in range(1, 4): E(ldrb_imm, 2, 0, B_TRK + k); E(eors_reg, 1, 2)
    E(movs_imm, 2, 0x5A); E(eors_reg, 1, 2); E(ldrb_imm, 2, 0, B_SUM); E(cmp_reg, 1, 2); E(b_cond, "ok_n", "ne")
    E(movs_imm, 0, 1); E(raw, RET)
    a.label("ok_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_pvget(r0 = track) -> r0 = its byte (0 without our block); clobbers r1-r3
    a.label("c_pvget")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_pvblk"); E(mov_reg, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "pg_z", "eq")
    E(bl, "c_pvok"); E(cmp_imm, 0, 0); E(b_cond, "pg_z", "eq")
    E(adds_reg, 0, 5, 4); E(ldrb_imm, 0, 0, B_TRK); E(pop_list, [4, 5], pc=True)
    a.label("pg_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_pvset(r0 = track, r1 = its byte): the block made when missing; clobbers r0-r3
    a.label("c_pvset")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_pvblk"); E(mov_reg, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "ps_x", "eq")
    E(bl, "c_pvok"); E(cmp_imm, 0, 0); E(b_cond, "ps_ok", "ne")
    E(movs_imm, 0, 0x50); E(strb_imm, 0, 6, 0); E(movs_imm, 0, 0x56); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 0)
    for k in range(4): E(strb_imm, 0, 6, B_TRK + k)
    E(strb_imm, 0, 6, B_AUD)
    a.label("ps_ok")
    E(adds_reg, 0, 6, 4); E(strb_imm, 5, 0, B_TRK)
    E(ldrb_imm, 1, 6, B_TRK)
    for k in range(1, 4): E(ldrb_imm, 2, 6, B_TRK + k); E(eors_reg, 1, 2)
    E(movs_imm, 2, 0x5A); E(eors_reg, 1, 2); E(strb_imm, 1, 6, B_SUM)
    a.label("ps_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pvon(r0 = track) -> r0 = 1 with the toggle on; c_pvd2(r0 = track) -> r0 = page 2's destination 0..7, or 0xFF; clobber r1-r3
    a.label("c_pvon")
    E(raw, h(0xB500)); E(bl, "c_pvget"); E(lsrs_imm, 0, 0, 7); E(raw, h(0xBD00))
    a.label("c_pvd2")
    E(raw, h(0xB500)); E(bl, "c_pvget"); E(movs_imm, 1, F_D2); E(tst_reg, 0, 1); E(b_cond, "d2_n", "eq")
    E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(raw, h(0xBD00))
    a.label("d2_n"); E(movs_imm, 0, 0xFF); E(raw, h(0xBD00))

    # ---- c_pvlofs2(r0 = track, r1 = destination) -> r0 = the offset of page 2's lane: MIDI lane 1, a synth the macro's; c_pvbase2 -> what an empty pair shows
    a.label("c_pvlofs2")
    E(cmp_imm, 0, 2); E(b_cond, "lf_s", "hs"); E(movs_imm, 0, 192); E(raw, RET)
    a.label("lf_s"); E(movs_imm, 0, 192); E(muls, 0, 1); E(raw, RET)
    a.label("c_pvbase2")
    if V3: E(cmp_imm, 0, 2); E(b_cond, "bs_s", "hs"); E(mov_reg, 0, 1); E(b, "c_pvbip")          # (V3) MIDI: the destination's point
    else: E(cmp_imm, 0, 2); E(b_cond, "bs_s", "hs"); E(movs_imm, 0, 64); E(raw, RET)
    a.label("bs_s")
    if V2: E(movs_imm, 0, 0); E(raw, RET)                                             # (V2) a synth's empty pair: 0
    E(raw, h(0xB500)); E(movs_imm, 2, 17); E(muls, 1, 2); E(adds_imm8, 1, 174); E(subs_imm8, 0, 2); E(bl, V.GETTER)
    E(cmp_imm, 0, 127); E(b_cond, "bs_x", "ls"); E(movs_imm, 0, 127)
    a.label("bs_x"); E(raw, h(0xBD00))

    # ---- c_pvlane2(r0 = track, r1 = step) -> r0 = the page-2 lane bytes of that step, 0 without a destination; clobbers r1-r3
    a.label("c_pvlane2")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_pvd2"); E(cmp_imm, 0, 0xFF); E(b_cond, "la_z", "eq"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, L["c_sdpat"]); E(mov_reg, 1, 5); E(bl, L["c_sdlna"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_pvlofs2"); E(adds_reg, 0, 0, 5); E(pop_list, [4, 5, 6], pc=True)
    a.label("la_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pvval2(r0 = track, r1 = step) -> r0 = the page-2 value shown (an empty pair: the base), 0xFF without a destination; clobbers r1-r3
    a.label("c_pvval2")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_pvlane2"); E(cmp_imm, 0, 0); E(b_cond, "vv_n", "eq")
    E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 127); E(b_cond, "vv_x", "ls")
    E(mov_reg, 0, 4); E(bl, "c_pvd2"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pvbase2")
    a.label("vv_x"); E(pop_list, [4], pc=True)
    a.label("vv_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_pvoff2(r0 = a MIDI track) -> r0 = the offset of page 2 at the step that counts (-64..63; none = 0); clobbers r1-r3
    a.label("c_pvoff2")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, L["c_sdpos"]); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pvlane2"); E(cmp_imm, 0, 0); E(b_cond, "of_z", "eq")
    E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 127); E(b_cond, "of_z", "hi")
    if V3:                                                                            # (V3) value - the destination's point
        E(push_list, [0]); E(mov_reg, 0, 4); E(bl, "c_pvd2"); E(bl, "c_pvbip"); E(mov_reg, 1, 0); E(pop_list, [0]); E(subs_reg, 0, 0, 1)
        E(pop_list, [4], pc=True)
    else: E(subs_imm8, 0, 64); E(pop_list, [4], pc=True)
    a.label("of_z"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_pvmark2(r0 = track): page 2's destination goes to the DSP again (MIDI, the step-drummer on); clobbers r0-r3
    a.label("c_pvmark2")
    E(cmp_imm, 0, 2); E(b_cond, "m2_m", "lo"); E(raw, RET)
    a.label("m2_m")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, L["c_sden"]); E(cmp_imm, 0, 0); E(b_cond, "m2_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_pvd2"); E(cmp_imm, 0, 0xFF); E(b_cond, "m2_x", "eq"); E(mov_reg, 5, 0)
    E(cmp_imm, 5, 1); E(b_cond, "m2_s", "hi")
    E(cmp_imm, 5, 0); E(b_cond, "m2_2", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 17); E(bl, L["c_vmark"]); E(mov_reg, 0, 4); E(movs_imm, 1, 18); E(bl, L["c_vmark"])
    a.label("m2_2"); E(mov_reg, 0, 4); E(movs_imm, 1, 27); E(bl, L["c_sdcur"]); E(b, "m2_x")
    a.label("m2_s")
    imm32(3, t_dest); E(ldrb_reg, 1, 3, 5); E(mov_reg, 0, 4); E(cmp_imm, 1, 26); E(b_cond, "m2_v", "hi"); E(bl, L["c_vmark"]); E(b, "m2_x")
    a.label("m2_v"); E(bl, L["c_sdcur"])
    a.label("m2_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_pvmk (c_sdmark's first 4 bytes): the stock's mark, then page 2's
    a.label("c_pvmk")
    E(cmp_imm, 0, 2); E(b_cond, "mk_m", "lo"); E(raw, RET)
    a.label("mk_m")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_sdmark"] + 6)
    E(mov_reg, 0, 4); E(bl, "c_pvmark2"); E(pop_list, [4], pc=True)

    # ---- c_pvmatch(r0 = a destination, r1 = a code) -> r0 = 0 none / 1 a pitch destination of that oscillator code / 2 a single one; clobbers r2, r3
    a.label("c_pvmatch")
    E(cmp_imm, 0, 1); E(b_cond, "mt_s", "hi")
    E(cmp_imm, 1, 27); E(b_cond, "mt_p", "eq"); E(cmp_imm, 1, 28); E(b_cond, "mt_p", "eq")
    E(cmp_imm, 0, 0); E(b_cond, "mt_n", "ne")
    E(cmp_imm, 1, 17); E(b_cond, "mt_p", "eq"); E(cmp_imm, 1, 18); E(b_cond, "mt_p", "eq")
    a.label("mt_n"); E(movs_imm, 0, 0); E(raw, RET)
    a.label("mt_p"); E(movs_imm, 0, 1); E(raw, RET)
    a.label("mt_s"); imm32(3, t_dest); E(ldrb_reg, 2, 3, 0); E(cmp_reg, 2, 1); E(b_cond, "mt_n", "ne"); E(movs_imm, 0, 2); E(raw, RET)

    # ---- c_pvfx (c_sdfx's first 4 bytes, all of it): r0 = track, r1 = the stored value of a code, r2 = code - 1 -> r1 = the value for the DSP:
    #      the offsets of page 1 and page 2 summed for their destinations (the pitch ones: 128 TUNE + FINE + 24 offset); r2, r4-r7 kept; clobbers r0, r3
    a.label("c_pvfx")
    E(raw, pushw([2, 4, 5, 6, 7, 8, 9], lr=True))
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(adds_imm8, 6, 1)
    E(mov_reg, 0, 4); E(bl, L["c_sden"]); E(cmp_imm, 0, 0); bc("fx_x", "eq")
    E(movs_imm, 7, 0); E(mov_reg, 8, 7); E(mov_reg, 9, 7)                              # r7 = the pitch offset, r8 = the single one, r9 = the kinds that matched
    for pg in (1, 2):
        nx = f"fx_n{pg}"
        if pg == 1:
            E(mov_reg, 0, 4); E(bl, L["c_sdnib"]); E(lsrs_imm, 0, 0, 1)
            if V2:                                                                    # the toggle on: page 1's pitch destinations are the note's
                E(cmp_imm, 0, 1); E(b_cond, "fx_pd", "hi")
                E(mov_reg, 0, 4); E(bl, "c_pvon"); E(cmp_imm, 0, 0); bc(nx, "ne")
                E(mov_reg, 0, 4); E(bl, L["c_sdnib"]); E(lsrs_imm, 0, 0, 1)
                a.label("fx_pd")
        else:
            E(mov_reg, 0, 4); E(bl, "c_pvd2"); E(cmp_imm, 0, 0xFF); bc(nx, "eq")
        E(mov_reg, 1, 6); E(bl, "c_pvmatch"); E(cmp_imm, 0, 0); bc(nx, "eq")
        E(mov_reg, 1, 9); E(orrs_reg, 1, 0); E(mov_reg, 9, 1)
        E(push_list, [0]); E(mov_reg, 0, 4); E(bl, ("c_pvoff1" if V3 else L["c_sdoff"]) if pg == 1 else "c_pvoff2"); E(pop_list, [1])
        E(cmp_imm, 1, 1); E(b_cond, f"fx_s{pg}", "ne"); E(adds_reg, 7, 7, 0); E(b, nx)
        a.label(f"fx_s{pg}"); E(mov_reg, 1, 8); E(adds_reg, 1, 1, 0); E(mov_reg, 8, 1)
        a.label(nx)
    E(mov_reg, 0, 9); E(movs_imm, 1, 1); E(tst_reg, 0, 1); bc("fx_g", "eq")
    E(movs_imm, 3, 17); E(cmp_imm, 6, 27); E(b_cond, "fx_tc", "lo"); E(movs_imm, 3, 27)
    a.label("fx_tc"); E(mov_reg, 9, 3)                                                 # r9 = the TUNE code of the oscillator
    E(mov_reg, 0, 4); E(mov_reg, 1, 9); E(bl, L["c_vvaddr"]); E(raw, V.ldrsb_w(0, 0, 0)); E(lsls_imm, 5, 0, 7)
    E(mov_reg, 0, 4); E(mov_reg, 1, 9); E(adds_imm8, 1, 1); E(bl, L["c_vvaddr"]); E(raw, V.ldrsb_w(0, 0, 0)); E(adds_reg, 5, 5, 0)
    E(movs_imm, 1, 24); E(muls, 1, 7); E(adds_reg, 5, 5, 1)
    E(mov_reg, 0, 5); E(adds_imm8, 0, 64); E(raw, V.asrs_imm(0, 0, 7))
    clamp(0, -64, 63, 1, "fx_t")
    E(mov_reg, 1, 9); E(cmp_reg, 6, 1); E(b_cond, "fx_f", "ne"); E(mov_reg, 5, 0); E(b, "fx_x")
    a.label("fx_f"); E(lsls_imm, 1, 0, 7); E(subs_reg, 5, 5, 1)
    clamp(5, -64, 63, 1, "fx_q")
    E(b, "fx_x")
    a.label("fx_g")                                                                    # single destinations: value + offsets, in the range of the code
    E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "fx_x", "eq")
    E(mov_reg, 0, 8); E(adds_reg, 5, 5, 0)
    E(cmp_imm, 6, 3); E(b_cond, "fx_u", "ne")
    clamp(5, -64, 63, 1, "fx_b")
    E(b, "fx_x")
    a.label("fx_u")
    E(cmp_imm, 6, 20); E(b_cond, "fx_w", "ne")
    clamp(5, 0, 100, 1, "fx_c")
    E(b, "fx_x")
    a.label("fx_w")
    clamp(5, 0, 127, 1, "fx_d")
    a.label("fx_x"); E(mov_reg, 1, 5); E(raw, popw([2, 4, 5, 6, 7, 8, 9])); E(raw, h(0xBD00))

    # ---- c_pvknob (c_sdknob's first 4 bytes: track, knob, delta): page 2 with a destination = its lane (both steps of the pair); the velocity only with the toggle
    a.label("c_pvknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(movs_imm, 0, V.F_SDPAGE); E(bl, L["c_sdflag"]); E(cmp_imm, 0, 0); bc("kn_o", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); bc("kn_o", "ne")              # the FX sequencer: as it was
    E(mov_reg, 0, 4); E(bl, "c_pvget"); E(mov_reg, 7, 0)
    E(movs_imm, 1, F_D2); E(tst_reg, 0, 1); bc("kn_v", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_sdconv"])
    E(lsls_imm, 0, 5, 1); E(bl, L["c_sdhalf"]); E(mov_reg, 1, 0)
    E(mov_reg, 0, 4); E(bl, "c_pvlane2"); E(mov_reg, 5, 0)
    E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, 127); E(b_cond, "kn_a", "ls")
    E(movs_imm, 1, 7); E(ands_reg, 1, 7); E(mov_reg, 0, 4); E(bl, "c_pvbase2")
    a.label("kn_a")
    E(adds_reg, 0, 0, 6); clamp(0, 0, 127, 1, "kn_c")
    for i in range(12): E(strb_imm, 0, 5, i)
    E(mov_reg, 0, 4); E(bl, "c_pvmark2")
    a.label("kn_v")
    E(lsrs_imm, 0, 7, 7); E(b_cond, "kn_o", "ne")
    E(raw, h(0xB003)); E(pop_list, [4, 5, 6, 7], pc=True)                               # add sp, #12
    a.label("kn_o")
    E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(raw, bytes.fromhex(HEADS["c_sdknob"])); E(b_w, L["c_sdknob"] + 4)

    # ---- c_pvpad (c_sdpad's first 4 bytes: track, pad 0..23): on page 2 pads 17-24 = its destination (the same again = none)
    a.label("c_pvpad")
    E(push_list, [0, 1, 4, 5, 6], lr=True)
    E(cmp_imm, 1, 16); bc("pp_o", "lo")
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(movs_imm, 0, V.F_SDPAGE); E(bl, L["c_sdflag"]); E(cmp_imm, 0, 0); bc("pp_o", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); bc("pp_o", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pvmark2")                                              # the old destination goes plain
    E(mov_reg, 0, 4); E(bl, "c_pvget"); E(mov_reg, 6, 0)
    E(subs_imm8, 5, 16)
    E(movs_imm, 0, F_D2); E(tst_reg, 6, 0); E(b_cond, "pp_s", "eq")
    E(movs_imm, 0, 7); E(ands_reg, 0, 6); E(cmp_reg, 0, 5); E(b_cond, "pp_s", "ne")
    E(movs_imm, 0, 0x0F); E(bics_reg, 6, 0); E(b, "pp_w")
    a.label("pp_s"); E(movs_imm, 0, 0x0F); E(bics_reg, 6, 0); E(adds_imm8, 5, F_D2); E(orrs_reg, 6, 5)
    a.label("pp_w"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_pvset")
    E(mov_reg, 0, 4); E(bl, "c_pvmark2")
    E(raw, h(0xB002)); E(pop_list, [4, 5, 6], pc=True)                                  # add sp, #8
    a.label("pp_o")
    E(raw, popw([0, 1, 4, 5, 6], lr=True)); E(raw, bytes.fromhex(HEADS["c_sdpad"])); E(b_w, L["c_sdpad"] + 4)

    # ---- c_pvkl (c_sdkleds' first 4 bytes: track, the knob LEDs): page 2 with the toggle off = the page-2 values in the destination's colour (none: dark)
    a.label("c_pvkl_t")
    E(raw, bytes.fromhex(HEADS["c_sdkleds"])); E(b_w, L["c_sdkleds"] + 4)
    a.label("c_pvkl")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True)
    E(bl, "c_pvkl_t")
    E(ldr_sp, 4, 0); E(ldr_sp, 5, 4)
    E(movs_imm, 0, V.F_SDPAGE); E(bl, L["c_sdflag"]); E(cmp_imm, 0, 0); bc("kl_p1" if V3 else "kl_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); bc("kl_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pvon"); E(cmp_imm, 0, 0); bc("kl_x", "ne")
    E(movs_imm, 6, 0)
    a.label("kl_l")
    E(lsls_imm, 0, 6, 1); E(ldrh_reg, 1, 5, 0); E(movw, 2, HEAD_LED); E(cmp_reg, 1, 2); E(b_cond, "kl_n", "eq")   # the pair that plays stays white
    E(lsls_imm, 0, 6, 1); E(bl, L["c_sdhalf"]); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pvval2")
    E(cmp_imm, 0, 0xFF); E(b_cond, "kl_c", "ne"); E(movs_imm, 0, 0); E(b, "kl_w")
    a.label("kl_c")
    E(mov_reg, 7, 0); E(mov_reg, 0, 4); E(bl, "c_pvd2")
    if V3:                                                                            # (V3) MIDI: the amount from the destination's point
        E(cmp_imm, 4, 2); E(b_cond, "kl_cs", "hs")
        E(push_list, [0]); E(bl, "c_pvbip"); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(bl, "c_pvamt"); E(mov_reg, 7, 0); E(pop_list, [0])
        a.label("kl_cs")
    imm32(3, t_col); E(ldrb_reg, 0, 3, 0)
    E(adds_imm8, 7, 2); E(lsls_imm, 7, 7, 8); E(orrs_reg, 0, 7)
    a.label("kl_w"); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    a.label("kl_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_l", "lo")
    if V3:                                                                            # (V3) page 1 of a MIDI track: the brightness = the amount from the point
        E(b, "kl_x")
        a.label("kl_p1")
        E(cmp_imm, 4, 2); bc("kl_x", "hs")
        E(mov_reg, 0, 4); E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); bc("kl_x", "ne")
        E(mov_reg, 0, 4); E(bl, L["c_sdbase"]); E(mov_reg, 7, 0)
        E(movs_imm, 6, 0)
        a.label("k1_l")
        E(lsls_imm, 0, 6, 1); E(ldrh_reg, 1, 5, 0); E(movw, 2, HEAD_LED); E(cmp_reg, 1, 2); E(b_cond, "k1_n", "eq")
        E(push_list, [1]); E(lsrs_imm, 0, 1, 8); E(subs_imm8, 0, 2); E(mov_reg, 1, 7); E(bl, "c_pvamt"); E(pop_list, [1])
        E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(movs_imm, 2, 0xFF); E(ands_reg, 1, 2); E(orrs_reg, 0, 1)
        E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
        a.label("k1_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "k1_l", "lo")
    a.label("kl_x"); E(raw, h(0xB002)); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- the pads of the two views (slot 0: view, pad, velocity): pad 32 with the step-drummer view on the screen = the toggle
    for v in ("t", "s"):
        a.label(f"c_pvp{v}")
        E(push_list, [0, 1, 2, 4], lr=True)
        E(cmp_imm, 1, PAD_PV); E(b_cond, f"p{v}_f", "ne")
        E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); E(b_cond, f"p{v}_f", "eq"); E(mov_reg, 4, 0)
        E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, f"p{v}_f", "ne")
        E(mov_reg, 0, 4); E(bl, "c_pvget"); E(movs_imm, 1, F_PV); E(eors_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_pvset")
        E(raw, h(0xB003)); E(pop_list, [4], pc=True)
        a.label(f"p{v}_f")
        E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["tpad" if v == "t" else "spad"])

    # ---- the LEDs of the two views (slot 7: view -> the pad LEDs): MIDI pad 30 dim / bright = off / on; the step-drummer view: pad 32 = the toggle,
    #      page 2: pads 17-24 = its destination
    a.label("c_pvlt")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["tled"]); E(mov_reg, 5, 0)
    E(ldrb_imm, 0, 4, 0x10); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(mov_reg, 4, 0)
    E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); E(b_cond, "lt_k", "ne")                 # out of the step-drummer view: pad 32 dark again (its LED is not redrawn here)
    E(bl, "c_pvblk"); E(cmp_imm, 0, 0); E(b_cond, "lt_k", "eq"); E(ldrb_imm, 1, 0, B_LED); E(cmp_imm, 1, 0); E(b_cond, "lt_k", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, B_LED); E(strh_imm, 1, 5, 2 * PAD_PV)
    a.label("lt_k")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("ls_x", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("ls_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_sdnib"]); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
    E(movs_imm, 1, V.COL_SD[1]); E(cmp_imm, 0, 0); E(b_cond, "lt_p", "eq"); E(movs_imm, 1, V.COL_SD[0])
    a.label("lt_p"); E(strh_imm, 1, 5, 2 * V.PAD_SD)
    E(b, "ls_c")
    a.label("c_pvls")
    E(push_list, [4, 5, 6], lr=True)
    E(bl, prev["sled"]); E(mov_reg, 5, 0)
    a.label("ls_c")
    E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); bc("ls_x", "eq"); E(mov_reg, 4, 0)
    E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("ls_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pvon"); E(movs_imm, 1, COL_PV[1]); E(cmp_imm, 0, 0); E(b_cond, "ls_q", "eq"); E(movs_imm, 1, COL_PV[0])
    a.label("ls_q"); E(strh_imm, 1, 5, 2 * PAD_PV)
    E(bl, "c_pvblk"); E(cmp_imm, 0, 0); E(b_cond, "ls_f", "eq"); E(movs_imm, 1, 1); E(strb_imm, 1, 0, B_LED)
    a.label("ls_f")
    E(movs_imm, 0, V.F_SDPAGE); E(bl, L["c_sdflag"]); E(cmp_imm, 0, 0); bc("ls_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); bc("ls_x", "ne")
    E(mov_reg, 0, 4); E(bl, "c_pvd2"); E(mov_reg, 6, 0)
    E(movs_imm, 4, 0)
    a.label("ls_d")
    imm32(3, t_col); E(ldrb_reg, 0, 3, 4)
    E(cmp_reg, 4, 6); E(b_cond, "ls_e", "eq")
    E(cmp_imm, 0, 0x32); E(b_cond, "ls_m", "ne"); E(movs_imm, 0, 0x36)                 # the dim magenta is 0x37
    a.label("ls_m"); E(adds_imm8, 0, 1)
    a.label("ls_e"); E(mov_reg, 1, 4); E(adds_imm8, 1, 16); E(lsls_imm, 1, 1, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "ls_d", "lo")
    a.label("ls_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pvdeg(r0 = a note, r1 = degrees, signed) -> r0 = the note that many degrees of the project's scale away (custom or stock), clamped 0..127
    a.label("c_pvdeg")
    E(raw, pushw([4, 5, 6, 7, 8, 9], lr=True))
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(0, KB); E(ldr_imm, 1, 0, 0x10); E(ldrb_imm, 6, 1, 0)                          # r6 = the root
    E(ldr_imm, 1, 0, 0xC); E(ldr_imm, 1, 1, 4); E(mov_reg, 8, 1)                        # r8 = the stock scale's mask (2 bits a degree, 0 = in it)
    E(bl, L["c_csget"]); E(mov_reg, 7, 0); E(mov_reg, 9, 1)                              # r7 = the custom scale's period (0 = off), r9 = its degrees
    a.label("dg_o")
    E(cmp_imm, 5, 0); bc("dg_x", "eq")
    E(movs_imm, 2, 1); E(cmp_imm, 5, 0); E(b_cond, "dg_i", "gt"); E(movs_imm, 2, 0); E(subs_imm8, 2, 1)
    a.label("dg_i")
    E(adds_reg, 4, 4, 2); E(cmp_imm, 4, 0); bc("dg_lo", "lt"); E(cmp_imm, 4, 127); bc("dg_hi", "gt")
    E(subs_reg, 0, 4, 6)                                                                 # r0 = the note above the root
    E(cmp_imm, 7, 0); E(b_cond, "dg_k", "eq")
    E(lsls_imm, 1, 7, 8); E(adds_reg, 0, 0, 1); E(subs_imm8, 0, 60); E(raw, udiv(1, 0, 7)); E(muls, 1, 7); E(subs_reg, 0, 0, 1)   # m = (r - 60) mod P
    E(cmp_imm, 0, 0); E(b_cond, "dg_in", "eq")
    E(mov_reg, 1, 9); E(lsrs_reg, 1, 0); E(lsls_imm, 1, 1, 31); E(b_cond, "dg_in", "mi"); E(b, "dg_i")
    a.label("dg_k")
    E(adds_imm8, 0, 120); E(movs_imm, 1, 12); E(raw, udiv(3, 0, 1)); E(muls, 3, 1); E(subs_reg, 0, 0, 3)
    E(lsls_imm, 0, 0, 1); E(mov_reg, 1, 8); E(lsrs_reg, 1, 0); E(movs_imm, 3, 3); E(ands_reg, 1, 3); E(b_cond, "dg_in", "eq"); E(b, "dg_i")
    a.label("dg_in"); E(subs_reg, 5, 5, 2); E(b, "dg_o")
    a.label("dg_lo"); E(movs_imm, 4, 0); E(b, "dg_x")
    a.label("dg_hi"); E(movs_imm, 4, 127)
    a.label("dg_x"); E(mov_reg, 0, 4); E(raw, popw([4, 5, 6, 7, 8, 9])); E(raw, h(0xBD00))

    # ---- c_pvk(r0 = track, r1 = step) -> r0 = the degrees its notes move: the toggle on, page 1's value - 64 at that step (none = 0); clobbers r1-r3
    a.label("c_pvk")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_pvon"); E(cmp_imm, 0, 0); E(b_cond, "pk_z", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_sden"]); E(cmp_imm, 0, 0); E(b_cond, "pk_z", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_sdpat"]); E(mov_reg, 1, 5); E(bl, L["c_sdlna"]); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, L["c_sdlofs"]); E(adds_reg, 0, 0, 6); E(ldrb_imm, 0, 0, 0)
    if V2:                                                                            # one degree every 8 units, rounded: MIDI from 64, a synth from 0
        E(cmp_imm, 0, 127); E(b_cond, "pk_z", "hi")
        E(cmp_imm, 4, 2); E(b_cond, "pk_s", "hs")
        if V3: E(push_list, [0]); E(mov_reg, 0, 4); E(bl, L["c_sdbase"]); E(mov_reg, 1, 0); E(pop_list, [0]); E(subs_reg, 0, 0, 1)   # (V3) from the point
        else: E(subs_imm8, 0, 64)
        a.label("pk_s")
        E(cmp_imm, 0, 0); E(b_cond, "pk_n", "lt")
        E(adds_imm8, 0, DEG_UNITS // 2); E(raw, V.asrs_imm(0, 0, 3)); E(pop_list, [4, 5, 6], pc=True)
        a.label("pk_n")
        E(raw, h(0x4240)); E(adds_imm8, 0, DEG_UNITS // 2); E(lsrs_imm, 0, 0, 3); E(raw, h(0x4240)); E(pop_list, [4, 5, 6], pc=True)   # negs r0, r0
    else:
        E(cmp_imm, 0, 127); E(b_cond, "pk_z", "hi"); E(subs_imm8, 0, 64); E(pop_list, [4, 5, 6], pc=True)
    a.label("pk_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_pvnote (the player's note load, after stepmod's c_rfnote): r0 = the player, r4 = the unit - 4, r7 = the unit -> r5 = the note, moved in the scale
    a.label("c_pvnote")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(bl, prev["note"])
    E(raw, pushw([4, 6, 7, 8, 9]))
    E(lsls_imm, 1, 7, 2); E(subs_reg, 1, 4, 1); E(mov_reg, 8, 1)                        # r8 = the step record
    E(ldr_sp, 0, 20); E(bl, L["c_artrk"]); E(cmp_imm, 0, 4); E(b_cond, "nt_x", "hs")
    E(adds_imm8, 0, 2); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(mov_reg, 4, 0)          # r4 = the step-drummer's track
    E(bl, "c_pvon"); E(cmp_imm, 0, 0); E(b_cond, "nt_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_sdpat"]); E(mov_reg, 1, 8); E(subs_reg, 1, 1, 0); E(movw, 2, 32 * 28); E(cmp_reg, 1, 2); E(b_cond, "nt_x", "hs")
    E(movs_imm, 2, 28); E(raw, udiv(1, 1, 2))
    E(mov_reg, 0, 4); E(bl, "c_pvk"); E(cmp_imm, 0, 0); E(b_cond, "nt_x", "eq")
    E(mov_reg, 1, 0); E(mov_reg, 0, 5); E(bl, "c_pvdeg"); E(mov_reg, 5, 0)
    a.label("nt_x"); E(raw, popw([4, 6, 7, 8, 9])); E(pop_list, [0, 1, 2, 3], pc=True)

    # ---- c_pvio (c_sdio's first 4 bytes: track, on / off, velocity, note): the audition of a step moved as it will play; its note-off the same note
    a.label("c_pvio")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 6, 3)
    E(bl, "c_pvblk"); E(cmp_imm, 0, 0); bc("io_g", "eq"); E(mov_reg, 5, 0)
    E(ldr_sp, 1, 4); E(cmp_imm, 1, 0); E(b_cond, "io_on", "ne")
    E(ldrb_imm, 0, 5, B_AUD); E(adds_imm3, 1, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "io_g", "ne")
    E(ldrb_imm, 6, 5, B_AUDN); E(movs_imm, 0, 0); E(strb_imm, 0, 5, B_AUD); E(b, "io_g")
    a.label("io_on")
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, B_AUD)
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "io_g", "eq"); E(ldrb_w, 0, 0, V.SD_AUD); E(cmp_imm, 0, 0); E(b_cond, "io_g", "eq")
    E(lsrs_imm, 1, 0, 6); E(cmp_reg, 1, 4); E(b_cond, "io_g", "ne")
    E(movs_imm, 1, 63); E(ands_reg, 1, 0); E(subs_imm8, 1, 1)
    E(mov_reg, 0, 4); E(bl, "c_pvk"); E(cmp_imm, 0, 0); E(b_cond, "io_g", "eq")
    E(mov_reg, 1, 0); E(mov_reg, 0, 6); E(bl, "c_pvdeg"); E(mov_reg, 6, 0)
    E(adds_imm3, 0, 4, 1); E(strb_imm, 0, 5, B_AUD); E(strb_imm, 6, 5, B_AUDN)
    a.label("io_g")
    E(str_sp, 6, 12)
    E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(raw, bytes.fromhex(HEADS["c_sdio"])); E(b_w, L["c_sdio"] + 4)

    # ---- c_pvap (c_vapply's first 4 bytes: track, lane, value) / c_pvrec (c_vcc_rec's: track, code, value): lane 1 (REL) belongs to page 2 while the step-drummer is on
    for nm, key, val in (("c_pvap", "c_vapply", 1), ("c_pvrec", "c_vcc_rec", V.LANE_TAB[1])):
        a.label(nm)
        E(cmp_imm, 1, val); E(b_cond, nm + "_g", "ne")
        E(push_list, [0, 1, 2], lr=True)
        E(bl, L["c_sden"]); E(cmp_imm, 0, 0); E(b_cond, nm + "_r", "eq")
        E(raw, h(0xB003)); E(raw, h(0xBD00))
        a.label(nm + "_r"); E(raw, popw([0, 1, 2], lr=True))
        a.label(nm + "_g"); E(raw, bytes.fromhex(HEADS[key])); E(b_w, L[key] + 4)

    if V2:
        # ---- c_pvbase (c_sdbase's first 4 bytes): a synth's empty pair starts from 0, a MIDI track's as before
        a.label("c_pvbase")
        E(cmp_imm, 0, 2); E(b_cond, "pb_m", "lo"); E(movs_imm, 0, 0); E(raw, RET)
        a.label("pb_m")
        if V3:                                                                        # (V3) MIDI: the FX sequencer 0, else the destination's point
            E(push_list, [4], lr=True); E(mov_reg, 4, 0)
            E(bl, L["c_fsq"]); E(cmp_imm, 0, 0); E(b_cond, "pb_z", "ne")
            E(mov_reg, 0, 4); E(bl, L["c_sdnib"]); E(lsrs_imm, 0, 0, 1); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(bl, "c_pvbip"); E(pop_list, [4], pc=True)
            a.label("pb_z"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)
            # ---- c_pvoff1(r0 = a MIDI track) -> r0 = the offset of page 1 at the step that counts: value - the point (none = 0); clobbers r1-r3
            a.label("c_pvoff1")
            E(push_list, [4, 5], lr=True)
            E(mov_reg, 4, 0); E(bl, L["c_sdpos"]); E(mov_reg, 5, 0)
            E(mov_reg, 0, 4); E(bl, L["c_sdpat"]); E(mov_reg, 1, 5); E(bl, L["c_sdlna"]); E(ldrb_imm, 0, 0, 0)
            E(cmp_imm, 0, 127); E(b_cond, "o1_z", "hi")
            E(push_list, [0]); E(mov_reg, 0, 4); E(bl, "c_pvbase"); E(mov_reg, 1, 0); E(pop_list, [0]); E(subs_reg, 0, 0, 1); E(pop_list, [4, 5], pc=True)
            a.label("o1_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)
        else: E(b_w, L["c_sdbase"] + 4)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the heads of eight of vcf21's routines, the player's note load, slots 0 / 7 of the MIDI template view and of the synth Preset view."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    vl = report["vcf20"]["labels"]
    L = {k: int(vl[k], 16) for k in ("c_sdscr", "c_sdflag", "c_sden", "c_sdnib", "c_sdpat", "c_sdlna", "c_sdlofs", "c_sdhalf", "c_sdconv", "c_sdpos",
                                       "c_sdoff", "c_vmark", "c_sdcur", "c_vvaddr", "c_von", "c_edact", "c_fsq", "c_sdbase", *HEADS)}
    L.update(c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16), c_csget=int(report["cscale"]["labels"]["c_csget"], 16),
             c_artrk=int(report["arp"]["labels"]["c_artrk"], 16))
    from fxdiag import bl_target
    prev = dict(tpad=u(TMPL_VT) & ~1, tled=u(TMPL_VT + 28) & ~1, spad=u(SYN_VT) & ~1, sled=u(SYN_VT + 28) & ~1,
                note=bl_target(img, MU.NOTE_LOAD, BASE))
    assert prev["note"] == int(report["stepmod"]["labels"]["c_rfnote"], 16), hex(prev["note"])
    for k, hx in HEADS.items():
        assert bytes(img[L[k] - BASE:L[k] - BASE + 4]).hex() == hx, k
    assert bytes(img[L["c_sdmark"] + 4 - BASE:L["c_sdmark"] + 6 - BASE]).hex() == "7047"
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    from thumb import b_w as bw_enc
    for k, ours in (("c_sdknob", "c_pvknob"), ("c_sdpad", "c_pvpad"), ("c_sdfx", "c_pvfx"), ("c_sdmark", "c_pvmk"), ("c_sdkleds", "c_pvkl"),
                    ("c_sdio", "c_pvio"), ("c_vapply", "c_pvap"), ("c_vcc_rec", "c_pvrec")):
        img[L[k] - BASE:L[k] - BASE + 4] = bw_enc(L[k], labels[ours])
    img[MU.NOTE_LOAD - BASE:MU.NOTE_LOAD - BASE + 4] = bl(MU.NOTE_LOAD, labels["c_pvnote"])
    if V2:
        a_ = L["c_sdbase"]; assert bytes(img[a_ - BASE:a_ - BASE + 2]).hex() == "0228" and img[a_ - BASE + 3] == 0xD2, "c_sdbase"
        img[a_ - BASE:a_ - BASE + 4] = bw_enc(a_, labels["c_pvbase"])
    struct.pack_into("<I", img, TMPL_VT - BASE, labels["c_pvpt"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 28 - BASE, labels["c_pvlt"] | 1)
    struct.pack_into("<I", img, SYN_VT - BASE, labels["c_pvps"] | 1)
    struct.pack_into("<I", img, SYN_VT + 28 - BASE, labels["c_pvls"] | 1)
    return labels, code, prev
