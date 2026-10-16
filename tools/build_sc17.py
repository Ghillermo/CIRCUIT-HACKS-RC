"""Circuit Tracks 4486 — SC17 = SC16 + Master FX view (Mixer pressed again while in Mixer).

UI:
  * In the Mixer view, press Mixer again -> Master FX view; press Mixer again -> back to the Mixer.
    Entering the Mixer from another view always opens the normal Mixer.  Shift + Mixer is untouched.
  * Master FX view, top row (pads 1-6): Gater, Auto-Filter LP, Auto-Filter HP, Digitise, Phaser, Vinyl.
    Hold = on while held; Shift + pad = latch on / off.  The last pad pressed is "selected":
    its pad in row 2 lights up and knobs 1-4 edit its parameters (both Auto-Filters share one set):
      Gater        K1 rate (1/1..1/32, synced)   K2 depth      K3 duty       K4 softness
      Auto-Filter  K1 rate (4 bars..1/16)        K2 depth      K3 resonance  K4 centre frequency
      Digitise     K1 sample-rate reduction      K2 bit depth
      Phaser       K1 rate (20 s .. 0.1 s)       K2 depth      K3 feedback   K4 mix
      Vinyl        K1 crackle                    K2 hiss       K3 tone (LP)  K4 wear (HP)
    Not saved (power-up: defaults, all off).  Latched effects keep running outside the view;
    held effects stop when the view is left.

DSP: tools/masterfx_dsp.py, master insert at P:$274 (after the master filter, before the compressor),
appended after SC16's code in the relocated core-0 program.  Parameters at X:$3A40.., cleared by sc_init.
ARM: state in the heap-top reservation (SC14 24 B + SC16 16 B + Master FX 128 B); LFOs and parameter
writes in the DSP service tick (chained before SC14's c_gtick).
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_sc14 as s14  # noqa: E402
GFX_SIZE = 128
s14.ST -= GFX_SIZE                    # build_sc16 lowers it by 16 more at import
import build_sc16 as s16  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc10 as s10  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import dsp56 as D  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cbz, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, str_imm, strb_imm, adds_imm8, subs_imm8, adds_reg, subs_reg,
                   ands_reg, orrs_reg, bics_reg, tst_reg, eors_reg, muls, strh_imm, raw, h, ldrb_w, strb_w, ldrb_reg, ldrh_reg,
                   lsls_reg, lsrs_reg)

BASE = ct_fw.APP_BASE
NAME = "SC17"
MARKER = b"SC17"

# ---------------- DSP
s16.CLR_N = G.FX_END - s16.CLR_FROM   # sc_init clears X:$3A00..$3A7F
_dsp16 = s16.dsp_code


def dsp_code_17(base):                # SC16 words, then the Master FX code
    w16, l16 = _dsp16(base)
    wg, lg = G.code(base + len(w16))
    return w16 + wg, {**l16, **lg}


s16.dsp_code = dsp_code_17
FX_HOOK = 0x274                       # move #>$2e10,r1 (2 words) before jsr func_0021c4

# ---------------- ARM
CTX = 0x200069E4
CTRL_VIEW = 0x6C                      # controller: active view object (Mixer view has vtable MIX_VT)
BTN13 = 0x0803354C                    # Mixer button: ldr r0,[r4,#0xc] ; movs r1,#0 (shift test follows)
BTN13_SHIFT, BTN13_STOCK = 0x08033560, 0x08033558
MIX_ID_LIT = 0x08033714               # literal loaded by the stock Mixer case (adr r1,#0x1b8): Mixer view id
VIEW_SWITCH = 0x0803390C              # controller view switch (ctrl, view id, button)
DIAG = False                          # SC17D: diagnostic LEDs in the synth Preset view (Shift held)
S_DIAG = 31                           # diagnostic sticky bits (block byte 31, unused otherwise)
D_SHIFTMIX, D_MIX, D_PRESS, D_LEDS, D_ACT = 1 << 2, 1 << 3, 1 << 4, 1 << 5, 1 << 6
HEAP_TOP = 0x20044E58                 # stock heap limit
DIAG_ON, DIAG_DIM = 0x32, 0x38        # Synth 1 colours (bright, dim)
ENTRY = "double"                      # "double": Mixer -> Mixer toggles (SC17/17.1); "shift": Shift + Mixer (SC17.2)
MIX_VT = 0x0805A5F0                   # Mixer view vtable: 0 press, 1 release, 4 knob, 7 getLeds
MIX_PRESS, MIX_REL, MIX_KNOB, MIX_LEDS = 0x080446E6, 0x080448E8, 0x080475A0, 0x08047592
# SC17-SC17.2 used button 13 / view 1 (0x200441A8), which is NOT the Mixer (it is the Patterns-type view:
# knob slot no-op, Shift = store 0x20039DE0).  The real Mixer is button 14 -> view id 2 -> object 0x200447D4:
# pads 0-7 = mute (0x08046626), knobs = track levels (0x080466C4), LEDs 0x08046C04.  Shift + button 14 never
# reaches the button switch (stock Shift mask 0x07DBBE00 lacks bit 14).
BTN14 = 0x08033506                    # case 14: movs r2,#0xe ; adr r0,#0x1fc ; b 0x080335fa
BTN14_LIT, BTN14_TAIL = 0x08033708, 0x080335FA
MIX2 = dict(MIX_VT=0x0805A668, MIX_PRESS=0x08046626, MIX_REL=0x080466B4, MIX_KNOB=0x080466C4, MIX_LEDS=0x08046C04)


LED_N = 32                            # entries in the Master FX LED buffer (SC17.4+: 42, see use_full_leds)


def use_full_leds():
    """SC17.4: the LED task (0x08034196, map 0x08059438) reads 42 entries from the active view:
    0-31 pads, 32/33 two buttons, 34-41 the 8 knob LEDs.  A 32-entry buffer showed garbage on the knobs."""
    global LED_N, GFX_SIZE
    extra = 20
    LED_N, GFX_SIZE = 42, GFX_SIZE + extra
    s14.ST -= extra                   # block still ends at the stock heap limit 0x20044E58


SLOTS = False                         # SC17.6: bottom FX row (pads 25-32) in the Master FX view + FX slots (see use_slots)
S_SLOT, S_SLOTH = 148, 176            # 7 slots x 4 bytes (params | effect bits in bit 7), mask of held slots


def use_slots():
    """SC17.6: the FX view's bottom row (stock "FX off" pad + 7 SC14 effects) is also shown in the Master FX view, and
    holding a top effect pad + a bottom pad assigns the top effect (mode + a copy of its 4 parameters) to the bottom pad.
    The Master FX block grows from 148 to 180 bytes; 8 bytes of the old reservation were unused, so +24 bytes."""
    global SLOTS, GFX_SIZE
    assert LED_N == 42 and GFX_SIZE == 148, "use_full_leds() first"
    SLOTS = True
    GFX_SIZE += 32
    s14.ST -= 24


SP_PLAY = False                       # SC20.1: the song pointer playhead (c_sppos) shows only while the transport runs: the Play store (the engine's own +0x28 store was not it)
PLAY_STORE = 0x20011034
SONGPTR = False                       # SC17.7: song pointer on pads 9-24 of the Master FX view (see songptr_code)
TICK_FN, TICK_BACK, SET_TICKS = 0x0802C418, 0x0802C41C, 0x0802BFE0   # sequencer tick / its second instruction / set song position
SP_BIG = 6 * 1441440                  # added when a loop to tick 0 (start step 1 in cycle 0) would need tick -1: a multiple of
                                      # 6 x lcm(1..16) x 2, so every pattern length 1-16 and 32 keeps its phase


def SP_COLORS(pc):                    # (idle step, playhead, start, end) LED codes, from the Master FX effect colours
    return pc[5][1], pc[5][0], pc[0][0], pc[1][0]


def use_songptr():
    """SC17.7: song pointer in the Master FX view.  Uses 4 bytes that were unused (SC14 state + 21..23 and the Master FX
    block's S_DIAG byte), so the RAM reservation does not grow."""
    global SONGPTR
    assert SLOTS and not DIAG, "use_slots() first"
    SONGPTR = True


JUMP = False                          # SC18.1: Master FX pad 7 = jump mode (hold / Shift = sticky): a step pad jumps there at the next step
S_JF, S_JT = 177, 178                 # Master FX block bytes (unused tail of the 180-byte block): jump flags (bit 0 held, bit 1 sticky), target
KNOB_BRIGHT = False                   # SC19.9: the knob LEDs of the Master FX view show the value of their parameter as brightness (the high byte of the LED halfword, see persist19.KNOB_LEVELS)
JUMP_REPEAT = False                   # SC19.7: while the jump mode is on (pad 7 held / sticky) the target step is repeated at every step boundary (S_JT bit 7 = repeating)
JUMP_HOLD = False                     # SC19.9: step jump = the touched step plays at the next step and is repeated while ITS pad stays pressed (S_JT: bits 0-4 step, bit 6 pad held, bit 7 jumped once);
                                      # the pad 7 mode (held / sticky) only enables the selection.  Supersedes JUMP_REPEAT
JUMP_WHITE = False                    # SC19.7: pad 7 is white (dim off / bright on) instead of the song pointer colours
JMP_ON, JMP_OFF = 0x01, 0x03          # white LED codes (the RGB table of 0x0803423C: 1 = 255, 255, 255; 3 = 74, 74, 74)
SPCACHE = False                       # SC23.5: the playhead is cached by the sequencer tick hook (step + a time stamp in the unused T0 word of set 2) and shown by the LED code from that
SP_HEAD = 0x01                        # SC23.5: the playhead is white (as the playing step of the stock step views), well apart from the dim idle steps
CLR_COPY = False                      # SC23.5: pad 8 shows exactly what the FX view's bypass pad (pad 25) shows
SP_NORM = False                       # SC23.4: the earlier of two chosen steps is always the start and the later the end (press order does not matter); a loop end that the playhead has already passed
                                      # jumps to the start at the next step
JUMP_LED = False                      # SC23.4: the target step of a pending / repeating jump is lit (white) in the song pointer rows
JUMP_UNSTICK = False                  # SC23.4: touching pad 7 again while it is latched (Shift + pad 7) unlatches it
CLEAR_SP = False                      # SC18.1: pad 8 also switches the song pointer off (start / end / held steps)
CLEARPAD = False                      # SC17.8: pad 8 of the Master FX view = all latched effects off; a tap on a latched pad unlatches it
CLR_ON, CLR_DIM = 0x19, 0x46          # clear pad LED codes (stock "FX off" look): some effect latched / none
SP2 = False                           # SC32: the song pointer without pad 7 (see use_sp2)
SMP = False                           # SC33: the captured sample (see use_sampler)
SMP_PAD, SMP_REC, SMP_SEL, SMP_SLOT = 6, 31, 6, 6      # pad 7 = play, pad 32 = record, S_SEL value of the sample, the slot whose 4 bytes hold its knobs (pad 32)
SMB_REC, SMB_GATE, SMB_LOOP, SMB_DIRTY = 1, 2, 4, 8    # S_JF bits (S_JF is free with SP2); bits 4-5 = pending command (1 start, 2 start in loop, 3 stop), bits 6-7 = last state sent
SMP_ON, SMP_DIM, REC_ON, REC_DIM = 0x2D, 0x2E, 0x53, 0x54   # pad 7 yellow, pad 32 red (RGB table B, G, R: 0x53 = 255, 0, 0; 0x54 = 102, 0, 0)
S_SMT = 48                            # SC33: the T0 word of effect set 4 (Vinyl has no LFO: written, never read; not written with SMP): pad 32 press time (bits 0-29, ms),
SMT_LATCH, SMT_ARM = 1 << 30, 1 << 31 #   bit 30 = recording latched (short press) / the armed bar running, bit 31 = armed (Shift + pad 32: records the next bar)
SMP_TAP = 300                         # ms: a pad 32 press shorter than this latches the recording (the next press stops it); longer = record while held
BAR_TICKS = 96                        # 16 steps x 6 ticks
SMP2 = False                          # SC34 (see use_sampler2)
SMP_SET = 41                          # SC34: setmap entry of the sample: block + S_KNOB + 4 x 41 = the 4 bytes of slot 6 (its knobs)
SMT_REQ_SH, SMT_TIME_MASK = 23, (1 << 23) - 1   # SC34: S_SMT bits 23-29 = a drum sample to replace + 1 (tools/drumrep.py), bits 0-22 = the pad 32 press time
MODE_COL = (0x2D, 0x17, 0x09)         # SC34: K2 of the sample, one colour per mode: one-shot yellow, gate green (0, 255, 0), loop blue (26, 71, 255); full brightness
SP2_WHITE = 0x01                      # SC32: pad 9 (step 1) while a phrase is latched
SMP_HOLD = False                      # SC34.1 (see use_loophold)
SP3 = False                           # SC34.2 (see use_sp3)
GLITCH = False                        # SC36 (see use_glitch)
GL_PAD, GL_SEL, GL_SLOT, GL_SET = 30, 7, 5, 40   # pad 31 = the Glitch, its S_SEL value, the slot whose 4 bytes hold K1..K4 (pad 31), setmap entry (S_KNOB + 4 x 40 = that slot)
GL_ON, GL_DIM = 0x4D, 0x4E                # teal bright / dim
GL2 = False                               # SC36.1 (see use_glitch2)
GL3 = False                               # SC37.4 (see use_glitch3)
VINYL_COL = None                          # SC37.4: (bright, dim) LED codes of Vinyl instead of the palette's (see use_vinyl_peach)
GCLEAR = False                            # SC37.9: Clear + knob in Master FX (see use_gclear)
GCLEAR2 = False                           # SC42.4: only the lavender (the default); no red: Master FX has no automation (see use_gclear2)
ARMPLAY = False                           # SC38.2: an armed capture starts at Play (see use_armplay)
ARMPLAY2 = False                          # SC38.4: ... from the stock's own start of the transport (see use_armplay2)
LATCH7 = False                            # SC38.5: Shift + pad 7 = a latched loop again (see use_latch7)
START_RET = 0x0802BD41                    # the return address of the transport start's call 0x0802BD3C bl SET_TICKS(engine, 0)
SEQ_ENGINE = 0x20038ECC                   # the sequencer engine: [+0x90] = the ticks store (parameter 0), 0 from a stop until the first tick
GCLR_BLUE, GCLR_RED = 0x07, 0x53          # the stock's Clear colours (persist19.use_blue7)
GL_DEF = (127, 127, 0, 0)                 # the Glitch's knobs back to: normal speed, continuous, no delay, no chaos
SMP_DEF = (64, 0, 0, 127)                 # the sample's real values back to: no transposition, one-shot, start 0, end 127
SMP_SAVEBIT = False                   # SC35: a replacement clears the "saved" bit of the slot it will use (X:SMB + 0x1E, bit REPK; tools/packio.py)


def use_jump(repeat=False, white=False, hold=False):
    """SC18.1: Master FX pad 7 = jump mode.  Hold it (or Shift + pad 7 = sticky on / off) and touch a song pointer step: the
    playback jumps to that step at the next step boundary.  Pad 8 (with CLEAR_SP) also clears it.
    SC19.7: repeat = the jump is repeated at every following step boundary while the pad is held / sticky (the same step
    plays again until the pad is released / toggled off); white = pad 7 is white."""
    global JUMP, JUMP_REPEAT, JUMP_WHITE, JUMP_HOLD
    assert SONGPTR and SLOTS, "use_songptr() / use_slots() first"
    JUMP = True
    JUMP_REPEAT, JUMP_WHITE, JUMP_HOLD = repeat and not hold, white, hold


def use_spcache():
    """SC23.5: the song pointer playhead (the lit step) comes from the sequencer tick hook: at every tick it stores the step of the tick about to run ((n / 6) mod 16) and a stamp of the HAL clock in the
    T0 word of effect set 2 (Digitise: the only set whose T0 nobody reads); the LED code shows that step while the stamp is younger than 2 s.  No dependence on the transport store."""
    global SPCACHE
    assert SONGPTR
    SPCACHE = True


def use_clear_copy():
    """SC23.5: pad 8 of Master FX copies the LED of pad 25 (the stock FX bypass pad, white) every time the buffer is built."""
    global CLR_COPY
    assert CLEARPAD
    CLR_COPY = True


def use_sp_norm():
    """SC23.4: song pointer ranges are normalised: the lower step is the start, the higher the end, whatever the order of the touches (two held steps, or a latched start + a tap below it);
    when the playhead is already beyond a chosen end (step > E) the playback jumps to the start at the next step boundary."""
    global SP_NORM
    assert SONGPTR
    SP_NORM = True


def use_jump_led():
    """SC23.4: the target of a step jump (pad 7 mode) is lit white in the song pointer rows while it is pending / repeating."""
    global JUMP_LED
    assert JUMP and SONGPTR
    JUMP_LED = True


def use_jump_unstick():
    """SC23.4: pad 7 latched (Shift + pad 7): touching it again (without Shift) unlatches the jump mode."""
    global JUMP_UNSTICK
    assert JUMP
    JUMP_UNSTICK = True


def use_sp2():
    """SC32: the song pointer reworked, pad 7 (jump mode) removed (dark, does nothing):
      * one step held = retrigger: that step plays at the next step boundary and is repeated while its pad stays pressed (the JUMP_HOLD target, S_JT);
      * two steps held = a phrase loop between them (the lower is the start); releasing either ends it (the step still held does nothing more);
      * Shift + a step = the start of a latched phrase (playback loops start..16 meanwhile); Shift + a second step = its end (the phrase is latched);
        Shift + the start again (no end yet) = off; Shift + a step with a latched phrase = a new start;
      * a latched phrase lights pad 9 (step 1) white; touching pad 9 (no Shift) removes it.  Held steps work inside a latched phrase (a held phrase wins)."""
    global SP2
    assert JUMP_HOLD and SP_NORM and SONGPTR
    SP2 = True


def use_sp3():
    """SC34.2 (the user, 2026-10-09): the phrase mode of the song pointer (replaces SC32's Shift + two steps):
      * Shift + a step (no phrase) = phrase mode on, that step is the start (the end is step 16 until a pad is touched);
      * in phrase mode a tap (no Shift) = the end of the phrase (a step before the start becomes the start, the old start the end); no retrigger, no
        momentary phrase; Shift + another step = a new start (an end before it goes back to 16); Shift + the start or pad 9 (white) = phrase mode off;
      * without phrase mode: SC32 (one held step = retrigger, two = a momentary phrase)."""
    global SP3
    assert SP2
    SP3 = True


MECH = False                              # SC39.7 (see use_mech)
MECH_T0, MECH_TK = 20, 2                  # the gesture lasts MECH_T0 + K x K >> MECH_TK ms (K = 0..127: 20 ms .. 4 s)
MECH_TEAR = (127, 50, -90, -127)          # the tear scratch: the speed of each quarter of a movement


def use_mech():
    """SC39.7 (the user, 2026-10-12: «replantea el efecto Vinyl: en su lugar … "manipulación mecánica" tipo tape stop, scratch, jog spin, rattle … cuando se toca se
    produce un stop … y al soltar, otro efecto contrario» … «usa el motor de Glitch, ocupando el atajo de Vinyl (Vinyl se descarta). La transición entre tipos será
    medianamente continua … Considera varios tipos de scratch (baby, tear…)»): pad 6 (and whatever switches the Vinyl effect on: its latch, a bottom slot, the FX
    sequencer) no longer sets the Vinyl bit of the DSP; while it is on, the DSP service tick drives the Glitch engine (core 1: a tape head on the recent master)
    with an envelope of its speed and repeat size, and when it goes off, with the same envelope backwards, then the Glitch engine is let go.
      K1 = how fast the hand moves (the movements per gesture of the scratches: 1..8), K2 = the kind, K3 = the time of the stop, K4 = the time of the start.
      K2 walks five kinds, every position in between a mix of its two neighbours: tape stop (the speed falls to 0) -> baby scratch (back and forth, dying)
      -> tear scratch (the same in steps) -> back spin (thrown backwards, dying) -> rattle (the repeat closes on itself, then stops).
    x = the place in the gesture 0..127, y = 127 - x; the speed v = -127..127 (127 = normal) goes to the Glitch as K1 = 64 + (63 v + 64 >> 7), the repeat as K2.
    State: bit 7 of the Glitch's K4 byte = the gesture runs (the Glitch's own tick waits); X:VN_T of the DSP (a Vinyl parameter, free now) = phase << 22 | start time."""
    global MECH
    assert GLITCH and GL3
    MECH = True


DIGI4 = False                             # SC39.9 (see use_digi4)
MECH_COL = (0x01, 0x2D, 0x2B, 0x45)       # the K2 LED of the mechanical gesture: tape -> baby white, baby -> tear yellow, tear -> spin orange, spin -> rattle red
MECH_MINB = 24                            # ... from this brightness at the start of a stretch up to 127 at its end


def use_digi4():
    """SC39.9 (the user, 2026-10-12: «en digitiser no se encienden knob 3 y 4, asigna a 4 una envolvente bipolar A/D a digitiser level. En el nuevo modo vinyl
    (manipulación mecánica) separa los modos con colores, aunque sean continuos (cada segmento de un color, con brillo ascendente)»).
      * Digitise shows its four knob LEDs (K3 = the delay throw of tools/throw.py; K4 dark in the middle, brighter either way).
      * K4 of Digitise = an envelope of the amount of the effect from the moment it is switched on: right of the middle = a decay (it starts whole and fades to
        clean), left = an attack (it starts clean and grows to whole); the further from the middle, the longer (20 ms + d x d, d = 1..64: up to ~4 s); the middle =
        none.  The amount scales the indices of K1 (sample rate) and K2 (bits) into their tables (index 0 = clean); the tick writes X:DG_N / DG_MASK while Digitise
        is on.  The start time lives in X:VN_ST of the DSP (a Vinyl state word, free since SC39.7), read only while Digitise is on with K4 off the middle.
      * the K2 LED of the mechanical gesture: one colour per stretch between two kinds (MECH_COL), brighter along the stretch."""
    global DIGI4
    assert MECH and KNOB_BRIGHT and SPCACHE
    DIGI4 = True


MSWAP = False                             # SC39.9 (see use_mechswap)
MECH_DEF = (40, 0, 60, 30)                # the mechanical gesture's knobs when they live in the Glitch's bytes (MSWAP): 3 movements, tape stop, ~0.9 s stop, ~0.25 s start


def use_mechswap():
    """SC39.9 (the user, 2026-10-12: «intercambia la posición de vinyl con glitch»): the Glitch is pad 6 of the top row (an effect like the others: held, latched
    with Shift, assignable to a bottom slot, bit 5 of the FX sequencer) and the mechanical gesture is pad 31 (held; pad 31 + a bottom pad assigns it; bit 6 of the
    FX sequencer).  Nothing moves in the views' code: the two engines swap where they read from.  The Glitch plays while effect 5 is on and takes its K1..K4 from
    the knob set of pad 6 (sent when it comes on and when a knob of the view changes); the gesture runs while pad 31 is held and takes its knobs from the four
    bytes of pad 31 (bits 0-6: their bit 7 keeps meaning held / to send / sent / a gesture runs)."""
    global MSWAP
    assert MECH
    MSWAP = True


T0FIX = False                             # SC40 (see use_t0fix)


def use_t0fix():
    """SC40 (found in SC39.9; the user: «arregla el lfo»): in c_fxtick the loop that stores the start time of every effect set that has just come on used the
    labels ft_t0..ft_t4, and ft_t0 is also the label of the end of that section: when the Gater (set 0) was not among the new ones the whole loop was jumped,
    so the LFO of the Auto-Filter and of the Phaser only started from the moment of the press when the Gater came on in the same tick; otherwise it went on
    from an older start (a phase that seemed random).  The loop's labels are its own now: every set starts its LFO when it comes on."""
    global T0FIX
    T0FIX = True


def use_glitch():
    """SC36 (the user, 2026-10-09): pad 31 of the Master FX view and of the FX view = the Glitch (DSP core 1, tools/granular_dsp.py): held = the master output replaced by a tape
    head reading the recent master (K1 speed: top = 1, middle = stopped, bottom = backwards; K2 repeat size, 127 = continuous; K3 delay; K4 chaos).  Pad 31 is no longer an
    assignable slot: its 4 bytes hold K1..K4 (bits 0-6; bit 7 of byte 0 = held, of byte 1 = to be sent).  Pressing it selects it (the Master FX knobs).  The DSP service tick
    writes X:GARM (the magic while held, then K1..K4); the view left = released."""
    global GLITCH
    assert SMP_HOLD
    GLITCH = True


def use_glitch2():
    """SC36.1 (the user, 2026-10-09): the Glitch can be assigned to the other bottom pads like any Master FX effect (pad 31 held + a bottom pad: that slot = the Glitch
    with a copy of K1..K4; the slot plays it while held, in its colour); the FX step sequencer of the MIDI tracks picks bottom-row slots (vcf21.use_fxseq2): c_fsqfx turns
    the slots it wants into effect bits (loading the slot's copy of the knobs when it differs) and the Glitch; c_slotcol gives the colour of a slot."""
    global GL2
    assert GLITCH
    GL2 = True


def use_glitch3():
    """SC37.4 (the user, 2026-10-10: two bottom pads with the Glitch and different knobs held together copied one's knobs into the other): «pad 31 held +
    a bottom pad = assign the Glitch» looked at bit 7 of KG (the Glitch plays), which a held Glitch slot sets too, so holding slot A and pressing slot B
    assigned the Glitch to B again with A's knobs.  Now pad 31 itself held is bit GL_SLOT of S_SLOTH (that slot is never assigned: its bytes are KG), and
    only it assigns; with two Glitch sources held the last one pressed plays, and releasing it brings back the knobs of one still held (c_glrel3)."""
    global GL3
    assert GL2
    GL3 = True


def use_vinyl_peach():
    """SC37.4 (the user, 2026-10-10: «cambia el color de vinyl a peach»): Vinyl (pad 6, its slots and knobs) in peach, the colour of the FX view's pads 1-16
    (0x6A bright = the selected one there, 0x6B dim).  The song pointer keeps its colours (SP_COLORS took Vinyl's palette entries)."""
    global VINYL_COL
    VINYL_COL = (0x6A, 0x6B)


def use_armplay():
    """SC38.2 (the user, 2026-10-11: «en el modo arm record de captura de sample (pulsar shift+captura para que empiece a grabar al pulsar play) se termina la
    grabación al final del compás»): the stock plays the downbeat of a start (tick 0) from the Play handler (0x0802BBAA -> 0x0802C008), not through the tick
    function c_sptick watches, so an armed capture (Shift + pad 32) armed while stopped began a bar late (tick 96) and ended at the end of the second bar.
    c_smtick: armed, not yet recording, the transport running and the ticks store still 0 (a start, before its first tick) = start now; c_sptick ends
    it on the next bar line (tick 96) as before.  Armed while playing: the next bar line, as before."""
    global ARMPLAY
    assert SMP
    ARMPLAY = True


LEDBUF = False                            # SC41.1 (see use_ledbuf)
LEDBUF_OFF = 0x27024 + 192                # the session record's tail + 192 (tools/patchain.py: 0..127 its parts, tools/fxsess.py: 128..154)
FSQRAND = False                           # SC41.1 (see use_fxseqrand)


def use_ledbuf():
    """SC41.1 (the user, 2026-10-14: «al entrar en Master FX view, el sinte propio deja de funcionar … deja de sonar Synth 2 … pasa cuando hay muchas
    cosas sonando»): while the Master FX view is on the screen its LED buffer (84 B: the block + 64..147 = c_gst() + 104..187) is drawn every frame, and
    that buffer was taken as idle memory by later modules: the pattern chains' «made for this project» mark (c_gst() + 143: the running part of
    the chains and of the fractal order was cleared again and again), the step frequency counters (+ 140..184), the state of the Sidechain knobs,
    of the own-synth patches, of the patch save, of the project copy, of the macro editor and the granular source.  The buffer now lives in the
    loaded project's record (its tail + 192, 84 B nobody else uses; saved with the project, redrawn every frame); without a record, the old place."""
    global LEDBUF
    LEDBUF = True


def use_fxseqrand():
    """SC41.1 (the user, 2026-10-14: «en el secuenciador de efectos master, añade una opción random: activa un efecto de la lista al azar»): value 7 of
    the FX sequencer (vcf21.use_fxseqrand) = one of the bottom-row slots that plays something, drawn for every occurrence of the step (the seed comes
    with the sequencer's bits: c_fsqbits puts it in bits 8-15 and bit 6)."""
    global FSQRAND
    FSQRAND = True


def use_engfix():
    """SC40.9: SEQ_ENGINE was the engine's interface (the engine + 0xC): its «ticks store» (+ 0x90) was the chain store, whose first word is 0
    while Synth 1 plays its pattern 1 alone, so the armed capture (ARMPLAY) started at once when it was armed while playing.  See vcf21.use_engfix."""
    global SEQ_ENGINE
    SEQ_ENGINE = 0x20038EC0


def use_armplay2():
    """SC38.4 (SC38.2 on the device, 2026-10-11: «desde parado > empieza a grabar en el segundo compás, debería hacerlo en el primero»): the stock
    starts the transport in the Play handler with 0x0802BD3C bl SET_TICKS(engine, 0) (seen in emulation: a Play press from a stop calls it, a stop
    does not), which plays the downbeat (0x0802C008); on the device the first tick follows at once, so c_smtick never sees the ticks store at 0.
    c_stk at the entry of SET_TICKS (the displaced push {r4-r6, lr}; mov r4, r0): called from that start with position 0, an armed capture that is not
    running yet starts there, on the downbeat; c_sptick ends it on the bar line 96 as before.  (Our song pointer calls SET_TICKS from c_sptick: not a
    start.)"""
    global ARMPLAY2
    assert SMP
    ARMPLAY2 = True


def use_latch7():
    """SC38.5 (the user, 2026-10-11: «en master fx, shift + sample pad ya no reproduce en bucle»; «hay dos comportamientos llamados loop, pero son distintos:
    en el modo de reproducción loop, el sample se repite mientras el pad se mantenga pulsado y para inmediatamente al soltar; al pulsar shift + 7, el pad se
    reproduce en bucle (independientemente del modo seleccionado) hasta que se vuelva a pulsar 7»).  SC34.1's loophold made Shift + pad 7 a held loop too.
    Now Shift + pad 7 (or Shift + a slot of the sample) starts a forced loop with the gate held and SMB_LOOP = latched: releasing the pad, or leaving
    Master FX, keeps the gate (the DSP's HOLD stops a loop only when the gate drops); the next press of pad 7 / a sample slot (with or without Shift) stops it
    (gate and loop off, command 3); pad 8 too.  The loop mode (K2) is unchanged: it plays while held."""
    global LATCH7
    assert SMP_HOLD and SMP2
    LATCH7 = True


def use_gclear():
    """SC37.9 (the user, 2026-10-11: «en master fx, clear+knob no funciona»): with Clear held, a knob of the selected effect turned right goes back to its
    default (the DEFAULTS of the effects, GL_DEF for the Glitch, SMP_DEF for the sample; as the stock does on the drum knobs), turned left does nothing (Master FX
    has no automation to delete).  While Clear is held the knob LEDs of the selected effect are blue at their default, red elsewhere (c_gclrled)."""
    global GCLEAR
    GCLEAR = True


def use_gclear2():
    """SC42.4 (the user, 2026-10-16: «clearing a knob successfully must show lavender … red for automation clear»): with Clear held, the knobs of the
    selected effect at their default show the stock's 0x07; the others keep their colour (red is the colour of an automation cleared, and Master FX has
    none)."""
    global GCLEAR2
    assert GCLEAR
    GCLEAR2 = True


def use_sampler():
    """SC33: the captured sample in Master FX (DSP side: tools/sampler_dsp.py).  Pad 32 held = record the output (with the effects); pad 7 = play it
    (one-shot / gate / loop by K2; Shift + pad 7 = loop whatever the mode, again = stop); pad 7 selects the sample: K1 pitch (-24..+23 semitones), K2 mode,
    K3 start, K4 end (end < start = reverse).  Pad 6 stays Vinyl.  The knobs live in the 4 bytes of slot 6 (pad 32 is no longer an assignable slot), stored so that
    zero bytes are the defaults (pitch = raw ^ 64, end = 127 - raw); the flags in S_JF; pad 8 stops the sample instead of clearing S_JF."""
    global SMP
    assert SP2 and SLOTS and CLEARPAD and CLEAR_SP and KNOB_BRIGHT
    SMP = True


def use_sampler2():
    """SC34 (the user, 2026-10-08): the sample is an effect that can be assigned to a bottom pad (26-31) like the others: pad 7 held + a bottom pad assigns it with a
    copy of its 4 knobs (setmap[6] = SMP_SET); a slot of the sample plays it (gate while held, Shift = loop); pad 32 records in the FX view too (a held recording
    goes on in either view); K2 shows the mode by colour; S_SMT bits 23-29 carry a drum replacement request to the DSP (CMD 4, sampler_dsp.V34)."""
    global SMP2
    assert SMP
    SMP2 = True


def use_loophold():
    """SC34.1 (the user, 2026-10-08): a loop plays only while its pad is held.  Shift + pad 7 / a slot of the sample = start in loop with the gate held (no more
    on / off toggle); every release of the pad (and leaving the view) drops the gate and the loop flag; the DSP side is sampler_dsp.HOLD (the gate stops every
    playback but a plain one-shot)."""
    global SMP_HOLD
    assert SMP2
    SMP_HOLD = True


def use_clearpad():
    """SC17.8: pad 8 (index 7) of the Master FX view switches off every effect latched with Shift (top row, assigned slots and
    the SC14 effects of the bottom row); touching any latched effect pad (without Shift) switches that one off.
    No new RAM: it only uses the existing latch bits."""
    global CLEARPAD
    assert SLOTS, "use_slots() first"
    CLEARPAD = True


def use_mixer14():                    # SC17.3+: Mixer button = 14, Master FX on Mixer -> Mixer
    global ENTRY
    ENTRY = "mixer14"
    globals().update(MIX2)
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
SVC_HOOK = s14.SVC_HOOK
GFX_OFF = 40                          # Master FX block = c_gst() + 40
MAGIC = 0x6F1D0C17
# block layout
S_MAGIC, S_MODE, S_HELD, S_LATCH, S_SEL = 0, 4, 5, 6, 7
S_KNOB = 8                            # 5 sets x 4 knobs
S_DIRTY, S_FXON, S_PREV = 28, 29, 30
S_T0 = 32                             # 5 x u32
S_SPS, S_SPT = S_T0 + 8, S_T0 + 9      # SC23.5: the playhead cache (bytes of the T0 word of effect set 2, see use_spcache)
S_CG, S_CF, S_CA = 52, 56, 60         # caches: G_TGT, AF_F, PH_A
S_LED = 64                            # 32 x u16
N_FX = 6
SETMAP = [0, 1, 1, 2, 3, 4]           # pad -> parameter set
FXBITS = [1 << G.B_GATE, 1 << G.B_AF, (1 << G.B_AF) | (1 << G.B_HP), 1 << G.B_DIG, 1 << G.B_PH, 1 << G.B_VN]
DEFAULTS = [(80, 127, 64, 40), (54, 100, 40, 64), (60, 64, 0, 0), (40, 100, 64, 64), (64, 40, 90, 30)]
PAL = 0x08056464
PAL_IDX = [(5, 13), (2, 10), (3, 11), (4, 12), (1, 9), (7, 15)]   # (bright, dim) palette index per pad
FS = 48000.0


def popw(regs, lr=False):
    return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)          # LDR.W Rt,[Rn,#imm12]
