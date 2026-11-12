"""SC54 (the user, 2026-11-07): the patch morph of Synth 1 / 2 and of the own synth of MIDI 1 / 2 (its codes and its 8-operator FM).  «Se
seleccionan dos (o más) parches y se toma el parche presente. Sólo funcionan los knobs. Uno para navegar entre parches y otros con lfos y cosas
para modular. Si cabe un envelope, se dispara con un pad»; «Pads 1 y 8 (para usarlo con dos manos)»; «Color de la pista»; «Durante este modo,
abrir la vista Preset muestra los parches en blanco iluminado, seleccionar uno carga ese parche. Mantener cambia los parches asignados manteniendo
el estado de los knobs»; chosen: a view of its own, out with pad 32 (red), a single patch or the track's button; «Duplicate no se usa en este
modo»; «los botones up/down cambian la posición del parche inicial en la cadena».  One morph at a time.

  * Enter: in the track's Preset view, two or more patches held 0.4 s (the user: «Solo con mantener», «al menos dos pads mantenidos a la vez»), or
    held + Duplicate.  The chain = the present sound (as it was before the held pads loaded anything: kept at the first patch press) + the held
    patches (up to 3, in pad order).  Synth 1 / 2: their patches (pad + 32 x the page); MIDI 1 / 2: the own-synth slots (pads 9-24 + 16 x the page)
    with the engine on.
  * Where the morph view is (the user: «Al volver a synth1 desde mixer … no se vuelve a la vista morph», «preset dos veces abre la misma vista que
    Synth dos veces»): Synth 1 / 2 = their alternative view (srcview's source view: Synth twice, now also Preset twice, which opens it with the
    morph off too); MIDI 1 / 2 = their Preset view (Preset toggles the morph view and the patches).  The track's button from anywhere else = the
    morph view; from the morph view = the stock (the Note view).
  * The morph view: only the knobs work.  K1 = the position in the chain, K2 / K3 LFO 1 (triangle) depth / rate,
    K4 / K5 LFO 2 (random steps) depth / rate, K6 random each step of the track, K7 / K8 envelope depth / time (the depths bipolar: right =
    towards the chain's end); Clear + knob = 0.  Pads 1 and 8 = the envelope from the top (the track's colour, bright while it runs); pad 32
    (red) = out; Octave down / up = the initial patch one place earlier / later in the chain (lit when it can move); Duplicate does nothing.
  * Preset (the button) in the morph view = the patches (the chain's in white); Preset again = back.  There a single patch tapped = that patch
    loaded and the morph out; patches held 0.4 s = the chain becomes the initial patch + those (the knobs as they were).  The morph goes on in
    the other views.  Out: pad 32 (back to the patches) or a single patch.  The sound stays where it is.
  * The LEDs are drawn into a copy of the view's buffer (LB): the stock's own buffer is only repainted by the stock, so a morph view drawn into
    it stayed on the pads after the exit.  The hooks of the LED task keep nothing on the stack while the chain below runs (the frame and LR
    in SV): SC54's first build went 76 B deeper in the MIDI Preset view's frame and the device reset there.
  * The engine (the LED task): one link a frame read from the card into RAM until the chain is cached; the position = K1 + the modulations;
    between links i and i + 1 at f: a continuous parameter A + (B - A) f, a discrete one the nearest link's.  Synth 1 / 2: the firmware's
    parameter table (0x0805454A, row = the parameter's NRPN index: its byte and kind, 1 / 2 continuous; bitfield rows left alone) as a received NRPN
    (0x08034D92), at most BUDGET a frame; MIDI 1 / 2: codes 1..34 (13, 16, 25 discrete) by c_vstore, the 8-operator FM block when both links
    carry one (fm_disc discrete), its dirty bit.
RAM MZ (0x2004E4A0..0x2004EDB8): the state, the cache (4 links x 310 B), the FM blocks (4 x 216 B), the LED copies, the saved frames.  Nothing saved.
Room (the flash is full): the functions are packed into several free areas (place(): the hole, dspz's two gaps, jumpflip's two handlers that
nothing calls since flipview, the image's end), each area assembled on its own, calls between them by address (two passes)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_w,  # noqa: E402
                   ldrb_reg, ldrh_imm, ldrh_reg, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list,
                   push_list, raw, str_imm, strb_imm, strb_reg, strh_imm, strh_reg, subs_imm3, subs_imm8, subs_reg, tst_reg)
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import vcf21 as V  # noqa: E402
import jumpseq as JS  # noqa: E402

MZ = 0x2004E4A0
SIG = 0x315A524D                         # "MRZ1"
O_ACT, O_N, O_SL, O_SNAP, O_CV, O_SHOW, O_K, O_S2, O_RS, O_LS, O_PG, O_HP, O_PPAD, O_PVEL, O_ORD = 4, 5, 6, 9, 10, 11, 12, 20, 21, 22, 23, 24, 25, 26, 28
O_PH1, O_PH2, O_ENV, O_RR = 32, 34, 36, 38                     # halfwords
O_RNG, O_T, O_TP, O_PVIEW = 40, 44, 48, 52                    # words
O_DT, O_SHT = 56, 60                                           # the frame's dt (halfword); when c_mzshow put up the MIDI morph view (word)
CC = MZ + 0x40                           # cache index j: + 310 j (Synth: the patch's bytes 30..339; own: codes 1..34)
FC = CC + 4 * 310                        # own: the FM block of cache index j at + 216 j
LB, LBN = FC + 4 * 216 + 8, 84                # the view's LEDs copied (42 entries)
KLB, KLBN = LB + LBN + 4, 32                  # the knob LEDs copied (16 entries)
SV = KLB + KLBN                               # the LED hooks' saved arguments and LR: + 0 / 4 the tick, + 8 / 12 the view, + 16 / 20 the knobs
END = SV + 24
NOVA_LEN, FM_LEN = 310, 216
BUDGET = 40
HOLD_MS = 400
ARMED = 4                                # O_HP with the morph off: a patch held since its press (the hold that opens it)
LIVE = 0x20010044                        # Synth 1's patch in RAM (Synth 2 + 344)
PARAM_SET, CTX = 0x08034D92, 0x200069E4
TABLE, NROWS = 0x0805454A, 310
STORE = 0x20038EC0
TRIG = (0, 7)                            # pads 1 and 8
P_OUT = 31                               # pad 32
WHITE, RED = 0x01, 0x53
DISC_OWN = (13, 16, 25)
UNI = 0x95                               # K1, K3, K5, K8: 0..127 (bits); the others -64..63
DEF_K = (0, 0, 64, 0, 64, 0, 0, 64)
DUP, ID_DOWN, ID_UP, ID_PRESET = 24, 19, 20, 8
CLEAR = 23
CLR2 = False                             # SC55.1 (use_clr2)
SUS = False                              # SC55.1 (use_sus)
NOCUR = False                            # SC55.1 (use_nocur)
FOUR = False                             # SC56.4 (use_four): up to 4 held patches
SLOW = False                             # SC56.5 (use_slow): K5 / K6 slow morph, square LFO, LFO slew on K8, colour K1 / K5
SL = 0x2004EDC0                          # (use_slow) + 0 flags (bit 0 K5 aimed, bit 1 gliding), + 1 the square's half, + 2 the glide's start (h),
                                         #   + 4 S1, + 8 S2, + 12 S2's target, + 16 K5's last turn (ms), + 20 the glide's progress (24 bits), + 24 its position
SL_END = SL + 28
AIM_MS = 500                             # K5 at rest this long = the glide starts
GRAD = bytes([0x53, 0x45, 0x7F, 0x51, 0x6D, 0x2D, 0x6F, 0x70, 0x71, 0x72, 0x17, 0x74, 0x4D, 0x13, 0x12, 0x09])   # red > yellow > green > blue
SLOW_FUNCS = ("c_mzslow", "c_mzslw", "c_mzgc")
TEMPO = 0x20011404
TRIMP = False                            # SC56 (use_trimpanel): c_mzpanel left out (NOCUR never calls it)
ENDLAST = False                          # SC56: the image's end only when nothing else fits (dspz v2's first gap is bigger than the end)
SVC = False                              # SC55.4 (use_svc)
NV = END                                 # (use_svc) + 0 a write pending, + 1 t, + 2 f, + 3 / 4 the links' cache indices, + 5 inside the
NV_END = NV + 12                         #   service's writes, + 8 the service's SP then (word)
MARK_DIRTY, MARK_RAW = 0x0803BDCC, 0x08021FDC
SVC_FUNCS = ("c_mzsvc", "c_mzmd")


def use_svc():
    """SC55.4 / Beta 5.39 (fix; the user, 2026-11-08, on Synth 1: «entering morph mode stops the playback, and resets the unit after a few
    seconds»): Synth 1 / 2's rows went through the firmware's parameter setter (0x08034D92) from the LED task, 40 a frame; each change calls
    MARK_DIRTY (0x0803BDCC), which waits for the DSP service's semaphore (0x08021064: a spin with a yield, not a mutex), and the main loop that
    holds it stalled: no audio, no sequencer, then the reset.  Now the LED task only leaves the frame's t, f and links (NV) and the head of the DSP
    service chain (c_mzsvc, where the service already holds the semaphore) writes the rows; while it does, MARK_DIRTY's head (c_mzmd) marks with
    0x08021FDC directly (the rule for the service's tick) when the call comes from that stack (within 1 KB below the SP it noted)."""
    global SVC
    SVC = True




def use_sus():
    """SC55.1 (the user, 2026-11-08: «the envelope pad on morph should have sustain as you hold it»): while pad 1 or 8 is held in the morph view the
    envelope stays where it is (at the top after the press); it falls from the release."""
    global SUS
    SUS = True


def use_nocur():
    """SC55.1 (the user, 2026-11-08: «discard the current patch from the patch morph selection, now patch morph just morphs between held patches (no
    current patch in the mix unless held again)»): the chain = the held patches only (cache 0, the present sound, still taken but at the chain's
    end, out of K1's range: ORD = 1, 2, 3, 0 and n - 2 segments); Octave in the morph view (the initial patch's place) has no meaning: nothing, unlit."""
    global NOCUR
    NOCUR = True


def use_four():
    """SC56.4 (the user, 2026-11-11: «Make it up to 4 patches»): with use_nocur the chain takes up to 4 held patches.  Cache 0 (the present sound,
    never reached with use_nocur) holds the 4th; its slot is byte O_SL + 3, so O_SNAP moves to the free byte 27 and the signature changes (an
    install does not clear the RAM).  ORD stays 1, 2, 3, 0: 3 held = 2 segments over caches 1-3, 4 held = 3 segments over 1, 2, 3, 0."""
    global FOUR, O_SNAP, SIG
    assert NOCUR
    FOUR = True
    O_SNAP = 27
    SIG = 0x325A524D                     # "MRZ2"


def use_slow():
    """SC56.5 (the user, 2026-11-11): «Random lfo speed is now k3 too. K5 and k6 become slow morph: K5 sets the morph destination. K6 sets the
    speed … the patch morphs from k1 into K5. The more clockwise k6, the longer the morph time. When the destination is reached, K5 value is
    assigned to K1 knob. K5 and K1 now show their patches with colors … a color palette that blends into each other. K8 is not only the envelope
    decay time, it adjusts the slew on the lfos. The tri lfo is now square with slew»; chosen: the glide starts when K5 has rested 0.5 s (turning
    it again re-aims from where the sound is), K6 fully left = at once, then 1/4 .. 32 bars of the project's tempo (an octave every 18 clicks),
    a fixed gradient (patch 1 red, 2 yellow, 3 green, 4 blue, palette shades in between), the old K6 (random each step) dropped.
      K1 position (turned while gliding: from where the glide is, the glide off), K2 / K4 depth of LFO 1 (square) / LFO 2 (random, a new value
      at each of the square's halves), K3 their rate, K5 destination, K6 time, K7 envelope depth, K8 envelope time = the LFOs' slew (the same rate:
      a full swing takes the envelope's time).  RAM SL (28 B between the morph's and loadcache's)."""
    global SLOW, UNI, DEF_K, SIG
    assert FOUR
    SLOW = True
    UNI = 0xB5                           # K1, K3, K5, K6, K8 unipolar
    DEF_K = (0, 0, 64, 0, 0, 64, 0, 64)
    SIG = 0x335A524D                     # "MRZ3"
    assert NV_END <= SL and SL_END <= 0x2004EE00


def use_trimpanel():
    """SC56 (room): with use_nocur the panel's Octave (c_mzpanel) is never called: left out."""
    global TRIMP, ENDLAST
    assert NOCUR
    TRIMP = ENDLAST = True


def use_clr2():
    """SC55.1 (the user, 2026-11-08: «clear + knob debe seguir funcionando, pero clear no debe salir de la vista», «clear+synth1 en esta vista
    debe devolver el morph al estado inicial (knobs a 0/centro)»): in the morph view Clear goes to the stock (its held state, so Clear + knob = 0
    still works) and the view is put back if the press closed it (srcview's «any button closes it»: the synths' morph view); Clear + the morphed
    track's button in the morph view = K1..K8 to 0 (the initial patch, every depth at the centre), the view stays, the stock's Clear + track not run."""
    global CLR2
    CLR2 = True
BTN, BTN_REL = 0x08033320, 0x0803381A
S_PAINT, F_SRC = 20, 4                   # srcview: the source view's flag, bit 2 of c_gst() + 20
F_SDOPEN = 0x10                          # vcf21's step-drummer view flag (O_FLAGS bit 4), changed with its c_sdfset
LED_DOWN, LED_UP = 51, 52
INV = V.INV
RET = h(0x4770)
PUSHALL, POPALL, POPALL_LR = h(0xE92D) + h(0x5FFF), h(0xE8BD) + h(0x9FFF), h(0xE8BD) + h(0x5FFF)     # push.w {r0-r12, lr} / pop.w {r0-r12, pc} / {r0-r12, lr}
POP_LR = h(0xF85D) + h(0xEB04)                                    # ldr lr, [sp], #4
JF_DEAD = (("c_jfpad", "jf_tg"), ("c_jfled", None))               # jumpflip's handlers flipview skips: [label, next label or the block's end)


def fm_disc():
    """the FM block's discrete bytes (a bitmap of 27 B, bit set = discrete)"""
    import fm8 as F
    d = [0] * 27
    def put(p): d[p >> 3] |= 1 << (p & 7)
    opd = [F.VOP.index(n) for n in ("lc", "rc", "rs", "ams", "kvs", "mode", "crs")] + list(range(len(F.VOP), F.OPB))
    for k in range(F.OPS):
        for i in opd: put(F.OPB * k + i)
    for g in (F.G_ALG, F.G_SYNC, F.G_TRN, F.G_NZOP): put(F.GLB + g)
    for p in range(F.GLB + 13, F.PLEN): put(p)
    return bytes(d)


def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)
def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def asrs(rd, rm, n): return h(0x1000 | n << 6 | rm << 3 | rd)
def mov_hi(rd, rm): return h(0x4600 | (rd & 8) << 4 | rm << 3 | (rd & 7))       # mov rd, rm (any)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


