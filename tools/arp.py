"""SC41.9 (the user, 2026-10-15): an arpeggiator on the note tracks (Synth 1 / 2, MIDI 1 / 2).

    «Función de arpeggiator: sigue la dirección de pattern settings. Se aplica tanto a la secuencia como a la entrada, cada vez que se tocan dos notas
    a la vez» · «una por paso» · «Shift + 25 en pattern settings» · «con Record se graba el acorde» · «la dirección de reproducción puede ser distinta
    a la del patrón. Shift + dirección (pads 27-32) elige el modo del arpeggiator».

The Pattern Settings view of a note track, Shift held: pad 25 = the arpeggiator of the pattern the track plays on / off (yellow / green), pads 27-32 =
its order (fractal, deconstructed, up, down, ping-pong, random; the chosen one green, the others yellow).  Without Shift pad 25 is green while the
pattern's arpeggiator is on.  The setting is a byte per track and pattern in a block of the project's tail (+ 280: "ARP1", a checksum, 32 bytes:
bit 7 on, bits 0-2 the order), so it goes with the project; a project without the block has every arpeggiator off.

  * The sequence: the player's slot 2 (0x08040E5A(this, pattern, step, micro step), called for every micro step while playing) is wrapped.  When two
    or more notes of a step start (the units of the step from this micro step on), they are taken out of the stock's mask and become the chord:
    sorted by pitch, one note a step at the chord's micro step, for as long as its longest note (its length in micro steps); each note through the
    stock's note-on with the length of a step (0x08040FA2: the stock's own note-offs).  The step's random-mutate / dynamics do not touch them.
  * The input: the live note-on of the four track views (0x0804B07A(view, note, velocity, pad)) and note-off (0x0804AF5A(view, pad)) are hooked.
    The first note sounds as always; a second note held with it starts the arpeggio of the held notes: no note-on of its own (with Record the stock's
    recorder gets it, 0x0802E56A, so the chord is recorded), and one note a step: while playing on the track's micro step 0 (stock note-on, a step
    long), stopped from the LED task at the project's tempo and the track's sync rate (the player's note interface, on / off by hand).  It goes on
    while any note is held; the step audition (0x0804B580) is left alone.
Running state (RAM only, put to 0 by each load and new project): the record's tail + 320 (sequence, 28 B a track) and + 432 (input, 28 B a track).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, h, str_sp, strb_imm, strb_reg, sub_sp_imm, add_sp_imm,
                   subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402
from build_sc14 import udiv  # noqa: E402

PLAYER_VT, PLAY_STOCK = 0x0805B750, 0x08040E5A               # slot 2 = play the units of a micro step
PLAYER0, PLAYER_SZ = 0x20040200, 0x184                        # the note tracks' players
NOTE_ON, REL_ENTRY = 0x08040FA2, 0x08041078                   # (this, note, vel, ticks, [sp] tie); free a live entry (this, i)
BATCH_ON, BATCH_OFF = 0x0803BDB4, 0x0803BDBC
TICKS_TAB = 0x0805B8B8                                        # ticks a step by sync rate (words)
LIVE_ON, LIVE_ON_BACK, LIVE_ON_OLD = 0x0804B07A, 0x0804B07E, bytes.fromhex("f8b50446")       # push {r3-r7, lr}; mov r4, r0
LIVE_OFF, LIVE_OFF_BACK, LIVE_OFF_OLD = 0x0804AF5A, 0x0804AF5E, bytes.fromhex("70b54418")     # push {r4-r6, lr}; adds r4, r0, r1
AUDITION_LR = 0x0804B585                                       # the held step's audition calls the live note-on too: left alone
REC, REC_ON = 0x2003C168, 0x0802E56A                          # the recorder's note-on gate (rec, note, vel, track)
ENG = 0x20038EC0                                              # + 0x30 + 4 t: the store of what track t plays (p0 the pattern)
TRANSPORT, TEMPO = 0x20011034, 0x20011404
PARAM_GET, PARAM_WPTR = 0x0803542C, 0x080354FA
HAL_TICK = 0x2000081C
RANDOM = 0x08049908
SESSION_OBJ, TAIL = 0x2003D71C, 0x27024
O_BLK, O_SEQ, O_LIVE, ST_SZ = 280, 320, 432, 28               # (from the tail) the setting block; the running states
O_END = O_LIVE + 4 * ST_SZ                                    # 544
SIG = 0x31505241                                              # "ARP1"
SUMX = 0x5A
PS_PAD_ARP, PS_PAD_ORD = 24, 26                               # pad 25; pads 27-32
ORD_OF_PAD = (4, 5, 0, 1, 2, 3)                               # pads 27-32: fractal, deconstructed, up, down, ping-pong, random
M_UP, M_DOWN, M_PP, M_RND, M_FRAC, M_DEC = 0, 1, 2, 3, 4, 5
COL_AV, COL_ON = 0x2D, 0x17                                   # yellow (available), green (chosen / on)
KWRAP = 120
RATE = False                                                  # SC42.3 (use_rate): the arpeggiator's own resolution and the notes' own gates
D_EXT = 360                                                   # (RATE) from a running state: + 0..5 the notes' gates (micro steps), + 6 the accumulator
EXT_LO, EXT_HI = O_SEQ + D_EXT, O_LIVE + D_EXT + 4 * ST_SZ    # 680 .. 904 of the tail (RAM only, put to 0 with the states)
GATECAP = False                                               # SC42.5 (use_gatecap): a note of the chord at most an arpeggio step
PS_PAD_RATE = 16                                              # (RATE) Shift + pads 17-24 = the resolution (the sync rates 1/32T .. 1/4)


COLS2 = False                                                 # SC42.5 (use_cols2): with Shift only the chosen ones green
RECOFF = False                                                # SC43.2 (use_recoff)
REC_OFF = 0x0802E5CC                                          # the recorder's note-off gate (rec, note, track)
VIEWOFF = False                                               # SC43.7 (use_viewoff)
VIEW_IFC0, VIEW_SZ = 0x200413F0, 0x2F4                        # the note-on interface of track t's view (embedded at view + 0x110)
RATEFLIP = False                                              # SC43.7 (use_rateflip)
PRESSORD = False                                              # SC45.3 (use_pressord)
MUTARP = False                                                # SC45.3 (use_mutarp)
MUTLIVE = False                                               # SC45.4 (use_mutlive)
D_POS, D_MUT = D_EXT + 8, D_EXT + 14                          # (PRESSORD) + 8..13 the notes' places; (MUTARP) + 14 the chord step's mutate level


def use_pressord():
    """SC45.3 (the user, 2026-10-20: «el orden de reproducción es el orden pulsado. Cuando una pulsación se retira, el slot de esa nota queda
    vacío, al volver a introducir una nota nueva, ocupa esa misma posición (y todas las posiciones vacías libres para notas sucesivas) antes de
    ir a una posición posterior»; an empty place is skipped; the orders walk the places): the list is no longer sorted by pitch: each note keeps
    the place it took (a byte per entry in the state's extension, + 8..13), a new note takes the lowest free place; the list stays in place
    order, so up / down / ping-pong / random / fractal / deconstructed walk the places and skip the empty ones.  A step's chord: its units in
    their order (the recorder's: the order they were pressed in)."""
    global PRESSORD
    assert RATE, "use_rate() first"
    PRESSORD = True


def use_mutarp():
    """SC45.3 (the user, 2026-10-20: «los modos mutates también afectan al arpegio si están activados»): a step's chord with a random-mutate
    level (byte [2] of the step) plays each note of its arpeggio through the same chances as the stock-played notes (mutate39: another degree of
    the scale, an octave up / down; the custom scale too); nothing is written back."""
    global MUTARP
    assert RATE, "use_rate() first"
    MUTARP = True


def use_mutlive():
    """SC45.4 (the user, 2026-10-20: «Random-mutate: afecta también al nivel en vivo»): the input's arpeggio (the notes held) through the
    random-mutate level of the step the track is on (the engine's step of the track: playing, the step that plays; stopped, where it stands), each
    note as it is played (c_arnext: the note after the order, before it sounds and becomes the last one); nothing is written."""
    global MUTLIVE
    assert MUTARP, "use_mutarp() first"
    MUTLIVE = True


def use_viewoff():
    """SC43.7 (the user, 2026-10-17: «implementar arpeggiator en midi1-2»): the first note held (the stock's, through the track view's note
    interface, view + 0x110) was stopped through the player's note interface ([player + 0x4C]) when the arpeggio took over; that interface only
    knows its own notes, so the note-off went nowhere (seen in emulation down to the MIDI transmitter): on MIDI 1 / 2 the first note stayed on
    under the whole arpeggio (the MIDI out and the own engine: its gate never closed), on the synths until the arpeggio played it again.  Now
    it is stopped through the view's interface that started it, with its pad (the view's note-off takes the pad: [view + 0x80 + note]; the
    stock's own note-off when the pad is let go then finds nothing)."""
    global VIEWOFF
    VIEWOFF = True


def use_rateflip():
    """SC43.7 (the user, 2026-10-17: «el reloj de arpeggiator no es consistente con reloj de proyecto. Solución: más lento a la izquierda, más
    rápido a la derecha»): the stock's sync rate pads (17-24 of Pattern Settings) go from 1/4 (pad 17) to 1/32T (pad 24); the arpeggiator's
    resolution pads went the other way.  Now the same as the stock's: pad 17 = 1/4 ... pad 24 = 1/32T.  The setting's values are the same
    (bits 3-6 = 1 + the sync rate, 0 = the track's): what a project holds keeps its resolution."""
    global RATEFLIP
    assert RATE
    RATEFLIP = True


def use_recoff():
    """SC43.2 (the user, 2026-10-16: «al grabar un patrón con arpegiador de 32 pasos, sólo se aplica el arpegiador a la página donde se pulsó
    grabar … grabar una segunda vez … sí que aplica el arpegiador, pero solo a las notas nuevas»): the second and later notes of a chord go to
    the recorder's note-on gate by us (0x0802E56A), but their note-off took the stock's path, which never reached the recorder (the stock's
    router only knows the notes it routed): the recorder kept them held (its list at [recorder + 0x54], 12 B a note, flag byte 3 = released)
    and ignored the same notes played again until Record was pressed again, so later chords were recorded as their first note alone and
    the arpeggiator saw no chord.  Now letting go of such a note also calls the recorder's note-off gate (0x0802E5CC(rec, note, track));
    letting go of the first note (the stock's) clears the state's first note, so a note pressed again while others are held is ours."""
    global RECOFF
    RECOFF = True




def use_cols2():
    """SC42.5 (the user, 2026-10-16: «arpeggiator parameters keep their pattern settings color (selection still green like now)»): with Shift held,
    pad 25, the order pads and the resolution pads keep the colours Pattern Settings gives them; only the chosen ones (and pad 25 when on) green."""
    global COLS2
    COLS2 = True


def use_gatecap():
    """SC42.5 (the user, 2026-10-16: «arpeggiator doesn't work anymore»): with every note lasting its own gate, a chord recorded by holding its
    notes sustained all of them to its end (a strum, not an arpeggio): a note now lasts its gate, at most one arpeggio step."""
    global GATECAP
    assert RATE
    GATECAP = True


def use_rate():
    """SC42.3 (the user, 2026-10-16: «arpeggiator: shift + clock resolution: set arpeggiator resolution (distinct from track tempo)»; «the time you keep
    the pad held becomes the gate length», also for the arpeggiated notes): bits 3-6 of the setting = the resolution (0 = the track's sync rate,
    1..8 = the sync rates 1/32T .. 1/4), set with Shift + pads 17-24 of Pattern Settings (the chosen one again: back to the track's); the arpeggio
    advances on an accumulator of sixths of a tick (the micro step adds the track's ticks a step, an arpeggio step takes 6 x its ticks); a note of
    the sequence's chord lasts its own gate (at most what is left of the chord) instead of a step; the input's notes last an arpeggio step."""
    global RATE
    RATE = True
# a running state: 0 n, 1 c (micro steps since the chord), 2 len, 3 k, 4 fractal group, 5 fractal place, 6..11 notes, 12..17 velocities,
# 18 the chord's micro step, 19 flags (bit 0 running, bit 1 a note on by hand), 20 the first note to stop (0xFF none), 21 the last note,
# 22 the micro step within the step (0..5), 23 the first note held, 24..27 the next time (ms; the input, stopped)
S_N, S_C, S_LEN, S_K, S_FG, S_FP, S_NOTES, S_VELS, S_M, S_FL, S_PEND, S_LAST, S_SUB, S_FIRST, S_NEXT = range(0, 15)
S_NOTES, S_VELS, S_M, S_FL, S_PEND, S_LAST, S_SUB, S_FIRST, S_NEXT = 6, 12, 18, 19, 20, 21, 22, 23, 24


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w_(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
def ldr_w_(rt, rn, off): return h(0xF8D0 | rn) + h(rt << 12 | off)
def str_w_(rt, rn, off): return h(0xF8C0 | rn) + h(rt << 12 | off)
def mls_(rd, rn, rm, ra): return h(0xFB00 | rn) + h(ra << 12 | rd << 8 | 0x10 | rm)      # rd = ra - rn * rm


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    t_ord = base; E(raw, bytes(ORD_OF_PAD) + bytes([PS_PAD_ORD + ORD_OF_PAD.index(m) for m in range(6)]))   # mode of a pad; pad of a mode

    # ---- c_artail() -> r0 = the record's tail, or 0; clobbers r1
    a.label("c_artail")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "at_x", "eq")
    imm32(1, TAIL); E(adds_reg, 0, 0, 1)
    a.label("at_x"); E(raw, h(0x4770))

    # ---- c_arsum(r0 = the block) -> r1 = the checksum of its 32 bytes; clobbers r2, r3
    a.label("c_arsum")
    E(movs_imm, 1, SUMX); E(movs_imm, 2, 0)
    a.label("su_l"); E(adds_imm8, 2, 5); E(ldrb_reg, 3, 0, 2); E(subs_imm8, 2, 5); E(adds_reg, 1, 1, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 32); E(b_cond, "su_l", "lo")
    E(raw, h(0xB2C9)); E(raw, h(0x4770))                                                # uxtb r1, r1

    # ---- c_arblk() -> r0 = the setting block if it is ours, or 0; clobbers r1-r3
    a.label("c_arblk")
    E(push_list, [4], lr=True)
    E(bl, "c_artail"); E(cmp_imm, 0, 0); E(b_cond, "bk_x", "eq"); imm32(1, O_BLK); E(adds_reg, 0, 0, 1)
    E(mov_reg, 4, 0); E(ldr_imm, 1, 4, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "bk_0", "ne")
    E(mov_reg, 0, 4); E(bl, "c_arsum"); E(ldrb_imm, 2, 4, 4); E(cmp_reg, 1, 2); E(b_cond, "bk_0", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("bk_0"); E(movs_imm, 0, 0)
    a.label("bk_x"); E(pop_list, [4], pc=True)

    # ---- c_arcfg(r0 = track, r1 = pattern) -> r0 = its setting (0: off); clobbers r1-r3
    a.label("c_arcfg")
    E(push_list, [4], lr=True)
    E(cmp_imm, 0, 3); E(b_cond, "cf_0", "hi"); E(cmp_imm, 1, 7); E(b_cond, "cf_0", "hi")
    E(lsls_imm, 4, 0, 3); E(adds_reg, 4, 4, 1)
    E(bl, "c_arblk"); E(cmp_imm, 0, 0); E(b_cond, "cf_x", "eq")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 5); E(pop_list, [4], pc=True)
    a.label("cf_0"); E(movs_imm, 0, 0)
    a.label("cf_x"); E(pop_list, [4], pc=True)

    # ---- c_arset(r0 = track, r1 = pattern, r2 = setting): the block made if missing, the byte, the checksum
    a.label("c_arset")
    E(push_list, [4, 5, 6], lr=True)
    E(lsls_imm, 4, 0, 3); E(adds_reg, 4, 4, 1); E(mov_reg, 5, 2)
    E(bl, "c_arblk"); E(cmp_imm, 0, 0); E(b_cond, "se_w", "ne")
    E(bl, "c_artail"); E(cmp_imm, 0, 0); E(b_cond, "se_x", "eq"); imm32(1, O_BLK); E(adds_reg, 0, 0, 1)
    imm32(1, SIG); E(raw, h(0x6001))                                                    # str r1, [r0]
    E(movs_imm, 1, 0); E(movs_imm, 2, 37)
    a.label("se_z"); E(subs_imm8, 2, 1); E(strb_reg, 1, 0, 2); E(cmp_imm, 2, 5); E(b_cond, "se_z", "hi")
    a.label("se_w"); E(mov_reg, 6, 0); E(adds_reg, 0, 0, 4); E(strb_imm, 5, 0, 5)
    E(mov_reg, 0, 6); E(bl, "c_arsum"); E(strb_imm, 1, 6, 4)
    a.label("se_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_arst(r0 = track, r1 = 0 sequence / 1 input) -> r0 = its running state, or 0; clobbers r1-r3
    a.label("c_arst")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(cmp_imm, 4, 3); E(b_cond, "sa_0", "hi")
    E(bl, "c_artail"); E(cmp_imm, 0, 0); E(b_cond, "sa_x", "eq")
    E(movs_imm, 1, ST_SZ); E(muls, 1, 4); E(adds_reg, 0, 0, 1); imm32(1, O_SEQ)
    E(cmp_imm, 5, 0); E(b_cond, "sa_a", "eq"); imm32(1, O_LIVE)
    a.label("sa_a"); E(adds_reg, 0, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("sa_0"); E(movs_imm, 0, 0)
    a.label("sa_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_artrk(r0 = a player) -> r0 = its track 0..3, or 0xFF; clobbers r1, r2
    a.label("c_artrk")
    imm32(1, PLAYER0); E(movs_imm, 2, 0)
    a.label("tk_l"); E(cmp_reg, 0, 1); E(b_cond, "tk_f", "eq"); imm32(3, PLAYER_SZ); E(adds_reg, 1, 1, 3)
    E(adds_imm8, 2, 1); E(cmp_imm, 2, 4); E(b_cond, "tk_l", "lo"); E(movs_imm, 2, 0xFF)
    a.label("tk_f"); E(mov_reg, 0, 2); E(raw, h(0x4770))

    # ---- c_arply(r0 = track) -> r0 = its player; clobbers r1
    a.label("c_arply")
    imm32(1, PLAYER_SZ); E(muls, 0, 1); imm32(1, PLAYER0); E(adds_reg, 0, 0, 1); E(raw, h(0x4770))

    # ---- c_arpat(r0 = track) -> r0 = the pattern it plays; clobbers r1-r3
    a.label("c_arpat")
    E(push_list, [4], lr=True)
    E(lsls_imm, 0, 0, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(pop_list, [4], pc=True)

    # ---- c_artps(r0 = a player) -> r0 = its ticks a step; clobbers r1-r3
    a.label("c_artps")
    E(push_list, [4], lr=True)
    E(ldr_imm, 0, 0, 0x10); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 7); E(b_cond, "tp_a", "ls"); E(movs_imm, 0, 7)
    a.label("tp_a"); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0)
    E(pop_list, [4], pc=True)

    if RATE:
        # ---- c_arRt(r0 = track) -> r0 = the ticks of an arpeggio step (the setting's resolution, or the track's sync rate); clobbers r1-r3
        a.label("c_arRt")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_arpat"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_arcfg")
        E(lsrs_imm, 0, 0, 3); E(movs_imm, 1, 15); E(raw, h(0x4008)); E(cmp_imm, 0, 0); E(b_cond, "rt_f", "eq")      # ands r0, r1
        E(cmp_imm, 0, 8); E(b_cond, "rt_f", "hi")
        E(subs_imm8, 0, 1); E(lsls_imm, 0, 0, 2); imm32(1, TICKS_TAB); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(pop_list, [4], pc=True)
        a.label("rt_f"); E(mov_reg, 0, 4); E(bl, "c_arply"); E(bl, "c_artps"); E(pop_list, [4], pc=True)
        # ---- c_arRp(r0 = a player) -> r0 = the ticks of its arpeggio step; clobbers r1-r3
        a.label("c_arRp")
        E(push_list, [4], lr=True)
        E(mov_reg, 4, 0); E(bl, "c_artrk"); E(cmp_imm, 0, 3); E(b_cond, "rp_s", "hi"); E(bl, "c_arRt"); E(pop_list, [4], pc=True)
        a.label("rp_s"); E(mov_reg, 0, 4); E(bl, "c_artps"); E(pop_list, [4], pc=True)

    if PRESSORD:
        # ---- c_arins(r0 = state, r1 = note, r2 = velocity, r3 = the gate): a note there: its velocity / gate; else the lowest free place
        a.label("c_arins")
        E(push_list, [3, 4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 0); E(ldrb_imm, 5, 4, S_N); E(movs_imm, 3, 0)
        a.label("ip_f"); E(cmp_reg, 3, 5); E(b_cond, "ip_n", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_NOTES); E(cmp_reg, 6, 1); E(b_cond, "ip_u", "eq")
        E(adds_imm8, 3, 1); E(b, "ip_f")
        a.label("ip_u"); E(strb_imm, 2, 0, S_VELS); E(ldr_sp, 6, 0); E(raw, strb_w_(6, 0, D_EXT)); E(b, "ip_x")
        a.label("ip_n"); E(cmp_imm, 5, 6); E(b_cond, "ip_x", "hs"); E(movs_imm, 3, 0)
        a.label("ip_p"); E(cmp_reg, 3, 5); E(b_cond, "ip_s", "hs"); E(adds_reg, 0, 4, 3); E(raw, ldrb_w_(6, 0, D_POS)); E(cmp_reg, 6, 3); E(b_cond, "ip_s", "ne")
        E(adds_imm8, 3, 1); E(b, "ip_p")
        a.label("ip_s"); E(mov_reg, 7, 5)                                                  # r3 = the place = the index; move up the ones from there
        a.label("ip_m"); E(cmp_reg, 7, 3); E(b_cond, "ip_w", "ls")
        E(adds_reg, 0, 4, 7); E(subs_imm8, 0, 1); E(ldrb_imm, 6, 0, S_NOTES); E(strb_imm, 6, 0, S_NOTES + 1)
        E(ldrb_imm, 6, 0, S_VELS); E(strb_imm, 6, 0, S_VELS + 1)
        E(raw, ldrb_w_(6, 0, D_EXT)); E(raw, strb_w_(6, 0, D_EXT + 1)); E(raw, ldrb_w_(6, 0, D_POS)); E(raw, strb_w_(6, 0, D_POS + 1))
        E(subs_imm8, 7, 1); E(b, "ip_m")
        a.label("ip_w"); E(adds_reg, 0, 4, 3); E(strb_imm, 1, 0, S_NOTES); E(strb_imm, 2, 0, S_VELS)
        E(ldr_sp, 6, 0); E(raw, strb_w_(6, 0, D_EXT)); E(raw, strb_w_(3, 0, D_POS))
        E(adds_imm8, 5, 1); E(strb_imm, 5, 4, S_N)
        a.label("ip_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_arins(r0 = state, r1 = note, r2 = velocity): into the sorted list (a note there: its velocity); at most 6
    a.label("c_arins" if not PRESSORD else "c_arins_old")
    E(push_list, [3, 4, 5, 6, 7] if RATE else [4, 5, 6, 7], lr=True)                  # (RATE: [sp] = the gate)
    E(mov_reg, 4, 0); E(ldrb_imm, 5, 4, S_N); E(movs_imm, 3, 0)
    a.label("in_f"); E(cmp_reg, 3, 5); E(b_cond, "in_p", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_NOTES)
    E(cmp_reg, 6, 1); E(b_cond, "in_p", "hs"); E(adds_imm8, 3, 1); E(b, "in_f")
    a.label("in_p")                                                                    # r3 = the place
    E(cmp_reg, 3, 5); E(b_cond, "in_n", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_NOTES); E(cmp_reg, 6, 1); E(b_cond, "in_n", "ne")
    E(strb_imm, 2, 0, S_VELS)
    if RATE: E(ldr_sp, 6, 0); E(raw, strb_w_(6, 0, D_EXT))
    E(b, "in_x")
    a.label("in_n"); E(cmp_imm, 5, 6); E(b_cond, "in_x", "hs")
    E(mov_reg, 7, 5)
    a.label("in_s"); E(cmp_reg, 7, 3); E(b_cond, "in_w", "ls")                          # move up the ones above
    E(adds_reg, 0, 4, 7); E(subs_imm8, 0, 1); E(ldrb_imm, 6, 0, S_NOTES); E(strb_imm, 6, 0, S_NOTES + 1)
    E(ldrb_imm, 6, 0, S_VELS); E(strb_imm, 6, 0, S_VELS + 1)
    if RATE: E(raw, ldrb_w_(6, 0, D_EXT)); E(raw, strb_w_(6, 0, D_EXT + 1))
    E(subs_imm8, 7, 1); E(b, "in_s")
    a.label("in_w"); E(adds_reg, 0, 4, 3); E(strb_imm, 1, 0, S_NOTES); E(strb_imm, 2, 0, S_VELS)
    if RATE: E(ldr_sp, 6, 0); E(raw, strb_w_(6, 0, D_EXT))
    E(adds_imm8, 5, 1); E(strb_imm, 5, 4, S_N)
    a.label("in_x"); E(pop_list, [3, 4, 5, 6, 7] if RATE else [4, 5, 6, 7], pc=True)

    # ---- c_ardel(r0 = state, r1 = note): out of the list
    a.label("c_ardel")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(ldrb_imm, 5, 4, S_N); E(movs_imm, 3, 0)
    a.label("de_f"); E(cmp_reg, 3, 5); E(b_cond, "de_x", "hs"); E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_NOTES); E(cmp_reg, 6, 1); E(b_cond, "de_m", "eq")
    E(adds_imm8, 3, 1); E(b, "de_f")
    a.label("de_m"); E(subs_imm8, 5, 1); E(strb_imm, 5, 4, S_N)
    a.label("de_s"); E(cmp_reg, 3, 5); E(b_cond, "de_x", "hs")
    E(adds_reg, 0, 4, 3); E(ldrb_imm, 6, 0, S_NOTES + 1); E(strb_imm, 6, 0, S_NOTES); E(ldrb_imm, 6, 0, S_VELS + 1); E(strb_imm, 6, 0, S_VELS)
    if RATE: E(raw, ldrb_w_(6, 0, D_EXT + 1)); E(raw, strb_w_(6, 0, D_EXT))
    if PRESSORD: E(raw, ldrb_w_(6, 0, D_POS + 1)); E(raw, strb_w_(6, 0, D_POS))
    E(adds_imm8, 3, 1); E(b, "de_s")
    a.label("de_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_armod(r0, r1) -> r0 = r0 mod r1 (r1 > 0); clobbers r2
    a.label("c_armod")
    E(raw, udiv(2, 0, 1)); E(raw, mls_(0, 2, 1, 0)); E(raw, h(0x4770))

    # ---- c_arord(r0 = state, r1 = the order) -> r0 = the place of the next note; the state moves on
    a.label("c_arord")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(ldrb_imm, 6, 4, S_N); E(ldrb_imm, 7, 4, S_K)
    E(cmp_imm, 6, 0); E(b_cond, "or_0", "eq")
    E(cmp_imm, 5, M_FRAC); E(b_cond, "or_fr", "eq")
    E(cmp_imm, 5, M_RND); E(b_cond, "or_rn", "eq")
    E(mov_reg, 0, 7); E(mov_reg, 1, 6)
    E(cmp_imm, 5, M_PP); E(b_cond, "or_pp", "eq")
    E(bl, "c_armod")                                                                   # r0 = k mod n
    E(cmp_imm, 5, M_DOWN); E(b_cond, "or_dn", "eq")
    E(cmp_imm, 5, M_DEC); E(b_cond, "or_k", "ne")
    E(mov_reg, 2, 6); E(adds_imm8, 2, 1); E(lsrs_imm, 2, 2, 1); E(cmp_reg, 0, 2); E(b_cond, "or_de", "hs")    # deconstructed: the even places, then the odd ones
    E(lsls_imm, 0, 0, 1); E(b, "or_k")
    a.label("or_de"); E(subs_reg, 0, 0, 2); E(lsls_imm, 0, 0, 1); E(adds_imm8, 0, 1); E(b, "or_k")
    a.label("or_dn"); E(subs_reg, 0, 6, 0); E(subs_imm8, 0, 1); E(b, "or_k")
    a.label("or_pp")                                                                   # ping-pong: 0 .. n-1 .. 1
    E(cmp_imm, 6, 1); E(b_cond, "or_0", "ls")
    E(lsls_imm, 1, 6, 1); E(subs_imm8, 1, 2); E(bl, "c_armod"); E(cmp_reg, 0, 6); E(b_cond, "or_k", "lo")
    E(lsls_imm, 1, 6, 1); E(subs_imm8, 1, 2); E(subs_reg, 0, 1, 0); E(b, "or_k")
    a.label("or_rn"); E(bl, RANDOM); E(mov_reg, 1, 6); E(bl, "c_armod"); E(b, "or_k")
    a.label("or_fr")                                                                   # fractal: 0 · 0 1 · 0 1 2 · ...
    E(ldrb_imm, 0, 4, S_FP); E(ldrb_imm, 1, 4, S_FG)
    E(cmp_reg, 1, 6); E(b_cond, "or_f1", "lo"); E(movs_imm, 1, 0); E(movs_imm, 0, 0)
    a.label("or_f1"); E(cmp_reg, 0, 1); E(b_cond, "or_f2", "ls"); E(movs_imm, 0, 0)
    a.label("or_f2"); E(mov_reg, 2, 0)
    E(adds_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "or_f3", "ls")
    E(movs_imm, 2, 0); E(adds_imm8, 1, 1); E(cmp_reg, 1, 6); E(b_cond, "or_f3", "lo"); E(movs_imm, 1, 0)
    a.label("or_f3"); E(strb_imm, 2, 4, S_FP); E(strb_imm, 1, 4, S_FG)
    a.label("or_k")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, KWRAP); E(b_cond, "or_w", "lo"); E(movs_imm, 7, 0)
    a.label("or_w"); E(strb_imm, 7, 4, S_K)
    E(cmp_reg, 0, 6); E(b_cond, "or_x", "lo")
    a.label("or_0"); E(movs_imm, 0, 0)
    a.label("or_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arnote(r0 = player, r1 = note, r2 = velocity, r3 = ticks): the stock's note-on (a live same note freed first)
    a.label("c_arnote")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(mov_reg, 7, 3)
    E(bl, BATCH_ON)
    E(adds_reg, 0, 4, 5); E(raw, ldrb_w_(1, 0, 0x9B)); E(cmp_imm, 1, 0xFF); E(b_cond, "no_a", "eq")
    E(mov_reg, 0, 4); E(bl, REL_ENTRY)
    a.label("no_a")
    E(movs_imm, 0, 0); E(str_sp, 0, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(mov_reg, 3, 7); E(bl, NOTE_ON)
    E(bl, BATCH_OFF)
    E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arifon / c_arifoff (r0 = player, r1 = note, r2 = velocity): note on / off through the player's note interface, by hand
    a.label("c_arifon")
    E(push_list, [4], lr=True); E(ldr_imm, 0, 0, 0x4C); E(movs_imm, 3, 0); E(ldr_imm, 4, 0, 0); E(ldr_imm, 4, 4, 0); E(raw, h(0x47A0))   # blx r4
    E(pop_list, [4], pc=True)
    a.label("c_arifoff")
    E(push_list, [4], lr=True); E(ldr_imm, 0, 0, 0x4C); E(movs_imm, 2, 0); E(ldr_imm, 4, 0, 0); E(ldr_imm, 4, 4, 4); E(raw, h(0x47A0))
    E(pop_list, [4], pc=True)

    if VIEWOFF:
        # ---- c_arvoff(r0 = player, r1 = note): note off through the note interface of its track's view
        a.label("c_arvoff")
        E(push_list, [4, 5], lr=True); E(mov_reg, 5, 1); E(bl, "c_artrk"); E(cmp_imm, 0, 3); E(b_cond, "vf_x", "hi")
        imm32(1, VIEW_SZ); E(muls, 0, 1); imm32(1, VIEW_IFC0 - 0x110); E(adds_reg, 0, 0, 1)                 # r0 = the view
        E(adds_reg, 2, 0, 5); E(raw, ldrb_w_(2, 2, 0x80))                                                  # r2 = the note's pad ([view + 0x80 + note])
        imm32(1, 0x110); E(adds_reg, 0, 0, 1)                                                              # its interface: (obj, note, pad)
        E(mov_reg, 1, 5); E(ldr_imm, 4, 0, 0); E(ldr_imm, 4, 4, 4); E(raw, h(0x47A0))                       # blx r4
        a.label("vf_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_arnext(r0 = state, r1 = order, r2 = player, r3 = 1: through the stock's note-on (ticks in [sp]), 0: by hand)
    #      a note by hand still on and the first note held are stopped; then the next note of the order
    a.label("c_arnext")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(str_sp, 3, 0)
    E(ldrb_imm, 1, 4, S_PEND); E(cmp_imm, 1, 0xFF); E(b_cond, "nx_m", "eq")
    E(mov_reg, 0, 6); E(bl, "c_arvoff" if VIEWOFF else "c_arifoff"); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S_PEND)
    a.label("nx_m")
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 30); E(b_cond, "nx_n", "pl")
    E(ldrb_imm, 1, 4, S_LAST); E(mov_reg, 0, 6); E(bl, "c_arifoff")
    E(ldrb_imm, 0, 4, S_FL); E(movs_imm, 1, 2); E(raw, h(0x4388)); E(strb_imm, 0, 4, S_FL)     # bics r0, r1
    a.label("nx_n")
    E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); E(b_cond, "nx_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arord")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 7, 0, S_NOTES); E(ldrb_imm, 5, 0, S_VELS)
    if MUTLIVE: E(mov_reg, 0, 6); E(mov_reg, 1, 7); E(bl, "c_armutL"); E(mov_reg, 7, 1)          # the input's note: the track's step's mutate level
    E(strb_imm, 7, 4, S_LAST)
    E(ldr_sp, 3, 0); E(cmp_imm, 3, 0); E(b_cond, "nx_h", "eq")
    E(mov_reg, 0, 6); E(bl, "c_arRp" if RATE else "c_artps"); E(mov_reg, 3, 0)
    E(mov_reg, 0, 6); E(mov_reg, 1, 7); E(mov_reg, 2, 5); E(bl, "c_arnote"); E(b, "nx_x")
    a.label("nx_h")
    E(mov_reg, 0, 6); E(mov_reg, 1, 7); E(mov_reg, 2, 5); E(bl, "c_arifon")
    E(ldrb_imm, 0, 4, S_FL); E(movs_imm, 1, 2); E(raw, h(0x4308)); E(strb_imm, 0, 4, S_FL)     # orrs r0, r1
    a.label("nx_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arlstep(r0 = track, r1 = 1 playing / 0 stopped): one step of the input's arpeggio
    a.label("c_arlstep")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0); E(mov_reg, 6, 1)
    E(movs_imm, 1, 1); E(bl, "c_arst"); E(cmp_imm, 0, 0); E(b_cond, "ls_x", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "ls_x", "pl")
    E(mov_reg, 0, 7); E(bl, "c_arpat"); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(bl, "c_arcfg"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 7); E(bl, "c_arply"); E(mov_reg, 2, 0)
    E(lsls_imm, 1, 5, 24); E(b_cond, "ls_off", "pl")                                    # the setting went off: the arpeggio ends
    E(movs_imm, 1, 7); E(raw, h(0x4029)); E(mov_reg, 0, 4); E(mov_reg, 3, 6); E(bl, "c_arnext")   # ands r1, r5
    E(b, "ls_x")
    a.label("ls_off")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(strb_imm, 1, 0, S_N); E(movs_imm, 1, 0); E(mov_reg, 3, 1); E(bl, "c_arnext")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, S_FL)
    a.label("ls_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arplay (the players' slot 2: this, pattern, step, micro step)
    zc = [0]
    INVC = {"eq": "ne", "ne": "eq", "hi": "ls", "ls": "hi", "lo": "hs", "hs": "lo", "pl": "mi", "mi": "pl"}
    def bcs(target, cond):                                                             # (RATE: the target can be far)
        if not RATE: E(b_cond, target, cond); return
        zc[0] += 1; n_ = f"_ps{zc[0]}"; E(b_cond, n_, INVC[cond]); E(b, target); a.label(n_)

    if MUTARP:
        # ---- c_armut(r1 = a note; r6 = the sequence state) -> r1 = the note through the chord step's mutate level (mutate39's chances)
        import mutate39 as MU
        a.label("c_armut")
        E(push_list, [0, 2, 3, 4, 5, 6, 7], lr=True)
        if not MUTLIVE: E(raw, ldrb_w_(7, 6, D_MUT)); E(cmp_imm, 7, 0); E(b_cond, "mu_x", "eq"); E(mov_reg, 5, 1)
        else:
            E(raw, ldrb_w_(7, 6, D_MUT)); E(b, "mu_k")
            # ---- c_armutk(r0 = a level, r1 = a note) -> r1 = the note through that level
            a.label("c_armutk")
            E(push_list, [0, 2, 3, 4, 5, 6, 7], lr=True); E(mov_reg, 7, 0)
            a.label("mu_k"); E(movs_imm, 0, 7); E(raw, h(0x4007)); E(cmp_imm, 7, 0); E(b_cond, "mu_x", "eq"); E(mov_reg, 5, 1)   # ands r7, r0
        E(bl, RANDOM); E(lsrs_imm, 6, 0, 6)                                                # r6 = 24 random bits
        E(movw, 0, MU.CHANCE[0] | MU.CHANCE[1] << 8); E(movt, 0, MU.CHANCE[2] | MU.CHANCE[3] << 8)
        E(cmp_imm, 7, 4); E(b_cond, "mu_c", "lo")
        E(movw, 0, MU.CHANCE[4] | MU.CHANCE[5] << 8); E(movt, 0, MU.CHANCE[6] | MU.CHANCE[7] << 8)
        a.label("mu_c")
        E(movs_imm, 1, 3); E(raw, h(0x4039)); E(lsls_imm, 1, 1, 3); E(raw, h(0x40C8)); E(movs_imm, 1, 0xFF); E(raw, h(0x4008)); E(mov_reg, 7, 0)   # ands r1, r7; lsrs r0, r1; ands r0, r1
        E(lsrs_imm, 0, 7, 4); E(movs_imm, 1, 15); E(raw, h(0x4031)); E(lsrs_imm, 6, 6, 4); E(cmp_reg, 1, 0); E(b_cond, "mu_o", "hs")      # ands r1, r6
        E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, L["c_mutscale"]); E(mov_reg, 5, 0); E(lsrs_imm, 6, 6, 8)
        a.label("mu_o")
        E(movs_imm, 0, 15); E(raw, h(0x4038)); E(movs_imm, 1, 15); E(raw, h(0x4031)); E(lsrs_imm, 6, 6, 4); E(cmp_reg, 1, 0); E(b_cond, "mu_e", "hs")   # ands r0, r7; ands r1, r6
        E(lsls_imm, 0, 6, 31); E(b_cond, "mu_d", "mi")
        E(adds_imm8, 5, 12); E(cmp_imm, 5, 127); E(b_cond, "mu_e", "ls"); E(subs_imm8, 5, 24); E(b, "mu_e")
        a.label("mu_d"); E(subs_imm8, 5, 12); E(b_cond, "mu_e", "pl"); E(adds_imm8, 5, 24)
        a.label("mu_e"); E(mov_reg, 1, 5)
        a.label("mu_x"); E(pop_list, [0, 2, 3, 4, 5, 6, 7], pc=True)
        if MUTLIVE:
            # ---- c_armutL(r0 = a player, r1 = a note) -> r1 = the note through the level of the step its track is on; clobbers r0
            a.label("c_armutL")
            E(push_list, [2, 3, 4, 5, 6, 7], lr=True)
            E(mov_reg, 4, 1); E(bl, "c_artrk"); E(cmp_imm, 0, 3); E(b_cond, "ml_x", "hi"); E(mov_reg, 5, 0)
            E(bl, "c_arpat"); E(mov_reg, 6, 0)                                                 # r6 = the pattern
            E(lsls_imm, 0, 5, 2); imm32(1, ENG + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 1); E(bl, PARAM_GET)
            E(ldrb_imm, 7, 0, 0); E(cmp_imm, 7, 31); E(b_cond, "ml_x", "hi")                    # r7 = the step
            E(mov_reg, 0, 5); E(bl, "c_arply"); E(ldr_imm, 0, 0, 0x48); imm32(1, 0xCA8); E(muls, 1, 6); E(adds_reg, 0, 0, 1)
            E(movs_imm, 1, 28); E(muls, 1, 7); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, 2)      # the step's byte [2]
            E(mov_reg, 1, 4); E(bl, "c_armutk"); E(pop_list, [2, 3, 4, 5, 6, 7], pc=True)
            a.label("ml_x"); E(mov_reg, 1, 4); E(pop_list, [2, 3, 4, 5, 6, 7], pc=True)

    a.label("c_arplay")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 16)
    E(str_sp, 0, 0); E(str_sp, 1, 4); E(str_sp, 2, 8); E(str_sp, 3, 12)
    E(bl, "c_artrk"); E(mov_reg, 7, 0); E(cmp_imm, 0, 3); bcs("py_s", "hi")
    E(movs_imm, 1, 0); E(bl, "c_arst"); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); bcs("py_s", "eq")
    E(ldr_sp, 1, 4); E(mov_reg, 0, 7); E(bl, "c_arcfg"); E(mov_reg, 5, 0)
    E(lsls_imm, 0, 5, 24); E(b_cond, "py_on", "mi")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, S_FL); E(b, "py_s")                           # off: nothing of ours
    a.label("py_on")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 12); E(adds_reg, 4, 0, 1)                             # r4 + 0x13C = this micro step's mask
    E(ldrb_imm, 0, 6, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "py_n", "pl")
    E(ldrb_imm, 1, 6, S_C); E(ldrb_imm, 2, 6, S_M); E(movs_imm, 3, 6); E(subs_reg, 3, 3, 2); E(cmp_reg, 1, 3); E(b_cond, "py_n", "hs")
    E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, 0x13C)); E(b, "py_s")                         # the rest of the chord's step: ours
    a.label("py_n")
    E(raw, ldrb_w_(0, 4, 0x13C)); E(cmp_imm, 0, 0); bcs("py_s", "eq")
    # the step: [this + 0x48] + 0xCA8 pattern + 28 step; its units from this micro step on
    E(ldr_sp, 0, 0); E(ldr_imm, 3, 0, 0x48); imm32(0, 0xCA8); E(ldr_sp, 1, 4); E(muls, 0, 1); E(adds_reg, 3, 3, 0)
    E(ldr_sp, 1, 8); E(movs_imm, 0, 28); E(muls, 0, 1); E(adds_reg, 3, 3, 0)               # r3 = the step
    E(movs_imm, 0, 0); E(movs_imm, 2, 0)                                                # r0 = unit, r2 = how many
    a.label("py_c"); E(ldrb_imm, 1, 3, 0)
    E(raw, h(0x40C1))                                                                  # lsrs r1, r0
    E(lsls_imm, 1, 1, 31); E(b_cond, "py_cn", "pl")
    E(lsls_imm, 1, 0, 2); E(adds_reg, 1, 1, 3); E(ldrb_imm, 1, 1, 6); E(ldr_sp, 4, 12); E(cmp_reg, 1, 4); E(b_cond, "py_cn", "lo")
    E(adds_imm8, 2, 1)
    a.label("py_cn"); E(adds_imm8, 0, 1); E(cmp_imm, 0, 6); E(b_cond, "py_c", "lo")
    E(cmp_imm, 2, 2); bcs("py_s", "lo")
    # a chord: the units into the state, the stock's mask empty
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, S_N); E(strb_imm, 0, 6, S_C); E(strb_imm, 0, 6, S_K); E(strb_imm, 0, 6, S_FG); E(strb_imm, 0, 6, S_FP)
    E(strb_imm, 0, 6, S_SUB); E(strb_imm, 0, 6, S_LEN); E(movs_imm, 0, 1); E(strb_imm, 0, 6, S_FL); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, S_PEND)
    E(ldr_sp, 0, 12); E(strb_imm, 0, 6, S_M)
    if MUTARP: E(ldrb_imm, 0, 3, 2); E(movs_imm, 1, 7); E(raw, h(0x4008)); E(raw, strb_w_(0, 6, D_MUT))      # ands r0, r1: the step's level
    E(movs_imm, 4, 0)
    a.label("py_u")
    E(ldrb_imm, 1, 3, 0); E(mov_reg, 0, 4); E(raw, h(0x40C1)); E(lsls_imm, 1, 1, 31); E(b_cond, "py_un", "pl")      # lsrs r1, r0
    E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 0, 3); E(ldrb_imm, 1, 0, 6); E(ldr_sp, 2, 12); E(cmp_reg, 1, 2); E(b_cond, "py_un", "lo")
    E(ldrb_imm, 1, 0, 5); E(lsls_imm, 1, 1, 25); E(lsrs_imm, 1, 1, 25); E(cmp_imm, 1, 0); E(b_cond, "py_l1", "ne"); E(movs_imm, 1, 1)
    a.label("py_l1"); E(ldrb_imm, 2, 6, S_LEN); E(cmp_reg, 1, 2); E(b_cond, "py_l2", "ls"); E(strb_imm, 1, 6, S_LEN)
    a.label("py_l2")
    E(push_list, [3])
    if RATE: E(ldrb_imm, 3, 0, 5); E(lsls_imm, 3, 3, 25); E(lsrs_imm, 3, 3, 25)                        # its gate (micro steps)
    E(ldrb_imm, 1, 0, 4); E(ldrb_imm, 2, 0, 7); E(mov_reg, 0, 6); E(bl, "c_arins"); E(pop_list, [3])
    a.label("py_un"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 6); E(b_cond, "py_u", "lo")
    if RATE:                                                                           # the first note on this micro step
        E(mov_reg, 0, 7); E(bl, "c_arRt"); E(movs_imm, 1, 6); E(muls, 0, 1); E(raw, strb_w_(0, 6, D_EXT + 6))
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 12); E(adds_reg, 4, 0, 1); E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, 0x13C))
    a.label("py_s")
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(ldr_sp, 3, 12); E(bl, PLAY_STOCK)
    E(cmp_imm, 7, 3); E(b_cond, "py_x", "hi")
    E(cmp_imm, 6, 0); E(b_cond, "py_l", "eq")
    E(ldrb_imm, 0, 6, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "py_l", "pl")
    if not RATE:
        E(ldrb_imm, 0, 6, S_SUB); E(cmp_imm, 0, 0); E(b_cond, "py_t", "ne")
        # a note of the chord: a step long, or what is left of the chord
        E(mov_reg, 0, 6); E(movs_imm, 1, 7); E(raw, h(0x4029)); E(bl, "c_arord")               # ands r1, r5
        E(adds_reg, 0, 0, 6); E(ldrb_imm, 1, 0, S_NOTES); E(ldrb_imm, 2, 0, S_VELS); E(push_list, [1, 2])
        E(ldr_sp, 0, 8); E(bl, "c_artps"); E(mov_reg, 4, 0)                                   # ([sp] moved by the push: this at sp + 8)
        E(ldrb_imm, 0, 6, S_LEN); E(ldrb_imm, 1, 6, S_C); E(subs_reg, 0, 0, 1); E(cmp_imm, 0, 6); E(b_cond, "py_d", "ls"); E(movs_imm, 0, 6)
        a.label("py_d"); E(muls, 0, 4); E(movs_imm, 1, 6); E(raw, udiv(3, 0, 1)); E(cmp_imm, 3, 0); E(b_cond, "py_e", "ne"); E(movs_imm, 3, 1)
        a.label("py_e"); E(pop_list, [1, 2]); E(ldr_sp, 0, 0); E(bl, "c_arnote")
        a.label("py_t")
        E(ldrb_imm, 0, 6, S_SUB); E(adds_imm8, 0, 1); E(cmp_imm, 0, 6); E(b_cond, "py_t2", "lo"); E(movs_imm, 0, 0)
        a.label("py_t2"); E(strb_imm, 0, 6, S_SUB)
        E(ldrb_imm, 0, 6, S_C); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, S_C); E(ldrb_imm, 1, 6, S_LEN); E(cmp_reg, 0, 1); E(b_cond, "py_l", "lo")
        E(movs_imm, 0, 0); E(strb_imm, 0, 6, S_FL)
        a.label("py_l")                                                                    # the input's arpeggio on micro step 0
        E(ldr_sp, 0, 12); E(cmp_imm, 0, 0); E(b_cond, "py_x", "ne")
        E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arlstep")
    else:
        E(mov_reg, 0, 7); E(bl, "c_arRt"); E(movs_imm, 1, 6); E(muls, 0, 1); E(mov_reg, 4, 0)            # r4 = 6 x the arpeggio step
        E(raw, ldrb_w_(0, 6, D_EXT + 6)); E(cmp_reg, 0, 4); E(b_cond, "py_t", "lo")
        E(subs_reg, 0, 0, 4); E(raw, strb_w_(0, 6, D_EXT + 6))
        # a note of the chord: its own gate, at most what is left of the chord
        E(mov_reg, 0, 6); E(movs_imm, 1, 7); E(raw, h(0x4029)); E(bl, "c_arord")           # ands r1, r5
        E(adds_reg, 0, 0, 6); E(ldrb_imm, 1, 0, S_NOTES)
        if MUTARP: E(bl, "c_armut")
        E(ldrb_imm, 2, 0, S_VELS); E(raw, ldrb_w_(3, 0, D_EXT)); E(push_list, [1, 2, 3])
        E(ldr_sp, 3, 8); E(cmp_imm, 3, 0); E(b_cond, "pg_1", "ne"); E(movs_imm, 3, 6)
        a.label("pg_1"); E(ldrb_imm, 0, 6, S_LEN); E(ldrb_imm, 1, 6, S_C); E(subs_reg, 0, 0, 1); E(cmp_reg, 0, 3); E(b_cond, "pg_2", "ls"); E(mov_reg, 0, 3)
        a.label("pg_2"); E(cmp_imm, 0, 0); E(b_cond, "pg_3", "ne"); E(movs_imm, 0, 1)
        a.label("pg_3"); E(mov_reg, 4, 0)
        E(ldr_sp, 0, 12); E(bl, "c_artps"); E(muls, 0, 4); E(movs_imm, 1, 6); E(raw, udiv(3, 0, 1)); E(cmp_imm, 3, 0); E(b_cond, "pg_4", "ne"); E(movs_imm, 3, 1)
        a.label("pg_4")
        if GATECAP:                                                                    # at most an arpeggio step
            E(push_list, [3]); E(mov_reg, 0, 7); E(bl, "c_arRt"); E(pop_list, [3]); E(cmp_reg, 3, 0); E(b_cond, "pg_5", "ls"); E(mov_reg, 3, 0)
            a.label("pg_5")
        E(pop_list, [1, 2]); E(add_sp_imm, 4); E(ldr_sp, 0, 0); E(bl, "c_arnote")
        a.label("py_t")
        E(ldr_sp, 0, 0); E(bl, "c_artps"); E(raw, ldrb_w_(1, 6, D_EXT + 6)); E(adds_reg, 1, 1, 0); E(cmp_imm, 1, 255); E(b_cond, "pt_k", "ls"); E(movs_imm, 1, 255)
        a.label("pt_k"); E(raw, strb_w_(1, 6, D_EXT + 6))
        E(ldrb_imm, 0, 6, S_C); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, S_C); E(ldrb_imm, 1, 6, S_LEN); E(cmp_reg, 0, 1); E(b_cond, "py_l", "lo")
        E(movs_imm, 0, 0); E(strb_imm, 0, 6, S_FL)
        a.label("py_l")                                                                # the input's arpeggio on its accumulator
        E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arst"); E(cmp_imm, 0, 0); E(b_cond, "py_x", "eq"); E(mov_reg, 4, 0)
        E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "py_x", "pl")
        E(mov_reg, 0, 7); E(bl, "c_arRt"); E(movs_imm, 1, 6); E(muls, 0, 1); E(mov_reg, 5, 0)
        E(raw, ldrb_w_(0, 4, D_EXT + 6)); E(cmp_reg, 0, 5); E(b_cond, "pl_a", "lo")
        E(subs_reg, 0, 0, 5); E(raw, strb_w_(0, 4, D_EXT + 6))
        E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arlstep")
        a.label("pl_a")
        E(ldr_sp, 0, 0); E(bl, "c_artps"); E(raw, ldrb_w_(1, 4, D_EXT + 6)); E(adds_reg, 1, 1, 0); E(cmp_imm, 1, 255); E(b_cond, "pl_k", "ls"); E(movs_imm, 1, 255)
        a.label("pl_k"); E(raw, strb_w_(1, 4, D_EXT + 6))
    a.label("py_x"); E(add_sp_imm, 16); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_arlon (the live note-on 0x0804B07A: view, note, velocity, pad)
    a.label("c_arlon")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(mov_reg, 0, 14); imm32(1, AUDITION_LR); E(cmp_reg, 0, 1); E(b_cond, "lo_s", "eq")
    E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x18); E(ldrb_imm, 7, 0, 0xC); E(cmp_imm, 7, 3); E(b_cond, "lo_s", "hi")
    E(mov_reg, 0, 7); E(bl, "c_arpat"); E(mov_reg, 1, 0); E(mov_reg, 0, 7); E(bl, "c_arcfg"); E(lsls_imm, 0, 0, 24); E(b_cond, "lo_s", "pl")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arst"); E(cmp_imm, 0, 0); E(b_cond, "lo_s", "eq"); E(mov_reg, 4, 0)
    E(ldrb_imm, 5, 4, S_N)
    E(mov_reg, 0, 4); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(bl, "c_arins")
    E(cmp_imm, 5, 0); E(b_cond, "lo_2", "ne")
    E(ldr_sp, 1, 4); E(strb_imm, 1, 4, S_FIRST); E(b, "lo_s")                          # the first note: as always
    a.label("lo_2")
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "lo_r", "mi")
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, S_FL); E(movs_imm, 0, 0); E(strb_imm, 0, 4, S_K); E(strb_imm, 0, 4, S_FG); E(strb_imm, 0, 4, S_FP)
    E(ldrb_imm, 0, 4, S_FIRST); E(strb_imm, 0, 4, S_PEND)
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(raw, str_w_(0, 4, S_NEXT))                # stopped: the first step now
    if RATE: E(mov_reg, 0, 7); E(bl, "c_arRt"); E(movs_imm, 1, 6); E(muls, 0, 1); E(raw, strb_w_(0, 4, D_EXT + 6))
    a.label("lo_r")                                                                    # the recorder still gets the note (the chord)
    imm32(0, REC); E(ldr_sp, 1, 4); E(ldr_sp, 2, 8); E(mov_reg, 3, 7); E(bl, REC_ON)
    E(ldr_sp, 0, 0); E(ldr_sp, 1, 4); E(adds_reg, 0, 0, 1); E(ldr_sp, 2, 12); E(raw, strb_w_(2, 0, 0x80))
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(raw, h(0x4770))
    a.label("lo_s"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(raw, LIVE_ON_OLD); E(b_w, LIVE_ON_BACK)

    # ---- c_arloff (the live note-off 0x0804AF5A: view, pad): the note out of the held ones; none left: the arpeggio ends
    a.label("c_arloff")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(adds_reg, 2, 0, 1); E(raw, ldrb_w_(5, 2, 0x40))                                   # r5 = the note
    E(ldr_imm, 0, 0, 0x18); E(ldrb_imm, 7, 0, 0xC); E(cmp_imm, 7, 3); E(b_cond, "lf_s", "hi")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arst"); E(cmp_imm, 0, 0); E(b_cond, "lf_s", "eq"); E(mov_reg, 4, 0)
    if RECOFF: E(ldrb_imm, 6, 4, S_N)                                                    # (RECOFF) r6 = how many before
    E(mov_reg, 1, 5); E(bl, "c_ardel")
    if RECOFF:
        E(ldrb_imm, 0, 4, S_N); E(cmp_reg, 0, 6); E(b_cond, "lf_q", "eq")                  # not one of the held: nothing
        E(ldrb_imm, 0, 4, S_FIRST); E(cmp_reg, 0, 5); E(b_cond, "lf_r", "ne")
        E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S_FIRST); E(b, "lf_q")                     # the stock's first note: its own note-off
        a.label("lf_r")
        imm32(0, REC); E(mov_reg, 1, 5); E(mov_reg, 2, 7); E(bl, REC_OFF)                  # ours: the recorder's note-off
        a.label("lf_q")
    E(ldrb_imm, 0, 4, S_PEND); E(cmp_reg, 0, 5); E(b_cond, "lf_p", "ne"); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 4, S_PEND)   # the stock stops it
    a.label("lf_p")
    E(ldrb_imm, 0, 4, S_N); E(cmp_imm, 0, 0); E(b_cond, "lf_s", "ne")
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "lf_s", "pl")
    E(mov_reg, 0, 7); E(bl, "c_arply"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(movs_imm, 3, 0); E(bl, "c_arnext")
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, S_FL)
    a.label("lf_s"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(raw, LIVE_OFF_OLD); E(b_w, LIVE_OFF_BACK)

    # ---- c_arpspad (the Pattern Settings view's pad press: view, pad, velocity): Shift + pad 25 / 27-32 on a note track
    a.label("c_arpspad")
    if RATE: E(cmp_imm, 1, PS_PAD_RATE); E(b_cond, "pp_r0", "lo"); E(cmp_imm, 1, PS_PAD_RATE + 7); E(b_cond, "pp_c", "ls"); a.label("pp_r0")
    E(cmp_imm, 1, PS_PAD_ARP); E(b_cond, "pp_c", "eq"); E(cmp_imm, 1, PS_PAD_ORD); E(b_cond, "pp_f", "lo"); E(cmp_imm, 1, 31); E(b_cond, "pp_f", "hi")
    a.label("pp_c")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 6, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pp_p", "eq")
    E(bl, L["c_rfnt"]); E(b_cond, "pp_p", "hs")
    E(bl, L["c_pmtp"]); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(bl, "c_arcfg")
    if RATE:                                                                           # pads 17-24: the resolution (the chosen one again: the track's)
        E(cmp_imm, 6, PS_PAD_ARP); E(b_cond, "pp_k", "hs")
        if RATEFLIP: E(movs_imm, 1, PS_PAD_RATE + 8); E(subs_reg, 6, 1, 6)                  # pad 17 = 8 (1/4) .. pad 24 = 1 (1/32T)
        else: E(subs_imm8, 6, PS_PAD_RATE - 1)
        E(lsrs_imm, 1, 0, 3); E(movs_imm, 2, 15); E(raw, h(0x4011)); E(cmp_reg, 1, 6); E(b_cond, "pp_rs", "ne")   # ands r1, r2
        E(movs_imm, 6, 0)
        a.label("pp_rs"); E(movs_imm, 1, 0x78); E(raw, h(0x4388)); E(lsls_imm, 6, 6, 3); E(raw, h(0x4330)); E(b, "pp_w")   # bics r0, r1; orrs r0, r6
        a.label("pp_k")
    E(cmp_imm, 6, PS_PAD_ARP); E(b_cond, "pp_o", "ne")
    E(movs_imm, 1, 0x80); E(raw, h(0x4048)); E(b, "pp_w")                                 # eors r0, r1
    a.label("pp_o")
    E(movs_imm, 1, 0xF8 if RATE else 0x80); E(raw, h(0x4008)); E(subs_imm8, 6, PS_PAD_ORD); imm32(2, t_ord); E(ldrb_reg, 2, 2, 6); E(raw, h(0x4310))  # ands r0, r1; orrs r0, r2
    a.label("pp_w"); E(mov_reg, 2, 0); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_arset")
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("pp_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True))
    a.label("pp_f"); E(b_w, prev["pspad"])

    # ---- c_arpsbuf (the Pattern Settings view's LED buffer getter): the chain, then pad 25 / 27-32 of ours
    a.label("c_arpsbuf")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 0); E(bl, prev["psbuf"]); E(mov_reg, 6, 0)
    E(bl, L["c_rfnt"]); E(b_cond, "pb_x", "hs")
    E(ldr_imm, 0, 7, 4); E(ldr_imm, 5, 0, 0)
    E(bl, L["c_pmtp"]); E(bl, "c_arcfg"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pb_s", "ne")
    E(lsls_imm, 0, 4, 24); E(b_cond, "pb_x", "pl")
    E(movs_imm, 1, COL_ON); E(movs_imm, 0, 2 * PS_PAD_ARP); E(raw, h(0x5229)); E(b, "pb_x")   # strh r1, [r5, r0]
    a.label("pb_s")
    if COLS2:
        E(lsls_imm, 0, 4, 24); E(b_cond, "pb_a2", "pl"); E(movs_imm, 1, COL_ON); E(movs_imm, 0, 2 * PS_PAD_ARP); E(raw, h(0x5229))
        a.label("pb_a2")
    else:
        E(movs_imm, 1, COL_AV); E(lsls_imm, 0, 4, 24); E(b_cond, "pb_a", "pl"); E(movs_imm, 1, COL_ON)
        a.label("pb_a"); E(movs_imm, 0, 2 * PS_PAD_ARP); E(raw, h(0x5229))
    E(movs_imm, 3, 0)
    a.label("pb_l")
    imm32(0, t_ord); E(ldrb_reg, 0, 0, 3); E(movs_imm, 1, COL_AV)
    E(movs_imm, 2, 7); E(raw, h(0x4022)); E(cmp_reg, 0, 2); E(b_cond, "pb_w", "ne"); E(movs_imm, 1, COL_ON)   # ands r2, r4
    if COLS2: E(b, "pb_w2")
    a.label("pb_w")
    if COLS2: E(b, "pb_n2")
    if COLS2: a.label("pb_w2")
    E(adds_imm8, 3, PS_PAD_ORD); E(lsls_imm, 0, 3, 1); E(raw, h(0x5229)); E(subs_imm8, 3, PS_PAD_ORD)
    if COLS2: a.label("pb_n2")
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 6); E(b_cond, "pb_l", "lo")
    if RATE:
        E(lsrs_imm, 7, 4, 3); E(movs_imm, 0, 15); E(raw, h(0x4007)); E(movs_imm, 3, 1)          # ands r7, r0: r7 = the resolution
        a.label("pb_r"); E(movs_imm, 1, COL_AV); E(cmp_reg, 3, 7); E(b_cond, "pb_rw", "ne"); E(movs_imm, 1, COL_ON)
        if COLS2: E(b, "pb_rw2")
        a.label("pb_rw")
        if COLS2: E(b, "pb_rn2")
        if COLS2: a.label("pb_rw2")
        if RATEFLIP: E(lsls_imm, 0, 3, 1); E(movs_imm, 2, 2 * (PS_PAD_RATE + 8)); E(subs_reg, 0, 2, 0)
        else: E(lsls_imm, 0, 3, 1); E(adds_imm8, 0, 2 * (PS_PAD_RATE - 1))
        E(raw, h(0x5229))                                                              # strh r1, [r5, r0]
        if COLS2: a.label("pb_rn2")
        E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "pb_r", "ls")
    a.label("pb_x"); E(mov_reg, 0, 6); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_arledtask (the LED task calls: ctrl, frame): the chain; stopped: no sequence arpeggio, the input's one on the clock
    a.label("c_arledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["ledtask"])
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "ne")
    E(movs_imm, 7, 0)
    a.label("lt_l")
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_arst"); E(cmp_imm, 0, 0); E(b_cond, "lt_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, S_FL)
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, "c_arst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, S_FL); E(lsls_imm, 0, 0, 31); E(b_cond, "lt_n", "pl")
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0); E(raw, ldr_w_(1, 4, S_NEXT)); E(subs_reg, 0, 5, 1); E(b_cond, "lt_n", "mi")
    # due: a step, then the next time = now + 2500 ticks-a-step / BPM ms
    E(mov_reg, 0, 7); E(movs_imm, 1, 0); E(bl, "c_arlstep")
    if RATE: E(mov_reg, 0, 7); E(bl, "c_arRt"); E(mov_reg, 6, 0)
    else: E(mov_reg, 0, 7); E(bl, "c_arply"); E(bl, "c_artps"); E(mov_reg, 6, 0)
    imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 30); E(b_cond, "lt_b", "hs"); E(movs_imm, 1, 120)
    a.label("lt_b"); imm32(0, 2500); E(muls, 0, 6); E(raw, udiv(0, 0, 1)); E(adds_reg, 0, 0, 5); E(raw, str_w_(0, 4, S_NEXT))
    a.label("lt_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "lt_l", "lo")
    a.label("lt_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_arzero(r0 = 1: the setting block too): the running states to 0; clobbers r1-r3
    a.label("c_arzero")
    E(push_list, [4], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_artail"); E(cmp_imm, 0, 0); E(b_cond, "zr_x", "eq")
    imm32(1, O_SEQ); E(cmp_imm, 4, 0); E(b_cond, "zr_a", "eq"); imm32(1, O_BLK)
    a.label("zr_a"); imm32(3, O_END); E(movs_imm, 2, 0)
    a.label("zr_l"); E(strb_reg, 2, 0, 1); E(adds_imm8, 1, 1); E(cmp_reg, 1, 3); E(b_cond, "zr_l", "lo")
    if RATE:
        imm32(1, EXT_LO); imm32(3, EXT_HI)
        a.label("zr_e"); E(strb_reg, 2, 0, 1); E(adds_imm8, 1, 1); E(cmp_reg, 1, 3); E(b_cond, "zr_e", "lo")
    a.label("zr_x"); E(pop_list, [4], pc=True)

    # ---- c_arload / c_arnew (the ends of the stock's apply and new project, in front of the others)
    a.label("c_arload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 0, 0); E(bl, "c_arzero"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    a.label("c_arnew")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 0, 1); E(bl, "c_arzero"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["new"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the players' slot 2, the live note-on / note-off, the Pattern Settings view's slots 0 / 7, the LED task calls, the ends of the
    stock's apply and new project."""
    import ct_fw
    import stepmod as SM
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_shift=lab("sc15", "c_shift"), c_rfnt=lab("stepmod", "c_rfnt"), c_pmtp=lab("playmode", "c_pmtp"))
    if MUTARP: L["c_mutscale"] = lab("mutate39", "c_mutscale")
    prev = dict(pspad=u(SM.PS_VT) & ~1, psbuf=u(SM.PS_VT + 28) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                load=MP.bw_target(img, P19.LOAD_END, BASE), new=MP.bw_target(img, P19.NEW_TAIL, BASE))
    assert u(PLAYER_VT + 8) == PLAY_STOCK | 1
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    def put(addr, data, old):
        assert bytes(img[addr - BASE:addr - BASE + len(old)]) == old, hex(addr)
        img[addr - BASE:addr - BASE + len(data)] = data
    struct.pack_into("<I", img, PLAYER_VT + 8 - BASE, labels["c_arplay"] | 1)
    put(LIVE_ON, b_w(LIVE_ON, labels["c_arlon"]), LIVE_ON_OLD)
    put(LIVE_OFF, b_w(LIVE_OFF, labels["c_arloff"]), LIVE_OFF_OLD)
    struct.pack_into("<I", img, SM.PS_VT - BASE, labels["c_arpspad"] | 1)
    struct.pack_into("<I", img, SM.PS_VT + 28 - BASE, labels["c_arpsbuf"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_arledtask"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_arload"])
    img[P19.NEW_TAIL - BASE:P19.NEW_TAIL - BASE + 4] = b_w(P19.NEW_TAIL, labels["c_arnew"])
    return labels, code, prev