def str_w(rt, rn, imm12): return h(0xF8C0 | rn) + h(rt << 12 | imm12)          # STR.W Rt,[Rn,#imm12]
def strh_w(rt, rn, imm12): return h(0xF8A0 | rn) + h(rt << 12 | imm12)          # STRH.W Rt,[Rn,#imm12]
def ldrh_w(rt, rn, imm12): return h(0xF8B0 | rn) + h(rt << 12 | imm12)          # LDRH.W Rt,[Rn,#imm12]
def ldr_reg_lsl2(rt, rn, rm): return h(0xF850 | rn) + h(rt << 12 | 0x20 | rm)  # LDR.W Rt,[Rn,Rm,LSL #2]


def q24(x): return max(-0x800000, min(0x7FFFFF, int(round(x * 0x800000)))) & 0xFFFFFF


def tables():
    t = {}
    t["GDIV"] = [[1, 2, 4, 8, 16, 32][k * 6 // 128] for k in range(128)]
    t["GK"] = [q24(min(0.999, 0.5 * 2 ** (-k / 127 * 9))) for k in range(128)]             # softness: 0.5 .. 1/1024 per frame
    t["AFN"] = [[64, 32, 16, 8, 4, 2, 1][k * 7 // 128] for k in range(128)]                # period in 1/16 notes
    t["AFTAB"] = [q24(min(0.9, 2 * math.sin(math.pi * 40 * 2 ** (i / 127 * math.log2(7500 / 40)) / FS))) for i in range(128)]
    t["AFQ"] = [q24(min(0.999, 1.0 - k / 127 * 0.92)) for k in range(128)]
    t["PHPER"] = [int(20000 * 2 ** (-k / 127 * math.log2(200))) for k in range(128)]       # 20 s .. 100 ms
    def ap(i):
        fc = 100 * 2 ** (i / 127 * math.log2(6000 / 100)); tt = math.tan(math.pi * fc / FS)
        return q24((tt - 1) / (tt + 1))
    t["PHTAB"] = [ap(i) for i in range(128)]
    t["PHFB"] = [q24(k / 127 * 0.85) for k in range(128)]
    t["MIX"] = [q24(min(0.999, k / 127)) for k in range(128)]
    t["DGN"] = [max(1, int(round(1 + (k / 127) ** 2 * 31))) for k in range(128)]
    t["DGM"] = [(0xFFFFFF << (k * 21 // 127)) & 0xFFFFFF for k in range(128)]
    t["VTH"] = [0x7FFFFF if k == 0 else q24(0.85 - k / 127 * 0.30) for k in range(128)]
    t["VHISS"] = [q24((k / 127) ** 2 * 0.12) for k in range(128)]
    t["VLPK"] = [q24(min(0.999, 1 - math.exp(-2 * math.pi * 500 * 2 ** (k / 127 * math.log2(40))/ FS))) for k in range(128)]
    t["VHPK"] = [0 if k == 0 else q24(1 - math.exp(-2 * math.pi * 20 * 2 ** (k / 127 * math.log2(60)) / FS)) for k in range(128)]
    t["GOFF"] = [q24((127 - k) / 127 * 0.999) for k in range(128)]
    if SMP:
        t["SMPI"] = [int(round(2 ** ((k - 64) * 24 / 64 / 12) * 65536)) for k in range(128)]   # the sample's increment, 16.16 (K1: -24..+23.6 semitones)
    return t


VN_CRAMP = q24(0.5)


def arm_code(base, L, tabaddr, defaults_addr, setmap_addr, fxbits_addr, pal_codes):
    a = Asm(base)
    c_gst, c_now, c_beat, c_gtick, c_shift = L["c_gst"], L["c_now"], L["c_beat"], L["c_gtick"], L["c_shift"]
    udiv, mls = s14.udiv, s14.mls

    zc = [0]
    INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
           "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}
    def bc(target, cond):                            # conditional branch, +-2KB
        zc[0] += 1; n = f"_c{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)
    def zjmp(reg, target):                           # cbz with unlimited range
        zc[0] += 1; n = f"_z{zc[0]}"
        a.emit(cmp_imm, reg, 0); a.emit(b_cond, n, "ne"); a.emit(b, target); a.label(n)

    def dset(rb, bit, tmp1=1, tmp2=2):               # [rb + S_DIAG] |= bit (diagnostic builds only)
        if not DIAG: return
        a.emit(ldrb_imm, tmp1, rb, S_DIAG); a.emit(movs_imm, tmp2, bit); a.emit(orrs_reg, tmp1, tmp2)
        a.emit(strb_imm, tmp1, rb, S_DIAG)
    def dmark(bit):                                  # c_gfst then set bit; clobbers r0-r3
        if not DIAG: return
        zc[0] += 1; n = f"_dm{zc[0]}"
        a.emit(bl, "c_gfst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, n, "eq"); dset(0, bit); a.label(n)

    def ldtab(rd, name, ridx):                       # rd = TABLE[ridx] (u32)
        a.emit(movw, rd, tabaddr[name] & 0xFFFF); a.emit(movt, rd, tabaddr[name] >> 16)
        a.emit(raw, ldr_reg_lsl2(rd, rd, ridx))

    def knob(rd, st, s, k):                          # rd = knobs[s*4+k] (state in st)
        a.emit(ldrb_w, rd, st, S_KNOB + 4 * s + k)

    # ---- c_gfst: r0 = Master FX block or 0
    a.label("c_gfst")
    a.emit(push_list, [3, 4], lr=True)
    a.emit(bl, c_gst); zjmp(0, "gf_out")
    a.emit(adds_imm8, 0, GFX_OFF); a.emit(mov_reg, 4, 0)
    a.emit(ldr_imm, 1, 0, S_MAGIC); a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16)
    a.emit(cmp_reg, 1, 2); bc("gf_out", "eq")
    a.emit(movs_imm, 1, 0); a.emit(movs_imm, 3, 0)
    a.label("gf_z"); a.emit(raw, h(0x50E1))                                    # str r1,[r4,r3]
    a.emit(adds_imm8, 3, 4); a.emit(cmp_imm, 3, GFX_SIZE); bc("gf_z", "lo")
    a.emit(movw, 1, defaults_addr & 0xFFFF); a.emit(movt, 1, defaults_addr >> 16)
    a.emit(movs_imm, 3, 0)
    a.label("gf_d"); a.emit(ldrb_reg, 0, 1, 3); a.emit(adds_imm8, 3, S_KNOB)
    a.emit(raw, h(0x54E0))                                                     # strb r0,[r4,r3]
    a.emit(subs_imm8, 3, S_KNOB - 1); a.emit(cmp_imm, 3, 20); bc("gf_d", "lo")
    if MSWAP:                                                                  # the gesture's knobs (pad 31's bytes) start at their defaults
        for k_, v_ in enumerate(MECH_DEF): a.emit(movs_imm, 0, v_); a.emit(strb_w, 0, 4, S_SLOT + 4 * GL_SLOT + k_)
    a.emit(movs_imm, 0, 1); a.emit(strb_imm, 0, 4, S_DIRTY)
    a.emit(movs_imm, 0, 0xFF); a.emit(strb_imm, 0, 4, S_FXON)
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x43C0))                             # mvns r0,r0 -> 0xFFFFFFFF
    for off in (S_CG, S_CF, S_CA): a.emit(raw, str_w(0, 4, off))
    a.emit(str_imm, 2, 4, S_MAGIC)
    a.emit(mov_reg, 0, 4)
    a.label("gf_out"); a.emit(pop_list, [3, 4], pc=True)

    # ---- c_gact: r0 = block if the Master FX view is showing, else 0 (clobbers r1-r3)
    a.label("c_gact")
    a.emit(push_list, [3, 4], lr=True)
    a.emit(bl, "c_gfst"); zjmp(0, "ga_out"); a.emit(mov_reg, 4, 0)
    a.emit(ldrb_imm, 1, 4, S_MODE); zjmp(1, "ga_no")
    a.emit(movw, 1, CTX & 0xFFFF); a.emit(movt, 1, CTX >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(ldr_imm, 1, 1, 0x40); a.emit(ldr_imm, 1, 1, CTRL_VIEW)
    a.emit(ldr_imm, 1, 1, 0); a.emit(movw, 2, MIX_VT & 0xFFFF); a.emit(movt, 2, MIX_VT >> 16)
    if DIAG:
        a.emit(cmp_reg, 1, 2); bc("ga_yes", "eq")
        a.label("ga_no"); a.emit(movs_imm, 0, 0); a.emit(b, "ga_out")
        a.label("ga_yes"); dset(4, D_ACT)
    else:
        a.emit(cmp_reg, 1, 2); bc("ga_out", "eq")
        a.label("ga_no"); a.emit(movs_imm, 0, 0)
    a.label("ga_out"); a.emit(pop_list, [3, 4], pc=True)

    # ---- c_mixbtn: Mixer button (r4 = controller, frame of 0x08033320: push {r3,r4,r5,lr})
    a.label("c_mixbtn")
    if ENTRY == "mixer14":                           # SC17.3: real Mixer button; Mixer in Mixer toggles Master FX
        a.emit(bl, "c_gfst"); zjmp(0, "m4_stock")
        a.emit(ldr_imm, 1, 4, CTRL_VIEW); zjmp(1, "m4_enter"); a.emit(ldr_imm, 1, 1, 0)
        a.emit(movw, 2, MIX_VT & 0xFFFF); a.emit(movt, 2, MIX_VT >> 16); a.emit(cmp_reg, 1, 2); bc("m4_enter", "ne")
        dset(0, D_SHIFTMIX)                          # diag pad 19: toggle
        a.emit(ldrb_imm, 1, 0, S_MODE); a.emit(movs_imm, 2, 1); a.emit(eors_reg, 1, 2); a.emit(strb_imm, 1, 0, S_MODE)
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_HELD)
        a.emit(pop_list, [3, 4, 5], pc=True)
        a.label("m4_enter")
        dset(0, D_MIX)                               # diag pad 20: Mixer entered from another view
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_MODE); a.emit(strb_imm, 1, 0, S_HELD)
        a.label("m4_stock")
        a.emit(movs_imm, 2, 14); a.emit(movw, 0, BTN14_LIT & 0xFFFF); a.emit(movt, 0, BTN14_LIT >> 16)
        a.emit(b_w, BTN14_TAIL)
    elif ENTRY == "shift":                             # SC17.2: Mixer = Mixer, Shift + Mixer = Master FX (no toggling)
        a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); bc("ms_grid", "ne")
        a.emit(bl, "c_gfst"); zjmp(0, "ms_stock"); dset(0, D_MIX)
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_MODE); a.emit(strb_imm, 1, 0, S_HELD)
        a.label("ms_stock"); a.emit(b_w, BTN13_STOCK)
        a.label("ms_grid")
        a.emit(bl, "c_gfst"); zjmp(0, "ms_shift"); dset(0, D_SHIFTMIX)
        a.emit(movs_imm, 1, 1); a.emit(strb_imm, 1, 0, S_MODE)       # mode first: the switch may sleep (store flush)
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_HELD)
        a.emit(mov_reg, 0, 4); a.emit(movw, 1, MIX_ID_LIT & 0xFFFF); a.emit(movt, 1, MIX_ID_LIT >> 16)
        a.emit(ldr_imm, 1, 1, 0); a.emit(movs_imm, 2, 13)
        a.emit(raw, popw([3, 4, 5], lr=True)); a.emit(b_w, VIEW_SWITCH)  # stock Mixer selection (tail call, as stock)
        a.label("ms_shift"); a.emit(b_w, BTN13_SHIFT)
    else:
        a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); bc("mb_shift", "ne")
        a.emit(bl, "c_gfst"); zjmp(0, "mb_stock")
        a.emit(ldr_imm, 1, 4, CTRL_VIEW); a.emit(ldr_imm, 1, 1, 0)
        a.emit(movw, 2, MIX_VT & 0xFFFF); a.emit(movt, 2, MIX_VT >> 16); a.emit(cmp_reg, 1, 2); bc("mb_enter", "ne")
        a.emit(ldrb_imm, 1, 0, S_MODE); a.emit(movs_imm, 2, 1); a.emit(eors_reg, 1, 2); a.emit(strb_imm, 1, 0, S_MODE)
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_HELD)
        a.emit(pop_list, [3, 4, 5], pc=True)                                       # return from the button handler
        a.label("mb_enter")
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_MODE); a.emit(strb_imm, 1, 0, S_HELD)
        a.label("mb_stock"); a.emit(b_w, BTN13_STOCK)
        a.label("mb_shift"); a.emit(b_w, BTN13_SHIFT)

    # ---- c_gpress (view, pad, vel)
    a.label("c_gpress")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 7, 2)
    dmark(D_PRESS)
    a.emit(bl, "c_gact"); zjmp(0, "gp_stock"); a.emit(mov_reg, 4, 0)
    a.emit(cmp_imm, 6, N_FX); bc("gp_out", "hs")
    a.emit(strb_imm, 6, 4, S_SEL)
    a.emit(movs_imm, 5, 1); a.emit(raw, h(0x40B5))                             # lsls r5,r6 -> bit
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("gp_hold", "eq")
    a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(eors_reg, 0, 5); a.emit(strb_imm, 0, 4, S_LATCH); a.emit(b, "gp_out")
    a.label("gp_hold")
    if CLEARPAD:                                                               # a latched effect: the tap switches it off
        a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(tst_reg, 0, 5); a.emit(b_cond, "gp_hd", "eq")
        a.emit(bics_reg, 0, 5); a.emit(strb_imm, 0, 4, S_LATCH); a.emit(b, "gp_out")
        a.label("gp_hd")
    a.emit(ldrb_imm, 0, 4, S_HELD); a.emit(orrs_reg, 0, 5); a.emit(strb_imm, 0, 4, S_HELD)
    a.label("gp_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("gp_stock")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, MIX_PRESS)

    # ---- c_grel (view, pad)
    a.label("c_grel")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1)
    a.emit(bl, "c_gact"); zjmp(0, "gr_stock")
    a.emit(cmp_imm, 6, N_FX); bc("gr_out", "hs")
    a.emit(movs_imm, 1, 1); a.emit(raw, h(0x40B1))                             # lsls r1,r6
    a.emit(ldrb_imm, 2, 0, S_HELD); a.emit(bics_reg, 2, 1); a.emit(strb_imm, 2, 0, S_HELD)
    a.label("gr_out"); a.emit(pop_list, [4, 5, 6], pc=True)
    a.label("gr_stock")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6)
    a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, MIX_REL)

    if GCLEAR:
        a.label("c_gclrh")                                                     # -> r0 = 1 while Clear is held (the controller's held buttons, bit 0)
        a.emit(push_list, [], lr=True)
        a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40)
        a.emit(ldr_imm, 0, 0, 0x20); a.emit(ldr_imm, 0, 0, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET)
        a.emit(ldrb_imm, 0, 0, 0); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(pop_list, [], pc=True)
        a.label("c_gcur")                                                      # (r4 = block, r0 = knob) -> r0 = its value as its knob routine moves it, r1 = its default; -1 = none
        a.emit(push_list, [5], lr=True); a.emit(mov_reg, 5, 0)
        a.emit(ldrb_imm, 2, 4, S_SEL)
        if GLITCH:
            a.emit(cmp_imm, 2, GL_SEL); a.emit(b_cond, "gc_ng", "ne")
            a.emit(adds_reg, 0, 4, 5); a.emit(ldrb_w, 0, 0, S_SLOT + 4 * GL_SLOT); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25)
            if MSWAP:
                for k_, v_ in enumerate(MECH_DEF): a.emit(movs_imm, 1, v_); a.emit(cmp_imm, 5, k_); a.emit(b_cond, "gc_x", "eq")
                a.emit(b, "gc_x")
            else:
                a.emit(movs_imm, 1, GL_DEF[2]); a.emit(cmp_imm, 5, 2); a.emit(b_cond, "gc_x", "hs"); a.emit(movs_imm, 1, GL_DEF[0]); a.emit(b, "gc_x")
            a.label("gc_ng")
        if SMP:
            a.emit(cmp_imm, 2, SMP_SEL); a.emit(b_cond, "gc_ns", "ne")
            a.emit(adds_reg, 0, 4, 5); a.emit(ldrb_w, 0, 0, S_SLOT + 4 * SMP_SLOT); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25)
            for k in range(4):
                a.emit(cmp_imm, 5, k); a.emit(b_cond, f"gc_s{k}", "ne")
                if k == 0: a.emit(movs_imm, 3, 64); a.emit(eors_reg, 0, 3)
                if k == 3: a.emit(movs_imm, 3, 127); a.emit(subs_reg, 0, 3, 0)
                a.emit(movs_imm, 1, SMP_DEF[k]); a.emit(b, "gc_x")
                a.label(f"gc_s{k}")
            a.label("gc_ns")
        a.emit(cmp_imm, 2, N_FX); a.emit(b_cond, "gc_no", "hs")
        a.emit(movw, 1, setmap_addr & 0xFFFF); a.emit(movt, 1, setmap_addr >> 16); a.emit(ldrb_reg, 1, 1, 2)       # r1 = the set
        a.emit(cmp_imm, 1, 2); a.emit(b_cond, "gc_4", "ne"); a.emit(cmp_imm, 5, 2); a.emit(b_cond, "gc_no", "hs")      # Digitise: 2 knobs
        a.label("gc_4")
        a.emit(lsls_imm, 1, 1, 2); a.emit(adds_reg, 1, 1, 5)                                                       # r1 = 4 set + knob
        a.emit(adds_reg, 0, 4, 1); a.emit(ldrb_w, 0, 0, S_KNOB)
        a.emit(movw, 2, defaults_addr & 0xFFFF); a.emit(movt, 2, defaults_addr >> 16); a.emit(ldrb_reg, 1, 2, 1); a.emit(b, "gc_x")
        a.label("gc_no"); a.emit(movs_imm, 0, 0); a.emit(subs_imm8, 0, 1)
        a.label("gc_x"); a.emit(pop_list, [5], pc=True)
        a.label("c_gclrled")                                                   # (r0 = the LED buffer): while Clear is held, the selected effect's knobs blue at their default, red elsewhere
        a.emit(push_list, [4, 5, 6, 7], lr=True); a.emit(mov_reg, 6, 0)
        a.emit(bl, "c_gclrh"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl3_x", "eq")
        a.emit(bl, "c_gfst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gl3_x", "eq"); a.emit(mov_reg, 4, 0)
        a.emit(movs_imm, 7, 0)
        a.label("gl3_l")
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_gcur"); a.emit(mov_reg, 2, 0); a.emit(adds_imm8, 2, 1); a.emit(b_cond, "gl3_n", "eq")
        if GCLEAR2: a.emit(cmp_reg, 0, 1); a.emit(b_cond, "gl3_n", "ne"); a.emit(movs_imm, 2, GCLR_BLUE)
        else: a.emit(movs_imm, 2, GCLR_RED); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "gl3_p", "ne"); a.emit(movs_imm, 2, GCLR_BLUE)
        a.label("gl3_p")
        a.emit(lsls_imm, 1, 7, 1); a.emit(adds_imm8, 1, 2 * 34); a.emit(raw, h(0x5200 | 1 << 6 | 6 << 3 | 2))    # strh r2,[r6,r1]
        a.label("gl3_n")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 4); a.emit(b_cond, "gl3_l", "lo")
        a.label("gl3_x"); a.emit(mov_reg, 0, 6); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_gknob (view, knob, delta)
    a.label("c_gknob")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 7, 2)
    a.emit(bl, "c_gact"); zjmp(0, "gk_stock"); a.emit(mov_reg, 4, 0)
    a.emit(cmp_imm, 6, 4); bc("gk_out", "hs")
    if GCLEAR:                                                                 # Clear held: right = the default (as a delta), left = nothing
        a.emit(bl, "c_gclrh"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gk_nc", "eq")
        a.emit(cmp_imm, 7, 0); bc("gk_out", "le")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_gcur"); a.emit(mov_reg, 2, 0); a.emit(adds_imm8, 2, 1); bc("gk_out", "eq")
        a.emit(subs_reg, 7, 1, 0)
        a.label("gk_nc")
    if SMP:                                                                    # the sample selected: its own knobs
        a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, SMP_SEL); a.emit(b_cond, "gk_nsm", "ne")
        a.emit(bl, "c_smknob"); a.emit(b, "gk_out")
        a.label("gk_nsm")
    if GLITCH:
        a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, GL_SEL); a.emit(b_cond, "gk_ngl", "ne")
        a.emit(bl, "c_glknob"); a.emit(b, "gk_out")
        a.label("gk_ngl")
    a.emit(ldrb_imm, 0, 4, S_SEL)
    a.emit(movw, 1, setmap_addr & 0xFFFF); a.emit(movt, 1, setmap_addr >> 16); a.emit(ldrb_reg, 0, 1, 0)
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 0, 0, 6); a.emit(adds_imm8, 0, S_KNOB)   # r0 = offset
    a.emit(ldrb_reg, 1, 4, 0); a.emit(adds_reg, 1, 1, 7)                       # value + delta (signed)
    a.emit(cmp_imm, 1, 0); bc("gk_lo", "ge"); a.emit(movs_imm, 1, 0)
    a.label("gk_lo"); a.emit(cmp_imm, 1, 127); bc("gk_hi", "le"); a.emit(movs_imm, 1, 127)
    a.label("gk_hi"); a.emit(raw, h(0x5421))                                   # strb r1,[r4,r0]
    a.emit(movs_imm, 1, 1); a.emit(strb_imm, 1, 4, S_DIRTY)
    a.label("gk_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("gk_stock")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, MIX_KNOB)

    # ---- c_gleds (view) -> LED buffer
    a.label("c_gleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0)
    dmark(D_LEDS)
    a.emit(bl, "c_gact"); zjmp(0, "gl_stock"); a.emit(mov_reg, 4, 0)
    if LED_N > 32:                                   # stock buffer: keep its entries 32/33, knob LEDs from Master FX
        a.emit(mov_reg, 0, 5); a.emit(bl, MIX_LEDS); a.emit(mov_reg, 7, 0)    # r7 = stock buffer (refreshed)
    if LEDBUF:                                                                 # r6 = the buffer: in the project's record (see use_ledbuf)
        a.emit(movw, 6, 0xD71C); a.emit(movt, 6, 0x2003); a.emit(ldr_imm, 6, 6, 0x14); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "gl_ob", "eq")
        a.emit(movw, 0, LEDBUF_OFF & 0xFFFF); a.emit(movt, 0, LEDBUF_OFF >> 16); a.emit(adds_reg, 6, 6, 0); a.emit(b, "gl_bk")
        a.label("gl_ob")
    a.emit(mov_reg, 6, 4); a.emit(adds_imm8, 6, S_LED)                        # r6 = buffer
    if LEDBUF: a.label("gl_bk")
    a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
    a.label("gl_clr"); a.emit(raw, h(0x5270))                                  # strh r0,[r6,r1]
    a.emit(adds_imm8, 1, 2); a.emit(cmp_imm, 1, 64); bc("gl_clr", "lo")
    if LED_N > 32:
        for k in (32, 33):
            a.emit(raw, ldrh_w(0, 7, 2 * k)); a.emit(raw, strh_w(0, 6, 2 * k))
    a.emit(ldrb_imm, 7, 4, S_HELD); a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(orrs_reg, 7, 0)   # r7 = on bits
    for i, (on, dim) in enumerate(pal_codes):
        a.emit(movw, 0, dim); a.emit(lsrs_imm, 1, 7, i + 1); a.emit(b_cond, f"gl_d{i}", "cc")
        a.emit(movw, 0, on)
        a.label(f"gl_d{i}"); a.emit(strh_imm, 0, 6, 2 * i)
    a.emit(ldrb_imm, 1, 4, S_SEL); a.emit(cmp_imm, 1, N_FX); bc("gl_knobs" if LED_N > 32 else "gl_ret", "hs")
    a.emit(lsls_imm, 2, 1, 1); a.emit(ldrh_reg, 0, 6, 2)                       # selected pad's colour (on or dim)
    a.emit(movw, 3, pal_codes[0][0]) if False else None
    a.emit(adds_imm8, 2, 16); a.emit(raw, h(0x52B0))                           # strh r0,[r6,r2]  (row 2)
    if LED_N > 32:
        a.label("gl_knobs")
        # entries 32/33 from the stock buffer (r7); knobs: selected effect's colour on its parameters, others off
        a.emit(ldrb_imm, 1, 4, S_SEL)
        a.emit(movs_imm, 0, 0)
        for k in range(8): a.emit(raw, strh_w(0, 6, 2 * (34 + k)))
        a.emit(cmp_imm, 1, N_FX); bc("gl_ret", "hs")
        for i, (on, dim) in enumerate(pal_codes):
            nk = 2 if SETMAP[i] == 2 and not DIGI4 else 4                      # Digitise has 2 parameters (4 with DIGI4)
            a.emit(cmp_imm, 1, i); a.emit(b_cond, f"gk_n{i}", "ne")
            a.emit(movw, 0, on)
            for k in range(nk):
                if DIGI4 and SETMAP[i] == 2 and k == 3:                        # Digitise K4, bipolar: |K4 - 64| x 2 as the brightness
                    a.emit(ldrb_w, 2, 4, S_KNOB + 4 * SETMAP[i] + k); a.emit(subs_imm8, 2, 64); a.emit(b_cond, f"gk_b{i}", "ge"); a.emit(raw, h(0x4252))   # rsbs r2, r2, #0
                    a.label(f"gk_b{i}"); a.emit(lsls_imm, 2, 2, 1); a.emit(cmp_imm, 2, 127); a.emit(b_cond, f"gk_c{i}", "ls"); a.emit(movs_imm, 2, 127)
                    a.label(f"gk_c{i}"); a.emit(adds_imm8, 2, 2); a.emit(lsls_imm, 2, 2, 8); a.emit(orrs_reg, 2, 0); a.emit(raw, strh_w(2, 6, 2 * (34 + k)))
                elif DIGI4 and not MSWAP and SETMAP[i] == 4 and k == 1:        # the kind of the mechanical gesture: the colour of the stretch, brighter along it
                    a.emit(ldrb_w, 2, 4, S_KNOB + 4 * SETMAP[i] + k); a.emit(movs_imm, 3, 0x7F); a.emit(ands_reg, 2, 3); a.emit(lsls_imm, 2, 2, 2)
                    a.emit(lsrs_imm, 3, 2, 7)                                   # r3 = the stretch 0..3
                    for q, col in enumerate(MECH_COL):
                        a.emit(cmp_imm, 3, q); a.emit(b_cond, f"gk_m{i}_{q}", "ne"); a.emit(movs_imm, 3, col); a.emit(b, f"gk_me{i}"); a.label(f"gk_m{i}_{q}")
                    a.emit(movs_imm, 3, MECH_COL[-1])
                    a.label(f"gk_me{i}")
                    a.emit(push_list, [0]); a.emit(movs_imm, 0, 127); a.emit(ands_reg, 2, 0); a.emit(movs_imm, 0, 127 - MECH_MINB); a.emit(muls, 2, 0)
                    a.emit(lsrs_imm, 2, 2, 7); a.emit(adds_imm8, 2, MECH_MINB + 2); a.emit(lsls_imm, 2, 2, 8); a.emit(orrs_reg, 2, 3); a.emit(pop_list, [0])
                    a.emit(raw, strh_w(2, 6, 2 * (34 + k)))
                elif KNOB_BRIGHT:                                              # colour | (value + 2) << 8: the converter hook of persist19.KNOB_LEVELS splits it
                    a.emit(ldrb_w, 2, 4, S_KNOB + 4 * SETMAP[i] + k); a.emit(adds_imm8, 2, 2); a.emit(lsls_imm, 2, 2, 8); a.emit(orrs_reg, 2, 0)
                    a.emit(raw, strh_w(2, 6, 2 * (34 + k)))
                else:
                    a.emit(raw, strh_w(0, 6, 2 * (34 + k)))
            a.emit(b, "gl_ret")
            a.label(f"gk_n{i}")
    a.label("gl_ret"); a.emit(mov_reg, 0, 6); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("gl_stock")
    a.emit(mov_reg, 0, 5); a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, MIX_LEDS)

    if DIAG:
        # ---- c_dleds (synth Preset view slot 7): SC15's c_sleds, then with Shift held
        #   pads 9-16  = free heap bytes / 16 (binary, pad 9 = MSB), pad 17 = Master FX block ok, 18 = mode,
        #   19..23 = sticky bits (Shift+Mixer, Mixer, c_gpress, c_gleds, c_gact true), 24 = heap limit is ours
        a.label("c_dleds")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(bl, L["c_sleds"]); a.emit(mov_reg, 5, 0)                       # r5 = buffer
        a.emit(bl, c_shift); zjmp(0, "dl_out")
        a.emit(movw, 6, 0x2B48); a.emit(movt, 6, 0x2000); a.emit(ldr_imm, 6, 6, 0)
        a.emit(movw, 0, HEAP_TOP & 0xFFFF); a.emit(movt, 0, HEAP_TOP >> 16)
        a.emit(subs_reg, 6, 0, 6); a.emit(lsrs_imm, 6, 6, 4)                   # r6 = free / 16
        a.emit(movs_imm, 7, 0)                                                 # r7 = row-3 bits
        a.emit(bl, "c_gfst"); a.emit(cmp_imm, 0, 0); bc("dl_nb", "eq")
        a.emit(ldrb_imm, 7, 0, S_DIAG); a.emit(movs_imm, 1, 0x7C); a.emit(ands_reg, 7, 1)
        a.emit(adds_imm8, 7, 1)                                                # bit 0: block ok
        a.emit(ldrb_imm, 1, 0, S_MODE); a.emit(cmp_imm, 1, 0); bc("dl_nb", "eq"); a.emit(adds_imm8, 7, 2)
        a.label("dl_nb")
        a.emit(movw, 1, 0x2B44); a.emit(movt, 1, 0x2000); a.emit(ldr_imm, 1, 1, 0)
        a.emit(movw, 2, s14.ST & 0xFFFF); a.emit(movt, 2, s14.ST >> 16); a.emit(cmp_reg, 1, 2); bc("dl_nl", "ne")
        a.emit(movs_imm, 1, 0x80); a.emit(orrs_reg, 7, 1)
        a.label("dl_nl")
        for i in range(8):                                                     # row 2: r6 bit 7-i -> pad 9+i
            a.emit(movs_imm, 0, DIAG_DIM); a.emit(lsrs_imm, 1, 6, 8 - i); a.emit(b_cond, f"dl_a{i}", "cc")
            a.emit(movs_imm, 0, DIAG_ON)
            a.label(f"dl_a{i}"); a.emit(strh_imm, 0, 5, 2 * (8 + i))
        for i in range(8):                                                     # row 3: r7 bit i -> pad 17+i
            a.emit(movs_imm, 0, DIAG_DIM); a.emit(lsrs_imm, 1, 7, i + 1); a.emit(b_cond, f"dl_b{i}", "cc")
            a.emit(movs_imm, 0, DIAG_ON)
            a.label(f"dl_b{i}"); a.emit(strh_imm, 0, 5, 2 * (16 + i))
        a.label("dl_out"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_dw: DSP_WRITE(0, r0 << 8, r1)
    a.label("c_dw")
    a.emit(mov_reg, 2, 1); a.emit(lsls_imm, 1, 0, 8); a.emit(movs_imm, 0, 0); a.emit(b_w, DSP_WRITE)
    # ---- c_dwc: write r0 to X:r1 unless equal to the cache word at [r4 + r2]
    a.label("c_dwc")
    a.emit(raw, h(0x58A3))                                                     # ldr r3,[r4,r2]
    a.emit(cmp_reg, 3, 0); bc("dc_same", "eq")
    a.emit(raw, h(0x50A0))                                                     # str r0,[r4,r2]
    a.emit(b, "c_dw")
    a.label("dc_same"); a.emit(raw, h(0x4770))

    # ---- c_tri(r0 = period ms, r1 = t0) -> r0 = triangle 0..127 (0 at t0), r1 = phase ms (clobbers r2, r3)
    a.label("c_tri")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(bl, c_now); a.emit(subs_reg, 0, 0, 5)                               # elapsed
    a.emit(cmp_imm, 4, 1); bc("tr_p", "hs"); a.emit(movs_imm, 4, 1)
    a.label("tr_p")
    a.emit(raw, udiv(1, 0, 4)); a.emit(raw, mls(1, 1, 4, 0))                   # r1 = elapsed % period
    a.emit(lsls_imm, 0, 1, 8); a.emit(raw, udiv(0, 0, 4))                      # 0..255
    a.emit(cmp_imm, 0, 128); bc("tr_up", "lo")
    a.emit(movs_imm, 2, 255); a.emit(subs_reg, 0, 2, 0)
    a.label("tr_up"); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_cut(r0 = tri 0..127, r1 = centre 0..127, r2 = depth 0..127) -> r0 = clamp(centre - depth/2 + tri*depth/127)
    a.label("c_cut")
    a.emit(muls, 0, 2); a.emit(movs_imm, 3, 127); a.emit(raw, udiv(0, 0, 3))
    a.emit(adds_reg, 0, 0, 1); a.emit(lsrs_imm, 2, 2, 1); a.emit(subs_reg, 0, 0, 2)
    a.emit(cmp_imm, 0, 0); bc("ct_lo", "ge"); a.emit(movs_imm, 0, 0)
    a.label("ct_lo"); a.emit(cmp_imm, 0, 127); bc("ct_hi", "le"); a.emit(movs_imm, 0, 127)
    a.label("ct_hi"); a.emit(raw, h(0x4770))

    if DIGI4:
        # ---- c_digenv (r4 = the block; Digitise is on): K4 off the middle = the amount of the effect follows an attack (left) or a decay (right) from its start
        a.label("c_digenv")
        a.emit(push_list, [5, 6, 7], lr=True)
        knob(5, 4, 2, 3); a.emit(subs_imm8, 5, 64); bc("dv_x", "eq")                # r5 = d
        a.emit(mov_reg, 6, 5); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "dv_m", "ge"); a.emit(raw, h(0x4276))     # rsbs r6, r6, #0
        a.label("dv_m"); a.emit(muls, 6, 6); a.emit(adds_imm8, 6, 20)             # r6 = the time: 20 + d x d ms
        a.emit(movs_imm, 0, 0); a.emit(movw, 1, G.VN_ST); a.emit(bl, 0x08029344); a.emit(lsrs_imm, 0, 0, 8); a.emit(mov_reg, 7, 0)
        a.emit(bl, c_now); a.emit(subs_reg, 0, 0, 7); a.emit(lsls_imm, 0, 0, 8); a.emit(lsrs_imm, 0, 0, 8)
        a.emit(movw, 1, 0x7FFF); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "dv_c", "ls"); a.emit(mov_reg, 0, 1)
        a.label("dv_c"); a.emit(movs_imm, 1, 127); a.emit(muls, 0, 1); a.emit(raw, udiv(0, 0, 6)); a.emit(cmp_imm, 0, 127); a.emit(b_cond, "dv_k", "ls"); a.emit(movs_imm, 0, 127)
        a.label("dv_k"); a.emit(mov_reg, 7, 0)                                      # r7 = x 0..127
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "dv_e", "lt"); a.emit(movs_imm, 0, 127); a.emit(subs_reg, 7, 0, 7)   # right: the decay; left: the attack
        a.label("dv_e")
        knob(1, 4, 2, 0); a.emit(muls, 1, 7); a.emit(lsrs_imm, 1, 1, 7); ldtab(0, "DGN", 1); a.emit(movw, 1, G.DG_N); a.emit(bl, "c_dw")
        knob(1, 4, 2, 1); a.emit(muls, 1, 7); a.emit(lsrs_imm, 1, 1, 7); ldtab(0, "DGM", 1); a.emit(movw, 1, G.DG_MASK); a.emit(bl, "c_dw")
        a.label("dv_x"); a.emit(pop_list, [5, 6, 7], pc=True)

    # ---- c_fxtick: DSP service tick (then SC14's c_gtick)
    a.label("c_fxtick")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, "c_gfst"); zjmp(0, "ft_out"); a.emit(mov_reg, 4, 0)
    a.emit(bl, "c_gact"); a.emit(cmp_imm, 0, 0); bc("ft_v", "ne")
    a.emit(movs_imm, 0, 0); a.emit(strb_imm, 0, 4, S_HELD)                     # view not showing: drop held pads
    a.label("ft_v")
    # r5 = DSP FX_ON from held|latch, r6 = active parameter-set bits
    a.emit(ldrb_imm, 7, 4, S_HELD); a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(orrs_reg, 7, 0)
    if SLOTS: a.emit(bl, "c_slotbits"); a.emit(orrs_reg, 7, 0)                # + effects driven by held FX slots
    if GLITCH: a.emit(bl, "c_fsqfx" if GL2 else "c_fxsq"); a.emit(movs_imm, 1, 0x3F); a.emit(ands_reg, 0, 1); a.emit(orrs_reg, 7, 0)   # + the FX step sequencer of the MIDI tracks (vcf21)
    if MECH:                                                                   # the Vinyl pad is the mechanical gesture: its bit drives the Glitch engine, not the DSP effect
        if MSWAP:                                                               # the gesture = pad 31 held, or the sequencer's bit 6
            a.emit(bl, "c_fsqfx"); a.emit(lsrs_imm, 1, 0, 6); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 1, 0)
            a.emit(ldrb_w, 0, 4, S_SLOT + 4 * GL_SLOT); a.emit(lsrs_imm, 0, 0, 7); a.emit(orrs_reg, 1, 0)
        else:
            a.emit(lsrs_imm, 1, 7, N_FX - 1); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 1, 0)
        a.emit(movs_imm, 0, 1 << (N_FX - 1)); a.emit(bics_reg, 7, 0); a.emit(bl, "c_mechtick")
    a.emit(movs_imm, 5, 0); a.emit(movs_imm, 6, 0)
    for i in range(N_FX):
        a.emit(lsrs_imm, 0, 7, i + 1); a.emit(b_cond, f"ft_n{i}", "cc")
        a.emit(movs_imm, 0, FXBITS[i]); a.emit(orrs_reg, 5, 0)
        a.emit(movs_imm, 0, 1 << SETMAP[i]); a.emit(orrs_reg, 6, 0)
        a.label(f"ft_n{i}")
    # newly active sets: t0 = now
    a.emit(ldrb_imm, 7, 4, S_PREV); a.emit(strb_imm, 6, 4, S_PREV)
    a.emit(bics_reg, 7, 6) if False else None
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 7, 6); a.emit(bics_reg, 7, 0)       # r7 = new bits
    zjmp(7, "ft_t0")
    a.emit(bl, c_now); a.emit(mov_reg, 1, 0)
    if DIGI4:                                                                   # Digitise switched on: its envelope starts (the time in the DSP), its parameters go again
        # (here, not in the loop below: its label of set 0, "ft_t0", is also the end's, so the loop only runs when the Gater comes on with the others)
        a.emit(lsrs_imm, 0, 7, 3); a.emit(b_cond, "ft_dg0", "cc")
        a.emit(push_list, [1]); a.emit(lsls_imm, 0, 1, 8); a.emit(lsrs_imm, 0, 0, 8); a.emit(movw, 1, G.VN_ST); a.emit(bl, "c_dw")
        a.emit(movs_imm, 0, 1); a.emit(strb_imm, 0, 4, S_DIRTY); a.emit(pop_list, [1])
        a.label("ft_dg0")
    for s in range(5):
        if SPCACHE and s == 2: a.label((f"ft_u{s}" if T0FIX else f"ft_t{s}")); continue                    # that word is the playhead cache
        if SMP and s == 4: a.label((f"ft_u{s}" if T0FIX else f"ft_t{s}")); continue                        # that word is the sample's record state
        a.emit(lsrs_imm, 0, 7, s + 1); a.emit(b_cond, (f"ft_u{s}" if T0FIX else f"ft_t{s}"), "cc")
        a.emit(str_imm, 1, 4, S_T0 + 4 * s)
        a.label((f"ft_u{s}" if T0FIX else f"ft_t{s}"))
    a.label("ft_t0")
    # FX_ON
    a.emit(ldrb_imm, 0, 4, S_FXON); a.emit(cmp_reg, 0, 5); bc("ft_on", "eq")
    a.emit(strb_imm, 5, 4, S_FXON); a.emit(movs_imm, 0, 1); a.emit(strb_imm, 0, 4, S_DIRTY)
    a.emit(mov_reg, 0, 5); a.emit(movw, 1, G.FX_ON); a.emit(bl, "c_dw")
    a.label("ft_on")
    # static parameters (all sets) when dirty
    a.emit(ldrb_imm, 0, 4, S_DIRTY); a.emit(cmp_imm, 0, 0); bc("ft_st", "eq")
    a.emit(movs_imm, 0, 0); a.emit(strb_imm, 0, 4, S_DIRTY)
    if MSWAP: a.emit(ldrb_w, 0, 4, S_SLOT + 4 * GL_SLOT + 1); a.emit(movs_imm, 1, 0x80); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 4, S_SLOT + 4 * GL_SLOT + 1)
    statics = [(0, 3, "GK", G.G_K), (1, 2, "AFQ", G.AF_Q), (2, 0, "DGN", G.DG_N), (2, 1, "DGM", G.DG_MASK),
               (3, 2, "PHFB", G.PH_FB), (3, 3, "MIX", G.PH_MIX), (4, 0, "VTH", G.VN_T), (4, 1, "VHISS", G.VN_HISS),
               (4, 2, "VLPK", G.VN_LPK), (4, 3, "VHPK", G.VN_HPK)]
    for s, k, tab, addr in statics:
        if MECH and s == 4: continue                                           # (the Vinyl parameters are not sent: X:VN_T holds the gesture's state)
        knob(1, 4, s, k); ldtab(0, tab, 1); a.emit(movw, 1, addr); a.emit(bl, "c_dw")
    if not MECH: a.emit(movw, 0, VN_CRAMP & 0xFFFF); a.emit(movt, 0, VN_CRAMP >> 16); a.emit(movw, 1, G.VN_CR); a.emit(bl, "c_dw")
    a.emit(raw, h(0x2000)); a.emit(raw, h(0x43C0))                             # r0 = 0xFFFFFFFF: force LFO rewrites
    for off in (S_CG, S_CF, S_CA): a.emit(raw, str_w(0, 4, off))
    a.label("ft_st")
    if DIGI4: a.emit(lsrs_imm, 0, 6, 3); bc("ft_dg", "cc"); a.emit(bl, "c_digenv"); a.label("ft_dg")
    # Gater: period = beat*4/div ; open while phase*128 < duty*period ; G = open ? 1 : GOFF[depth]
    a.emit(lsrs_imm, 0, 6, 1); bc("ft_g", "cc")
    a.emit(bl, c_beat); a.emit(lsls_imm, 5, 0, 2)                              # r5 = bar ms
    knob(1, 4, 0, 0); ldtab(0, "GDIV", 1); a.emit(raw, udiv(5, 5, 0))         # r5 = period
    a.emit(mov_reg, 0, 5); a.emit(ldr_imm, 1, 4, S_T0); a.emit(bl, "c_tri")   # r1 = phase ms
    a.emit(lsls_imm, 1, 1, 7)                                                  # phase*128
    knob(0, 4, 0, 2); a.emit(movs_imm, 2, 112); a.emit(muls, 0, 2); a.emit(movs_imm, 2, 127); a.emit(raw, udiv(0, 0, 2))
    a.emit(adds_imm8, 0, 8); a.emit(muls, 0, 5)                                # duty*period
    a.emit(cmp_reg, 1, 0); bc("ft_gc", "hs")
    a.emit(movw, 0, 0xFFFF); a.emit(movt, 0, 0x7F); a.emit(b, "ft_gw")
    a.label("ft_gc"); knob(1, 4, 0, 1); ldtab(0, "GOFF", 1)
    a.label("ft_gw"); a.emit(movw, 1, G.G_TGT); a.emit(movs_imm, 2, S_CG); a.emit(bl, "c_dwc")
    a.label("ft_g")
    # Auto-Filter: period = beat*n16/4 ; idx = cut(127 - tri, centre, depth) ; f = AFTAB[idx]
    a.emit(lsrs_imm, 0, 6, 2); bc("ft_a", "cc")
    a.emit(bl, c_beat); a.emit(mov_reg, 5, 0)
    knob(1, 4, 1, 0); ldtab(0, "AFN", 1); a.emit(muls, 0, 5); a.emit(lsrs_imm, 0, 0, 2)
    a.emit(ldr_imm, 1, 4, S_T0 + 4); a.emit(bl, "c_tri")
    a.emit(movs_imm, 1, 127); a.emit(subs_reg, 0, 1, 0)
    knob(1, 4, 1, 3); knob(2, 4, 1, 1); a.emit(bl, "c_cut")
    a.emit(mov_reg, 1, 0); ldtab(0, "AFTAB", 1)
    a.emit(movw, 1, G.AF_F); a.emit(movs_imm, 2, S_CF); a.emit(bl, "c_dwc")
    a.label("ft_a")
    # Phaser: period = PHPER[rate] ; idx = cut(tri, 64, depth) ; A = PHTAB[idx]
    a.emit(lsrs_imm, 0, 6, 4); bc("ft_p", "cc")
    knob(1, 4, 3, 0); ldtab(0, "PHPER", 1)
    a.emit(ldr_imm, 1, 4, S_T0 + 12); a.emit(bl, "c_tri")
    a.emit(movs_imm, 1, 64); knob(2, 4, 3, 1); a.emit(bl, "c_cut")
    a.emit(mov_reg, 1, 0); ldtab(0, "PHTAB", 1)
    a.emit(movw, 1, G.PH_A); a.emit(movs_imm, 2, S_CA); a.emit(bl, "c_dwc")
    a.label("ft_p")
    if SMP: a.emit(bl, "c_smtick")
    if GLITCH: a.emit(bl, "c_gltick")
    a.label("ft_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, c_gtick)
    if SLOTS:
        slots_code(a, L, setmap_addr, pal_codes, bc, zjmp)
    if SMP:
        sampler_code(a, L, tabaddr, bc, zjmp)
    if GLITCH:
        glitch_code(a, dict(L, setmap_addr=setmap_addr, pal_codes=pal_codes), bc, zjmp)
    if MECH:
        mech_code(a, L, bc, zjmp)
    return a.assemble()


def mech_code(a, L, bc, zjmp):
    """SC39.7 (use_mech): c_mechtick(r1 = the gesture's pad is on; r4 = the Master FX block), from the DSP service tick: DSP reads / writes only, no lock taken."""
    import granular_dsp as GD
    KG = S_SLOT + 4 * GL_SLOT
    DSP_READ = 0x08029344
    E = a.emit
    udiv = s14.udiv
    def asr7(r): E(raw, h(0x1000 | 7 << 6 | r << 3 | r))                              # asrs r, r, #7
    def neg(rd, rm): E(raw, h(0x4240 | rm << 3 | rd))                                 # rsbs rd, rm, #0
    def vk(rd, k): E(ldrb_w, rd, 4, (KG if MSWAP else S_KNOB + 16) + k); E(movs_imm, 3, 0x7F); E(ands_reg, rd, 3)      # the gesture's knob k (clobbers r3)
    def now22(): E(bl, L["c_now"]); E(lsls_imm, 0, 0, 10); E(lsrs_imm, 0, 0, 10)      # r0 = the time, 22 bits

    # ---- mk_shape(r0 = kind 0..4; r5 = y, r6 = p) -> r0 = the speed -127..127; clobbers r1-r3
    a.label("mk_shape")
    E(cmp_imm, 0, 0); E(b_cond, "ms_1", "ne"); E(mov_reg, 0, 5); E(raw, h(0x4770))                  # tape stop: y
    a.label("ms_1"); E(cmp_imm, 0, 1); E(b_cond, "ms_2", "ne")
    E(lsls_imm, 0, 6, 1); E(subs_imm8, 0, 127); E(b_cond, "ms_1p", "ge"); neg(0, 0)                 # baby scratch: the triangle |2p - 127| x 2 - 127, dying with y
    a.label("ms_1p"); E(lsls_imm, 0, 0, 1); E(subs_imm8, 0, 127); E(muls, 0, 5); asr7(0); E(raw, h(0x4770))
    a.label("ms_2"); E(cmp_imm, 0, 2); E(b_cond, "ms_3", "ne")
    E(lsrs_imm, 1, 6, 5)                                                                             # tear scratch: four steps per movement
    for q, val in enumerate(MECH_TEAR):
        E(cmp_imm, 1, q); E(b_cond, f"ms_t{q}", "ne")
        E(movs_imm, 0, abs(val))
        if val < 0: neg(0, 0)
        E(b, "ms_tm"); a.label(f"ms_t{q}")
    E(movs_imm, 0, 0)
    a.label("ms_tm"); E(muls, 0, 5); asr7(0); E(raw, h(0x4770))
    a.label("ms_3"); E(cmp_imm, 0, 3); E(b_cond, "ms_4", "ne")
    E(mov_reg, 0, 5); E(muls, 0, 5); asr7(0); neg(0, 0); E(raw, h(0x4770))                           # back spin: -y x y
    a.label("ms_4"); E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "ms_x", "eq"); E(movs_imm, 0, 127)   # rattle: the tape runs until the end
    a.label("ms_x"); E(raw, h(0x4770))

    a.label("c_mechtick")
    E(push_list, [5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(ldrb_w, 6, 4, KG + 3); E(lsrs_imm, 6, 6, 7)                                     # r6 = a gesture runs
    E(cmp_imm, 5, 0); E(b_cond, "mk_off", "eq")
    E(cmp_imm, 6, 0); E(b_cond, "mk_p1", "eq")                                        # on, nothing running: the stop starts
    E(movs_imm, 0, 0); E(movw, 1, G.VN_T); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8); E(mov_reg, 7, 0)
    E(lsrs_imm, 0, 7, 22); E(cmp_imm, 0, 1); bc("mk_run", "eq")
    a.label("mk_p1"); E(movs_imm, 6, 1); E(b, "mk_new")
    a.label("mk_off")
    E(cmp_imm, 6, 0); bc("mk_x", "eq")
    E(movs_imm, 0, 0); E(movw, 1, G.VN_T); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8); E(mov_reg, 7, 0)
    E(lsrs_imm, 0, 7, 22); E(cmp_imm, 0, 1); bc("mk_run", "ne")
    E(movs_imm, 6, 2)                                                                 # let go: the start begins
    a.label("mk_new")                                                                 # r6 = the new phase: its time; the Glitch's delay and chaos off
    E(ldrb_w, 0, 4, KG + 3); E(movs_imm, 1, 0x80); E(orrs_reg, 0, 1); E(strb_w, 0, 4, KG + 3)
    now22(); E(lsls_imm, 1, 6, 22); E(orrs_reg, 0, 1); E(mov_reg, 7, 0); E(movw, 1, G.VN_T); E(bl, "c_dw")
    E(movs_imm, 0, 0); E(movw, 1, GD.GARM + 3); E(bl, "c_dw"); E(movs_imm, 0, 0); E(movw, 1, GD.GARM + 4); E(bl, "c_dw")
    a.label("mk_run")                                                                 # r7 = phase << 22 | t0
    E(lsrs_imm, 6, 7, 22)                                                             # r6 = the phase (1 the stop, 2 the start)
    now22(); E(subs_reg, 0, 0, 7); E(lsls_imm, 0, 0, 10); E(lsrs_imm, 0, 0, 10); E(mov_reg, 7, 0)       # r7 = the time gone
    vk(1, 2); E(cmp_imm, 6, 1); E(b_cond, "mk_k", "eq"); vk(1, 3)
    a.label("mk_k"); E(mov_reg, 0, 1); E(muls, 0, 1); E(lsrs_imm, 0, 0, MECH_TK); E(adds_imm8, 0, MECH_T0)   # r0 = the time of the gesture
    E(movw, 1, 0x7FFF); E(cmp_reg, 7, 1); E(b_cond, "mk_c", "ls"); E(mov_reg, 7, 1)
    a.label("mk_c"); E(movs_imm, 1, 127); E(muls, 7, 1); E(raw, udiv(7, 7, 0)); E(cmp_imm, 7, 127); E(b_cond, "mk_xk", "ls"); E(movs_imm, 7, 127)
    a.label("mk_xk")                                                                  # r7 = x 0..127
    E(cmp_imm, 6, 2); E(b_cond, "mk_sh", "ne")
    E(cmp_imm, 7, 127); E(b_cond, "mk_inv", "lo")
    E(ldrb_w, 0, 4, KG + 3); E(movs_imm, 1, 0x80); E(bics_reg, 0, 1); E(strb_w, 0, 4, KG + 3)       # the start is over: the Glitch's own state goes again
    E(ldrb_w, 0, 4, KG + 1); E(movs_imm, 1, 0x80); E(orrs_reg, 0, 1); E(strb_w, 0, 4, KG + 1)
    E(b, "mk_x")
    a.label("mk_inv"); E(movs_imm, 0, 127); E(subs_reg, 7, 0, 7)                      # the start = the stop backwards
    a.label("mk_sh")
    E(movs_imm, 0, 127); E(subs_reg, 5, 0, 7)                                         # r5 = y
    vk(0, 0); E(lsrs_imm, 0, 0, 4); E(adds_imm8, 0, 1); E(mov_reg, 6, 7); E(muls, 6, 0); E(movs_imm, 0, 127); E(ands_reg, 6, 0)   # r6 = p: the place in a movement
    vk(7, 1); E(lsls_imm, 7, 7, 2)                                                    # r7 = K2 x 4: the kind (bits 7-8) and the mix (bits 0-6)
    E(lsrs_imm, 0, 7, 7); E(bl, "mk_shape"); E(push_list, [0])
    E(lsrs_imm, 0, 7, 7); E(adds_imm8, 0, 1); E(bl, "mk_shape")
    E(movs_imm, 1, 127); E(ands_reg, 1, 7); E(muls, 0, 1)                             # b x w
    E(pop_list, [2]); E(movs_imm, 3, 128); E(subs_reg, 3, 3, 1); E(muls, 2, 3); E(adds_reg, 0, 0, 2); asr7(0)   # v = (a (128 - w) + b w) >> 7
    E(movs_imm, 1, 63); E(muls, 0, 1); E(adds_imm8, 0, 64); asr7(0); E(adds_imm8, 0, 64)      # 127 -> 127 (normal), 0 -> 64 (stopped), -127 -> 1
    E(cmp_imm, 0, 1); E(b_cond, "mk_v1", "ge"); E(movs_imm, 0, 1)
    a.label("mk_v1"); E(cmp_imm, 0, 127); E(b_cond, "mk_v2", "le"); E(movs_imm, 0, 127)
    a.label("mk_v2"); E(movw, 1, GD.GARM + 1); E(bl, "c_dw")
    E(movs_imm, 0, 127)                                                               # the repeat: continuous, closing towards the rattle
    E(lsrs_imm, 1, 7, 7); E(cmp_imm, 1, 3); E(b_cond, "mk_r", "lo")
    E(mov_reg, 0, 5); E(muls, 0, 5); asr7(0); E(subs_imm8, 0, 127)                    # (y x y >> 7) - 127 <= 0
    E(movs_imm, 1, 127); E(ands_reg, 1, 7); E(muls, 0, 1); asr7(0); E(adds_imm8, 0, 127)
    E(cmp_imm, 0, 1); E(b_cond, "mk_r", "ge"); E(movs_imm, 0, 1)
    a.label("mk_r"); E(movw, 1, GD.GARM + 2); E(bl, "c_dw")
    E(movw, 0, GD.GMAGIC & 0xFFFF); E(movt, 0, GD.GMAGIC >> 16); E(movw, 1, GD.GARM); E(bl, "c_dw")
    a.label("mk_x"); E(pop_list, [5, 6, 7], pc=True)