FUNCS = {}


def fn(f):
    FUNCS[f.__name__] = f
    return f


# Each function: f(c) with c = the part's context (E, a, imm32, call, bc, now, L, prev, ext); its first label is its name.

@fn
def c_mzst(c):                           # () -> r0 = MZ (the first time: off, no snapshot); clobbers r1, r2
    E = c.E; c.imm32(0, MZ); E(ldr_imm, 1, 0, 0); c.imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, O_ACT); E(strb_imm, 1, 0, O_SNAP)
    c.lab("st_x"); E(raw, RET)


@fn
def c_mzon(c):                           # (r0 = t) -> r0 = 1 when the track's Preset view is on the screen; clobbers r1-r3
    E = c.E; E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(cmp_imm, 4, 2); E(b_cond, "on_m", "hs"); c.call("c_pson"); E(b, "on_c")
    c.lab("on_m"); c.call("c_mpon"); E(adds_imm8, 0, 2)
    c.lab("on_c"); E(cmp_reg, 0, 4); E(movs_imm, 0, 0); E(b_cond, "on_x", "ne"); E(movs_imm, 0, 1)
    c.lab("on_x"); E(pop_list, [4], pc=True)


@fn
def c_mzvon(c):                          # (r4 = t, MIDI) -> r0 = its engine on; clobbers r1-r3
    E = c.E; E(push_list, [], lr=True); E(mov_reg, 0, 4); E(subs_imm8, 0, 2); c.call("c_von"); E(pop_list, [], pc=True)


@fn
def c_mzheld(c):                         # (r4 = t) -> r0 = the patch pads held (bits); clobbers r1
    E = c.E; c.imm32(0, MP.MGR + 0x84); E(ldr_imm, 0, 0, 0); E(cmp_imm, 4, 2); E(b_cond, "hd_x", "lo"); c.imm32(1, 0x00FFFF00); E(ands_reg, 0, 1)
    c.lab("hd_x"); E(raw, RET)


@fn
def c_mzrnd(c):                          # (r6 = MZ) -> r0 = -128..127; clobbers r1, r2
    E = c.E; E(ldr_imm, 1, 6, O_RNG); c.imm32(2, 1664525); E(muls, 1, 2); c.imm32(2, 1013904223); E(adds_reg, 1, 1, 2); E(str_imm, 1, 6, O_RNG)
    E(lsrs_imm, 0, 1, 24); E(subs_imm8, 0, 128); E(raw, RET)


@fn
def c_mzcpy(c):                          # (r0 = dst, r1 = src, r2 = bytes); clobbers r2, r3
    E = c.E; c.lab("cp_l"); E(subs_imm8, 2, 1); E(ldrb_reg, 3, 1, 2); E(strb_reg, 3, 0, 2); E(cmp_imm, 2, 0); E(b_cond, "cp_l", "ne"); E(raw, RET)


@fn
def c_mzcol(c):                          # (r4 = t) -> r0 = the track's colour, r1 = its dim one; clobbers r2
    E = c.E; E(lsls_imm, 2, 4, 1); E(adds_imm8, 2, 2); c.imm32(1, JS.PAL); E(ldrh_reg, 0, 1, 2); E(adds_imm8, 2, 16); E(ldrh_reg, 1, 1, 2); E(raw, RET)


@fn
def c_mzpos(c):                          # (r6 = MZ) -> r0 = the initial patch's place, r2 = n - 1; clobbers r1
    E = c.E; E(movs_imm, 0, 0)
    c.lab("ps_l"); E(adds_reg, 1, 6, 0); E(ldrb_imm, 1, 1, O_ORD); E(cmp_imm, 1, 0); E(b_cond, "ps_x", "eq"); E(adds_imm8, 0, 1); E(cmp_imm, 0, 3)
    E(b_cond, "ps_l", "lo")
    c.lab("ps_x"); E(ldrb_imm, 2, 6, O_N); E(subs_imm8, 2, 1); E(raw, RET)


@fn
def c_mzsp(c):                           # (r0 = a view) -> Z set when it is the synths' Preset view; clobbers r0, r1
    E = c.E; E(ldr_imm, 0, 0, 0); c.imm32(1, c.SP); E(cmp_reg, 0, 1); E(raw, RET)


@fn
def c_mzalt(c):                          # (r0 = s) -> r0 = 1 when synth s's alternative view (srcview's source view) is on the screen; clobbers r1-r3
    E = c.E; E(push_list, [], lr=True)
    c.imm32(1, MP.MGR); E(ldr_imm, 2, 1, 0x6C); E(ldr_imm, 3, 1, 0x2C); E(cmp_reg, 2, 3); E(b_cond, "al_0", "ne")
    E(ldrb_w, 2, 1, V.S_CUR); E(lsls_imm, 3, 0, 3); E(adds_reg, 3, 3, 0); E(cmp_reg, 2, 3); E(b_cond, "al_0", "ne")
    c.call("c_gst"); E(cmp_imm, 0, 0); E(b_cond, "al_x", "eq")
    E(ldrb_imm, 0, 0, S_PAINT); E(lsrs_imm, 0, 0, 2); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
    c.lab("al_x"); E(pop_list, [], pc=True)
    c.lab("al_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)


@fn
def c_mzmv(c):                           # (r4 = t <= 3, r6 = MZ) -> r0 = 1 when t's morph view is on the screen; clobbers r1-r3
    E = c.E; E(push_list, [], lr=True)
    E(cmp_imm, 4, 2); E(b_cond, "mv_m", "hs"); E(mov_reg, 0, 4); c.call("c_mzalt"); E(pop_list, [], pc=True)
    c.lab("mv_m"); E(ldrb_imm, 0, 6, O_SHOW); E(cmp_imm, 0, 0); E(b_cond, "mv_0", "eq")
    c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "mv_0", "ne"); E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    c.lab("mv_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)


@fn
def c_mzsrc(c):                          # (r0 = 0 close / 1 open / 2 open as the morph view: vcf21's step-drummer view closed) srcview's flag; clobbers r0-r3
    E = c.E; E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    c.call("c_gst"); E(cmp_imm, 0, 0); E(b_cond, "sr_x", "eq"); E(adds_imm8, 0, S_PAINT)
    E(movs_imm, 1, F_SRC); E(movs_imm, 2, 0); E(cmp_imm, 4, 0); E(b_cond, "sr_1", "ne"); E(movs_imm, 1, 0); E(movs_imm, 2, F_SRC)
    c.lab("sr_1"); c.call("c_rmw")
    E(cmp_imm, 4, 2); E(b_cond, "sr_x", "ne"); E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 0); c.call("c_sdfset")
    c.lab("sr_x"); E(pop_list, [4], pc=True)


@fn
def c_mztap(c):                          # () a tap on Preset (press + release through the controller); clobbers r0-r3
    E = c.E; E(push_list, [], lr=True)
    c.imm32(0, MP.MGR); E(movs_imm, 1, ID_PRESET); c.call(BTN)
    c.imm32(0, MP.MGR); E(movs_imm, 1, ID_PRESET); c.call(BTN_REL)
    E(pop_list, [], pc=True)


@fn
def c_mzshow(c):                         # (r4 = t, r6 = MZ) t's morph view on the screen (after the track's button went to the stock); clobbers r0-r3
    E = c.E; E(push_list, [], lr=True)
    E(cmp_imm, 4, 2); E(b_cond, "sh_m", "hs")
    E(mov_reg, 0, 4); c.call("c_mzalt"); E(cmp_imm, 0, 0); E(b_cond, "sh_x", "ne")
    c.call("c_pson"); E(cmp_reg, 0, 4); E(b_cond, "sh_s", "eq")
    c.call("c_mztap"); c.call("c_pson"); E(cmp_reg, 0, 4); E(b_cond, "sh_x", "ne")
    c.lab("sh_s"); E(movs_imm, 0, 2); c.call("c_mzsrc"); E(b, "sh_x")
    c.lab("sh_m"); c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "sh_o", "eq")
    c.call("c_mztap"); c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "sh_o", "eq")
    E(movs_imm, 0, F_SDOPEN); E(movs_imm, 1, 0); c.call("c_sdfset")                         # its own step-drummer covers it: closed
    c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "sh_x", "ne")
    c.lab("sh_o"); E(movs_imm, 0, 1); E(strb_imm, 0, 6, O_SHOW); c.now(0); E(str_imm, 0, 6, O_SHT)
    c.lab("sh_x"); E(pop_list, [], pc=True)


@fn
def c_mzlb(c):                           # (r5 = the view's buffer) -> r5 = LB, a copy; clobbers r0-r3
    E = c.E; E(push_list, [], lr=True)
    c.imm32(0, LB); E(mov_reg, 1, 5); E(movs_imm, 2, LBN); c.call("c_mzcpy"); c.imm32(5, LB)
    E(pop_list, [], pc=True)


@fn
def c_mzcd(c):                           # () -> r0 = Clear (bit 0) / Duplicate (bit 1) held; clobbers r1-r3
    E = c.E; E(push_list, [], lr=True)
    c.imm32(0, MP.MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); c.call(PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(pop_list, [], pc=True)


@fn
def c_mzkey(c):                          # () -> r0 = [MGR + 0x152] | 0x100 when the container is not the view on the screen; clobbers r1-r3
    E = c.E; c.imm32(1, MP.MGR); E(ldrb_w, 0, 1, V.S_CUR); E(ldr_imm, 2, 1, 0x6C); E(ldr_imm, 3, 1, 0x2C); E(cmp_reg, 2, 3); E(b_cond, "ky_x", "eq")
    E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2)
    c.lab("ky_x"); E(raw, RET)


@fn
def c_mzsnap(c):                         # (r4 = t, r6 = MZ): the present sound into cache 0 (and its FM block); clobbers r0-r3, r5
    import fm8arm as A
    E = c.E; E(push_list, [], lr=True)
    E(strb_imm, 4, 6, O_SNAP); E(movs_imm, 0, 1); E(strb_imm, 0, 6, O_CV)
    E(cmp_imm, 4, 2); E(b_cond, "sn_o", "hs")
    c.imm32(1, LIVE + 30); E(movw, 0, 344); E(muls, 0, 4); E(adds_reg, 1, 1, 0); c.imm32(0, CC); E(movw, 2, NOVA_LEN); c.call("c_mzcpy")
    E(pop_list, [], pc=True)
    c.lab("sn_o"); E(movs_imm, 5, 1)
    c.lab("sn_l"); E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(mov_reg, 1, 5); c.call("c_vvaddr"); E(ldrb_imm, 0, 0, 0)
    c.imm32(1, CC - 1); E(strb_reg, 0, 1, 5); E(adds_imm8, 5, 1); E(cmp_imm, 5, 34); E(b_cond, "sn_l", "ls")
    c.imm32(1, A.FM8R + A.TB0 - 0x200); E(lsls_imm, 0, 4, 8); E(adds_reg, 1, 1, 0); E(movs_imm, 0, A.B_ON); E(ldrb_reg, 0, 1, 0); E(cmp_imm, 0, 1)
    E(b_cond, "sn_x", "ne")
    c.imm32(0, FC); E(movs_imm, 2, FM_LEN); c.call("c_mzcpy"); E(movs_imm, 0, 0x11); E(strb_imm, 0, 6, O_CV)
    c.lab("sn_x"); E(pop_list, [], pc=True)


