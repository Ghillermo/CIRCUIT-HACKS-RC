"""SC19: the settings made with our patches are saved in the project (ARM side).

Where: the 65 bytes of the session blobs that no parameter descriptor covers ("XMEM", flat index 0..64, see FLAT) travel with every
project (stock save copies the whole blobs into the session record, stock load copies them back; verified on the hardware with the
SC182D / SC183D probes: they survive Save -> power off -> Load, are per project, follow "save as copy", are not touched by patch changes,
and are NOT reset by "new project").  What is stored:
    XM[0..27]   Master FX slot assignments (7 slots x 4 bytes, the block's S_SLOT layout)
    XM[28..63]  drums: 9 bytes per drum, d = 0..3 at XM[28 + 9 d]
                  byte c-1 (c = 1..8 = mailbox code PE, RMF, LFO, LSPD, EC, RES, ENVS, RMA): bits 0-6 value (two's complement for the
                  bipolar codes), bit 7 = bit c-1 of the extended values (bits 3..0 K4 start point, 7..4 K6 bitcrush)
                  byte 8: filter mode (code 9, bits 0-2); drum 0: bits 3-7 = SIGNATURE (a project that does not carry it is read as empty)
    XM[64]      synth source modes (bits 0-2 Synth 1, bits 3-5 Synth 2)
The drum values are the state (the ARM sends the DSP the ABSOLUTE value, drums2_dsp.ABS); the slots and the modes live in RAM as before and
are copied to XMEM right before every stock save (the bl to the save function is hooked) and back after every project load.

Events (hooks):
    0x0802F5B8  end of the stock "apply session" (project load, new project, power-up): sets RESYNC (block byte 179 bit 0)
    0x0802F5FA  tail of the stock "new project" defaults: sets NEW (bit 1)
    0x0802FE5E  the bl to the stock save: XMEM <- RAM, then the stock save
The DSP service tick (c_dtick19, first in the chain as in SC18) does the work when RESYNC is set and the four drum handlers exist:
zero XMEM (NEW, or the signature is missing), XMEM -> RAM (slots, modes + resend the Audio In group), mark every drum parameter dirty
(one DSP message per drum per tick), switch every Master FX effect and the song pointer off (c_clrall).
Drum knob turns (c_dk19, slot 4 of the drum macro handlers) change the XMEM bytes and mark them dirty; the tick sends the absolute value.
Also in SC19: synth source modes 0..4 only (the delay / reverb return modes were dropped); the chromatic drum view shows all four rows again;
the master resonance step is on the real "1-16 / 17-32" button (id 21, LED 53), ids 16 / 17 (Record / Play) are stock again.
Dirty bits per drum (handler padding bytes, zeroed by the SC18 constructor hook): +0x3E bit 7 = mailbox tag, bits 0-6 = codes 1-7,
+0x3F bits 0-2 = codes 8, 9 and the extended values (code 10).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (sub_sp_imm, add_sp_imm)  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, ldrb_w, strb_w, strb_imm, strh_imm, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, h, subs_imm8, adds_imm8, adds_reg, subs_reg,
                   ands_reg, orrs_reg, bics_reg, eors_reg, muls, tst_reg, adds_imm3, lsls_reg, lsrs_reg, ldrb_reg, strb_reg, strh_reg)

CTXP = 0x200069B4
STORE_VT = 0x0805BBAC
STORE_COPY = 0x0803BBE2               # vtable slot 3: copy `size` bytes from r1 into the store
CTX_SYNTH1, CTX_SYNTH2, CTX_DRUMS, CTX_PROJECT = 0x344, 0x348, 0x34C, 0x350
FLAT = ([(CTX_PROJECT, o) for o in (11, 12, 13, 14, 15, 30)]
        + [(CTX_DRUMS, o) for o in (7, 8, 9, 10, 18, 19, 20, 21, 29, 30, 31, 32, 40, 41, 42)]       # offset 43 (last byte of the store) is not used
        + [(CTX_SYNTH1, o) for o in list(range(18, 32)) + [101, 103, 104] + list(range(111, 116))]
        + [(CTX_SYNTH2, o) for o in list(range(18, 32)) + [101, 103, 104] + list(range(111, 116))])
N_XM = len(FLAT)                      # 65
S1_FIRST = next(i for i, (c, o) in enumerate(FLAT) if c == CTX_SYNTH1)       # flat index of the first byte kept in the Synth 1 store (21)
S2_FIRST = next(i for i, (c, o) in enumerate(FLAT) if c == CTX_SYNTH2)       # ... Synth 2 store (43)
N_SYNTH_B = S2_FIRST - S1_FIRST       # 22 bytes per synth store
XM_SLOTS, XM_DRUMS, XM_MODES = 0, 28, 64
XM_SIG = XM_DRUMS + 8                 # drum 0, byte 8: bits 3-7 = signature
SIG = 21                              # 5 bits
S_SLOT, S_SLOTH, S_HELD, FLAGS = 148, 176, 5, 179
F_RESYNC, F_NEW, F_MSG = 1, 2, 4
SAVE_MASK = False                     # SC30: the save skips the XMEM copy only while a load / new project is pending (bits 0-1).  Before, any bit stopped it, and since SC20
                                      # the VCF tick keeps bit 3 ("initialised this session") set: no save wrote the slots, the modes or the signature any more
GFX_GLOBAL = False                    # SC30: the Master FX slot assignments are loaded from the project only once after power-up; a later project load / new project keeps the RAM
                                      # ones (the effects and the song pointer are still switched off).  The top-row parameters were already RAM only.  The save still copies them
GFX_SESSION = False                   # SC40.9 (not with GFX_GLOBAL): the slot assignments are loaded from every project that carries our signature; a project
                                      # without it (and a new project) keeps the RAM ones
F_GBOOT = 0x20                        # FLAGS bit (GFX_GLOBAL): the first deferred load since power-up is done (the block is zero when it is created)
BLOB_KEEP = False                     # SC19.4: the whole-blob copy into a synth store (vtable slot 3, 0x0803BBE2: a patch change, the stock "reload patch" 0x0802FC82, an apply
                                      # with another patch) keeps our 22 bytes of that store (the library patches have zeros there)
REC_RESTORE = False                   # SC19.4: after a project load the 65 bytes are copied from the session RECORD into the live stores (see c_xm_from_rec)
SESSION_OBJ = 0x2003D71C              # session manager (the stock save / load object); [obj + 0x14] = the session record
REC_BASE = {CTX_SYNTH1: 0x26D14, CTX_SYNTH2: 0x26E68, CTX_DRUMS: 0x26FBC, CTX_PROJECT: 0x26FE8}   # where the stock save puts each blob in the record
FIX_LOCK = False                      # SC19.3: c_xm_load runs in the DSP service tick, which already holds the service semaphore: the stock MARK_DIRTY (0x0803BDCC) takes it
                                      # again (0x08021064 waits for a count the service itself zeroed) and the device froze for ever -> call its dirty-bit setter 0x08021FDC directly
MARK_DIRTY_SVC = 0x08021FDC
GUARD = False                         # SC19.2: the deferred work waits after power-up (stage A: BOOT_A ms, no DSP message; stage B: BOOT_B ms, the drum messages)
BOOT_A, BOOT_B = 15000, 30000
TICK = 0x2000081C                     # HAL uwTick (ms since power-up)
REMAP = False                         # SC19.8: the drum knobs follow the panel labels (see REMAP_* below); the stock parameters keep their id, their saved value and their MIDI
# physical knob (0..7 = K1..K8) -> what it turns.  Codes are the mailbox codes (MAP2); "stock" entries are the stock macro knob index the stock handler is called with
# (1 pitch, 3 decay, 5 distortion, 7 EQ), so the parameter, the project and the MIDI are the stock ones: the MIDI follows the parameter, not the knob.
REMAP_PLAIN = {1: 2, 3: 5, 5: 6, 6: 3}      # K2 osc mod = ring mod frequency, K4 filter envelope = env -> cutoff, K6 resonance, K7 modulation = LFO amount
REMAP_PLAIN_STOCK = {0: 1, 2: 3, 4: 7, 7: 5}  # K1 oscillator = pitch, K3 amp envelope = decay (+ start point), K5 filter frequency = EQ, K8 FX = distortion (+ bitcrush)
REMAP_SHIFT = {0: 1, 1: 8, 3: 7, 4: 9, 6: 4}  # Shift: K1 pitch envelope, K2 ring mod amount, K4 envelope shape, K5 filter mode, K7 LFO speed (K6: free)
REMAP_SHIFT_STOCK = {2: 3, 7: 5}            # Shift + K3 / K8: the stock handler as before (nothing of ours)
# LED of each knob position: (position, code alone, code with Shift); None = not ours in that layer (the stock LED)
REMAP_LEDS = ((0, None, 1), (1, 2, 8), (3, 5, 7), (4, None, 9), (5, 6, 6), (6, 3, 4))
REMAP_LEDS_XT_NS = ((0, None, 1), (1, 2, 8), (3, 5, 7), (4, None, 9), (5, 6, 6), (6, 3, 4), (7, None, 10))   # EXTRAS without the slope: Shift + K8 shows the distortion type
REMAP_LEDS_XT = ((0, None, 1), (1, 2, 8), (3, 5, 7), (4, None, 9), (5, 6, 11), (6, 3, 4), (7, None, 10))    # EXTRAS: Shift + K6 shows the slope, Shift + K8 the distortion type
EXTRAS = False                        # SC19.9 (needs REMAP): per drum a distortion type (2 bits) and a filter slope (1 bit), sent to the DSP in the bits 8-10 of the extended-values word
# where the 3 bits of drum d live: (flat index of the byte, mask); bits 0-1 = type, bit 2 = slope.  The byte 8 of drum 0 keeps the signature in its upper bits, so the bits of drum 0 are
# in the byte 8 of drums 1 and 2 (bits nothing else uses).  Old projects have 0 there = the stock distortion and 12 dB, the behaviour before.
XT_BITS = [(XM_DRUMS + 9 + 8, 0x40), (XM_DRUMS + 9 + 8, 0x80), (XM_DRUMS + 18 + 8, 0x40)] + \
          [(XM_DRUMS + 9 * d + 8, m) for d in (1, 2, 3) for m in (0x08, 0x10, 0x20)]
EXTRAS_SLOPE = False                  # also Shift + K6 = filter slope 12 / 24 dB (needs drums2_dsp.SLOPE_PASS); dropped for SC19.9 (the user discarded it)
REMAP_XT = {5: 1, 7: 0}                     # Shift + K6 = filter slope (which = 1, with EXTRAS_SLOPE), Shift + K8 = distortion type (which = 0)
CLEAR = False                        # SC20.1 (needs REMAP): Clear + a knob of ours: right = back to the default value (blue LED), left = nothing to delete (red LED); the stock-routed knobs keep the stock Clear (their LED shown at the right position)
CLR_RED, CLR_BLUE = 0x53, 0x46        # the stock LED codes of the Clear feedback (halfwords at 0x08056464 + 0x26A / + 0x1A)


FSEL_STOCK0 = False                   # R0901 / SC41.4 (see use_fselstock)
SPLIT3 = False                        # SC41.7 (see use_k3split)
K3_TAIL, K3_OFF = 0x27024, 160        # the block in the session record's tail: + 160 "DRX1", + 164 sum, + 165 + 3 d = attack, start, cut of drum d (tail + 160..176 free)
K3_SIG = 0x31585244                   # "DRX1"
K3_LIM = 120                          # start / cut at most 120 / 128 of the sample
K3_ATK_MAX = 1.0                      # s: the attack at 127 (time ~ (A / 127)^2)
K3_COL_WHITE = 0x01                   # the K3 LED: the attack (and, with Shift, the cut) in white; the start in the drum's colour


def use_k3split():
    """SC41.7 (the user, 2026-10-15: K3 «izquierda: decay, derecha: ataque, centro neutro»; Shift + K3 «izquierda: inicio, derecha: corte»; before, the start point
    lived left of decay 0 on K3, so it only played with the shortest decay).  Needs drums2_dsp.use_k3split().
      * K3 (amp envelope): the stock decay as always; turned right past its maximum (127, the whole sample) = an amp attack 1..127 (~(A / 127)^2 s, up to 1 s);
        turned left the attack goes back to 0 first.  Neutral = decay 127, attack 0.
      * Shift + K3: left = the start point moves into the sample (S / 128, up to 120), right = a cut from the end (E / 128, up to 120); one goes back to 0 before the
        other moves.  Neutral = the whole sample.  (Before: Shift + K3 = the stock decay again.)
      * Clear + K3 right: attack, start and cut to 0 too (the stock puts the decay to its default).
      * Stored per project in the session record's tail (+ 160: "DRX1", a sum, 3 bytes per drum), which the stock saves and loads; a project without it (a stock one,
        an older one) = 0 = neutral, with its old start point (the XMEM nibble, 0..15 = s / 64) taken over as S = 2 s.  A new project: 0.
      * The DSP service tick writes AINC (= C / A^2 limited to 1), STARTF = S << 16 and ENDC = E << 16 into the drum's block with the extended values.
      * LED of K3: the attack in white (its value as brightness) while there is one, else the stock decay; with Shift the start in the drum's colour, the cut in white."""
    global SPLIT3
    SPLIT3 = True