def glitch_code(a, L, bc, zjmp):
    """SC36 (use_glitch): r4 = the Master FX block.  KG = the 4 bytes of slot 5 (K1..K4 in bits 0-6, held = bit 7 of KG, to send = bit 7 of KG + 1)."""
    import granular_dsp as GD
    KG = S_SLOT + 4 * GL_SLOT
    def setbit(off, on):                              # bit 7 of byte off (clobbers r0, r1)
        a.emit(ldrb_w, 0, 4, off); a.emit(movs_imm, 1, 0x80); a.emit(orrs_reg if on else bics_reg, 0, 1); a.emit(strb_w, 0, 4, off)

    a.label("c_fxsq")                                                          # -> r0 = the effects the FX step sequencer of the MIDI tracks wants (bits 0-5 = top pads, bit 6 = the Glitch):
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))                             #    0 here; vcf21.install (use_fxseq) puts a b.w to its routine over these 4 bytes

    if GL2:
        a.label("c_fsqfx")                                                     # r4 = the block -> r0 = effect bits (0-5) | the Glitch (bit 6) of the slots the FX sequencer wants
        a.emit(push_list, [5, 6, 7], lr=True)
        a.emit(bl, "c_fxsq"); a.emit(mov_reg, 5, 0)
        if FSQRAND:                                                            # bit 6 = random: one of the slots that play something, by the seed in bits 8-15
            a.emit(movs_imm, 0, 0x40); a.emit(tst_reg, 5, 0); bc("fr_x", "eq"); a.emit(bics_reg, 5, 0)
            a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 0)
            a.label("fr_l")
            a.emit(cmp_imm, 7, GL_SLOT); bc("fr_y", "eq")
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, GL_SEL); bc("fr_y", "eq"); a.emit(cmp_imm, 0, N_FX); bc("fr_n", "hs")
            a.label("fr_y"); a.emit(movs_imm, 0, 1); a.emit(lsls_reg, 0, 7); a.emit(orrs_reg, 6, 0)
            a.label("fr_n"); a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 6); bc("fr_l", "lo")
            a.emit(movs_imm, 1, 0); a.emit(movs_imm, 7, 0)                     # r1 = how many
            a.label("fr_c"); a.emit(lsrs_reg, 0, 6, 7) if False else None
            a.emit(mov_reg, 0, 6); a.emit(lsrs_reg, 0, 7); a.emit(lsls_imm, 0, 0, 31); a.emit(b_cond, "fr_c0", "eq"); a.emit(adds_imm8, 1, 1)
            a.label("fr_c0"); a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 6); a.emit(b_cond, "fr_c", "lo")
            a.emit(cmp_imm, 1, 0); bc("fr_x", "eq")
            a.emit(lsrs_imm, 2, 5, 8); a.emit(movs_imm, 0, 0xFF); a.emit(ands_reg, 2, 0); a.emit(muls, 2, 1); a.emit(lsrs_imm, 2, 2, 8)   # r2 = which of them
            a.emit(movs_imm, 7, 0)
            a.label("fr_p")
            a.emit(mov_reg, 0, 6); a.emit(lsrs_reg, 0, 7); a.emit(lsls_imm, 0, 0, 31); a.emit(b_cond, "fr_q", "eq")
            a.emit(cmp_imm, 2, 0); a.emit(b_cond, "fr_s", "eq"); a.emit(subs_imm8, 2, 1)
            a.label("fr_q"); a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 6); a.emit(b_cond, "fr_p", "lo"); a.emit(b, "fr_x")
            a.label("fr_s"); a.emit(movs_imm, 0, 1); a.emit(lsls_reg, 0, 7); a.emit(orrs_reg, 5, 0)
            a.label("fr_x")
        a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 0)                         # r5 = slots, r6 = result, r7 = slot j
        a.label("fq_l")
        a.emit(movs_imm, 0, 1); a.emit(lsls_reg, 0, 7); a.emit(tst_reg, 5, 0); bc("fq_n", "eq")
        a.emit(cmp_imm, 7, GL_SLOT); bc("fq_g", "eq")                          # pad 31 itself: the Glitch
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, GL_SEL); bc("fq_ga", "eq")
        a.emit(cmp_imm, 0, N_FX); bc("fq_n", "hs")                             # unassigned / the sample: nothing
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 6, 1)
        a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 7); a.emit(bl, "c_sldif"); a.emit(b, "fq_n")
        a.label("fq_ga")                                                       # a slot of the Glitch: its knobs (bit 7 of the live bytes kept), then on
        a.emit(lsls_imm, 0, 7, 2); a.emit(adds_reg, 0, 0, 4)
        for k in range(4):
            a.emit(ldrb_w, 1, 0, S_SLOT + k); a.emit(lsls_imm, 1, 1, 25); a.emit(lsrs_imm, 1, 1, 25)
            a.emit(ldrb_w, 2, 4, KG + k); a.emit(lsls_imm, 3, 2, 25); a.emit(lsrs_imm, 3, 3, 25); a.emit(cmp_reg, 3, 1); a.emit(b_cond, f"fq_k{k}", "eq")
            a.emit(movs_imm, 3, 0x80); a.emit(ands_reg, 2, 3); a.emit(orrs_reg, 2, 1); a.emit(strb_w, 2, 4, KG + k)
            a.emit(ldrb_w, 2, 4, KG + 1); a.emit(orrs_reg, 2, 3); a.emit(strb_w, 2, 4, KG + 1)            # (r3 = 0x80: to send)
            a.label(f"fq_k{k}")
        a.label("fq_g"); a.emit(movs_imm, 0, 0x40); a.emit(orrs_reg, 6, 0)
        a.label("fq_n")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 6); bc("fq_l", "lo")
        a.emit(mov_reg, 0, 6); a.emit(pop_list, [5, 6, 7], pc=True)

        a.label("c_sldif")                                                     # r0 = slot j, r1 = effect k: the slot's copy -> the live parameters of k, only when they differ
        a.emit(push_list, [5, 6, 7], lr=True)
        a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1)
        a.emit(movw, 2, L["setmap_addr"] & 0xFFFF); a.emit(movt, 2, L["setmap_addr"] >> 16); a.emit(ldrb_reg, 2, 2, 1); a.emit(lsls_imm, 2, 2, 2); a.emit(adds_reg, 2, 2, 4)   # r2 = block + 4 set
        a.emit(lsls_imm, 3, 0, 2); a.emit(adds_reg, 3, 3, 4)                    # r3 = block + 4 j
        a.emit(movs_imm, 7, 0)
        a.label("sl_l")
        a.emit(adds_reg, 0, 3, 7); a.emit(ldrb_w, 0, 0, S_SLOT); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25)
        a.emit(adds_reg, 1, 2, 7); a.emit(ldrb_w, 1, 1, S_KNOB); a.emit(cmp_reg, 0, 1); bc("sl_d", "ne")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 4); bc("sl_l", "lo")
        a.emit(pop_list, [5, 6, 7], pc=True)
        a.label("sl_d"); a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(bl, "c_sload"); a.emit(pop_list, [5, 6, 7], pc=True)

        a.label("c_slotcol")                                                   # r0 = slot j -> r0 = the colour of what it plays (0x03 dim white: nothing); from vcf21
        a.emit(push_list, [4, 5], lr=True)
        a.emit(mov_reg, 5, 0); a.emit(bl, "c_gfst"); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 0, 0x03); a.emit(cmp_imm, 4, 0); bc("sc_x", "eq")
        a.emit(movs_imm, 0, GL_ON); a.emit(cmp_imm, 5, GL_SLOT); bc("sc_x", "eq")
        a.emit(mov_reg, 0, 5); a.emit(bl, "c_stype")
        for kk, (on, dim) in enumerate(L["pal_codes"]):
            a.emit(cmp_imm, 0, kk); a.emit(b_cond, f"sc_c{kk}", "ne"); a.emit(movs_imm, 0, on); a.emit(b, "sc_x")
            a.label(f"sc_c{kk}")
        a.emit(movs_imm, 1, SMP_ON); a.emit(cmp_imm, 0, SMP_SEL); a.emit(b_cond, "sc_s", "eq")
        a.emit(movs_imm, 1, GL_ON); a.emit(cmp_imm, 0, GL_SEL); a.emit(b_cond, "sc_s", "eq"); a.emit(movs_imm, 1, 0x03)
        a.label("sc_s"); a.emit(mov_reg, 0, 1)
        a.label("sc_x"); a.emit(pop_list, [4, 5], pc=True)

    a.label("c_glpress")                                                       # pad 31 pressed: selected, held, to send
    a.emit(push_list, [5], lr=True)
    a.emit(movs_imm, 0, GL_SEL); a.emit(strb_imm, 0, 4, S_SEL)
    setbit(KG, True); setbit(KG + 1, True)
    a.emit(pop_list, [5], pc=True)
    a.label("c_glrel")                                                         # pad 31 released
    a.emit(push_list, [5], lr=True)
    setbit(KG, False); setbit(KG + 1, True)
    a.emit(pop_list, [5], pc=True)

    if GL3:
        a.label("c_gl31p")                                                     # pad 31 pressed: the Glitch, and pad 31 held (bit GL_SLOT of S_SLOTH)
        a.emit(push_list, [5], lr=True)
        a.emit(bl, "c_glpress")
        a.emit(ldrb_w, 0, 4, S_SLOTH); a.emit(movs_imm, 1, 1 << GL_SLOT); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 4, S_SLOTH)
        a.emit(pop_list, [5], pc=True)
        a.label("c_glrel3")                                                    # r0 = the released source (slot j; GL_SLOT = pad 31): a Glitch source still held plays on
        a.emit(push_list, [5, 6, 7], lr=True)
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0)
        a.emit(ldrb_w, 5, 4, S_SLOTH); a.emit(bics_reg, 5, 1); a.emit(strb_w, 5, 4, S_SLOTH)      # r5 = what is still held
        a.emit(movs_imm, 7, 0)
        a.label("g3_l")
        a.emit(cmp_imm, 7, GL_SLOT); a.emit(b_cond, "g3_n", "eq")
        a.emit(movs_imm, 0, 1); a.emit(lsls_reg, 0, 7); a.emit(tst_reg, 5, 0); a.emit(b_cond, "g3_n", "eq")
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, GL_SEL); a.emit(b_cond, "g3_n", "ne")
        a.emit(mov_reg, 0, 7); a.emit(movs_imm, 1, GL_SEL); a.emit(bl, "c_sload")                 # a Glitch slot still held: its knobs
        a.emit(bl, "c_glpress"); a.emit(pop_list, [5, 6, 7], pc=True)
        a.label("g3_n")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 7); a.emit(b_cond, "g3_l", "lo")
        a.emit(movs_imm, 0, 1 << GL_SLOT); a.emit(tst_reg, 5, 0); a.emit(b_cond, "g3_x", "ne")      # pad 31 still held: it plays on
        a.emit(bl, "c_glrel")
        a.label("g3_x"); a.emit(pop_list, [5, 6, 7], pc=True)

    a.label("c_glknob")                                                        # r6 = knob 0-3, r7 = delta: K clamped 0..127, bit 7 kept, to send
    a.emit(push_list, [5], lr=True)
    a.emit(adds_reg, 5, 4, 6); a.emit(ldrb_w, 0, 5, KG); a.emit(movs_imm, 2, 0x80); a.emit(ands_reg, 2, 0)   # r2 = bit 7
    a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25); a.emit(adds_reg, 0, 0, 7)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "glk_l", "ge"); a.emit(movs_imm, 0, 0)
    a.label("glk_l"); a.emit(cmp_imm, 0, 127); a.emit(b_cond, "glk_h", "le"); a.emit(movs_imm, 0, 127)
    a.label("glk_h"); a.emit(orrs_reg, 0, 2); a.emit(strb_w, 0, 5, KG)
    setbit(KG + 1, True)
    a.emit(pop_list, [5], pc=True)

    a.label("c_gltick")                                                        # from c_fxtick (the DSP service tick: DSP writes only)
    a.emit(push_list, [5, 6], lr=True)
    if MECH: a.emit(ldrb_w, 0, 4, KG + 3); a.emit(lsrs_imm, 0, 0, 7); bc("glt_x", "ne")           # a mechanical gesture has the engine
    a.emit(bl, "c_gact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "glt_v", "ne")                   # neither view showing: released
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40)
    a.emit(ldr_imm, 1, 0, CTRL_VIEW); a.emit(ldr_imm, 2, 0, 0x44); a.emit(cmp_reg, 1, 2); a.emit(b_cond, "glt_v", "eq")
    a.emit(ldrb_w, 0, 4, KG); a.emit(lsrs_imm, 0, 0, 7); a.emit(b_cond, "glt_v", "eq")
    setbit(KG, False); setbit(KG + 1, True)
    a.label("glt_v")                                                           # on = held | the sequencer's bit 6; a change of it (vs bit 7 of KG + 2 = sent on) = to send
    if MSWAP:                                                                  # the Glitch = effect 5 of the top row: held, latched, a slot, the sequencer
        a.emit(ldrb_imm, 5, 4, S_HELD); a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(orrs_reg, 5, 0)
        a.emit(bl, "c_slotbits"); a.emit(orrs_reg, 5, 0); a.emit(bl, "c_fsqfx"); a.emit(orrs_reg, 5, 0)
        a.emit(lsrs_imm, 5, 5, N_FX - 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 5, 1)
    else:
        a.emit(bl, "c_fsqfx" if GL2 else "c_fxsq"); a.emit(lsrs_imm, 5, 0, 6); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 5, 1)
        a.emit(ldrb_w, 0, 4, KG); a.emit(lsrs_imm, 0, 0, 7); a.emit(orrs_reg, 5, 0)                    # r5 = on
    a.emit(ldrb_w, 0, 4, KG + 2); a.emit(lsrs_imm, 0, 0, 7); a.emit(cmp_reg, 0, 5); a.emit(b_cond, "glt_s", "eq")
    setbit(KG + 1, True)
    a.label("glt_s")
    a.emit(ldrb_w, 0, 4, KG + 1); a.emit(lsrs_imm, 0, 0, 7); bc("glt_x", "eq")
    setbit(KG + 1, False)
    a.emit(ldrb_w, 0, 4, KG + 2); a.emit(movs_imm, 1, 0x80); a.emit(bics_reg, 0, 1); a.emit(lsls_imm, 1, 5, 7); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 4, KG + 2)
    a.emit(cmp_imm, 5, 0); bc("glt_off", "eq")
    for k in range(4):
        a.emit(ldrb_w, 0, 4, (S_KNOB + 16 if MSWAP else KG) + k); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25); a.emit(movw, 1, GD.GARM + 1 + k); a.emit(bl, "c_dw")
    a.emit(movw, 0, GD.GMAGIC & 0xFFFF); a.emit(movt, 0, GD.GMAGIC >> 16); a.emit(movw, 1, GD.GARM); a.emit(bl, "c_dw")
    a.emit(b, "glt_x")
    a.label("glt_off")
    a.emit(movs_imm, 0, 0); a.emit(movw, 1, GD.GARM); a.emit(bl, "c_dw")
    a.label("glt_x"); a.emit(pop_list, [5, 6], pc=True)

    a.label("c_gl31")                                                          # r0 = an LED buffer, r4 = the block: pad 31 = the Glitch (bright while held)
    a.emit(ldrb_w, 1, 4, KG + (3 if MSWAP else 2)); a.emit(movs_imm, 2, GL_DIM); a.emit(lsrs_imm, 1, 1, 7); a.emit(b_cond, "g31_s", "eq"); a.emit(movs_imm, 2, GL_ON)   # lit while it plays (MSWAP: while a gesture runs)
    a.label("g31_s"); a.emit(strh_imm, 2, 0, 2 * GL_PAD); a.emit(raw, h(0x4770))

    a.label("c_glleds")                                                        # r0 = the LED buffer of the Master FX view: pad 31, and the knobs while the Glitch is selected
    a.emit(push_list, [5], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(bl, "c_gl31")
    a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, GL_SEL); bc("gll_x", "ne")
    for k in range(8):
        if k == 1 and MSWAP and DIGI4:                                         # the kind of the gesture: the colour of its stretch, brighter along it
            a.emit(ldrb_w, 0, 4, KG + k); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 23)   # K2 x 4
            a.emit(lsrs_imm, 1, 0, 7)
            for q, col in enumerate(MECH_COL):
                a.emit(cmp_imm, 1, q); a.emit(b_cond, f"gll_m{q}", "ne"); a.emit(movs_imm, 1, col); a.emit(b, "gll_me"); a.label(f"gll_m{q}")
            a.emit(movs_imm, 1, MECH_COL[-1])
            a.label("gll_me")
            a.emit(movs_imm, 2, 127); a.emit(ands_reg, 0, 2); a.emit(movs_imm, 2, 127 - MECH_MINB); a.emit(muls, 0, 2); a.emit(lsrs_imm, 0, 0, 7)
            a.emit(adds_imm8, 0, MECH_MINB + 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 1)
        elif k < 4:
            a.emit(ldrb_w, 0, 4, KG + k); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25)
            a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(movs_imm, 1, GL_ON); a.emit(orrs_reg, 0, 1)
        else:
            a.emit(movs_imm, 0, 0)
        a.emit(raw, strh_w(0, 5, 2 * (34 + k)))
    a.label("gll_x"); a.emit(pop_list, [5], pc=True)