@fn
def c_mzchain(c):                        # (r0 = the patch pads held, r4 = t, r6 = MZ) -> r0 = n; the initial patch kept at its place; clobbers r1-r3, r5, r7
    E = c.E; E(push_list, [4], lr=True)
    E(movs_imm, 1, 0); E(movs_imm, 3, 32); E(movs_imm, 7, 32)
    E(cmp_imm, 4, 2); E(b_cond, "ch_s", "lo"); E(movs_imm, 1, 8); E(movs_imm, 3, 24); E(movs_imm, 7, 16)
    c.lab("ch_s"); E(ldrb_imm, 2, 6, O_PG); E(muls, 7, 2); E(subs_reg, 7, 7, 1)          # r7 = page x size - the first pad: slot = pad + r7
    E(movs_imm, 2, 1)
    c.lab("ch_l"); E(cmp_reg, 1, 3); E(b_cond, "ch_d", "hs"); E(cmp_imm, 2, 5 if FOUR else 4); E(b_cond, "ch_d", "hs")
    E(movs_imm, 5, 1); E(lsls_reg, 5, 1); E(tst_reg, 0, 5); E(b_cond, "ch_n", "eq")
    E(adds_reg, 5, 1, 7); E(adds_reg, 4, 6, 2); E(strb_imm, 5, 4, O_SL - 1); E(adds_imm8, 2, 1)
    c.lab("ch_n"); E(adds_imm8, 1, 1); E(b, "ch_l")
    c.lab("ch_d"); E(strb_imm, 2, 6, O_N)
    if NOCUR:                                                                             # (NOCUR) the held patches only: ORD = 1, 2, 3, 0
        if FOUR: E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_CV)                              # (FOUR) cache 0 may be the 4th held patch
        else: E(ldrb_imm, 0, 6, O_CV); E(movs_imm, 1, 0x11); E(ands_reg, 0, 1); E(strb_imm, 0, 6, O_CV)
        c.imm32(0, 0x00030201); E(str_imm, 0, 6, O_ORD)
        E(ldrb_imm, 0, 6, O_N); E(pop_list, [4], pc=True)
    E(ldrb_imm, 0, 6, O_CV); E(movs_imm, 1, 0x11); E(ands_reg, 0, 1); E(strb_imm, 0, 6, O_CV)
    E(push_list, [2]); c.call("c_mzpos"); E(mov_reg, 3, 0); E(pop_list, [2])              # r3 = p, clamped to n - 1
    E(subs_imm8, 2, 1); E(cmp_reg, 3, 2); E(b_cond, "ch_pc", "ls"); E(mov_reg, 3, 2)
    c.lab("ch_pc"); E(movs_imm, 1, 0)                                                     # ORD[j] = j + 1 (j < p), 0 (p), j (j > p)
    c.lab("ch_o"); E(adds_imm3, 0, 1, 1); E(cmp_reg, 1, 3); E(b_cond, "ch_ow", "lo"); E(mov_reg, 0, 1); E(b_cond, "ch_ow", "ne"); E(movs_imm, 0, 0)
    c.lab("ch_ow"); E(adds_reg, 5, 6, 1); E(strb_imm, 0, 5, O_ORD); E(adds_imm8, 1, 1); E(cmp_imm, 1, 4); E(b_cond, "ch_o", "lo")
    E(ldrb_imm, 0, 6, O_N); E(pop_list, [4], pc=True)


@fn
def c_mzenter(c):                        # (r0 = the patch pads held, r4 = t, r6 = MZ) -> r0 = 1 when the morph is on; clobbers r1-r3, r5, r7
    E = c.E; E(push_list, [], lr=True)
    E(movs_imm, 1, 0); E(str_imm, 1, 6, O_ORD)
    c.call("c_mzchain"); E(cmp_imm, 0, 3); E(b_cond, "en_0", "lo")                          # two held patches at least
    E(strb_imm, 4, 6, O_ACT); E(movs_imm, 0, 0); E(cmp_imm, 4, 2); E(b_cond, "en_s", "lo"); E(movs_imm, 0, 1)
    c.lab("en_s"); E(strb_imm, 0, 6, O_SHOW)                                                # MIDI: over the Preset view
    for j in (0, 4): c.imm32(0, struct.unpack("<I", bytes(DEF_K[j:j + 4]))[0]); E(str_imm, 0, 6, O_K + j)
    E(movs_imm, 0, 0); E(strh_imm, 0, 6, O_ENV); E(strb_imm, 0, 6, O_HP); E(str_imm, 0, 6, O_SHT)
    if SLOW:                                                                                # (SLOW) no glide, the LFOs' values at 0
        c.imm32(1, SL)
        for o in (0, 4, 8, 12): E(str_imm, 0, 1, o)
    E(cmp_imm, 4, 2); E(b_cond, "en_1", "hs"); E(movs_imm, 0, 2); c.call("c_mzsrc")         # synth: its alternative view
    c.lab("en_1"); E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    c.lab("en_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)


@fn
def c_mzpad(c):                          # (r4 = t, r5 = pad, r6 = 1 when a patch pad, r7 = the page; [sp + 4] the view, [sp + 12] the velocity) -> r0 = 1 swallowed
    E = c.E; E(push_list, [], lr=True)
    E(cmp_imm, 6, 0); E(b_cond, "pd_s", "eq")
    c.call("c_mzcd"); E(cmp_imm, 0, 0); E(b_cond, "pd_n", "ne")                              # Clear / Duplicate + a patch: the stock's gestures
    c.lab("pd_s")
    c.call("c_mzst"); E(mov_reg, 3, 0)
    E(ldrb_imm, 0, 3, O_ACT); E(cmp_reg, 0, 4); E(b_cond, "pd_off", "ne")
    E(cmp_imm, 6, 0); E(b_cond, "pd_y", "eq")                                               # the patches: other pads swallowed
    E(ldrb_imm, 0, 3, O_HP); E(cmp_imm, 0, 0); E(b_cond, "pd_1", "eq")
    c.now(0); E(str_imm, 0, 3, O_TP); E(movs_imm, 0, 2); E(b, "pd_2")                        # a second patch: no tap; the hold from now
    c.lab("pd_1"); E(strb_imm, 5, 3, O_PPAD); E(strb_imm, 7, 3, O_PG); E(ldr_sp, 0, 4); E(str_imm, 0, 3, O_PVIEW); E(ldr_sp, 0, 12)
    E(strb_imm, 0, 3, O_PVEL); c.now(0); E(str_imm, 0, 3, O_TP); E(movs_imm, 0, 1)
    c.lab("pd_2"); E(strb_imm, 0, 3, O_HP)
    c.lab("pd_y"); E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    c.lab("pd_off"); E(cmp_imm, 0, 0xFF); E(b_cond, "pd_n", "ne")
    E(cmp_imm, 6, 0); E(b_cond, "pd_n", "eq")
    E(push_list, [3]); c.call("c_mzheld"); E(pop_list, [3]); E(movs_imm, 1, 1); E(lsls_reg, 1, 5); E(bics_reg, 0, 1)
    E(cmp_imm, 0, 0); E(b_cond, "pd_rt", "ne")                                               # another patch held: not the first press
    E(strb_imm, 7, 3, O_PG); E(push_list, [5, 6]); E(mov_reg, 6, 3); c.call("c_mzsnap")
    E(movs_imm, 0, ARMED); E(strb_imm, 0, 6, O_HP); c.now(0); E(str_imm, 0, 6, O_TP); E(pop_list, [5, 6])   # the hold that opens the morph
    c.lab("pd_n"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)
    c.lab("pd_rt"); E(ldrb_imm, 0, 3, O_HP); E(cmp_imm, 0, ARMED); E(b_cond, "pd_n", "ne")     # armed: the 0.4 s from this press
    c.now(0); E(str_imm, 0, 3, O_TP); E(b, "pd_n")


@fn
def c_mzpadX(c):                         # slot 0 of both Preset views (view, pad, velocity): the synths' or the template's by the view's vtable
    E = c.E; E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    c.call("c_mzst"); E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, O_ACT); E(cmp_imm, 4, 3); E(b_cond, "px_v", "hi")
    c.call("c_mzmv"); E(cmp_imm, 0, 0); E(b_cond, "px_v", "eq")
    for p in TRIG: E(cmp_imm, 5, p); E(b_cond, "px_env", "eq")                              # the morph view: pads 1 / 8, 32; the rest nothing
    E(cmp_imm, 5, P_OUT); E(b_cond, "px_y", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, O_ACT); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP)
    E(cmp_imm, 4, 2); E(b_cond, "px_y", "hs"); E(movs_imm, 0, 0); c.call("c_mzsrc"); E(b, "px_y")   # synth: back to the patches
    c.lab("px_env"); E(movw, 0, 0xFFFF); E(strh_imm, 0, 6, O_ENV)
    c.lab("px_y"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    c.lab("px_v"); E(ldr_sp, 0, 0)
    c.call("c_mzsp"); E(b_cond, "px_o", "ne")
    c.call("c_pson"); E(cmp_imm, 0, 1); E(b_cond, "px_p", "hi"); E(mov_reg, 4, 0)
    E(movs_imm, 6, 0); E(cmp_imm, 5, 32); E(b_cond, "px_c", "hs")
    E(ldr_sp, 0, 0); E(ldr_imm, 0, 0, 0x20); E(movs_imm, 1, 0); c.call(PK.PARAM_GET); E(ldrb_imm, 7, 0, 0); E(movs_imm, 6, 1); E(b, "px_c")
    c.lab("px_o")
    c.call("c_mpon"); E(cmp_imm, 0, 1); E(b_cond, "px_p", "hi"); E(adds_imm3, 4, 0, 2)
    E(movs_imm, 6, 0); E(cmp_imm, 5, 8); E(b_cond, "px_c", "lo"); E(cmp_imm, 5, 23); E(b_cond, "px_c", "hi")
    c.call("c_mzvon"); E(cmp_imm, 0, 0); E(b_cond, "px_c", "eq")
    c.call("c_mpc"); E(cmp_imm, 0, 0); E(b_cond, "px_c", "eq"); E(ldrb_imm, 7, 0, 3); E(movs_imm, 6, 1)
    c.lab("px_c"); c.call("c_mzpad"); E(cmp_imm, 0, 0); E(b_cond, "px_p", "eq")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    c.lab("px_p"); E(ldr_sp, 0, 0); c.call("c_mzsp"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_cond, "px_n", "eq"); E(b_w, c.prev["opad"])
    c.lab("px_n"); E(b_w, c.prev["npad"])


@fn
def c_mzrelX(c):                         # slot 1 of both (view, pad): a tap of a single patch in the patches = that patch loaded (its press below us), the morph out
    E = c.E; E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    c.call("c_mzst"); E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, O_ACT)
    E(ldrb_imm, 0, 6, O_SHOW); E(cmp_imm, 0, 0); E(b_cond, "rx_p", "ne")
    E(ldrb_imm, 0, 6, O_HP); E(cmp_imm, 0, 1); E(b_cond, "rx_p", "ne")
    E(ldrb_imm, 0, 6, O_PPAD); E(cmp_reg, 0, 5); E(b_cond, "rx_p", "ne")
    E(mov_reg, 0, 4); c.call("c_mzon"); E(cmp_imm, 0, 0); E(b_cond, "rx_p", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, O_ACT)
    E(ldr_imm, 0, 6, O_PVIEW); c.call("c_mzsp"); E(ldr_imm, 0, 6, O_PVIEW); E(mov_reg, 1, 5); E(ldrb_imm, 2, 6, O_PVEL)
    E(b_cond, "rx_n", "eq"); c.call(c.prev["opad"]); E(b, "rx_p")
    c.lab("rx_n"); c.call(c.prev["npad"])
    c.lab("rx_p"); E(ldr_sp, 0, 0); c.call("c_mzsp"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_cond, "rx_nn", "eq"); E(b_w, c.prev["orel"])
    c.lab("rx_nn"); E(b_w, c.prev["nrel"])