def use_fselstock():
    """R0901 / SC41.4 (the user, 2026-10-14: «los usuarios reportan que el sonido de los samples no es igual que el de Circuit stock … asegurarse de
    que el filtro seleccionado por defecto es el mismo que el de stock»): the drums' filter mode is a stored value 0..4 that defaulted to 0 = the DJ
    filter, which also flattens the stock tilt EQ, so K5 did not do what it does on a stock Circuit.  The value sent to the DSP now swaps 0 and 4:
    stored 0 (every new project, every project that never touched it) = the stock tilt EQ, as the original; 1 band-pass, 2 notch, 3 comb as before;
    4 = the DJ filter.  The DSP and its numbering do not change."""
    global FSEL_STOCK0
    FSEL_STOCK0 = True


def use_blue7():
    """SC37.9 (SC37.8 on the device, 2026-10-11: «en drums, clear+derecha funciona pero no se enciende led azul»): the stock reads its Clear colours from a
    palette in RAM, where + 0x1A is 0x07 (a bright blue); 0x46, the flash palette's entry, is a dim red-orange (RGB words are B, G, R).  The stock itself
    (emulation of the original firmware, Drum 1, Clear + K4 right x 40) writes 0x07; the red 0x53 was right."""
    global CLR_BLUE
    CLR_BLUE = 0x07
O_CLR = 0x3F                          # macro handler byte: bits 0-2 = dirty bits (codes 8-10), bit 3 = a Clear LED is shown, bit 4 = blue, bits 5-7 = the knob position
CLEAR_BOTH = False                    # SC23.5 (needs CLEAR): Clear + a plain knob also puts the Shift layer of that knob back to its default (Shift disables the Clear button: the stock ignores it)
K8_BRIGHT = False                     # SC23.5 (needs REMAP, KNOB_LEVELS): the plain K8 (distortion left of... bitcrush) shows max(distortion, bitcrush) as brightness: dark with no effect, brighter either way
KNOB_LEVELS = False                   # SC19.6: the new drum knobs (K1 / K3 / K5 / K7) show their value as LED brightness, like the stock K2 / K4 / K6 / K8 (see knob_levels_code)
LED_CONV_HOOK = 0x080342B0            # inside the stock LED colour converter 0x0803423C (knob LEDs 60..68): ldrh r7, [r6] ; movs r4, #0xff
LED_CONV_BYTES = bytes.fromhex("3788ff24")
GFX_OFF = 40
SC14_MODE, SC14_HELD = 18, 4
MARK_DIRTY = 0x0803BDCC
N_MODES = 5                           # synth source modes 0..4 (noise, inputs 1 / 2, inverted): the delay / reverb return modes were dropped
CTX_PTR = 0x200069E4
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
O_FLAGS, O_DELTA = 0x3E, 0x3F
LOAD_END, LOAD_END_TXT = 0x0802F5B8, "pop.w {r0, r4, r5, r6, r7, r8, sb, sl, fp, pc}"
NEW_TAIL, NEW_TAIL_TXT, NEW_TARGET = 0x0802F5FA, "b.w #0x8029a00", 0x08029A00
SAVE_CALL, SAVE_CALL_TXT, SAVE_FN = 0x0802FE5E, "bl #0x802f63c", 0x0802F63C
MH_VT = 0x0805AADC
MH_SLOT4 = MH_VT + 0x10
MH_SLOT7 = MH_VT + 0x1C
KNOB_CODES = ((0, 7, 1), (2, 2, 8), (4, 3, 4), (6, 5, 9))     # (knob index, code on its own, code with Shift) = MAP2
UNIPOLAR = (2, 6, 8)
MAP2 = dict(plain={0: 7, 2: 2, 4: 3, 6: 5}, shift={0: 1, 2: 8, 4: 4, 6: 9, 7: 6})

INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)          # LDR.W Rt,[Rn,#imm12]
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def asrs_imm(rd, rm, imm): return h(0x1000 | imm << 6 | rm << 3 | rd)           # ASRS Rd,Rm,#imm5
def uxth(rd, rm): return h(0xB280 | rm << 3 | rd)


def table():
    t = b"".join(struct.pack("<HH", c, o) for c, o in FLAT)
    if REC_RESTORE: t += b"".join(struct.pack("<I", REC_BASE[c] + o) for c, o in FLAT)       # record offset of every byte, after the (ctx, offset) pairs
    if EXTRAS: t += b"".join(bytes([i, m]) for i, m in XT_BITS)                              # (flat index, mask) of the 12 distortion type / slope bits
    return t