def sampler_code(a, L, tabaddr, bc, zjmp):
    """SC33 (use_sampler): r4 = the Master FX block in every routine.  Knob k of the sample: byte S_SLOT + 4 * SMP_SLOT + k (bits 0-6), real value =
    raw ^ 64 (K1), raw (K2, K3), 127 - raw (K4).  S_JF: SMB_* bits, the pending command in bits 4-5, the last state sent to the DSP in bits 6-7."""
    import sampler_dsp as SD
    c_shift = L["c_shift"]
    udiv = s14.udiv
    KB = S_SLOT + 4 * SMP_SLOT

    def real(rd, k):                                  # rd = the real value of knob k (clobbers r3)
        a.emit(ldrb_w, rd, 4, KB + k); a.emit(lsls_imm, rd, rd, 25); a.emit(lsrs_imm, rd, rd, 25)
        if k == 0: a.emit(movs_imm, 3, 64); a.emit(eors_reg, rd, 3)
        if k == 3: a.emit(movs_imm, 3, 127); a.emit(subs_reg, rd, 3, rd)

    # ---- c_smpress: pad 7 pressed (Shift: forced loop on / off; else start + gate)
    a.label("c_smpress")
    a.emit(push_list, [5], lr=True)
    a.emit(movs_imm, 0, SMP_SEL); a.emit(strb_imm, 0, 4, S_SEL)
    a.emit(bl, c_shift); a.emit(ldrb_w, 1, 4, S_JF); a.emit(movs_imm, 2, 0x30); a.emit(bics_reg, 1, 2)
    if LATCH7:                                                                                        # a latched loop: this press stops it
        a.emit(movs_imm, 2, SMB_LOOP); a.emit(tst_reg, 1, 2); a.emit(b_cond, "smp_nl", "eq")
        a.emit(movs_imm, 2, SMB_LOOP | SMB_GATE); a.emit(bics_reg, 1, 2); a.emit(movs_imm, 2, 0x30); a.emit(orrs_reg, 1, 2); a.emit(b, "smp_w")
        a.label("smp_nl")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smp_n", "eq")
    if SMP_HOLD:                                                                                      # start in loop, gate held
        a.emit(movs_imm, 2, 0x20 | SMB_LOOP | SMB_GATE); a.emit(orrs_reg, 1, 2); a.emit(b, "smp_w")
    else:
        a.emit(movs_imm, 2, SMB_LOOP); a.emit(tst_reg, 1, 2); a.emit(b_cond, "smp_lon", "eq")
        a.emit(bics_reg, 1, 2); a.emit(movs_imm, 2, 0x30); a.emit(orrs_reg, 1, 2); a.emit(b, "smp_w")      # looping: stop
        a.label("smp_lon")
        a.emit(orrs_reg, 1, 2); a.emit(movs_imm, 2, 0x20); a.emit(orrs_reg, 1, 2); a.emit(b, "smp_w")      # start in loop
    a.label("smp_n")
    a.emit(movs_imm, 2, SMB_LOOP); a.emit(bics_reg, 1, 2); a.emit(movs_imm, 2, 0x10 | SMB_GATE); a.emit(orrs_reg, 1, 2)   # start, gate held
    a.label("smp_w"); a.emit(strb_w, 1, 4, S_JF)
    a.emit(pop_list, [5], pc=True)

    def req(rd):                                      # rd |= the request bits 23-29 of S_SMT (r5 = S_SMT; clobbers r3)
        a.emit(movw, 3, 0); a.emit(movt, 3, 0x3F80); a.emit(ands_reg, 3, 5); a.emit(orrs_reg, rd, 3)

    def setrec(on):                                   # S_JF bit REC on / off (clobbers r0, r1)
        a.emit(ldrb_w, 0, 4, S_JF); a.emit(movs_imm, 1, SMB_REC); a.emit(orrs_reg if on else bics_reg, 0, 1); a.emit(strb_w, 0, 4, S_JF)

    # ---- c_smrec: pad 32 pressed.  Shift: arm / disarm (the next bar is recorded); recording latched or armed: stop; else start (time stamped)
    a.label("c_smrec")
    a.emit(push_list, [5, 6], lr=True)
    a.emit(ldr_imm, 5, 4, S_SMT)
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smr_ns", "eq")
    a.emit(movs_imm, 6, 0); a.emit(cmp_imm, 5, 0); a.emit(b_cond, "smr_set", "lt")             # armed: disarm (and stop)
    a.emit(movw, 6, 0); a.emit(movt, 6, SMT_ARM >> 16)                                        # arm
    a.label("smr_set")
    if SMP2: req(6)
    a.emit(str_imm, 6, 4, S_SMT); setrec(False); a.emit(pop_list, [5, 6], pc=True)
    a.label("smr_ns")
    a.emit(lsrs_imm, 0, 5, 30); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smr_go", "eq")          # latched or armed
    a.emit(movs_imm, 0, 0)
    if SMP2: req(0)
    a.emit(str_imm, 0, 4, S_SMT); setrec(False); a.emit(pop_list, [5, 6], pc=True)
    a.label("smr_go")
    if SMP2: a.emit(bl, L["c_now"]); a.emit(lsls_imm, 0, 0, 9); a.emit(lsrs_imm, 0, 0, 9); req(0)
    else: a.emit(bl, L["c_now"]); a.emit(lsls_imm, 0, 0, 2); a.emit(lsrs_imm, 0, 0, 2)
    a.emit(str_imm, 0, 4, S_SMT)
    setrec(True); a.emit(pop_list, [5, 6], pc=True)

    # ---- c_smrrel: pad 32 released: a short press latches the recording, a long one ends it (nothing while latched / armed / stopped)
    a.label("c_smrrel")
    a.emit(push_list, [5, 6], lr=True)
    a.emit(ldrb_w, 0, 4, S_JF); a.emit(movs_imm, 1, SMB_REC); a.emit(tst_reg, 0, 1); a.emit(b_cond, "smrr_x", "eq")
    a.emit(ldr_imm, 5, 4, S_SMT); a.emit(lsrs_imm, 0, 5, 30); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smrr_x", "ne")
    if SMP2:                                                                    # the time stamp: 23 bits (bits 23-29 are the request)
        a.emit(bl, L["c_now"]); a.emit(lsls_imm, 0, 0, 9); a.emit(lsrs_imm, 0, 0, 9); a.emit(lsls_imm, 1, 5, 9); a.emit(lsrs_imm, 1, 1, 9); a.emit(subs_reg, 0, 0, 1)
        a.emit(lsls_imm, 0, 0, 9); a.emit(lsrs_imm, 0, 0, 9)                                   # elapsed (23 bit)
    else:
        a.emit(bl, L["c_now"]); a.emit(lsls_imm, 0, 0, 2); a.emit(lsrs_imm, 0, 0, 2); a.emit(subs_reg, 0, 0, 5)
        a.emit(lsls_imm, 0, 0, 2); a.emit(lsrs_imm, 0, 0, 2)                                   # elapsed (30 bit)
    a.emit(movw, 1, SMP_TAP); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "smrr_end", "hs")
    a.emit(movw, 0, 0); a.emit(movt, 0, SMT_LATCH >> 16); a.emit(orrs_reg, 5, 0); a.emit(str_imm, 5, 4, S_SMT)   # short: latched
    a.emit(pop_list, [5, 6], pc=True)
    a.label("smrr_end")
    setrec(False)
    a.label("smrr_x"); a.emit(pop_list, [5, 6], pc=True)

    # ---- c_smknob (r6 = knob 0-3, r7 = delta): the sample's knob, clamped 0..127, stored raw (bit 7 of the 4 bytes cleared: never an assigned slot)
    a.label("c_smknob")
    a.emit(push_list, [5], lr=True)
    for k in range(4):
        a.emit(cmp_imm, 6, k); a.emit(b_cond, f"smk_{k}", "ne")
        real(0, k); a.emit(adds_reg, 0, 0, 7)
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"smk_l{k}", "ge"); a.emit(movs_imm, 0, 0)
        a.label(f"smk_l{k}"); a.emit(cmp_imm, 0, 127); a.emit(b_cond, f"smk_h{k}", "le"); a.emit(movs_imm, 0, 127)
        a.label(f"smk_h{k}")
        if k == 0: a.emit(movs_imm, 3, 64); a.emit(eors_reg, 0, 3)
        if k == 3: a.emit(movs_imm, 3, 127); a.emit(subs_reg, 0, 3, 0)
        a.emit(strb_w, 0, 4, KB + k); a.emit(b, "smk_x")
        a.label(f"smk_{k}")
    a.label("smk_x")
    for k in range(4):
        a.emit(ldrb_w, 0, 4, KB + k); a.emit(lsls_imm, 0, 0, 25); a.emit(lsrs_imm, 0, 0, 25); a.emit(strb_w, 0, 4, KB + k)
    a.emit(ldrb_w, 0, 4, S_JF); a.emit(movs_imm, 1, SMB_DIRTY); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 4, S_JF)
    a.emit(pop_list, [5], pc=True)

    # ---- c_smtick (from c_fxtick, the DSP service tick: DSP writes only, no semaphore): state, parameters, command to the DSP
    a.label("c_smtick")
    a.emit(push_list, [5, 6], lr=True)
    a.emit(ldrb_w, 5, 4, S_JF)
    if ARMPLAY:                                                                  # SC38.2: armed + a start (running, ticks 0): the bar starts now
        a.emit(ldr_imm, 0, 4, S_SMT); a.emit(cmp_imm, 0, 0); bc("sap_x", "ge")                       # not armed
        a.emit(lsls_imm, 0, 0, 1); bc("sap_x", "mi")                                                  # already running its bar
        a.emit(movw, 0, PLAY_STORE & 0xFFFF); a.emit(movt, 0, PLAY_STORE >> 16); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(cmp_imm, 0, 0); bc("sap_x", "eq")                                                       # stopped
        a.emit(movw, 0, SEQ_ENGINE & 0xFFFF); a.emit(movt, 0, SEQ_ENGINE >> 16); a.emit(raw, ldr_w(0, 0, 0x90))
        a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0); a.emit(cmp_imm, 0, 0); bc("sap_x", "ne")   # not the start
        a.emit(ldr_imm, 0, 4, S_SMT); a.emit(movw, 1, 0); a.emit(movt, 1, SMT_LATCH >> 16); a.emit(orrs_reg, 0, 1); a.emit(str_imm, 0, 4, S_SMT)
        a.emit(movs_imm, 0, SMB_REC); a.emit(orrs_reg, 5, 0)
        a.label("sap_x")
    a.emit(bl, "c_gact"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smt_v", "ne")
    if SMP2:                                                                     # the FX view (pad 32 records there too) counts as showing
        a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40)
        a.emit(ldr_imm, 1, 0, CTRL_VIEW); a.emit(ldr_imm, 2, 0, 0x44); a.emit(cmp_reg, 1, 2); a.emit(b_cond, "smt_v", "eq")
    if LATCH7:                                                                   # the view left: pad 7 no longer held (a latched loop goes on)
        a.emit(movs_imm, 0, SMB_LOOP); a.emit(tst_reg, 5, 0); a.emit(b_cond, "smt_lk", "ne"); a.emit(movs_imm, 0, SMB_GATE); a.emit(bics_reg, 5, 0)
        a.label("smt_lk")
    else:
        a.emit(movs_imm, 0, SMB_GATE | (SMB_LOOP if SMP_HOLD else 0)); a.emit(bics_reg, 5, 0)   # the view left: pad 7 no longer held
    a.emit(ldr_imm, 0, 4, S_SMT); a.emit(lsrs_imm, 0, 0, 30); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smt_v", "ne")   # latched / armed: goes on
    a.emit(movs_imm, 0, SMB_REC); a.emit(bics_reg, 5, 0)                         # a held recording ends
    a.label("smt_v")
    a.emit(movs_imm, 6, 3); a.emit(ands_reg, 6, 5); a.emit(lsrs_imm, 0, 5, 6); a.emit(cmp_reg, 0, 6); a.emit(b_cond, "smt_ps", "eq")
    a.emit(mov_reg, 0, 6); a.emit(movw, 1, SD.STATE); a.emit(bl, "c_dw")
    a.emit(lsls_imm, 5, 5, 26); a.emit(lsrs_imm, 5, 5, 26); a.emit(lsls_imm, 0, 6, 6); a.emit(orrs_reg, 5, 0)
    a.label("smt_ps")
    a.emit(movs_imm, 0, 0x30 | SMB_DIRTY); a.emit(tst_reg, 5, 0); bc("smt_out", "eq")
    real(6, 0)                                                                   # pitch -> INCI / INCF
    a.emit(movw, 0, tabaddr["SMPI"] & 0xFFFF); a.emit(movt, 0, tabaddr["SMPI"] >> 16); a.emit(raw, ldr_reg_lsl2(6, 0, 6))
    a.emit(lsrs_imm, 0, 6, 16); a.emit(movw, 1, SD.INCI); a.emit(bl, "c_dw")
    a.emit(lsls_imm, 0, 6, 16); a.emit(lsrs_imm, 0, 0, 8); a.emit(movw, 1, SD.INCF); a.emit(bl, "c_dw")
    for k, addr in ((2, SD.SF), (3, SD.EF)):                                    # start / end -> fractions 0..$7FFFFF
        real(0, k); a.emit(movw, 1, 0xFFFF); a.emit(movt, 1, 0x7F); a.emit(muls, 0, 1); a.emit(movs_imm, 1, 127); a.emit(raw, udiv(0, 0, 1))
        a.emit(movw, 1, addr); a.emit(bl, "c_dw")
    real(0, 1); a.emit(movs_imm, 1, 3); a.emit(muls, 0, 1); a.emit(lsrs_imm, 0, 0, 7)   # mode 0 / 1 / 2
    a.emit(movw, 1, SD.MODE); a.emit(bl, "c_dw")
    a.emit(movs_imm, 0, SMB_DIRTY); a.emit(bics_reg, 5, 0)
    a.emit(lsrs_imm, 0, 5, 4); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smt_out", "eq")
    a.emit(movw, 1, SD.CMD); a.emit(bl, "c_dw")
    a.emit(movs_imm, 0, 0x30); a.emit(bics_reg, 5, 0)
    a.label("smt_out")
    a.emit(strb_w, 5, 4, S_JF)
    if SMP2:                                                                     # a drum replacement (no other command pending): REPN, then CMD 4
        a.emit(lsrs_imm, 0, 5, 4); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smt_x", "ne")
        a.emit(ldr_imm, 6, 4, S_SMT); a.emit(lsls_imm, 0, 6, 2); a.emit(lsrs_imm, 0, 0, 25); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "smt_x", "eq")
        a.emit(subs_imm8, 0, 1); a.emit(movw, 1, SD.REPN); a.emit(bl, "c_dw")
        a.emit(movs_imm, 0, 4); a.emit(movw, 1, SD.CMD); a.emit(bl, "c_dw")
        if SMP_SAVEBIT:                                                          # the slot REPK gets a new capture: not saved any more (the tick may read the DSP)
            a.emit(movs_imm, 0, 0); a.emit(movw, 1, SD.REPK); a.emit(bl, 0x08029344); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 0, 1)
            a.emit(movs_imm, 5, 1); a.emit(raw, h(0x4085))                       # lsls r5, r0 -> r5 = bit of the slot
            a.emit(movs_imm, 0, 0); a.emit(movw, 1, SD.SMB + 0x1E); a.emit(bl, 0x08029344); a.emit(lsrs_imm, 0, 0, 8)
            a.emit(bics_reg, 0, 5); a.emit(movw, 1, SD.SMB + 0x1E); a.emit(bl, "c_dw")
            a.emit(ldrb_w, 5, 4, S_JF)                                           # r5 back (S_JF)
        a.emit(movw, 0, 0); a.emit(movt, 0, 0x3F80); a.emit(bics_reg, 6, 0); a.emit(str_imm, 6, 4, S_SMT)
        a.label("smt_x")
    a.emit(pop_list, [5, 6], pc=True)

    # ---- c_smleds (r0 = LED buffer of the Master FX view): pad 7, pad 32, and the knobs while the sample is selected
    a.label("c_smleds")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 0)
    a.emit(bl, "c_gfst"); zjmp(0, "sml_out"); a.emit(mov_reg, 4, 0)
    a.emit(ldrb_w, 1, 4, S_JF)
    a.emit(movw, 0, SMP_DIM); a.emit(movs_imm, 2, SMB_GATE | SMB_LOOP); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sml_7", "eq"); a.emit(movw, 0, SMP_ON)
    a.label("sml_7"); a.emit(strh_imm, 0, 5, 2 * SMP_PAD)
    a.emit(movw, 0, REC_ON); a.emit(movs_imm, 2, SMB_REC); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sml_r", "ne")
    a.emit(movw, 0, REC_DIM); a.emit(ldr_imm, 1, 4, S_SMT); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "sml_r", "ge")   # armed (bit 31), not yet recording: blink
    a.emit(bl, L["c_now"]); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(movw, 1, REC_DIM); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sml_b", "eq"); a.emit(movw, 1, REC_ON)
    a.label("sml_b"); a.emit(mov_reg, 0, 1)
    a.label("sml_r"); a.emit(strh_imm, 0, 5, 2 * SMP_REC)
    a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, SMP_SEL); bc("sml_out", "ne")
    for k in range(8):
        if k == 1 and SMP2:                                                        # K2: the mode's colour, full brightness
            real(0, 1); a.emit(movs_imm, 1, 3); a.emit(muls, 0, 1); a.emit(lsrs_imm, 0, 0, 7)
            a.emit(movw, 1, (129 << 8) | MODE_COL[0]); a.emit(cmp_imm, 0, 1); a.emit(b_cond, "sml_m", "lo")
            a.emit(movw, 1, (129 << 8) | MODE_COL[1]); a.emit(b_cond, "sml_m", "eq"); a.emit(movw, 1, (129 << 8) | MODE_COL[2])
            a.label("sml_m"); a.emit(mov_reg, 0, 1)
        elif k < 4:
            real(0, k); a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(movs_imm, 1, SMP_ON); a.emit(orrs_reg, 0, 1)   # colour | (value + 2) << 8
        else:
            a.emit(movs_imm, 0, 0)
        a.emit(raw, strh_w(0, 5, 2 * (34 + k)))
    a.label("sml_out"); a.emit(pop_list, [4, 5], pc=True)
    if SMP2:
        # ---- c_smled32 (r0 = an LED buffer, r4 = the block): pad 32 = the record pad (red; bright recording, blinking armed)
        a.label("c_smled32")
        a.emit(push_list, [5], lr=True)
        a.emit(mov_reg, 5, 0); a.emit(ldrb_w, 1, 4, S_JF)
        a.emit(movw, 0, REC_ON); a.emit(movs_imm, 2, SMB_REC); a.emit(tst_reg, 1, 2); a.emit(b_cond, "s32_r", "ne")
        a.emit(movw, 0, REC_DIM); a.emit(ldr_imm, 1, 4, S_SMT); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "s32_r", "ge")
        a.emit(bl, L["c_now"]); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
        a.emit(movw, 1, REC_DIM); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "s32_b", "eq"); a.emit(movw, 1, REC_ON)
        a.label("s32_b"); a.emit(mov_reg, 0, 1)
        a.label("s32_r"); a.emit(strh_imm, 0, 5, 2 * SMP_REC)
        a.emit(pop_list, [5], pc=True)


