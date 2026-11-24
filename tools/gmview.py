"""Alpha 7.16 (the user, 2026-11-20: «a new page, "global macro view"» -> «the view (up+down) makes every knob adress their same position.  After
touching a knob, an interface allow us to select which tracks are adressed» -> pads 1-8, the tracks' main knobs («Midi 1/2 on the first assigned
controls page (pad1, also called page 4)»), no tracks by default, per project, no Preset shortcut -> opened with «mixer+patterns»).

  * Mixer + Patterns together (the second pressed while the first is held) = the macro view on / off; the second press and its release go nowhere,
    the first is the stock's (its view comes up underneath).  On: a tap of Mixer or Patterns alone, or any other button but Record, Play, Clear and
    Duplicate, closes it (and is the stock's).
  * On: knob Kn (K1-K8) = the same event on knob n of every track linked to it: the track's knob handler (the track views' container,
    [0x20040DB8 + 0x148 + 4 t], slot 4: what the track's own knobs do); MIDI 1 / 2 on the own synth's page 4 (vcf21's page 3, set for the call and
    put back: the assigned controls, pad 1); the knob becomes the selected one.  The master filter knob: the stock's.
  * On: pads 1-8 = Synth 1, Synth 2, MIDI 1, MIDI 2, Drum 1-4 for the selected knob, in the stock's track colours (0x08056464: [1 + t] bright =
    linked, [9 + t] dim = not); a tap toggles; pads 9-32 dark and do nothing (a pad pressed in the view is released in it too).
  * LEDs (a head of the LED task, LR / frame in RAM): the pads; a knob linked = the colour of its first track, full (the selected one) or dimmer;
    the selected knob unlinked = dim white; Mixer and Patterns white (the mode's indicator).
  * Saved with the project: bytes 8..17 of the settings of MIDI 2's pattern 8 (projsyn 0..4, wtui 5 / 6; free): 0xD7, the 8 masks, the sum ^ 0xA5;
    written by a head of the save call (when a mask is set or the block is ours), read by a head of the load's re-send (no block = none linked).
RAM GM = 0x2004F5C0 (28 B, free: S514D's map, after patchain's PCL): + 0 "GMV1", + 4 on, + 5 the selected knob, + 6 Patterns / Mixer held, + 7 the
release to drop, + 8 the masks, + 16 the LED head's LR, + 20 the frame, + 24 the pads pressed in the view.  Code in dspz's first gap."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bics_reg, bl, blx_reg, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm,  # noqa: E402
                   ldrh_reg, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm,
                   strh_reg, subs_imm8, subs_reg, tst_reg)
import fxdiag as FD  # noqa: E402
import packio as PK  # noqa: E402
import persist19 as P19  # noqa: E402
import projsyn as PS  # noqa: E402
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402

GM = 0x2004F5C0
SIG = struct.unpack("<I", b"GMV1")[0]
O_SIG, O_ON, O_LAST, O_HELD, O_SWAL, O_M, O_LR, O_FR, O_PADS = 0, 4, 5, 6, 7, 8, 16, 20, 24
PAT_BTN, MIX_BTN = 13, 14
PASS = (16, 17, 23, 24)                                 # Record, Play, Clear, Duplicate: the view stays
PAD, PADUP, KNOB = 0x08033282, 0x080332FE, 0x08033848
CONT, HANDLERS = 0x20040DB8, 0x148
COLS = 0x08056464                                       # the stock's colour table (u16): [1 + t] a track's colour, [9 + t] its dim one
KNOB_LED, LED_BTN = 60, 32                              # the panel frame: knobs 60..67 (colour | (v + 2) << 8), buttons 32 + id
COL_WHITE, BR_SEL, BR_ON, BR_IDLE = 0x01, 129, 48, 24
MIDI_PAGE = 3                                           # vcf21's page 3 = page 4 (pad 1: the assigned controls)
RESEND_CALL = 0x0802F5B4
BSIG = 0xD7
BLK = PS.AREA + PS.PSIZE * (8 + 7) + PS.SET + PS.BYTE0  # MIDI 2's pattern 8, settings + 8
assert GM + 28 <= 0x2004F600
ROWS = False                                            # Alpha 7.17 (use_rows)
MIXV, MIX_KNOB, MIX_PAGE = 0x200447D4, 0x080466C4, 0xAD  # the Mixer view, its stock knob handler, its page byte (0 levels, 1 pans)
FXV = 0x200443B4                                        # the FX view: [+ 0xC] the delay sends' sub-view, [+ 0x10] the reverb sends'
BSIG2, OLD_BLK = 0xD8, 4                                # (ROWS) the block's signature; 7.16's block (0xD7, 8 masks, sum) at its + 4
COMPAT = True                                           # (ROWS) a 7.16 project's links load into row 1
DIMLED = False                                          # Alpha 7.18 (use_dimled)
PAGE2 = False                                           # Alpha 7.46 (use_page2)
O_PG, O_P2 = 52, 53
P2COL = False                                           # Alpha 7.47 (use_page2col)
O_MX = 56                                               # (P2COL) the grid: 4 rows (K5, pan, K3, K8) x bit = knob
OCT_DN, OCT_UP = 19, 20


def use_dimled():
    """Alpha 7.18 (the user, on 7.17 on the device: «the knob leds don't seem to paint much difference» -> «Clearer states only»): a linked knob
    that is not the picked one in its first track's dim colour (the stock table's [9 + t]) at full brightness instead of its colour at a third;
    the picked one stays full in the bright colour, an unlinked one off, the picked unlinked dim white.  The same size."""
    global DIMLED
    DIMLED = True


def use_rows():
    """Alpha 7.17 (the user, 2026-11-20: «Add level, reverb, delay»): pads 9-16 / 17-24 / 25-32 = the eight tracks' Mixer level / reverb send /
    delay send for the selected knob, as pads 1-8 are their main knobs (bright = linked, a tap toggles).  A level = the stock Mixer handler
    (0x080466C4, the Mixer view with its levels page set for the call: not Master FX, not the pans, not the cue); a send = the FX view's send
    sub-view, slot 4 (the chain: fxparams, fxcap's cap with the returns on strips 3 / 4, the stock).  Knob strip k = track k in both views.
    The masks: 4 rows x 8 knobs (+ 8 r + k); RAM GM + 8..39, then LR 40, frame 44, pads 48 (signed "GMV2").  Saved: the masks in bytes 8..39 of
    MIDI 2's pattern 8 settings, the signature 0xD8 and the sum ^ 0xA5 in its bytes 4 / 5 (free with the group chains; patchain.use_keep46
    keeps Clear off them); a 7.16 block (0xD7 at byte 8) loads into row 1."""
    global ROWS, O_LR, O_FR, O_PADS, SIG, BLK
    ROWS = True
    O_LR, O_FR, O_PADS = 40, 44, 48
    SIG = struct.unpack("<I", b"GMV2")[0]
    BLK = PS.AREA + PS.PSIZE * (8 + 7) + PS.SET + 4
    assert GM + O_PADS + 4 <= 0x2004F600


def use_page2():
    """Alpha 7.46 (the user, 2026-11-24; the roadmap: «a second page for the global macro view», «One page, pads pick»): in the view, Octave
    up = page 2, Octave down = page 1 (the lit one is the way to the other; their presses and releases go nowhere).  Page 2: knob Kn = track n
    (K1 Synth 1 .. K8 Drum 4), pads 1-4 pick what they move: 1 the track's K5 (cutoff), 2 its pan (the Mixer's pans page), 3 its K3 (envelope),
    4 its K8 (FX); MIDI 1 / 2 on page 4 as in page 1; the picked pad white, the other three dim, the rest dark; the knobs in their tracks'
    colours.  Opening the view = page 1.  RAM + 52 the page, + 53 the pick (signed "GMV3": a state from before starts clean)."""
    global PAGE2
    PAGE2 = True                                        # (the signature and the ROWS check in arm_code: use_rows runs later in the chain)


def use_page2col():
    """Alpha 7.47 (the user, on 7.46 on the device: «Each knob gets their own column. The lit pads signal wether that knob adresses same
    track's k5, pan, k3 and k8 on their macros»): page 2 is a grid: column n = knob Kn = track n (K1 Synth 1 .. K8 Drum 4); row 1 = the
    track's K5 (cutoff), row 2 its pan, row 3 its K3 (envelope), row 4 its K8 (FX); a pad lit (the track's bright colour; dim = off) = that
    knob moves that parameter; a tap toggles; a knob moves every lit row of its column at once.  The knob LEDs: the tracks' colours (as 7.46).  The grid in RAM (GM + 56..59, a byte per row), kept across loads, cleared with the state ("GMV4")."""
    global P2COL, COMPAT
    use_page2()
    P2COL = True
    COMPAT = False                                      # (room) 7.16's one-row block no longer loaded: a 7.16 project opens with no links


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrbw(rt, rn, imm): return h(0xF890 | rn) + h(rt << 12 | imm)   # ldrb.w (offsets past 31)
def strbw(rt, rn, imm): return h(0xF880 | rn) + h(rt << 12 | imm)
def str_lr(rn): return h(0xF8C0 | rn) + h(0xE000)          # str.w lr, [rn]