def arm_code(base, tab, L, DB, STRIDE, EXT):
    a = Asm(base)
    zc = [0]
    SH = STRIDE.bit_length() - 1

    def bc(target, cond):                              # conditional branch, +-2KB
        zc[0] += 1; n = f"_c{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    # ---------------------------------------------------------------- XMEM access
    # ---- c_xpp(r0 = ctx offset, r1 = byte offset) -> r0 = address in the live store or 0   (clobbers r1-r3)
    a.label("c_xpp")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    a.emit(movw, 2, CTXP & 0xFFFF); a.emit(movt, 2, CTXP >> 16); a.emit(ldr_imm, 2, 2, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "xp_none", "eq")
    a.emit(adds_reg, 2, 2, 0); a.emit(ldr_imm, 2, 2, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "xp_none", "eq")
    a.emit(ldr_imm, 3, 2, 0); a.emit(movw, 0, STORE_VT & 0xFFFF); a.emit(movt, 0, STORE_VT >> 16)
    a.emit(cmp_reg, 3, 0); a.emit(b_cond, "xp_none", "ne")
    a.emit(ldr_imm, 1, 2, 0x10); a.emit(cmp_reg, 4, 1); a.emit(b_cond, "xp_none", "hs")
    a.emit(ldr_imm, 0, 2, 0xC); a.emit(ldr_imm, 0, 0, 0); a.emit(adds_reg, 0, 0, 4)
    a.emit(pop_list, [4], pc=True)
    a.label("xp_none")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

    # ---- c_xp(r0 = flat index) -> r0 = address or 0
    a.label("c_xp")
    a.emit(push_list, [], lr=True)
    a.emit(lsls_imm, 1, 0, 2)
    a.emit(movw, 2, tab & 0xFFFF); a.emit(movt, 2, tab >> 16); a.emit(adds_reg, 2, 2, 1)
    a.emit(ldrh_imm, 0, 2, 0); a.emit(ldrh_imm, 1, 2, 2)
    a.emit(bl, "c_xpp")
    a.emit(pop_list, [], pc=True)

    # ---- c_dget(r0 = drum, r1 = code 1..9) -> r0 = byte, or 0xFFFFFFFF
    a.label("c_dget")
    a.emit(push_list, [], lr=True)
    a.emit(movs_imm, 2, 9); a.emit(muls, 0, 2); a.emit(adds_reg, 0, 0, 1); a.emit(adds_imm8, 0, XM_DRUMS - 1)
    a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dg_inv", "eq")
    a.emit(ldrb_imm, 0, 0, 0); a.emit(pop_list, [], pc=True)
    a.label("dg_inv")
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x43C0)); a.emit(pop_list, [], pc=True)

    # ---- c_dput(r0 = drum, r1 = code, r2 = byte)
    a.label("c_dput")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 2)
    a.emit(movs_imm, 2, 9); a.emit(muls, 0, 2); a.emit(adds_reg, 0, 0, 1); a.emit(adds_imm8, 0, XM_DRUMS - 1)
    a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dp_x", "eq"); a.emit(strb_imm, 4, 0, 0)
    a.label("dp_x"); a.emit(pop_list, [4], pc=True)

    # ---- c_dext_get(r0 = drum) -> r0 = extended values (8 bits)
    a.label("c_dext_get")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0); a.emit(movs_imm, 6, 0)
    a.label("eg_l")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 5, 1); a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 5, 1)       # r1 = k + 1
    a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "eg_n", "eq")
    a.emit(lsrs_imm, 0, 0, 7); a.emit(lsls_reg, 0, 5); a.emit(orrs_reg, 6, 0)
    a.label("eg_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 8); a.emit(b_cond, "eg_l", "lo")
    a.emit(mov_reg, 0, 6); a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_dext_set(r0 = drum, r1 = extended values)
    a.label("c_dext_set")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 7, 1); a.emit(movs_imm, 5, 0)
    a.label("es_l")
    a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 5, 1); a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 5, 1)
    a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "es_n", "eq")
    a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 0, 1)
    a.emit(mov_reg, 1, 7); a.emit(lsrs_reg, 1, 5); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 1, 2); a.emit(lsls_imm, 1, 1, 7); a.emit(orrs_reg, 0, 1)
    a.emit(mov_reg, 2, 0); a.emit(mov_reg, 0, 4); a.emit(adds_imm8, 5, 1); a.emit(mov_reg, 1, 5); a.emit(subs_imm8, 5, 1)
    a.emit(bl, "c_dput")
    a.label("es_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 8); a.emit(b_cond, "es_l", "lo")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_dnib_get(r0 = drum, r1 = shift) -> r0 = nibble ; c_dnib_set(r0 = drum, r1 = shift, r2 = value)
    a.label("c_dnib_get")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1); a.emit(bl, "c_dext_get"); a.emit(lsrs_reg, 0, 4); a.emit(movs_imm, 1, 15); a.emit(ands_reg, 0, 1)
    a.emit(pop_list, [4], pc=True)
    a.label("c_dnib_set")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, "c_dext_get")
    a.emit(movs_imm, 1, 15); a.emit(lsls_reg, 1, 5); a.emit(bics_reg, 0, 1)
    a.emit(mov_reg, 1, 6); a.emit(lsls_reg, 1, 5); a.emit(orrs_reg, 0, 1)
    a.emit(mov_reg, 1, 0); a.emit(mov_reg, 0, 4); a.emit(bl, "c_dext_set")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_dnew(r0 = code, r1 = old byte, r2 = delta) -> r0 = new byte (bit 7 and the bits above the mode kept)
    a.label("c_dnew")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 1)
    a.emit(cmp_imm, 0, 9); a.emit(b_cond, "dn_fsel", "eq")
    a.emit(lsls_imm, 3, 1, 25)
    for c in UNIPOLAR:
        a.emit(cmp_imm, 0, c); a.emit(b_cond, "dn_uni", "eq")
    a.emit(raw, asrs_imm(3, 3, 25)); a.emit(adds_reg, 3, 3, 2)                       # bipolar: -64..63
    a.emit(cmp_imm, 3, 63); a.emit(b_cond, "dn_b1", "le"); a.emit(movs_imm, 3, 63)
    a.label("dn_b1")
    a.emit(movs_imm, 5, 0); a.emit(subs_imm8, 5, 64); a.emit(cmp_reg, 3, 5); a.emit(b_cond, "dn_v", "ge"); a.emit(mov_reg, 3, 5)
    a.emit(b, "dn_v")
    a.label("dn_uni")
    a.emit(lsrs_imm, 3, 3, 25); a.emit(adds_reg, 3, 3, 2)                            # unipolar: 0..127
    a.emit(cmp_imm, 3, 127); a.emit(b_cond, "dn_u1", "le"); a.emit(movs_imm, 3, 127)
    a.label("dn_u1")
    a.emit(cmp_imm, 3, 0); a.emit(b_cond, "dn_v", "ge"); a.emit(movs_imm, 3, 0)
    a.label("dn_v")
    a.emit(movs_imm, 5, 0x7F); a.emit(ands_reg, 3, 5); a.emit(movs_imm, 5, 0x80); a.emit(ands_reg, 5, 4); a.emit(orrs_reg, 3, 5)
    a.emit(mov_reg, 0, 3); a.emit(pop_list, [4, 5], pc=True)
    a.label("dn_fsel")                                                               # filter mode: one step per turn, wraps 0..4
    a.emit(movs_imm, 3, 7); a.emit(ands_reg, 3, 1)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "dn_f", "eq"); a.emit(b_cond, "dn_up", "gt")
    a.emit(subs_imm8, 3, 1); a.emit(b_cond, "dn_f", "ge"); a.emit(movs_imm, 3, 4); a.emit(b, "dn_f")
    a.label("dn_up")
    a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 4); a.emit(b_cond, "dn_f", "le"); a.emit(movs_imm, 3, 0)
    a.label("dn_f")
    a.emit(movs_imm, 5, 0xF8); a.emit(ands_reg, 5, 4); a.emit(orrs_reg, 3, 5)
    a.emit(mov_reg, 0, 3); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_mark(r0 = macro handler, r1 = code 1..10): set the dirty bit
    a.label("c_mark")
    a.emit(cmp_imm, 1, 7); a.emit(b_cond, "mk_hi", "gt")
    a.emit(movs_imm, 2, 1); a.emit(subs_imm8, 1, 1); a.emit(lsls_reg, 2, 1)
    a.emit(raw, ldrb_w(3, 0, O_FLAGS)); a.emit(orrs_reg, 3, 2); a.emit(raw, strb_w(3, 0, O_FLAGS)); a.emit(raw, h(0x4770))
    a.label("mk_hi")
    a.emit(movs_imm, 2, 1); a.emit(subs_imm8, 1, 8); a.emit(lsls_reg, 2, 1)
    a.emit(raw, ldrb_w(3, 0, O_DELTA)); a.emit(orrs_reg, 3, 2); a.emit(raw, strb_w(3, 0, O_DELTA)); a.emit(raw, h(0x4770))

    # ---- c_dext_turn(r0 = obj, r1 = knob, r2 = delta, r3 = drum) -> r0 = 1 handled / 0 stock (K4 / K6 extended values)
    a.label("c_dext_turn")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); a.emit(mov_reg, 7, 3)
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "dx_done", "eq")
    a.emit(ldr_imm, 0, 4, 0xC); a.emit(lsrs_imm, 1, 5, 1); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 4, 0, 0)         # r4 = stock value
    a.emit(subs_imm8, 5, 3); a.emit(lsls_imm, 5, 5, 1)                                                           # r5 = nibble shift 0 / 4
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_dnib_get")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "dx_right", "gt")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dx_l", "ne"); a.emit(cmp_imm, 4, 0); a.emit(b_cond, "dx_stock", "ne")    # left: counts when ext > 0 or the stock value is 0
    a.label("dx_l")
    a.emit(subs_reg, 0, 0, 6); a.emit(cmp_imm, 0, 15); a.emit(b_cond, "dx_set", "le"); a.emit(movs_imm, 0, 15); a.emit(b, "dx_set")
    a.label("dx_right")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dx_stock", "eq")
    a.emit(subs_reg, 0, 0, 6); a.emit(b_cond, "dx_set", "ge"); a.emit(movs_imm, 0, 0)
    a.label("dx_set")
    a.emit(mov_reg, 2, 0); a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_dnib_set")
    a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(movs_imm, 1, 10); a.emit(bl, "c_mark")
    a.label("dx_done")
    a.emit(movs_imm, 0, 1); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dx_stock")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if CLEAR:
        # ---- c_clr_held(r0 = macro handler) -> r0 = 1 while the Clear button is held (the stock test: the store at [obj + 0x1C], parameter 0, bit 0)
        a.label("c_clr_held")
        a.emit(push_list, [], lr=True)
        a.emit(ldr_imm, 0, 0, 0x1C); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
        a.emit(pop_list, [], pc=True)
        # ---- c_clr_set(r0 = macro handler, r1 = knob position, r2 = 1 blue / 0 red): the Clear LED of that knob (one at a time), kept while Clear is held
        a.label("c_clr_set")
        a.emit(push_list, [4], lr=True)
        a.emit(raw, ldrb_w(3, 0, O_CLR)); a.emit(movs_imm, 4, 7); a.emit(ands_reg, 3, 4); a.emit(movs_imm, 4, 8); a.emit(orrs_reg, 3, 4)
        a.emit(lsls_imm, 2, 2, 4); a.emit(orrs_reg, 3, 2); a.emit(lsls_imm, 1, 1, 5); a.emit(orrs_reg, 3, 1)
        a.emit(raw, strb_w(3, 0, O_CLR))
        a.emit(pop_list, [4], pc=True)

    if CLEAR and CLEAR_BOTH:
        # ---- c_dzero(r0 = drum, r1 = code): the saved value of our code back to 0 (the extension bit / the upper mode bits kept), marked dirty
        a.label("c_dzero")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 5, 0); a.emit(mov_reg, 6, 1)
        a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "dz_x", "eq")
        a.emit(movs_imm, 1, 0x80); a.emit(cmp_imm, 6, 9); a.emit(b_cond, "dz_m", "ne"); a.emit(movs_imm, 1, 0xF8)
        a.label("dz_m")
        a.emit(ands_reg, 0, 1); a.emit(mov_reg, 2, 0); a.emit(mov_reg, 0, 5); a.emit(mov_reg, 1, 6); a.emit(bl, "c_dput")
        a.emit(mov_reg, 0, 5); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 1, 6); a.emit(bl, "c_mark")
        a.label("dz_x")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_dk19(obj, knob, delta): slot 4 of the drum macro handlers
    a.label("c_dk19")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(movs_imm, 7, 0)
    a.label("dk_f")
    a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(cmp_reg, 0, 4); a.emit(b_cond, "dk_have", "eq")
    a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 4); a.emit(b_cond, "dk_f", "lo"); a.emit(b, "dk_old")
    a.label("dk_have")
    a.emit(bl, L["c_shift"]); a.emit(cmp_imm, 0, 0); bc("dk_ns", "eq")
    if REMAP:                                                                       # chromatic drum view: Shift + pitch = the semitone bias of SC11 (stock handler), as before
        a.emit(cmp_imm, 5, 0); a.emit(b_cond, "dk_nc", "ne")
        a.emit(mov_reg, 0, 7); a.emit(bl, L["c_dview"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dk_nc", "eq")
        a.emit(raw, ldrb_w(1, 0, 0x51)); a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "dk_nc", "eq")
        a.emit(movs_imm, 5, 1); a.emit(b, "dk_old")
        a.label("dk_nc")
    for knob, code in sorted((REMAP_SHIFT if REMAP else MAP2["shift"]).items()):
        a.emit(movs_imm, 1, code); a.emit(cmp_imm, 5, knob); bc("dk_code", "eq")
    if REMAP:
        if EXTRAS:
            for knob, which in sorted(xt_map().items()):
                a.emit(cmp_imm, 5, knob); a.emit(b_cond, f"dk_sx{knob}", "ne"); a.emit(movs_imm, 1, which); a.emit(b, "dk_xt"); a.label(f"dk_sx{knob}")
        for knob, s in sorted(REMAP_SHIFT_STOCK.items()):
            if EXTRAS and knob in xt_map(): continue
            if SPLIT3 and knob == 2:                                                # Shift + K3: start / cut
                a.emit(cmp_imm, 5, 2); a.emit(b_cond, "dk_sk2", "ne"); a.emit(b, "dk_k3s"); a.label("dk_sk2"); continue
            a.emit(cmp_imm, 5, knob); a.emit(b_cond, f"dk_sk{knob}", "ne"); a.emit(movs_imm, 5, s); a.emit(b, "dk_old"); a.label(f"dk_sk{knob}")
        a.emit(b, "dk_done")                                                        # Shift + K6 without EXTRAS: nothing
    else:
        a.emit(b, "dk_old")
    a.label("dk_ns")
    if CLEAR and CLEAR_BOTH:
        # Clear held + a plain knob: the Shift layer of the same knob goes to its default too (codes of REMAP_SHIFT; K8: the distortion type).  r4 = handler, r5 = knob, r7 = drum.
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); bc("dk_nbc", "eq")
        for knob, code in sorted(REMAP_SHIFT.items()):
            a.emit(cmp_imm, 5, knob); a.emit(b_cond, f"dk_bc{knob}", "ne"); a.emit(mov_reg, 0, 7); a.emit(movs_imm, 1, code); a.emit(bl, "c_dzero"); a.emit(b, "dk_nbc"); a.label(f"dk_bc{knob}")
        if EXTRAS:
            for knob, which in sorted(xt_map().items()):
                if which != 0: continue
                a.emit(cmp_imm, 5, knob); a.emit(b_cond, f"dk_bx{knob}", "ne")
                a.emit(mov_reg, 0, 7); a.emit(movs_imm, 1, 0); a.emit(bl, "c_xt_set"); a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(movs_imm, 1, 10); a.emit(bl, "c_mark")
                a.label(f"dk_bx{knob}")
        a.label("dk_nbc")
    for knob, code in sorted((REMAP_PLAIN if REMAP else MAP2["plain"]).items()):
        a.emit(movs_imm, 1, code); a.emit(cmp_imm, 5, knob); bc("dk_code", "eq")
    if REMAP:
        for knob, s in sorted(REMAP_PLAIN_STOCK.items()):
            a.emit(cmp_imm, 5, knob); a.emit(b_cond, f"dk_pk{knob}", "ne"); a.emit(movs_imm, 5, s); a.emit(b, "dk_chk"); a.label(f"dk_pk{knob}")
        a.emit(b, "dk_done")
        a.label("dk_chk")
    a.emit(cmp_imm, 5, 3); a.emit(b_cond, "dk_x", "eq"); a.emit(cmp_imm, 5, 5); a.emit(b_cond, "dk_old", "ne")
    a.label("dk_x")
    if SPLIT3:                                                                      # K3: decay (stock) / attack
        a.emit(cmp_imm, 5, 3); bc("dk_xo", "ne")
        if CLEAR:
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); bc("dk_k3n", "eq")
            a.emit(cmp_imm, 6, 0); bc("dk_old", "le")                               # Clear + left: the stock's (automation)
            a.emit(mov_reg, 0, 7); a.emit(bl, "c_k3zero"); a.emit(b, "dk_old")      # Clear + right: ours to 0, the stock's decay default
            a.label("dk_k3n")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 6); a.emit(mov_reg, 2, 7); a.emit(bl, "c_k3turn")
        a.emit(cmp_imm, 0, 0); bc("dk_old", "eq"); a.emit(b, "dk_done")
        a.label("dk_k3s")
        a.emit(mov_reg, 0, 6); a.emit(mov_reg, 1, 7); a.emit(bl, "c_k3sturn"); a.emit(b, "dk_done")
        a.label("dk_xo")
    if CLEAR:
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); bc("dk_old", "ne")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(mov_reg, 3, 7)
    a.emit(bl, "c_dext_turn"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dk_old", "eq"); a.emit(b, "dk_done")
    if REMAP and EXTRAS:
        a.label("dk_xt")                                                            # r1 = which (0 distortion type, 1 filter slope)
        if CLEAR:
            a.emit(cmp_imm, 1, 0); bc("dk_xtn", "ne")
            a.emit(mov_reg, 0, 4); a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); bc("dk_xtc", "ne")
            a.emit(movs_imm, 1, 0)
            a.label("dk_xtn")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 2, 6); a.emit(mov_reg, 3, 7); a.emit(bl, "c_xt_turn"); a.emit(b, "dk_done")
        if CLEAR:
            a.label("dk_xtc")                                                       # Clear + distortion type: right = type 0, left = red LED only
            a.emit(cmp_imm, 6, 0); bc("dk_cl", "le")
            a.emit(mov_reg, 0, 7); a.emit(movs_imm, 1, 0); a.emit(bl, "c_xt_set")
            a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 10); a.emit(bl, "c_mark")
            a.emit(b, "dk_cr")
    a.label("dk_old")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_dknob3"])
    a.label("dk_code")                                                              # r1 = code
    a.emit(mov_reg, 4, 1)
    if CLEAR:
        a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); bc("dk_nclr", "eq")
        a.emit(cmp_imm, 6, 0); bc("dk_cl", "le")
        a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); bc("dk_done", "eq")
        a.emit(movs_imm, 1, 0x80); a.emit(cmp_imm, 4, 9); bc("dk_cm", "ne"); a.emit(movs_imm, 1, 0xF8)
        a.label("dk_cm")
        a.emit(ands_reg, 0, 1); a.emit(mov_reg, 2, 0); a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(bl, "c_dput")        # default value (the ext bit / the upper mode bits kept)
        a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 1, 4); a.emit(bl, "c_mark")
        a.label("dk_cr")                                                             # blue LED: look the handler up again
        a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 2, 1); a.emit(b, "dk_cf")
        a.label("dk_cl")                                                             # left: red LED, nothing to delete
        a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 2, 0)
        a.label("dk_cf")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, "c_clr_set"); a.emit(b, "dk_done")
        a.label("dk_nclr")
        a.emit(mov_reg, 1, 4)                                                        # r1 = the code again (the Clear test clobbered it)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "dk_done", "eq")
    a.emit(mov_reg, 5, 0)
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6); a.emit(bl, "c_dnew")
    a.emit(cmp_reg, 0, 5); a.emit(b_cond, "dk_done", "eq")
    a.emit(mov_reg, 2, 0); a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(bl, "c_dput")
    a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 1, 4); a.emit(bl, "c_mark")
    a.label("dk_done")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---------------------------------------------------------------- XMEM <-> RAM
    # ---- c_xm_zero: the 65 bytes to 0
    a.label("c_xm_zero")
    a.emit(push_list, [4], lr=True)
    a.emit(movs_imm, 4, 0)
    a.label("xz_l")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xz_n", "eq")
    a.emit(movs_imm, 1, 0); a.emit(strb_imm, 1, 0, 0)
    a.label("xz_n")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, N_XM); a.emit(b_cond, "xz_l", "lo")
    a.emit(pop_list, [4], pc=True)

    if BLOB_KEEP:
        # ---- c_bcopy (store, source) = vtable slot 3 of the stores (the stock whole-blob copy 0x0803BBE2) that keeps our bytes of a synth store
        #      r4 = store, r5 = source, r6 = flat index of the first byte of that store, r7 = counter; 28 bytes of stack hold the 22 saved bytes
        a.label("c_bcopy")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
        a.emit(movw, 2, CTXP & 0xFFFF); a.emit(movt, 2, CTXP >> 16); a.emit(ldr_imm, 2, 2, 0)
        a.emit(cmp_imm, 2, 0); a.emit(b_cond, "bc_pass", "eq")
        a.emit(raw, ldr_w(3, 2, CTX_SYNTH1)); a.emit(movs_imm, 6, S1_FIRST); a.emit(cmp_reg, 3, 4); a.emit(b_cond, "bc_have", "eq")
        a.emit(raw, ldr_w(3, 2, CTX_SYNTH2)); a.emit(movs_imm, 6, S2_FIRST); a.emit(cmp_reg, 3, 4); a.emit(b_cond, "bc_pass", "ne")
        a.label("bc_have")
        a.emit(raw, sub_sp_imm(28))
        a.emit(movs_imm, 7, 0)
        a.label("bc_sv")
        a.emit(adds_reg, 0, 6, 7); a.emit(bl, "c_xp"); a.emit(movs_imm, 3, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "bc_s1", "eq"); a.emit(ldrb_imm, 3, 0, 0)
        a.label("bc_s1")
        a.emit(mov_reg, 1, 13); a.emit(strb_reg, 3, 1, 7)
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, N_SYNTH_B); a.emit(b_cond, "bc_sv", "lo")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(bl, STORE_COPY)              # the stock copy
        a.emit(movs_imm, 7, 0)
        a.label("bc_rs")
        a.emit(adds_reg, 0, 6, 7); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "bc_r1", "eq")
        a.emit(mov_reg, 1, 13); a.emit(ldrb_reg, 3, 1, 7); a.emit(strb_imm, 3, 0, 0)
        a.label("bc_r1")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, N_SYNTH_B); a.emit(b_cond, "bc_rs", "lo")
        a.emit(raw, add_sp_imm(28))
        a.emit(pop_list, [4, 5, 6, 7], pc=True)
        a.label("bc_pass")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5)
        a.emit(raw, popw([4, 5, 6, 7], lr=True))
        a.emit(b_w, STORE_COPY)

    if REC_RESTORE:
        # ---- c_xm_from_rec: the 65 bytes <- the session record ([SESSION_OBJ + 0x14] + REC_BASE[store] + offset).  The stock load restores the project and drum
        #      blobs whole, but a synth blob only when the patch of the record differs from the one that is loaded (apply 0x0802EEFE, 0x0802F438 / 0x0802F4A2:
        #      same patch -> only 6 parameters): the reserved bytes of the synths (the signature, the slots, most drum values) stayed as they were
        a.label("c_xm_from_rec")
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(movw, 0, SESSION_OBJ & 0xFFFF); a.emit(movt, 0, SESSION_OBJ >> 16); a.emit(ldr_imm, 6, 0, 0x14)
        a.emit(cmp_imm, 6, 0); a.emit(b_cond, "fr_x", "eq")
        a.emit(movs_imm, 4, 0)
        a.label("fr_l")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fr_n", "eq"); a.emit(mov_reg, 5, 0)       # r5 = live byte
        a.emit(lsls_imm, 1, 4, 2); a.emit(movw, 2, (tab + 4 * N_XM) & 0xFFFF); a.emit(movt, 2, (tab + 4 * N_XM) >> 16)
        a.emit(raw, h(0x5851))                                                       # ldr r1, [r2, r1] : record offset
        a.emit(ldrb_reg, 1, 6, 1); a.emit(strb_imm, 1, 5, 0)
        a.label("fr_n")
        a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, N_XM); a.emit(b_cond, "fr_l", "lo")
        a.label("fr_x")
        a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_xm_validate: no signature -> the whole zone is cleared (a project saved by stock, or by the diagnostic builds)
    a.label("c_xm_validate")
    a.emit(push_list, [], lr=True)
    a.emit(movs_imm, 0, XM_SIG); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xv_x", "eq")
    a.emit(ldrb_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 3); a.emit(cmp_imm, 0, SIG); a.emit(b_cond, "xv_x", "eq")
    a.emit(bl, "c_xm_zero")
    a.label("xv_x"); a.emit(pop_list, [], pc=True)

    # ---- c_xm_load(r0 = Master FX block): XMEM -> slots (validated) and synth modes (validated, Audio In group resent)
    a.label("c_xm_load")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0)
    if GFX_SESSION:                                                                  # nothing of ours in this project: keep the RAM ones
        a.emit(movs_imm, 0, XM_SIG); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xl_modes", "eq")
        a.emit(ldrb_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 3); a.emit(cmp_imm, 0, SIG); a.emit(b_cond, "xl_modes", "ne")
    if GFX_GLOBAL:                                                                   # slots already loaded since power-up: keep the RAM ones
        a.emit(ldrb_w, 0, 4, FLAGS); a.emit(movs_imm, 1, F_GBOOT); a.emit(tst_reg, 0, 1); a.emit(b_cond, "xl_modes", "ne")
    a.label("xl_s")
    a.emit(mov_reg, 0, 5); a.emit(bl, "c_xp"); a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xl_z", "eq"); a.emit(ldrb_imm, 1, 0, 0)
    a.label("xl_z")
    a.emit(mov_reg, 3, 4); a.emit(adds_imm8, 3, S_SLOT); a.emit(adds_reg, 3, 3, 5); a.emit(strb_imm, 1, 3, 0)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 28); a.emit(b_cond, "xl_s", "lo")
    a.emit(movs_imm, 5, 0)                                                           # slot validation: assigned with an effect > 5 -> unassigned
    a.label("xl_v")
    a.emit(lsls_imm, 6, 5, 2); a.emit(adds_reg, 6, 6, 4); a.emit(adds_imm8, 6, S_SLOT)      # r6 = slot j
    a.emit(ldrb_imm, 0, 6, 3); a.emit(lsrs_imm, 1, 0, 7); a.emit(b_cond, "xl_vn", "eq")
    a.emit(ldrb_imm, 1, 6, 0); a.emit(lsrs_imm, 1, 1, 7)
    a.emit(ldrb_imm, 2, 6, 1); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 1); a.emit(orrs_reg, 1, 2)
    a.emit(ldrb_imm, 2, 6, 2); a.emit(lsrs_imm, 2, 2, 7); a.emit(lsls_imm, 2, 2, 2); a.emit(orrs_reg, 1, 2)
    a.emit(cmp_imm, 1, 5); a.emit(b_cond, "xl_vn", "ls")
    a.emit(movs_imm, 1, 0x7F); a.emit(ands_reg, 0, 1); a.emit(strb_imm, 0, 6, 3)
    a.label("xl_vn")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 7); a.emit(b_cond, "xl_v", "lo")
    if GFX_GLOBAL or GFX_SESSION: a.label("xl_modes")
    a.emit(movs_imm, 0, XM_MODES); a.emit(bl, "c_xp"); a.emit(movs_imm, 5, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xl_m", "eq"); a.emit(ldrb_imm, 5, 0, 0)
    a.label("xl_m")
    a.emit(mov_reg, 6, 4); a.emit(subs_imm8, 6, GFX_OFF)                             # r6 = SC14 state
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 5); a.emit(cmp_imm, 1, N_MODES - 1); a.emit(b_cond, "xl_m1", "ls"); a.emit(movs_imm, 1, 0)
    a.label("xl_m1")
    a.emit(strb_imm, 1, 6, SC14_MODE)
    a.emit(lsrs_imm, 1, 5, 3); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 1, 2); a.emit(cmp_imm, 1, N_MODES - 1); a.emit(b_cond, "xl_m2", "ls"); a.emit(movs_imm, 1, 0)
    a.label("xl_m2")
    a.emit(strb_imm, 1, 6, SC14_MODE + 1)
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 48); a.emit(bl, MARK_DIRTY_SVC if FIX_LOCK else MARK_DIRTY)       # resend the Audio In group
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_xm_save(r0 = Master FX block): slots, modes and the signature -> XMEM (right before the stock save)
    a.label("c_xm_save")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0)
    a.label("xs_s")
    a.emit(mov_reg, 0, 5); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xs_n", "eq")
    a.emit(mov_reg, 3, 4); a.emit(adds_imm8, 3, S_SLOT); a.emit(adds_reg, 3, 3, 5); a.emit(ldrb_imm, 1, 3, 0); a.emit(strb_imm, 1, 0, 0)
    a.label("xs_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 28); a.emit(b_cond, "xs_s", "lo")
    a.emit(movs_imm, 0, XM_MODES); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xs_g", "eq")
    a.emit(mov_reg, 6, 4); a.emit(subs_imm8, 6, GFX_OFF)
    a.emit(ldrb_imm, 1, 6, SC14_MODE + 1); a.emit(lsls_imm, 1, 1, 3); a.emit(ldrb_imm, 2, 6, SC14_MODE); a.emit(orrs_reg, 1, 2)
    a.emit(strb_imm, 1, 0, 0)
    a.label("xs_g")
    a.emit(movs_imm, 0, XM_SIG); a.emit(bl, "c_xp"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xs_x", "eq")
    a.emit(ldrb_imm, 1, 0, 0); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 1, 2); a.emit(movs_imm, 2, (SIG << 3) & 0xFF); a.emit(orrs_reg, 1, 2)
    a.emit(strb_imm, 1, 0, 0)
    a.label("xs_x")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_rs: the deferred work after a project load / new project / power-up (runs in the DSP service tick)
    a.label("c_rs")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); bc("rs_x", "eq")
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_w, 5, 4, FLAGS)
    if GUARD:
        def wait_ms(ms):                                                             # return (rs_x) while the uptime is below ms; clobbers r0 / r1
            a.emit(movw, 0, TICK & 0xFFFF); a.emit(movt, 0, TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
            a.emit(movw, 1, ms); a.emit(cmp_reg, 0, 1); bc("rs_x", "lo")
        a.emit(movs_imm, 1, F_MSG); a.emit(tst_reg, 5, 1); bc("rs_a", "eq")          # stage B pending: the drum messages
        wait_ms(BOOT_B)
        a.emit(bl, "c_rs_dirty")
        a.emit(ldrb_w, 0, 4, FLAGS); a.emit(movs_imm, 1, F_MSG); a.emit(bics_reg, 0, 1); a.emit(raw, strb_w(0, 4, FLAGS))
        a.emit(b, "rs_x")
        a.label("rs_a")
    a.emit(movs_imm, 1, F_RESYNC); a.emit(tst_reg, 5, 1); bc("rs_x", "eq")
    if GUARD: wait_ms(BOOT_A)
    a.emit(movs_imm, 6, 0)
    a.label("rs_h")                                                                  # the four drum handlers must exist
    a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"]); a.emit(cmp_imm, 0, 0); bc("rs_x", "eq")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 4); a.emit(b_cond, "rs_h", "lo")
    if REC_RESTORE:
        a.emit(movs_imm, 1, F_NEW); a.emit(tst_reg, 5, 1); a.emit(b_cond, "rs_r", "eq"); a.emit(bl, "c_xm_zero"); a.emit(b, "rs_v")
        a.label("rs_r"); a.emit(bl, "c_xm_from_rec")                                 # a load: the record has the project's own bytes
    else:
        a.emit(movs_imm, 1, F_NEW); a.emit(tst_reg, 5, 1); a.emit(b_cond, "rs_v", "eq"); a.emit(bl, "c_xm_zero")
    a.label("rs_v")
    a.emit(bl, "c_xm_validate")
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_xm_load")
    if SPLIT3:
        a.emit(mov_reg, 0, 5); a.emit(bl, "c_k3load")
    if not GUARD:
        a.emit(movs_imm, 6, 0)
        a.label("rs_d")                                                              # every drum parameter dirty
        a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"])
        a.emit(raw, ldrb_w(1, 0, O_FLAGS)); a.emit(movs_imm, 2, 0x7F); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, O_FLAGS))
        a.emit(raw, ldrb_w(1, 0, O_DELTA)); a.emit(movs_imm, 2, 7); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, O_DELTA))
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 4); a.emit(b_cond, "rs_d", "lo")
    a.emit(movs_imm, 0, 0); a.emit(raw, strb_w(0, 4, S_HELD)); a.emit(raw, strb_w(0, 4, S_SLOTH))                   # held pads off first (c_clrall re-picks)
    a.emit(mov_reg, 1, 4); a.emit(subs_imm8, 1, GFX_OFF); a.emit(strb_imm, 0, 1, SC14_HELD)
    a.emit(mov_reg, 0, 4); a.emit(bl, L["c_clrall"])                                 # Master FX effects and song pointer off
    a.emit(movs_imm, 0, (F_MSG if GUARD else 0) | (F_GBOOT if GFX_GLOBAL else 0)); a.emit(raw, strb_w(0, 4, FLAGS))
    a.label("rs_x")
    a.emit(pop_list, [4, 5, 6], pc=True)
    if GUARD:
        a.label("c_rs_dirty")                                                        # every drum parameter dirty (stage B)
        a.emit(push_list, [6], lr=True)
        a.emit(movs_imm, 6, 0)
        a.label("rd_l")
        a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "rd_n", "eq")
        a.emit(raw, ldrb_w(1, 0, O_FLAGS)); a.emit(movs_imm, 2, 0x7F); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, O_FLAGS))
        a.emit(raw, ldrb_w(1, 0, O_DELTA)); a.emit(movs_imm, 2, 7); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, O_DELTA))
        a.label("rd_n")
        a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 4); a.emit(b_cond, "rd_l", "lo")
        a.emit(pop_list, [6], pc=True)

    # ---- c_dtick19: DSP service hook (first in the chain, DSP lock held): deferred work, then one absolute message per drum
    a.label("c_dtick19")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, "c_rs")
    a.emit(movs_imm, 7, 0)
    a.label("dt_l")
    a.emit(mov_reg, 0, 7); a.emit(bl, L["c_mh"]); a.emit(cmp_imm, 0, 0); bc("dt_n", "eq")
    a.emit(mov_reg, 4, 0)
    a.emit(raw, ldrb_w(5, 4, O_FLAGS)); a.emit(raw, ldrb_w(6, 4, O_DELTA))
    a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 0, 5); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 6); a.emit(lsls_imm, 1, 1, 7); a.emit(orrs_reg, 0, 1)
    a.emit(cmp_imm, 0, 0); bc("dt_n", "eq")
    a.emit(movs_imm, 1, 0)
    a.label("dt_f")
    a.emit(movs_imm, 2, 1); a.emit(tst_reg, 0, 2); a.emit(b_cond, "dt_g", "ne"); a.emit(lsrs_imm, 0, 0, 1); a.emit(adds_imm8, 1, 1); a.emit(b, "dt_f")
    a.label("dt_g")                                                                  # r1 = lowest dirty bit k (0..9)
    a.emit(movs_imm, 2, 1); a.emit(lsls_reg, 2, 1)
    a.emit(movs_imm, 3, 0x7F); a.emit(ands_reg, 3, 2); a.emit(bics_reg, 5, 3)
    a.emit(lsrs_imm, 2, 2, 7); a.emit(bics_reg, 6, 2)
    a.emit(cmp_imm, 1, 9); bc("dt_ext", "eq")
    a.emit(movs_imm, 0, 0x80); a.emit(eors_reg, 5, 0)                                # toggle the mailbox tag
    a.emit(raw, strb_w(5, 4, O_FLAGS)); a.emit(raw, strb_w(6, 4, O_DELTA))
    a.emit(adds_imm8, 1, 1); a.emit(mov_reg, 4, 1)                                   # r4 = code
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(bl, "c_dget"); a.emit(adds_imm3, 1, 0, 1); bc("dt_n", "eq")
    if FSEL_STOCK0:                                                                  # stored 0 <-> mode 4 (the stock EQ), 4 <-> 0 (DJ)
        a.emit(cmp_imm, 4, 9); a.emit(b_cond, "dt_v", "ne"); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 0, 1)
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dt_f0", "ne"); a.emit(movs_imm, 0, 4); a.emit(b, "dt_m")
        a.label("dt_f0"); a.emit(cmp_imm, 0, 4); a.emit(b_cond, "dt_m", "ne"); a.emit(movs_imm, 0, 0); a.emit(b, "dt_m")
    else:
        a.emit(cmp_imm, 4, 9); a.emit(b_cond, "dt_v", "ne"); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 0, 1); a.emit(b, "dt_m")
    a.label("dt_v")
    a.emit(lsls_imm, 0, 0, 25)
    for c in UNIPOLAR:
        a.emit(cmp_imm, 4, c); a.emit(b_cond, "dt_u", "eq")
    a.emit(raw, asrs_imm(0, 0, 25)); a.emit(b, "dt_m")
    a.label("dt_u")
    a.emit(lsrs_imm, 0, 0, 25)
    a.label("dt_m")
    a.emit(raw, uxth(0, 0))
    a.emit(lsrs_imm, 1, 5, 7); a.emit(lsls_imm, 1, 1, 23); a.emit(lsls_imm, 2, 4, 16); a.emit(orrs_reg, 1, 2); a.emit(orrs_reg, 1, 0)
    a.emit(lsls_imm, 1, 1, 8)
    a.emit(lsls_imm, 2, 7, SH); a.emit(movw, 0, DB & 0xFFFF); a.emit(adds_reg, 2, 2, 0)
    a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE); a.emit(b, "dt_n")
    a.label("dt_ext")
    a.emit(raw, strb_w(5, 4, O_FLAGS)); a.emit(raw, strb_w(6, 4, O_DELTA))
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_dext_get")
    if EXTRAS:
        a.emit(mov_reg, 5, 0); a.emit(mov_reg, 0, 7); a.emit(bl, "c_xt_get"); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 5)
    a.emit(lsls_imm, 1, 0, 8)
    a.emit(lsls_imm, 2, 7, SH); a.emit(movw, 0, (DB + EXT) & 0xFFFF); a.emit(adds_reg, 2, 2, 0)
    a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    if SPLIT3:
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_k3w")
    a.label("dt_n")
    a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 4); bc("dt_l", "lo")
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["svc_next"])

    # ---------------------------------------------------------------- hooks
    # ---- c_pl_load: end of the stock apply (the function's own pop.w follows): RESYNC
    a.label("c_pl_load")
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pl_x", "eq")
    a.emit(raw, ldrb_w(1, 0, FLAGS)); a.emit(movs_imm, 2, F_RESYNC); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, FLAGS))
    a.label("pl_x")
    a.emit(raw, L["load_end_instr"])
    # ---- c_pl_new: tail of the stock "new project" defaults (r0 = ctx, r1 = 0x10000, r2 = 1 for 0x08029A00): NEW
    a.label("c_pl_new")
    a.emit(push_list, [0, 1, 2, 3, 4], lr=True)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pn_x", "eq")
    a.emit(raw, ldrb_w(1, 0, FLAGS)); a.emit(movs_imm, 2, F_NEW); a.emit(orrs_reg, 1, 2); a.emit(raw, strb_w(1, 0, FLAGS))
    a.label("pn_x")
    a.emit(raw, popw([0, 1, 2, 3, 4], lr=True)); a.emit(b_w, NEW_TARGET)
    # ---- c_pl_save: replaces the bl to the stock save (r0 = session manager): XMEM <- RAM unless a load is still pending
    a.label("c_pl_save")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ps_x", "eq")
    if SAVE_MASK:
        a.emit(raw, ldrb_w(1, 0, FLAGS)); a.emit(movs_imm, 2, F_RESYNC | F_NEW); a.emit(tst_reg, 1, 2); a.emit(b_cond, "ps_x", "ne")
    else:
        a.emit(raw, ldrb_w(1, 0, FLAGS)); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "ps_x", "ne")
    a.emit(bl, "c_xm_save")
    a.label("ps_x")
    a.emit(mov_reg, 0, 4); a.emit(bl, SAVE_FN)
    a.emit(pop_list, [4], pc=True)
    if EXTRAS:
        extras_code(a, tab)
    if KNOB_LEVELS:
        knob_levels_code(a, L)
    if SPLIT3:
        k3_code(a, DB, SH, L)
    return a.assemble()