@fn
def c_mzbtn(c):                          # the controller's button press, the head (ctrl, id)
    E = c.E; E(push_list, [0, 1, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    c.call("c_mzst"); E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, O_ACT)
    E(cmp_imm, 5, ID_PRESET); E(b_cond, "bt_np0", "ne")
    c.call("c_shift"); E(cmp_imm, 0, 0); c.bc("bt_p", "ne")
    c.call("c_pson"); E(cmp_imm, 0, 1); E(b_cond, "bt_pm", "hi")
    E(cmp_reg, 0, 4); E(b_cond, "bt_s2", "eq"); E(movs_imm, 0, 1); E(b, "bt_s")          # a synth's Preset view: Preset again = its alternative view
    c.lab("bt_s2"); E(movs_imm, 0, 2)                                                       # (the morphed synth's: the morph view)
    c.lab("bt_s"); c.call("c_mzsrc"); E(b, "bt_y")
    c.lab("bt_pm"); E(cmp_imm, 4, 2); c.bc("bt_p", "lo"); E(cmp_imm, 4, 3); c.bc("bt_p", "hi")
    c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "bt_pe", "ne")
    E(ldrb_imm, 0, 6, O_SHOW); E(cmp_imm, 0, 0); E(b_cond, "bt_tg", "eq")                   # a Preset right after the track's button put up the
    c.now(0); E(ldr_imm, 1, 6, O_SHT); E(subs_reg, 0, 0, 1); E(cmp_imm, 0, 50); c.bc("bt_y", "lo")   # morph view (dblpress's Shift + track): kept
    c.lab("bt_tg"); E(ldrb_imm, 0, 6, O_SHOW); E(movs_imm, 1, 1); E(raw, h(0x4048)); E(strb_imm, 0, 6, O_SHOW)   # eors r0, r1: MIDI, the morph view <-> the patches
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP); E(b, "bt_y")
    c.lab("bt_pe"); c.now(0); E(ldr_imm, 1, 6, O_SHT); E(subs_reg, 0, 0, 1); E(cmp_imm, 0, 50); E(movs_imm, 0, 0); E(b_cond, "bt_pw", "hs")
    E(movs_imm, 0, 1)                                                                       # right after the track's button left the morph view: back to it
    c.lab("bt_pw"); E(strb_imm, 0, 6, O_SHOW); E(b, "bt_p")                                  # from another view: the patches
    c.lab("bt_np0")
    E(cmp_imm, 4, 0xFF); c.bc("bt_on", "eq")
    if CLR2:                                                                                # (CLR2) Clear in the morph view: the stock's, the view kept
        E(cmp_imm, 5, CLEAR); E(b_cond, "bt_ncl", "ne")
        c.call("c_mzmv"); E(cmp_imm, 0, 0); c.bc("bt_p", "eq")
        E(ldr_sp, 0, 0); E(mov_reg, 1, 5); c.call(c.prev["btn"])
        c.call("c_mzmv"); E(cmp_imm, 0, 0); c.bc("bt_y", "ne")
        E(cmp_imm, 4, 2); c.bc("bt_y", "hs")
        E(movs_imm, 0, 2); c.call("c_mzsrc"); E(b, "bt_y")
        c.lab("bt_ncl")
    E(cmp_imm, 5, DUP); E(b_cond, "bt_nd", "ne")
    c.call("c_mzmv"); E(cmp_imm, 0, 0); c.bc("bt_y", "ne"); E(b, "bt_p")             # Duplicate: nothing in the morph view
    c.lab("bt_nd")
    E(cmp_reg, 5, 4); E(b_cond, "bt_trk", "eq")
    E(cmp_imm, 5, ID_DOWN); E(b_cond, "bt_oc", "eq"); E(cmp_imm, 5, ID_UP); c.bc("bt_p", "ne")
    c.lab("bt_oc")                                                                          # Octave in the morph view: the initial patch's place
    c.call("c_mzmv"); E(cmp_imm, 0, 0); c.bc("bt_p", "eq")
    if NOCUR: E(b, "bt_y")                                                                  # (NOCUR) no initial patch in the chain: nothing
    c.call("c_mzpos"); E(mov_reg, 1, 0)                                                    # r1 = p, r2 = n - 1
    E(cmp_imm, 5, ID_UP); E(b_cond, "bt_dn", "ne"); E(cmp_reg, 1, 2); c.bc("bt_y", "hs"); E(adds_imm3, 3, 1, 1); E(b, "bt_sw")
    c.lab("bt_dn"); E(cmp_imm, 1, 0); c.bc("bt_y", "eq"); E(mov_reg, 3, 1); E(subs_imm8, 3, 1)
    c.lab("bt_sw"); E(adds_reg, 1, 6, 1); E(adds_reg, 3, 6, 3); E(ldrb_imm, 0, 1, O_ORD); E(ldrb_imm, 2, 3, O_ORD)
    E(strb_imm, 2, 1, O_ORD); E(strb_imm, 0, 3, O_ORD); E(b, "bt_y")
    c.lab("bt_trk")                                                                         # the morphed track's button: from its morph view the stock,
    if CLR2:                                                                                # (CLR2) Clear + the track in the morph view: the knobs to 0
        c.call("c_mzmv"); E(cmp_imm, 0, 0); E(b_cond, "bt_tk0", "eq")
        c.call("c_mzcd"); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "bt_tk0", "eq")
        E(movs_imm, 0, 0)
        for k in range(8): E(strb_imm, 0, 6, O_K + k)
        if SLOW: c.imm32(1, SL); E(strb_imm, 0, 1, 0)
        E(b, "bt_y")
        c.lab("bt_tk0")
    c.call("c_shift"); E(cmp_imm, 0, 0); c.bc("bt_p", "ne")                                  # from anywhere else the stock, then the morph view
    c.call("c_mzmv"); E(cmp_imm, 0, 0); E(b_cond, "bt_k", "eq")
    c.now(0); E(str_imm, 0, 6, O_SHT); E(b, "bt_p")                                          # leaving the morph view: the time (bt_pe)
    c.lab("bt_k"); c.call("c_mzkey"); E(mov_reg, 7, 0)
    E(ldr_sp, 0, 0); E(mov_reg, 1, 5); c.call(c.prev["btn"])
    c.call("c_mzkey"); E(cmp_reg, 0, 7); c.bc("bt_y", "eq")                                 # the press used by the chain (split, Clear ...): nothing more
    E(movs_imm, 1, 9); E(muls, 1, 4); E(cmp_reg, 0, 1); c.bc("bt_y", "lo"); E(adds_imm8, 1, 9); E(cmp_reg, 0, 1); c.bc("bt_y", "hs")   # not t's view
    c.call("c_mzcd"); E(cmp_imm, 0, 0); c.bc("bt_y", "ne")
    c.call("c_mzshow"); E(b, "bt_y")
    c.lab("bt_on")                                                                          # off: Duplicate with patches held = on
    E(cmp_imm, 5, DUP); c.bc("bt_p", "ne")
    E(ldrb_imm, 0, 6, O_HP); E(cmp_imm, 0, ARMED); c.bc("bt_p", "ne")                       # the patches pressed for this gesture
    E(ldrb_imm, 4, 6, O_SNAP); E(cmp_imm, 4, 3); c.bc("bt_p", "hi")
    E(mov_reg, 0, 4); c.call("c_mzon"); E(cmp_imm, 0, 0); c.bc("bt_p", "eq")
    c.call("c_mzheld"); E(cmp_imm, 0, 0); c.bc("bt_p", "eq")
    c.call("c_mzenter"); E(cmp_imm, 0, 0); c.bc("bt_p", "eq")
    c.lab("bt_y"); E(pop_list, [0, 1, 4, 5, 6, 7], pc=True)
    c.lab("bt_p"); E(raw, popw([0, 1, 4, 5, 6, 7], lr=True)); E(b_w, c.prev["btn"])


def off_jump(c, label, target):           # (r2, r3 free) the morph off (MZ's track byte above 3): straight on to target, nothing on the stack
    E = c.E; c.imm32(3, MZ); E(ldrb_imm, 2, 3, O_ACT); E(cmp_imm, 2, 3); E(b_cond, label, "ls")
    if isinstance(target, tuple):        # (the Preset views: by the view's vtable)
        E(ldr_imm, 2, 0, 0); c.imm32(3, c.SP); E(cmp_reg, 2, 3); E(b_cond, label + "n", "eq"); E(b_w, target[1])
        c.lab(label + "n"); E(b_w, target[0])
    else: E(b_w, target)
    c.lab(label)


def save(c, at):                          # (r0 = the argument; r2, r3 free) the argument and LR into SV + at
    E = c.E; c.imm32(2, SV + at); E(str_imm, 0, 2, 0); E(raw, mov_hi(3, 14)); E(str_imm, 3, 2, 4)


def restore_lr(c, at):                    # LR back from SV + at + 4 (r2, r3 free)
    E = c.E; c.imm32(2, SV + at); E(ldr_imm, 3, 2, 4); E(raw, mov_hi(14, 3))


@fn
def c_mzledX(c):                         # slot 7 of both Preset views (view) -> the buffer
    off_jump(c, "lx_on", (c.prev["nled"], c.prev["oled"]))
    E = c.E; save(c, 8)                                                                    # nothing on the stack while the view draws
    c.call("c_mzsp"); E(ldr_imm, 0, 2, 0); E(b_cond, "lx_o", "ne")
    c.call(c.prev["nled"]); E(b, "lx_c0")
    c.lab("lx_o"); c.call(c.prev["oled"])
    c.lab("lx_c0"); restore_lr(c, 8); E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 0)
    c.call("c_mzst"); E(mov_reg, 6, 0); E(ldrb_imm, 4, 6, O_ACT); E(cmp_imm, 4, 3); E(b_cond, "lx_x", "hi")
    c.call("c_mzmv"); E(cmp_imm, 0, 0); E(b_cond, "lx_pv", "eq")
    c.call("c_mzlb"); E(movs_imm, 0, 1); c.call("c_mzpl"); E(b, "lx_x")                       # the morph view
    c.lab("lx_pv"); E(cmp_imm, 4, 2); E(b_cond, "lx_m", "hs")                              # the patches of the morphed track: the chain in white
    c.call("c_pson"); E(cmp_reg, 0, 4); E(b_cond, "lx_x", "ne")
    c.imm32(0, SV + 8); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x20); E(movs_imm, 1, 0); c.call(PK.PARAM_GET); E(ldrb_imm, 7, 0, 0); E(lsls_imm, 7, 7, 5)
    E(b, "lx_w")
    c.lab("lx_m"); c.call("c_mpon"); E(adds_imm8, 0, 2); E(cmp_reg, 0, 4); E(b_cond, "lx_x", "ne")
    E(ldrb_imm, 0, 6, O_SHOW); E(cmp_imm, 0, 0); E(b_cond, "lx_x", "ne")
    c.call("c_mpc"); E(movs_imm, 7, 0); E(cmp_imm, 0, 0); E(b_cond, "lx_0", "eq"); E(ldrb_imm, 7, 0, 3)
    c.lab("lx_0"); E(lsls_imm, 7, 7, 4); E(subs_imm8, 7, 8)
    c.lab("lx_w"); c.call("c_mzlb"); E(movs_imm, 0, 0); c.call("c_mzpl")
    c.lab("lx_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)


@fn
def c_mzpl(c):                           # (r0 = 1 the morph view / 0 the chain's patches in white; r4 = t, r5 = the buffer, r6 = MZ, r7 = slot - pad); clobbers r0-r3
    E = c.E; E(push_list, [], lr=True)
    E(cmp_imm, 0, 0); E(b_cond, "pl_pat", "eq")
    E(movs_imm, 0, 0); E(movs_imm, 1, 0)
    c.lab("pl_z"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 64); E(b_cond, "pl_z", "lo")
    c.call("c_mzcol"); E(ldrh_imm, 2, 6, O_ENV); E(cmp_imm, 2, 0); E(b_cond, "pl_e", "ne"); E(mov_reg, 0, 1)
    c.lab("pl_e")
    for p in TRIG: E(strh_imm, 0, 5, 2 * p)
    E(movs_imm, 0, RED); E(strh_imm, 0, 5, 2 * P_OUT); E(b, "pl_x")
    c.lab("pl_pat"); E(movs_imm, 2, 1)
    c.lab("pl_l"); E(ldrb_imm, 3, 6, O_N); E(cmp_reg, 2, 3); E(b_cond, "pl_x", "hs")
    E(adds_reg, 0, 6, 2); E(ldrb_imm, 0, 0, O_SL - 1); E(subs_reg, 0, 0, 7)
    E(cmp_imm, 4, 2); E(b_cond, "pl_s", "lo"); E(subs_imm8, 0, 8); E(cmp_imm, 0, 15); E(b_cond, "pl_n", "hi"); E(adds_imm8, 0, 8); E(b, "pl_w")
    c.lab("pl_s"); E(cmp_imm, 0, 31); E(b_cond, "pl_n", "hi")
    c.lab("pl_w"); E(lsls_imm, 0, 0, 1); E(movs_imm, 1, WHITE); E(strh_reg, 1, 5, 0)
    c.lab("pl_n"); E(adds_imm8, 2, 1); E(b, "pl_l")
    c.lab("pl_x"); E(pop_list, [], pc=True)


@fn
def c_mzobj(c):                          # (r0 = a macro handler) -> r0 = MZ when it is the morphed track's, 0 otherwise; r4 = t; clobbers r1-r3
    E = c.E; E(push_list, [5], lr=True); E(mov_reg, 5, 0); c.call("c_mzst"); E(ldrb_imm, 4, 0, O_ACT); E(cmp_imm, 4, 3); E(b_cond, "ob_n", "hi")
    c.imm32(1, CTX); E(ldr_imm, 1, 1, 0); E(ldr_imm, 1, 1, 0x40); E(ldr_imm, 1, 1, 0x2C)
    E(lsls_imm, 3, 4, 2); E(adds_reg, 1, 1, 3); E(movw, 3, 0x148); E(raw, h(0x58C9)); E(cmp_reg, 1, 5); E(b_cond, "ob_x", "eq")   # ldr r1, [r1, r3]
    c.lab("ob_n"); E(movs_imm, 0, 0)
    c.lab("ob_x"); E(pop_list, [5], pc=True)


@fn
def c_mzknob(c):                         # slot 4 of the macro handlers (obj, knob, delta)
    E = c.E; E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    c.call("c_mzobj"); E(cmp_imm, 0, 0); E(b_cond, "kn_p", "eq"); E(mov_reg, 6, 0)
    E(ldr_sp, 5, 4); E(movs_imm, 0, 7); E(ands_reg, 5, 0); E(adds_reg, 7, 6, 5); E(adds_imm8, 7, O_K)   # r7 = the knob's byte
    if SLOW:                                                                                # (SLOW) K1 while gliding: from the glide's place, the glide off
        E(cmp_imm, 5, 0); E(b_cond, "kn_g", "ne"); c.imm32(0, SL); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 2); E(tst_reg, 1, 2); E(b_cond, "kn_g", "eq")
        E(bics_reg, 1, 2); E(strb_imm, 1, 0, 0); E(ldr_imm, 1, 0, 24); E(lsrs_imm, 1, 1, 8); E(strb_imm, 1, 7, 0)
        c.lab("kn_g")
    c.call("c_mxclrh"); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "kn_w", "ne")                       # Clear + knob = 0
    E(ldr_sp, 2, 8); E(movs_imm, 0, UNI); E(lsrs_reg, 0, 5); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "kn_u", "ne")
    E(movs_imm, 0, 0); E(raw, ldrsb_reg(1, 7, 0)); E(adds_reg, 1, 1, 2); E(movs_imm, 0, 63); E(cmp_reg, 1, 0); E(b_cond, "kn_b1", "le"); E(mov_reg, 1, 0)
    c.lab("kn_b1"); E(movs_imm, 0, 0); E(subs_imm8, 0, 64); E(cmp_reg, 1, 0); E(b_cond, "kn_w", "ge"); E(mov_reg, 1, 0); E(b, "kn_w")
    c.lab("kn_u"); E(ldrb_imm, 1, 7, 0); E(adds_reg, 1, 1, 2); E(b_cond, "kn_u1", "pl"); E(movs_imm, 1, 0)
    c.lab("kn_u1"); E(cmp_imm, 1, 127); E(b_cond, "kn_w", "le"); E(movs_imm, 1, 127)
    c.lab("kn_w"); E(strb_imm, 1, 7, 0)
    if SLOW:                                                                                # (SLOW) K5 turned: aimed, the time
        E(cmp_imm, 5, 4); E(b_cond, "kn_x", "ne"); c.imm32(0, SL); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 1); E(orrs_reg, 1, 2); E(strb_imm, 1, 0, 0)
        c.now(1); E(str_imm, 1, 0, 16)
        c.lab("kn_x")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    c.lab("kn_p"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, c.prev["knob"])