def arm_code(base, L, prev):
    global SIG
    if PAGE2:
        assert ROWS, "page 2 needs use_rows"
        SIG = struct.unpack("<I", b"GMV4" if P2COL else b"GMV3")[0]
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_gmst() -> r0 = GM, set up the first time; clobbers r1, r2
    a.label("c_gmst")
    imm32(0, GM); E(ldr_imm, 1, 0, O_SIG); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_ok", "eq")
    if ROWS:
        E(str_imm, 2, 0, O_SIG); E(movs_imm, 1, 0); E(str_imm, 1, 0, O_ON); E(str_imm, 1, 0, O_PADS)
        if PAGE2: E(str_imm, 1, 0, O_PG)
        if P2COL: E(str_imm, 1, 0, O_MX)
        E(adds_imm8, 0, O_M); E(movs_imm, 2, 8)
        a.label("st_z"); E(raw, h(0xC002)); E(subs_imm8, 2, 1); E(b_cond, "st_z", "ne")      # stm r0!, {r1}
        imm32(0, GM)
    else:
        E(str_imm, 2, 0, O_SIG); E(movs_imm, 1, 0); E(str_imm, 1, 0, O_ON); E(str_imm, 1, 0, O_M); E(str_imm, 1, 0, O_M + 4); E(str_imm, 1, 0, O_PADS)
    a.label("st_ok"); E(raw, RET)

    # ---- c_gmbtn (ctrl, id): the head of the button presses
    a.label("c_gmbtn")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, "c_gmst"); E(mov_reg, 4, 0)
    E(mov_reg, 0, 5); E(subs_imm8, 0, PAT_BTN); E(cmp_imm, 0, 1); E(b_cond, "bt_oth", "hi")
    E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(movs_imm, 2, 3); E(eors_reg, 2, 1)       # r1 = its bit, r2 = the other's
    E(ldrb_imm, 3, 4, O_HELD); E(tst_reg, 3, 2); E(b_cond, "bt_hold", "eq")
    E(bics_reg, 3, 2); E(strb_imm, 3, 4, O_HELD)                                     # the chord: the first one's release goes on as it is
    E(ldrb_imm, 0, 4, O_ON); E(movs_imm, 2, 1); E(eors_reg, 0, 2); E(strb_imm, 0, 4, O_ON)
    if PAGE2: E(movs_imm, 2, 0); E(raw, strbw(2, 4, O_PG))
    E(ldrb_imm, 0, 4, O_SWAL); E(orrs_reg, 0, 1); E(strb_imm, 0, 4, O_SWAL)
    E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("bt_hold"); E(orrs_reg, 3, 1); E(strb_imm, 3, 4, O_HELD); E(b, "bt_prev")
    a.label("bt_oth")
    E(ldrb_imm, 0, 4, O_ON); E(cmp_imm, 0, 0); E(b_cond, "bt_prev", "eq")
    if PAGE2:                                                                          # Octave: the pages
        E(movs_imm, 0, 1); E(cmp_imm, 5, OCT_UP); E(b_cond, "bt_pg", "eq")
        E(movs_imm, 0, 0); E(cmp_imm, 5, OCT_DN); E(b_cond, "bt_pgn", "ne")
        a.label("bt_pg"); E(raw, strbw(0, 4, O_PG)); E(pop_list, [0, 1, 4, 5], pc=True)
        a.label("bt_pgn")
    for k in PASS:
        E(cmp_imm, 5, k); E(b_cond, "bt_prev", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_ON)
    a.label("bt_prev"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_gmrel (ctrl, id): the head of the button releases
    a.label("c_gmrel")
    E(push_list, [0, 1, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, "c_gmst"); E(mov_reg, 4, 0)
    if PAGE2:
        E(ldrb_imm, 0, 4, O_ON); E(cmp_imm, 0, 0); E(b_cond, "rl_np", "eq")
        E(mov_reg, 0, 5); E(subs_imm8, 0, OCT_DN); E(cmp_imm, 0, 1); E(b_cond, "rl_np", "hi")
        E(pop_list, [0, 1, 4, 5], pc=True)
        a.label("rl_np")
    E(mov_reg, 0, 5); E(subs_imm8, 0, PAT_BTN); E(cmp_imm, 0, 1); E(b_cond, "rl_prev", "hi")
    E(movs_imm, 1, 1); E(lsls_reg, 1, 0)
    E(ldrb_imm, 2, 4, O_SWAL); E(tst_reg, 2, 1); E(b_cond, "rl_h", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 4, O_SWAL)                                     # the chord's second: dropped
    E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("rl_h")
    E(ldrb_imm, 2, 4, O_HELD); E(tst_reg, 2, 1); E(b_cond, "rl_prev", "eq")
    E(bics_reg, 2, 1); E(strb_imm, 2, 4, O_HELD)
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_ON)                                       # Mixer / Patterns alone: the view closes
    a.label("rl_prev"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["rel"])

    # ---- c_gmknob (ctrl, knob, delta): the head of the knob entry
    a.label("c_gmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_gmst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, O_ON); E(cmp_imm, 0, 0); E(b_cond, "kn_prev", "eq")
    E(cmp_imm, 5, 8); E(b_cond, "kn_prev", "hs")
    if not P2COL: E(strb_imm, 5, 4, O_LAST)
    if PAGE2:                                                                          # page 2: knob n = track n, the picked parameter
        E(raw, ldrbw(0, 4, O_PG)); E(cmp_imm, 0, 0); E(b_cond, "kn_p1", "eq")
        if P2COL:                                                                      # the grid: every lit row of this knob's column
            E(movs_imm, 7, 0)
            a.label("kg_l")
            E(adds_reg, 0, 4, 7); E(raw, ldrbw(0, 0, O_MX)); E(lsrs_reg, 0, 5); E(lsls_imm, 0, 0, 31); E(b_cond, "kg_n", "eq")
            E(mov_reg, 0, 7); E(bl, "c_gmp2")
            a.label("kg_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "kg_l", "lo")
            E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
            a.label("c_gmp2")                                                          # r0 = the row, r5 = the knob / track, r6 = the delta
            E(push_list, [4, 7], lr=True)
            E(cmp_imm, 0, 1); E(b_cond, "kn_pan", "eq")
        else:
            E(raw, ldrbw(0, 4, O_P2)); E(cmp_imm, 0, 1); E(b_cond, "kn_pan", "eq")
        E(movs_imm, 1, 4); E(cmp_imm, 0, 0); E(b_cond, "kn_go", "eq")
        E(movs_imm, 1, 2); E(cmp_imm, 0, 2); E(b_cond, "kn_go", "eq")
        E(movs_imm, 1, 7)
        a.label("kn_go"); E(mov_reg, 0, 5); E(mov_reg, 2, 6); E(bl, "c_gmcall"); E(b, "kn_end")
        a.label("kn_pan")                                                              # the pan: the stock Mixer handler on its pans page
        imm32(7, MIXV + MIX_PAGE); E(ldrb_imm, 0, 7, 0); E(push_list, [0]); E(movs_imm, 0, 1); E(strb_imm, 0, 7, 0)
        E(mov_reg, 0, 7); E(subs_imm8, 0, MIX_PAGE); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, MIX_KNOB)
        E(pop_list, [0]); E(strb_imm, 0, 7, 0)
        a.label("kn_end")
        if P2COL: E(pop_list, [4, 7], pc=True)
        else: E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
        a.label("kn_p1")
        if P2COL: E(strb_imm, 5, 4, O_LAST)                                           # (the grid's knobs leave page 1's pick alone)
    if ROWS:                                                                           # r7 = 8 row + track, over the four rows
        E(movs_imm, 7, 0)
        a.label("kn_l")
        E(lsrs_imm, 0, 7, 3); E(lsls_imm, 0, 0, 3); E(adds_reg, 0, 0, 5); E(adds_reg, 0, 4, 0); E(ldrb_imm, 0, 0, O_M)   # the row's mask
        E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 29); E(lsrs_reg, 0, 1); E(lsls_imm, 0, 0, 31); E(b_cond, "kn_n", "eq")
        E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_gmcall")
        a.label("kn_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "kn_l", "lo")
    else:
        E(adds_reg, 0, 4, 5); E(ldrb_imm, 7, 0, O_M)                                   # r7 = the knob's tracks
        E(movs_imm, 4, 0)
        a.label("kn_l")
        E(movs_imm, 0, 1); E(lsls_reg, 0, 4); E(tst_reg, 7, 0); E(b_cond, "kn_n", "eq")
        E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, "c_gmcall")
        a.label("kn_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 8); E(b_cond, "kn_l", "lo")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_gmcall(r0 track, r1 knob, r2 delta): the track's knob handler (MIDI 1 / 2: on page 4 for the call)
    a.label("c_gmcall")
    E(push_list, [4, 5, 6, 7], lr=True)
    if ROWS:                                                                           # r0 = 8 row + track
        E(mov_reg, 5, 1); E(mov_reg, 6, 2)
        E(lsls_imm, 4, 0, 29); E(lsrs_imm, 4, 4, 29); E(lsrs_imm, 3, 0, 3)               # r4 = the track, r3 = the row
        E(cmp_imm, 3, 1); E(b_cond, "gc_lv", "eq"); E(b_cond, "gc_fx", "hi")
    else:
        E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    imm32(0, CONT + HANDLERS); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1); E(ldr_imm, 7, 0, 0)
    E(cmp_imm, 7, 0); E(b_cond, "gc_x", "eq")
    E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(cmp_imm, 0, 1); E(b_cond, "gc_c", "hi")
    E(bl, L["c_vpage"]); E(push_list, [0])                                            # MIDI: the page now
    E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(movs_imm, 1, MIDI_PAGE); E(bl, L["c_vsetpage"])
    E(bl, "gc_go")
    E(pop_list, [1]); E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(bl, L["c_vsetpage"])     # and back
    E(b, "gc_x")
    if ROWS:
        a.label("gc_lv")                                                               # the level: the stock Mixer handler on its levels page
        imm32(7, MIXV + MIX_PAGE); E(ldrb_imm, 0, 7, 0); E(push_list, [0]); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 0)
        E(mov_reg, 0, 7); E(subs_imm8, 0, MIX_PAGE); E(mov_reg, 1, 4); E(mov_reg, 2, 6); E(bl, MIX_KNOB)
        E(pop_list, [0]); E(strb_imm, 0, 7, 0); E(b, "gc_x")
        a.label("gc_fx")                                                               # a send: the sub-view's slot 4 (reverb + 0x10, delay + 0xC)
        E(lsls_imm, 3, 3, 2); E(movs_imm, 0, 0x18); E(subs_reg, 0, 0, 3); imm32(1, FXV); E(raw, h(0x5808))   # ldr r0, [r1, r0]
        E(movs_imm, 7, 0); E(adds_reg, 7, 7, 0); E(b_cond, "gc_x", "eq"); E(mov_reg, 5, 4)
    a.label("gc_c"); E(bl, "gc_go")
    a.label("gc_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("gc_go")                                                                   # handler slot 4 (handler, knob, delta)
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(ldr_imm, 3, 0, 0); E(ldr_imm, 3, 3, 0x10); E(raw, h(0x4718))   # bx r3 (returns to gc_go's caller)

    # ---- c_gmpad (ctrl, pad, velocity): the head of the pad presses
    a.label("c_gmpad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, "c_gmst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, O_ON); E(cmp_imm, 0, 0); E(b_cond, "pd_prev", "eq")
    E(raw, h(0x9901)); E(cmp_imm, 1, 32); E(b_cond, "pd_prev", "hs")                   # ldr r1, [sp, #4]: the pad
    E(movs_imm, 0, 1); E(lsls_reg, 0, 1); E(ldr_imm, 2, 4, O_PADS); E(orrs_reg, 2, 0); E(str_imm, 2, 4, O_PADS)
    if PAGE2:                                                                          # page 2: pads 1-4 pick, the rest nothing
        E(raw, ldrbw(0, 4, O_PG)); E(cmp_imm, 0, 0); E(b_cond, "pd_p1", "eq")
        if P2COL:                                                                      # the grid: row = pad / 8, column = pad % 8
            E(lsrs_imm, 2, 1, 3); E(adds_reg, 2, 4, 2); E(lsls_imm, 3, 1, 29); E(lsrs_imm, 3, 3, 29)
            E(movs_imm, 0, 1); E(lsls_reg, 0, 3); E(raw, ldrbw(3, 2, O_MX)); E(eors_reg, 3, 0); E(raw, strbw(3, 2, O_MX)); E(b, "pd_x")
        else:
            E(cmp_imm, 1, 4); E(b_cond, "pd_x", "hs"); E(raw, strbw(1, 4, O_P2)); E(b, "pd_x")
        a.label("pd_p1")
    if ROWS:                                                                           # pad = 8 row + track: that row's mask of the knob
        E(lsrs_imm, 2, 1, 3); E(lsls_imm, 2, 2, 3); E(ldrb_imm, 3, 4, O_LAST); E(adds_reg, 2, 2, 3); E(adds_reg, 2, 4, 2)
        E(lsls_imm, 3, 1, 29); E(lsrs_imm, 3, 3, 29); E(movs_imm, 0, 1); E(lsls_reg, 0, 3)
    else:
        E(cmp_imm, 1, 8); E(b_cond, "pd_x", "hs")
        E(ldrb_imm, 2, 4, O_LAST); E(adds_reg, 2, 4, 2)
    E(ldrb_imm, 3, 2, O_M); E(eors_reg, 3, 0); E(strb_imm, 3, 2, O_M)
    a.label("pd_x"); E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["pad"])

    # ---- c_gmpadup (ctrl, pad): the head of the pad releases: a pad pressed in the view is released in it
    a.label("c_gmpadup")
    E(push_list, [0, 1, 4], lr=True)
    E(bl, "c_gmst"); E(mov_reg, 4, 0)
    E(raw, h(0x9901)); E(cmp_imm, 1, 32); E(b_cond, "pu_prev", "hs")
    E(movs_imm, 0, 1); E(lsls_reg, 0, 1); E(ldr_imm, 2, 4, O_PADS); E(tst_reg, 2, 0); E(b_cond, "pu_prev", "eq")
    E(bics_reg, 2, 0); E(str_imm, 2, 4, O_PADS)
    E(pop_list, [0, 1, 4], pc=True)
    a.label("pu_prev"); E(raw, popw([0, 1, 4], lr=True)); E(b_w, prev["padup"])

    # ---- c_gmled (the LED task calls: ctrl, frame): the chain first, nothing of ours on the stack; then the view over it
    a.label("c_gmled")
    imm32(2, GM + O_LR); E(raw, str_lr(2)); E(str_imm, 1, 2, O_FR - O_LR)
    E(bl, prev["led"])
    E(push_list, [4, 5, 6, 7])
    E(bl, "c_gmst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, O_ON); E(cmp_imm, 0, 0)
    if P2COL: E(b_cond, "ld_on", "ne"); E(b, "ld_x"); a.label("ld_on")              # (the grid makes the function longer than a short branch)
    else: E(b_cond, "ld_x", "eq")
    E(ldr_imm, 5, 4, O_FR)
    if PAGE2:
        E(raw, ldrbw(0, 4, O_PG)); E(cmp_imm, 0, 0); E(b_cond, "ld_p1", "eq")
        E(movs_imm, 7, 0)
        if P2COL:
            a.label("ld_q")                                                            # the grid: lit = the track's bright colour, else its dim one
            E(lsrs_imm, 6, 7, 3); E(adds_reg, 6, 4, 6); E(raw, ldrbw(6, 6, O_MX))
            E(lsls_imm, 2, 7, 29); E(lsrs_imm, 2, 2, 29); E(lsrs_reg, 6, 2); E(movs_imm, 1, 9); E(lsls_imm, 6, 6, 31); E(b_cond, "ld_qc", "eq"); E(movs_imm, 1, 1)
            a.label("ld_qc"); E(adds_reg, 1, 1, 2); E(lsls_imm, 1, 1, 1); imm32(3, COLS); E(ldrh_reg, 0, 3, 1)
            E(lsls_imm, 1, 7, 1); E(strh_reg, 0, 5, 1); E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "ld_q", "lo")
        else:
            a.label("ld_q")                                                            # pads: 1-4 the picks (white / dim), the rest dark
            E(movs_imm, 0, 0); E(cmp_imm, 7, 4); E(b_cond, "ld_qw", "hs"); E(movs_imm, 0, 2)
            E(raw, ldrbw(1, 4, O_P2)); E(cmp_reg, 7, 1); E(b_cond, "ld_qw", "ne"); E(movs_imm, 0, 1)
            a.label("ld_qw"); E(lsls_imm, 1, 7, 1); E(strh_reg, 0, 5, 1); E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "ld_q", "lo")
        E(movs_imm, 7, 0)
        a.label("ld_q2")                                                               # knobs: their tracks' colours
        E(movs_imm, 1, 1); E(adds_reg, 1, 1, 7); E(lsls_imm, 1, 1, 1); imm32(2, COLS); E(ldrh_reg, 0, 2, 1)
        E(movs_imm, 2, BR_SEL); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2)
        E(lsls_imm, 1, 7, 1); E(adds_imm8, 1, 2 * KNOB_LED); E(strh_reg, 0, 5, 1)
        E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ld_q2", "lo")
        E(movs_imm, 0, COL_WHITE); E(movs_imm, 1, 2 * (LED_BTN + OCT_DN)); E(strh_reg, 0, 5, 1)
        E(movs_imm, 0, 0); E(adds_imm8, 1, 2); E(strh_reg, 0, 5, 1)
        E(b, "ld_btn")
        a.label("ld_p1")
    if ROWS:                                                                           # the 32 pads: row = pad / 8, track = pad % 8
        E(movs_imm, 7, 0)
        a.label("ld_p")
        E(lsrs_imm, 6, 7, 3); E(lsls_imm, 6, 6, 3); E(ldrb_imm, 0, 4, O_LAST); E(adds_reg, 6, 6, 0); E(adds_reg, 6, 4, 6); E(ldrb_imm, 6, 6, O_M)
        E(lsls_imm, 2, 7, 29); E(lsrs_imm, 2, 2, 29)
        E(movs_imm, 0, 1); E(lsls_reg, 0, 2); E(movs_imm, 1, 9); E(tst_reg, 6, 0); E(b_cond, "ld_pc", "eq"); E(movs_imm, 1, 1)
        a.label("ld_pc")
        E(adds_reg, 1, 1, 2); E(lsls_imm, 1, 1, 1); imm32(3, COLS); E(ldrh_reg, 0, 3, 1)
        E(lsls_imm, 1, 7, 1); E(strh_reg, 0, 5, 1)
        E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "ld_p", "lo")
    else:
        E(ldrb_imm, 6, 4, O_LAST); E(adds_reg, 6, 4, 6); E(ldrb_imm, 6, 6, O_M)        # r6 = the selected knob's tracks
        E(movs_imm, 7, 0)
        a.label("ld_p")
        E(movs_imm, 0, 1); E(lsls_reg, 0, 7); E(movs_imm, 1, 9); E(tst_reg, 6, 0); E(b_cond, "ld_pc", "eq"); E(movs_imm, 1, 1)
        a.label("ld_pc")
        E(adds_reg, 1, 1, 7); E(lsls_imm, 1, 1, 1); imm32(2, COLS); E(ldrh_reg, 0, 2, 1)
        E(lsls_imm, 1, 7, 1); E(strh_reg, 0, 5, 1)
        E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ld_p", "lo")
        E(movs_imm, 0, 0); E(movs_imm, 1, 16)
        a.label("ld_z"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 64); E(b_cond, "ld_z", "lo")
    E(movs_imm, 7, 0)
    a.label("ld_k")
    E(adds_reg, 0, 4, 7); E(ldrb_imm, 6, 0, O_M)
    if ROWS:                                                                           # linked = in any row
        for r in (1, 2, 3): E(adds_imm8, 0, 8); E(ldrb_imm, 1, 0, O_M); E(orrs_reg, 6, 1)
    E(ldrb_imm, 3, 4, O_LAST)                                                           # r3 = the selected knob
    E(cmp_imm, 6, 0); E(b_cond, "ld_kl", "ne")
    E(movs_imm, 0, 0); E(cmp_reg, 7, 3); E(b_cond, "ld_kw", "ne")
    E(movs_imm, 0, BR_IDLE); E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, COL_WHITE); E(b, "ld_kw")
    a.label("ld_kl")
    E(movs_imm, 1, 0)
    a.label("ld_b"); E(movs_imm, 2, 1); E(lsls_reg, 2, 1); E(tst_reg, 6, 2); E(b_cond, "ld_bf", "ne"); E(adds_imm8, 1, 1); E(b, "ld_b")
    a.label("ld_bf")
    if DIMLED:                                                                         # (use_dimled) not the picked one: the dim colour, full
        E(adds_imm8, 1, 1); E(cmp_reg, 7, 3); E(b_cond, "ld_bs", "eq"); E(adds_imm8, 1, 8)
        a.label("ld_bs"); E(lsls_imm, 1, 1, 1); imm32(2, COLS); E(ldrh_reg, 0, 2, 1)
        E(movs_imm, 2, BR_SEL)
    else:
        E(adds_imm8, 1, 1); E(lsls_imm, 1, 1, 1); imm32(2, COLS); E(ldrh_reg, 0, 2, 1)
        E(movs_imm, 2, BR_ON); E(cmp_reg, 7, 3); E(b_cond, "ld_kb", "ne"); E(movs_imm, 2, BR_SEL)
    a.label("ld_kb"); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2)
    a.label("ld_kw"); E(lsls_imm, 1, 7, 1); E(adds_imm8, 1, 2 * KNOB_LED); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ld_k", "lo")
    if PAGE2:                                                                          # page 1: Octave up lit (the way to page 2)
        E(movs_imm, 0, 0); E(movs_imm, 1, 2 * (LED_BTN + OCT_DN)); E(strh_reg, 0, 5, 1)
        E(movs_imm, 0, COL_WHITE); E(adds_imm8, 1, 2); E(strh_reg, 0, 5, 1)
        a.label("ld_btn")
    E(movs_imm, 0, COL_WHITE); E(movs_imm, 1, 2 * (LED_BTN + PAT_BTN)); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(strh_reg, 0, 5, 1)
    a.label("ld_x")
    E(pop_list, [4, 5, 6, 7])
    imm32(2, GM + O_LR); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))                         # bx r2

    # ---- c_gmblk() -> r0 = the project's block (MIDI 2's pattern 8, settings + 8), 0 = no record; clobbers r1
    a.label("c_gmblk")
    imm32(0, PS.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq")
    imm32(1, BLK); E(adds_reg, 0, 0, 1)
    a.label("bk_x"); E(raw, RET)

    if ROWS:
        # ---- c_gmsum(r0 = 32 bytes) -> r0 = their sum ^ 0xA5, a byte; clobbers r1-r3
        a.label("c_gmsum")
        E(movs_imm, 1, 0); E(movs_imm, 2, 32)
        a.label("su_l"); E(ldrb_imm, 3, 0, 0); E(adds_reg, 1, 1, 3); E(adds_imm8, 0, 1); E(subs_imm8, 2, 1); E(b_cond, "su_l", "ne")
        E(movs_imm, 0, 0xA5); E(eors_reg, 0, 1); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24); E(raw, RET)

        # ---- c_gmsave (the bl of the stock save): the masks into the record (a mask set, or the block ours), then the chain
        a.label("c_gmsave")
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
        E(bl, "c_gmst"); E(mov_reg, 4, 0)
        E(bl, "c_gmblk"); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq"); E(mov_reg, 5, 0)
        E(movs_imm, 6, 0); E(movs_imm, 7, 0)
        a.label("sv_o"); E(adds_reg, 0, 4, 7); E(ldr_imm, 0, 0, O_M); E(orrs_reg, 6, 0); E(adds_imm8, 7, 4); E(cmp_imm, 7, 32); E(b_cond, "sv_o", "lo")
        E(cmp_imm, 6, 0); E(b_cond, "sv_w", "ne")
        E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, BSIG2); E(b_cond, "sv_x", "ne")
        a.label("sv_w")
        E(movs_imm, 0, BSIG2); E(strb_imm, 0, 5, 0)
        E(mov_reg, 0, 4); E(adds_imm8, 0, O_M); E(bl, "c_gmsum"); E(strb_imm, 0, 5, 1)
        E(movs_imm, 7, 0)
        a.label("sv_l"); E(adds_reg, 0, 4, 7); E(ldrb_imm, 0, 0, O_M); E(adds_reg, 1, 5, 7); E(strb_imm, 0, 1, 4); E(adds_imm8, 7, 1); E(cmp_imm, 7, 32); E(b_cond, "sv_l", "lo")
        a.label("sv_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["save"])

        # ---- c_gmload (the load's re-send: a load, a new project, power-up): the masks from the block (7.16's into row 1), or none; the view closed
        a.label("c_gmload")
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
        E(bl, "c_gmst"); E(mov_reg, 4, 0)
        E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_ON); E(strb_imm, 0, 4, O_LAST)
        E(mov_reg, 1, 4); E(adds_imm8, 1, O_M); E(movs_imm, 2, 8)
        a.label("lo_z"); E(raw, h(0xC101)); E(subs_imm8, 2, 1); E(b_cond, "lo_z", "ne")      # stm r1!, {r0}
        E(bl, "c_gmblk"); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq"); E(mov_reg, 5, 0)
        E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, BSIG2); E(b_cond, "lo_old" if COMPAT else "lo_x", "ne")
        E(mov_reg, 0, 5); E(adds_imm8, 0, 4); E(bl, "c_gmsum"); E(ldrb_imm, 1, 5, 1); E(cmp_reg, 0, 1); E(b_cond, "lo_x", "ne")
        E(movs_imm, 6, 32); E(movs_imm, 2, 4)
        a.label("lo_cp")                                                               # r6 bytes from block + r2
        E(movs_imm, 7, 0)
        a.label("lo_c"); E(adds_reg, 1, 5, 7); E(adds_reg, 1, 1, 2); E(ldrb_imm, 0, 1, 0); E(adds_reg, 1, 4, 7); E(strb_imm, 0, 1, O_M)
        E(adds_imm8, 7, 1); E(cmp_reg, 7, 6); E(b_cond, "lo_c", "lo")
        if COMPAT:
            E(b, "lo_x")
            a.label("lo_old")                                                          # 7.16's block at + OLD_BLK: 0xD7, 8 masks, sum ^ 0xA5
            E(ldrb_imm, 0, 5, OLD_BLK); E(cmp_imm, 0, BSIG); E(b_cond, "lo_x", "ne")
            E(movs_imm, 6, 0); E(movs_imm, 7, 0)
            a.label("lo_s"); E(adds_reg, 1, 5, 7); E(ldrb_imm, 0, 1, OLD_BLK + 1); E(adds_reg, 6, 6, 0); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "lo_s", "lo")
            E(movs_imm, 0, 0xA5); E(eors_reg, 6, 0); E(lsls_imm, 6, 6, 24); E(lsrs_imm, 6, 6, 24)
            E(ldrb_imm, 0, 5, OLD_BLK + 9); E(cmp_reg, 0, 6); E(b_cond, "lo_x", "ne")
            E(movs_imm, 6, 8); E(movs_imm, 2, OLD_BLK + 1); E(b, "lo_cp")
        a.label("lo_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["resend"])
    else:
        # ---- c_gmsave (the bl of the stock save): the masks into the record (a mask set, or the block ours), then the chain
        a.label("c_gmsave")
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
        E(bl, "c_gmst"); E(mov_reg, 4, 0)
        E(bl, "c_gmblk"); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq"); E(mov_reg, 5, 0)
        E(ldr_imm, 0, 4, O_M); E(ldr_imm, 1, 4, O_M + 4); E(orrs_reg, 0, 1); E(b_cond, "sv_w", "ne")
        E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, BSIG); E(b_cond, "sv_x", "ne")
        a.label("sv_w")
        E(movs_imm, 0, BSIG); E(strb_imm, 0, 5, 0); E(movs_imm, 6, 0); E(movs_imm, 7, 0)
        a.label("sv_l")
        E(adds_reg, 0, 4, 7); E(ldrb_imm, 0, 0, O_M); E(adds_reg, 6, 6, 0); E(adds_reg, 1, 5, 7); E(strb_imm, 0, 1, 1)
        E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "sv_l", "lo")
        E(movs_imm, 0, 0xA5); E(eors_reg, 6, 0); E(strb_imm, 6, 5, 9)
        a.label("sv_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["save"])

        # ---- c_gmload (the load's re-send: a load, a new project, power-up): the masks from the block, or none; the view closed
        a.label("c_gmload")
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
        E(bl, "c_gmst"); E(mov_reg, 4, 0)
        E(movs_imm, 0, 0); E(str_imm, 0, 4, O_M); E(str_imm, 0, 4, O_M + 4); E(strb_imm, 0, 4, O_ON); E(strb_imm, 0, 4, O_LAST)
        E(bl, "c_gmblk"); E(cmp_imm, 0, 0); E(b_cond, "lo_x", "eq"); E(mov_reg, 5, 0)
        E(ldrb_imm, 0, 5, 0); E(cmp_imm, 0, BSIG); E(b_cond, "lo_x", "ne")
        E(movs_imm, 6, 0); E(movs_imm, 7, 0)
        a.label("lo_s"); E(adds_reg, 1, 5, 7); E(ldrb_imm, 0, 1, 1); E(adds_reg, 6, 6, 0); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "lo_s", "lo")
        E(movs_imm, 0, 0xA5); E(eors_reg, 6, 0); E(lsls_imm, 6, 6, 24); E(lsrs_imm, 6, 6, 24)
        E(ldrb_imm, 0, 5, 9); E(cmp_reg, 0, 6); E(b_cond, "lo_x", "ne")
        E(movs_imm, 7, 0)
        a.label("lo_c"); E(adds_reg, 1, 5, 7); E(ldrb_imm, 0, 1, 1); E(adds_reg, 1, 4, 7); E(strb_imm, 0, 1, O_M); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "lo_c", "lo")
        a.label("lo_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["resend"])
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap): heads of the button press / release, pad press / release and knob entries, the LED
    task calls, the save call and the load's re-send."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    v = report["vcf20"]["labels"]
    L = dict(c_vpage=int(v["c_vpage"], 16), c_vsetpage=int(v["c_vsetpage"], 16))
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), rel=MP.bw_target(img, SV.BTN_REL, BASE), pad=MP.bw_target(img, PAD, BASE),
                padup=MP.bw_target(img, PADUP, BASE), knob=MP.bw_target(img, KNOB, BASE), led=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                save=FD.bl_target(img, P19.SAVE_CALL, BASE), resend=FD.bl_target(img, RESEND_CALL, BASE))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["led"]
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for at, lb in ((SV.BTN, "c_gmbtn"), (SV.BTN_REL, "c_gmrel"), (PAD, "c_gmpad"), (PADUP, "c_gmpadup"), (KNOB, "c_gmknob")):
        img[at - BASE:at - BASE + 4] = b_w(at, labels[lb])
    for c in PK.LED_CALLS:
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_gmled"])
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_gmsave"])
    img[RESEND_CALL - BASE:RESEND_CALL - BASE + 4] = bl(RESEND_CALL, labels["c_gmload"])
    report["gmview"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()}, ram=hex(GM))
    return labels, code, prev