def k3_code(a, DB, SH, L):
    """SC41.7 (use_k3split): the block of attack / start / cut in the record's tail, K3 / Shift + K3, the load, the DSP words."""
    import drums2_dsp as DD
    from build_sc14 import udiv
    from thumb import str_imm
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def off3(rd, rdrum, rwhich):                       # rd = 5 + 3 drum + which (rd != rdrum, rwhich)
        E(lsls_imm, rd, rdrum, 1); E(adds_reg, rd, rd, rdrum); E(adds_reg, rd, rd, rwhich); E(adds_imm8, rd, 5)
    C = round(DD.NFR * 2 ** 23 * 127 ** 2 / (DD.FS * K3_ATK_MAX))

    # ---- c_k3blk() -> r0 = the block in the record's tail, or 0
    a.label("c_k3blk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "kb_x", "eq")
    imm32(1, K3_TAIL + K3_OFF); E(adds_reg, 0, 0, 1)
    a.label("kb_x"); E(raw, h(0x4770))

    # ---- c_k3sum(r0 = block) -> r0 = (sum of the 12 bytes) ^ 0x5A, 8 bits; clobbers r1-r3
    a.label("c_k3sum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 5)
    a.label("ks_l"); E(ldrb_reg, 3, 0, 2); E(adds_reg, 1, 1, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 17); E(b_cond, "ks_l", "lo")
    E(movs_imm, 0, 0x5A); E(eors_reg, 0, 1); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(raw, h(0x4770))

    # ---- c_k3ok(r0 = block) -> r0 = 1 when it carries the signature and its sum; clobbers r1-r3
    a.label("c_k3ok")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(ldr_imm, 1, 4, 0); imm32(2, K3_SIG); E(cmp_reg, 1, 2); E(b_cond, "ko_n", "ne")
    E(mov_reg, 0, 4); E(bl, "c_k3sum"); E(ldrb_imm, 1, 4, 4); E(cmp_reg, 0, 1); E(b_cond, "ko_n", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ko_n"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_k3init(r0 = block, r1 = 1: the old start point taken over): signature, zeros, sum; clobbers r0-r3
    a.label("c_k3init")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(0, K3_SIG); E(str_imm, 0, 4, 0)
    E(movs_imm, 6, 0)
    a.label("ki_l")
    E(movs_imm, 7, 0)
    E(cmp_imm, 5, 0); E(b_cond, "ki_z", "eq")
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, "c_dnib_get"); E(lsls_imm, 7, 0, 1)            # S = 2 x the nibble (s / 64 = 2 s / 128)
    a.label("ki_z")
    E(lsls_imm, 1, 6, 1); E(adds_reg, 1, 1, 6); E(adds_imm8, 1, 5); E(movs_imm, 0, 0)
    E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(strb_reg, 7, 4, 1); E(adds_imm8, 1, 1); E(strb_reg, 0, 4, 1)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "ki_l", "lo")
    E(mov_reg, 0, 4); E(bl, "c_k3sum"); E(strb_imm, 0, 4, 4)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_k3get(r0 = drum, r1 = 0 attack / 1 start / 2 cut) -> r0 = the value (0 without a valid block); clobbers r1-r3
    a.label("c_k3get")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_k3blk"); E(cmp_imm, 0, 0); E(b_cond, "kg_z", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_k3ok"); E(cmp_imm, 0, 0); E(b_cond, "kg_z", "eq")
    off3(0, 4, 5); E(ldrb_reg, 0, 6, 0); E(pop_list, [4, 5, 6], pc=True)
    a.label("kg_z"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_k3put(r0 = drum, r1 = which, r2 = value): into the block (made valid first), its sum, the drum's extended values dirty; clobbers r0-r3
    a.label("c_k3put")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 7, 2)
    E(bl, "c_k3blk"); E(cmp_imm, 0, 0); E(b_cond, "kp_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_k3ok"); E(cmp_imm, 0, 0); E(b_cond, "kp_ok", "ne")
    E(mov_reg, 0, 6); E(movs_imm, 1, 1); E(bl, "c_k3init")
    a.label("kp_ok")
    off3(0, 4, 5); E(strb_reg, 7, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_k3sum"); E(strb_imm, 0, 6, 4)
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "kp_x", "eq"); E(movs_imm, 1, 10); E(bl, "c_mark")
    a.label("kp_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_k3zero(r0 = drum): attack, start and cut to 0
    a.label("c_k3zero")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(movs_imm, 5, 0)
    a.label("kz_l"); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(bl, "c_k3put"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 3); E(b_cond, "kz_l", "lo")
    E(pop_list, [4, 5], pc=True)

    # ---- c_k3load(r0 = the flags): after a load / a new project: a new project = zeros; a project without a valid block = zeros + its old start point
    a.label("c_k3load")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_k3blk"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "eq"); E(mov_reg, 5, 0)
    E(movs_imm, 1, F_NEW); E(tst_reg, 4, 1); E(b_cond, "kl_ld", "eq")
    E(mov_reg, 0, 5); E(movs_imm, 1, 0); E(bl, "c_k3init"); E(b, "kl_x")
    a.label("kl_ld"); E(mov_reg, 0, 5); E(bl, "c_k3ok"); E(cmp_imm, 0, 0); E(b_cond, "kl_x", "ne")
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, "c_k3init")
    a.label("kl_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_k3turn(r0 = handler, r1 = delta, r2 = drum) -> r0 = 1 handled (the attack) / 0 the stock decay
    a.label("c_k3turn")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(cmp_imm, 5, 0); E(b_cond, "kt_1", "eq")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(ldrb_imm, 7, 0, 0)             # r7 = the stock decay
    E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, "c_k3get")                                          # r0 = the attack
    E(cmp_imm, 5, 0); E(b_cond, "kt_l", "lt")
    E(cmp_imm, 7, 127); E(b_cond, "kt_0", "lo")                                                    # right: the decay up to its maximum first
    E(adds_reg, 0, 0, 5); E(cmp_imm, 0, 127); E(b_cond, "kt_p", "le"); E(movs_imm, 0, 127); E(b, "kt_p")
    a.label("kt_l")
    E(cmp_imm, 0, 0); E(b_cond, "kt_0", "eq")                                                      # left: the attack back to 0 first
    E(adds_reg, 0, 0, 5); E(cmp_imm, 0, 0); E(b_cond, "kt_p", "ge"); E(movs_imm, 0, 0)
    a.label("kt_p"); E(mov_reg, 2, 0); E(mov_reg, 0, 6); E(movs_imm, 1, 0); E(bl, "c_k3put")
    a.label("kt_1"); E(movs_imm, 0, 1); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("kt_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_k3sturn(r0 = delta, r1 = drum): Shift + K3: left = the start moves in (the cut back to 0 first), right = the cut (the start back to 0 first)
    a.label("c_k3sturn")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 4, 0); E(b_cond, "kq_x", "eq")
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, "c_k3get"); E(mov_reg, 6, 0)                       # r6 = start
    E(mov_reg, 0, 5); E(movs_imm, 1, 2); E(bl, "c_k3get"); E(mov_reg, 7, 0)                       # r7 = cut
    E(cmp_imm, 4, 0); E(b_cond, "kq_l", "lt")
    E(cmp_imm, 6, 0); E(b_cond, "kq_c", "eq")
    E(subs_reg, 6, 6, 4); E(b_cond, "kq_s", "ge"); E(movs_imm, 6, 0); E(b, "kq_s")
    a.label("kq_c"); E(adds_reg, 7, 7, 4); E(cmp_imm, 7, K3_LIM); E(b_cond, "kq_e", "le"); E(movs_imm, 7, K3_LIM); E(b, "kq_e")
    a.label("kq_l")
    E(cmp_imm, 7, 0); E(b_cond, "kq_st", "eq")
    E(adds_reg, 7, 7, 4); E(b_cond, "kq_e", "ge"); E(movs_imm, 7, 0); E(b, "kq_e")
    a.label("kq_st"); E(subs_reg, 6, 6, 4); E(cmp_imm, 6, K3_LIM); E(b_cond, "kq_s", "le"); E(movs_imm, 6, K3_LIM)
    a.label("kq_s"); E(mov_reg, 2, 6); E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, "c_k3put"); E(b, "kq_x")
    a.label("kq_e"); E(mov_reg, 2, 7); E(mov_reg, 0, 5); E(movs_imm, 1, 2); E(bl, "c_k3put")
    a.label("kq_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_k3w(r0 = drum): AINC, STARTF, ENDC into the drum's DSP block (from the DSP service tick: DSP writes only)
    a.label("c_k3w")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(lsls_imm, 5, 4, SH); E(movw, 0, DB & 0xFFFF); E(adds_reg, 5, 5, 0)                          # r5 = the block
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_k3get"); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "kw_a", "eq")
    E(mov_reg, 1, 0); E(muls, 1, 0); imm32(0, C); E(raw, udiv(1, 0, 1))                             # C / A^2
    imm32(0, 0x7FFFFF); E(cmp_reg, 1, 0); E(b_cond, "kw_a", "ls"); E(mov_reg, 1, 0)
    a.label("kw_a"); E(lsls_imm, 1, 1, 8); E(mov_reg, 2, 5); E(adds_imm8, 2, DD.AINC); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    for which, word in ((1, DD.STARTF), (2, DD.ENDC)):
        E(mov_reg, 0, 4); E(movs_imm, 1, which); E(bl, "c_k3get"); E(lsls_imm, 1, 0, 24); E(mov_reg, 2, 5); E(adds_imm8, 2, word); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    E(pop_list, [4, 5], pc=True)


def xt_map(): return REMAP_XT if EXTRAS_SLOPE else {k: v for k, v in REMAP_XT.items() if v == 0}


def extras_code(a, tab):
    XT = tab + 4 * N_XM * (2 if REC_RESTORE else 1)
    def entry():                                       # r4 = drum, r6 = bit j -> r7 = mask, r0 = address of the byte or 0; clobbers r0-r3
        a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 3); a.emit(muls, 0, 1); a.emit(adds_reg, 0, 0, 6); a.emit(lsls_imm, 0, 0, 1)
        a.emit(movw, 2, XT & 0xFFFF); a.emit(movt, 2, XT >> 16); a.emit(adds_reg, 2, 2, 0)
        a.emit(ldrb_imm, 7, 2, 1); a.emit(ldrb_imm, 0, 2, 0); a.emit(bl, "c_xp")
    # ---- c_xt_get(r0 = drum) -> r0 = type | slope << 2
    a.label("c_xt_get")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0); a.emit(movs_imm, 6, 0)
    a.label("xg_l")
    entry()
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xg_n", "eq"); a.emit(ldrb_imm, 1, 0, 0); a.emit(tst_reg, 1, 7); a.emit(b_cond, "xg_n", "eq")
    a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 6); a.emit(orrs_reg, 5, 1)
    a.label("xg_n")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 3); a.emit(b_cond, "xg_l", "lo")
    a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_xt_set(r0 = drum, r1 = type | slope << 2)
    a.label("c_xt_set")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(movs_imm, 6, 0)
    a.label("xw_l")
    entry()
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "xw_n", "eq")
    a.emit(mov_reg, 2, 5); a.emit(lsrs_reg, 2, 6); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)
    a.emit(ldrb_imm, 1, 0, 0); a.emit(bics_reg, 1, 7); a.emit(cmp_imm, 2, 0); a.emit(b_cond, "xw_w", "eq"); a.emit(orrs_reg, 1, 7)
    a.label("xw_w"); a.emit(strb_imm, 1, 0, 0)
    a.label("xw_n")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 3); a.emit(b_cond, "xw_l", "lo")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    # ---- c_xt_turn(r0 = macro handler, r1 = which (0 type, 1 slope), r2 = delta, r3 = drum): type steps +-1 (wraps 0..3), slope = 1 for a right turn, 0 for a left one
    a.label("c_xt_turn")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2); a.emit(mov_reg, 7, 3)
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_xt_get")
    a.emit(movs_imm, 1, 3); a.emit(ands_reg, 1, 0)                                   # r1 = type
    a.emit(cmp_imm, 5, 0); a.emit(b_cond, "xt_sl", "ne")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "xt_dn", "le"); a.emit(adds_imm8, 1, 1); a.emit(b, "xt_w")
    a.label("xt_dn"); a.emit(subs_imm8, 1, 1)
    a.label("xt_w")
    a.emit(movs_imm, 2, 3); a.emit(ands_reg, 1, 2); a.emit(movs_imm, 2, 4); a.emit(ands_reg, 2, 0); a.emit(orrs_reg, 1, 2); a.emit(b, "xt_c")
    a.label("xt_sl")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "xt_c", "le"); a.emit(movs_imm, 2, 4); a.emit(orrs_reg, 1, 2)
    a.label("xt_c")
    a.emit(cmp_reg, 1, 0); a.emit(b_cond, "xt_x", "eq")
    a.emit(mov_reg, 0, 7); a.emit(bl, "c_xt_set")
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 10); a.emit(bl, "c_mark")
    a.label("xt_x")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)