@fn
def c_mzkled(c):                         # slot 7 of the macro handlers (obj) -> the buffer: the track's colour, the brightness = the value (depths: the distance from 0)
    off_jump(c, "kl_on", c.prev["kled"])
    E = c.E; save(c, 16); c.call(c.prev["kled"])                                           # nothing on the stack while the handler draws
    restore_lr(c, 16); E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 0)
    c.imm32(0, SV + 16); E(ldr_imm, 0, 0, 0); c.call("c_mzobj"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq"); E(mov_reg, 6, 0)
    c.imm32(0, KLB); E(mov_reg, 1, 5); E(movs_imm, 2, KLBN); c.call("c_mzcpy"); c.imm32(5, KLB)   # into a copy
    c.call("c_mzcol"); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(mov_reg, 4, 0)       # r4 = the colour
    E(movs_imm, 7, 0)
    c.lab("kl_l"); E(adds_reg, 1, 6, 7); E(adds_imm8, 1, O_K)
    E(movs_imm, 0, UNI); E(lsrs_reg, 0, 7); E(movs_imm, 2, 1); E(tst_reg, 0, 2); E(b_cond, "kl_u", "ne")
    E(movs_imm, 0, 0); E(raw, ldrsb_reg(0, 1, 0)); E(cmp_imm, 0, 0); E(b_cond, "kl_pp", "ge"); E(raw, h(0x4240))   # rsbs r0, r0
    c.lab("kl_pp"); E(lsls_imm, 0, 0, 1); E(b, "kl_c")
    c.lab("kl_u"); E(ldrb_imm, 0, 1, 0)
    c.lab("kl_c"); E(adds_imm8, 0, 2); E(cmp_imm, 0, 127); E(b_cond, "kl_m", "le"); E(movs_imm, 0, 127)
    c.lab("kl_m"); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 4); E(lsls_imm, 1, 7, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "kl_l", "lo")
    if SLOW:                                                                                # (SLOW) K1 (the glide's place while gliding) / K5: their patch's colour
        c.imm32(0, SL); E(ldrb_imm, 1, 0, 0); E(movs_imm, 2, 2); E(tst_reg, 1, 2); E(b_cond, "kl_k1", "eq"); E(ldr_imm, 0, 0, 24); E(b, "kl_kc")
        c.lab("kl_k1"); E(ldrb_imm, 0, 6, O_K); E(lsls_imm, 0, 0, 8)
        c.lab("kl_kc"); c.call("c_mzgc"); E(movs_imm, 1, 127); E(lsls_imm, 1, 1, 8); E(orrs_reg, 0, 1); E(strh_imm, 0, 5, 0)
        E(ldrb_imm, 0, 6, O_K + 4); E(lsls_imm, 0, 0, 8); c.call("c_mzgc"); E(movs_imm, 1, 127); E(lsls_imm, 1, 1, 8); E(orrs_reg, 0, 1); E(strh_imm, 0, 5, 8)
    c.lab("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)


@fn
def c_mzfill(c):                         # (r4 = t, r6 = MZ): one uncached link read -> r0 = 1 when one was read; clobbers r0-r3, r5, r7
    E = c.E; E(push_list, [], lr=True)
    E(ldrb_imm, 0, 6, O_CV); E(ldrb_imm, 1, 6, O_N); E(movs_imm, 5, 1)
    c.lab("fl_f"); E(cmp_reg, 5, 1); E(b_cond, "fl_0", "hs"); E(movs_imm, 2, 1)
    if FOUR: E(movs_imm, 3, 3); E(ands_reg, 3, 5); E(lsls_reg, 2, 3)                       # (FOUR) entry 4 = cache 0
    else: E(lsls_reg, 2, 5)
    E(tst_reg, 0, 2); E(b_cond, "fl_go", "eq")
    E(adds_imm8, 5, 1); E(b, "fl_f")
    c.lab("fl_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)
    c.lab("fl_go"); E(orrs_reg, 0, 2); E(strb_imm, 0, 6, O_CV)
    E(movs_imm, 0, 5); c.call(PK.BUF_LOCK)
    E(adds_reg, 0, 6, 5); E(ldrb_imm, 7, 0, O_SL - 1)                                      # r7 = the slot / patch
    if FOUR: E(movs_imm, 0, 3); E(ands_reg, 5, 0)                                          # r5 = the cache index
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)                     # the bank, 512 (slot & 7)
    E(cmp_imm, 4, 2); E(b_cond, "fl_own", "hs")
    c.imm32(2, PK.BUF); E(movw, 3, 340); c.call("c_mpr")
    E(movw, 0, NOVA_LEN); E(muls, 0, 5); c.imm32(1, CC); E(adds_reg, 0, 0, 1); c.imm32(1, PK.BUF + 30); E(movw, 2, NOVA_LEN); E(b, "fl_cp")
    c.lab("fl_own")
    E(push_list, [0, 1]); c.imm32(2, MP.OFF); E(adds_reg, 1, 1, 2); c.imm32(2, PK.BUF); E(movs_imm, 3, 40); c.call("c_mpr")
    E(movw, 0, NOVA_LEN); E(muls, 0, 5); c.imm32(1, CC); E(adds_reg, 0, 0, 1)
    c.imm32(1, PK.BUF); E(ldr_imm, 2, 1, 0); c.imm32(3, MP.MAGIC4); E(cmp_reg, 2, 3); E(b_cond, "fl_ok", "eq")
    c.imm32(1, CC - 6)                                                                      # an empty slot: the initial patch's codes
    c.lab("fl_ok"); E(adds_imm8, 1, 6); E(movs_imm, 2, 34); c.call("c_mzcpy")
    E(pop_list, [0, 1]); c.imm32(2, 4096); E(adds_reg, 1, 1, 2); c.imm32(2, PK.BUF); E(movs_imm, 3, FM_LEN + 4); c.call("c_mpr")
    c.imm32(1, PK.BUF); E(ldr_imm, 2, 1, 0); c.imm32(3, 0x01384D46); E(cmp_reg, 2, 3); E(b_cond, "fl_u", "ne")
    E(movs_imm, 2, 16); E(lsls_reg, 2, 5); E(ldrb_imm, 3, 6, O_CV); E(orrs_reg, 3, 2); E(strb_imm, 3, 6, O_CV)
    E(movs_imm, 0, FM_LEN); E(muls, 0, 5); c.imm32(2, FC); E(adds_reg, 0, 0, 2); E(adds_imm8, 1, 4); E(movs_imm, 2, FM_LEN)
    c.lab("fl_cp"); c.call("c_mzcpy")
    c.lab("fl_u"); c.call(PK.BUF_UNLOCK); E(movs_imm, 0, 1); E(pop_list, [], pc=True)


@fn
def c_mzlfo(c):                          # (r0 = the phase's address, r1 = rate 0..127, r5 = dt) -> r0 = the phase (u16), r1 = 1 when it wrapped; clobbers r2
    E = c.E
    E(adds_imm8, 1, 1); E(muls, 1, 1); E(adds_imm8, 1, 16); E(muls, 1, 5); E(lsrs_imm, 1, 1, 4)
    E(ldrh_imm, 2, 0, 0); E(adds_reg, 2, 2, 1); E(strh_imm, 2, 0, 0)
    E(lsrs_imm, 1, 2, 16); E(lsls_imm, 0, 2, 16); E(lsrs_imm, 0, 0, 16); E(raw, RET)


@fn
def c_mzdep(c):                          # (r0 = a modulator -128..128, r1 = its knob's offset, r6 = MZ) -> r7 += it x the depth; clobbers r1
    E = c.E; E(raw, ldrsb_reg(1, 6, 1)); E(muls, 0, 1); E(adds_reg, 7, 7, 0); E(raw, RET)


@fn
def c_mzpanel(c):                        # (r4 = t, r6 = MZ, r3 = the frame; clobbers r0-r3, r7): Octave down / up in the track's colour when the initial patch can move
    E = c.E; E(push_list, [], lr=True)
    c.call("c_mzcol"); E(mov_reg, 7, 0); c.call("c_mzpos"); E(adds_imm8, 3, 2 * LED_DOWN)   # r7 = the colour, r0 = p, r2 = n - 1
    E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "pn_1", "eq"); E(mov_reg, 1, 7)
    c.lab("pn_1"); E(strh_imm, 1, 3, 0)
    E(movs_imm, 1, 0); E(cmp_reg, 0, 2); E(b_cond, "pn_2", "hs"); E(mov_reg, 1, 7)
    c.lab("pn_2"); E(strh_imm, 1, 3, 2 * (LED_UP - LED_DOWN))
    E(pop_list, [], pc=True)


@fn
def c_mzhold(c):                         # (r4 = t, r6 = MZ): patches held 0.4 s in the patches view = the chain anew; clobbers r0-r3, r5, r7
    E = c.E; E(push_list, [], lr=True)
    E(ldrb_imm, 0, 6, O_HP); E(cmp_imm, 0, 0); E(b_cond, "hl_x", "eq")
    E(mov_reg, 0, 4); c.call("c_mzon"); E(cmp_imm, 0, 0); E(b_cond, "hl_c", "eq")
    E(ldrb_imm, 0, 6, O_SHOW); E(cmp_imm, 0, 0); E(b_cond, "hl_c", "ne")
    c.call("c_mzheld"); E(cmp_imm, 0, 0); E(b_cond, "hl_s", "ne")
    E(ldrb_imm, 1, 6, O_HP); E(cmp_imm, 1, 1); E(b_cond, "hl_x", "eq")                     # a single tap waits for its release
    c.lab("hl_c"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP); E(b, "hl_x")
    c.lab("hl_s"); E(ldrb_imm, 1, 6, O_HP); E(cmp_imm, 1, 3); E(b_cond, "hl_x", "eq")
    E(mov_reg, 7, 0); c.now(1); E(ldr_imm, 2, 6, O_TP); E(subs_reg, 1, 1, 2); E(movw, 2, HOLD_MS); E(cmp_reg, 1, 2); E(b_cond, "hl_x", "lo")
    E(mov_reg, 0, 7); E(subs_imm3, 1, 0, 1); E(raw, h(0x4208)); E(b_cond, "hl_x", "eq")                     # two held at least
    c.call("c_mzcd"); E(movs_imm, 1, 3); E(strb_imm, 1, 6, O_HP); E(cmp_imm, 0, 0); E(b_cond, "hl_x", "ne")   # a Clear / Duplicate gesture: the hold used
    E(mov_reg, 0, 7); c.call("c_mzchain")                                                   # up (no tap, no chain until all are let go)
    c.lab("hl_x"); E(pop_list, [], pc=True)


