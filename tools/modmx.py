"""SC44.2 (the user, 2026-10-18: «Design a light mod matrix for the own synth» … «modw and aftertouch are not supported» … «Add all exposed parameters as
destination. Give them colors and make them slow knobs» … «Each Knob 1-8 represents a source, the knob state is the destination. Moving inside a
destination range controls the amount»): a mod matrix for the own synth of MIDI 1 / 2 (tools/vcf21.py), on the ARM.

The page: pad 6 of the MIDI Preset view (with the engine on, pads 6-8 did nothing) = knob page 6 (vcf21's page 5: the page row's `cmp r5, #4` of
vp_row becomes `cmp r5, #5`).  Pad 6 light blue (bright on the page, dim off it); Clear + pad 6 = every source off.
  * K1..K8 = the sources: K1 velocity, K2 the note (C3 = 0, +-1 octave = +-24), K3 random (a new value at each note), K4 LFO 2, K5 envelope 2
    (attack / decay from each note), K6 drum hit (a decay from each hit of a chosen drum), K7 the pattern position (a ramp from the first to the last
    step of the track's pattern), K8 step random (a new value every N steps of the sequencer).
  * The knob's position is the destination and the amount: position 0 = off; then one zone of ZONE steps per destination (DEST: every code on the
    knob pages, in page order, the first place it appears: 33), the amount growing from 1 / ZONE to full inside the zone.  A slow knob: DIV knob
    events per step (an accumulator for the knob touched last).  Full amount = the destination's whole range for a full source.
  * The knob LED: the colour of the destination's page (the page pads' colours: VCA / VCF orange, OSC 1 green, OSC 2 teal, lanes yellow, modulation
    magenta), the brightness of the amount; off = dark.  While a source knob turns (OVL_MS after the last event) pads 9-24 show where its
    destination lives: the destination's page pad bright, pads 9-16 / 17-24 = that page's K1..K8 / Shift + K1..K8 (dim the ones with a parameter,
    bright the destination); presses on pads 9-24 are swallowed meanwhile (else they load patches).
  * Shift + K4 = LFO 2: 4 zones of 32 = shape (triangle, saw, square, sample & hold) x rate (0.05 Hz .. 20 Hz); Shift + K5 = envelope 2: attack zone
    (0, 30, 150, 600 ms) x decay (20 ms .. 4 s); Shift + K6 = drum 1-4 x its decay; Shift + K8 = steps per new value (1, 2, 4, 8, 16).  Their LEDs:
    the zone's colour, the brightness of the position.  Clear + K = the source off (with Shift: its parameter back to the default).

How it reaches the DSP: every value of the engine goes through vcf21's c_sdfx (the step-drummer's offset) in c_vsend; both calls go to c_mxfx = c_sdfx,
then + the matrix's offset of that code (the sum of the slots that point there), clamped to the code's range (a granular track: GR_TAB's; in sample mode code 25, the sample number, -1..63).  A head
of the DSP service chain (c_mxtick) updates the sources every 4 ms and marks one changed destination per update (round robin over the slots, so a
moving source cannot starve the others: c_vmark for codes 1..26, the sweep cursor c_sdcur for 27..34); a note-on (the head of the note vtable)
takes its velocity, note, a random value and restarts envelope 2, and marks the note sources' destinations at once; a drum hit (SC16's tail of the
drum trigger) records its time.  Rate: one message per voice every 2 ms (vcf21.use_ratelimit), shared by everything that moves.

RAM: MXR (0x20045000..+0xA0): above the heap's limit (0x20044E58), below the stock's own stack reserve (0x2004FE00): the stock's memory report
(0x0801D426: «Total RAM Used: … Remaining: …» = 0x2004FE00 - the heap pointer) counts it as free, and two RAM dumps of the running firmware hold the
SRAM's power-up pattern there (never written) up to ~0x2004FC00; no literal of the stock points inside.  Not cleared at power-up: a signature.
Saved: with the own-synth patches (mpatch): 24 bytes at padding + 64 (after the name): "MX", version 1, 8 positions (u16), 4 parameters, a check
byte; c_mpsave's gather and c_mpload's apply are wrapped (a patch without them loads the matrix off).  Not with the project, not at power-up.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, ldr_sp, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   ldrh_imm, ldrh_reg, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm,
                   strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import build_sc14 as S14  # noqa: E402

MXR = 0x20045000                      # our RAM (see the docstring)
SIG = 0x3152584D                      # "MXR1"
G_ACC, G_LK, G_OVK, G_RNG, G_OVT, G_HIT = 4, 5, 6, 8, 12, 16    # globals: knob accumulator, its knob (t << 4 | k), the overlay's knob (0xFF none), rng, time, 4 drum hit times
T0, TS, SIZE = 32, 64, 160            # track blocks: MXR + T0 + TS t
B_POS, B_PAR, B_SRC, B_RR, B_RND, B_SRV, B_STP, B_LAST = 0, 16, 20, 28, 29, 30, 31, 32
B_ENV, B_PH, B_SH, B_SCN, B_UPD, B_NOTE, B_VEL = 40, 44, 46, 47, 48, 52, 53
ZONE, DIV = 16, 2                     # amount steps per destination, knob events per step
PAGE = 5                              # vcf21's knob page index of the matrix (pad 6)
UPD_MS, OVL_MS = 4, 1500
COL_MX = (0x13, 0x14)                 # pad 6: light blue bright / dim
PAR_KNOB = (0xFF, 0xFF, 0xFF, 0, 1, 2, 0xFF, 3)                 # Shift + K: the parameter it moves
PAR_DEF = (16, 16, 16, 0)             # triangle at ~1 Hz; attack 0, decay ~0.4 s; drum 1, decay ~0.4 s; one step
LFO_COL = (0x17, 0x2D, 0x45, 0x49)    # triangle green, saw yellow, square red, S&H violet
ATK_COL = (0x01, 0x13, 0x4D, 0x09)    # attack 0 white, short light blue, medium teal, long blue
DRM_COL = (0x45, 0x2D, 0x49, 0x4D)    # drum 1-4: the granular source colours of the drums (vcf21.GRS_COL)
SRN_COL = (0x01, 0x17, 0x2D, 0x09, 0x32)
SRN_STEPS = (1, 2, 4, 8, 16)
ATK_MS = (0, 30, 150, 600)
V2 = False                            # SC44.3 (use_v2)
LFO_COL2 = (0x17, 0x32, 0x53, 0x01, 0x49)   # (V2) the engine LFO's colours: triangle green, saw magenta, square red, S&H white, slewed S&H violet
PAR_MAX2 = (5 * 32 - 1, 127, 127, 127)      # (V2) LFO 2: 5 shapes x 32 rates
B_SHP = 54                            # (V2) the slewed S&H's last value


SYNC = False                          # SC44.8 (use_sync)
SYNC_RAM = MXR + 0x100                # (SYNC) the last sequencer tick seen by each track's LFO 2 (u32 x 2)


SHSYNC = False                        # SC46.1 (use_shsync)


def use_shsync():
    """SC46.1 (a fix of the beta; «lfo s&h (random) no funciona»): LFO 2's sample & hold takes a new value when its 16-bit phase overflows; synced
    (the lower half of each shape's zone), c_mxsync sets the phase on every new sequencer tick and the cycle's start (the phase back to 0) never
    overflowed: the value stayed.  Now a new tick that sets the phase more than half a cycle back stores it less the advance about to be added, so
    the add overflows (a new value) and lands on it."""
    global SHSYNC
    assert SYNC
    SHSYNC = True


def use_sync():
    """SC44.8 (lfosync.py; the user, 2026-10-19: «en los lfo rate, hazlo bipolar … derecha libre, izquierda a tempo con sync en beat 1»; the LFO 2
    of the matrix «por forma»): in each shape's zone of 32 (Shift + K4), the lower half 0..15 = synced to the tempo, the division
    lfosync.DIVS[15 - r] (the centre of the zone = 1/16T, its start = 8 bars), the upper half 16..31 = free, the rate lfoinc[2 (r - 16) + 1];
    synced: the phase moves BPM x 2^16 x 24 / (60000 d) a ms and, on every new sequencer tick, is set to (tick mod d) / d; the LED with Shift
    dim at the zone's centre, brighter to both sides.  The default 24 (about the 1 Hz of before)."""
    global SYNC, PAR_DEF
    SYNC = True
    PAR_DEF = (24,) + tuple(PAR_DEF[1:])


def use_v2():
    """SC44.3 (the user, 2026-10-18: «add s&h (stepped random) and slewed s&h (glided random) as waveshapes»): LFO 2 (K4) gets a fifth shape, slewed
    sample & hold (a glide from the last random value to a new one over each cycle; violet), its Shift + K4 range 5 zones x 32; its colours are
    the engine LFO's (triangle green, saw magenta, square red, sample & hold white).  The triangle stays the default."""
    global V2, LFO_COL
    V2, LFO_COL = True, LFO_COL2
TRIG_TAIL = 0x08051B7C                # SC16's b.w to c_trig at the drum trigger's tail (r2 = 0x99 + the drum)
NOTE_VT = 0x08059FC4                  # the note-on of the tracks' transmitter (vcf21's c_vnon is a head there)
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)
def asrs_imm(rd, rm, imm): return h(0x1000 | (imm & 31) << 6 | rm << 3 | rd)
def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def sdiv(rd, rn, rm): return h(0xFB90 | rn) + h(0xF0F0 | rd << 8 | rm)
def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def dests():
    """(code, page, index 0..15) of every code on the knob pages, the first place it appears (code 14 = the second note: not a value)"""
    rows = [V.KNOB_CODES, V.KNOB_CODES_B, V.KNOB_CODES_C, V.KNOB_CODES_D, V.KNOB_CODES_E]
    out, seen = [], set()
    for pg, row in enumerate(rows):
        for i, c in enumerate(row):
            if c and c != 14 and c not in seen:
                out.append((c, pg, i)); seen.add(c)
    return rows, out