def slots_code(a, L, setmap_addr, pal_codes, bc, zjmp):
    """SC17.6: bottom FX row in the Master FX view and FX slots.  Block fields (r4 = Master FX block everywhere):
      S_SLOT + 4 j + i : slot j (bottom pad 25 + j), byte i = parameter i (bits 0-6) | effect bit i (bit 7);
                         effect = top pad 0-5 (bits 0-2 of the effect number in bit 7 of bytes 0-2), bit 7 of byte 3 = assigned
      S_SLOTH          : bit j = slot j held (activates its effect through c_slotbits)
    Unassigned slots are the SC14 effects (c_fxpress / c_fxrel / c_fxleds)."""
    c_gst, c_shift = L["c_gst"], L["c_shift"]
    c_fxpress, c_fxrel, c_fxleds = L["c_fxpress"], L["c_fxrel"], L["c_fxleds"]
    def ctrl(rd):                                     # rd = controller
        a.emit(movw, rd, CTX & 0xFFFF); a.emit(movt, rd, CTX >> 16)
        a.emit(ldr_imm, rd, rd, 0); a.emit(ldr_imm, rd, rd, 0x40)
    def fxview(rd):                                   # rd = FX view object
        ctrl(rd); a.emit(ldr_imm, rd, rd, 0x44)
    def knobset(rk, rs):                              # rs = block + 4 * set of effect rk
        a.emit(movw, rs, setmap_addr & 0xFFFF); a.emit(movt, rs, setmap_addr >> 16)
        a.emit(ldrb_reg, rs, rs, rk); a.emit(lsls_imm, rs, rs, 2); a.emit(adds_reg, rs, rs, 4)

    # ---- c_stype: r0 = slot j -> r0 = effect pad 0-5, or 0xFF if unassigned; clobbers r1, r2
    a.label("c_stype")
    a.emit(lsls_imm, 1, 0, 2); a.emit(adds_reg, 1, 1, 4)
    a.emit(ldrb_w, 2, 1, S_SLOT + 3); a.emit(lsrs_imm, 2, 2, 7)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "st_has", "ne")
    a.emit(movs_imm, 0, 0xFF); a.emit(raw, h(0x4770))
    a.label("st_has")
    a.emit(ldrb_w, 0, 1, S_SLOT); a.emit(lsrs_imm, 0, 0, 7)
    a.emit(ldrb_w, 2, 1, S_SLOT + 1); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 1); a.emit(orrs_reg, 0, 2)
    a.emit(ldrb_w, 2, 1, S_SLOT + 2); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 2); a.emit(orrs_reg, 0, 2)
    a.emit(raw, h(0x4770))

    # ---- c_sassign: r0 = slot j, r1 = effect k -> slot := effect k + a copy of its 4 live parameters; clobbers r0-r3
    a.label("c_sassign")
    a.emit(push_list, [5, 6], lr=True)
    knobset(1, 2)
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 0, 0, 4)                       # r0 = block + 4 j
    a.emit(movs_imm, 3, 0)
    a.label("sa_l")
    a.emit(adds_reg, 5, 2, 3); a.emit(ldrb_w, 5, 5, S_KNOB)                    # live parameter i
    a.emit(lsls_imm, 5, 5, 25); a.emit(lsrs_imm, 5, 5, 25)                     # & 0x7F
    a.emit(movs_imm, 6, 1)
    a.emit(cmp_imm, 3, 3); a.emit(b_cond, "sa_b", "hs")
    a.emit(mov_reg, 6, 1); a.emit(lsrs_reg, 6, 3)                              # effect bit i
    a.emit(lsls_imm, 6, 6, 31); a.emit(lsrs_imm, 6, 6, 31)
    a.label("sa_b")
    a.emit(lsls_imm, 6, 6, 7); a.emit(orrs_reg, 5, 6)
    a.emit(adds_reg, 6, 0, 3); a.emit(strb_w, 5, 6, S_SLOT)
    a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 4); a.emit(b_cond, "sa_l", "lo")
    a.emit(pop_list, [5, 6], pc=True)

    # ---- c_sload: r0 = slot j, r1 = effect k -> live parameters of effect k := the slot's copy; clobbers r0-r3
    a.label("c_sload")
    a.emit(push_list, [5], lr=True)
    knobset(1, 2)
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 0, 0, 4)
    a.emit(movs_imm, 3, 0)
    a.label("sd_l")
    a.emit(adds_reg, 5, 0, 3); a.emit(ldrb_w, 5, 5, S_SLOT)
    a.emit(lsls_imm, 5, 5, 25); a.emit(lsrs_imm, 5, 5, 25)
    a.emit(adds_reg, 1, 2, 3); a.emit(strb_w, 5, 1, S_KNOB)
    a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 4); a.emit(b_cond, "sd_l", "lo")
    a.emit(movs_imm, 1, 1); a.emit(strb_imm, 1, 4, S_DIRTY)                    # parameters changed: resend
    a.emit(pop_list, [5], pc=True)

    # ---- c_slotbits: effect bits driven by the held slots (the tick ORs them with held | latched); drops them when
    #      neither the FX view nor the Master FX view is showing
    a.label("c_slotbits")
    a.emit(push_list, [5, 6], lr=True)
    ctrl(0)
    a.emit(ldr_imm, 1, 0, CTRL_VIEW); a.emit(ldr_imm, 2, 0, 0x44); a.emit(cmp_reg, 1, 2); bc("sb_keep", "eq")
    a.emit(bl, "c_gact"); a.emit(cmp_imm, 0, 0); bc("sb_drop", "eq")
    a.label("sb_keep")
    a.emit(ldrb_w, 5, 4, S_SLOTH); a.emit(movs_imm, 6, 0)
    for j in range(7):
        a.emit(lsrs_imm, 0, 5, j + 1); a.emit(b_cond, f"sb_n{j}", "cc")
        a.emit(movs_imm, 0, j); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, f"sb_n{j}", "eq")
        a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(orrs_reg, 6, 1)
        a.label(f"sb_n{j}")
    a.emit(mov_reg, 0, 6); a.emit(pop_list, [5, 6], pc=True)
    a.label("sb_drop")
    a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 4, S_SLOTH); a.emit(pop_list, [5, 6], pc=True)

    # ---- c_f_press (FX view slot 0: view, pad, vel): assigned slots run their effect, the rest is SC14's
    a.label("c_f_press")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 7, 2)
    a.emit(cmp_imm, 6, 25); bc("fp2_orig", "lo"); a.emit(cmp_imm, 6, 32); bc("fp2_orig", "hs")
    a.emit(bl, "c_gfst"); zjmp(0, "fp2_orig"); a.emit(mov_reg, 4, 0)
    if SMP2:
        a.emit(cmp_imm, 6, SMP_REC); a.emit(b_cond, "fp2_nr", "ne"); a.emit(bl, "c_smrec"); a.emit(b, "fp2_out")
        a.label("fp2_nr")
    if GLITCH:
        a.emit(cmp_imm, 6, GL_PAD); a.emit(b_cond, "fp2_ngl", "ne"); a.emit(bl, "c_gl31p" if GL3 else "c_glpress"); a.emit(b, "fp2_out")
        a.label("fp2_ngl")
    a.emit(mov_reg, 0, 6); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_stype")
    a.emit(cmp_imm, 0, 0xFF); bc("fp2_u" if CLEARPAD else "fp2_orig", "eq")
    a.emit(strb_imm, 0, 4, S_SEL)                                              # the effect becomes the selected one
    a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 6); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_sload")
    if SMP2:                                                                   # a slot of the sample: its knobs are loaded; play it (Shift = loop), lit while held
        a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, SMP_SEL); a.emit(b_cond, "fp2_nsm", "ne")
        a.emit(bl, "c_smpress")
        if not SMP_HOLD: a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("fp2_out", "ne")
        a.emit(b, "fp2_sh")
        a.label("fp2_nsm")
    if GL2:                                                                    # a slot of the Glitch: its knobs are loaded (c_sload), it plays while held (no latch)
        a.emit(ldrb_imm, 0, 4, S_SEL); a.emit(cmp_imm, 0, GL_SEL); bc("fp2_ngs", "ne")
        a.emit(bl, "c_glpress"); a.emit(b, "fp2_sh")
        a.label("fp2_ngs")
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("fp2_hold", "eq")
    a.emit(ldrb_imm, 1, 4, S_SEL); a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 1)                  # Shift: latch the effect
    a.emit(ldrb_imm, 3, 4, S_LATCH); a.emit(eors_reg, 3, 2); a.emit(strb_imm, 3, 4, S_LATCH); a.emit(b, "fp2_out")
    a.label("fp2_hold")
    if CLEARPAD:                                                               # latched effect: the tap switches it off
        a.emit(ldrb_imm, 1, 4, S_SEL); a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 1)
        a.emit(ldrb_imm, 3, 4, S_LATCH); a.emit(tst_reg, 3, 2); a.emit(b_cond, "fp2_h2", "eq")
        a.emit(bics_reg, 3, 2); a.emit(strb_imm, 3, 4, S_LATCH); a.emit(b, "fp2_out")
        a.label("fp2_h2")
    a.label("fp2_sh")
    a.emit(mov_reg, 1, 6); a.emit(subs_imm8, 1, 25); a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 1)
    a.emit(ldrb_w, 3, 4, S_SLOTH); a.emit(orrs_reg, 3, 2); a.emit(strb_w, 3, 4, S_SLOTH)
    a.label("fp2_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    if CLEARPAD:
        # unassigned bottom pad = an SC14 effect: without Shift, a tap on a latched one switches it off (and re-picks the active
        # Gater / Auto-Filter); everything else is SC14's handler (r4 = Master FX block = SC14 state + GFX_OFF)
        a.label("fp2_u")
        a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("fp2_orig", "ne")
        a.emit(mov_reg, 0, 4); a.emit(subs_imm8, 0, GFX_OFF)                    # r0 = SC14 state
        a.emit(ldrb_imm, 1, 0, s14.S_LATCH)
        a.emit(mov_reg, 2, 6); a.emit(subs_imm8, 2, 25); a.emit(movs_imm, 3, 1); a.emit(lsls_reg, 3, 2)   # r3 = bit of the pad
        a.emit(tst_reg, 1, 3); bc("fp2_orig", "eq")
        a.emit(bics_reg, 1, 3); a.emit(strb_imm, 1, 0, s14.S_LATCH)
        a.emit(mov_reg, 4, 0)                                                   # r4 = SC14 state (c_gpick_t)
        a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 2, 4); a.emit(b_cond, "fp2_ut", "lo"); a.emit(movs_imm, 1, 1)
        a.label("fp2_ut"); a.emit(bl, L["c_gpick_t"]); a.emit(b, "fp2_out")
    a.label("fp2_orig")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, c_fxpress)

    # ---- c_f_rel (FX view slot 1: view, pad, x): release the slot, then SC14's release
    a.label("c_f_rel")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(cmp_imm, 5, 25); bc("fr2_t", "lo"); a.emit(cmp_imm, 5, 32); bc("fr2_t", "hs")
    a.emit(bl, "c_gfst"); zjmp(0, "fr2_t")
    if SMP2:
        a.emit(push_list, [4]); a.emit(mov_reg, 4, 0)                          # r4 = the block for the sampler routines (the view is r4 again below)
        a.emit(cmp_imm, 5, SMP_REC); a.emit(b_cond, "fr2_ns", "ne")
        a.emit(bl, "c_smrrel"); a.emit(pop_list, [4]); a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("fr2_ns")
        if GLITCH:
            a.emit(cmp_imm, 5, GL_PAD); a.emit(b_cond, "fr2_ngl", "ne")
            if GL3: a.emit(movs_imm, 0, GL_SLOT); a.emit(bl, "c_glrel3")
            else: a.emit(bl, "c_glrel")
            a.emit(pop_list, [4]); a.emit(pop_list, [4, 5, 6], pc=True)
            a.label("fr2_ngl")
        a.emit(mov_reg, 0, 5); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, SMP_SEL); a.emit(b_cond, "fr2_ng", "ne")
        if LATCH7:                                                             # a latched loop keeps its gate
            a.emit(ldrb_w, 1, 4, S_JF); a.emit(movs_imm, 2, SMB_LOOP); a.emit(tst_reg, 1, 2); a.emit(b_cond, "fr2_ng", "ne")
            a.emit(movs_imm, 2, SMB_GATE); a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 4, S_JF)
        else:
            a.emit(ldrb_w, 1, 4, S_JF); a.emit(movs_imm, 2, SMB_GATE | (SMB_LOOP if SMP_HOLD else 0)); a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 4, S_JF)
        a.label("fr2_ng")
        if GL2:
            a.emit(mov_reg, 0, 5); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, GL_SEL); a.emit(b_cond, "fr2_ngg", "ne")
            if GL3: a.emit(mov_reg, 0, 5); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_glrel3")
            else: a.emit(bl, "c_glrel")
            a.label("fr2_ngg")
        a.emit(mov_reg, 0, 4); a.emit(pop_list, [4])
    a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 1, 25); a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 1)
    a.emit(ldrb_w, 3, 0, S_SLOTH); a.emit(bics_reg, 3, 2); a.emit(strb_w, 3, 0, S_SLOTH)
    a.label("fr2_t")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, c_fxrel)

    # ---- c_f_leds (FX view slot 7: view): SC14's LEDs, assigned slots in their effect's colour
    a.label("c_f_leds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, c_fxleds); a.emit(mov_reg, 6, 0)                                 # r6 = LED buffer
    a.emit(bl, "c_gfst"); zjmp(0, "fl2_out"); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 5, 0)
    a.label("fl2_l")
    a.emit(mov_reg, 0, 5); a.emit(bl, "c_stype"); a.emit(cmp_imm, 0, 0xFF); bc("fl2_n", "eq")
    a.emit(mov_reg, 7, 0)                                                      # r7 = effect
    a.emit(movs_imm, 3, 0)                                                     # r3 = lit?
    a.emit(ldrb_imm, 1, 4, S_HELD); a.emit(ldrb_imm, 2, 4, S_LATCH); a.emit(orrs_reg, 1, 2)
    a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 7); a.emit(tst_reg, 1, 2); a.emit(b_cond, "fl2_on", "ne")
    a.emit(ldrb_w, 1, 4, S_SLOTH); a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 5); a.emit(tst_reg, 1, 2); a.emit(b_cond, "fl2_pick", "eq")
    a.label("fl2_on"); a.emit(movs_imm, 3, 1)
    a.label("fl2_pick")
    for kk, (on, dim) in enumerate(pal_codes):
        a.emit(cmp_imm, 7, kk); a.emit(b_cond, f"fl2_c{kk}", "ne")
        a.emit(movw, 0, dim); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "fl2_s", "eq"); a.emit(movw, 0, on); a.emit(b, "fl2_s")
        a.label(f"fl2_c{kk}")
    if GL2:
        a.emit(cmp_imm, 7, GL_SEL); a.emit(b_cond, "fl2_ngl", "ne")
        a.emit(movw, 0, GL_DIM); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "fl2_s", "eq"); a.emit(movw, 0, GL_ON); a.emit(b, "fl2_s")
        a.label("fl2_ngl")
    if SMP2:
        a.emit(movw, 0, SMP_DIM); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "fl2_s", "eq"); a.emit(movw, 0, SMP_ON)
    a.label("fl2_s")
    a.emit(mov_reg, 1, 5); a.emit(adds_imm8, 1, 25); a.emit(lsls_imm, 1, 1, 1); a.emit(raw, h(0x5200 | 1 << 6 | 6 << 3 | 0))   # strh r0,[r6,r1]
    a.label("fl2_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 7); bc("fl2_l", "lo")
    if SMP2: a.emit(mov_reg, 0, 6); a.emit(bl, "c_smled32")                    # pad 32: record
    if GLITCH: a.emit(mov_reg, 0, 6); a.emit(bl, "c_gl31")                       # pad 31: the Glitch
    a.label("fl2_out"); a.emit(mov_reg, 0, 6); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- Mixer view slots 0 / 1 / 7 in Master FX mode
    a.label("c_s_press")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1); a.emit(mov_reg, 7, 2)
    a.emit(bl, "c_gact"); zjmp(0, "sp2_fwd"); a.emit(mov_reg, 4, 0)
    if SMP:                                                                    # pad 7 = play the sample, pad 32 = record
        a.emit(cmp_imm, 6, SMP_PAD); a.emit(b_cond, "sp2_ns", "ne"); a.emit(bl, "c_smpress"); a.emit(b, "sp2_out")
        a.label("sp2_ns")
        a.emit(cmp_imm, 6, SMP_REC); a.emit(b_cond, "sp2_nr", "ne"); a.emit(bl, "c_smrec"); a.emit(b, "sp2_out")
        a.label("sp2_nr")
    if GLITCH:
        a.emit(cmp_imm, 6, GL_PAD); a.emit(b_cond, "sp2_ngl", "ne"); a.emit(bl, "c_gl31p" if GL3 else "c_glpress"); a.emit(b, "sp2_out")
        a.label("sp2_ngl")
    a.emit(cmp_imm, 6, 24); bc("sp2_top", "lo")
    a.emit(cmp_imm, 6, 32); bc("sp2_fwd", "hs")
    a.emit(cmp_imm, 6, 25); bc("sp2_del", "lo")                                # bottom row: pad 25 = stock "FX off"
    if GL2:                                                                    # the Glitch held (pad 31) + another bottom pad, no Shift: assign the Glitch to it
        if GL3: a.emit(ldrb_w, 1, 4, S_SLOTH); a.emit(movs_imm, 2, 1 << GL_SLOT); a.emit(tst_reg, 1, 2); bc("sp2_nga", "eq")    # pad 31 itself held
        else: a.emit(ldrb_w, 1, 4, S_SLOT + 4 * GL_SLOT); a.emit(lsrs_imm, 1, 1, 7); bc("sp2_nga", "eq")
        a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("sp2_nga", "ne")
        a.emit(mov_reg, 0, 6); a.emit(subs_imm8, 0, 25); a.emit(movs_imm, 1, GL_SEL); a.emit(bl, "c_sassign"); a.emit(b, "sp2_out")
        a.label("sp2_nga")
    if SMP2:                                                                   # no top effect held but pad 7 (the sample): assign the sample
        a.emit(ldrb_imm, 1, 4, S_HELD); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "sp2_hh", "ne")
        if LATCH7:                                                             # pad 7 held = the gate without a latched loop
            a.emit(ldrb_w, 1, 4, S_JF); a.emit(movs_imm, 2, SMB_GATE | SMB_LOOP); a.emit(ands_reg, 1, 2); a.emit(cmp_imm, 1, SMB_GATE); bc("sp2_del", "ne")
        else:
            a.emit(ldrb_w, 1, 4, S_JF); a.emit(movs_imm, 2, SMB_GATE); a.emit(tst_reg, 1, 2); bc("sp2_del", "eq")
        a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("sp2_del", "ne")
        a.emit(mov_reg, 0, 6); a.emit(subs_imm8, 0, 25); a.emit(movs_imm, 1, SMP_SEL); a.emit(bl, "c_sassign"); a.emit(b, "sp2_out")
        a.label("sp2_hh")
    a.emit(ldrb_imm, 1, 4, S_HELD); zjmp(1, "sp2_del")                         # a top effect is held?
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("sp2_del", "ne")
    a.emit(ldrb_imm, 1, 4, S_HELD); a.emit(movs_imm, 2, 0)                      # -> assign it (lowest held) to this pad
    a.label("sp2_lb")
    a.emit(movs_imm, 3, 1); a.emit(lsls_reg, 3, 2); a.emit(tst_reg, 1, 3); bc("sp2_ab", "ne")
    a.emit(adds_imm8, 2, 1); a.emit(cmp_imm, 2, 6); bc("sp2_lb", "lo"); a.emit(b, "sp2_del")
    a.label("sp2_ab")
    a.emit(mov_reg, 1, 2); a.emit(mov_reg, 0, 6); a.emit(subs_imm8, 0, 25); a.emit(bl, "c_sassign"); a.emit(b, "sp2_out")
    a.label("sp2_del")                                                         # FX view's handler: (FX view, pad, vel)
    fxview(0); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7); a.emit(bl, "c_f_press"); a.emit(b, "sp2_out")
    a.label("sp2_top")
    if SONGPTR:                                                                # pads 9-24: the song pointer
        a.emit(cmp_imm, 6, 8); bc("sp2_nsp", "lo")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_sp_press"); a.emit(b, "sp2_out")
        a.label("sp2_nsp")
    if SP2:                                                                    # SC32: pad 7 does nothing
        a.emit(cmp_imm, 6, 6); bc("sp2_njp", "ne"); a.emit(b, "sp2_out")
        a.label("sp2_njp")
    elif JUMP:                                                                 # pad 7: jump mode (hold; Shift = sticky toggle)
        a.emit(cmp_imm, 6, 6); bc("sp2_njp", "ne")
        a.emit(bl, c_shift); a.emit(ldrb_w, 1, 4, S_JF)
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sp2_jh", "eq")
        a.emit(movs_imm, 2, 2); a.emit(eors_reg, 1, 2); a.emit(b, "sp2_js")
        a.label("sp2_jh")
        if JUMP_UNSTICK:                                                       # latched and touched again (no Shift): unlatch (the touch itself does not start a momentary jump mode)
            a.emit(movs_imm, 2, 2); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sp2_jn", "eq"); a.emit(movs_imm, 1, 0); a.emit(b, "sp2_js")
            a.label("sp2_jn")
        a.emit(movs_imm, 2, 1); a.emit(orrs_reg, 1, 2)
        a.label("sp2_js"); a.emit(strb_w, 1, 4, S_JF); a.emit(b, "sp2_out")
        a.label("sp2_njp")
    if CLEARPAD:                                                               # pad 8: switch off every latched effect
        a.emit(cmp_imm, 6, 7); bc("sp2_ncl", "ne")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_clrall"); a.emit(b, "sp2_out")
        a.label("sp2_ncl")
    a.emit(cmp_imm, 6, N_FX); bc("sp2_fwd", "hs")
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); bc("sp2_fwd", "ne")
    a.emit(bl, c_gst); zjmp(0, "sp2_fwd")
    a.emit(ldrb_imm, 1, 0, 4); a.emit(ldrb_w, 2, 4, S_SLOTH); a.emit(orrs_reg, 1, 2)   # a bottom pad is held (SC14 | slots)?
    if GL3: a.emit(movs_imm, 2, 1 << GL_SLOT); a.emit(bics_reg, 1, 2)          # (pad 31 held is not a slot)
    bc("sp2_fwd", "eq")
    a.emit(movs_imm, 2, 0)
    a.label("sp2_lt")
    a.emit(movs_imm, 3, 1); a.emit(lsls_reg, 3, 2); a.emit(tst_reg, 1, 3); bc("sp2_at", "ne")
    a.emit(adds_imm8, 2, 1); a.emit(cmp_imm, 2, 7); bc("sp2_lt", "lo"); a.emit(b, "sp2_fwd")
    a.label("sp2_at")                                                          # assign this top effect to that bottom pad
    a.emit(mov_reg, 0, 2); a.emit(mov_reg, 1, 6); a.emit(bl, "c_sassign"); a.emit(b, "sp2_out")
    a.label("sp2_fwd")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, "c_gpress")
    a.label("sp2_out"); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    a.label("c_s_rel")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1)
    a.emit(bl, "c_gact"); zjmp(0, "sr2_fwd")
    if SMP:                                                                    # pad 7 released: the gate drops; pad 32 released: hold or latch
        a.emit(cmp_imm, 6, SMP_REC); a.emit(b_cond, "sr2_nrr", "ne")
        a.emit(mov_reg, 4, 0); a.emit(bl, "c_smrrel"); a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_nrr")
        a.emit(cmp_imm, 6, SMP_PAD); a.emit(b_cond, "sr2_ns", "ne")
        if LATCH7:                                                             # a latched loop keeps its gate
            a.emit(ldrb_w, 1, 0, S_JF); a.emit(movs_imm, 2, SMB_LOOP); a.emit(tst_reg, 1, 2); a.emit(b_cond, "sr2_lk", "ne")
            a.emit(movs_imm, 2, SMB_GATE); a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 0, S_JF)
            a.label("sr2_lk"); a.emit(pop_list, [4, 5, 6], pc=True)
        else:
            a.emit(ldrb_w, 1, 0, S_JF); a.emit(movs_imm, 2, SMB_GATE | (SMB_LOOP if SMP_HOLD else 0)); a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 0, S_JF); a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_ns")
    if GLITCH:
        a.emit(cmp_imm, 6, GL_PAD); a.emit(b_cond, "sr2_ngl", "ne")
        a.emit(mov_reg, 4, 0)
        if GL3: a.emit(movs_imm, 0, GL_SLOT); a.emit(bl, "c_glrel3")
        else: a.emit(bl, "c_glrel")
        a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_ngl")
    if SP2:
        a.emit(cmp_imm, 6, 6); bc("sr2_nj", "ne"); a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_nj")
    elif JUMP:                                                                 # pad 7 released: end of the momentary jump mode
        a.emit(cmp_imm, 6, 6); bc("sr2_nj", "ne")
        a.emit(ldrb_w, 1, 0, S_JF); a.emit(movs_imm, 2, 1); a.emit(bics_reg, 1, 2); a.emit(strb_w, 1, 0, S_JF)
        a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_nj")
    if SONGPTR:
        a.emit(cmp_imm, 6, 24); bc("sr2_b", "hs")
        a.emit(cmp_imm, 6, 8); bc("sr2_fwd", "lo")
        a.emit(mov_reg, 0, 6); a.emit(bl, "c_sp_rel"); a.emit(pop_list, [4, 5, 6], pc=True)
        a.label("sr2_b")
        a.emit(cmp_imm, 6, 32); bc("sr2_fwd", "hs")
    else:
        a.emit(cmp_imm, 6, 24); bc("sr2_fwd", "lo"); a.emit(cmp_imm, 6, 32); bc("sr2_fwd", "hs")
    fxview(0); a.emit(mov_reg, 1, 6); a.emit(movs_imm, 2, 0); a.emit(bl, "c_f_rel"); a.emit(pop_list, [4, 5, 6], pc=True)
    a.label("sr2_fwd")
    a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6)
    a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, "c_grel")

    a.label("c_s_leds")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 5, 0)
    a.emit(bl, "c_gleds"); a.emit(mov_reg, 4, 0)                               # r4 = buffer (Master FX's or stock's)
    a.emit(bl, "c_gact"); zjmp(0, "sl2_out")
    fxview(0); a.emit(bl, "c_f_leds")                                          # r0 = FX view's LED buffer
    for i in range(24, 32):                                                    # bottom row from the FX view
        a.emit(raw, ldrh_w(1, 0, 2 * i)); a.emit(raw, strh_w(1, 4, 2 * i))
    if SONGPTR: a.emit(mov_reg, 0, 4); a.emit(bl, "c_sp_leds")                  # rows 2 and 3: the song pointer
    if CLEARPAD: a.emit(mov_reg, 0, 4); a.emit(bl, "c_clrled")                  # pad 8
    if SP2: a.emit(movs_imm, 1, 0); a.emit(strh_imm, 1, 4, 12)                 # pad 7: dark
    elif JUMP: a.emit(mov_reg, 0, 4); a.emit(bl, "c_jmpled")                    # pad 7
    if SMP: a.emit(mov_reg, 0, 4); a.emit(bl, "c_smleds")                       # pad 7, pad 32, the sample's knobs
    if GLITCH:                                                                 # pad 31 and the Glitch's knobs (r4 is the buffer here: the block for the routine)
        a.emit(push_list, [4]); a.emit(bl, "c_gfst"); a.emit(mov_reg, 1, 4); a.emit(mov_reg, 4, 0); a.emit(mov_reg, 0, 1)
        a.emit(cmp_imm, 4, 0); a.emit(b_cond, "sl2_ng", "eq"); a.emit(bl, "c_glleds")
        a.label("sl2_ng"); a.emit(pop_list, [4])
    if GCLEAR: a.emit(mov_reg, 0, 4); a.emit(bl, "c_gclrled")                   # Clear held: the knobs' default state
    a.label("sl2_out"); a.emit(mov_reg, 0, 4); a.emit(pop_list, [4, 5, 6], pc=True)
    if SONGPTR:
        songptr_code(a, L, pal_codes, bc, zjmp)
    if CLEARPAD:
        # ---- c_clrall (r0 = Master FX block): every latched effect off.  The Master FX latch bits cover the top row and the
        #      assigned slots; the SC14 latch bits (state + 5) the unassigned bottom pads, whose active Gater / Auto-Filter is re-picked.
        a.label("c_clrall")
        a.emit(push_list, [4], lr=True)
        a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, S_LATCH)
        a.emit(subs_imm8, 0, GFX_OFF); a.emit(strb_imm, 1, 0, s14.S_LATCH)       # r0 = SC14 state
        a.emit(mov_reg, 4, 0)
        if CLEAR_SP:                                                            # song pointer: LS, LE, H1 (SC14 +21..23), H2 (block +31)
            for off in (21, 22, 23, GFX_OFF + 31) + (((GFX_OFF + S_JT,) if SMP else (GFX_OFF + S_JF, GFX_OFF + S_JT)) if JUMP else ()): a.emit(strb_w, 1, 0, off)
            if SMP:                                                             # the sample: stop (and no forced loop)
                a.emit(ldrb_w, 2, 0, GFX_OFF + S_JF); a.emit(movs_imm, 3, 0x30 | SMB_LOOP | (SMB_GATE if LATCH7 else 0)); a.emit(bics_reg, 2, 3)
                a.emit(movs_imm, 3, 0x30 | SMB_REC); a.emit(bics_reg, 2, 3); a.emit(movs_imm, 3, 0x30); a.emit(orrs_reg, 2, 3); a.emit(strb_w, 2, 0, GFX_OFF + S_JF)
                a.emit(raw, str_w(1, 0, GFX_OFF + S_SMT))                       # (r1 = 0) not latched, not armed
        a.emit(bl, L["c_gpick_t"])                                              # r1 = 0: Gater
        a.emit(movs_imm, 1, 1); a.emit(bl, L["c_gpick_t"])                      # r1 = 1: Auto-Filter
        a.emit(pop_list, [4], pc=True)
        # ---- c_clrled (r0 = LED buffer): entry 7 lit while any effect is latched
        a.label("c_clrled")
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0)
        if CLR_COPY: a.emit(raw, ldrh_w(0, 4, 48)); a.emit(strh_imm, 0, 4, 14); a.emit(b, "cl_out")      # = pad 25, the FX bypass pad copied from the FX view
        a.emit(bl, "c_gfst"); zjmp(0, "cl_out")
        a.emit(ldrb_imm, 1, 0, S_LATCH)
        a.emit(subs_imm8, 0, GFX_OFF); a.emit(ldrb_imm, 2, 0, s14.S_LATCH); a.emit(orrs_reg, 1, 2)
        if CLEAR_SP:                                                            # lit too while a song pointer range is set
            a.emit(ldrb_imm, 2, 0, 21); a.emit(orrs_reg, 1, 2); a.emit(ldrb_imm, 2, 0, 23); a.emit(orrs_reg, 1, 2)
        a.emit(movw, 0, CLR_DIM); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "cl_s", "eq"); a.emit(movw, 0, CLR_ON)
        a.label("cl_s"); a.emit(strh_imm, 0, 4, 14)
        a.label("cl_out"); a.emit(pop_list, [4], pc=True)