def knob_levels_code(a, L):
    """The stock LED converter (0x0803423C) lights a knob LED from a dynamic code (0xC1..0x108): the colour of the code scaled by the value of a stock parameter.
    Our knobs have no stock parameter, so the brightness travels in the high byte of the LED halfword: the macro handler's LED slot (slot 7, leds18.c_mhleds
    puts the drum colour on K1 / K3 / K5 / K7) sets (brightness + 2) << 8 | colour code (the stock codes go up to 0x112, so a high byte of 0 or 1 is a stock code), and
    c_ledhook (a bl at the top of the converter's knob loop in place of `ldrh r7, [r6] ; movs r4, #0xff`) splits it again: r7 = colour code, r4 = brightness
    (or 0xFF = unscaled, the stock value for static codes).  The converter
    then scales the colour by r4 exactly as it does for the dynamic codes (b -> 10 % .. 100 %, halved in the dim mode)."""
    # ---- c_lvl(r0 = drum, r1 = code) -> r0 = brightness 0..127 of that value: unipolar = the value, bipolar = twice the distance from the centre (as the stock bipolar
    #      knobs: dark in the middle), filter mode = 0, 32, 64, 96, 127
    a.label("c_lvl")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    if EXTRAS:
        a.emit(cmp_imm, 4, 10); a.emit(b_cond, "lv_n", "lo")
        a.emit(bl, "c_xt_get"); a.emit(cmp_imm, 4, 10); a.emit(b_cond, "lv_sl", "ne")
        a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(movs_imm, 1, 42); a.emit(muls, 0, 1); a.emit(b, "lv_x")
        a.label("lv_sl")
        a.emit(lsrs_imm, 0, 0, 2); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(b_cond, "lv_x", "eq"); a.emit(movs_imm, 0, 127); a.emit(b, "lv_x")
        a.label("lv_n")
    a.emit(bl, "c_dget")
    a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "lv_0", "eq")
    a.emit(cmp_imm, 4, 9); a.emit(b_cond, "lv_m", "eq")
    a.emit(lsls_imm, 0, 0, 25)
    for c in UNIPOLAR:
        a.emit(cmp_imm, 4, c); a.emit(b_cond, "lv_u", "eq")
    a.emit(raw, asrs_imm(0, 0, 25))
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "lv_p", "ge")
    a.emit(raw, h(0x43C0))                                                           # mvns r0, r0 : -s - 1
    a.label("lv_p")
    a.emit(lsls_imm, 0, 0, 1); a.emit(b, "lv_x")
    a.label("lv_u")
    a.emit(lsrs_imm, 0, 0, 25); a.emit(b, "lv_x")
    a.label("lv_m")
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 0, 1); a.emit(cmp_imm, 0, 4); a.emit(b_cond, "lv_m1", "ls"); a.emit(movs_imm, 0, 4)
    a.label("lv_m1")
    a.emit(lsls_imm, 0, 0, 5); a.emit(cmp_imm, 0, 127); a.emit(b_cond, "lv_x", "ls"); a.emit(movs_imm, 0, 127); a.emit(b, "lv_x")
    a.label("lv_0")
    a.emit(movs_imm, 0, 0)
    a.label("lv_x")
    a.emit(pop_list, [4], pc=True)

    # ---- c_mhleds19(obj): slot 7 of the drum macro handlers = leds18.c_mhleds, then the brightness of K1 / K3 / K5 / K7 (the Shift layer's values while Shift is held)
    a.label("c_mhleds19")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0)
    a.emit(bl, L["c_mhleds"]); a.emit(mov_reg, 5, 0)
    a.emit(movs_imm, 6, 0)
    a.label("ml_f")
    a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"]); a.emit(cmp_reg, 0, 4); a.emit(b_cond, "ml_hit", "eq")
    a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 4); a.emit(b_cond, "ml_f", "lo"); a.emit(b, "ml_x")
    a.label("ml_hit")
    a.emit(bl, L["c_shift"]); a.emit(mov_reg, 7, 0)
    if REMAP:
        # the stock knob LEDs follow their parameters: the dynamic codes 0xE1 + 4 d + (0 pitch, 1 decay, 2 distortion, 3 EQ) go to the positions 0, 2, 7, 4 and the drum colour
        # (c_mhleds wrote it at position 0 just now, every call) to 1, 3, 5, 6.  The buffer is persistent: everything is rewritten each call, nothing is read back.
        a.emit(ldrh_imm, 4, 5, 0)
        a.emit(lsls_imm, 1, 6, 2); a.emit(adds_imm8, 1, 0xE1)
        a.emit(strh_imm, 1, 5, 0); a.emit(adds_imm8, 1, 1); a.emit(strh_imm, 1, 5, 4); a.emit(adds_imm8, 1, 1); a.emit(strh_imm, 1, 5, 14); a.emit(adds_imm8, 1, 1); a.emit(strh_imm, 1, 5, 8)
        for pos in (1, 3, 5, 6): a.emit(strh_imm, 4, 5, 2 * pos)
        for pos, plain, shift in (REMAP_LEDS_XT if EXTRAS and EXTRAS_SLOPE else REMAP_LEDS_XT_NS if EXTRAS else REMAP_LEDS):
            skip = f"ml_k{pos}"
            a.emit(mov_reg, 0, 6)
            if plain is not None and shift is not None:
                a.emit(movs_imm, 1, plain); a.emit(cmp_imm, 7, 0); a.emit(b_cond, f"ml_c{pos}", "eq"); a.emit(movs_imm, 1, shift); a.label(f"ml_c{pos}")
            elif plain is not None:
                a.emit(cmp_imm, 7, 0); a.emit(b_cond, skip, "ne"); a.emit(movs_imm, 1, plain)
            else:
                a.emit(cmp_imm, 7, 0); a.emit(b_cond, skip, "eq"); a.emit(movs_imm, 1, shift)
            a.emit(bl, "c_lvl"); a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 4); a.emit(strh_imm, 0, 5, 2 * pos)
            a.label(skip)
        if SPLIT3:
            # K3 (position 2): the attack in white while there is one (else the stock decay); with Shift the start in the drum's colour, the cut in white.  r4 = the drum colour, r6 = the drum, r7 = Shift
            a.emit(cmp_imm, 7, 0); a.emit(b_cond, "k3l_s", "ne")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_k3get"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "k3l_x", "eq")
            a.emit(movs_imm, 1, K3_COL_WHITE); a.emit(b, "k3l_w")
            a.label("k3l_s")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(bl, "c_k3get"); a.emit(mov_reg, 1, 4); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "k3l_w", "ne")
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 2); a.emit(bl, "c_k3get"); a.emit(movs_imm, 1, K3_COL_WHITE)
            a.label("k3l_w")
            a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 1); a.emit(strh_imm, 0, 5, 4)
            a.label("k3l_x")
        if K8_BRIGHT:
            # K8 without Shift: stock distortion (macro 2 of the drum, 0..127) to the right, bitcrush (nibble 4..7 of the extended values, 0..15) to the left; centre = no effect = dimmest.  r4 = the drum colour here.
            a.emit(cmp_imm, 7, 0); a.emit(b_cond, "k8_skip", "ne")
            a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"]); a.emit(ldr_imm, 0, 0, 0xC); a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 7, 0, 0)       # r7 = the distortion
            a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 4); a.emit(bl, "c_dnib_get")                                                                     # r0 = the bitcrush nibble
            a.emit(lsls_imm, 1, 0, 3); a.emit(lsrs_imm, 0, 0, 1); a.emit(adds_reg, 1, 1, 0)                                                              # nibble * 8 + nibble / 2 (15 -> 127)
            a.emit(cmp_reg, 1, 7); a.emit(b_cond, "k8_m", "ls"); a.emit(mov_reg, 7, 1)
            a.label("k8_m")
            a.emit(adds_imm8, 7, 2); a.emit(lsls_imm, 7, 7, 8); a.emit(orrs_reg, 7, 4); a.emit(strh_imm, 7, 5, 14)
            a.label("k8_skip")
        a.emit(b, "ml_clr" if CLEAR else "ml_x")
    for k, plain, shift in KNOB_CODES:
        a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, plain)
        a.emit(cmp_imm, 7, 0); a.emit(b_cond, f"ml_s{k}", "eq"); a.emit(movs_imm, 1, shift)
        a.label(f"ml_s{k}")
        a.emit(bl, "c_lvl")
        a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8)
        a.emit(ldrh_imm, 1, 5, 2 * k); a.emit(orrs_reg, 0, 1); a.emit(strh_imm, 0, 5, 2 * k)
    if CLEAR:
        # Clear feedback: while Clear is held the knobs that completed a stock Clear (counter = 0x28, left = red, right = blue; the stock writes their LED at the stock knob index, here the
        # positions 0 / 2 / 7 / 4 for the macros 0 / 1 / 2 / 3) and the knob of ours turned last (the O_CLR bits) show red / blue; released: the bits are dropped
        a.label("ml_clr")
        a.emit(mov_reg, 0, 6); a.emit(bl, L["c_mh"]); a.emit(mov_reg, 4, 0)
        a.emit(bl, "c_clr_held"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "ml_on", "ne")
        a.emit(raw, ldrb_w(1, 4, O_CLR)); a.emit(movs_imm, 2, 7); a.emit(ands_reg, 1, 2); a.emit(raw, strb_w(1, 4, O_CLR)); a.emit(b, "ml_x")
        a.label("ml_on")
        for sb, pos in ((0, 0), (1, 2), (2, 7), (3, 4)):
            for off, code in ((0x36, CLR_RED), (0x3A, CLR_BLUE)):
                a.emit(raw, ldrb_w(1, 4, off + sb)); a.emit(cmp_imm, 1, 0x28); a.emit(b_cond, f"ml_n{off}_{sb}", "ne")
                a.emit(movs_imm, 0, code); a.emit(strh_imm, 0, 5, 2 * pos)
                a.label(f"ml_n{off}_{sb}")
        a.emit(raw, ldrb_w(1, 4, O_CLR)); a.emit(lsls_imm, 2, 1, 28); a.emit(b_cond, "ml_x", "pl")
        a.emit(lsrs_imm, 0, 1, 5); a.emit(lsls_imm, 0, 0, 1)
        a.emit(movs_imm, 2, CLR_RED); a.emit(lsls_imm, 3, 1, 27); a.emit(b_cond, "ml_r", "pl"); a.emit(movs_imm, 2, CLR_BLUE)
        a.label("ml_r")
        a.emit(strh_reg, 2, 5, 0)
    a.label("ml_x")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ledhook: in the converter's knob loop (r6 = the LED halfword's address; r0-r3 free; lr is saved by the converter)
    a.label("c_ledhook")
    a.emit(ldrh_imm, 7, 6, 0); a.emit(movs_imm, 4, 0xFF)
    a.emit(lsrs_imm, 0, 7, 8); a.emit(cmp_imm, 0, 2); a.emit(b_cond, "lh_x", "lo")
    a.emit(subs_imm8, 0, 2); a.emit(mov_reg, 4, 0)
    a.emit(raw, h(0xB2C0 | 7 << 3 | 7))                                              # uxtb r7, r7
    a.label("lh_x")
    a.emit(raw, h(0x4770))