def ranges():
    """lo / hi of every stored code 0..34 (vcf21's knob clamps), and the granular page's (GR_TAB) where it differs"""
    lo, hi = [0] * 35, [127] * 35
    for c in range(1, 35):
        if V.BIPOLAR_MASK >> (c - 1) & 1: lo[c], hi[c] = -64, 63
        if c in (20, 30): hi[c] = 100
    glo, ghi = list(lo), list(hi)
    for c, mn, mx, _f in V.GR_TAB: glo[c], ghi[c] = mn, mx
    return lo, hi, glo, ghi


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_x{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)

    # ---- data (addresses known before the code)
    rows, D = dests()
    assert len(D) * ZONE < 0x10000
    lo, hi, glo, ghi = ranges()
    pcol = [V.COL_PAGE[0], V.COL_PAGE[1], V.COL_PAGE[2], V.COL_PAGE2[0], V.COL_PAGE2[1]]
    lfoinc = [max(1, round(0.05 * 400 ** (r / 31) * 65.536)) for r in range(32)]
    decms = [round(20 * 200 ** (d / 31)) for d in range(32)]
    data = bytearray()
    T = {}
    def put(name, bs):
        while len(data) % 2: data.append(0)
        T[name] = base + len(data); data.extend(bs)
    put("dcode", bytes(c for c, _p, _i in D))
    put("dcol", bytes(pcol[p][0] for _c, p, _i in D))
    put("dmap", bytes(p << 4 | i for _c, p, i in D))
    put("rows", bytes(c if c != 14 else 0 for r in rows for c in r))
    put("pbri", bytes(c[0] for c in pcol)); put("pdim", bytes(c[1] for c in pcol))
    put("lo", bytes(v & 0xFF for v in lo)); put("hi", bytes(v & 0xFF for v in hi))
    put("glo", bytes(v & 0xFF for v in glo)); put("ghi", bytes(v & 0xFF for v in ghi))
    put("span", bytes(min(255, h_ - l_) for l_, h_ in zip(lo, hi)))
    put("lfoinc", struct.pack("<32H", *lfoinc)); put("dec", struct.pack("<32H", *decms)); put("atk", struct.pack("<4H", *ATK_MS))
    put("pk", bytes(PAR_KNOB)); put("pdef", bytes(PAR_DEF))
    if V2: put("zcol", bytes(LFO_COL + ATK_COL + (0,) + DRM_COL + (0,))); put("pmx", bytes(PAR_MAX2))
    else: put("zcol", bytes(LFO_COL + ATK_COL + DRM_COL + SRN_COL[:4]))
    put("scol", bytes(SRN_COL)); put("srn", bytes(SRN_STEPS))
    if SYNC:
        import lfosync as LF
        while (base + len(data)) % 4: data.append(0)
        put("ldiv", struct.pack("<16I", *LF.DIVS))
        put("lk2", struct.pack("<16I", *(round((1 << 16) * 24 * 4096 / (60000 * d)) for d in LF.DIVS)))
    while len(data) % 4: data.append(0)
    E(raw, bytes(data))
    PMAX = len(D) * ZONE

    # ---- c_mxst() -> r0 = MXR, set up at the first use (the RAM holds the power-up pattern); clobbers r1-r3
    a.label("c_mxst")
    imm32(0, MXR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_init", "ne"); E(raw, h(0x4770))
    a.label("st_init")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(movs_imm, 1, 0); E(movs_imm, 3, SIZE // 4)
    a.label("st_z"); E(str_imm, 1, 0, 0); E(adds_imm8, 0, 4); E(subs_imm8, 3, 1); E(b_cond, "st_z", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, G_OVK)
    for t in (0, 1):
        for j, v in enumerate(PAR_DEF): E(movs_imm, 1, v); E(strb_imm, 1, 0, T0 + TS * t + B_PAR + j) if T0 + TS * t + B_PAR + j < 32 else E(strb_w, 1, 0, T0 + TS * t + B_PAR + j)
        E(movs_imm, 1, 60); E(strb_w, 1, 0, T0 + TS * t + B_NOTE)
    imm32(1, SIG); E(str_imm, 1, 0, 0)
    E(pop_list, [4], pc=True)

    # ---- c_mxblk(r0 = track) -> r0 = its block; clobbers r1-r3
    a.label("c_mxblk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_mxst")
    E(lsls_imm, 1, 4, 6); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, T0); E(pop_list, [4], pc=True)

    # ---- c_mxcode(r0 = position) -> r0 = its code, 0 = off; clobbers r1
    a.label("c_mxcode")
    E(cmp_imm, 0, 0); E(b_cond, "cd_x", "eq")
    E(subs_imm8, 0, 1); E(lsrs_imm, 0, 0, 4); imm32(1, T["dcode"]); E(ldrb_reg, 0, 1, 0)
    a.label("cd_x"); E(raw, h(0x4770))

    # ---- c_mxmark(r0 = track, r1 = code): sent to the DSP again (codes 1..26 dirty, 27..34 next in the sweep); clobbers r0-r3
    a.label("c_mxmark")
    E(cmp_imm, 1, 0); E(b_cond, "mk_x", "eq"); E(cmp_imm, 1, 26); E(b_cond, "mk_v", "hi"); E(b_w, L["c_vmark"])
    a.label("mk_v"); E(b_w, L["c_sdcur"])
    a.label("mk_x"); E(raw, h(0x4770))

    # ---- c_mxset(r0 = track, r1 = slot, r2 = position): the old and the new destination sent again; clobbers r0-r3
    a.label("c_mxset")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_mxblk"); E(mov_reg, 7, 0)
    E(lsls_imm, 1, 5, 1); E(ldrh_reg, 0, 7, 1); E(cmp_reg, 0, 6); E(b_cond, "se_x", "eq")
    E(bl, "c_mxcode"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_mxmark")
    E(lsls_imm, 1, 5, 1); E(strh_reg, 6, 7, 1)
    E(mov_reg, 0, 6); E(bl, "c_mxcode"); E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, "c_mxmark")
    a.label("se_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxrnd() -> r0 = a random value -127..127; clobbers r1-r3
    a.label("c_mxrnd")
    E(push_list, [4], lr=True)
    E(bl, "c_mxst"); E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, G_RNG); imm32(1, 1664525); E(muls, 0, 1); imm32(1, 1013904223); E(adds_reg, 0, 0, 1)
    now(1); E(adds_reg, 0, 0, 1); E(str_imm, 0, 4, G_RNG)
    E(lsrs_imm, 0, 0, 24); E(subs_imm8, 0, 128)
    E(mov_reg, 1, 0); E(adds_imm8, 1, 127); E(b_cond, "rn_x", "pl"); E(movs_imm, 0, 0); E(subs_imm8, 0, 127)
    a.label("rn_x"); E(pop_list, [4], pc=True)

    # ---- c_mxgran(r0 = track) -> r0 = 1 for the granular engine (vcf21.c_grpg without the page); clobbers r1-r3
    a.label("c_mxgran")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "gr_0", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, 2); E(bl, L["c_vflag"]); E(cmp_imm, 0, 0); E(b_cond, "gr_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_vdbit"]); E(cmp_imm, 0, 0); E(b_cond, "gr_0", "ne")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 2); E(bl, L["c_vdbit"]); E(pop_list, [4], pc=True)
    a.label("gr_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_mxoff(r0 = track, r1 = code) -> r0 = the matrix's offset of the code; clobbers r1-r3
    a.label("c_mxoff")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, "c_mxblk"); E(mov_reg, 4, 0)
    E(movs_imm, 6, 0); E(movs_imm, 7, 0)
    a.label("of_l")
    E(lsls_imm, 1, 7, 1); E(ldrh_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "of_n", "eq")
    E(subs_imm8, 0, 1); E(lsrs_imm, 1, 0, 4); imm32(2, T["dcode"]); E(ldrb_reg, 2, 2, 1); E(cmp_reg, 2, 5); E(b_cond, "of_n", "ne")
    E(movs_imm, 1, 15); E(ands_reg, 0, 1); E(adds_imm8, 0, 1)                          # the amount 1..16
    E(movs_imm, 1, B_SRC); E(adds_reg, 1, 1, 7); E(raw, ldrsb_reg(1, 4, 1)); E(muls, 0, 1)
    imm32(2, T["span"]); E(ldrb_reg, 1, 2, 5); E(muls, 0, 1)
    E(raw, asrs_imm(0, 0, 11)); E(adds_reg, 6, 6, 0)
    a.label("of_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "of_l", "lo")
    E(mov_reg, 0, 6); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxfx(r0 = track, r1 = a value, r2 = code - 1): c_sdfx (the step-drummer), then + the matrix; r1 = the value for the DSP, r2 and r4-r7 kept
    a.label("c_mxfx")
    E(push_list, [0, 2, 3, 4, 5, 6, 7], lr=True)
    E(bl, L["c_sdfx"]); E(mov_reg, 4, 1)
    E(ldr_sp, 5, 4); E(adds_imm8, 5, 1)                                           # r5 = code
    E(ldr_sp, 0, 0); E(mov_reg, 1, 5); E(bl, "c_mxoff"); E(cmp_imm, 0, 0); E(b_cond, "fx_x", "eq")
    E(adds_reg, 4, 4, 0)
    E(ldr_sp, 0, 0); E(bl, "c_mxgran"); E(cmp_imm, 0, 0); E(b_cond, "fx_g", "ne")       # the granular engine: GR_TAB's ranges
    E(cmp_imm, 5, 25); E(b_cond, "fx_n", "ne"); E(ldr_sp, 0, 0); E(bl, L["c_vsmode"]); E(cmp_imm, 0, 0); E(b_cond, "fx_g", "ne")   # the sample: code 25 = the sample number
    a.label("fx_n"); imm32(2, T["lo"]); imm32(3, T["hi"]); E(b, "fx_c")
    a.label("fx_g"); imm32(2, T["glo"]); imm32(3, T["ghi"])
    a.label("fx_c")
    E(raw, ldrsb_reg(0, 2, 5)); E(cmp_reg, 4, 0); E(b_cond, "fx_1", "ge"); E(mov_reg, 4, 0)
    a.label("fx_1")
    E(raw, ldrsb_reg(0, 3, 5)); E(cmp_reg, 4, 0); E(b_cond, "fx_x", "le"); E(mov_reg, 4, 0)
    a.label("fx_x"); E(mov_reg, 1, 4); E(pop_list, [0, 2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_mxdecay(r0 = elapsed ms, r1 = decay ms) -> r0 = 127 .. 0 (linear), 0 past the end; clobbers r1-r3
    a.label("c_mxdecay")
    E(cmp_reg, 0, 1); E(b_cond, "dy_0", "hs")
    E(movs_imm, 2, 127); E(muls, 0, 2); E(raw, udiv(0, 0, 1)); E(movs_imm, 2, 127); E(subs_reg, 0, 2, 0); E(raw, h(0x4770))
    a.label("dy_0"); E(movs_imm, 0, 0); E(raw, h(0x4770))

    if SYNC:
        import lfosync as LF
        # ---- c_mxsync(r0 = track, r1 = the division's index, r2 = dt ms, r3 = the block) -> r1 = the phase's advance; a new tick sets the phase
        a.label("c_mxsync")
        E(push_list, [4, 5, 6, 7], lr=True)
        E(mov_reg, 4, 3); E(lsls_imm, 5, 1, 2); E(mov_reg, 6, 2); E(mov_reg, 7, 0)
        imm32(0, LF.TEMPO); E(movs_imm, 1, 0); E(bl, LF.PARAM_GET); E(ldrb_imm, 0, 0, 0)
        imm32(1, T["lk2"]); E(adds_reg, 1, 1, 5); E(ldr_imm, 1, 1, 0); E(muls, 0, 1); E(muls, 0, 6); E(lsrs_imm, 6, 0, 12)   # r6 = the advance
        imm32(0, LF.ENG + 0x90); E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0); E(bl, LF.PARAM_GET); E(ldr_imm, 0, 0, 0)          # r0 = the tick
        imm32(1, SYNC_RAM); E(lsls_imm, 2, 7, 2); E(adds_reg, 1, 1, 2); E(ldr_imm, 2, 1, 0); E(cmp_reg, 2, 0); E(b_cond, "sy_x", "eq"); E(str_imm, 0, 1, 0)
        imm32(1, T["ldiv"]); E(adds_reg, 1, 1, 5); E(ldr_imm, 1, 1, 0)
        E(raw, udiv(2, 0, 1)); E(muls, 2, 1); E(subs_reg, 0, 0, 2); E(lsls_imm, 0, 0, 16); E(raw, udiv(0, 0, 1))
        if SHSYNC:                                                                      # the cycle's start (more than half a cycle back): an overflow to come
            E(ldrh_imm, 2, 4, B_PH); E(subs_reg, 2, 2, 0); E(b_cond, "sy_w", "mi"); E(lsrs_imm, 3, 2, 15); E(b_cond, "sy_w", "eq"); E(subs_reg, 0, 0, 6)
            a.label("sy_w")
        E(strh_imm, 0, 4, B_PH)
        a.label("sy_x"); E(mov_reg, 1, 6); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxupd(r0 = track, r1 = now): the sources every UPD_MS; one changed destination marked (round robin)
    a.label("c_mxupd")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 7, 1)
    E(bl, "c_mxblk"); E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, B_UPD); E(subs_reg, 5, 7, 0); E(cmp_imm, 5, UPD_MS); bc("up_x", "lo")
    E(str_imm, 7, 4, B_UPD); E(cmp_imm, 5, 100); E(b_cond, "up_dt", "ls"); E(movs_imm, 5, 100)
    a.label("up_dt")                                                                    # r5 = dt (ms)
    # velocity, note, random
    E(ldrb_w, 0, 4, B_VEL); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(strb_imm, 0, 4, B_SRC + 0)
    E(ldrb_w, 0, 4, B_NOTE); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(subs_imm8, 0, 60); E(lsls_imm, 0, 0, 1)
    E(cmp_imm, 0, 127); E(b_cond, "up_n1", "le"); E(movs_imm, 0, 127)
    a.label("up_n1"); E(mov_reg, 1, 0); E(adds_imm8, 1, 127); E(b_cond, "up_n2", "pl"); E(movs_imm, 0, 0); E(subs_imm8, 0, 127)
    a.label("up_n2"); E(strb_imm, 0, 4, B_SRC + 1)
    E(ldrb_imm, 0, 4, B_RND); E(strb_imm, 0, 4, B_SRC + 2)
    # LFO 2: the phase += inc x dt; a wrap = a new sample-and-hold value
    if SYNC:                                                                            # r1 = the phase's advance
        E(ldrb_imm, 0, 4, B_PAR + 0); E(movs_imm, 1, 31); E(ands_reg, 1, 0); E(cmp_imm, 1, 16); E(b_cond, "up_ls", "lo")
        E(subs_imm8, 1, 16); E(lsls_imm, 1, 1, 1); E(adds_imm8, 1, 1); E(lsls_imm, 1, 1, 1); imm32(2, T["lfoinc"]); E(ldrh_reg, 1, 2, 1); E(muls, 1, 5); E(b, "up_la")
        a.label("up_ls"); E(movs_imm, 2, 15); E(subs_reg, 1, 2, 1); E(mov_reg, 0, 6); E(mov_reg, 2, 5); E(mov_reg, 3, 4); E(bl, "c_mxsync")
        a.label("up_la")
    else:
        E(ldrb_imm, 0, 4, B_PAR + 0); E(movs_imm, 1, 31); E(ands_reg, 1, 0); E(lsls_imm, 1, 1, 1); imm32(2, T["lfoinc"]); E(ldrh_reg, 1, 2, 1)
        E(muls, 1, 5)
    E(ldrh_imm, 2, 4, B_PH); E(adds_reg, 2, 2, 1); E(strh_imm, 2, 4, B_PH)
    E(lsrs_imm, 2, 2, 16); E(cmp_imm, 2, 0); E(b_cond, "up_l1", "eq")
    if V2: E(ldrb_w, 0, 4, B_SH); E(strb_w, 0, 4, B_SHP)
    E(bl, "c_mxrnd"); E(strb_w, 0, 4, B_SH)
    a.label("up_l1")
    E(ldrh_imm, 2, 4, B_PH); E(lsrs_imm, 2, 2, 8)                                       # r2 = the phase 0..255
    E(ldrb_imm, 3, 4, B_PAR + 0); E(lsrs_imm, 3, 3, 5)                                   # r3 = the shape
    E(cmp_imm, 3, 0); E(b_cond, "up_s1", "ne")                                           # triangle
    E(lsls_imm, 0, 2, 1); E(cmp_imm, 2, 128); E(b_cond, "up_t1", "hs"); E(subs_imm8, 0, 128); E(b, "up_lv")
    a.label("up_t1"); E(movs_imm, 1, 0xFF); E(adds_imm8, 1, 128); E(subs_reg, 0, 1, 0); E(b, "up_lv")     # 383 - 2p
    a.label("up_s1"); E(cmp_imm, 3, 1); E(b_cond, "up_s2", "ne"); E(mov_reg, 0, 2); E(subs_imm8, 0, 128); E(b, "up_lv")   # saw
    a.label("up_s2"); E(cmp_imm, 3, 2); E(b_cond, "up_s3", "ne"); E(movs_imm, 0, 127); E(cmp_imm, 2, 128); E(b_cond, "up_lv", "lo")
    E(movs_imm, 0, 0); E(subs_imm8, 0, 127); E(b, "up_lv")                              # square
    a.label("up_s3")
    if V2:                                                                              # shape 4: the glide prev + (new - prev) x phase
        E(cmp_imm, 3, 4); E(b_cond, "up_sh", "ne")
        E(movs_imm, 0, B_SH); E(raw, ldrsb_reg(0, 4, 0)); E(movs_imm, 1, B_SHP); E(raw, ldrsb_reg(1, 4, 1))
        E(subs_reg, 0, 0, 1); E(muls, 0, 2); E(raw, asrs_imm(0, 0, 8)); E(adds_reg, 0, 0, 1); E(b, "up_lv")
        a.label("up_sh")
    E(movs_imm, 0, B_SH); E(raw, ldrsb_reg(0, 4, 0))                                    # sample and hold
    a.label("up_lv")
    E(cmp_imm, 0, 127); E(b_cond, "up_l2", "le"); E(movs_imm, 0, 127)
    a.label("up_l2"); E(mov_reg, 1, 0); E(adds_imm8, 1, 127); E(b_cond, "up_l3", "pl"); E(movs_imm, 0, 0); E(subs_imm8, 0, 127)
    a.label("up_l3"); E(strb_imm, 0, 4, B_SRC + 3)
    # envelope 2: attack, then the decay
    E(movs_imm, 0, 0); E(ldr_imm, 1, 4, B_ENV); E(cmp_imm, 1, 0); bc("up_e9", "eq")
    E(subs_reg, 5, 7, 1)                                                                # r5 = elapsed (dt is not needed any more)
    E(ldrb_imm, 3, 4, B_PAR + 1); E(lsrs_imm, 2, 3, 5); E(lsls_imm, 2, 2, 1); imm32(1, T["atk"]); E(ldrh_reg, 1, 1, 2)    # r1 = attack ms
    E(cmp_reg, 5, 1); E(b_cond, "up_e1", "hs")
    E(movs_imm, 0, 127); E(muls, 0, 5); E(raw, udiv(0, 0, 1)); E(b, "up_e9")
    a.label("up_e1")
    E(subs_reg, 0, 5, 1); E(movs_imm, 2, 31); E(ands_reg, 3, 2); E(lsls_imm, 3, 3, 1); imm32(2, T["dec"]); E(ldrh_reg, 1, 2, 3)
    E(bl, "c_mxdecay")
    a.label("up_e9"); E(strb_imm, 0, 4, B_SRC + 4)
    # drum hit: the decay from the chosen drum's last hit
    E(ldrb_imm, 3, 4, B_PAR + 2); E(lsrs_imm, 0, 3, 5); E(lsls_imm, 0, 0, 2)
    imm32(1, MXR + G_HIT); E(adds_reg, 1, 1, 0); E(ldr_imm, 1, 1, 0)
    E(movs_imm, 0, 0); E(cmp_imm, 1, 0); E(b_cond, "up_d9", "eq")
    E(subs_reg, 0, 7, 1); E(movs_imm, 2, 31); E(ands_reg, 3, 2); E(lsls_imm, 3, 3, 1); imm32(2, T["dec"]); E(ldrh_reg, 1, 2, 3)
    E(bl, "c_mxdecay")
    a.label("up_d9"); E(strb_imm, 0, 4, B_SRC + 5)
    # the pattern position and the step random
    E(mov_reg, 0, 6); E(movs_imm, 1, 1); E(bl, L["c_sdeng"]); E(ldrb_imm, 5, 0, 0); E(movs_imm, 1, 31); E(ands_reg, 5, 1)     # r5 = the step
    E(mov_reg, 0, 6); E(bl, L["c_sdpat"]); E(movw, 1, 0x380); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(ldrb_imm, 2, 0, 1)                                          # r1 = the last step, r2 = the first
    E(movs_imm, 0, 0); E(cmp_reg, 1, 2); E(b_cond, "up_p9", "ls")
    E(cmp_reg, 5, 2); E(b_cond, "up_p9", "lo"); E(cmp_reg, 5, 1); E(b_cond, "up_p1", "ls"); E(mov_reg, 5, 1)
    a.label("up_p1"); E(subs_reg, 0, 5, 2); E(movs_imm, 3, 127); E(muls, 0, 3); E(subs_reg, 1, 1, 2); E(raw, udiv(0, 0, 1))
    a.label("up_p9"); E(strb_imm, 0, 4, B_SRC + 6)
    E(adds_imm8, 5, 1); E(ldrb_imm, 0, 4, B_STP); E(cmp_reg, 0, 5); E(b_cond, "up_r9", "eq")
    E(strb_imm, 5, 4, B_STP)
    E(ldrb_w, 0, 4, B_SCN); E(adds_imm8, 0, 1)
    E(ldrb_imm, 1, 4, B_PAR + 3); E(movs_imm, 2, 5); E(muls, 1, 2); E(lsrs_imm, 1, 1, 7); imm32(2, T["srn"]); E(ldrb_reg, 1, 2, 1)
    E(cmp_reg, 0, 1); E(b_cond, "up_r1", "lo")
    E(bl, "c_mxrnd"); E(strb_imm, 0, 4, B_SRV); E(movs_imm, 0, 0)
    a.label("up_r1"); E(strb_w, 0, 4, B_SCN)
    a.label("up_r9"); E(ldrb_imm, 0, 4, B_SRV); E(strb_imm, 0, 4, B_SRC + 7)
    # one changed destination, round robin from the slot after the last one marked
    E(ldrb_imm, 5, 4, B_RR); E(movs_imm, 7, 8)
    a.label("up_m")
    E(adds_imm8, 5, 1); E(movs_imm, 0, 7); E(ands_reg, 5, 0)
    E(lsls_imm, 1, 5, 1); E(ldrh_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "up_mn", "eq")
    E(movs_imm, 1, B_SRC); E(adds_reg, 1, 1, 5); E(ldrb_reg, 2, 4, 1)
    E(movs_imm, 1, B_LAST); E(adds_reg, 1, 1, 5); E(ldrb_reg, 3, 4, 1); E(cmp_reg, 2, 3); E(b_cond, "up_mn", "eq")
    E(strb_reg, 2, 4, 1); E(strb_imm, 5, 4, B_RR)
    E(bl, "c_mxcode"); E(mov_reg, 1, 0); E(mov_reg, 0, 6); E(bl, "c_mxmark"); E(b, "up_x")
    a.label("up_mn"); E(subs_imm8, 7, 1); E(b_cond, "up_m", "ne")
    a.label("up_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxtick: the head of the DSP service chain (the tick holds the DSP semaphore: RAM only, no MARK_DIRTY)
    a.label("c_mxtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    now(5); E(movs_imm, 4, 0)
    a.label("tk_l")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "tk_n", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_mxupd")
    a.label("tk_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["svc"])

    # ---- c_mxnon (the note vtable's slot: this, track id, note, velocity): MIDI 1 / 2, a note on: its velocity / note, a random value, envelope 2
    a.label("c_mxnon")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True))
    E(mov_reg, 4, 1); E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); bc("nn_x", "hi")
    E(cmp_imm, 3, 0); bc("nn_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_mxblk"); E(mov_reg, 5, 0)
    E(ldr_sp, 2, 8); E(strb_w, 2, 5, B_NOTE); E(ldr_sp, 3, 12); E(strb_w, 3, 5, B_VEL)
    E(bl, "c_mxrnd"); E(strb_imm, 0, 5, B_RND)
    now(0); E(cmp_imm, 0, 0); E(b_cond, "nn_t", "ne"); E(movs_imm, 0, 1)
    a.label("nn_t"); E(str_imm, 0, 5, B_ENV)
    E(mov_reg, 0, 4); E(bl, "c_mxnsrc")
    a.label("nn_x")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7, 8], lr=True)); E(b_w, prev["non"])

    # ---- c_mxnsrc(r0 = track): the note sources (velocity, note, random) now, their destinations marked at once
    a.label("c_mxnsrc")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(bl, "c_mxblk"); E(mov_reg, 4, 0)
    E(ldrb_w, 0, 4, B_VEL); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(strb_imm, 0, 4, B_SRC + 0)
    E(ldrb_w, 0, 4, B_NOTE); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(subs_imm8, 0, 60); E(lsls_imm, 0, 0, 1)
    E(cmp_imm, 0, 127); E(b_cond, "ns_n1", "le"); E(movs_imm, 0, 127)
    a.label("ns_n1"); E(mov_reg, 1, 0); E(adds_imm8, 1, 127); E(b_cond, "ns_n2", "pl"); E(movs_imm, 0, 0); E(subs_imm8, 0, 127)
    a.label("ns_n2"); E(strb_imm, 0, 4, B_SRC + 1)
    E(ldrb_imm, 0, 4, B_RND); E(strb_imm, 0, 4, B_SRC + 2)
    E(movs_imm, 5, 0)
    a.label("ns_l")
    E(lsls_imm, 1, 5, 1); E(ldrh_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "ns_n", "eq")
    E(movs_imm, 1, B_SRC); E(adds_reg, 1, 1, 5); E(ldrb_reg, 2, 4, 1); E(movs_imm, 1, B_LAST); E(adds_reg, 1, 1, 5); E(strb_reg, 2, 4, 1)
    E(bl, "c_mxcode"); E(mov_reg, 1, 0); E(mov_reg, 0, 6); E(bl, "c_mxmark")
    a.label("ns_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 3); E(b_cond, "ns_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxtrig (SC16's tail of the drum trigger: r0 = 0, r1 = 0xF00, r2 = 0x99 + drum): the hit's time
    a.label("c_mxtrig")
    E(push_list, [0, 1, 2, 3, 4], lr=True)
    E(mov_reg, 4, 2); E(subs_imm8, 4, 0x99); E(cmp_imm, 4, 3); E(b_cond, "tg_x", "hi")
    E(bl, "c_mxst"); E(lsls_imm, 1, 4, 2); E(adds_reg, 0, 0, 1)
    now(1); E(cmp_imm, 1, 0); E(b_cond, "tg_t", "ne"); E(movs_imm, 1, 1)
    a.label("tg_t"); E(str_imm, 1, 0, G_HIT)
    a.label("tg_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["trig"])

    # ---- c_mxpage(r0 = track) -> r0 = 1 when the matrix page of the track is the one the knobs move (mode on, no CC editor, no step-drummer view)
    a.label("c_mxpage")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); E(b_cond, "pg_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("pg_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_mxknob (slot 4 of the macro handlers: obj, knob, delta): the matrix page of MIDI 1 / 2, else the previous slot
    a.label("c_mxknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_mxpage"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 5, 4); E(movs_imm, 0, 7); E(ands_reg, 5, 0)                          # r5 = knob 0..7
    E(mov_reg, 0, 6); E(bl, "c_mxblk"); E(mov_reg, 4, 0)                                # r4 = the block
    E(ldr_sp, 0, 0); E(bl, L["c_vclr"]); E(mov_reg, 7, 0)                          # r7 = Clear held
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("kn_src", "eq")
    # Shift: a source's parameter
    imm32(1, T["pk"]); E(ldrb_reg, 1, 1, 5); E(cmp_imm, 1, 0xFF); bc("kn_x", "eq")
    E(adds_imm8, 1, B_PAR); E(cmp_imm, 7, 0); E(b_cond, "kn_sp", "eq")
    E(subs_imm8, 1, B_PAR); imm32(2, T["pdef"]); E(ldrb_reg, 0, 2, 1); E(adds_imm8, 1, B_PAR); E(strb_reg, 0, 4, 1); E(b, "kn_x")
    a.label("kn_sp")
    E(ldrb_reg, 0, 4, 1); E(ldr_sp, 2, 8); E(adds_reg, 0, 0, 2)
    E(cmp_imm, 0, 0); E(b_cond, "kn_p1", "ge"); E(movs_imm, 0, 0)
    if V2:
        a.label("kn_p1"); E(mov_reg, 2, 1); E(subs_imm8, 2, B_PAR); imm32(3, T["pmx"]); E(ldrb_reg, 2, 3, 2); E(cmp_reg, 0, 2); E(b_cond, "kn_p2", "le"); E(mov_reg, 0, 2)
    else:
        a.label("kn_p1"); E(cmp_imm, 0, 127); E(b_cond, "kn_p2", "le"); E(movs_imm, 0, 127)
    a.label("kn_p2"); E(strb_reg, 0, 4, 1); E(b, "kn_x")
    # a source: Clear = off; else the slow knob (an accumulator for the knob touched last)
    a.label("kn_src")
    E(cmp_imm, 7, 0); E(b_cond, "kn_ac", "eq")
    E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(bl, "c_mxset"); E(b, "kn_x")
    a.label("kn_ac")
    E(bl, "c_mxst"); E(mov_reg, 7, 0)
    E(lsls_imm, 1, 6, 4); E(orrs_reg, 1, 5); E(ldrb_imm, 2, 7, G_LK); E(cmp_reg, 2, 1); E(b_cond, "kn_sm", "eq")
    E(strb_imm, 1, 7, G_LK); E(movs_imm, 2, 0); E(strb_imm, 2, 7, G_ACC)
    a.label("kn_sm")
    E(strb_imm, 1, 7, G_OVK); now(0); E(str_imm, 0, 7, G_OVT)                           # the overlay: this knob, now
    E(movs_imm, 2, G_ACC); E(raw, ldrsb_reg(2, 7, 2)); E(ldr_sp, 3, 8); E(adds_reg, 2, 2, 3)
    E(movs_imm, 3, DIV); E(raw, sdiv(0, 2, 3)); E(muls, 3, 0); E(subs_reg, 2, 2, 3); E(strb_imm, 2, 7, G_ACC)
    E(cmp_imm, 0, 0); E(b_cond, "kn_x", "eq")
    E(lsls_imm, 1, 5, 1); E(ldrh_reg, 2, 4, 1); E(adds_reg, 2, 2, 0)
    E(cmp_imm, 2, 0); E(b_cond, "kn_q1", "ge"); E(movs_imm, 2, 0)
    a.label("kn_q1"); imm32(3, PMAX); E(cmp_reg, 2, 3); E(b_cond, "kn_q2", "le"); E(mov_reg, 2, 3)
    a.label("kn_q2"); E(mov_reg, 0, 6); E(mov_reg, 1, 5); E(bl, "c_mxset")
    a.label("kn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_mxkleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: on the matrix page the sources (or, with Shift, their parameters)
    a.label("c_mxkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_mxpage"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, "c_mxblk"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(mov_reg, 7, 0); E(movs_imm, 6, 0)
    a.label("kl_l")
    E(cmp_imm, 7, 0); E(b_cond, "kl_sh", "ne")
    E(lsls_imm, 1, 6, 1); E(ldrh_reg, 0, 4, 1); E(cmp_imm, 0, 0); E(b_cond, "kl_dk", "eq")
    E(subs_imm8, 0, 1); E(lsrs_imm, 1, 0, 4); imm32(2, T["dcol"]); E(ldrb_reg, 1, 2, 1)   # r1 = the colour
    E(movs_imm, 2, 15); E(ands_reg, 0, 2); E(adds_imm8, 0, 1); E(lsls_imm, 0, 0, 3); E(subs_imm8, 0, 1)   # r0 = 8 x amount - 1
    E(b, "kl_put")
    a.label("kl_sh")                                                                    # Shift: the parameter's zone colour, the position's brightness
    imm32(1, T["pk"]); E(ldrb_reg, 2, 1, 6); E(cmp_imm, 2, 0xFF); E(b_cond, "kl_dk", "eq")
    E(movs_imm, 1, B_PAR); E(adds_reg, 1, 1, 2); E(ldrb_reg, 0, 4, 1)                  # r0 = the parameter, r2 = its index
    E(cmp_imm, 2, 3); E(b_cond, "kl_z4", "ne")
    E(movs_imm, 1, 5); E(muls, 1, 0); E(lsrs_imm, 1, 1, 7); imm32(3, T["scol"]); E(ldrb_reg, 1, 3, 1); E(movs_imm, 0, 100); E(b, "kl_put")
    a.label("kl_z4")
    if V2: E(lsrs_imm, 1, 0, 5); E(movs_imm, 3, 5); E(muls, 3, 2); E(adds_reg, 1, 1, 3); imm32(3, T["zcol"]); E(ldrb_reg, 1, 3, 1)
    else: E(lsrs_imm, 1, 0, 5); E(lsls_imm, 3, 2, 2); E(adds_reg, 1, 1, 3); imm32(3, T["zcol"]); E(ldrb_reg, 1, 3, 1)
    if SYNC:                                                                            # LFO 2 (index 0): |2 r - 31| x 4, dim at the zone's centre
        E(movs_imm, 3, 31); E(ands_reg, 0, 3); E(cmp_imm, 2, 0); E(b_cond, "kl_np", "ne")
        E(lsls_imm, 0, 0, 1); E(subs_imm8, 0, 31); E(b_cond, "kl_ab", "pl"); E(raw, h(0x4240))      # rsbs r0, r0, #0
        a.label("kl_ab"); E(lsls_imm, 0, 0, 2); E(b, "kl_put")
        a.label("kl_np"); E(lsls_imm, 0, 0, 2); E(adds_imm8, 0, 3)
    else:
        E(movs_imm, 3, 31); E(ands_reg, 0, 3); E(lsls_imm, 0, 0, 2); E(adds_imm8, 0, 3)
    a.label("kl_put"); E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 1); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1); E(b, "kl_n")
    a.label("kl_dk"); E(movs_imm, 0, 0); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    a.label("kl_n"); E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_l", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxovl(r0 = track) -> r0 = 1 while the overlay of a source knob of this track is shown; clobbers r1-r3
    a.label("c_mxovl")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_mxpage"); E(cmp_imm, 0, 0); E(b_cond, "ov_0", "eq")
    E(bl, "c_mxst"); E(ldrb_imm, 1, 0, G_OVK); E(lsrs_imm, 1, 1, 4); E(cmp_reg, 1, 4); E(b_cond, "ov_0", "ne")
    E(ldr_imm, 1, 0, G_OVT); now(2); E(subs_reg, 2, 2, 1); imm32(1, OVL_MS); E(cmp_reg, 2, 1); E(b_cond, "ov_0", "hs")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ov_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_mxclrh() -> r0 = 1 while Clear is held (the controller's held buttons, as mpatch reads them); clobbers r1-r3
    a.label("c_mxclrh")
    E(push_list, [], lr=True)
    imm32(0, MP.MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(pop_list, [], pc=True)

    # ---- c_mxpad (the MIDI Preset view's slot 0: view, pad, velocity): Clear + pad 6 = the matrix off; pads 9-24 swallowed under the overlay
    a.label("c_mxpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 1, 5); E(b_cond, "pd_6", "eq")
    E(cmp_imm, 1, 8); bc("pd_prev", "lo"); E(cmp_imm, 1, 23); bc("pd_prev", "hi")
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pd_prev", "hi")
    E(bl, "c_mxovl"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(b, "pd_x")
    a.label("pd_6")
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pd_prev", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(bl, "c_mxclrh"); E(cmp_imm, 0, 0); bc("pd_prev", "eq")
    E(movs_imm, 5, 0)
    a.label("pd_l"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(bl, "c_mxset"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 8); E(b_cond, "pd_l", "lo")
    a.label("pd_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("pd_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_mxleds (the MIDI Preset view's slot 7: view) -> r0 = the LED buffer: pad 6; the overlay on pads 9-24
    a.label("c_mxleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("pl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("pl_x", "eq")
    E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(movs_imm, 1, COL_MX[1]); E(cmp_imm, 0, PAGE); E(b_cond, "pl_c", "ne"); E(movs_imm, 1, COL_MX[0])
    a.label("pl_c"); E(strh_imm, 1, 5, 10)
    E(mov_reg, 0, 6); E(bl, "c_mxovl"); E(cmp_imm, 0, 0); bc("pl_x", "eq")
    E(bl, "c_mxst"); E(ldrb_imm, 7, 0, G_OVK); E(movs_imm, 1, 7); E(ands_reg, 7, 1)
    E(mov_reg, 0, 6); E(bl, "c_mxblk"); E(lsls_imm, 1, 7, 1); E(ldrh_reg, 0, 0, 1); E(cmp_imm, 0, 0); bc("pl_x", "eq")
    E(subs_imm8, 0, 1); E(lsrs_imm, 0, 0, 4); imm32(1, T["dmap"]); E(ldrb_reg, 4, 1, 0)   # r4 = page << 4 | index
    E(lsrs_imm, 0, 4, 4); E(lsls_imm, 0, 0, 4); imm32(6, T["rows"]); E(adds_reg, 6, 6, 0)  # r6 = the page's 16 codes
    E(movs_imm, 7, 0)
    a.label("pl_l")
    E(ldrb_reg, 0, 6, 7); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "pl_put", "eq")
    E(lsrs_imm, 2, 4, 4); imm32(3, T["pdim"]); E(ldrb_reg, 1, 3, 2)
    E(movs_imm, 3, 15); E(ands_reg, 3, 4); E(cmp_reg, 3, 7); E(b_cond, "pl_put", "ne")
    imm32(3, T["pbri"]); E(ldrb_reg, 1, 3, 2)
    a.label("pl_put"); E(mov_reg, 0, 7); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "pl_l", "lo")
    E(lsrs_imm, 2, 4, 4); imm32(3, T["pbri"]); E(ldrb_reg, 1, 3, 2); E(lsls_imm, 0, 2, 1); E(strh_reg, 1, 5, 0)   # the destination's page pad
    a.label("pl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxgath(r0 = track) in c_mpsave: mpatch's gather, then the matrix at padding + 64 (the save writes the whole padding)
    a.label("c_mxgath")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_mpgather"])
    E(mov_reg, 0, 4); E(bl, "c_mxblk"); E(mov_reg, 5, 0); imm32(6, PK.BUF + 64)
    E(movs_imm, 0, ord("M")); E(strb_imm, 0, 6, 0); E(movs_imm, 0, ord("X")); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 2)
    E(movs_imm, 7, 0)
    a.label("ga_l"); E(ldrb_reg, 0, 5, 7); E(adds_imm8, 7, 3); E(strb_reg, 0, 6, 7); E(subs_imm8, 7, 2); E(cmp_imm, 7, 20); E(b_cond, "ga_l", "lo")
    E(movs_imm, 0, 0x5A); E(movs_imm, 7, 0)
    a.label("ga_s"); E(ldrb_reg, 1, 6, 7); E(adds_reg, 0, 0, 1); E(adds_imm8, 7, 1); E(cmp_imm, 7, 23); E(b_cond, "ga_s", "lo")
    E(strb_imm, 0, 6, 23)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mxappl(r0 = track) in c_mpload (r5 = the slot there): mpatch's apply, then the matrix of the patch (none: off)
    a.label("c_mxappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, L["c_mpapply"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20); imm32(2, MP.OFF + 64); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + 64); E(movs_imm, 3, 24); E(bl, L["c_mpr"])
    E(movs_imm, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "ap_go", "ne"); E(cmp_imm, 1, 24); E(b_cond, "ap_go", "ne")
    imm32(6, PK.BUF + 64)
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, ord("M")); E(b_cond, "ap_go", "ne"); E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, ord("X")); E(b_cond, "ap_go", "ne")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 1); E(b_cond, "ap_go", "ne")
    E(movs_imm, 0, 0x5A); E(movs_imm, 1, 0)
    a.label("ap_s"); E(ldrb_reg, 2, 6, 1); E(adds_reg, 0, 0, 2); E(adds_imm8, 1, 1); E(cmp_imm, 1, 23); E(b_cond, "ap_s", "lo")
    E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(ldrb_imm, 1, 6, 23); E(cmp_reg, 0, 1); E(b_cond, "ap_go", "ne")
    E(movs_imm, 5, 1)                                                                   # r5 = the patch holds a matrix
    E(mov_reg, 0, 4); E(bl, "c_mxblk"); E(movs_imm, 3, 0)
    a.label("ap_p"); E(adds_imm8, 3, 19); E(ldrb_reg, 1, 6, 3); E(subs_imm8, 3, 19)
    if V2: E(push_list, [0]); imm32(0, T["pmx"]); E(ldrb_reg, 0, 0, 3); E(cmp_reg, 1, 0); E(b_cond, "ap_pm", "ls"); E(mov_reg, 1, 0); a.label("ap_pm"); E(pop_list, [0])
    else: E(cmp_imm, 1, 127); E(b_cond, "ap_p1", "ls"); E(movs_imm, 1, 127)
    a.label("ap_p1"); E(adds_imm8, 3, B_PAR); E(strb_reg, 1, 0, 3); E(subs_imm8, 3, B_PAR); E(adds_imm8, 3, 1); E(cmp_imm, 3, 4); E(b_cond, "ap_p", "lo")
    a.label("ap_go")                                                                    # the 8 positions (0 without a matrix)
    E(movs_imm, 7, 0)
    a.label("ap_l")
    E(movs_imm, 2, 0); E(cmp_imm, 5, 0); E(b_cond, "ap_set", "eq")
    E(lsls_imm, 1, 7, 1); E(adds_imm8, 1, 3); E(ldrb_reg, 2, 6, 1); E(adds_imm8, 1, 1); E(ldrb_reg, 1, 6, 1); E(lsls_imm, 1, 1, 8); E(orrs_reg, 2, 1)
    imm32(1, PMAX); E(cmp_reg, 2, 1); E(b_cond, "ap_set", "ls"); E(movs_imm, 2, 0)
    a.label("ap_set"); E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, "c_mxset")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ap_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble(), T, PMAX


def bl_target(img, addr, base):
    h1, h2 = struct.unpack_from("<HH", img, addr - base)
    assert h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000, hex(addr)
    s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
    if s: off -= 1 << 25
    return addr + 4 + off


def bl_sites(img, lo, hi, target, base):
    """the bl instructions in [lo, hi) that call target"""
    out = []
    for a in range(lo, hi - 3, 2):
        h1, h2 = struct.unpack_from("<HH", img, a - base)
        if h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0xD000 and bl_target(img, a, base) == target:
            out.append(a)
    return out


def install(img, report, base_addr):
    """Append the code; the hooks: the DSP service chain's head, the note vtable, the drum trigger, the macro handlers' slots 4 / 7, the MIDI Preset
    view's slots 0 / 7, vcf21's two calls of c_sdfx and vp_row's page limit, mpatch's gather / apply calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vtrack", "c_von", "c_edact", "c_sdview", "c_vpage", "c_vclr", "c_vmark", "c_sdcur", "c_sdfx", "c_sdeng",
                                      "c_sdpat", "c_vflag", "c_vdbit", "vp_row", "c_vsmode")}
    L["c_shift"] = lab("sc15", "c_shift")
    for k in ("c_mpon", "c_mpr", "c_mpgather", "c_mpapply", "c_mpload", "c_mpsave"): L[k] = lab("mpatch", k)
    KN, TP = V.AC64_VT, MP.TMPL_VT
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), non=u(NOTE_VT) & ~1, trig=MP.bw_target(img, TRIG_TAIL, BASE),
                knob=u(KN + 16) & ~1, kleds=u(KN + 28) & ~1, pad=u(TP) & ~1, leds=u(TP + 28) & ~1)
    (code, labels), T, pmax = arm_code(base_addr, L, prev)
    end0 = BASE + len(img)                               # the code before ours (hole.add: base_addr is below it)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or base_addr < 0x08018800          # in the hole: hole.add moves it back
    # vcf21: both calls of c_sdfx (the values and the sweep) -> c_mxfx
    sites = bl_sites(img, BASE + 0x4CDDC, end0, L["c_sdfx"], BASE)
    assert len(sites) == 2, [hex(s) for s in sites]
    for s in sites: img[s - BASE:s - BASE + 4] = bl(s, labels["c_mxfx"])
    # vp_row: pad 6 (index 5) is a page too
    at = [x for x in range(L["vp_row"], L["vp_row"] + 64, 2) if struct.unpack_from("<H", img, x - BASE)[0] == 0x2D04]
    assert len(at) == 1, at
    struct.pack_into("<H", img, at[0] - BASE, 0x2D05)
    # mpatch: the gather of the save, the apply of the load
    for site_of, orig, ours in ((L["c_mpsave"], L["c_mpgather"], "c_mxgath"), (L["c_mpload"], L["c_mpapply"], "c_mxappl")):
        s = bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    assert len(bl_sites(img, BASE + 0x4CDDC, end0, L["c_mpapply"], BASE)) == 0       # nobody else applies a patch
    # the heads
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_mxtick"])
    img[TRIG_TAIL - BASE:TRIG_TAIL - BASE + 4] = b_w(TRIG_TAIL, labels["c_mxtrig"])
    struct.pack_into("<I", img, NOTE_VT - BASE, labels["c_mxnon"] | 1)
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_mxknob"] | 1)
    struct.pack_into("<I", img, KN + 28 - BASE, labels["c_mxkleds"] | 1)
    struct.pack_into("<I", img, TP - BASE, labels["c_mxpad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_mxleds"] | 1)
    prev.update(c_sdfx_sites=sites[0], c_sdfx_sites2=sites[1], vp_row_cmp=at[0], pmax=pmax)
    labels.update({f"t_{k}": v for k, v in T.items()})
    return labels, code, prev
