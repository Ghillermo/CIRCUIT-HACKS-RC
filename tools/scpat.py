"""SC43.4 (the user, 2026-10-16: «¿Se pueden añadir canales MIDI 1/2 como trigger del sidechain?» … «Implement midi1/2 and synth1/2 sidechain
pattern-driven triggers only»): Synth 1, Synth 2, MIDI 1 and MIDI 2 as sources of the side-chain, besides Drum 1-4.

The stock (read in the firmware and the DSP program, emulated):
  * a target (Synth 1, Synth 2, MIDI 1 = audio strip 3, MIDI 2 = strip 4) has five project parameters (type 0x20, 26 + 5 t: source 0..3 = Drum 1-4,
    attack, hold, decay, depth); the DSP groups 5-8 (0x08028C9D, 0x08028D33, 0x08028DC9, 0x08028E37) write the source with
    0x080292F8(0, source << 8, X:$3F2 / $564 / $28C / $291) (the calls at 0x08028CAE, 0x08028D44, 0x08028DDA, 0x08028E48);
  * a drum hit writes X:$99 + drum = $F (one bit a target); the DSP (P:$1277...) restarts target k's envelope when bit k of X:($99 + its source) is
    set, and clears it (bclr #k, x:(r1 + n1), r1 = $99, n1 = the source word).  X:$9D on are taken (a synth voice word, the drum velocities);
  * the Sidechain view (0x20042BB8, vtable 0x0805AC2C): row 1 pads 5-8 = the source of the target of [[view + 0x1C] + 0x14] (the last preset row
    touched; the page's first track after a page change), rows 3 / 4 = the presets of the page's two targets; row 1 pads 1-4 dark and unused.

Ours:
  * four trigger words in free X memory, X:$3BF2..$3BF5 (TRIG + s, s = 0 Synth 1, 1 Synth 2, 2 MIDI 1, 3 MIDI 2; after vcf21's $3BE0..$3BF1);
  * a target's own source (0 = the stock's drum, 1..4 = Synth 1, Synth 2, MIDI 1, MIDI 2) in the record's tail + 596 (saved with the project:
    0xC5, two nibble bytes, a check byte); the four call sites write X:(source) = TRIG + own - 1 - $99 instead of the drum, so the DSP reads that
    word;
  * every pattern note of a note track (the players' note-on 0x08040FA2, velocity > 0; the arpeggiator's notes too) with a target listening to it:
    X:(TRIG + track) = $F, as a drum hit;
  * the Sidechain view, the stock pages (SC16's page < 2): row 1 pads 1-4 = Synth 1, Synth 2, MIDI 1, MIDI 2 as the source of the chosen target (the
    group marked dirty, so the DSP gets it); pads 5-8 (a drum) give it back to the stock; LEDs: the chosen source in the target's colour, the
    others dim (pads 1-4 dim when a drum is chosen, pads 5-8 dim when ours is).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_sp, strb_imm, strh_imm, ands_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

SITES = (0x08028CAE, 0x08028D44, 0x08028DDA, 0x08028E48)     # bl 0x080292F8 of the source, groups 5-8 = targets Synth 1, Synth 2, MIDI 1, MIDI 2
DSP_W = 0x080292F8
FLAGS, TRIG = 0x99, 0x3BF2
NOTE_ON, NOTE_ON_OLD = 0x08040FA2, bytes.fromhex("2de9f041")  # push.w {r4-r8, lr}
SC_VT, SC_VIEW = 0x0805AC2C, 0x20042BB8
SESSION_OBJ, TAIL, O_BLK, MAGIC = 0x2003D71C, 0x27024, 596, 0xC5
TYPE, BASE0, PER = 0x20, 26, 5
MARK_DIRTY, GETTER = 0x0803BDCC, 0x08036192
COL = (0x32, 0x17, 0x09, 0x3B)                                # the targets' colours (as the stock's chosen source pad, sckn.COL)
DIM = 0x02                                                    # the stock's not-chosen source pad
PAD_DRUM0 = 4                                                 # pads 5-8: the stock's sources
DRUMS = False                                                 # SC43.8 (use_drums)
S16_BLK, PAL = 0x3A10, 0x08056464                             # SC16's DSP blocks (X:$3A10 + 9 d: word 0 = the trigger); the palette
OWN0 = 4                                                      # (DRUMS) SC16's trigger byte [8 + d]: 0..3 a drum, 4..7 Synth 1, Synth 2, MIDI 1, MIDI 2
DIM_I = 0x13                                                  # SC16's palette index of a source pad not chosen (the chosen: 5 + the drum)


def use_drums():
    """SC43.8 (the user, 2026-10-17: «add gate sidechain to the drums»): Synth 1, Synth 2, MIDI 1 and MIDI 2 as the trigger of SC16's drum
    side-chain too.  SC16 (build_sc16.py): its state (c_gst() + 24) holds a trigger drum per drum ([8 + d], 0..3; RAM only, as its presets);
    a drum hit (c_trig) writes word 0 of the DSP block X:$3A10 + 9 k = 1 for every drum k with a preset whose trigger is that drum.
    Ours: the trigger byte 4..7 = a note track (SC16's own code never matches it: no drum fires it, no pad 5-8 is lit):
      * on SC16's drum pages of the Sidechain view, row 1 pads 1-4 (dark there) = Synth 1, Synth 2, MIDI 1, MIDI 2 as the trigger of the drum
        touched last ([13], the one SC16's pads 5-8 set); a pad 5-8 gives it back to a drum (SC16's);
      * every pattern note of that track (the players' note-on, velocity > 0, as for the note tracks' targets) = word 0 of the drum's block;
      * LEDs from the LED task: the chosen pad in the colour SC16 gives the chosen drum source (palette 5 + the drum), the others dim (0x13)."""
    global DRUMS
    DRUMS = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    E(raw, bytes(COL)); t_col = base

    # ---- c_spblk() -> r0 = our block (the tail + 596), or 0 without a record; clobbers r1
    a.label("c_spblk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "sb_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("sb_x"); E(raw, RET)

    # ---- c_spok(r0 = the block) -> r0 = 1 when it holds ours; clobbers r1, r2
    a.label("c_spok")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "so_n", "ne")
    E(ldrb_imm, 1, 0, 1); E(ldrb_imm, 2, 0, 2); E(eors_reg, 1, 2); E(movs_imm, 2, 0x5A); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 0, 3); E(cmp_reg, 1, 2); E(b_cond, "so_n", "ne")
    E(movs_imm, 0, 1); E(raw, RET)
    a.label("so_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_spget(r0 = target 0..3) -> r0 = its own source (0 = the stock's drum, 1..4); clobbers r1-r3
    a.label("c_spget")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_spblk"); E(mov_reg, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "sg_z", "eq")
    E(bl, "c_spok"); E(cmp_imm, 0, 0); E(b_cond, "sg_z", "eq")
    E(lsrs_imm, 1, 4, 1); E(adds_reg, 1, 1, 5); E(ldrb_imm, 0, 1, 1)
    E(lsls_imm, 1, 4, 31); E(b_cond, "sg_l", "eq"); E(lsrs_imm, 0, 0, 4)
    a.label("sg_l"); E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(cmp_imm, 0, 4); E(b_cond, "sg_x", "ls")
    a.label("sg_z"); E(movs_imm, 0, 0)
    a.label("sg_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_spset(r0 = target, r1 = its own source 0..4): the block made when missing; clobbers r0-r3
    a.label("c_spset")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_spblk"); E(mov_reg, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "ss_x", "eq")
    E(bl, "c_spok"); E(cmp_imm, 0, 0); E(b_cond, "ss_ok", "ne")
    E(movs_imm, 0, MAGIC); E(strb_imm, 0, 6, 0); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 1); E(strb_imm, 0, 6, 2)
    a.label("ss_ok")
    E(lsrs_imm, 1, 4, 1); E(adds_reg, 1, 1, 6); E(ldrb_imm, 0, 1, 1)
    E(movs_imm, 2, 15); E(movs_imm, 3, 0)
    E(lsls_imm, 3, 4, 31); E(b_cond, "ss_lo", "eq")
    E(lsls_imm, 2, 2, 4); E(lsls_imm, 5, 5, 4)
    a.label("ss_lo"); E(raw, h(0x4390)); E(orrs_reg, 0, 5); E(strb_imm, 0, 1, 1)                   # bics r0, r2
    E(ldrb_imm, 0, 6, 1); E(ldrb_imm, 1, 6, 2); E(eors_reg, 0, 1); E(movs_imm, 1, 0x5A); E(eors_reg, 0, 1); E(strb_imm, 0, 6, 3)
    a.label("ss_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_spuses(r0 = a source 1..4) -> r0 = 1 when a target listens to it; clobbers r1-r3
    a.label("c_spuses")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 5, 0)
    a.label("su_l"); E(mov_reg, 0, 5); E(bl, "c_spget"); E(cmp_reg, 0, 4); E(b_cond, "su_y", "eq")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 4); E(b_cond, "su_l", "lo")
    E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)
    a.label("su_y"); E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)

    # ---- c_spsrc0..3 (the groups' bl 0x080292F8 of the source: 0, value << 8, address): our source = the address of its trigger word - $99
    for t in range(4):
        a.label(f"c_spsrc{t}")
        E(push_list, [0, 1, 2, 3, 4], lr=True)
        E(movs_imm, 0, t); E(bl, "c_spget"); E(cmp_imm, 0, 0); E(b_cond, f"sr_k{t}", "eq")
        E(movw, 1, TRIG - FLAGS - 1); E(adds_reg, 1, 1, 0); E(lsls_imm, 1, 1, 8); E(str_sp, 1, 4)
        a.label(f"sr_k{t}"); E(raw, popw([0, 1, 2, 3, 4], lr=True))
        E(b_w, DSP_W)

    # ---- c_spnote (the players' note-on 0x08040FA2: this, note, velocity, ticks): a pattern note of a track somebody listens to = its trigger word
    a.label("c_spnote")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(cmp_imm, 2, 0); E(b_cond, "sn_x", "eq")
    E(bl, L["c_artrk"]); E(cmp_imm, 0, 3); E(b_cond, "sn_x", "hi"); E(mov_reg, 4, 0)
    if DRUMS: E(bl, "c_spdrum"); E(mov_reg, 0, 4)
    E(adds_imm8, 0, 1); E(bl, "c_spuses"); E(cmp_imm, 0, 0); E(b_cond, "sn_x", "eq")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0xF); E(lsls_imm, 1, 1, 8); E(movw, 2, TRIG); E(adds_reg, 2, 2, 4); E(bl, DSP_W)
    a.label("sn_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True))
    E(raw, NOTE_ON_OLD); E(b_w, NOTE_ON + 4)

    if DRUMS:
        # ---- c_spdrum(r0 = a note track 0..3): the drums whose side-chain it triggers: word 0 of their blocks
        a.label("c_spdrum")
        E(push_list, [4, 5, 6], lr=True)
        E(adds_imm8, 0, OWN0); E(mov_reg, 6, 0)
        E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "dd_x", "eq"); E(mov_reg, 4, 0); E(movs_imm, 5, 0)
        a.label("dd_l")
        E(adds_reg, 0, 4, 5); E(ldrb_imm, 1, 0, 4); E(cmp_imm, 1, 0); E(b_cond, "dd_n", "eq")          # a preset on
        E(ldrb_imm, 1, 0, 8); E(cmp_reg, 1, 6); E(b_cond, "dd_n", "ne")
        E(movs_imm, 2, 9); E(muls, 2, 5); E(movw, 0, S16_BLK); E(adds_reg, 2, 2, 0)
        E(movs_imm, 0, 0); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 8); E(bl, DSP_W)
        a.label("dd_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 4); E(b_cond, "dd_l", "lo")
        a.label("dd_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_spdirty(r0 = target): its source parameter marked, so the group goes to the DSP again (the interface task); clobbers r0-r3
    a.label("c_spdirty")
    E(raw, h(0xB500)); E(movs_imm, 1, PER); E(muls, 1, 0); E(adds_imm8, 1, BASE0); E(movs_imm, 0, TYPE); E(bl, MARK_DIRTY); E(raw, h(0xBD00))

    # ---- c_spstock() -> r0 = 1 on the stock pages (SC16's page < 2); clobbers r1-r3
    a.label("c_spstock")
    E(raw, h(0xB500)); E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "sk_y", "eq")
    E(ldrb_imm, 0, 0, 12); E(cmp_imm, 0, 2); E(b_cond, "sk_y", "lo"); E(movs_imm, 0, 0); E(raw, h(0xBD00))
    a.label("sk_y"); E(movs_imm, 0, 1); E(raw, h(0xBD00))

    # ---- c_sppad (the Sidechain view's slot 0: view, pad, velocity): row 1 pads 1-4 = ours as the chosen target's source; pads 5-8 = back to the stock
    a.label("c_sppad")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, 8); E(b_cond, "sp_f", "hs")
    E(bl, "c_spstock"); E(cmp_imm, 0, 0); E(b_cond, "sp_dr" if DRUMS else "sp_f", "eq")
    E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x1C); E(ldrb_imm, 4, 0, 0x14); E(cmp_imm, 4, 3); E(b_cond, "sp_f", "hi")   # r4 = the target
    E(ldr_sp, 5, 4); E(cmp_imm, 5, PAD_DRUM0); E(b_cond, "sp_d", "hs")
    E(mov_reg, 0, 4); E(adds_imm8, 5, 1); E(mov_reg, 1, 5); E(bl, "c_spset"); E(mov_reg, 0, 4); E(bl, "c_spdirty")
    E(raw, h(0xB003)); E(pop_list, [4, 5], pc=True)                                                    # add sp, #12
    a.label("sp_d")
    E(mov_reg, 0, 4); E(bl, "c_spget"); E(cmp_imm, 0, 0); E(b_cond, "sp_f", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_spset"); E(mov_reg, 0, 4); E(bl, "c_spdirty")
    a.label("sp_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["pad"])
    if DRUMS:                                                                                          # a drum page: pads 1-4 = a note track
        a.label("sp_dr")
        E(ldr_sp, 5, 4); E(cmp_imm, 5, PAD_DRUM0); E(b_cond, "sp_f", "hs")
        E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "sp_f", "eq")
        E(ldrb_imm, 1, 0, 13); E(cmp_imm, 1, 3); E(b_cond, "sp_f", "hi"); E(adds_reg, 1, 1, 0)
        E(adds_imm8, 5, OWN0); E(strb_imm, 5, 1, 8)
        E(raw, h(0xB003)); E(pop_list, [4, 5], pc=True)                                                # add sp, #12

    # ---- c_spledtask (the LED task calls: ctrl, frame): the chain; the Sidechain view's stock pages: pads 1-8 as above
    a.label("c_spledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, L["c_skon"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "eq")
    E(bl, "c_spstock"); E(cmp_imm, 0, 0); E(b_cond, "sl_dr" if DRUMS else "sl_x", "eq")
    imm32(0, SC_VIEW); E(ldr_imm, 0, 0, 0x1C); E(ldrb_imm, 4, 0, 0x14); E(cmp_imm, 4, 3); E(b_cond, "sl_x", "hi")
    E(mov_reg, 0, 4); E(bl, "c_spget"); E(mov_reg, 6, 0)                                               # r6 = ours (0: the stock's drum)
    E(movs_imm, 7, 0)
    a.label("sl_l")
    E(movs_imm, 0, DIM); E(cmp_imm, 7, PAD_DRUM0); E(b_cond, "sl_o", "lo")
    E(cmp_imm, 6, 0); E(b_cond, "sl_n", "eq"); E(b, "sl_w")                                            # pads 5-8: the stock's, or dim with ours
    a.label("sl_o")                                                                                    # pads 1-4: dim, or the target's colour for ours
    E(adds_imm3, 1, 7, 1); E(cmp_reg, 1, 6); E(b_cond, "sl_w", "ne")
    imm32(1, t_col); E(adds_reg, 1, 1, 4); E(ldrb_imm, 0, 1, 0)
    a.label("sl_w"); E(lsls_imm, 1, 7, 1); E(raw, h(0x5268))                                            # strh r0, [r5, r1]
    a.label("sl_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "sl_l", "lo")
    a.label("sl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    if DRUMS:                                                                                          # a drum page: pads 1-4
        a.label("sl_dr")
        E(bl, L["c_scst"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "eq"); E(mov_reg, 4, 0)
        E(ldrb_imm, 6, 4, 13); E(cmp_imm, 6, 3); E(b_cond, "sl_x", "hi")                               # r6 = the drum
        E(adds_reg, 0, 4, 6); E(ldrb_imm, 7, 0, 8); E(movs_imm, 3, 0)                                  # r7 = its trigger
        a.label("sl_dl")
        E(movs_imm, 0, DIM_I); E(adds_imm3, 1, 3, OWN0); E(cmp_reg, 1, 7); E(b_cond, "sl_dw", "ne"); E(adds_imm3, 0, 6, 5)
        a.label("sl_dw"); E(lsls_imm, 0, 0, 1); imm32(1, PAL); E(raw, h(0x5A08))                       # ldrh r0, [r1, r0]
        E(lsls_imm, 1, 3, 1); E(raw, h(0x5268))                                                        # strh r0, [r5, r1]
        E(adds_imm8, 3, 1); E(cmp_imm, 3, 4); E(b_cond, "sl_dl", "lo")
        E(b, "sl_x")
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the four source writes of groups 5-8, the players' note-on, slot 0 of the Sidechain view, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_artrk=lab("arp", "c_artrk"), c_scst=lab("sc16", "c_scst"), c_skon=lab("sckn", "c_skon"))
    prev = dict(pad=u(SC_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    for s in SITES:
        assert bytes(img[s - BASE:s - BASE + 4]) == bl_enc(s, DSP_W), hex(s)
    assert bytes(img[NOTE_ON - BASE:NOTE_ON - BASE + 4]) == NOTE_ON_OLD
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for t, s in enumerate(SITES):
        img[s - BASE:s - BASE + 4] = bl_enc(s, labels[f"c_spsrc{t}"])
    img[NOTE_ON - BASE:NOTE_ON - BASE + 4] = b_w(NOTE_ON, labels["c_spnote"])
    struct.pack_into("<I", img, SC_VT - BASE, labels["c_sppad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_spledtask"])
    return labels, code, prev