def sp2_press(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2):
    """SC32 step press (r4 = SC14 state, r5 = step 1-16; ends at spp_out): Shift = the latched phrase, else held steps (one = retrigger, two = phrase)."""
    if SP3:
        sp3_head(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2)
    else:
        sp2_head(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2)
    a.label("q_mom")
    a.emit(ldrb_w, 1, 4, O_H1); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "q_m2", "ne")
    a.emit(strb_w, 5, 4, O_H1); a.emit(mov_reg, 1, 5); a.emit(movs_imm, 2, 0x40); a.emit(orrs_reg, 1, 2)   # one step: retrigger (bit 6 = its pad held)
    a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spp_out")
    a.label("q_m2")
    a.emit(cmp_reg, 1, 5); bc("spp_out", "eq")
    a.emit(ldrb_w, 2, 4, O_H2); a.emit(cmp_imm, 2, 0); bc("spp_out", "ne")
    a.emit(strb_w, 5, 4, O_H2); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spp_out")   # two steps: the phrase, no retrigger


def sp3_head(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2):
    """SC34.2: Shift = phrase mode on / new start / off; in phrase mode a tap = the end, pad 9 = off; else -> q_mom."""
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "q_ns", "eq")
    a.emit(ldrb_w, 0, 4, O_LS); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "q_new", "eq")
    a.emit(cmp_reg, 0, 5); a.emit(b_cond, "q_mv", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LS); a.emit(strb_w, 1, 4, O_LE); a.emit(b, "q_clr")   # Shift + the start: off
    a.label("q_mv")                                                                      # Shift + another step: a new start
    a.emit(strb_w, 5, 4, O_LS); a.emit(ldrb_w, 1, 4, O_LE); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "q_clr", "eq")
    a.emit(cmp_reg, 1, 5); a.emit(b_cond, "q_clr", "hs"); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LE); a.emit(b, "q_clr")   # an end before it: 16
    a.label("q_new")                                                                     # phrase mode on: the start, the end = 16
    a.emit(strb_w, 5, 4, O_LS); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LE)
    a.label("q_clr")                                                                     # held steps and the retrigger forgotten
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_H1); a.emit(strb_w, 1, 4, O_H2); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spp_out")
    a.label("q_ns")
    a.emit(ldrb_w, 0, 4, O_LS); a.emit(cmp_imm, 0, 0); bc("q_mom", "eq")
    a.emit(cmp_imm, 5, 1); a.emit(b_cond, "q_end", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LS); a.emit(strb_w, 1, 4, O_LE); a.emit(b, "q_clr")   # pad 9 (white): off
    a.label("q_end")                                                                     # a tap: the end (before the start: they swap)
    a.emit(cmp_reg, 5, 0); a.emit(b_cond, "q_e2", "hs")
    a.emit(strb_w, 0, 4, O_LE); a.emit(strb_w, 5, 4, O_LS); a.emit(b, "q_clr")
    a.label("q_e2"); a.emit(strb_w, 5, 4, O_LE); a.emit(b, "q_clr")


