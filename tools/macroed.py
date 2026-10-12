"""SC39.3 (the user, 2026-10-12: «destinos de macro knob ajustables mediante interfaz (se escriben en el parche usando los nrpn de stock)» … «hazlo como
se haría en Components o a través de controlador externo»): an on-device editor of the synth macros' destinations.

A macro (8 per synth patch) has four slots A-D; each slot = destination (0..69), start position, end position (the stretch of the knob's travel where
the slot acts, 0 / 127 by default) and depth (-64..63, stored 0..127).  Programmer's Reference Guide: macro k position CC 79 + k, slot r of macro k at
NRPN 3:(16 (k - 1) + 4 r) = destination, + 1 start, + 2 end, + 3 depth.  In the firmware those are the parameters 174 + 17 (k - 1) (position) and
175 + 17 (k - 1) + 4 r ... of the session's type 0 / 1 (the patch of Synth 1 / 2): read with 0x08036192(type, index), written with the listener the
MIDI input uses, 0x08034D92(this + 4, type, index, value), so an edit here is exactly a received NRPN (the patch in RAM, the macro offsets, the DSP).
The 70 destinations are the firmware's table at 0x0805A2B0 (docs/NOTAS.md, «destinos de los macro knobs»).

Use (the source view of a synth: Synth 1 / 2 pressed again with its view on the screen):
  * pad 32 = the editor on / off (teal: bright on, dim off);
  * the editor on: turning a knob picks its macro (the knob LED white, the others dim teal); the pads then show the value of the field as a number;
    turning that knob changes it; Octave down / up = the next / previous field: slot (1-4, yellow) -> start (green) -> end (orange) -> destination ->
    depth; any pad = back to the pads of the source view (the macro dropped, the editor still on);
  * destination: shown as the parameter's CC number (white) or the LSB of its NRPN (light blue 0:x, magenta 1:x, violet 2:x); the knob walks the 31
    destinations that have a CC by ascending CC number, then the 39 NRPN ones in the order of the destinations (the user: «primero los CC en orden
    parámetro destino ascendente y luego los nrpn en orden destino ascendente»);
  * depth: the amount without its sign, teal when positive, red when negative, dim white at 0;
  * any other button closes the source view as always, and the editor with it.
State (no new RAM): 4 bytes of the Master FX block's idle LED buffer (c_gst() + 120: after the 16 bytes of the patch caches; the CC editor's scratch of
the MIDI views, never on the screen at the same time): a tag, the flags (on, macro picked, synth, macro), the field and the slot, the knob events counted towards the next step.
The edits live in the patch of the project (the session); saving the patch to the pack's bank is not done on the device.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, h, strb_imm, strh_imm, strh_reg,
                   subs_imm8, subs_reg, tst_reg)
import packio as PK  # noqa: E402
import srcview as SV  # noqa: E402
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402

SP_VT = 0x0805AC9C                    # the Preset view of the synths (the source view is this view with F_SRC): slot 0 pads, slot 7 LEDs
AC64_VT = 0x0805AC64                  # the macro handlers of the four note tracks: slot 4 knob, slot 7 knob LEDs
BTN_ENTRY, MGR, CTX = MP.BTN_ENTRY, MP.MGR, 0x200069E4
GETTER, PARAM_SET = 0x08036192, 0x08034D92
ST_OFF, MAGIC = PK.PM_CACHE + 16, 0xE7
F_ON, F_SEL = 0x80, 0x40
PAD_ED = 31                           # pad 32
COL_ED = (0x4D, 0x4E)                 # teal bright / dim
COL_SLOT, COL_START, COL_END = 0x2D, 0x17, 0x2B      # yellow, green, orange
COL_POS, COL_NEG, COL_ZERO = 0x4D, 0x53, 0x02        # depth: teal, red, dim white
COL_BANK = {"CC": 0x01, 0: 0x13, 1: 0x32, 2: 0x49}  # destination: CC white, NRPN 0:x light blue, 1:x magenta, 2:x violet
KNOB_SEL, KNOB_IDLE = 0x01 | (127 + 2) << 8, 0x4D | (24 + 2) << 8
STEP_SLOT, STEP_DEST = 16, 2          # knob events per step of the slot / of the destination (a turn sends many events of +-1: SC36.1 on the device)
NFIELD = 5                            # slot, start, end, destination, depth
FIELD_OFS = (None, 1, 2, 0, 3)        # the field's parameter inside the slot (destination, start, end, depth)
# the 70 destinations: (name, "CC" or the NRPN's MSB, number)
DEST = ([("Portamento rate", "CC", 5), ("Post FX level", "CC", 59)]
        + [(f"Osc 1 {n}", "CC", c) for n, c in zip(("wave interpolate", "pulse width index", "virtual sync depth", "density", "density detune", "semitones", "cents"), (20, 21, 22, 24, 25, 26, 27))]
        + [(f"Osc 2 {n}", "CC", c) for n, c in zip(("wave interpolate", "pulse width index", "virtual sync depth", "density", "density detune", "semitones", "cents"), (30, 31, 33, 35, 36, 37, 39))]
        + [("Osc 1 level", "CC", 51), ("Osc 2 level", "CC", 52), ("Ring mod level", "CC", 54), ("Noise level", "CC", 56)]
        + [("Filter frequency", "CC", 74), ("Filter resonance", "CC", 71), ("Filter drive", "CC", 63), ("Filter tracking", "CC", 69), ("Env 2 to filter frequency", "CC", 79)]
        + [("Env 1 attack", "CC", 73), ("Env 1 decay", "CC", 75), ("Env 1 sustain", "CC", 70), ("Env 1 release", "CC", 72)]
        + [(f"Env 2 {n}", 0, c) for n, c in zip(("attack", "decay", "sustain", "release"), (1, 2, 3, 4))]
        + [(f"Env 3 {n}", 0, c) for n, c in zip(("delay", "attack", "decay", "sustain", "release"), (14, 15, 16, 17, 18))]
        + [("LFO 1 rate", 0, 76), ("LFO 1 rate sync", 0, 77), ("LFO 1 slew rate", 0, 72), ("LFO 2 rate", 0, 85), ("LFO 2 rate sync", 0, 86), ("LFO 2 slew rate", 0, 81)]
        + [("Distortion level", "CC", 91), ("Chorus level", "CC", 93)]
        + [("Chorus rate", 1, 25), ("Chorus feedback", 1, 27), ("Chorus mod depth", 1, 28), ("Chorus delay", 1, 29)]
        + [(f"Mod matrix {k + 1} depth", (83 + 3 + 5 * k) // 128 + 1, (83 + 3 + 5 * k) % 128) for k in range(20)])
assert len(DEST) == 70
ORDER = sorted((d for d in range(70) if DEST[d][1] == "CC"), key=lambda d: DEST[d][2]) + [d for d in range(70) if DEST[d][1] != "CC"]
INV = [ORDER.index(d) for d in range(70)]
INV8 = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_c{zc[0]}"
        E(b_cond, n, INV8[cond]); E(b, target); a.label(n)
    # ---- data first (known addresses): the walk order, its inverse, the number and the colour shown for each destination
    t_order, t_inv, t_num, t_col = base, base + 70, base + 140, base + 210
    E(raw, bytes(ORDER) + bytes(INV) + bytes(d[2] for d in DEST) + bytes(COL_BANK[d[1]] for d in DEST))

    # ---- c_mcst() -> r0 = the state (tag written when the bytes were someone else's: off), 0 without the block; clobbers r1-r3
    a.label("c_mcst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "cs_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "cs_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 2); E(strb_imm, 1, 0, 3)
    a.label("cs_x"); E(pop_list, [4], pc=True)

    # ---- c_mcacc(r0 = events per step; r7 = the state, r6 = the delta) -> r0 = +1 / -1 when the turn adds up to a step, else 0; clobbers r1
    a.label("c_mcacc")
    E(ldrb_imm, 1, 7, 3); E(raw, h(0xB249)); E(adds_reg, 1, 1, 6)                     # (sxtb r1, r1)
    E(cmp_reg, 1, 0); E(b_cond, "ca_up", "ge"); E(raw, h(0x42C1)); E(b_cond, "ca_dn", "le")    # (cmn r1, r0)
    E(strb_imm, 1, 7, 3); E(movs_imm, 0, 0); E(raw, h(0x4770))
    a.label("ca_up"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3); E(movs_imm, 0, 1); E(raw, h(0x4770))
    a.label("ca_dn"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 3); E(subs_imm8, 0, 1); E(raw, h(0x4770))

    # ---- c_mcsrc() -> r0 = the synth (0 / 1) whose source view is on the screen, or 0xFF; clobbers r1-r3
    a.label("c_mcsrc")
    E(push_list, [4], lr=True)
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "cr_n", "ne")
    E(ldrb_w, 2, 0, V.S_CUR)
    E(movs_imm, 4, 0); E(cmp_imm, 2, 0); E(b_cond, "cr_t", "eq")
    E(movs_imm, 4, 1); E(cmp_imm, 2, 9); E(b_cond, "cr_n", "ne")
    a.label("cr_t")
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "cr_n", "eq")
    E(ldrb_imm, 0, 0, 20); E(movs_imm, 1, SV.F_SRC); E(tst_reg, 0, 1); E(b_cond, "cr_n", "eq")
    E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); E(b_cond, "cr_n", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("cr_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_mcon() -> r0 = the state when the editor is on for the source view on the screen (r1 = its synth), else 0; clobbers r2, r3
    a.label("c_mcon")
    E(push_list, [4, 5], lr=True)
    E(bl, "c_mcsrc"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); E(b_cond, "co_z", "eq")
    E(bl, "c_mcst"); E(mov_reg, 5, 0); E(cmp_imm, 5, 0); E(b_cond, "co_z", "eq")
    E(ldrb_imm, 1, 5, 1); E(movs_imm, 2, F_ON); E(tst_reg, 1, 2); E(b_cond, "co_z", "eq")
    E(lsrs_imm, 1, 1, 3); E(movs_imm, 2, 1); E(ands_reg, 1, 2); E(cmp_reg, 1, 4); E(b_cond, "co_z", "ne")
    E(mov_reg, 0, 5); E(mov_reg, 1, 4); E(pop_list, [4, 5], pc=True)
    a.label("co_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_mcidx(r0 = the state) -> r0 = the parameter of the slot's destination: 175 + 17 macro + 4 slot; clobbers r1-r3
    a.label("c_mcidx")
    E(ldrb_imm, 1, 0, 1); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(movs_imm, 2, 17); E(muls, 1, 2)
    E(ldrb_imm, 2, 0, 2); E(lsrs_imm, 2, 2, 4); E(movs_imm, 3, 3); E(ands_reg, 2, 3); E(lsls_imm, 2, 2, 2)
    E(adds_reg, 0, 1, 2); E(adds_imm8, 0, 175); E(raw, h(0x4770))

    # ---- c_mcfidx(r0 = the state) -> r0 = the parameter of the field shown (fields 1..4); clobbers r1-r3
    a.label("c_mcfidx")
    E(push_list, [4], lr=True)
    E(ldrb_imm, 4, 0, 2); E(movs_imm, 1, 7); E(ands_reg, 4, 1)
    E(bl, "c_mcidx")
    for f in (1, 2, 4):
        E(cmp_imm, 4, f); E(b_cond, f"cf_n{f}", "ne"); E(adds_imm8, 0, FIELD_OFS[f]); a.label(f"cf_n{f}")
    E(pop_list, [4], pc=True)

    # ---- c_mcset(r0 = synth, r1 = parameter, r2 = value): as a received NRPN
    a.label("c_mcset")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(mov_reg, 1, 4); E(mov_reg, 2, 5); E(mov_reg, 3, 6); E(bl, PARAM_SET)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_mcknob (the macro handlers' slot 4: handler, knob, delta): the editor on = the knob picks its macro, then changes the field
    a.label("c_mcknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_mcon"); E(mov_reg, 7, 0); E(mov_reg, 4, 1); E(cmp_imm, 7, 0); bc("ck_f", "eq")
    E(cmp_imm, 5, 8); bc("ck_f", "hs")
    E(ldrb_imm, 0, 7, 1); E(movs_imm, 1, F_SEL); E(tst_reg, 0, 1); E(b_cond, "ck_pick", "eq")
    E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(cmp_reg, 0, 5); E(b_cond, "ck_ed", "eq")
    a.label("ck_pick")                                                                # another knob: its macro, slot A, the first field
    E(lsls_imm, 0, 4, 3); E(orrs_reg, 0, 5); E(movs_imm, 1, F_ON | F_SEL); E(orrs_reg, 0, 1); E(strb_imm, 0, 7, 1)
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 2); E(strb_imm, 0, 7, 3); E(b, "ck_e")
    a.label("ck_ed")
    E(cmp_imm, 6, 0); bc("ck_e", "eq")
    E(ldrb_imm, 0, 7, 2); E(movs_imm, 1, 7); E(ands_reg, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "ck_val", "ne")
    E(movs_imm, 0, STEP_SLOT); E(bl, "c_mcacc"); E(cmp_imm, 0, 0); E(b_cond, "ck_e", "eq"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 7, 2); E(lsrs_imm, 2, 0, 4)                                        # the slot 0..3, a step every STEP_SLOT events, no wrap
    E(cmp_imm, 6, 0); E(b_cond, "ck_sd", "lt")
    E(cmp_imm, 2, 3); E(b_cond, "ck_e", "hs"); E(adds_imm8, 2, 1); E(b, "ck_sw")
    a.label("ck_sd"); E(cmp_imm, 2, 0); E(b_cond, "ck_e", "eq"); E(subs_imm8, 2, 1)
    a.label("ck_sw"); E(lsls_imm, 2, 2, 4); E(strb_imm, 2, 7, 2); E(b, "ck_e")       # (the field stays 0)
    a.label("ck_val")
    E(mov_reg, 0, 7); E(bl, "c_mcfidx"); E(mov_reg, 5, 0)                            # r5 = the parameter
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1)
    E(push_list, [0])                                                                 # the value now
    E(ldrb_imm, 1, 7, 2); E(movs_imm, 2, 7); E(ands_reg, 1, 2); E(cmp_imm, 1, 3); E(b_cond, "ck_lin", "ne")
    E(movs_imm, 0, STEP_DEST); E(bl, "c_mcacc"); E(mov_reg, 6, 0); E(raw, h(0x9800))  # the destination: a place of the walk every STEP_DEST events (ldr r0, [sp])
    E(cmp_imm, 6, 0); E(b_cond, "ck_wr", "eq")
    E(cmp_imm, 0, 70); E(b_cond, "ck_dk", "lo"); E(movs_imm, 0, 0)
    a.label("ck_dk"); imm32(1, t_inv); E(ldrb_reg, 0, 1, 0)
    E(cmp_imm, 6, 0); E(b_cond, "ck_dd", "lt")
    E(cmp_imm, 0, 69); E(b_cond, "ck_dw", "hs"); E(adds_imm8, 0, 1); E(b, "ck_dw")
    a.label("ck_dd"); E(cmp_imm, 0, 0); E(b_cond, "ck_dw", "eq"); E(subs_imm8, 0, 1)
    a.label("ck_dw"); imm32(1, t_order); E(ldrb_reg, 0, 1, 0); E(b, "ck_wr")
    a.label("ck_lin")
    E(adds_reg, 0, 0, 6); E(cmp_imm, 0, 0); E(b_cond, "ck_l1", "ge"); E(movs_imm, 0, 0)
    a.label("ck_l1"); E(cmp_imm, 0, 127); E(b_cond, "ck_wr", "le"); E(movs_imm, 0, 127)
    a.label("ck_wr")
    E(pop_list, [1]); E(cmp_reg, 0, 1); E(b_cond, "ck_e", "eq")
    E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_mcset")
    a.label("ck_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("ck_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_mcpad (the synth Preset view's slot 0: view, pad, velocity), in the source view: pad 32 = the editor; a macro picked: any pad drops it
    a.label("c_mcpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_mcsrc"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); E(b_cond, "cp_f", "eq")
    E(bl, "c_mcst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "cp_f", "eq")
    E(ldrb_imm, 6, 7, 1)
    E(movs_imm, 0, F_ON); E(tst_reg, 6, 0); E(b_cond, "cp_off", "eq")
    E(lsrs_imm, 0, 6, 3); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "cp_off", "ne")
    E(movs_imm, 0, F_SEL); E(tst_reg, 6, 0); E(b_cond, "cp_on", "eq")
    E(bics_reg, 6, 0); E(strb_imm, 6, 7, 1); E(b, "cp_e")                             # a macro was shown: back to the pads
    a.label("cp_on")
    E(cmp_imm, 5, PAD_ED); E(b_cond, "cp_f", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1); E(b, "cp_e")                             # the editor off
    a.label("cp_off")
    E(cmp_imm, 5, PAD_ED); E(b_cond, "cp_f", "ne")
    E(lsls_imm, 0, 4, 3); E(movs_imm, 1, F_ON); E(orrs_reg, 0, 1); E(strb_imm, 0, 7, 1); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 2)
    a.label("cp_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("cp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_mcleds (that view's slot 7): pad 32; a macro picked: the pads show the field's value
    a.label("c_mcleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_mcsrc"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); bc("cl_x", "eq")
    E(bl, "c_mcst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("cl_x", "eq")
    E(ldrb_imm, 6, 7, 1)
    E(movs_imm, 2, COL_ED[1])
    E(movs_imm, 0, F_ON); E(tst_reg, 6, 0); E(b_cond, "cl_p", "eq")
    E(lsrs_imm, 0, 6, 3); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "cl_p", "ne")
    E(movs_imm, 2, COL_ED[0])
    E(movs_imm, 0, F_SEL); E(tst_reg, 6, 0); E(b_cond, "cl_num", "ne")
    a.label("cl_p"); E(strh_imm, 2, 5, 2 * PAD_ED); E(b, "cl_x")
    a.label("cl_num")
    E(ldrb_imm, 0, 7, 2); E(movs_imm, 1, 7); E(ands_reg, 1, 0); E(mov_reg, 6, 1)     # r6 = the field
    E(cmp_imm, 6, 0); E(b_cond, "cl_v", "ne")
    E(lsrs_imm, 1, 0, 4); E(adds_imm8, 1, 1); E(movs_imm, 2, COL_SLOT); E(b, "cl_d")
    a.label("cl_v")
    E(mov_reg, 0, 7); E(bl, "c_mcfidx"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, GETTER); E(movs_imm, 1, 0xFF); E(ands_reg, 1, 0)   # r1 = the value
    E(movs_imm, 2, COL_START); E(cmp_imm, 6, 1); E(b_cond, "cl_d", "eq")
    E(movs_imm, 2, COL_END); E(cmp_imm, 6, 2); E(b_cond, "cl_d", "eq")
    E(cmp_imm, 6, 3); E(b_cond, "cl_dep", "ne")
    E(cmp_imm, 1, 70); E(b_cond, "cl_dk", "lo"); E(movs_imm, 1, 0)
    a.label("cl_dk"); imm32(0, t_col); E(ldrb_reg, 2, 0, 1); imm32(0, t_num); E(ldrb_reg, 1, 0, 1); E(b, "cl_d")
    a.label("cl_dep")
    E(movs_imm, 2, COL_ZERO); E(cmp_imm, 1, 64); E(b_cond, "cl_dz", "eq"); E(b_cond, "cl_dn", "lo")
    E(subs_imm8, 1, 64); E(movs_imm, 2, COL_POS); E(b, "cl_d")
    a.label("cl_dn"); E(movs_imm, 0, 64); E(subs_reg, 1, 0, 1); E(movs_imm, 2, COL_NEG); E(b, "cl_d")
    a.label("cl_dz"); E(movs_imm, 1, 0)
    a.label("cl_d"); E(mov_reg, 0, 5); E(bl, L["c_ednum"])
    a.label("cl_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_mckleds (the macro handlers' slot 7): the editor on = the knobs dim teal, the picked macro's white
    a.label("c_mckleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(bl, "c_mcon"); E(mov_reg, 7, 0); E(mov_reg, 6, 1); E(cmp_imm, 7, 0); E(b_cond, "cq_x", "eq")
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "cq_x", "eq")       # the handler of that synth only
    E(ldr_imm, 0, 0, 0x40); E(cmp_imm, 0, 0); E(b_cond, "cq_x", "eq"); E(ldr_imm, 0, 0, 0x2C); E(cmp_imm, 0, 0); E(b_cond, "cq_x", "eq")
    E(lsls_imm, 1, 6, 2); E(adds_reg, 0, 0, 1); E(raw, h(0xF8D0) + h(0 << 12 | 0x148)); E(cmp_reg, 0, 4); E(b_cond, "cq_x", "ne")   # ldr.w r0, [r0, #0x148]
    E(ldrb_imm, 6, 7, 1)
    E(movs_imm, 3, 0)
    a.label("cq_l")
    E(movw, 2, KNOB_IDLE)
    E(movs_imm, 0, F_SEL); E(tst_reg, 6, 0); E(b_cond, "cq_w", "eq")
    E(movs_imm, 0, 7); E(ands_reg, 0, 6); E(cmp_reg, 0, 3); E(b_cond, "cq_w", "ne")
    E(movw, 2, KNOB_SEL)
    a.label("cq_w"); E(lsls_imm, 0, 3, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "cq_l", "lo")
    a.label("cq_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_mcbtn (the controller's button press: ctrl, id): a macro picked = Octave down / up step the fields; another button ends the editor
    a.label("c_mcbtn")
    E(cmp_imm, 1, SV.ID_SHIFT); E(b_cond, "cb_f", "eq")
    E(push_list, [0, 1, 4, 5, 6, 7], lr=True); E(raw, h(0xB081))                    # (+ sub sp, #4: 8 words)
    E(mov_reg, 4, 1)
    E(cmp_imm, 4, MP.ID_DOWN); E(b_cond, "cb_o", "eq"); E(cmp_imm, 4, MP.ID_UP); E(b_cond, "cb_o", "eq")
    E(bl, "c_mcst"); E(cmp_imm, 0, 0); E(b_cond, "cb_fp", "eq")                       # any other button: the editor off
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1); E(b, "cb_fp")
    a.label("cb_o")
    E(bl, "c_mcon"); E(mov_reg, 5, 0); E(cmp_imm, 5, 0); E(b_cond, "cb_fp", "eq")
    E(ldrb_imm, 0, 5, 1); E(movs_imm, 1, F_SEL); E(tst_reg, 0, 1); E(b_cond, "cb_fp", "eq")
    E(ldrb_imm, 0, 5, 2); E(movs_imm, 1, 7); E(ands_reg, 1, 0)                        # r1 = the field
    E(cmp_imm, 4, MP.ID_DOWN); E(b_cond, "cb_up", "ne")
    E(cmp_imm, 1, NFIELD - 1); E(b_cond, "cb_e", "hs"); E(adds_imm8, 0, 1); E(b, "cb_w")
    a.label("cb_up"); E(cmp_imm, 1, 0); E(b_cond, "cb_e", "eq"); E(subs_imm8, 0, 1)
    a.label("cb_w"); E(strb_imm, 0, 5, 2); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 3)
    a.label("cb_e"); E(raw, h(0xB001)); E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
    a.label("cb_fp"); E(raw, h(0xB001)); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True))
    a.label("cb_f"); E(b_w, prev["btn"])

    # ---- c_mcledtask (the LED task calls: ctrl, frame): the chain, then Octave down / up lit while there is a next / previous field
    a.label("c_mcledtask")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_mcon"); E(cmp_imm, 0, 0); E(b_cond, "ct_x", "eq")
    E(ldrb_imm, 1, 0, 1); E(movs_imm, 2, F_SEL); E(tst_reg, 1, 2); E(b_cond, "ct_x", "eq")
    E(ldrb_imm, 4, 0, 2); E(movs_imm, 1, 7); E(ands_reg, 4, 1)
    E(movs_imm, 2, 0); E(cmp_imm, 4, 0); E(b_cond, "ct_u", "eq"); E(movs_imm, 2, MP.COL_BTN)
    a.label("ct_u"); E(movs_imm, 0, 2 * MP.LED_UP); E(strh_reg, 2, 5, 0)
    E(movs_imm, 2, 0); E(cmp_imm, 4, NFIELD - 1); E(b_cond, "ct_d", "hs"); E(movs_imm, 2, MP.COL_BTN)
    a.label("ct_d"); E(movs_imm, 0, 2 * MP.LED_DOWN); E(strh_reg, 2, 5, 0)
    a.label("ct_x"); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the synth Preset view's slots 0 / 7, the macro handlers' slots 4 / 7, the head of the button chain, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_sdscr=lab("vcf20", "c_sdscr"), c_ednum=lab("vcf20", "c_ednum"))
    prev = dict(pad=u(SP_VT) & ~1, leds=u(SP_VT + 28) & ~1, knob=u(AC64_VT + 16) & ~1, kleds=u(AC64_VT + 28) & ~1,
                btn=MP.bw_target(img, BTN_ENTRY, BASE), ledtask=lab("mpatch", "c_mpledtask"))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SP_VT - BASE, labels["c_mcpad"] | 1)
    struct.pack_into("<I", img, SP_VT + 28 - BASE, labels["c_mcleds"] | 1)
    struct.pack_into("<I", img, AC64_VT + 16 - BASE, labels["c_mcknob"] | 1)
    struct.pack_into("<I", img, AC64_VT + 28 - BASE, labels["c_mckleds"] | 1)
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_mcbtn"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_mcledtask"])
    return labels, code, prev
