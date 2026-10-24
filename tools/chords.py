"""SC46.3 / Beta 3.20 (a request from a user, brought by the user; decisions of the user, 2026-10-24: «tu propuesta es correcta. la vista de acordes
sería solo en Note Expand, por falta de espacio. Desde note Expand, shift+pad8 activa/desactiva acordes» · «se pierden al apagar. La interpretación
grabada con estas herramientas queda almacenada en el pattern para poder reproducirla con normalidad»): the chord screen of the note tracks.

In the expanded Note view ([ctrl + 0x152] = 9 t + 6) of Synth 1 / 2 and MIDI 1 / 2 (not the sample picker of MIDI 1 / 2, not the split keyboard),
Shift + pad 8 = the chord screen on / off for that track (the stock's Shift + pad only plays the note).  On:
  * row 1 = the chord type: major, minor, 7, m7, maj7, sus4, dim, aug; Shift + pads 1-7 = sus2, 6, m6, add9, 9, 7sus4, fifth (pad 8 with Shift
    is the on / off; with Shift the row yellow, the type chosen white);
  * row 2 = pads 9-12 the inversion (root, 1st, 2nd, 3rd: orange; the same again = root), pad 13 open voicing (the second note an octave up),
    pad 14 the root an octave down added, pad 15 diatonic (the chord stacks thirds of the project's scale, the custom one or Jankó too: 3 notes,
    4 when the type has 4 or more), pad 16 latch (the chord keeps sounding until the next root, latch off or the screen off): green on, dim off;
  * rows 3-4 = the roots: the same notes as the Note view's keyboard (its scale, root, octave, Jankó); a root plays its chord while it is held
    (each note through the track view's live note-on 0x0804B07A with the pad's velocity: it sounds, it is recorded with Record and the arpeggiator
    takes it; the note-offs one by one through 0x0804AF5A), up to 6 notes; the stock lights the notes that sound.
Nothing saved (RAM only, lost at power-off): what is played and recorded is plain notes of the pattern.
RAM: modmx.MXR + 0x520 (160 B with a signature).  In the hole (no card, no settings).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm, strh_reg,
                   subs_imm8, subs_reg)
import modmx as MX  # noqa: E402

MGR, S_CUR = 0x20040B10, 0x152
CONT_VT = 0x0805A62C                                     # the track views' container: slot 0 pad (obj, pad, vel), 1 release (obj, pad), 7 the LEDs
VIEW0, VIEW_SZ = 0x200412E0, 0x2F4
PAD_IDX, KEY_SKIP = 0x0804B174, 0x080523E8               # (view, pad) -> the keyboard's index; (kbd, index) != 0 = no key there
NOTE_ON, NOTE_OFF = 0x0804B07A, 0x0804AF5A               # (view, note, vel, pad) / (view, pad: its note = [view + 0x40 + pad])
KB, QUANT = 0x20041044, 0x080408C6
CR = MX.MXR + 0x520                                      # + 0 "CHD1", + 4 flags[4], + 8 type[4], + 12 inversion[4], + 16 the pads swallowed,
RSIG = 0x31444843                                        # + 20 the latched slot + 1, + 24 the build (8), + 32 held[16] (6 notes, count, track + 1)
O_FL, O_TY, O_INV, O_SW, O_LAT, O_BUF, O_HELD, RSZ = 4, 8, 12, 16, 20, 24, 32, 160
F_ON, F_OPEN, F_BASS, F_DIA, F_LATCH = 1, 2, 4, 8, 16
PAD_TOG = 7
TYPES = ((0, 4, 7), (0, 3, 7), (0, 4, 7, 10), (0, 3, 7, 10), (0, 4, 7, 11), (0, 5, 7), (0, 3, 6), (0, 4, 8),
         (0, 2, 7), (0, 4, 7, 9), (0, 3, 7, 9), (0, 4, 7, 14), (0, 4, 7, 10, 14), (0, 5, 7, 10), (0, 7, 12))
COL_DIM, COL_SEL, COL_SHIFT, COL_INV, COL_ON = 0x02, 0x01, 0x2D, 0x09, 0x17
VMAX = 139
INV = {"eq": "ne", "ne": "eq", "hs": "lo", "lo": "hs", "hi": "ls", "ls": "hi", "ge": "lt", "lt": "ge", "gt": "le", "le": "gt"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def type_table():
    out = b""
    for t in TYPES: out += bytes(t) + bytes([0xFF] * (6 - len(t)))
    return out


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    zc = [0]
    def bc(target, cond):                                # a conditional branch of any length
        zc[0] += 1; n = f"_h{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    E(raw, type_table())
    t_types = base
    a.label("c_chram")                                                                 # -> r0 = our RAM (cleared the first time); clobbers r1, r2
    imm32(0, CR); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "cr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 2, 4)
    a.label("cr_l"); E(raw, h(0x5081)); E(adds_imm8, 2, 4); E(cmp_imm, 2, RSZ); E(b_cond, "cr_l", "lo")   # str r1, [r0, r2]
    a.label("cr_x"); E(raw, RET)

    # ---- c_chtrk() -> r0 = the note track 0..3 whose expanded Note view is on the screen (not the sample picker / the split), or 0xFF
    a.label("c_chtrk")
    E(push_list, [4], lr=True)
    imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 4, 0)
    a.label("ct_l"); E(movs_imm, 0, 9); E(muls, 0, 4); E(adds_imm8, 0, 6); E(cmp_reg, 1, 0); E(b_cond, "ct_y", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "ct_l", "lo"); E(b, "ct_n")
    a.label("ct_y")
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); E(b_cond, "ct_n", "ne")
    E(bl, L["c_s4on"]); E(cmp_imm, 0, 0); E(b_cond, "ct_n", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("ct_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_chview(r0 = track) -> r0 = its view; clobbers r1
    a.label("c_chview")
    imm32(1, VIEW_SZ); E(muls, 0, 1); imm32(1, VIEW0); E(adds_reg, 0, 0, 1); E(raw, RET)

    # ---- c_chins(r0 = a value 0..15 of 1..139): the in-scale test -> r0 = 1 when the quantiser leaves it; clobbers r1-r3
    a.label("c_chins")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(mov_reg, 1, 0); imm32(0, KB); E(ldr_imm, 0, 0, 0xC); E(bl, QUANT)
    E(cmp_reg, 0, 4); E(b_cond, "ci_0", "ne"); E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ci_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_chbuild(r0 = track, r1 = the root) -> r0 = how many notes, in our RAM + O_BUF
    #      r4 = RAM, r5 = the root, r6 = the track, r7 = n
    a.label("c_chbuild")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 5, 1); E(bl, "c_chram"); E(mov_reg, 4, 0)
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_TY); E(movs_imm, 1, 6); E(muls, 0, 1); imm32(1, t_types); E(adds_reg, 1, 1, 0)   # r1 = its intervals
    E(movs_imm, 7, 0)
    a.label("cb_n"); E(ldrb_reg, 0, 1, 7); E(cmp_imm, 0, 0xFF); E(b_cond, "cb_ne", "eq")
    E(adds_reg, 0, 0, 5); E(adds_reg, 2, 4, 7); E(strb_imm, 0, 2, O_BUF); E(adds_imm8, 7, 1); E(cmp_imm, 7, 6); E(b_cond, "cb_n", "lo")
    a.label("cb_ne")
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_FL); E(movs_imm, 1, F_DIA); E(raw, h(0x4208)); E(b_cond, "cb_od", "eq")   # tst r0, r1
    # diatonic: the root, then the 2nd, 4th, (6th) note of the scale above it; 3 notes, 4 when the type has 4 or more
    E(cmp_imm, 7, 4); E(b_cond, "cb_d4", "lo"); E(movs_imm, 7, 4); E(b, "cb_dg")
    a.label("cb_d4"); E(movs_imm, 7, 3)
    a.label("cb_dg")
    E(strb_imm, 5, 4, O_BUF); E(push_list, [7]); E(movs_imm, 7, 1)                     # r7 = the next note wanted (1..n - 1); [sp] = n
    E(movs_imm, 2, 0)                                                                  # r2 = the scale notes passed
    E(mov_reg, 0, 5)
    a.label("cb_dw")
    E(adds_imm8, 0, 1); E(mov_reg, 3, 5); E(adds_imm8, 3, 30); E(cmp_reg, 0, 3); E(b_cond, "cb_dx", "hi")
    E(push_list, [0, 2]); E(bl, "c_chins"); E(mov_reg, 3, 0); E(pop_list, [0, 2]); E(cmp_imm, 3, 0); E(b_cond, "cb_dw", "eq")
    E(adds_imm8, 2, 1); E(lsls_imm, 3, 7, 1); E(cmp_reg, 2, 3); E(b_cond, "cb_dw", "ne")   # every second scale note
    E(adds_reg, 3, 4, 7); E(strb_imm, 0, 3, O_BUF); E(adds_imm8, 7, 1)
    E(raw, h(0x9B00)); E(cmp_reg, 7, 3); E(b_cond, "cb_dw", "lo")                      # ldr r3, [sp]
    a.label("cb_dx"); E(pop_list, [3])                                                 # r7 = the notes found
    a.label("cb_od")
    # open voicing: the second note an octave up
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_FL); E(movs_imm, 1, F_OPEN); E(raw, h(0x4208)); E(b_cond, "cb_s", "eq")
    E(cmp_imm, 7, 3); E(b_cond, "cb_s", "lo"); E(ldrb_imm, 0, 4, O_BUF + 1); E(adds_imm8, 0, 12); E(strb_imm, 0, 4, O_BUF + 1)
    a.label("cb_s")                                                                    # sorted (insertion)
    E(movs_imm, 1, 1)
    a.label("cb_so"); E(cmp_reg, 1, 7); E(b_cond, "cb_i", "hs"); E(mov_reg, 2, 1)
    a.label("cb_si"); E(cmp_imm, 2, 0); E(b_cond, "cb_sn", "eq")
    E(adds_reg, 3, 4, 2); E(ldrb_imm, 0, 3, O_BUF); E(subs_imm8, 3, 1); E(push_list, [1]); E(ldrb_imm, 1, 3, O_BUF); E(cmp_reg, 1, 0)
    E(b_cond, "cb_sp", "ls"); E(strb_imm, 0, 3, O_BUF); E(strb_imm, 1, 3, O_BUF + 1); E(pop_list, [1]); E(subs_imm8, 2, 1); E(b, "cb_si")
    a.label("cb_sp"); E(pop_list, [1])
    a.label("cb_sn"); E(adds_imm8, 1, 1); E(b, "cb_so")
    a.label("cb_i")                                                                    # the inversion: the lowest k up an octave (k < n)
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 1, 0, O_INV); E(cmp_reg, 1, 7); E(b_cond, "cb_ik", "lo"); E(mov_reg, 1, 7); E(subs_imm8, 1, 1)
    a.label("cb_ik"); E(movs_imm, 2, 0)
    a.label("cb_il"); E(cmp_reg, 2, 1); E(b_cond, "cb_b", "hs"); E(adds_reg, 3, 4, 2); E(ldrb_imm, 0, 3, O_BUF); E(adds_imm8, 0, 12); E(strb_imm, 0, 3, O_BUF)
    E(adds_imm8, 2, 1); E(b, "cb_il")
    a.label("cb_b")                                                                    # the root an octave down
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_FL); E(movs_imm, 1, F_BASS); E(raw, h(0x4208)); E(b_cond, "cb_f", "eq")
    E(cmp_imm, 7, 6); E(b_cond, "cb_f", "hs"); E(mov_reg, 0, 5); E(subs_imm8, 0, 12); E(b_cond, "cb_f", "le")
    E(adds_reg, 3, 4, 7); E(strb_imm, 0, 3, O_BUF); E(adds_imm8, 7, 1)
    a.label("cb_f")                                                                    # out of 1..139: dropped
    E(movs_imm, 1, 0); E(movs_imm, 2, 0)
    a.label("cb_fl"); E(cmp_reg, 1, 7); E(b_cond, "cb_fx", "hs"); E(adds_reg, 3, 4, 1); E(ldrb_imm, 0, 3, O_BUF)
    E(cmp_imm, 0, 1); E(b_cond, "cb_fn", "lo"); E(cmp_imm, 0, VMAX); E(b_cond, "cb_fn", "hi")
    E(adds_reg, 3, 4, 2); E(strb_imm, 0, 3, O_BUF); E(adds_imm8, 2, 1)
    a.label("cb_fn"); E(adds_imm8, 1, 1); E(b, "cb_fl")
    a.label("cb_fx"); E(mov_reg, 0, 2); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_choff(r0 = a held slot 0..15): its notes off (through its root pad); clobbers r0-r3
    a.label("c_choff")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0); E(bl, "c_chram"); E(lsls_imm, 1, 7, 3); E(adds_reg, 4, 0, 1); E(adds_imm8, 4, O_HELD)   # r4 = the slot
    E(ldrb_imm, 0, 4, 7); E(cmp_imm, 0, 0); E(b_cond, "co_x", "eq"); E(subs_imm8, 0, 1); E(bl, "c_chview"); E(mov_reg, 5, 0)   # r5 = the view
    E(adds_imm8, 7, 16)                                                                # r7 = the pad
    E(movs_imm, 6, 0)
    a.label("co_l"); E(ldrb_imm, 0, 4, 6); E(cmp_reg, 6, 0); E(b_cond, "co_e", "hs")
    E(ldrb_reg, 0, 4, 6); E(adds_reg, 1, 5, 7); E(adds_imm8, 1, 0x40); E(strb_imm, 0, 1, 0)
    E(mov_reg, 0, 5); E(mov_reg, 1, 7); E(bl, NOTE_OFF); E(adds_imm8, 6, 1); E(b, "co_l")
    a.label("co_e"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, 6); E(strb_imm, 0, 4, 7)
    a.label("co_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_challoff(r0 = track): its held chords off, its latch dropped; clobbers r0-r3
    a.label("c_challoff")
    E(push_list, [4, 5, 6], lr=True)
    E(adds_imm8, 0, 1); E(mov_reg, 5, 0); E(bl, "c_chram"); E(mov_reg, 6, 0); E(movs_imm, 4, 0)
    a.label("ca_l")
    E(lsls_imm, 0, 4, 3); E(adds_reg, 0, 0, 6); E(adds_imm8, 0, O_HELD); E(ldrb_imm, 0, 0, 7); E(cmp_reg, 0, 5); E(b_cond, "ca_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_choff")
    E(ldrb_imm, 0, 6, O_LAT); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "ca_n", "ne"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_LAT)
    a.label("ca_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "ca_l", "lo")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_chpad (the container's slot 0: obj, pad, velocity)
    #      r4 = RAM, r5 = the pad, r6 = the track, r7 = the flags' address
    a.label("c_chpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, "c_chtrk"); E(cmp_imm, 0, 0xFF); bc("cp_f", "eq"); E(mov_reg, 6, 0)
    E(ldr_sp, 5, 4); E(cmp_imm, 5, 31); bc("cp_f", "hi")
    E(bl, "c_chram"); E(mov_reg, 4, 0); E(adds_reg, 7, 4, 6); E(adds_imm8, 7, O_FL)
    E(bl, L["c_shift"]); E(mov_reg, 3, 0)                                              # r3 = Shift
    E(cmp_imm, 5, PAD_TOG); E(b_cond, "cp_on", "ne"); E(cmp_imm, 3, 0); E(b_cond, "cp_on", "eq")
    E(ldr_imm, 0, 4, O_SW); E(movs_imm, 1, 1); E(raw, h(0x40A9)); E(orrs_reg, 0, 1); E(str_imm, 0, 4, O_SW)   # swallowed (lsls r1, r5)
    E(ldrb_imm, 0, 7, 0); E(movs_imm, 1, F_ON); E(raw, h(0x4048)); E(strb_imm, 0, 7, 0)  # eors r0, r1: on / off
    E(raw, h(0x4208)); bc("cp_x", "ne"); E(mov_reg, 0, 6); E(bl, "c_challoff"); E(b, "cp_x")
    a.label("cp_on"); E(ldrb_imm, 0, 7, 0); E(lsls_imm, 0, 0, 31); bc("cp_f", "eq")   # the screen off: the stock's
    E(ldr_imm, 0, 4, O_SW); E(movs_imm, 1, 1); E(raw, h(0x40A9)); E(orrs_reg, 0, 1); E(str_imm, 0, 4, O_SW)   # swallowed (its release too)
    E(cmp_imm, 5, 8); E(b_cond, "cp_m", "hs")
    E(mov_reg, 0, 5); E(cmp_imm, 3, 0); E(b_cond, "cp_ty", "eq"); E(adds_imm8, 0, 8)     # row 1: the type (Shift: page 2)
    a.label("cp_ty"); E(adds_reg, 1, 4, 6); E(strb_imm, 0, 1, O_TY); E(b, "cp_x")
    a.label("cp_m"); E(cmp_imm, 5, 16); E(b_cond, "cp_r", "hs")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(cmp_imm, 0, 4); E(b_cond, "cp_g", "hs")      # pads 9-12: the inversion (the same again = root)
    E(adds_reg, 1, 4, 6); E(ldrb_imm, 2, 1, O_INV); E(cmp_reg, 2, 0); E(b_cond, "cp_iv", "ne"); E(movs_imm, 0, 0)
    a.label("cp_iv"); E(strb_imm, 0, 1, O_INV); E(b, "cp_x")
    a.label("cp_g"); E(subs_imm8, 0, 3); E(movs_imm, 1, 1); E(raw, h(0x4081)); E(ldrb_imm, 0, 7, 0); E(raw, h(0x4048)); E(strb_imm, 0, 7, 0)   # lsls r1, r0; eors r0, r1
    E(cmp_imm, 1, F_LATCH); bc("cp_x", "ne"); E(raw, h(0x4208)); bc("cp_x", "ne")   # latch off: the latched chord off
    E(ldrb_imm, 0, 4, O_LAT); E(cmp_imm, 0, 0); bc("cp_x", "eq"); E(subs_imm8, 0, 1); E(bl, "c_choff"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_LAT)
    E(b, "cp_x")
    a.label("cp_r")                                                                    # a root
    E(ldrb_imm, 0, 7, 0); E(movs_imm, 1, F_LATCH); E(raw, h(0x4208)); E(b_cond, "cp_rh", "eq")
    E(ldrb_imm, 0, 4, O_LAT); E(cmp_imm, 0, 0); E(b_cond, "cp_rh", "eq"); E(subs_imm8, 0, 1); E(bl, "c_choff"); E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_LAT)
    a.label("cp_rh"); E(mov_reg, 0, 5); E(subs_imm8, 0, 16); E(bl, "c_choff")
    E(mov_reg, 0, 6); E(bl, "c_chview"); E(mov_reg, 7, 0)                              # r7 = the view
    E(mov_reg, 1, 5); E(bl, PAD_IDX); E(mov_reg, 1, 0); E(push_list, [1]); E(ldr_imm, 0, 7, 0x38); E(bl, KEY_SKIP); E(pop_list, [1])
    E(cmp_imm, 0, 0); bc("cp_x", "ne")
    E(ldr_imm, 0, 7, 0x38); E(adds_reg, 0, 0, 1); E(ldrb_imm, 1, 0, 0x14); E(cmp_imm, 1, 0); bc("cp_x", "eq")   # r1 = the root
    E(push_list, [1]); E(mov_reg, 0, 6); E(bl, "c_chbuild"); E(pop_list, [1])
    E(lsls_imm, 2, 5, 3); E(subs_imm8, 2, 128); E(adds_reg, 2, 2, 4); E(adds_imm8, 2, O_HELD)   # r2 = the slot (pad - 16) x 8
    E(strb_imm, 0, 2, 6); E(adds_imm8, 6, 1); E(strb_imm, 6, 2, 7); E(subs_imm8, 6, 1)    # count, track + 1
    E(push_list, [1, 2]); E(movs_imm, 3, 0)
    a.label("cp_nl"); E(raw, h(0x9A01)); E(ldrb_imm, 0, 2, 6); E(cmp_reg, 3, 0); E(b_cond, "cp_ne", "hs")   # ldr r2, [sp, #4]
    E(adds_reg, 0, 4, 3); E(ldrb_imm, 1, 0, O_BUF); E(adds_reg, 0, 2, 3); E(strb_imm, 1, 0, 0)
    E(push_list, [3]); E(mov_reg, 0, 7); E(raw, h(0x9A05)); E(mov_reg, 3, 5); E(bl, NOTE_ON); E(pop_list, [3])   # ldr r2, [sp, #20]: the velocity
    E(adds_imm8, 3, 1); E(b, "cp_nl")
    a.label("cp_ne"); E(pop_list, [1, 2])
    E(adds_reg, 0, 7, 5); E(adds_imm8, 0, 0x40); E(strb_imm, 1, 0, 0); E(ldr_sp, 1, 8); E(adds_imm8, 0, 0x20); E(strb_imm, 1, 0, 0)   # the root pad held
    E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, O_FL); E(movs_imm, 1, F_LATCH); E(raw, h(0x4208)); bc("cp_x", "eq")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 15); E(strb_imm, 0, 4, O_LAT)
    a.label("cp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("cp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_chrel (the container's slot 1: obj, pad): a pad we took is ours; a root's chord off (not the latched one)
    a.label("c_chrel")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(cmp_imm, 1, 31); E(b_cond, "cl_f", "hi"); E(mov_reg, 5, 1)
    E(bl, "c_chram"); E(mov_reg, 4, 0); E(ldr_imm, 0, 4, O_SW); E(movs_imm, 1, 1); E(raw, h(0x40A9)); E(raw, h(0x4208)); E(b_cond, "cl_f", "eq")
    E(raw, h(0x4388)); E(str_imm, 0, 4, O_SW)                                          # bics r0, r1
    E(cmp_imm, 5, 16); E(b_cond, "cl_x", "lo")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 15); E(ldrb_imm, 1, 4, O_LAT); E(cmp_reg, 0, 1); E(b_cond, "cl_x", "eq")
    E(subs_imm8, 0, 1); E(bl, "c_choff")
    a.label("cl_x"); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("cl_f"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["rel"])

    # ---- c_chleds (the container's slot 7: obj) -> r0 = the LED buffer: rows 1-2 of the chord screen; with Shift pad 8 yellow / green
    a.label("c_chleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_chtrk"); E(cmp_imm, 0, 0xFF); E(b_cond, "cd_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_chram"); E(adds_reg, 4, 0, 6)                                             # r4 = RAM + the track
    E(bl, L["c_shift"]); E(mov_reg, 7, 0)                                              # r7 = Shift
    E(ldrb_imm, 0, 4, O_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "cd_on", "ne")
    E(cmp_imm, 7, 0); E(b_cond, "cd_x", "eq"); E(movs_imm, 0, COL_SHIFT); E(strh_imm, 0, 5, 2 * PAD_TOG); E(b, "cd_x")
    a.label("cd_on")
    E(movs_imm, 3, 0)
    a.label("cd_t")                                                                    # row 1
    E(mov_reg, 0, 3); E(movs_imm, 2, COL_DIM); E(cmp_imm, 7, 0); E(b_cond, "cd_tn", "eq"); E(adds_imm8, 0, 8); E(movs_imm, 2, COL_SHIFT)
    E(cmp_imm, 3, PAD_TOG); E(b_cond, "cd_tn", "ne"); E(movs_imm, 2, COL_ON); E(b, "cd_tw")
    a.label("cd_tn"); E(ldrb_imm, 1, 4, O_TY); E(cmp_reg, 1, 0); E(b_cond, "cd_tw", "ne"); E(movs_imm, 2, COL_SEL)
    a.label("cd_tw"); E(lsls_imm, 0, 3, 1); E(strh_reg, 2, 5, 0); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "cd_t", "lo")
    a.label("cd_m")                                                                    # row 2
    E(mov_reg, 0, 3); E(subs_imm8, 0, 8); E(movs_imm, 2, COL_DIM); E(cmp_imm, 0, 4); E(b_cond, "cd_g", "hs")
    E(ldrb_imm, 1, 4, O_INV); E(cmp_reg, 1, 0); E(b_cond, "cd_mw", "ne"); E(movs_imm, 2, COL_INV); E(b, "cd_mw")
    a.label("cd_g"); E(subs_imm8, 0, 3); E(movs_imm, 1, 1); E(raw, h(0x4081)); E(ldrb_imm, 0, 4, O_FL); E(raw, h(0x4208)); E(b_cond, "cd_mw", "eq")
    E(movs_imm, 2, COL_ON)
    a.label("cd_mw"); E(lsls_imm, 0, 3, 1); E(strh_reg, 2, 5, 0); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "cd_m", "lo")
    a.label("cd_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the track views' container's slots 0 / 1 / 7 (in front of the chain)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_spk=lab("smpick", "c_spk"), c_s4on=lab("split4", "c_s4on"))
    prev = dict(pad=u(CONT_VT) & ~1, rel=u(CONT_VT + 4) & ~1, leds=u(CONT_VT + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert CR + RSZ <= MX.MXR + 0x600
    struct.pack_into("<I", img, CONT_VT - BASE, labels["c_chpad"] | 1)
    struct.pack_into("<I", img, CONT_VT + 4 - BASE, labels["c_chrel"] | 1)
    struct.pack_into("<I", img, CONT_VT + 28 - BASE, labels["c_chleds"] | 1)
    return labels, code, prev