def sp2_head(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2):
    """SC32: Shift = the latched phrase; pad 9 with a latched phrase = off; else -> q_mom."""
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "q_ns", "eq")
    a.emit(ldrb_w, 0, 4, O_LS); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "q_new", "eq")
    a.emit(ldrb_w, 1, 4, O_LE); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "q_new", "ne")    # a latched phrase: a new start
    a.emit(cmp_reg, 0, 5); a.emit(b_cond, "q_end", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LS); a.emit(b, "q_clr")              # the start again: off
    a.label("q_end")                                                                     # the second step: the end (the lower is the start)
    a.emit(cmp_reg, 5, 0); a.emit(b_cond, "q_e2", "hs")
    a.emit(strb_w, 0, 4, O_LE); a.emit(strb_w, 5, 4, O_LS); a.emit(b, "q_clr")
    a.label("q_e2"); a.emit(strb_w, 5, 4, O_LE); a.emit(b, "q_clr")
    a.label("q_new")
    a.emit(strb_w, 5, 4, O_LS); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LE)
    a.label("q_clr")                                                                     # held steps and the retrigger forgotten
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_H1); a.emit(strb_w, 1, 4, O_H2); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spp_out")
    a.label("q_ns")
    a.emit(ldrb_w, 0, 4, O_LS); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "q_mom", "eq")
    a.emit(cmp_imm, 5, 1); a.emit(b_cond, "q_mom", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LS); a.emit(strb_w, 1, 4, O_LE); a.emit(b, "q_clr")   # pad 9 with a latched phrase: off


