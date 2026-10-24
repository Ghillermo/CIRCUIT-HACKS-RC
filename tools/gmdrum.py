"""SC46.2 / Beta 3.19 (the user, 2026-10-24: «New function on Beta for General MIDI with a toggle on setup memory/setup view.  A user selected value
per drum Channel (ranging 35 to 81) sets the target note.  Whenever that Channel triggers, a noteOn is sent with said value instead of the stock
pitch» · «El envío del modo GM es en el canal asignado a los drums» · «De fábrica, el canal asignado a los drums es el 10.  Este se puede cambiar
en setup view de stock.  Ese canal elegido será el designado para la salida»; how the value is chosen: ours, on controls nobody uses).

The stock's MIDI out of the drums: the drums' note interface reaches the transmitter (0x20011334, its vtable's note-on 0x08059FC4 / note-off
0x08059FC8: (tx, track, note, velocity)) with the track 16 (0x10, the drums' channel of the Setup view: 10 by default) and the fixed notes 60 / 62 /
64 / 65 = Drum 1..4.
  * the heads of those two entries (c_gmon / c_gmoff, in front of the chain): the GM mode on, a drum's note-on goes out with its GM note instead
    (kept as the sounding note of that drum), its note-off with the note its note-on had (so a change, or the mode turned off, leaves nothing
    hanging); other notes, other tracks: as before;
  * the Setup view (mode 8 of [ctrl + 0x14], not the Advanced page), whose knobs the stock does not use (its slot 4 is a stub; the user,
    2026-10-24: «usa K4-8 (knobs sobre las pistas de drums) y Shift o salida de Setup para confirmar»): K5..K8 (over the drum tracks) = the GM
    note of Drum 1..4, 35..81, 2 clicks a note; every new note sounds once on the drums' channel (on and off at once: a GM module plays its
    percussion one-shot) and its number is drawn on the 32 pads in the drum's colour (vcf21's c_ednum: the stock tempo display's font) until
    Shift or leaving the Setup view confirms (the save asked then); meanwhile the Setup's pads do nothing; K4 = the mode, to the right on, to the
    left off (saved at once); LEDs: K5..K8 in the drums' colours with a brightness after the note (dim with the mode off), K4 green on / dim off;
  * saved with the unit's settings (the Setup's memory): bytes 1-3 of parameters 4..7 of the settings record, which nothing reads (the channels of
    the tracks are their bytes 0; pgmch / cue use parameter 3): parameter 4 byte 1 = 0xC9 (the signature), byte 2 = the flags (bit 0 the mode),
    byte 3 = Drum 1's note; parameters 5 / 6 / 7 byte 1 = Drums 2..4's; both copies of the store (no commit: its listeners send MIDI) and the save
    asked of lazysave (the record's tail + 186 = 0xA5, + 188 the time: written with the transport stopped); without the signature (or a note out
    of range) the defaults: off, 36 / 38 / 42 / 46 (kick, snare, closed hat, open hat).
RAM: modmx.MXR + 0x4A0 (16 B with a signature: the sounding notes, the knobs' accumulators, the drum being edited).  In the hole (it writes no card: lazysave does).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm, lsrs_reg,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, str_sp, strb_imm, strb_reg, strh_reg, subs_imm8,
                   subs_reg)
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import lazysave as LZ  # noqa: E402
import pgmch as PG  # noqa: E402

TX_VT = 0x08059FC4                                       # the transmitter's vtable: + 0 note-on, + 4 note-off
TX = 0x20011334
DRUMS = 0x10                                             # the drums' track at the transmitter
STOCK_NOTES = (60, 62, 64, 65)
DEFAULTS = (36, 38, 42, 46)
NMIN, NMAX = 35, 81
P0, SIG, B_FLAGS = 4, 0xC9, 2                            # parameter 4: byte 1 the signature, byte 2 the flags, byte 3 Drum 1's note; 5..7 byte 1
RAM = MX.MXR + 0x4A0                                     # + 0 "GMD1", + 4..7 the sounding notes, + 8..11 the accumulators (s8), + 12 1 + the drum edited
RSIG = 0x31444D47
CLICKS = 2
K_TOG, K_D1 = 3, 4                                       # K4 the mode, K5..K8 Drum 1..4
COL_ON, COL_OFF = 0x17, 0x02
O_EDIT = 12
PREVIEW_VEL = 100
V2 = False                                               # SC46.3 (use_v2)
V3 = False                                               # SC46.4 (use_v3)


def use_v3():
    """SC46.4: K4 changes only bit 0 of the flags byte (usbmerge keeps its bit 1 there)."""
    global V3
    V3 = True


def use_v2():
    """SC46.3 (the user, 2026-10-24: «Cuando k4:off, la vista se cierra y vuelve el setup y el funcionamiento normal de drums»): K4 to off closes
    the number view (the Setup's pads back, the save asked); with the mode off K5..K8 do nothing and their LEDs are the stock's."""
    global V2
    V2 = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev, L, DC):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def ctx(rd, off): imm32(rd, PG.CTX); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, 0); E(ldr_imm, rd, rd, off)
    RET = h(0x4770)

    # ---- c_gmram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_gmram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "gr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(str_imm, 1, 0, 12)
    a.label("gr_x"); E(raw, RET)

    # ---- c_gmp(r0 = parameter, r1 = 0 the read copy / 1 the write copy) -> r0 = its 4 bytes in the settings store; clobbers r1-r3
    a.label("c_gmp")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(cmp_imm, 1, 0); E(b_cond, "gp_w", "ne")
    ctx(0, 0x54); E(mov_reg, 1, 4); E(bl, PG.PARAM_GET); E(pop_list, [4], pc=True)
    a.label("gp_w"); ctx(0, 0x54); E(mov_reg, 1, 4); E(bl, PG.PARAM_WPTR); E(pop_list, [4], pc=True)

    # ---- c_gmsig() -> r0 = 1 with our signature; clobbers r1-r3
    a.label("c_gmsig")
    E(raw, h(0xB500)); E(movs_imm, 0, P0); E(movs_imm, 1, 0); E(bl, "c_gmp"); E(ldrb_imm, 0, 0, 1)
    E(cmp_imm, 0, SIG); E(b_cond, "gs_0", "ne"); E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("gs_0"); E(movs_imm, 0, 0); E(raw, h(0xBD00))

    # ---- c_gmon_q() -> r0 = 1 with the mode on; clobbers r1-r3
    a.label("c_gmon_q")
    E(raw, h(0xB500)); E(bl, "c_gmsig"); E(cmp_imm, 0, 0); E(b_cond, "go_x", "eq")
    E(movs_imm, 0, P0); E(movs_imm, 1, 0); E(bl, "c_gmp"); E(ldrb_imm, 0, 0, B_FLAGS); E(movs_imm, 1, 1); E(raw, h(0x4008))   # ands r0, r1
    a.label("go_x"); E(raw, h(0xBD00))

    # ---- c_gmaddr(r0 = drum, r1 = copy) -> r0 = the address of its note byte; clobbers r1-r3
    a.label("c_gmaddr")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(cmp_imm, 4, 0); E(b_cond, "ga_1", "ne"); E(movs_imm, 0, P0); E(bl, "c_gmp"); E(adds_imm8, 0, 3); E(pop_list, [4], pc=True)
    a.label("ga_1"); E(mov_reg, 0, 4); E(adds_imm8, 0, P0); E(bl, "c_gmp"); E(adds_imm8, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_gmnote(r0 = drum) -> r0 = its GM note (the default without the signature or out of range); clobbers r1-r3
    a.label("c_gmnote")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_gmsig"); E(cmp_imm, 0, 0); E(b_cond, "gn_d", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_gmaddr"); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, NMIN); E(b_cond, "gn_d", "lo"); E(cmp_imm, 0, NMAX); E(b_cond, "gn_d", "hi"); E(pop_list, [4], pc=True)
    a.label("gn_d"); imm32(0, struct.unpack("<I", bytes(DEFAULTS))[0]); E(lsls_imm, 1, 4, 3); E(raw, h(0x40C8)); E(movs_imm, 1, 0xFF); E(raw, h(0x4008))   # lsrs r0, r1; ands r0, r1
    E(pop_list, [4], pc=True)

    # ---- c_gmput(r0 = byte offset in parameter 4 or a drum + 16, r1 = the value): both copies; the signature and the defaults made first;
    #      the save asked of lazysave.  (r0 < 16: byte r0 of parameter 4; r0 = 16 + d: drum d's note)
    a.label("c_gmput")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_gmsig"); E(cmp_imm, 0, 0); E(b_cond, "gu_s", "ne")
    E(movs_imm, 6, 0)                                                                          # no signature yet: the defaults written
    a.label("gu_d")
    for cp in (0, 1):
        E(mov_reg, 0, 6); imm32(1, struct.unpack("<I", bytes(DEFAULTS))[0]); E(lsls_imm, 2, 6, 3); E(raw, h(0x40D1)); E(push_list, [1])   # lsrs r1, r2
        E(mov_reg, 0, 6); E(movs_imm, 1, cp); E(bl, "c_gmaddr"); E(pop_list, [1]); E(strb_imm, 1, 0, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "gu_d", "lo")
    for cp in (0, 1):
        E(movs_imm, 0, P0); E(movs_imm, 1, cp); E(bl, "c_gmp"); E(movs_imm, 1, SIG); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(strb_imm, 1, 0, B_FLAGS)
    a.label("gu_s")
    for cp in (0, 1):
        E(cmp_imm, 4, 16); E(b_cond, f"gu_n{cp}", "hs")
        E(movs_imm, 0, P0); E(movs_imm, 1, cp); E(bl, "c_gmp"); E(strb_reg, 5, 0, 4); E(b, f"gu_e{cp}")
        a.label(f"gu_n{cp}"); E(mov_reg, 0, 4); E(subs_imm8, 0, 16); E(movs_imm, 1, cp); E(bl, "c_gmaddr"); E(strb_imm, 5, 0, 0)
        a.label(f"gu_e{cp}")
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_gmsave(): the settings' save asked of lazysave (pending, now); clobbers r0, r1
    a.label("c_gmsave")
    imm32(0, LZ.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "gv_x", "eq")
    imm32(1, LZ.TAIL); E(adds_reg, 0, 0, 1); E(movs_imm, 1, LZ.PEND); E(raw, h(0xF880) + h(1 << 12 | LZ.O_PEND))   # strb.w r1, [r0, #186]
    imm32(1, LZ.HAL_TICK); E(ldr_imm, 1, 1, 0); E(raw, h(0xF8C0) + h(1 << 12 | LZ.O_TIME))         # str.w r1, [r0, #188]
    a.label("gv_x"); E(raw, RET)

    # ---- c_gmdrum(r2 = a note) -> r0 = its drum 0..3, or 4; clobbers r1
    a.label("c_gmdrum")
    E(movs_imm, 0, 0)
    for k, n in enumerate(STOCK_NOTES):
        E(cmp_imm, 2, n); E(b_cond, "gd_x", "eq"); E(adds_imm8, 0, 1)
    a.label("gd_x"); E(raw, RET)

    # ---- c_gmon (the transmitter's note-on: tx, track, note, velocity): a drum with the mode on = its GM note, kept as sounding
    a.label("c_gmon")
    E(cmp_imm, 1, DRUMS); E(b_cond, "on_f", "ne")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(bl, "c_gmdrum"); E(cmp_imm, 0, 4); E(b_cond, "on_p", "hs"); E(mov_reg, 4, 0)
    E(bl, "c_gmram"); E(adds_reg, 5, 0, 4)                                                         # r5 = its sounding byte - 4
    E(bl, "c_gmon_q"); E(cmp_imm, 0, 0); E(b_cond, "on_0", "eq")
    E(mov_reg, 0, 4); E(bl, "c_gmnote"); E(strb_imm, 0, 5, 4); E(str_sp, 0, 8); E(b, "on_p")     # the note sent: [sp + 8] = r2
    a.label("on_0"); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 4)
    a.label("on_p"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True))
    a.label("on_f"); E(b_w, prev["on"])

    # ---- c_gmoff (the transmitter's note-off: tx, track, note, velocity): a drum = the note its note-on had
    a.label("c_gmoff")
    E(cmp_imm, 1, DRUMS); E(b_cond, "of_f", "ne")
    E(raw, pushw([0, 1, 2, 3, 4, 5], lr=True))
    E(bl, "c_gmdrum"); E(cmp_imm, 0, 4); E(b_cond, "of_p", "hs"); E(mov_reg, 4, 0)
    E(bl, "c_gmram"); E(adds_reg, 5, 0, 4); E(ldrb_imm, 0, 5, 4); E(cmp_imm, 0, 0); E(b_cond, "of_p", "eq")
    E(str_sp, 0, 8); E(movs_imm, 0, 0); E(strb_imm, 0, 5, 4)
    a.label("of_p"); E(raw, popw([0, 1, 2, 3, 4, 5], lr=True))
    a.label("of_f"); E(b_w, prev["off"])

    # ---- c_gmsetup() -> r0 = 1 with the Setup view (not Advanced) on the screen; clobbers r1-r3
    a.label("c_gmsetup")
    E(raw, h(0xB500))
    imm32(0, PG.MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PG.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "su_0", "ne")
    imm32(0, PG.SETUP_OBJ); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "su_0", "ne")
    E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("su_0"); E(movs_imm, 0, 0); E(raw, h(0xBD00))

    # ---- c_gmknob (the Setup view's slot 4: view, knob, delta): K5..K8 the drums' GM notes (the number shown until confirmed), K4 the mode
    a.label("c_gmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "gk_f", "ne")
    E(cmp_imm, 5, K_TOG); E(b_cond, "gk_n", "ne")
    E(movs_imm, 1, 1); E(cmp_imm, 6, 0); E(b_cond, "gk_t", "gt"); E(movs_imm, 1, 0)                 # K4: right = on, left = off
    a.label("gk_t")
    E(push_list, [1]); E(bl, "c_gmon_q"); E(pop_list, [1]); E(cmp_reg, 0, 1); E(b_cond, "gk_x", "eq")
    if V2: E(mov_reg, 4, 1)
    if V3:                                                                                         # the other bits of the flags kept
        E(push_list, [1]); E(bl, "c_gmsig"); E(pop_list, [1]); E(cmp_imm, 0, 0); E(b_cond, "gk_v", "eq")
        E(push_list, [1]); E(movs_imm, 0, P0); E(movs_imm, 1, 0); E(bl, "c_gmp"); E(ldrb_imm, 0, 0, B_FLAGS); E(pop_list, [1])
        E(movs_imm, 2, 0xFE); E(raw, h(0x4010)); E(orrs_reg, 1, 0)                                 # ands r0, r2
        a.label("gk_v")
    E(movs_imm, 0, B_FLAGS); E(bl, "c_gmput")
    if V2:                                                                                         # off: the number view closed
        E(cmp_imm, 4, 0); E(b_cond, "gk_s", "ne"); E(bl, "c_gmram"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_EDIT)
        a.label("gk_s")
    E(bl, "c_gmsave"); E(b, "gk_x")
    a.label("gk_n"); E(cmp_imm, 5, K_D1); E(b_cond, "gk_f", "lo"); E(subs_imm8, 5, K_D1)            # r5 = the drum
    if V2: E(bl, "c_gmon_q"); E(cmp_imm, 0, 0); E(b_cond, "gk_x", "eq")                             # the mode off: nothing
    E(bl, "c_gmram"); E(adds_reg, 7, 0, 5)                                                         # r7 + 8 = its accumulator
    E(ldrb_imm, 0, 7, 8); E(raw, h(0xB240)); E(adds_reg, 0, 0, 6)                                  # sxtb r0, r0: + delta
    E(movs_imm, 4, 0)                                                                              # r4 = the notes to move
    a.label("gk_a")
    E(cmp_imm, 0, CLICKS); E(b_cond, "gk_b", "lt"); E(subs_imm8, 0, CLICKS); E(adds_imm8, 4, 1); E(b, "gk_a")
    a.label("gk_b")
    E(mov_reg, 1, 0); E(adds_imm8, 1, CLICKS); E(cmp_imm, 1, 0); E(b_cond, "gk_c", "gt"); E(adds_imm8, 0, CLICKS); E(subs_imm8, 4, 1); E(b, "gk_b")
    a.label("gk_c"); E(strb_imm, 0, 7, 8)
    E(cmp_imm, 4, 0); E(b_cond, "gk_e", "eq")
    E(mov_reg, 0, 5); E(bl, "c_gmnote"); E(adds_reg, 1, 0, 4)                                      # the new note, kept in range
    E(cmp_imm, 1, NMIN); E(b_cond, "gk_l", "ge"); E(movs_imm, 1, NMIN)
    a.label("gk_l"); E(cmp_imm, 1, NMAX); E(b_cond, "gk_h", "le"); E(movs_imm, 1, NMAX)
    a.label("gk_h"); E(cmp_reg, 1, 0); E(b_cond, "gk_e", "eq"); E(mov_reg, 7, 1)
    E(mov_reg, 0, 5); E(adds_imm8, 0, 16); E(bl, "c_gmput")
    imm32(0, TX); E(movs_imm, 1, DRUMS); E(mov_reg, 2, 7); E(movs_imm, 3, PREVIEW_VEL); E(bl, prev["on"])   # it sounds once (the chain under ours)
    imm32(0, TX); E(movs_imm, 1, DRUMS); E(mov_reg, 2, 7); E(movs_imm, 3, 0); E(bl, prev["off"])
    a.label("gk_e"); E(bl, "c_gmram"); E(adds_imm8, 5, 1); E(strb_imm, 5, 0, O_EDIT)               # its number on the pads until confirmed
    a.label("gk_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("gk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_gmpad (the Setup view's slot 0: view, pad, velocity): nothing while a number is shown
    a.label("c_gmpad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, "c_gmram"); E(ldrb_imm, 0, 0, O_EDIT); E(cmp_imm, 0, 0); E(b_cond, "gp_f", "eq")
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("gp_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["pad"])

    # ---- c_gmled (the LED task calls: ctrl, frame): the chain; a number shown: Shift or out of the Setup view = confirmed (the save asked);
    #      the Setup view (not Advanced): K4 and K5..K8, and the number on the pads
    a.label("c_gmled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_gmram"); E(mov_reg, 7, 0); E(ldrb_imm, 4, 7, O_EDIT)                                   # r4 = 1 + the drum edited, or 0
    E(bl, "c_gmsetup"); E(mov_reg, 6, 0)
    E(cmp_imm, 4, 0); E(b_cond, "gl_n", "eq")
    E(cmp_imm, 6, 0); E(b_cond, "gl_c", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "gl_n", "eq")
    a.label("gl_c"); E(movs_imm, 4, 0); E(strb_imm, 4, 7, O_EDIT); E(bl, "c_gmsave")
    a.label("gl_n"); E(cmp_imm, 6, 0); E(b_cond, "gl_x", "eq")
    E(bl, "c_gmon_q"); E(mov_reg, 6, 0)                                                            # r6 = the mode
    E(movs_imm, 7, 0)
    if V2: E(cmp_imm, 6, 0); E(b_cond, "gl_k4", "eq")                                               # off: K5..K8 the stock's
    a.label("gl_l")
    E(mov_reg, 0, 7); E(bl, "c_gmnote"); E(subs_imm8, 0, NMIN - 1); E(lsls_imm, 0, 0, 1)            # brightness 2 .. 94
    E(cmp_imm, 6, 0); E(b_cond, "gl_b", "ne"); E(movs_imm, 0, 6)                                     # off: dim
    a.label("gl_b"); E(lsls_imm, 0, 0, 8)
    imm32(1, DC); E(lsls_imm, 2, 7, 3); E(lsrs_reg, 1, 2); E(movs_imm, 2, 0xFF); E(ands_reg, 1, 2); E(orrs_reg, 0, 1)   # the drum's colour
    E(lsls_imm, 1, 7, 1); E(adds_imm8, 1, 2 * (60 + K_D1)); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "gl_l", "lo")
    if V2: a.label("gl_k4")
    imm32(0, 0x2000 | COL_OFF); E(cmp_imm, 6, 0); E(b_cond, "gl_t", "eq"); imm32(0, 0x7F00 | COL_ON)
    a.label("gl_t"); E(movs_imm, 1, 2 * (60 + K_TOG)); E(strh_reg, 0, 5, 1)
    E(cmp_imm, 4, 0); E(b_cond, "gl_x", "eq")
    E(subs_imm8, 4, 1)
    imm32(6, DC); E(lsls_imm, 2, 4, 3); E(lsrs_reg, 6, 2); E(movs_imm, 2, 0xFF); E(ands_reg, 6, 2)  # r6 = its colour
    E(mov_reg, 0, 4); E(bl, "c_gmnote"); E(mov_reg, 1, 0); E(mov_reg, 2, 6); E(mov_reg, 0, 5); E(bl, L["c_ednum"])
    a.label("gl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the transmitter's note-on / note-off entries, the Setup view's slots 0 / 4, the LED task calls."""
    import ct_fw
    import leds18
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_ednum=lab("vcf20", "c_ednum"))
    prev = dict(on=u(TX_VT) & ~1, off=u(TX_VT + 4) & ~1, knob=u(PG.SETUP_VT + 16) & ~1, pad=u(PG.SETUP_VT) & ~1,
                ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    dc = leds18.drum_codes(img)
    assert all(c < 0x100 for c in dc), dc
    code, labels = arm_code(base_addr, prev, L, struct.unpack("<I", bytes(dc))[0])
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    from thumb import bl as bl_enc
    struct.pack_into("<I", img, TX_VT - BASE, labels["c_gmon"] | 1)
    struct.pack_into("<I", img, TX_VT + 4 - BASE, labels["c_gmoff"] | 1)
    struct.pack_into("<I", img, PG.SETUP_VT - BASE, labels["c_gmpad"] | 1)
    struct.pack_into("<I", img, PG.SETUP_VT + 16 - BASE, labels["c_gmknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_gmled"])
    return labels, code, prev
