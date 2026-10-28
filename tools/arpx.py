"""SC47.2 / Beta 3.29 (issues #13 / #14 of the public repository, brought by the user, 2026-10-26: «user wants arpeggiator to work with external midi
input. Also, when you press a step and arpeggiator is active, the step pre-listen runs through the arp» · «additional feature: with shift+note (if
available) the note is latched until next press of such note»; issue #14, ledlaux: the external keyboard through the arp «should be toggleable …
default setting should be like it is now»): the arpeggiator's input from a held step and from an external keyboard, and Shift + note = latch.

  * The held step's audition (transport stopped: 0x0804AD50): pressing a step, the view's slot 9 (0x0804B1F2, an event of [view + 0x14] for each
    micro step) plays the units starting there (0x0804AF7E, the call at 0x0804AFE8); the track view's store listener (0x0804B272) plays a unit
    that appears or whose note changes while the step is held (0x0804B4CC; 0x0804B580, the live note-on, which the arpeggiator left alone) and
    stops them (0x0804B39E, 0x0804B438); letting go of the step stops them at 0x0804B06A (0x0804B00C); all through the view's note interface.  Now they go through the arpeggiator's input like held pads (c_xin /
    c_xout: the first note sounds, a second one starts the arpeggio, the LED task steps it at the tempo), without the recorder (the step has them).
    If the transport starts while a step is held, the stock never sends its note-offs: the LED task lets go of those notes when no step is held.
  * An external keyboard (the MIDI-in listener 0x080592E0, heads in front of kbin's): with the toggle on, a note on the channel of Synth 1 / 2 or
    MIDI 1 / 2 whose arpeggiator is on goes into its input as a held pad would: the first sounds as always (through the listener), the next ones
    are held (to the recorder by us) and arpeggiated; the first is stopped through the listener's chain when the arpeggio takes it (c_xvoff, in
    place of the arpeggiator's call to c_arvoff, which only stops what the track view started).  Internal injections are left alone.  The toggle:
    Advanced Setup, pad 22 (green on / dim off; the stock ignores the pads there), bit 2 of gmdrum's flags byte, saved with the unit's settings.
  * Latch (the note tracks' view, slots 0 / 1): Shift + a key (no step held) = the note sounds and its release is ignored: it keeps sounding (and
    stays among the arpeggiator's held notes: an arpeggio latch); the next press of that note (any pad that holds or shows it, with or without
    Shift) stops it, and that press does nothing else.  Where the stock or the mod uses Shift + pad (the chord screen's pad 8, the sample picker)
    those take it first (they are in front, on the container).  With Shift held in a Note view the keys light yellow, the latched ones green.
RAM: modmx.MXR + 0x700 ("ARX1", 120 B: the listener, the external first note per track and its state, the latch bits (16 B a track), the
releases to ignore, the audition's notes (6 a track)).  In the hole (no card; the toggle's save is gmdrum's, through lazysave).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, blx_reg, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   lsls_imm, lsls_reg, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm,
                   strb_reg, strb_w, strh_imm, tst_reg)
import modmx as MX  # noqa: E402
import arp as A  # noqa: E402
import gmdrum as G  # noqa: E402
import pgmch as PG  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import chords as CH  # noqa: E402

XR = MX.MXR + 0x700
SIG = 0x31585241                                         # "ARX1"
O_THIS, O_XF, O_XS, O_LB, O_EAT, O_AUD, RSZ = 4, 8, 12, 16, 80, 96, 120
XS_ON, XS_STOP = 1, 3                                    # the external first note: sounding / stopped by us (its release ignored)
F_ARX = 0x04                                             # bit 2 of gmdrum's flags byte
PAD_ARX = 21                                             # pad 22
COL_ON, COL_OFF = 0x17, 0x02
COL_AV, COL_LAT = 0x2D, 0x17                             # with Shift: a key yellow, a latched note green
NOLATCHLED = False                                       # SC48.3 (use_nolatchled)
LATCHCYAN = False                                        # SC48.4 (use_latchcyan)
COL_CYAN = 0x4D                                          # (LATCHCYAN) bright cyan, steady (0x4E dim, 0x4F blinks)


def use_nolatchled():
    """SC48.3 / Beta 3.40 (the user, 2026-10-28: «on note latch toggle (shift+any pad) dont change the color of the keyboard or the held notes,
    just make the pad white like it does now with no yellow or green»): c_ltleds is not put in the container's slot 7: with Shift the keys keep
    their colours (a note that sounds lights white, the stock's)."""
    global NOLATCHLED
    NOLATCHLED = True


def use_latchcyan():
    """SC48.4 / Beta 3.41 (the user, 2026-10-28: «interface fix: make hold notes bright cyan on shift layout», «latched notes», «only when shift
    held»): c_ltleds back in the container's slot 7, but only the latched notes' keys change: bright cyan while Shift is held; the other keys
    keep their colours (use_nolatchled's rule)."""
    global LATCHCYAN
    LATCHCYAN = True
LIS_VT = 0x080592E0                                      # the MIDI-in listener: + 0 note-on, + 4 note-off (this, track, note, velocity)
CTX, INJ = 0x200069E4, 0x20                              # [[CTX] + 0x14] bit 5 = an internal injection
TV_VT = 0x0805A064                                       # the note tracks' views: slot 0 a pad (view, pad, vel), slot 1 let go (view, pad)
CONT_VT = 0x0805A62C                                     # their container: slot 7 the LED buffer
VIEW0, VIEW_SZ = 0x200412E0, 0x2F4
MGR, S_CUR = 0x20040B10, 0x152                           # [ctrl + 0x152] = 9 t + 1: the Note view; 9 t + 6: the expanded one
PAD_IDX, KEY_SKIP = 0x0804B174, 0x080523E8
LIVE_OFF = 0x0804AF5A                                    # (view, pad): the stock's let-go (the arpeggiator's c_arloff in front)
PARAM_GET = 0x0803542C
HAL_TICK = 0x2000081C
# the held step's audition (0x0804B272): the four calls and their bytes
AU_A, AU_A_OLD = 0x0804B39E, bytes.fromhex("d3f804c0e047")        # ldr.w ip, [r3, #4]; blx ip   (r0 ifc, r1 note, r2 pad; r4 = the view)
AU_B, AU_B_OLD = 0x0804B438, bytes.fromhex("dcf80490c847")        # ldr.w sb, [ip, #4]; blx sb
AU_C, AU_C_OLD = 0x0804B4CC, bytes.fromhex("d0f800c0dcf80090c847")    # ldr.w ip, [r0]; ldr.w sb, [ip]; blx sb  (r6 = the view)
AU_D = 0x0804B580                                        # bl 0x0804B07A (view, note, vel, pad)
AU_E, AU_E_OLD = 0x0804AFE8, bytes.fromhex("d0f800c0dcf800902146c847")   # ldr.w ip, [r0]; ldr.w sb, [ip]; mov r1, r4; blx sb  (r7 = the view)
AU_F, AU_F_OLD = 0x0804B06A, bytes.fromhex("5f68b847")                   # ldr r7, [r3, #4]; blx r7  (r0 ifc, r1 note, r2 pad, r3 its vtable)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def str_w_(rt, rn, off): return h(0xF8C0 | rn) + h(rt << 12 | off)
def ldr_w_(rt, rn, off): return h(0xF8D0 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    S = A

    # ---- c_xram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_xram")
    imm32(0, XR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "xr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 2, 4)
    a.label("xr_l"); E(raw, h(0x5081)); E(adds_imm8, 2, 4); E(cmp_imm, 2, RSZ); E(b_cond, "xr_l", "lo")   # str r1, [r0, r2]
    a.label("xr_x"); E(raw, RET)

    # ---- c_xin(r0 = track, r1 = note, r2 = velocity, r3 = 1: to the recorder) -> r0 = 0 not the arpeggiator's, 2 the first note (it sounds), 1 held
    a.label("c_xin")
    E(push_list, [4, 5, 6, 7], lr=True); E(raw, h(0xB082))                              # sub sp, #8
    E(mov_reg, 7, 0); E(raw, h(0x9100)); E(raw, h(0x9201)); E(mov_reg, 6, 3)            # str r1, [sp]; str r2, [sp, #4]
    E(cmp_imm, 7, 3); E(b_cond, "xi_0", "hi")
    E(mov_reg, 0, 7); E(bl, L["c_arpat"]); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(bl, L["c_arcfg"]); E(lsls_imm, 0, 0, 24); E(b_cond, "xi_0", "pl")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_arst"]); E(cmp_imm, 0, 0); E(b_cond, "xi_0", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 5, 4, S.S_N)
    E(mov_reg, 0, 4); E(ldr_sp, 1, 0); E(ldr_sp, 2, 4); E(movs_imm, 3, 0); E(bl, L["c_arins"])
    E(cmp_imm, 5, 0); E(b_cond, "xi_2", "ne")
    E(ldr_sp, 1, 0); E(strb_imm, 1, 4, S.S_FIRST); E(movs_imm, 0, 2); E(b, "xi_x")        # the first note: as always
    a.label("xi_2")                                                                    # in the list now? (a full list ignores it)
    E(ldrb_imm, 2, 4, S.S_N); E(movs_imm, 3, 0)
    a.label("xi_f"); E(cmp_reg, 3, 2); E(b_cond, "xi_0", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 0, 0, S.S_NOTES); E(ldr_sp, 1, 0)
    E(cmp_reg, 0, 1); E(b_cond, "xi_in", "eq"); E(adds_imm8, 3, 1); E(b, "xi_f")
    a.label("xi_in")
    E(ldrb_imm, 0, 4, S.S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "xi_r", "mi")
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, S.S_FL); E(movs_imm, 0, 0); E(strb_imm, 0, 4, S.S_K); E(strb_imm, 0, 4, S.S_FG); E(strb_imm, 0, 4, S.S_FP)
    E(ldrb_imm, 0, 4, S.S_FIRST); E(strb_imm, 0, 4, S.S_PEND)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 4, S.S_NEXT)                  # stopped: the first step now
    if S.RATE: E(mov_reg, 0, 7); E(bl, L["c_arRt"]); E(movs_imm, 1, 6); E(muls, 0, 1); E(raw, strb_w_(0, 4, S.D_EXT + 6))
    a.label("xi_r")
    E(lsls_imm, 0, 6, 31); E(b_cond, "xi_1", "pl")
    imm32(0, S.REC); E(ldr_sp, 1, 0); E(ldr_sp, 2, 4); E(mov_reg, 3, 7); E(bl, S.REC_ON)
    a.label("xi_1"); E(movs_imm, 0, 1); E(b, "xi_x")
    a.label("xi_0"); E(movs_imm, 0, 0)
    a.label("xi_x"); E(raw, h(0xB002)); E(pop_list, [4, 5, 6, 7], pc=True)                 # add sp, #8

    # ---- c_xout(r0 = track, r1 = note, r2 = 1: to the recorder) -> r0 = 1 it was one of the held (not the first), else 0
    a.label("c_xout")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(movs_imm, 1, 1); E(bl, L["c_arst"]); E(cmp_imm, 0, 0); E(b_cond, "xo_z", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 2, 4, S.S_N); E(movs_imm, 3, 0)
    a.label("xo_f"); E(cmp_reg, 3, 2); E(b_cond, "xo_z", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 0, 0, S.S_NOTES)
    E(cmp_reg, 0, 5); E(b_cond, "xo_in", "eq"); E(adds_imm8, 3, 1); E(b, "xo_f")
    a.label("xo_in")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_ardel"])
    E(ldrb_imm, 0, 4, S.S_PEND); E(cmp_reg, 0, 5); E(b_cond, "xo_p", "ne"); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S.S_PEND)
    a.label("xo_p")
    E(ldrb_imm, 0, 4, S.S_FIRST); E(cmp_reg, 0, 5); E(b_cond, "xo_o", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S.S_FIRST); E(movs_imm, 5, 0); E(b, "xo_e")    # the first: its own note-off
    a.label("xo_o")
    E(lsls_imm, 0, 6, 31); E(b_cond, "xo_1", "pl")
    imm32(0, S.REC); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, S.REC_OFF)
    a.label("xo_1"); E(movs_imm, 5, 1)
    a.label("xo_e")                                                                    # none left: the arpeggio ends
    E(ldrb_imm, 0, 4, S.S_N); E(cmp_imm, 0, 0); E(b_cond, "xo_r", "ne")
    E(ldrb_imm, 0, 4, S.S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "xo_r", "pl")
    E(mov_reg, 0, 7); E(bl, L["c_arply"]); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(movs_imm, 3, 0); E(bl, L["c_arnext"])
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, S.S_FL)
    a.label("xo_r"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("xo_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xaud(r0 = track, r1 = note, r2 = 1 add / 0 remove): the audition's notes (6 a track, 0 = none); clobbers r0-r3
    a.label("c_xaud")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(push_list, [2]); E(bl, "c_xram"); E(pop_list, [2])
    E(movs_imm, 1, 6); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, O_AUD)       # r0 = the track's six
    E(movs_imm, 3, 0)
    a.label("xd_l"); E(ldrb_reg, 1, 0, 3); E(cmp_reg, 1, 5); E(b_cond, "xd_m", "eq"); E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "xd_l", "lo")
    E(cmp_imm, 2, 0); E(b_cond, "xd_x", "eq")                                          # not there: add it in a free place
    E(movs_imm, 3, 0)
    a.label("xd_e"); E(ldrb_reg, 1, 0, 3); E(cmp_imm, 1, 0); E(b_cond, "xd_w", "eq"); E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "xd_e", "lo"); E(b, "xd_x")
    a.label("xd_w"); E(raw, h(0x54C5)); E(b, "xd_x")                                    # strb r5, [r0, r3]
    a.label("xd_m"); E(cmp_imm, 2, 0); E(b_cond, "xd_x", "ne"); E(movs_imm, 1, 0); E(raw, h(0x54C1))   # strb r1, [r0, r3]
    a.label("xd_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_xau(r0 = view, r1 = note, r2 = velocity, r3 = pad): the audition's note-on (sites C / D) through the arpeggiator's input
    a.label("c_xau")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(mov_reg, 7, 3)
    E(ldr_imm, 0, 4, 0x18); E(ldrb_imm, 0, 0, 0xC); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(movs_imm, 3, 0); E(bl, "c_xin")
    E(cmp_imm, 0, 0); E(b_cond, "xa_s", "eq")
    E(push_list, [0]); E(ldr_imm, 0, 4, 0x18); E(ldrb_imm, 0, 0, 0xC); E(mov_reg, 1, 5); E(movs_imm, 2, 1); E(bl, "c_xaud"); E(pop_list, [0])
    E(cmp_imm, 0, 1); E(b_cond, "xa_p", "eq")                                          # held: no note-on
    a.label("xa_s")
    E(ldr_imm, 0, 4, 0x18); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0); E(mov_reg, 12, 3)
    E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(mov_reg, 3, 7); E(blx_reg, 12)               # the view's note interface: note-on
    a.label("xa_p"); E(adds_reg, 0, 4, 5); E(adds_imm8, 0, 0x80); E(strb_imm, 7, 0, 0)    # [view + 0x80 + note] = the pad
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xaA / c_xaB (sites A, F / B: r0 = the interface, r1 = note, r2 = pad; the slot in r3 / ip): out of the arpeggiator, then the stock's off
    a.label("c_xaA")
    E(raw, pushw([0, 1, 2, 3, 4], lr=True))
    E(ldrb_imm, 4, 0, 0xC); E(mov_reg, 0, 4); E(movs_imm, 2, 0); E(bl, "c_xout")
    E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(movs_imm, 2, 0); E(bl, "c_xaud")
    E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(ldr_imm, 3, 3, 4); E(raw, h(0x4718))        # bx r3
    a.label("c_xaB")
    E(raw, pushw([0, 1, 2, 3, 4, 12], lr=True))
    E(ldrb_imm, 4, 0, 0xC); E(mov_reg, 0, 4); E(movs_imm, 2, 0); E(bl, "c_xout")
    E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(movs_imm, 2, 0); E(bl, "c_xaud")
    E(raw, popw([0, 1, 2, 3, 4, 12], lr=True)); E(raw, ldr_w_(3, 12, 4)); E(raw, h(0x4718))

    # ---- c_xtog() -> r0 = 1 with the external input through the arpeggiator on; clobbers r1-r3
    a.label("c_xtog")
    E(raw, h(0xB500))
    E(bl, L["c_gmsig"]); E(cmp_imm, 0, 0); E(b_cond, "xt_0", "eq")
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 0, 0, G.B_FLAGS); E(movs_imm, 1, F_ARX); E(tst_reg, 0, 1)
    E(b_cond, "xt_0", "eq"); E(movs_imm, 0, 1); E(raw, h(0xBD00))
    a.label("xt_0"); E(movs_imm, 0, 0); E(raw, h(0xBD00))

    # ---- c_xinj() -> r0 != 0 for an internal injection; clobbers r1
    a.label("c_xinj")
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "xj_x", "eq")
    E(ldrb_imm, 0, 0, 0x14); E(movs_imm, 1, INJ); E(raw, h(0x4008))                      # ands r0, r1
    a.label("xj_x"); E(raw, RET)

    # ---- c_xkon (the listener's note-on: this, track, note, velocity), in front of kbin's
    a.label("c_xkon")
    E(cmp_imm, 1, 3); E(b_cond, "xk_f", "hi"); E(cmp_imm, 3, 0); E(b_cond, "xk_f", "eq")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_xtog"); E(cmp_imm, 0, 0); E(b_cond, "xk_p", "eq")
    E(bl, "c_xinj"); E(cmp_imm, 0, 0); E(b_cond, "xk_p", "ne")
    E(bl, "c_xram"); E(mov_reg, 4, 0); E(ldr_sp, 0, 0); E(str_imm, 0, 4, O_THIS)
    E(ldr_sp, 0, 4); E(ldr_sp, 1, 8); E(ldr_sp, 2, 12); E(movs_imm, 3, 1); E(bl, "c_xin")
    E(cmp_imm, 0, 1); E(b_cond, "xk_s", "eq"); E(cmp_imm, 0, 2); E(b_cond, "xk_p", "ne")
    E(ldr_sp, 1, 4); E(adds_reg, 2, 4, 1); E(ldr_sp, 0, 8); E(strb_imm, 0, 2, O_XF); E(movs_imm, 0, XS_ON); E(strb_imm, 0, 2, O_XS)
    a.label("xk_p"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    a.label("xk_f"); E(b_w, prev["lis_on"])
    a.label("xk_s"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(raw, RET)

    # ---- c_xkoff (the listener's note-off: this, track, note, velocity): ours swallowed (the recorder's note-off by us), the first as it was
    a.label("c_xkoff")
    E(cmp_imm, 1, 3); E(b_cond, "xf_f", "hi")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_xinj"); E(cmp_imm, 0, 0); E(b_cond, "xf_p", "ne")
    E(bl, "c_xram"); E(mov_reg, 4, 0); E(ldr_sp, 5, 4); E(ldr_sp, 6, 8); E(adds_reg, 7, 4, 5)
    E(ldrb_imm, 3, 7, O_XS); E(cmp_imm, 3, 0); E(b_cond, "xf_o", "eq"); E(ldrb_imm, 0, 7, O_XF); E(cmp_reg, 0, 6); E(b_cond, "xf_o", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, O_XS)                                         # the external first note
    E(push_list, [3]); E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(movs_imm, 2, 1); E(bl, "c_xout"); E(pop_list, [3])
    E(cmp_imm, 3, XS_STOP); E(b_cond, "xf_s", "eq"); E(b, "xf_p")
    a.label("xf_o"); E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(movs_imm, 2, 1); E(bl, "c_xout"); E(cmp_imm, 0, 0); E(b_cond, "xf_s", "ne")
    a.label("xf_p"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    a.label("xf_f"); E(b_w, prev["lis_off"])
    a.label("xf_s"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(raw, RET)

    # ---- c_xvoff(r0 = player, r1 = note): in c_arnext, the first held note stopped as the arpeggio takes over: an external one through the listener's
    #      chain behind us (kbin, the stock), the others through c_arvoff (the track view's interface)
    a.label("c_xvoff")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 0); E(mov_reg, 6, 1)
    E(bl, L["c_artrk"]); E(cmp_imm, 0, 3); E(b_cond, "xv_v", "hi"); E(mov_reg, 4, 0)
    E(bl, "c_xram"); E(adds_reg, 0, 0, 4)
    E(ldrb_imm, 1, 0, O_XS); E(cmp_imm, 1, XS_ON); E(b_cond, "xv_v", "ne"); E(ldrb_imm, 1, 0, O_XF); E(cmp_reg, 1, 6); E(b_cond, "xv_v", "ne")
    E(movs_imm, 1, XS_STOP); E(strb_imm, 1, 0, O_XS)
    E(bl, "c_xram"); E(ldr_imm, 0, 0, O_THIS); E(mov_reg, 1, 4); E(mov_reg, 2, 6); E(movs_imm, 3, 0); E(bl, prev["lis_off"])
    E(pop_list, [4, 5, 6], pc=True)
    a.label("xv_v"); E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(raw, popw([4, 5, 6], lr=True)); E(b_w, L["c_arvoff"])

    # ---- c_xspad (the Setup view's slot 0: view, pad, velocity): Advanced Setup, pad 22 = the external input through the arpeggiator on / off
    a.label("c_xspad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, PAD_ARX); E(b_cond, "xs_f", "ne")
    E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "xs_f", "eq")
    E(bl, L["c_gmsig"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "xs_w", "eq")       # no signature yet: the flags are 0
    E(movs_imm, 0, G.P0); E(movs_imm, 1, 0); E(bl, L["c_gmp"]); E(ldrb_imm, 1, 0, G.B_FLAGS)
    a.label("xs_w"); E(movs_imm, 0, F_ARX); E(raw, h(0x4041))                          # eors r1, r0
    E(movs_imm, 0, G.B_FLAGS); E(bl, L["c_gmput"]); E(bl, L["c_gmsave"])
    E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("xs_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["setup_pad"])

    # ---- c_xled (the LED task calls: ctrl, frame): the chain; Advanced Setup: pad 22; a track whose step was let go while playing: its audition out
    a.label("c_xled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    imm32(0, MGR); E(ldr_imm, 0, 0, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "xl_a", "ne")
    imm32(0, PG.SETUP_OBJ); E(ldrb_w, 0, 0, PG.ADV_OFF); E(cmp_imm, 0, 0); E(b_cond, "xl_a", "eq")
    E(movs_imm, 4, COL_ON); E(bl, "c_xtog"); E(cmp_imm, 0, 0); E(b_cond, "xl_w", "ne"); E(movs_imm, 4, COL_OFF)
    a.label("xl_w"); E(strh_imm, 4, 5, 2 * PAD_ARX)
    a.label("xl_a")
    E(movs_imm, 6, 0)
    a.label("xl_t")
    E(bl, "c_xram"); E(movs_imm, 1, 6); E(muls, 1, 6); E(adds_reg, 4, 0, 1); E(adds_imm8, 4, O_AUD)   # r4 = the track's six
    E(movs_imm, 7, 0)
    a.label("xl_q"); E(ldrb_reg, 0, 4, 7); E(cmp_imm, 0, 0); E(b_cond, "xl_h", "ne"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 6); E(b_cond, "xl_q", "lo"); E(b, "xl_n")
    a.label("xl_h")                                                                    # some: is a step still held on its view?
    imm32(0, VIEW_SZ); E(muls, 0, 6); imm32(1, VIEW0); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0x2C); E(movs_imm, 1, 0); E(bl, PARAM_GET)
    E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "xl_n", "ne")
    E(movs_imm, 7, 0)
    a.label("xl_o"); E(ldrb_reg, 1, 4, 7); E(cmp_imm, 1, 0); E(b_cond, "xl_oo", "eq")
    E(mov_reg, 0, 6); E(movs_imm, 2, 0); E(bl, "c_xout"); E(movs_imm, 0, 0); E(strb_reg, 0, 4, 7)
    a.label("xl_oo"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 6); E(b_cond, "xl_o", "lo")
    a.label("xl_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "xl_t", "lo")
    E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_ltbit(r0 = track, r1 = note) -> r0 = the latch byte's address, r1 = its mask; clobbers r2
    a.label("c_ltbit")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_xram")
    E(lsls_imm, 1, 4, 4); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, O_LB); E(lsrs_imm, 1, 5, 3); E(adds_reg, 0, 0, 1)
    E(movs_imm, 2, 7); E(raw, h(0x402A)); E(movs_imm, 1, 1); E(lsls_reg, 1, 2)          # ands r2, r5
    E(pop_list, [4, 5], pc=True)

    # ---- c_lteat(r0 = track, r1 = pad): its release ignored; clobbers r0-r3
    a.label("c_lteat")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_xram")
    E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 1, 0, O_EAT); E(movs_imm, 2, 1); E(lsls_reg, 2, 5); E(orrs_reg, 1, 2); E(str_imm, 1, 0, O_EAT)
    E(pop_list, [4, 5], pc=True)

    # ---- c_ltpad (the note tracks' view, slot 0: view, pad, velocity): Shift + a key latches its note; a latched note's next press stops it
    a.label("c_ltpad")
    E(cmp_imm, 1, 31); E(b_cond, "lp_f", "hi")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(ldr_imm, 0, 0, 0x2C); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "lp_p", "ne")   # a step held: the stock's
    E(ldr_sp, 4, 0); E(ldr_imm, 0, 4, 0x18); E(ldrb_imm, 5, 0, 0xC); E(cmp_imm, 5, 3); E(b_cond, "lp_p", "hi")
    E(ldr_sp, 1, 4); E(adds_reg, 0, 4, 1); E(ldrb_w, 7, 0, 0x40); E(cmp_imm, 7, 0); E(b_cond, "lp_k", "eq")   # the pad still holds a note
    E(mov_reg, 0, 5); E(mov_reg, 1, 7); E(bl, "c_ltbit"); E(ldrb_imm, 2, 0, 0); E(tst_reg, 2, 1); E(b_cond, "lp_k", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 0, 0); E(ldr_sp, 6, 4); E(b, "lp_u")              # latched there: stop it
    a.label("lp_k")                                                                    # the note the pad shows
    E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(bl, PAD_IDX); E(mov_reg, 6, 0); E(ldr_imm, 0, 4, 0x38); E(mov_reg, 1, 6); E(bl, KEY_SKIP)
    E(cmp_imm, 0, 0); E(b_cond, "lp_p", "ne")
    E(ldr_imm, 0, 4, 0x38); E(adds_reg, 0, 0, 6); E(ldrb_imm, 7, 0, 0x14); E(cmp_imm, 7, 0); E(b_cond, "lp_p", "eq")   # r7 = the note
    E(mov_reg, 0, 5); E(mov_reg, 1, 7); E(bl, "c_ltbit"); E(ldrb_imm, 2, 0, 0); E(tst_reg, 2, 1); E(b_cond, "lp_sh", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 0, 0)                                            # latched: the pad that holds it
    E(movs_imm, 6, 0)
    a.label("lp_fd"); E(adds_reg, 0, 4, 6); E(ldrb_w, 0, 0, 0x40); E(cmp_reg, 0, 7); E(b_cond, "lp_u", "eq")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "lp_fd", "lo"); E(b, "lp_p")            # none (a load cleared it): the press as always
    a.label("lp_u")                                                                    # r6 = the pad holding it: its let-go, this press and release ignored
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, LIVE_OFF)
    E(mov_reg, 0, 5); E(ldr_sp, 1, 4); E(bl, "c_lteat")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(raw, RET)
    a.label("lp_sh"); E(push_list, [0, 1]); E(bl, L["c_shift"]); E(mov_reg, 3, 0); E(pop_list, [0, 1]); E(cmp_imm, 3, 0); E(b_cond, "lp_p", "eq")
    E(ldrb_imm, 2, 0, 0); E(orrs_reg, 2, 1); E(strb_imm, 2, 0, 0)                       # Shift: latched, its release ignored, the press as always
    E(mov_reg, 0, 5); E(ldr_sp, 1, 4); E(bl, "c_lteat")
    a.label("lp_p"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    a.label("lp_f"); E(b_w, prev["tv_pad"])

    # ---- c_ltrel (the view's slot 1: view, pad): a release to ignore
    a.label("c_ltrel")
    E(cmp_imm, 1, 31); E(b_cond, "lr_f", "hi")
    E(push_list, [0, 1, 4], lr=True)
    E(ldr_imm, 0, 0, 0x18); E(ldrb_imm, 4, 0, 0xC); E(cmp_imm, 4, 3); E(b_cond, "lr_p", "hi")
    E(bl, "c_xram"); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 2, 0, O_EAT); E(ldr_sp, 1, 4); E(movs_imm, 3, 1); E(lsls_reg, 3, 1)
    E(tst_reg, 2, 3); E(b_cond, "lr_p", "eq")
    E(bics_reg, 2, 3); E(str_imm, 2, 0, O_EAT); E(pop_list, [0, 1, 4], pc=True)
    a.label("lr_p"); E(raw, popw([0, 1, 4], lr=True))
    a.label("lr_f"); E(b_w, prev["tv_rel"])

    # ---- c_ltleds (the container's slot 7: obj) -> r0 = the LED buffer: with Shift, in a Note view of a note track, its keys yellow, latched green
    a.label("c_ltleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["cont_leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "ll_x", "eq")
    imm32(1, MGR + S_CUR); E(ldrb_imm, 1, 1, 0); E(movs_imm, 4, 0)
    a.label("ll_t"); E(movs_imm, 0, 9); E(muls, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 1, 0); E(b_cond, "ll_nv", "eq")
    E(adds_imm8, 0, 5); E(cmp_reg, 1, 0); E(b_cond, "ll_ex", "eq")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 4); E(b_cond, "ll_t", "lo"); E(b, "ll_x")
    a.label("ll_nv"); E(movs_imm, 6, 16); E(b, "ll_go")                                  # the Note view: pads 17-32
    a.label("ll_ex")                                                                   # the expanded one: not the sample picker, the split, the chord screen
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); E(b_cond, "ll_x", "ne")
    E(bl, L["c_s4on"]); E(cmp_imm, 0, 0); E(b_cond, "ll_x", "ne")
    imm32(0, CH.CR); E(ldr_imm, 1, 0, 0); imm32(2, CH.RSIG); E(cmp_reg, 1, 2); E(b_cond, "ll_e0", "ne")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, CH.O_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "ll_x", "mi")
    a.label("ll_e0"); E(movs_imm, 6, 0)
    a.label("ll_go")
    imm32(0, VIEW_SZ); E(muls, 0, 4); imm32(1, VIEW0); E(adds_reg, 7, 0, 1)            # r7 = the view
    a.label("ll_q")
    E(mov_reg, 0, 7); E(mov_reg, 1, 6); E(bl, PAD_IDX); E(mov_reg, 1, 0); E(push_list, [1]); E(ldr_imm, 0, 7, 0x38); E(bl, KEY_SKIP); E(pop_list, [1])
    E(cmp_imm, 0, 0); E(b_cond, "ll_n", "ne")
    E(ldr_imm, 0, 7, 0x38); E(adds_reg, 0, 0, 1); E(ldrb_imm, 1, 0, 0x14); E(cmp_imm, 1, 0); E(b_cond, "ll_n", "eq")
    if LATCHCYAN:                                                                      # (LATCHCYAN) a latched key cyan, the others as they are
        E(mov_reg, 0, 4); E(bl, "c_ltbit"); E(ldrb_imm, 0, 0, 0); E(tst_reg, 0, 1); E(b_cond, "ll_n", "eq"); E(movs_imm, 2, COL_CYAN)
    else:
        E(mov_reg, 0, 4); E(bl, "c_ltbit"); E(ldrb_imm, 0, 0, 0); E(movs_imm, 2, COL_AV); E(tst_reg, 0, 1); E(b_cond, "ll_w", "eq"); E(movs_imm, 2, COL_LAT)
    a.label("ll_w"); E(lsls_imm, 0, 6, 1); E(raw, h(0x522A))                               # strh r2, [r5, r0]
    a.label("ll_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 32); E(b_cond, "ll_q", "lo")
    a.label("ll_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)


def bl_target(img, at, base):
    h1, h2 = struct.unpack_from("<HH", img, at - base)
    if h1 & 0xF800 != 0xF000 or h2 & 0xD000 != 0xD000: return None
    s = (h1 >> 10) & 1; imm10 = h1 & 0x3FF; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1; imm11 = h2 & 0x7FF
    i1 = 1 - (j1 ^ s); i2 = 1 - (j2 ^ s)
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s: off -= 1 << 25
    return at + 4 + off


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the audition's six calls, the arpeggiator's call to c_arvoff, the listener's slots 0 / 1, the note tracks'
    view slots 0 / 1, the container's slot 7, the Setup view's slot 0, the LED task calls."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    assert A.VIEWOFF and A.PRESSORD, "the arpeggiator with use_viewoff / use_pressord"
    L = {k: lab("arp", k) for k in ("c_arst", "c_arins", "c_ardel", "c_arnext", "c_arply", "c_arpat", "c_arcfg", "c_artrk", "c_arvoff")}
    if A.RATE: L["c_arRt"] = lab("arp", "c_arRt")
    L.update({k: lab("gmdrum", k) for k in ("c_gmsig", "c_gmp", "c_gmput", "c_gmsave")})
    L.update(c_shift=lab("sc15", "c_shift"), c_spk=lab("smpick", "c_spk"), c_s4on=lab("split4", "c_s4on"))
    prev = dict(lis_on=u(LIS_VT) & ~1, lis_off=u(LIS_VT + 4) & ~1, tv_pad=u(TV_VT) & ~1, tv_rel=u(TV_VT + 4) & ~1, cont_leds=u(CONT_VT + 28) & ~1,
                setup_pad=u(PG.SETUP_VT) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["lis_on"] == lab("kbin", "c_kbon") and prev["lis_off"] == lab("kbin", "c_kboff"), "kbin first"
    assert prev["tv_pad"] == 0x0804AB5A, hex(prev["tv_pad"])
    for at, old in ((AU_A, AU_A_OLD), (AU_B, AU_B_OLD), (AU_C, AU_C_OLD), (AU_E, AU_E_OLD), (AU_F, AU_F_OLD)):
        assert bytes(img[at - BASE:at - BASE + len(old)]) == old, hex(at)
    assert bl_target(img, AU_D, BASE) == A.LIVE_ON, hex(AU_D)
    arnext = L["c_arnext"]
    voff = [x for x in range(arnext, arnext + 64, 2) if bl_target(img, x, BASE) == L["c_arvoff"]]
    assert len(voff) == 1, voff
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert XR + RSZ <= MX.MXR + 0x800
    NOP = h(0xBF00)
    def put(at, data): img[at - BASE:at - BASE + len(data)] = data
    put(AU_A, bl_enc(AU_A, labels["c_xaA"]) + NOP)
    put(AU_B, bl_enc(AU_B, labels["c_xaB"]) + NOP)
    put(AU_C, h(0x4630) + bl_enc(AU_C + 2, labels["c_xau"]) + NOP + NOP)                   # mov r0, r6 (the view); bl
    put(AU_D, bl_enc(AU_D, labels["c_xau"]))
    put(AU_E, h(0x4638) + h(0x4621) + bl_enc(AU_E + 4, labels["c_xau"]) + NOP + NOP)       # mov r0, r7; mov r1, r4; bl
    put(AU_F, bl_enc(AU_F, labels["c_xaA"]))
    put(voff[0], bl_enc(voff[0], labels["c_xvoff"]))
    struct.pack_into("<I", img, LIS_VT - BASE, labels["c_xkon"] | 1)
    struct.pack_into("<I", img, LIS_VT + 4 - BASE, labels["c_xkoff"] | 1)
    struct.pack_into("<I", img, TV_VT - BASE, labels["c_ltpad"] | 1)
    struct.pack_into("<I", img, TV_VT + 4 - BASE, labels["c_ltrel"] | 1)
    if LATCHCYAN or not NOLATCHLED: struct.pack_into("<I", img, CONT_VT + 28 - BASE, labels["c_ltleds"] | 1)
    struct.pack_into("<I", img, PG.SETUP_VT - BASE, labels["c_xspad"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_xled"])
    return labels, code, prev