def songptr_code(a, L, pal_codes, bc, zjmp):
    """SC17.7: song pointer in the Master FX view (pads 9-24 = steps 1-16).
    State (all in reserved bytes that were unused, zeroed by the block / SC14 init):
      SC14 state + 21  LS  latched start step (1-16, 0 = none)
      SC14 state + 22  LE  latched end step (0 = default 16)
      SC14 state + 23  H1  first held step (0 = none)           (momentary range, only while no latched start)
      Master FX block + 31 (= SC14 state + 71)  H2  second held step
    Effective range (S, E) = (LS, LE or 16) if LS else (H1, H2 or 16) if H1 else none.  The sequencer tick (0x0802C418)
    is hooked: when the tick about to run is the first of step E + 1 (of the 16-step cycle), the song position is set
    (stock 0x0802BFE0: ticks + resync of all tracks) so that it runs the first tick of step S instead.
    """
    c_gst, c_shift = L["c_gst"], L["c_shift"]
    udiv, mls = s14.udiv, s14.mls
    O_LS, O_LE, O_H1, O_H2 = 21, 22, 23, GFX_OFF + 31
    base_c, head_c, start_c, end_c = SP_COLORS(L.get("pal_sp", pal_codes))

    # ---- c_speff: r0 = SC14 state -> r0 = start step S (0: no range), r1 = end step E; clobbers r2
    a.label("c_speff")
    if SP2:                                                                    # two held steps first (the lower is the start), then the latched phrase
        a.emit(ldrb_w, 2, 0, O_H1); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "se_l", "eq")
        a.emit(ldrb_w, 1, 0, O_H2); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "se_l", "eq")
        a.emit(cmp_reg, 1, 2); a.emit(b_cond, "se_ok", "hs"); a.emit(mov_reg, 3, 1); a.emit(mov_reg, 1, 2); a.emit(mov_reg, 2, 3); a.emit(b, "se_ok")
        a.label("se_l")
        a.emit(ldrb_w, 2, 0, O_LS); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "se_no", "eq")
        a.emit(ldrb_w, 1, 0, O_LE); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "se_ok", "ne"); a.emit(movs_imm, 1, 16)
        a.label("se_ok"); a.emit(mov_reg, 0, 2); a.emit(raw, h(0x4770))
        a.label("se_no"); a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 16); a.emit(raw, h(0x4770))
    else:
        a.emit(ldrb_w, 2, 0, O_LS); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "se_nl", "eq")
        a.emit(ldrb_w, 1, 0, O_LE); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "se_ok", "ne"); a.emit(movs_imm, 1, 16)
        a.label("se_ok"); a.emit(mov_reg, 0, 2); a.emit(raw, h(0x4770))
        a.label("se_nl")
        a.emit(ldrb_w, 2, 0, O_H1); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "se_no", "eq")
        if SP_NORM:                                                            # the lower of the two held steps is the start
            a.emit(ldrb_w, 1, 0, O_H2); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "se_h2z", "eq")
            a.emit(cmp_reg, 1, 2); a.emit(b_cond, "se_ok", "hs"); a.emit(mov_reg, 3, 1); a.emit(mov_reg, 1, 2); a.emit(mov_reg, 2, 3); a.emit(b, "se_ok")
            a.label("se_h2z"); a.emit(movs_imm, 1, 16); a.emit(b, "se_ok")
        else:
            a.emit(ldrb_w, 1, 0, O_H2); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "se_ok", "ne"); a.emit(movs_imm, 1, 16); a.emit(b, "se_ok")
        a.label("se_no"); a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 16); a.emit(raw, h(0x4770))

    # ---- c_spengine: r0 = sequencer engine (X = [[ctx + 0x10]]; E = [[X + 0x2C] + 4])
    a.label("c_spengine")
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x10); a.emit(ldr_imm, 0, 0, 0)
    a.emit(ldr_imm, 0, 0, 0x2C); a.emit(ldr_imm, 0, 0, 4); a.emit(raw, h(0x4770))

    # ---- c_sppos: r0 = current step 0-15 of the 16-step cycle, or 0xFF when the transport is not running
    a.label("c_sppos")
    a.emit(push_list, [4], lr=True)
    a.emit(bl, "c_spengine"); a.emit(mov_reg, 4, 0)
    if SP_PLAY:                                                                # the transport state: the store the Play button toggles (0x20011034, = [macro handler + 0x28])
        a.emit(movw, 0, PLAY_STORE & 0xFFFF); a.emit(movt, 0, PLAY_STORE >> 16)
    else:
        a.emit(ldr_imm, 0, 4, 0x28)
    a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pp_run", "ne"); a.emit(movs_imm, 0, 0xFF); a.emit(pop_list, [4], pc=True)
    a.label("pp_run")
    a.emit(raw, ldr_w(0, 4, 0x90)); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0)
    a.emit(movs_imm, 1, 6); a.emit(raw, udiv(0, 0, 1)); a.emit(movs_imm, 1, 15); a.emit(ands_reg, 0, 1)
    a.emit(pop_list, [4], pc=True)

    if SPCACHE:
        # ---- c_spcur: r0 = the step 0-15 the tick hook saw last, or 0xFF when that was more than 2 s ago (stopped).  The word at S_SPS = (HAL clock / 64, 24 bit) << 8 | step: it does not wrap into "fresh" for 12 days
        a.label("c_spcur")
        a.emit(push_list, [4], lr=True)
        a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "cur_no", "eq"); a.emit(mov_reg, 4, 0)
        a.emit(ldr_imm, 1, 4, GFX_OFF + S_SPS)
        a.emit(movw, 2, s14.TICK & 0xFFFF); a.emit(movt, 2, s14.TICK >> 16); a.emit(ldr_imm, 2, 2, 0); a.emit(lsrs_imm, 2, 2, 6)
        a.emit(mov_reg, 3, 1); a.emit(lsrs_imm, 3, 3, 8); a.emit(subs_reg, 3, 2, 3); a.emit(lsls_imm, 3, 3, 8); a.emit(lsrs_imm, 3, 3, 8)       # age (24 bit, units of 64 ms)
        a.emit(cmp_imm, 3, 32); a.emit(b_cond, "cur_no", "hs")
        a.emit(movs_imm, 0, 0xFF); a.emit(ands_reg, 1, 0); a.emit(mov_reg, 0, 1); a.emit(pop_list, [4], pc=True)
        a.label("cur_no")
        a.emit(movs_imm, 0, 0xFF); a.emit(pop_list, [4], pc=True)

    # ---- c_sp_press (r0 = pad 8-23): Shift = latch the start (again = off), latched start: a tap sets the end,
    #      otherwise hold = momentary start (first pad) and end (second pad)
    a.label("c_sp_press")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(subs_imm8, 0, 7); a.emit(mov_reg, 5, 0)                             # r5 = step 1-16
    a.emit(bl, c_gst); zjmp(0, "spp_out"); a.emit(mov_reg, 4, 0)
    if SP2:
        sp2_press(a, bc, c_shift, O_LS, O_LE, O_H1, O_H2)
    if JUMP and not SP2:                                                       # jump mode: this step is the target of the next step
        a.emit(ldrb_w, 1, 4, GFX_OFF + S_JF); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "spp_nj", "eq")
        if JUMP_HOLD:
            a.emit(mov_reg, 1, 5); a.emit(movs_imm, 2, 0x40); a.emit(orrs_reg, 1, 2); a.emit(strb_w, 1, 4, GFX_OFF + S_JT)
        else:
            a.emit(strb_w, 5, 4, GFX_OFF + S_JT)
        a.emit(b, "spp_out")
        a.label("spp_nj")
    a.emit(bl, c_shift); a.emit(mov_reg, 6, 0)
    a.emit(ldrb_w, 0, 4, O_LS)
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "spp_ns", "eq")
    a.emit(cmp_reg, 0, 5); a.emit(b_cond, "spp_set", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LS); a.emit(strb_w, 1, 4, O_LE); a.emit(b, "spp_clr")      # same step: off
    a.label("spp_set")
    a.emit(strb_w, 5, 4, O_LS)                                                # new start (moves it)
    a.emit(ldrb_w, 1, 4, O_LE); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "spp_clr", "eq")
    a.emit(cmp_reg, 1, 5); a.emit(b_cond, "spp_clr", "hs"); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_LE)  # end before start: default
    a.label("spp_clr")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_H1); a.emit(strb_w, 1, 4, O_H2); a.emit(b, "spp_out")
    a.label("spp_ns")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "spp_mom", "eq")
    if SP_NORM:                                                                # latched start: a tap above = end; a tap below = the new start, the old start becomes the end
        a.emit(cmp_reg, 5, 0); a.emit(b_cond, "spp_te", "hs")
        a.emit(strb_w, 0, 4, O_LE); a.emit(strb_w, 5, 4, O_LS); a.emit(b, "spp_out")
        a.label("spp_te"); a.emit(strb_w, 5, 4, O_LE); a.emit(b, "spp_out")
    else:
        a.emit(cmp_reg, 5, 0); a.emit(b_cond, "spp_out", "lo"); a.emit(strb_w, 5, 4, O_LE); a.emit(b, "spp_out")   # latched start: tap = end
    a.label("spp_mom")
    a.emit(ldrb_w, 1, 4, O_H1); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "spp_m2", "ne"); a.emit(strb_w, 5, 4, O_H1); a.emit(b, "spp_out")
    a.label("spp_m2")
    a.emit(cmp_reg, 1, 5); a.emit(b_cond, "spp_out", "eq")
    a.emit(ldrb_w, 2, 4, O_H2); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "spp_out", "ne"); a.emit(strb_w, 5, 4, O_H2)
    a.label("spp_out"); a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_sp_rel (r0 = pad 8-23): release of a momentary pad
    a.label("c_sp_rel")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(subs_imm8, 0, 7); a.emit(mov_reg, 5, 0)
    a.emit(bl, c_gst); zjmp(0, "spr_out"); a.emit(mov_reg, 4, 0)
    if SP2:                                                                    # the retrigger target released: no more repeats (one not done yet still happens once); then the held steps
        a.emit(ldrb_w, 1, 4, GFX_OFF + S_JT); a.emit(movs_imm, 3, 0x1F); a.emit(mov_reg, 2, 1); a.emit(ands_reg, 2, 3)
        a.emit(cmp_reg, 2, 5); a.emit(b_cond, "spr_h", "ne")
        a.emit(movs_imm, 3, 0x80); a.emit(tst_reg, 1, 3); a.emit(b_cond, "spr_qb", "eq")
        a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spr_h")
        a.label("spr_qb")
        a.emit(movs_imm, 3, 0x40); a.emit(bics_reg, 1, 3); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spr_h")
    elif JUMP_HOLD:                                                            # the step pad of a step jump is released: no more repeats (a jump not done yet still happens once)
        a.emit(ldrb_w, 1, 4, GFX_OFF + S_JT); a.emit(movs_imm, 3, 0x1F); a.emit(mov_reg, 2, 1); a.emit(ands_reg, 2, 3)
        a.emit(cmp_reg, 2, 5); a.emit(b_cond, "spr_nh", "ne")
        a.emit(movs_imm, 3, 0x80); a.emit(tst_reg, 1, 3); a.emit(b_cond, "spr_hb", "eq")
        a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spr_out")
        a.label("spr_hb")
        a.emit(movs_imm, 3, 0x40); a.emit(bics_reg, 1, 3); a.emit(strb_w, 1, 4, GFX_OFF + S_JT); a.emit(b, "spr_out")
        a.label("spr_nh")
    a.emit(ldrb_w, 1, 4, O_LS); zjmp(1, "spr_h"); a.emit(b, "spr_out")        # latched start: holds are not tracked
    a.label("spr_h")
    a.emit(ldrb_w, 1, 4, O_H2); a.emit(cmp_reg, 1, 5); a.emit(b_cond, "spr_1", "ne")
    a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_H2); a.emit(b, "spr_out")
    a.label("spr_1")
    a.emit(ldrb_w, 1, 4, O_H1); a.emit(cmp_reg, 1, 5); a.emit(b_cond, "spr_out", "ne")
    a.emit(ldrb_w, 1, 4, O_H2); a.emit(strb_w, 1, 4, O_H1); a.emit(movs_imm, 1, 0); a.emit(strb_w, 1, 4, O_H2)
    a.label("spr_out"); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_sp_leds (r0 = LED buffer): pads 9-24 = the 16 steps: dim, start / end markers, the playhead bright
    a.label("c_sp_leds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 16)                            # S = none, E = 16
    a.emit(bl, c_gst); zjmp(0, "spl_p"); a.emit(bl, "c_speff"); a.emit(mov_reg, 6, 0); a.emit(mov_reg, 7, 1)
    a.label("spl_p")
    a.emit(bl, "c_spcur" if SPCACHE else "c_sppos"); a.emit(mov_reg, 5, 0)     # r5 = playhead step 0-15 or 0xFF
    a.emit(movs_imm, 2, 0)
    a.label("spl_l")
    a.emit(movw, 3, base_c)
    a.emit(mov_reg, 1, 2); a.emit(adds_imm8, 1, 1)                             # r1 = step 1-16
    a.emit(cmp_reg, 1, 6); a.emit(b_cond, "spl_n1", "ne"); a.emit(movw, 3, start_c)
    a.label("spl_n1")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "spl_n2", "eq"); a.emit(cmp_reg, 1, 7); a.emit(b_cond, "spl_n2", "ne"); a.emit(movw, 3, end_c)
    a.label("spl_n2")
    a.emit(cmp_reg, 2, 5); a.emit(b_cond, "spl_n3", "ne"); a.emit(movw, 3, SP_HEAD if SPCACHE else head_c)
    a.label("spl_n3")
    a.emit(lsls_imm, 0, 2, 1); a.emit(adds_imm8, 0, 16); a.emit(raw, h(0x5200 | 0 << 6 | 4 << 3 | 3))      # strh r3,[r4,r0]
    a.emit(adds_imm8, 2, 1); a.emit(cmp_imm, 2, 16); bc("spl_l", "lo")
    if JUMP_LED:                                                               # the step a jump is pending / repeating on: lit (white with JUMP_WHITE)
        a.emit(bl, c_gst); zjmp(0, "spl_x")
        a.emit(ldrb_w, 1, 0, GFX_OFF + S_JT); a.emit(movs_imm, 2, 0x1F); a.emit(ands_reg, 1, 2); zjmp(1, "spl_x")
        a.emit(subs_imm8, 1, 1); a.emit(lsls_imm, 1, 1, 1); a.emit(adds_imm8, 1, 16)
        a.emit(movw, 3, JMP_ON if JUMP_WHITE else head_c); a.emit(raw, h(0x5200 | 1 << 6 | 4 << 3 | 3))
        a.label("spl_x")
    if SP2:                                                                    # a latched phrase: pad 9 (step 1) white
        a.emit(bl, c_gst); zjmp(0, "spl_y")
        a.emit(ldrb_w, 1, 0, O_LS); zjmp(1, "spl_y")
        a.emit(movw, 3, SP2_WHITE); a.emit(strh_imm, 3, 4, 16)
        a.label("spl_y")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if JUMP:
        # ---- c_jmpled (r0 = LED buffer): pad 7 bright while the jump mode is on, dim otherwise
        a.label("c_jmpled")
        a.emit(push_list, [4], lr=True)
        a.emit(mov_reg, 4, 0)
        a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "jl_out", "eq")
        a.emit(ldrb_w, 1, 0, GFX_OFF + S_JF)
        off_c, on_c = (JMP_OFF, JMP_ON) if JUMP_WHITE else (base_c, head_c)
        a.emit(movw, 0, off_c); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "jl_s", "eq"); a.emit(movw, 0, on_c)
        a.label("jl_s"); a.emit(strh_imm, 0, 4, 12)
        a.label("jl_out"); a.emit(pop_list, [4], pc=True)

    # ---- c_sptick: entry of the sequencer tick (0x0802C418; displaced `push.w {r4-r8, lr}` first, r0 = engine)
    a.label("c_sptick")
    a.emit(raw, h(0xE92D) + h(0x41F0))
    a.emit(mov_reg, 8, 0)
    a.emit(bl, c_gst); zjmp(0, "spt_d"); a.emit(mov_reg, 7, 0)
    a.emit(ldr_imm, 1, 7, GFX_OFF); a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16)
    a.emit(cmp_reg, 1, 2); bc("spt_d", "ne")                                   # Master FX block not initialised yet
    if SPCACHE:                                                                # the playhead: the step of the tick about to run, with the time of the observation
        a.emit(raw, ldr_w(0, 8, 0x90)); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 6, 0, 0); a.emit(adds_imm8, 6, 1)
        a.emit(movs_imm, 1, 6); a.emit(raw, udiv(2, 6, 1)); a.emit(movs_imm, 3, 15); a.emit(ands_reg, 2, 3)
        a.emit(movw, 0, s14.TICK & 0xFFFF); a.emit(movt, 0, s14.TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 6); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 2)
        a.emit(str_imm, 0, 7, GFX_OFF + S_SPS)                                 # (clock / 64) << 8 | step
    if SMP:                                                                    # the armed bar of the sample: starts / ends on a bar line (tick % 96 == 0)
        a.emit(raw, ldr_w(5, 7, GFX_OFF + S_SMT)); a.emit(cmp_imm, 5, 0); bc("spt_ns", "ge")
        a.emit(raw, ldr_w(0, 8, 0x90)); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0); a.emit(adds_imm8, 0, 1)
        a.emit(movs_imm, 1, BAR_TICKS); a.emit(raw, udiv(2, 0, 1)); a.emit(raw, mls(3, 2, 1, 0)); a.emit(cmp_imm, 3, 0); bc("spt_ns", "ne")
        a.emit(ldrb_w, 0, 7, GFX_OFF + S_JF); a.emit(movs_imm, 1, SMB_REC)
        a.emit(lsls_imm, 2, 5, 1); a.emit(b_cond, "spt_sb", "pl")                               # bit 30 clear: the bar starts
        if SMP2: a.emit(bics_reg, 0, 1); a.emit(movw, 2, 0); a.emit(movt, 2, 0x3F80); a.emit(ands_reg, 5, 2); a.emit(b, "spt_sw")   # bit 30 set: the bar is over (the request stays)
        else: a.emit(bics_reg, 0, 1); a.emit(movs_imm, 5, 0); a.emit(b, "spt_sw")                    # bit 30 set: the bar is over
        a.label("spt_sb")
        a.emit(orrs_reg, 0, 1); a.emit(movw, 2, 0); a.emit(movt, 2, SMT_LATCH >> 16); a.emit(orrs_reg, 5, 2)
        a.label("spt_sw")
        a.emit(strb_w, 0, 7, GFX_OFF + S_JF); a.emit(raw, str_w(5, 7, GFX_OFF + S_SMT))
        a.label("spt_ns")
    if JUMP:                                                                   # pending jump: at the first tick of the next step
        a.emit(ldrb_w, 4, 7, GFX_OFF + S_JT); a.emit(cmp_imm, 4, 0); bc("spt_nj", "eq")
        if JUMP_HOLD:
            a.emit(movs_imm, 5, 0x1F); a.emit(ands_reg, 4, 5)                  # r4 = the target step 1-16 (bit 6 = its pad is held, bit 7 = jumped once)
        if JUMP_REPEAT:                                                        # bit 7 = repeating: it ends the moment the jump mode is off (pad released / toggled)
            a.emit(movs_imm, 5, 0x80); a.emit(tst_reg, 4, 5); bc("spt_jg", "eq")
            a.emit(ldrb_w, 5, 7, GFX_OFF + S_JF); a.emit(cmp_imm, 5, 0); bc("spt_jg", "ne")
            a.emit(movs_imm, 5, 0); a.emit(strb_w, 5, 7, GFX_OFF + S_JT); a.emit(b, "spt_nj")
            a.label("spt_jg")
            a.emit(movs_imm, 5, 0x1F); a.emit(ands_reg, 4, 5)                  # r4 = the target step 1-16
        a.emit(raw, ldr_w(0, 8, 0x90)); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 6, 0, 0)
        a.emit(adds_imm8, 6, 1)                                                # n = the tick about to run
        a.emit(movs_imm, 1, 6); a.emit(raw, udiv(2, 6, 1)); a.emit(raw, mls(3, 2, 1, 6))
        a.emit(cmp_imm, 3, 0); bc("spt_nj", "ne")
        a.emit(movs_imm, 3, 15); a.emit(ands_reg, 2, 3); a.emit(muls, 2, 1)     # (step of n) * 6
        a.emit(subs_reg, 6, 6, 2); a.emit(subs_imm8, 4, 1); a.emit(muls, 4, 1); a.emit(adds_reg, 6, 6, 4)   # + (target - 1) * 6
        if JUMP_HOLD:                                                          # the step pad still held: keep the target (bit 7 = jumped once); released before: one jump only
            a.emit(ldrb_w, 0, 7, GFX_OFF + S_JT); a.emit(movs_imm, 1, 0x40); a.emit(tst_reg, 0, 1); a.emit(b_cond, "spt_j1", "eq")
            a.emit(movs_imm, 1, 0x80); a.emit(orrs_reg, 0, 1); a.emit(strb_w, 0, 7, GFX_OFF + S_JT); a.emit(b, "spt_nz0")
            a.label("spt_j1")
        if JUMP_REPEAT:                                                        # jump mode still on: keep the target and mark it as repeating
            a.emit(ldrb_w, 0, 7, GFX_OFF + S_JF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "spt_j1", "eq")
            a.emit(ldrb_w, 0, 7, GFX_OFF + S_JT); a.emit(movs_imm, 1, 0x80); a.emit(orrs_reg, 0, 1)
            a.emit(strb_w, 0, 7, GFX_OFF + S_JT); a.emit(b, "spt_nz0")
            a.label("spt_j1")
        a.emit(movs_imm, 0, 0); a.emit(strb_w, 0, 7, GFX_OFF + S_JT)
        a.emit(b, "spt_nz0")
        a.label("spt_nj")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_speff")                               # r0 = S, r1 = E
    zjmp(0, "spt_d")
    a.emit(cmp_reg, 1, 0); bc("spt_d", "lo")                                   # end before start: no loop
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(cmp_imm, 4, 1); a.emit(b_cond, "spt_a", "ne"); a.emit(cmp_imm, 5, 16); bc("spt_d", "eq")   # 1..16: nothing to do
    a.label("spt_a")
    a.emit(raw, ldr_w(0, 8, 0x90)); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 6, 0, 0)
    a.emit(adds_imm8, 6, 1)                                                    # n = the tick about to run
    a.emit(movs_imm, 1, 6); a.emit(raw, udiv(2, 6, 1)); a.emit(raw, mls(3, 2, 1, 6))
    a.emit(cmp_imm, 3, 0); bc("spt_d", "ne")                                   # not the first tick of a step
    a.emit(movs_imm, 3, 15); a.emit(ands_reg, 2, 3)                            # step index of n in the 16-step cycle
    if SP_NORM:                                                                # at or beyond the end (step > E), or the wrap when E = 16: back to the start
        a.emit(cmp_imm, 5, 16); a.emit(b_cond, "spt_e16", "hs")
        a.emit(cmp_reg, 2, 5); bc("spt_d", "lo"); a.emit(mov_reg, 3, 2); a.emit(b, "spt_go")
        a.label("spt_e16"); a.emit(cmp_imm, 2, 0); bc("spt_d", "ne"); a.emit(movs_imm, 3, 16)
        a.label("spt_go")
        a.emit(subs_reg, 0, 3, 4); a.emit(adds_imm8, 0, 1); a.emit(movs_imm, 1, 6); a.emit(muls, 0, 1)   # (steps past the start) * 6
    else:
        a.emit(mov_reg, 3, 5); a.emit(movs_imm, 0, 15); a.emit(ands_reg, 3, 0)     # E mod 16 (16 -> 0)
        a.emit(cmp_reg, 2, 3); bc("spt_d", "ne")
        a.emit(subs_reg, 0, 5, 4); a.emit(adds_imm8, 0, 1); a.emit(movs_imm, 1, 6); a.emit(muls, 0, 1)   # (E - S + 1) * 6
    a.emit(subs_reg, 6, 6, 0)                                                  # new tick = n - that
    a.label("spt_nz0")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "spt_nz", "ne")                      # 0 would need tick -1: use a later, aligned tick
    a.emit(movw, 0, SP_BIG & 0xFFFF); a.emit(movt, 0, SP_BIG >> 16); a.emit(adds_reg, 6, 6, 0)
    a.label("spt_nz")
    a.emit(subs_imm8, 6, 1); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 0, 8); a.emit(bl, SET_TICKS)   # stock sets ticks and resyncs the tracks; the tick adds 1
    a.label("spt_d")
    a.emit(mov_reg, 0, 8); a.emit(b_w, TICK_BACK)
    if ARMPLAY2:
        # ---- c_stk: entry of SET_TICKS (0x0802BFE0; displaced push {r4-r6, lr}; mov r4, r0): the transport's start (0x0802BD3C, position 0) starts an armed capture
        a.label("c_stk")
        a.emit(cmp_imm, 1, 0); bc("stk_o", "ne")
        a.emit(mov_reg, 2, 14); a.emit(movw, 3, START_RET & 0xFFFF); a.emit(movt, 3, START_RET >> 16); a.emit(cmp_reg, 2, 3); bc("stk_o", "ne")
        a.emit(push_list, [0, 1, 4], lr=True)
        a.emit(bl, c_gst); a.emit(cmp_imm, 0, 0); bc("stk_x", "eq"); a.emit(mov_reg, 4, 0)
        a.emit(raw, ldr_w(1, 4, GFX_OFF)); a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16); a.emit(cmp_reg, 1, 2); bc("stk_x", "ne")
        a.emit(raw, ldr_w(1, 4, GFX_OFF + S_SMT)); a.emit(cmp_imm, 1, 0); bc("stk_x", "ge")                 # not armed
        a.emit(lsls_imm, 2, 1, 1); bc("stk_x", "mi")                                                        # its bar already running
        a.emit(movw, 2, 0); a.emit(movt, 2, SMT_LATCH >> 16); a.emit(orrs_reg, 1, 2); a.emit(raw, str_w(1, 4, GFX_OFF + S_SMT))
        a.emit(ldrb_w, 1, 4, GFX_OFF + S_JF); a.emit(movs_imm, 2, SMB_REC); a.emit(orrs_reg, 1, 2); a.emit(strb_w, 1, 4, GFX_OFF + S_JF)
        a.label("stk_x")
        a.emit(raw, popw([0, 1, 4], lr=True))
        a.label("stk_o")
        a.emit(raw, h(0xB570)); a.emit(raw, h(0x4604)); a.emit(b_w, SET_TICKS + 4)


def patch_p(img, p, old, new):
    """patch DSP P words in the relocated block (loader table) and in the original block."""
    tab = struct.unpack_from("<I", img, s16.DSP_TABLE - BASE)[0]
    for blk in (tab, s10.DSP0):
        o = blk - BASE + 6 + 3 * p
        cur = [int.from_bytes(img[o + 3 * i:o + 3 * i + 3], 'big') for i in range(len(old))]
        assert cur == old, (hex(blk), hex(p), [hex(x) for x in cur])
        for i, w in enumerate(new):
            img[o + 3 * i:o + 3 * i + 3] = w.to_bytes(3, 'big')


def build(stock: bytes, listing: Path):
    img16, report = s16.build(stock, listing)
    img = bytearray(img16)
    img[sc.MARK_OFF:sc.MARK_OFF + 6] = MARKER.ljust(6, b"\0")
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    patch_p(img, FX_HOOK, [0x61F400, 0x002E10], D.jsr(dl["fx_hook"]))

    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    assert text(BTN13, 4) == "ldr r0, [r4, #0xc]|movs r1, #0", text(BTN13, 4)
    assert text(BTN14, 6) == "movs r2, #0xe|adr r0, #0x1fc|b #0x80335fa", text(BTN14, 6)
    assert ((BTN14 + 2 + 4) & ~3) + 0x1FC == BTN14_LIT and struct.unpack_from("<I", stock, BTN14_LIT - BASE)[0] == 2
    assert text(BTN14_TAIL, 2) == "ldr r1, [r0]"
    assert text(BTN13_STOCK, 2) == "adr r1, #0x1b8", text(BTN13_STOCK, 2)
    assert ((BTN13_STOCK + 4) & ~3) + 0x1B8 == MIX_ID_LIT and text(BTN13_STOCK + 2, 4) == "movs r2, #0xd|ldr r1, [r1]"
    assert text(0x080335FC, 8) == "mov r0, r4|pop.w {r3, r4, r5, lr}|b #0x803390c", text(0x080335FC, 8)
    vt = [struct.unpack_from("<I", img, MIX_VT + 4 * i - BASE)[0] for i in (0, 1, 4, 7)]
    assert vt == [MIX_PRESS | 1, MIX_REL | 1, MIX_KNOB | 1, MIX_LEDS | 1], [hex(x) for x in vt]
    L = {k: int(report["sc14"]["labels"][k], 16) for k in ("c_gst", "c_now", "c_beat", "c_gtick")}
    L["c_shift"] = int(report["sc15"]["labels"]["c_shift"], 16)
    L["c_sleds"] = int(report["sc15"]["labels"]["c_sleds"], 16)
    if SLOTS:
        for k in ("c_fxpress", "c_fxrel", "c_fxleds"): L[k] = int(report["sc14"]["labels"][k], 16)
    if CLEARPAD: L["c_gpick_t"] = int(report["sc14"]["labels"]["c_gpick_t"], 16)
    assert bytes(img[SVC_HOOK - BASE:SVC_HOOK - BASE + 4]) == b_w(SVC_HOOK, L["c_gtick"])

    # data: tables, defaults, maps, palette codes
    pal = [struct.unpack_from("<H", stock, PAL - BASE + 2 * i)[0] for i in range(16)]
    pal_codes = [(pal[on], pal[dim]) for on, dim in PAL_IDX]
    if VINYL_COL:
        L["pal_sp"] = list(pal_codes); pal_codes[5] = VINYL_COL
    tabs = tables()
    ext = (len(img) + BASE + 3) & ~3
    data = bytearray()
    tabaddr = {}
    for name, vals in tabs.items():
        tabaddr[name] = ext + len(data); data += struct.pack("<128I", *vals)
    defaults_addr = ext + len(data); data += bytes(x for d in DEFAULTS for x in d)
    setmap_addr = ext + len(data); data += bytes(SETMAP + ([SMP_SET] if SMP2 else []) + ([GL_SET] if GLITCH else []))
    assert not GLITCH or S_KNOB + 4 * GL_SET == S_SLOT + 4 * GL_SLOT
    assert not SMP2 or S_KNOB + 4 * SMP_SET == S_SLOT + 4 * SMP_SLOT
    fxbits_addr = ext + len(data); data += bytes(FXBITS)
    while len(data) % 4: data += b"\xFF"
    code_at = ext + len(data)
    code, labels = arm_code(code_at, L, tabaddr, defaults_addr, setmap_addr, fxbits_addr, pal_codes)
    img += b"\xFF" * (ext - BASE - len(img)) + data + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    hook = BTN14 if ENTRY == "mixer14" else BTN13
    img[hook - BASE:hook - BASE + 4] = b_w(hook, labels["c_mixbtn"])
    img[SVC_HOOK - BASE:SVC_HOOK - BASE + 4] = b_w(SVC_HOOK, labels["c_fxtick"])
    if DIAG:
        import build_sc15 as s15m
        assert struct.unpack_from("<I", img, s15m.SP_VT + 0x1C - BASE)[0] == L["c_sleds"] | 1
        struct.pack_into("<I", img, s15m.SP_VT + 0x1C - BASE, labels["c_dleds"] | 1)
    mix_hooks = ((0, "c_gpress"), (1, "c_grel"), (4, "c_gknob"), (7, "c_gleds"))
    if SLOTS:                                        # SC17.6: bottom FX row; the Master FX view hands pads 25-32 to the FX view's handlers
        fxvt = [struct.unpack_from("<I", img, s14.FX_VT + 4 * i - BASE)[0] for i in (0, 1, 7)]
        assert fxvt == [L["c_fxpress"] | 1, L["c_fxrel"] | 1, L["c_fxleds"] | 1], [hex(x) for x in fxvt]
        for slot, lab in ((0, "c_f_press"), (1, "c_f_rel"), (7, "c_f_leds")):
            struct.pack_into("<I", img, s14.FX_VT + 4 * slot - BASE, labels[lab] | 1)
        mix_hooks = ((0, "c_s_press"), (1, "c_s_rel"), (4, "c_gknob"), (7, "c_s_leds"))
    for slot, lab in mix_hooks:
        struct.pack_into("<I", img, MIX_VT + 4 * slot - BASE, labels[lab] | 1)
    if SONGPTR:                                      # SC17.7: sequencer tick (first 4 bytes: push.w {r4-r8, lr})
        assert text(TICK_FN, 6) == "push.w {r4, r5, r6, r7, r8, lr}|mov r4, r0", text(TICK_FN, 6)
        assert bytes(img[TICK_FN - BASE:TICK_FN - BASE + 4]) == bytes(stock[TICK_FN - BASE:TICK_FN - BASE + 4])
        img[TICK_FN - BASE:TICK_FN - BASE + 4] = b_w(TICK_FN, labels["c_sptick"])
        if ARMPLAY2:
            assert bytes(img[SET_TICKS - BASE:SET_TICKS - BASE + 4]) == h(0xB570) + h(0x4604)
            img[SET_TICKS - BASE:SET_TICKS - BASE + 4] = b_w(SET_TICKS, labels["c_stk"])
    report["D"]["marker"] = MARKER.decode()
    report["sc17"] = dict(state=hex(s14.ST + GFX_OFF), sc14_state=hex(s14.ST), data=hex(ext),
                          tables={k: hex(v) for k, v in tabaddr.items()}, arm_start=hex(code_at),
                          labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), code_at),
                          pal_codes=[(hex(x), hex(y)) for x, y in pal_codes],
                          **({"jump_repeat": True} if JUMP_REPEAT else {}), **({"jump_hold": True} if JUMP_HOLD else {}), **({"knob_bright": True} if KNOB_BRIGHT else {}), **({"jump_white": [hex(JMP_OFF), hex(JMP_ON)]} if JUMP_WHITE else {}), **({"sp2": hex(SP2_WHITE)} if SP2 else {}), **({"sampler": True} if SMP else {}), **({"sampler2": True} if SMP2 else {}), **({"loophold": True} if SMP_HOLD else {}), **({"sp3": True} if SP3 else {}), **({"smp_savebit": True} if SMP_SAVEBIT else {}), **({"glitch": True} if GLITCH else {}), **({"glitch2": True} if GL2 else {}), **({"glitch3": True} if GL3 else {}))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc17"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{NAME}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{NAME}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=NAME, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("image", hex(len(img)), "state", report["sc17"]["state"], "dsp words", report["sc16"]["dsp_words"])
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