@fn
def c_mzmod(c):                          # (r4 = t, r5 = dt, r6 = MZ) -> r0 = the position 0..32512; clobbers r1-r3, r7
    E = c.E; E(push_list, [], lr=True)
    if SLOW: return mod_slow(c)
    E(movs_imm, 7, 0)
    E(mov_reg, 0, 6); E(adds_imm8, 0, O_PH1); E(ldrb_imm, 1, 6, O_K + 2); c.call("c_mzlfo")
    E(lsrs_imm, 0, 0, 8); E(subs_imm8, 0, 128); E(b_cond, "md_a", "pl"); E(raw, h(0x4240))
    c.lab("md_a"); E(lsls_imm, 0, 0, 1); E(subs_imm8, 0, 128); E(movs_imm, 1, O_K + 1); c.call("c_mzdep")
    E(mov_reg, 0, 6); E(adds_imm8, 0, O_PH2); E(ldrb_imm, 1, 6, O_K + 4); c.call("c_mzlfo"); E(cmp_imm, 1, 0); E(b_cond, "md_s2", "eq")
    c.call("c_mzrnd"); E(strb_imm, 0, 6, O_S2)
    c.lab("md_s2"); E(movs_imm, 0, O_S2); E(raw, ldrsb_reg(0, 6, 0)); E(movs_imm, 1, O_K + 3); c.call("c_mzdep")
    E(lsls_imm, 0, 4, 2); c.imm32(1, STORE + 0x30); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 1); c.call(PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(ldrb_imm, 1, 6, O_LS); E(cmp_reg, 0, 1); E(b_cond, "md_st", "eq"); E(strb_imm, 0, 6, O_LS); c.call("c_mzrnd"); E(strb_imm, 0, 6, O_RS)
    c.lab("md_st"); E(movs_imm, 0, O_RS); E(raw, ldrsb_reg(0, 6, 0)); E(movs_imm, 1, O_K + 5); c.call("c_mzdep")
    E(ldrb_imm, 1, 6, O_K + 7); E(movs_imm, 0, 129); E(subs_reg, 1, 0, 1); E(muls, 1, 1); E(lsrs_imm, 1, 1, 2); E(adds_imm8, 1, 16); E(muls, 1, 5)
    if SUS:                                                                               # (SUS) pad 1 / 8 held in the morph view: the envelope stays
        E(push_list, [1]); c.call("c_mzmv"); E(mov_reg, 2, 0); E(pop_list, [1]); E(cmp_imm, 2, 0); E(b_cond, "md_ns", "eq")
        c.imm32(2, MP.MGR + 0x84); E(ldr_imm, 2, 2, 0); E(movs_imm, 3, sum(1 << q for q in TRIG)); E(tst_reg, 2, 3); E(b_cond, "md_ns", "eq"); E(movs_imm, 1, 0)
        c.lab("md_ns")
    E(ldrh_imm, 0, 6, O_ENV); E(subs_reg, 0, 0, 1); E(b_cond, "md_e", "pl"); E(movs_imm, 0, 0)
    c.lab("md_e"); E(strh_imm, 0, 6, O_ENV); E(lsrs_imm, 0, 0, 9); E(movs_imm, 1, O_K + 6); c.call("c_mzdep")
    E(ldrb_imm, 0, 6, O_K); E(lsls_imm, 0, 0, 8); E(lsls_imm, 7, 7, 2); E(adds_reg, 0, 0, 7)        # K1 << 8 + 4 x the sum, clamped
    E(b_cond, "md_c0", "pl"); E(movs_imm, 0, 0)
    c.lab("md_c0"); E(movw, 1, 127 * 256); E(cmp_reg, 0, 1); E(b_cond, "md_c1", "le"); E(mov_reg, 0, 1)
    c.lab("md_c1"); E(pop_list, [], pc=True)


def mod_slow(c):                         # (SLOW) c_mzmod: LFO 1 square / LFO 2 random at its halves (K3), slewed by K8's rate; the envelope; the glide's base
    E = c.E; E(movs_imm, 7, 0)
    E(ldrb_imm, 1, 6, O_K + 7); E(movs_imm, 0, 129); E(subs_reg, 1, 0, 1); E(muls, 1, 1); E(lsrs_imm, 1, 1, 2); E(adds_imm8, 1, 16); E(muls, 1, 5)
    E(push_list, [1])                                                                       # [sp] = the rate (the envelope's fall = the slew)
    E(mov_reg, 0, 6); E(adds_imm8, 0, O_PH1); E(ldrb_imm, 1, 6, O_K + 2); c.call("c_mzlfo"); E(lsrs_imm, 0, 0, 15)   # r0 = the half
    c.imm32(3, SL); E(ldrb_imm, 1, 3, 1); E(cmp_reg, 0, 1); E(b_cond, "ms_h", "eq")
    E(strb_imm, 0, 3, 1); c.call("c_mzrnd"); E(lsls_imm, 0, 0, 8); c.imm32(3, SL); E(str_imm, 0, 3, 12)    # a new random target
    c.lab("ms_h"); c.imm32(3, SL); E(ldrb_imm, 0, 3, 1); E(movw, 1, 0x7FFF); E(cmp_imm, 0, 0); E(b_cond, "ms_t", "eq"); E(movs_imm, 1, 1)
    E(lsls_imm, 1, 1, 15); E(raw, h(0x4249))                                                # rsbs r1, r1: -32768
    c.lab("ms_t"); E(ldr_sp, 3, 0); c.imm32(0, SL + 4); c.call("c_mzslw"); E(movs_imm, 1, O_K + 1); c.call("c_mzdep")
    c.imm32(0, SL + 12); E(ldr_imm, 1, 0, 0); E(subs_imm8, 0, 4); E(ldr_sp, 3, 0); c.call("c_mzslw"); E(movs_imm, 1, O_K + 3); c.call("c_mzdep")
    E(pop_list, [1])
    if SUS:                                                                               # (SUS) pad 1 / 8 held in the morph view: the envelope stays
        E(push_list, [1]); c.call("c_mzmv"); E(mov_reg, 2, 0); E(pop_list, [1]); E(cmp_imm, 2, 0); E(b_cond, "ms_ns", "eq")
        c.imm32(2, MP.MGR + 0x84); E(ldr_imm, 2, 2, 0); E(movs_imm, 3, sum(1 << q for q in TRIG)); E(tst_reg, 2, 3); E(b_cond, "ms_ns", "eq"); E(movs_imm, 1, 0)
        c.lab("ms_ns")
    E(ldrh_imm, 0, 6, O_ENV); E(subs_reg, 0, 0, 1); E(b_cond, "ms_e", "pl"); E(movs_imm, 0, 0)
    c.lab("ms_e"); E(strh_imm, 0, 6, O_ENV); E(lsrs_imm, 0, 0, 9); E(movs_imm, 1, O_K + 6); c.call("c_mzdep")
    c.call("c_mzslow"); E(lsls_imm, 7, 7, 2); E(adds_reg, 0, 0, 7)                        # the base + 4 x the sum, clamped
    E(b_cond, "ms_c0", "pl"); E(movs_imm, 0, 0)
    c.lab("ms_c0"); E(movw, 1, 127 * 256); E(cmp_reg, 0, 1); E(b_cond, "ms_c1", "le"); E(mov_reg, 0, 1)
    c.lab("ms_c1"); E(pop_list, [], pc=True)


@fn
def c_mzslw(c):                          # (SLOW; r0 = a value's address (word), r1 = its target, r3 = the step) -> r0 = the value >> 8; clobbers r2
    E = c.E; E(ldr_imm, 2, 0, 0); E(cmp_reg, 2, 1); E(b_cond, "sw_d", "ge")
    E(adds_reg, 2, 2, 3); E(cmp_reg, 2, 1); E(b_cond, "sw_s", "le"); E(mov_reg, 2, 1); E(b, "sw_s")
    c.lab("sw_d"); E(subs_reg, 2, 2, 3); E(cmp_reg, 2, 1); E(b_cond, "sw_s", "ge"); E(mov_reg, 2, 1)
    c.lab("sw_s"); E(str_imm, 2, 0, 0); E(raw, asrs(0, 2, 8)); E(raw, RET)


@fn
def c_mzslow(c):                         # (SLOW; r5 = dt, r6 = MZ) -> r0 = the base 0..32512: K1 or the glide's place; clobbers r1-r3
    E = c.E; E(push_list, [], lr=True)
    c.imm32(3, SL); E(ldrb_imm, 2, 3, 0)
    E(movs_imm, 0, 1); E(tst_reg, 2, 0); E(b_cond, "sl_a", "eq")                            # K5 aimed and at rest: the glide from where the sound is
    c.now(0); E(ldr_imm, 1, 3, 16); E(subs_reg, 0, 0, 1); E(movw, 1, AIM_MS); E(cmp_reg, 0, 1); E(b_cond, "sl_a", "lo")
    E(movs_imm, 0, 2); E(tst_reg, 2, 0); E(b_cond, "sl_k", "eq"); E(ldr_imm, 0, 3, 24); E(b, "sl_st")
    c.lab("sl_k"); E(ldrb_imm, 0, 6, O_K); E(lsls_imm, 0, 0, 8)
    c.lab("sl_st"); E(strh_imm, 0, 3, 2); E(str_imm, 0, 3, 24); E(movs_imm, 0, 0); E(str_imm, 0, 3, 20); E(movs_imm, 2, 2); E(strb_imm, 2, 3, 0)
    c.lab("sl_a"); E(movs_imm, 0, 2); E(tst_reg, 2, 0); E(b_cond, "sl_k1", "eq")
    E(ldrb_imm, 0, 6, O_K + 5); E(cmp_imm, 0, 0); E(b_cond, "sl_d", "eq")                   # K6 fully left: at once
    E(subs_imm8, 0, 1); E(movs_imm, 1, 18); E(raw, udiv(2, 0, 1)); E(muls, 1, 2); E(subs_reg, 0, 0, 1)   # r2 = the octave, r0 = the 18ths
    E(movs_imm, 1, 57); E(muls, 0, 1); c.imm32(1, 1024); E(adds_reg, 0, 0, 1); E(push_list, [0, 2])       # [sp] = 1024 x 2^(f / 18) (linear), [sp + 4] = e
    c.imm32(0, TEMPO); E(movs_imm, 1, 0); c.call(PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "sl_b", "ne"); E(movs_imm, 0, 120)
    c.lab("sl_b"); c.imm32(1, 240000); E(raw, udiv(1, 1, 0))                                # r1 = a bar in ms
    E(pop_list, [0, 2]); E(muls, 1, 0); E(lsrs_imm, 1, 1, 10); E(lsls_reg, 1, 2); E(lsrs_imm, 1, 1, 2)   # 1/4 bar x 2^(K6 / 18)
    E(cmp_imm, 1, 0); E(b_cond, "sl_n", "ne"); E(movs_imm, 1, 1)
    c.lab("sl_n"); E(lsls_imm, 0, 5, 24); E(raw, udiv(0, 0, 1)); c.imm32(3, SL); E(ldr_imm, 2, 3, 20); E(adds_reg, 2, 2, 0)
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 24); E(cmp_reg, 2, 0); E(b_cond, "sl_d", "hs"); E(str_imm, 2, 3, 20)
    E(ldrb_imm, 0, 6, O_K + 4); E(lsls_imm, 0, 0, 8); E(ldrh_imm, 1, 3, 2); E(subs_reg, 0, 0, 1); E(lsrs_imm, 2, 2, 8); E(muls, 0, 2)
    E(raw, asrs(0, 0, 16)); E(adds_reg, 0, 0, 1); E(str_imm, 0, 3, 24); E(pop_list, [], pc=True)
    c.lab("sl_d"); c.imm32(3, SL); E(ldrb_imm, 0, 6, O_K + 4); E(strb_imm, 0, 6, O_K); E(movs_imm, 0, 0); E(strb_imm, 0, 3, 0)   # there: K1 = K5
    c.lab("sl_k1"); E(ldrb_imm, 0, 6, O_K); E(lsls_imm, 0, 0, 8); E(pop_list, [], pc=True)


@fn
def c_mzgc(c):                           # (SLOW; r0 = a place 0..32512, r6 = MZ) -> r0 = its colour in the gradient (5 shades a link); clobbers r1, r2
    E = c.E; E(push_list, [], lr=True)
    E(ldrb_imm, 1, 6, O_N); E(subs_imm8, 1, 2); E(movs_imm, 2, 5); E(muls, 1, 2); E(muls, 0, 1); E(movw, 1, 127 * 256); E(raw, udiv(0, 0, 1))
    E(cmp_imm, 0, 15); E(b_cond, "gc_l", "ls"); E(movs_imm, 0, 15)
    c.lab("gc_l"); E(bl, "gc_t"); E(raw, GRAD)
    c.lab("gc_t"); E(raw, mov_hi(1, 14)); E(subs_imm8, 1, 1); E(ldrb_reg, 0, 1, 0); E(pop_list, [], pc=True)