def install(img, report, base_addr, text):
    """Append table + code at base_addr; re-point the drum knob handler, the DSP service chain head and the three project hooks."""
    import ct_fw
    import build_sc14 as s14
    import drums18
    import drums2_dsp as DD
    BASE = ct_fw.APP_BASE
    assert text(LOAD_END, 4) == LOAD_END_TXT, text(LOAD_END, 4)
    assert text(NEW_TAIL, 4) == NEW_TAIL_TXT, text(NEW_TAIL, 4)
    assert text(SAVE_CALL, 4) == SAVE_CALL_TXT, text(SAVE_CALL, 4)
    assert DD.ABS, "drums2_dsp.ABS must be on (the ARM sends absolute values)"
    assert not CLEAR or (REMAP and KNOB_LEVELS and EXTRAS), "CLEAR needs REMAP, KNOB_LEVELS and EXTRAS"
    s18 = report["sc18"]["labels"]
    assert struct.unpack_from("<I", img, MH_SLOT4 - BASE)[0] == int(s18["c_dk18"], 16) | 1
    assert drums18.decode_bw(img, s14.SVC_HOOK) == int(s18["c_dtick"], 16)
    L = dict(c_mh=int(s18["c_mh"], 16), svc_next=int(s18["svc_next"], 16),
             c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_dknob3=int(report["sc12"]["labels"]["c_dknob3"], 16),
             c_dview=int(report["sc11"]["labels"]["c_dview"], 16), c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16), c_clrall=int(report["sc17"]["labels"]["c_clrall"], 16),
             load_end_instr=bytes(img[LOAD_END - BASE:LOAD_END - BASE + 4]))
    if KNOB_LEVELS:
        L["c_mhleds"] = int(report["leds18"]["labels"]["c_mhleds"], 16)
        assert struct.unpack_from("<I", img, MH_SLOT7 - BASE)[0] == L["c_mhleds"] | 1
        assert bytes(img[LED_CONV_HOOK - BASE:LED_CONV_HOOK - BASE + 4]) == LED_CONV_BYTES, bytes(img[LED_CONV_HOOK - BASE:LED_CONV_HOOK - BASE + 4]).hex()
    tab = table()
    code_at = base_addr + len(tab)
    code, labels = arm_code(code_at, base_addr, L, DD.DB, DD.STRIDE, DD.EXT)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + tab + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    # chromatic / scale drum Preset view: all four rows lit again (SC18.1's c_dleds18 darkened rows 1-2): SC08's LEDs
    assert struct.unpack_from("<I", img, drums18.DP_VT_SLOT7 - BASE)[0] == int(s18["c_dleds18"], 16) | 1
    struct.pack_into("<I", img, drums18.DP_VT_SLOT7 - BASE, int(report["sc08"]["labels"]["c_dleds"], 16) | 1)
    struct.pack_into("<I", img, MH_SLOT4 - BASE, labels["c_dk19"] | 1)
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick19"])
    if BLOB_KEEP:
        assert struct.unpack_from("<I", img, STORE_VT + 12 - BASE)[0] == STORE_COPY | 1
        struct.pack_into("<I", img, STORE_VT + 12 - BASE, labels["c_bcopy"] | 1)
    if KNOB_LEVELS:
        struct.pack_into("<I", img, MH_SLOT7 - BASE, labels["c_mhleds19"] | 1)
        img[LED_CONV_HOOK - BASE:LED_CONV_HOOK - BASE + 4] = bl(LED_CONV_HOOK, labels["c_ledhook"])
    img[LOAD_END - BASE:LOAD_END - BASE + 4] = b_w(LOAD_END, labels["c_pl_load"])
    img[NEW_TAIL - BASE:NEW_TAIL - BASE + 4] = b_w(NEW_TAIL, labels["c_pl_new"])
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_pl_save"])
    return labels, code, dict(table=base_addr, flat=N_XM)