@fn
def c_mzfm(c):                           # (r4 = t, r5 = f, r6 = MZ, r9 / r10 = the links' cache indices): the FM block when both carry one; clobbers r0-r4, r6, r7
    import fm8arm as A
    E = c.E; E(push_list, [], lr=True)
    c.imm32(7, A.FM8R + A.TB0 - 0x200); E(lsls_imm, 0, 4, 8); E(adds_reg, 7, 7, 0)          # r7 = the block
    E(movs_imm, 0, A.B_ON); E(ldrb_reg, 0, 7, 0); E(cmp_imm, 0, 1); E(b_cond, "fm_x", "ne")
    E(raw, mov_hi(2, 9)); E(raw, mov_hi(3, 10))                                             # r2 / r3 = the links' cache indices
    E(ldrb_imm, 0, 6, O_CV); E(lsrs_imm, 0, 0, 4); E(mov_reg, 1, 0); E(lsrs_reg, 0, 2); E(lsrs_reg, 1, 3); E(ands_reg, 0, 1)
    E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "fm_x", "eq")
    E(movs_imm, 0, FM_LEN); E(muls, 2, 0); E(muls, 3, 0); c.imm32(0, FC); E(adds_reg, 2, 2, 0); E(adds_reg, 3, 3, 0)
    E(raw, mov_hi(8, 2)); E(raw, mov_hi(11, 3))                                             # r8 = link i's FM, r11 = link i + 1's
    E(movs_imm, 4, 0); E(movs_imm, 3, 0)                                                    # r4 = changed, r3 = p
    c.lab("fm_l")
    E(raw, mov_hi(0, 8)); E(ldrb_reg, 1, 0, 3); E(raw, mov_hi(0, 11)); E(ldrb_reg, 2, 0, 3)   # r1 = A, r2 = B
    c.imm32(0, c.ext["t_disc"]); E(lsrs_imm, 6, 3, 3); E(ldrb_reg, 0, 0, 6); E(movs_imm, 6, 7); E(ands_reg, 6, 3); E(lsrs_reg, 0, 6)
    E(lsls_imm, 0, 0, 31); E(b_cond, "fm_c", "eq")
    E(cmp_imm, 5, 64); E(b_cond, "fm_v", "lo"); E(mov_reg, 1, 2); E(b, "fm_v")
    c.lab("fm_c"); E(subs_reg, 2, 2, 1); E(muls, 2, 5); E(raw, asrs(2, 2, 7)); E(adds_reg, 1, 1, 2)
    c.lab("fm_v"); E(ldrb_reg, 2, 7, 3); E(cmp_reg, 1, 2); E(b_cond, "fm_n", "eq"); E(strb_reg, 1, 7, 3); E(movs_imm, 4, 1)
    c.lab("fm_n"); E(adds_imm8, 3, 1); E(cmp_imm, 3, FM_LEN); E(b_cond, "fm_l", "lo")
    E(cmp_imm, 4, 0); E(b_cond, "fm_x", "eq"); E(movs_imm, 0, 1); E(movs_imm, 1, A.B_DIRTY); E(strb_reg, 0, 7, 1)
    c.lab("fm_x"); E(pop_list, [], pc=True)


@fn
def c_mzown(c):                          # (r4 = t, r5 = f, r8 / r11 = the links' caches): MIDI 1 / 2's codes 1..34; clobbers r0-r3, r7
    E = c.E; E(push_list, [], lr=True)
    E(movs_imm, 7, 1)
    c.lab("ow_l")
    E(raw, mov_hi(0, 8)); E(adds_reg, 0, 0, 7); E(subs_imm8, 0, 1); E(movs_imm, 1, 0); E(raw, ldrsb_reg(2, 0, 1))
    E(raw, mov_hi(0, 11)); E(adds_reg, 0, 0, 7); E(subs_imm8, 0, 1); E(raw, ldrsb_reg(3, 0, 1))
    for c_ in DISC_OWN: E(cmp_imm, 7, c_); E(b_cond, "ow_d", "eq")
    E(subs_reg, 3, 3, 2); E(muls, 3, 5); E(raw, asrs(3, 3, 7)); E(adds_reg, 2, 2, 3); E(b, "ow_s")
    c.lab("ow_d"); E(cmp_imm, 5, 64); E(b_cond, "ow_s", "lo"); E(mov_reg, 2, 3)
    c.lab("ow_s"); E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(mov_reg, 1, 7); c.call("c_vstore")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 34); E(b_cond, "ow_l", "ls")
    E(pop_list, [], pc=True)


@fn
def c_mznova(c):                         # (r4 = t, r5 = f, r6 = MZ, r8 / r11 = the links' caches): Synth 1 / 2's rows from the round robin's place, at most BUDGET written
    E = c.E; E(push_list, [], lr=True)
    c.imm32(0, LIVE + 30); E(movw, 1, 344); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(raw, mov_hi(9, 0))      # r9 = the live bytes 30..
    c.imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0); E(adds_imm8, 0, 4); E(raw, mov_hi(10, 0))   # r10 = this + 4
    E(movs_imm, 0, BUDGET); E(raw, mov_hi(12, 0))                                           # r12 = the budget (kept on the stack around the call)
    E(ldrh_imm, 7, 6, O_RR)
    c.lab("nv_l")
    E(movw, 0, NROWS); E(cmp_reg, 7, 0); E(b_cond, "nv_k", "lo"); E(movs_imm, 7, 0)
    c.lab("nv_k")
    E(lsls_imm, 0, 7, 3); c.imm32(1, TABLE); E(adds_reg, 3, 0, 1)                          # r3 = the row
    E(ldrb_imm, 0, 3, 0); E(cmp_imm, 0, 0xFD); E(b_cond, "nv_s", "hs")                      # a bitfield: left alone
    E(ldrb_imm, 0, 3, 2); E(ldrb_imm, 1, 3, 3); E(lsls_imm, 1, 1, 8); E(orrs_reg, 0, 1); E(subs_imm8, 0, 30)
    E(movw, 1, NOVA_LEN); E(cmp_reg, 0, 1); E(b_cond, "nv_s", "hs")                         # r0 = the byte - 30
    E(raw, mov_hi(1, 8)); E(ldrb_reg, 2, 1, 0); E(raw, mov_hi(1, 11)); E(ldrb_reg, 1, 1, 0)   # r2 = A, r1 = B
    E(push_list, [0]); E(ldrb_imm, 0, 3, 4); E(subs_imm8, 0, 1); E(cmp_imm, 0, 1); E(b_cond, "nv_c", "ls")    # kinds 1 / 2 (a range): continuous
    E(cmp_imm, 5, 64); E(b_cond, "nv_v", "lo"); E(mov_reg, 2, 1); E(b, "nv_v")
    c.lab("nv_c"); E(subs_reg, 1, 1, 2); E(muls, 1, 5); E(raw, asrs(1, 1, 7)); E(adds_reg, 2, 2, 1)
    c.lab("nv_v"); E(pop_list, [0]); E(raw, mov_hi(1, 9)); E(ldrb_reg, 1, 1, 0); E(cmp_reg, 1, 2); E(b_cond, "nv_s", "eq")
    E(mov_reg, 3, 2); E(raw, mov_hi(0, 10)); E(mov_reg, 1, 4); E(mov_reg, 2, 7)
    E(raw, h(0xF84D) + h(0xCD04)); c.call(PARAM_SET); E(raw, h(0xF85D) + h(0xCB04))       # str.w r12, [sp, #-4]! / ldr.w r12, [sp], #4
    E(raw, h(0xF1BC) + h(0x0C01)); E(b_cond, "nv_e", "eq")                                  # subs.w r12, r12, #1
    c.lab("nv_s"); E(adds_imm8, 7, 1)
    E(movw, 0, NROWS); E(cmp_reg, 7, 0); E(b_cond, "nv_t", "lo"); E(movs_imm, 7, 0)
    c.lab("nv_t"); E(ldrh_imm, 0, 6, O_RR); E(cmp_reg, 0, 7); E(b_cond, "nv_l", "ne")       # a whole round: done
    c.lab("nv_e"); E(strh_imm, 7, 6, O_RR); E(pop_list, [], pc=True)


@fn
def c_mztick(c):                         # the LED task's call (ctrl, frame): the chain below first, then the morph
    E = c.E
    c.imm32(3, MZ); E(ldrb_imm, 2, 3, O_ACT); E(cmp_imm, 2, 3); E(b_cond, "tk_on", "ls"); E(ldrb_imm, 2, 3, O_HP); E(cmp_imm, 2, ARMED); E(b_cond, "tk_on", "eq")
    E(b_w, c.prev["led"])
    c.lab("tk_on")
    c.imm32(2, SV); E(str_imm, 1, 2, 0); E(raw, mov_hi(3, 14)); E(str_imm, 3, 2, 4)        # nothing on the stack while the chain below runs
    c.call(c.prev["led"])
    c.imm32(2, SV); E(ldr_imm, 1, 2, 0); E(ldr_imm, 3, 2, 4); E(raw, mov_hi(14, 3))
    E(push_list, [1], lr=True); E(raw, PUSHALL)
    c.call("c_mzst"); E(mov_reg, 6, 0)
    c.now(0); E(ldr_imm, 1, 6, O_T); E(str_imm, 0, 6, O_T); E(subs_reg, 5, 0, 1); c.bc("tk_bt", "lo")   # the clock went back: a reset
    E(cmp_imm, 5, 100); E(b_cond, "tk_d", "ls"); E(movs_imm, 5, 100)
    c.lab("tk_d")
    c.lab("tk_b2"); E(strh_imm, 5, 6, O_DT); E(ldrb_imm, 4, 6, O_ACT); E(cmp_imm, 4, 3); E(b_cond, "tk_arm", "hi")
    c.call("c_mzmv"); E(cmp_imm, 0, 0); E(b_cond, "tk_h", "eq")
    if not NOCUR: E(ldr_sp, 3, 56); c.call("c_mzpanel")
    c.lab("tk_h"); c.call("c_mzhold")
    c.call("c_mzfill"); E(cmp_imm, 0, 0); E(b_cond, "tk_x", "ne")
    E(ldrh_imm, 5, 6, O_DT); c.call("c_mzmod")                                             # (r1 = 32512)
    # i = x / 32512, f = the rest >> 8, x = pos (n - 1)
    E(ldrb_imm, 2, 6, O_N); E(subs_imm8, 2, 2 if NOCUR else 1); E(muls, 0, 2); E(raw, udiv(3, 0, 1)); E(mov_reg, 7, 3); E(muls, 3, 1); E(subs_reg, 0, 0, 3); E(lsrs_imm, 5, 0, 8)
    E(subs_imm8, 2, 1); E(cmp_reg, 7, 2); E(b_cond, "tk_i", "ls"); E(mov_reg, 7, 2); E(movs_imm, 5, 128)
    c.lab("tk_i")                                                                           # r7 = i, r5 = f; r8 = link i's cache, r11 = link i + 1's
    E(adds_reg, 0, 6, 7); E(ldrb_imm, 1, 0, O_ORD); E(ldrb_imm, 2, 0, O_ORD + 1); E(raw, mov_hi(9, 1)); E(raw, mov_hi(10, 2))
    E(movw, 3, NOVA_LEN); E(muls, 1, 3); E(muls, 2, 3); c.imm32(0, CC); E(adds_reg, 1, 1, 0); E(adds_reg, 2, 2, 0)
    E(raw, mov_hi(8, 1)); E(raw, mov_hi(11, 2))
    E(cmp_imm, 4, 2); E(b_cond, "tk_o", "hs")
    if SVC:                                                                                 # the writes go to the DSP service (c_mzsvc)
        c.imm32(0, NV); E(strb_imm, 4, 0, 1); E(strb_imm, 5, 0, 2); E(raw, mov_hi(1, 9)); E(strb_imm, 1, 0, 3); E(raw, mov_hi(1, 10)); E(strb_imm, 1, 0, 4)
        E(movs_imm, 1, 1); E(strb_imm, 1, 0, 0); E(b, "tk_x")
    else:
        c.call("c_mznova"); E(b, "tk_x")
    c.lab("tk_o"); c.call("c_mzown"); c.call("c_mzfm")
    c.lab("tk_x"); E(raw, POPALL_LR); E(pop_list, [1], pc=True)
    # off, a patch held since its press: 0.4 s = the morph on (the patches held then); let go before = nothing
    c.lab("tk_arm"); E(ldrb_imm, 0, 6, O_HP); E(cmp_imm, 0, ARMED); E(b_cond, "tk_x", "ne")
    E(ldrb_imm, 4, 6, O_SNAP); E(cmp_imm, 4, 3); E(b_cond, "tk_dis", "hi")
    E(mov_reg, 0, 4); c.call("c_mzon"); E(cmp_imm, 0, 0); E(b_cond, "tk_dis", "eq")
    c.call("c_mzheld"); E(cmp_imm, 0, 0); E(b_cond, "tk_dis", "eq"); E(mov_reg, 7, 0)
    c.now(1); E(ldr_imm, 2, 6, O_TP); E(subs_reg, 1, 1, 2); E(movw, 2, HOLD_MS); E(cmp_reg, 1, 2); E(b_cond, "tk_x", "lo")
    E(mov_reg, 0, 7); E(subs_imm3, 1, 0, 1); E(raw, h(0x4208)); E(b_cond, "tk_x", "eq")                    # two held at least
    c.call("c_mzcd"); E(cmp_imm, 0, 0); E(b_cond, "tk_dis", "ne")                           # a Clear / Duplicate gesture: disarmed
    E(mov_reg, 0, 7); c.call("c_mzenter"); E(b, "tk_x")
    c.lab("tk_dis"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP); E(b, "tk_x")
    c.lab("tk_bt"); E(ldrb_imm, 0, 6, O_ACT); E(cmp_imm, 0, 3); E(b_cond, "tk_b1", "ls")       # off (a patch armed): dt 100, on as always
    E(movs_imm, 5, 100); E(b, "tk_b2")
    c.lab("tk_b1"); E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, O_ACT); E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HP); E(b, "tk_x")   # a morph running: off


@fn
def c_mzsvc(c):                          # (use_svc) the head of the DSP service chain: the frame's Synth 1 / 2 rows, the service holding its semaphore
    E = c.E
    E(raw, PUSHALL)
    c.imm32(6, NV); E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "sv_x", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)
    E(ldrb_imm, 4, 6, 1); E(ldrb_imm, 5, 6, 2); E(ldrb_imm, 1, 6, 3); E(ldrb_imm, 2, 6, 4)
    c.imm32(6, MZ); E(ldrb_imm, 0, 6, O_ACT); E(cmp_reg, 0, 4); E(b_cond, "sv_x", "ne"); E(cmp_imm, 4, 2); E(b_cond, "sv_x", "hs")
    E(movw, 3, NOVA_LEN); E(muls, 1, 3); E(muls, 2, 3); c.imm32(0, CC); E(adds_reg, 1, 1, 0); E(adds_reg, 2, 2, 0)
    E(raw, mov_hi(8, 1)); E(raw, mov_hi(11, 2))
    c.imm32(0, NV); E(raw, h(0x4669)); E(str_imm, 1, 0, 8); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 5)   # mov r1, sp
    c.call("c_mznova")
    c.imm32(0, NV); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 5)
    c.lab("sv_x"); E(raw, POPALL_LR); E(b_w, c.prev["svc"])


@fn
def c_mzmd(c):                           # (use_svc) MARK_DIRTY's head (type, index): inside c_mzsvc's writes = 0x08021FDC, no semaphore
    E = c.E
    c.imm32(2, NV); E(ldrb_imm, 3, 2, 5); E(cmp_imm, 3, 0); E(b_cond, "md_s", "eq")
    E(ldr_imm, 3, 2, 8); E(raw, h(0x466A)); E(subs_reg, 3, 3, 2); E(lsrs_imm, 3, 3, 10); E(cmp_imm, 3, 0); E(b_cond, "md_s", "ne")   # mov r2, sp
    E(b_w, MARK_RAW)
    c.lab("md_s"); E(raw, h(0xB538) + h(0x460D)); E(b_w, MARK_DIRTY + 4)                   # push {r3, r4, r5, lr}; mov r5, r1


class Ctx:
    def __init__(self, base, ext, prev, L, SP):
        self.a = Asm(base); self.E = self.a.emit; self.ext, self.prev, self.L, self.SP = ext, prev, L, SP
        self.local = set(); self.zc = 0; self.pre = ""
    def lab(self, n): self.a.label(self.pre + n)
    def imm32(self, rd, v): self.E(movw, rd, v & 0xFFFF); self.E(movt, rd, (v >> 16) & 0xFFFF)
    def now(self, rd): self.imm32(rd, JS.HAL_TICK); self.E(ldr_imm, rd, rd, 0)
    def call(self, t):
        if isinstance(t, int): self.E(bl, t)
        elif t in self.L: self.E(bl, self.L[t])
        elif t in self.local: self.E(bl, t)
        else: self.E(bl, self.ext[t])
    def bc(self, target, cond):
        self.zc += 1; n = f"{self.pre}_z{self.zc}"
        self.E(b_cond, n, INV[cond]); self.E(b, self.pre + target); self.a.label(n)


def assemble(base, names, ext, prev, L, SP, data=b""):
    """the functions `names` at base, then data (label t_disc); local labels prefixed by the function's name"""
    c = Ctx(base, ext, prev, L, SP)
    c.local = set(names)
    E0 = c.E
    for nm in names:
        c.a.label(nm)
        c.pre = nm + "."
        def E(f, *args, _E0=E0, _c=c, **kw):
            # local labels: any string argument that is not a function name / external gets the prefix
            if f in (b_cond, b, b_w, bl) and args and isinstance(args[0], str) and args[0] not in _c.local and not args[0].startswith(_c.pre):
                args = (_c.pre + args[0],) + args[1:]
            return _E0(f, *args, **kw)
        c.E = E
        FUNCS[nm](c)
    c.E = E0
    if data:
        c.a.label("t_disc"); c.E(raw, data)
    return c.a.assemble()


def _dis(sc, code, at):
    try: return sc.disasm(bytes(code), at)
    except ValueError: return []                     # (the table at the end)


def dead_ranges(img, report):
    """jumpflip's two handlers that flipview skips: their ranges, after checking that nothing in the image calls or points into them"""
    import ct_fw
    BASE = ct_fw.APP_BASE
    jl = {k: int(v, 16) for k, v in report["jumpflip"]["labels"].items()}
    jend = int(report["dspz"]["blocks"]["jumpflip"][1], 16)
    out = []
    for a, nxt in JF_DEAD:
        lo, hi = jl[a], (jl[nxt] if nxt else jend)
        out.append((lo, hi))
    def inside(t): return any(lo <= t < hi for lo, hi in out)
    n = len(img) & ~1
    for o in range(0, n - 4, 2):                                                       # bl / b.w into them from outside
        at = BASE + o
        if inside(at): continue
        h1, h2 = struct.unpack_from("<HH", img, o)
        if h1 & 0xF800 == 0xF000 and h2 & 0xD000 in (0xD000, 0x9000):
            s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
            off = s << 24 | (1 - (j1 ^ s)) << 23 | (1 - (j2 ^ s)) << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
            if s: off -= 1 << 25
            assert not inside(at + 4 + off), f"{at:#x} calls into jumpflip's dead handlers"
    for o in range(0, n - 4, 4):                                                       # vtable words / pointers
        w = struct.unpack_from("<I", img, o)[0]
        assert not inside(w & ~1) or inside(BASE + o), f"{BASE + o:#x} points into jumpflip's dead handlers"
    return out


def place(img, report):
    """SC54's extra, the last module: the areas, the functions packed into them (first fit, the biggest first), two passes, the hooks."""
    import ct_fw
    import hole
    import modmx as MX
    import psave
    import hashlib
    import build_shared_channels as sc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_pson=lab("psave", "c_pson"), c_mpon=lab("mpatch", "c_mpon"), c_mpc=lab("mpatch", "c_mpc"), c_mpr=lab("mpatch", "c_mpr"),
             c_von=lab("vcf20", "c_von"), c_vvaddr=lab("vcf20", "c_vvaddr"), c_vstore=lab("vcf20", "c_vstore"), c_mxclrh=lab("modmx", "c_mxclrh"),
             c_gst=lab("sc14", "c_gst"), c_rmw=lab("srcview", "c_rmw"), c_shift=lab("sc15", "c_shift"),
             c_sdfset=lab("vcf20", "c_sdfset"))
    import build_sc15 as s15
    import srcview as SV_
    assert (S_PAINT, F_SRC, F_SDOPEN) == (s15.S_PAINT, SV_.F_SRC, V.F_SDOPEN)
    SP, TP, KN = psave.SP_VT, MP.TMPL_VT, V.AC64_VT
    leds = [MX.bl_target(img, s, BASE) for s in PK.LED_CALLS]
    assert leds[0] == leds[1], [hex(x) for x in leds]
    prev = dict(npad=u(SP) & ~1, nrel=u(SP + 4) & ~1, nled=u(SP + 28) & ~1, opad=u(TP) & ~1, orel=u(TP + 4) & ~1, oled=u(TP + 28) & ~1,
                btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), knob=u(KN + 16) & ~1, kled=u(KN + 28) & ~1, led=leds[0])
    for k in ("npad", "opad"): assert prev[k] != 0
    if SVC:
        import build_sc14 as S14
        prev["svc"] = MP.bw_target(img, S14.SVC_HOOK, BASE)
        assert img[MARK_DIRTY - BASE:MARK_DIRTY - BASE + 4] == bytes.fromhex("38b50d46"), img[MARK_DIRTY - BASE:MARK_DIRTY - BASE + 4].hex()
    # the areas: [name, lo, hi]
    hb = report["hole"]; d = report["dspz"]
    areas = [["hole", (int(hb["next"], 16) + 3) & ~3, hole.HI],
             ["gap0", (int(d["next"], 16) + 3) & ~3, int(d["gaps"][0][1], 16)],
             ["gap1", (int(d["next1"], 16) + 3) & ~3, int(d["gaps"][1][1], 16)]]
    for i, (lo, hi) in enumerate(dead_ranges(img, report)): areas.append([f"jf{i}", (lo + 3) & ~3, hi])
    end = BASE + len(img)
    areas.append(["end", (end + 3) & ~3, BASE + 0x70000])
    disc = fm_disc()
    names = [n for n in FUNCS if (SVC or n not in SVC_FUNCS) and not (TRIMP and n == "c_mzpanel") and (SLOW or n not in SLOW_FUNCS)]
    dummy = {n: 0x08300000 + 64 * i for i, n in enumerate(names)}
    dummy["t_disc"] = 0x08380000
    size = {n: len(assemble(0x08020000, [n], dummy, prev, L, SP)[0]) for n in names}
    size["t_disc"] = len(disc) + 2
    # first fit decreasing; the table goes with c_mzfm when it can
    order = sorted(names, key=lambda n: -size[n])
    room = {a[0]: a[2] - a[1] for a in areas}
    parts = {a[0]: [] for a in areas}
    for n in order:
        need = size[n] + (size["t_disc"] if n == "c_mzfm" else 0)
        cands = [a[0] for a in areas if room[a[0]] >= need]
        assert cands, f"morphz: no room for {n} ({size[n]} B; free {room}; left {[(x, size[x]) for x in order[order.index(n):]]}; areas {[(a_[0], a_[2] - a_[1]) for a_ in areas]})"
        k = min(cands, key=lambda k_: (ENDLAST and k_ == "end", room[k_]))           # best fit (ENDLAST: the image's end last)
        parts[k].append(n); room[k] -= need
    base_of = {a[0]: a[1] for a in areas}
    hi_of = {a[0]: a[2] for a in areas}
    def build(ext):
        out, labels = {}, {}
        for k, ns in parts.items():
            if not ns: continue
            code, lb = assemble(base_of[k], ns, ext, prev, L, SP, disc if "c_mzfm" in ns else b"")
            out[k] = code; labels.update({x: v for x, v in lb.items()})
        return out, labels
    _, lab1 = build(dummy)
    out, lab2 = build({**{n: lab1[n] for n in names}, "t_disc": lab1["t_disc"]})
    assert all(lab1[n] == lab2[n] for n in names) and lab1["t_disc"] == lab2["t_disc"]
    for k, code in out.items():
        lo = base_of[k]; e = lo + len(code)
        assert e <= hi_of[k], (k, hex(e), hex(hi_of[k]))
        if k == "end":
            assert len(img) <= lo - BASE
            img += bytes([0xFF]) * (lo - BASE - len(img)) + code
        else:
            if k in ("gap0", "gap1"): assert all(x == 0xFF for x in img[lo - BASE:e - BASE]), k
            img[lo - BASE:e - BASE] = code
        if k == "hole":
            hb["next"] = hex(e); hb["blocks"]["morphz"] = [hex(lo), hex(e), hashlib.sha256(bytes(code)).hexdigest()]
        elif k == "gap0": d["next"] = hex(e); d["blocks"]["morphz"] = [hex(lo), hex(e)]
        elif k == "gap1": d["next1"] = hex(e); d["blocks"]["morphz1"] = [hex(lo), hex(e)]
    for slot, k in ((SP, "c_mzpadX"), (SP + 4, "c_mzrelX"), (SP + 28, "c_mzledX"), (TP, "c_mzpadX"), (TP + 4, "c_mzrelX"), (TP + 28, "c_mzledX"),
                    (KN + 16, "c_mzknob"), (KN + 28, "c_mzkled")):
        struct.pack_into("<I", img, slot - BASE, lab2[k] | 1)
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, lab2["c_mzbtn"])
    for s in PK.LED_CALLS: img[s - BASE:s - BASE + 4] = bl(s, lab2["c_mztick"])
    assert (NV_END if SVC else END) <= 0x2004F400
    if SVC:
        img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, lab2["c_mzsvc"])
        img[MARK_DIRTY - BASE:MARK_DIRTY - BASE + 4] = b_w(MARK_DIRTY, lab2["c_mzmd"])
    report["morphz"] = dict(labels={n: hex(v) for n, v in lab2.items() if "." not in n}, prev={k: hex(v) for k, v in prev.items()},
                            parts={k: [hex(base_of[k]), hex(base_of[k] + len(out[k])), parts[k]] for k in out},
                            listing={k: _dis(sc, out[k], base_of[k]) for k in out}, free={k: hi_of[k] - base_of[k] - len(out[k]) for k in out})
    return lab2
