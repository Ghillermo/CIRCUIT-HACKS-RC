"""SC39.1 (the user, 2026-10-12): patches of the MIDI tracks' own synth (the engine of MIDI 1 / 2: tools/vcf21.py), kept in the pack; and Clear + a page
pad of that view = the values of that knob page back to their defaults (vcf21.use_resetview: Clear + pad 27 no longer resets everything).

Where (the user: «se pueden usar las dos filas centrales de la vista preset de midi 1/2, en un color que no esté en uso … 4 páginas de 16 (con octave
up/down) en los 64 primeros sintes, si no existen se crean init»): rows 2 and 3 (pads 9-24) of the Preset view of MIDI 1 / 2 are 16 patch slots, four
pages with Octave down / up = 64 slots, shared by both tracks.  Slot n lives in the padding of the pack's synth patch n: a record of
Patches/NN_PATCHBANK.cpb is 512 bytes, 340 of the synth patch and 172 of 0xFF, which the stock never writes (the PATCHD diagnostic, 2026-10-12: the
marks survived a project save, a pack change, a power cycle and patch saves).  A record that does not exist yet is created with the stock's Initial
Patch (0x080584F0), as are the records before it (a bank cannot keep a hole).

Gestures: a pad = load the slot into this track (an empty slot does nothing); Duplicate + pad = save this track's engine there; Clear + pad = empty
the slot.  Colours: the idle step colour of the song pointer (dim peach 0x6B) for a slot in use, bright peach 0x6A for the last one loaded / saved,
dark for an empty one.  Not while the CC editor or a step-drummer view is on the screen (they use those pads and Octave).

What a patch holds (42 bytes; «guarda todo si cabe»: it fits): the engine (mode on, oscillator source, the two bits of the engine nibble = VA-drum /
granular / FX sequencer / velocity, two oscillators, the chain order), the step-drummer nibble (enabled + destination), the 26 values of the track and
its 8 OSC2 values.  The steps of the step-drummer and of the FX sequencer are notes / lanes of the pattern: they belong to the project.
    [0..3] "CTM1"  [4] flags (bit 0 on, 1 oscillator, 2 / 3 engine nibble, 4 two oscillators, 5 chain order)  [5] step-drummer nibble
    [6..31] codes 1..26  [32..39] codes 27..34  [40] sum of [4..39]  [41] 1
State (no new RAM): 16 bytes in the Master FX block's idle LED buffer, where packio keeps the voice modes of the synth Preset view (another view,
another tag): the page, the last slot, the 16 "in use" bits of the page with the pack / page / time they were read for (read again when they change
and every 4 s: the page's two banks, at most 4 KB each, into the stock's shared buffer under its lock).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, blx_reg, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w,  # noqa: E402
                   ldrh_imm, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, h, str_imm,
                   strb_imm, strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg, sub_sp_imm, add_sp_imm, tst_reg)
import packio as PK  # noqa: E402
import vcf21 as V  # noqa: E402

TMPL_VT = 0x0805AE5C                  # the Preset view of MIDI 1 / 2 (the template view): slot 0 pads, slot 7 the LED buffer
BTN_ENTRY = 0x08033320                # the controller's button press: its first 4 bytes are a b.w to the chain of hooks
MGR = 0x20040B10
SUBS = (18, 27)                       # [MGR + 0x152] with the Preset view of MIDI 1 / 2 on the screen
MAGIC, MAGIC4 = 0x4D51, 0x314D5443    # the cache's tag; "CTM1"
LIFE = 16                             # x 256 ms: the "in use" bits are read again after ~4 s
OFF, LEN, DATA = 340, 172, 44         # the padding of a record; the bytes of a patch
COL_LIT, COL_DIM = 0x6A, 0x6B         # bright peach / the song pointer's idle step colour (steady codes)
ID_DOWN, ID_UP = 19, 20               # Octave down = the next page, Octave up = the previous one
LED_DOWN, LED_UP, COL_BTN = 51, 52, 0x01
PAGES = 4
INV = V.INV
LSHAPE = False                        # SC43.9 (see use_lshape)


def use_lshape():
    """SC43.9: a patch also holds the LFO shape of the engine (vcf21.use_lfoshape): [41] = 2 (the version) and [42] = the shape 0..5; a patch of
    version 1 (or any other) loads the reverse saw.  The check (the signature, the sum of [4..39]) stays: older firmwares load these patches as before."""
    global LSHAPE
    assert V.LFOSHAPE
    LSHAPE = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def bw_target(img, addr, base):
    """the target of the b.w at addr"""
    h1, h2 = struct.unpack_from("<HH", img, addr - base)
    assert h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0x9000, hex(addr)
    s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
    i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
    off = s << 24 | i1 << 23 | i2 << 22 | (h1 & 0x3FF) << 12 | (h2 & 0x7FF) << 1
    if s: off -= 1 << 25
    return addr + 4 + off


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def tick(rd): imm32(rd, PK.HAL_TICK); E(ldr_imm, rd, rd, 0); E(lsrs_imm, rd, rd, 8)
    BUF, TAIL = PK.BUF, V.TAIL

    # ---- data first (their addresses are known): the codes of the knob pages (16 per page: K1..K8, Shift + K1..K8; row 5 = the granular page, which
    #      takes the place of page 2 with the granular engine), then the default of every code 1..34
    rows = [V.KNOB_CODES, V.KNOB_CODES_B, V.KNOB_CODES_C, V.KNOB_CODES_D, V.KNOB_CODES_E, tuple(g[0] for g in V.GR_TAB)]
    assert all(len(r) == 16 for r in rows)
    t_rows = base; t_def = base + 96
    dflt = tuple(V.DEFAULTS[:26]) + tuple(V.DEFAULTS_V2)
    E(raw, bytes(c for r in rows for c in r) + bytes(v & 0xFF for v in dflt) + bytes(2))
    assert len(dflt) == 34

    # ---- c_mpc() -> r0 = the cache (its tag written when it was someone else's: page 0, nothing read), 0 without the Master FX block; clobbers r1-r3
    #      [0] tag  [2] pack  [3] the page shown  [4] in-use bits  [6] last slot + 1  [7] the page the bits belong to (0xFF: none)  [12] time
    a.label("c_mpc")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "mc_x", "eq")
    E(adds_imm8, 0, PK.PM_CACHE); E(mov_reg, 4, 0)
    E(ldrh_imm, 1, 4, 0); E(movw, 2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "mc_ok", "eq")
    E(movs_imm, 1, 0); E(str_imm, 1, 4, 0); E(str_imm, 1, 4, 4); E(str_imm, 1, 4, 8); E(str_imm, 1, 4, 12)
    E(strh_imm, 2, 4, 0); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 4, 2); E(strb_imm, 1, 4, 7)
    a.label("mc_ok"); E(mov_reg, 0, 4)
    a.label("mc_x"); E(pop_list, [4], pc=True)

    # ---- c_mpon() -> r0 = the track (0 / 1) whose slots are on the screen, or 0xFF (another view, the CC editor, a step-drummer view); clobbers r1-r3
    a.label("c_mpon")
    E(push_list, [4], lr=True)
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "mo_n", "ne")
    E(ldrb_w, 2, 0, V.S_CUR)
    E(movs_imm, 4, 0); E(cmp_imm, 2, SUBS[0]); E(b_cond, "mo_t", "eq")
    E(movs_imm, 4, 1); E(cmp_imm, 2, SUBS[1]); E(b_cond, "mo_n", "ne")
    a.label("mo_t")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "mo_n", "ne")
    E(bl, L["c_sdscr"]); E(cmp_imm, 0, 0xFF); E(b_cond, "mo_n", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("mo_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_mpsz(r0 = bank) -> r0 = the size of its file (0: none); c_mpr / c_mpw(r0 = bank, r1 = offset, r2 = buffer, r3 = length) -> r0 = status,
    #      r1 = the bytes moved; the loaded pack by its number
    a.label("c_mpsz")
    E(push_list, [4, 5], lr=True); E(sub_sp_imm, 16); E(mov_reg, 4, 13)
    E(movs_imm, 1, PK.KIND_PATCH); E(str_imm, 1, 4, 0); E(str_imm, 0, 4, 4)
    E(bl, L["c_curpack"]); E(str_imm, 0, 4, 8)
    E(mov_reg, 0, 4); E(bl, PK.SIZE)
    E(add_sp_imm, 16); E(pop_list, [4, 5], pc=True)
    a.label("c_mpr"); E(push_list, [4, 5, 6, 7], lr=True); imm32(4, PK.READ | 1); E(b, "mp_io")
    a.label("c_mpw"); E(push_list, [4, 5, 6, 7], lr=True); imm32(4, PK.WRITE | 1)
    a.label("mp_io")
    E(sub_sp_imm, 32); E(mov_reg, 7, 13)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(str_imm, 3, 7, 28)
    E(movs_imm, 2, PK.KIND_PATCH); E(str_imm, 2, 7, 16); E(str_imm, 0, 7, 20)
    E(bl, L["c_curpack"]); E(str_imm, 0, 7, 24)
    E(movs_imm, 0, 0); E(str_imm, 0, 7, 0); E(str_imm, 0, 7, 4); E(str_imm, 0, 7, 12)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 12); E(str_imm, 0, 7, 8)
    E(mov_reg, 0, 7); E(adds_imm8, 0, 16); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(ldr_imm, 3, 7, 28); E(blx_reg, 4)
    E(ldr_imm, 1, 7, 12)
    E(add_sp_imm, 32); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mprefresh(r0 = the cache): the in-use bits of the page shown, read when the pack or the page changed or they are older than ~4 s
    a.label("c_mprefresh")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, L["c_curpack"]); E(mov_reg, 5, 0)
    E(ldrb_imm, 1, 4, 2); E(cmp_reg, 1, 5); E(b_cond, "mf_r", "ne")
    E(ldrb_imm, 1, 4, 7); E(ldrb_imm, 2, 4, 3); E(cmp_reg, 1, 2); E(b_cond, "mf_r", "ne")
    tick(0); E(ldrh_imm, 1, 4, 12); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); bc("mf_x", "lo")
    if PK.PLAYHOLD:                                                                  # older, but playing: kept (no card access; packio.use_playhold)
        imm32(0, PK.TRANSPORT); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); bc("mf_x", "ne")
    a.label("mf_r")
    E(strb_imm, 5, 4, 2); E(movs_imm, 0, 0); E(strh_imm, 0, 4, 4)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(movs_imm, 6, 0)
    a.label("mf_b")
    E(ldrb_imm, 0, 4, 3); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 6); E(bl, "c_mpsz"); E(mov_reg, 7, 0)
    E(cmp_imm, 7, 0); E(b_cond, "mf_n", "eq")
    E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 12); E(cmp_reg, 7, 1); E(b_cond, "mf_c", "ls"); E(mov_reg, 7, 1)
    a.label("mf_c")
    E(ldrb_imm, 0, 4, 3); E(lsls_imm, 0, 0, 1); E(adds_reg, 0, 0, 6); E(movs_imm, 1, 0); imm32(2, BUF); E(mov_reg, 3, 7); E(bl, "c_mpr")
    E(cmp_imm, 0, 0); E(b_cond, "mf_n", "ne"); E(mov_reg, 7, 1)                      # r7 = the bytes read
    E(movs_imm, 3, 0)
    a.label("mf_k")
    E(lsls_imm, 0, 3, 9); imm32(1, OFF + 4); E(adds_reg, 0, 0, 1); E(cmp_reg, 0, 7); E(b_cond, "mf_n", "hi")
    E(lsls_imm, 0, 3, 9); imm32(1, BUF + OFF); E(adds_reg, 0, 0, 1); E(ldr_imm, 0, 0, 0); imm32(1, MAGIC4); E(cmp_reg, 0, 1); E(b_cond, "mf_kn", "ne")
    E(lsls_imm, 0, 6, 3); E(adds_reg, 0, 0, 3); E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(ldrh_imm, 0, 4, 4); E(orrs_reg, 0, 1); E(strh_imm, 0, 4, 4)
    a.label("mf_kn")
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "mf_k", "lo")
    a.label("mf_n")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 2); bc("mf_b", "lo")
    E(bl, PK.BUF_UNLOCK)
    E(ldrb_imm, 0, 4, 3); E(strb_imm, 0, 4, 7)
    tick(0); E(strh_imm, 0, 4, 12)
    a.label("mf_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mpleds (the view's slot 7): the stock / vcf21 buffer, then pads 9-24 = the slots of the page
    a.label("c_mpleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_mpon"); E(cmp_imm, 0, 0xFF); E(b_cond, "ml_x", "eq")
    E(bl, "c_mpc"); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "eq"); E(mov_reg, 6, 0)
    E(bl, "c_mprefresh")
    E(ldrh_imm, 7, 6, 4)
    E(ldrb_imm, 0, 6, 3); E(lsls_imm, 0, 0, 4); E(ldrb_imm, 4, 6, 6); E(subs_reg, 4, 4, 0)       # r4 = the last slot's pad of this page + 1
    E(movs_imm, 3, 0)
    a.label("ml_l")
    E(movs_imm, 2, 0); E(movs_imm, 0, 1); E(lsls_reg, 0, 3); E(tst_reg, 7, 0); E(b_cond, "ml_w", "eq")
    E(movs_imm, 2, COL_DIM); E(mov_reg, 0, 3); E(adds_imm8, 0, 1); E(cmp_reg, 0, 4); E(b_cond, "ml_w", "ne")
    E(movs_imm, 2, COL_LIT)
    a.label("ml_w")
    E(mov_reg, 0, 3); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "ml_l", "lo")
    a.label("ml_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mpgather(r0 = track): its engine into the shared buffer (DATA bytes)
    a.label("c_mpgather")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); imm32(5, BUF); imm32(6, TAIL)
    imm32(0, MAGIC4); E(str_imm, 0, 5, 0)
    E(ldrb_w, 0, 6, V.O_FLAGS); E(lsrs_reg, 0, 4); E(movs_imm, 7, 1); E(ands_reg, 7, 0)                      # bit 0: the mode is on
    E(lsrs_imm, 0, 0, 2); E(movs_imm, 1, 1); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 1); E(orrs_reg, 7, 0)      # bit 1: the oscillator
    E(ldrb_w, 0, 6, V.O_SIG); E(lsrs_reg, 0, 4); E(movs_imm, 1, 5); E(ands_reg, 0, 1)                        # bits 0 / 2 of the engine nibble
    E(lsrs_imm, 1, 0, 1); E(orrs_reg, 0, 1); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(lsls_imm, 0, 0, 2); E(orrs_reg, 7, 0)   # -> bits 2 / 3
    E(lsls_imm, 0, 4, 3); E(adds_reg, 0, 0, 6)
    E(ldrb_w, 1, 0, V.O_RT + V.RT_VEL); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, 4); E(orrs_reg, 7, 1)
    E(ldrb_w, 1, 0, V.O_RT + V.RT_NOTE); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, 5); E(orrs_reg, 7, 1)
    E(strb_imm, 7, 5, 4)
    E(mov_reg, 0, 4); E(bl, L["c_sdnib"]); E(strb_imm, 0, 5, 5)
    E(movs_imm, 0, V.STRIDE); E(muls, 0, 4); E(adds_reg, 0, 0, 6); E(adds_imm8, 0, V.O_PAR)
    E(movs_imm, 3, 0)
    a.label("mg_v"); E(ldrb_reg, 2, 0, 3); E(mov_reg, 1, 3); E(adds_imm8, 1, 6); E(strb_reg, 2, 5, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, 26); E(b_cond, "mg_v", "lo")
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "mg_d", "eq")
    E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, V.V2_OFF)
    E(movs_imm, 3, 0)
    a.label("mg_w"); E(ldrb_reg, 2, 0, 3); E(mov_reg, 1, 3); E(adds_imm8, 1, 32); E(strb_reg, 2, 5, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "mg_w", "lo")
    E(b, "mg_s")
    a.label("mg_d")
    for k, v in enumerate(V.DEFAULTS_V2): E(movs_imm, 2, v & 0xFF); E(strb_w, 2, 5, 32 + k)
    a.label("mg_s")
    E(bl, "c_mpsum"); E(movs_imm, 1, 40); E(strb_reg, 0, 5, 1); E(movs_imm, 0, 1); E(movs_imm, 1, 41); E(strb_reg, 0, 5, 1)
    if LSHAPE:                                                                                               # version 2: + the LFO shape
        E(movs_imm, 0, 2); E(strb_reg, 0, 5, 1); E(mov_reg, 0, 4); E(bl, L["c_vlsh"]); E(movs_imm, 1, 42); E(strb_reg, 0, 5, 1)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mpsum() -> r0 = the sum of the buffer's bytes 4..39; clobbers r1-r3
    a.label("c_mpsum")
    imm32(1, BUF); E(movs_imm, 0, 0); E(movs_imm, 3, 4)
    a.label("mu_l"); E(ldrb_reg, 2, 1, 3); E(adds_reg, 0, 0, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, 40); E(b_cond, "mu_l", "lo")
    E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(raw, h(0x4770))

    # ---- c_mpapply(r0 = track): the buffer's patch into the engine of the track; everything goes to the DSP again (the settings are not saved here)
    a.label("c_mpapply")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); imm32(5, BUF); imm32(6, TAIL)
    E(ldrb_imm, 7, 5, 4)
    E(ldrb_w, 0, 6, V.O_FLAGS); E(movs_imm, 1, 4); E(lsls_reg, 1, 4); E(bics_reg, 0, 1)                      # the oscillator flag
    E(lsrs_imm, 2, 7, 1); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(lsls_imm, 2, 2, 2); E(lsls_reg, 2, 4); E(orrs_reg, 0, 2); E(strb_w, 0, 6, V.O_FLAGS)
    E(ldrb_w, 0, 6, V.O_SIG); E(movs_imm, 1, 5); E(lsls_reg, 1, 4); E(bics_reg, 0, 1)                        # the engine nibble
    E(lsrs_imm, 2, 7, 2); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(lsrs_imm, 1, 7, 3); E(ands_reg, 1, 3); E(lsls_imm, 1, 1, 2); E(orrs_reg, 2, 1)
    E(lsls_reg, 2, 4); E(orrs_reg, 0, 2); E(strb_w, 0, 6, V.O_SIG)
    E(lsls_imm, 0, 4, 3); E(adds_reg, 0, 0, 6)
    for off, bit in ((V.RT_VEL, 4), (V.RT_NOTE, 5)):                                                         # two oscillators, the chain order
        E(ldrb_w, 1, 0, V.O_RT + off); E(lsls_imm, 1, 1, 25); E(lsrs_imm, 1, 1, 25)
        E(lsrs_imm, 2, 7, bit); E(movs_imm, 3, 1); E(ands_reg, 2, 3); E(lsls_imm, 2, 2, 7); E(orrs_reg, 1, 2); E(strb_w, 1, 0, V.O_RT + off)
    E(mov_reg, 0, 4); E(ldrb_imm, 1, 5, 5); E(movs_imm, 2, 15); E(ands_reg, 1, 2); E(bl, L["c_sdsetnib"])
    E(movs_imm, 0, V.STRIDE); E(muls, 0, 4); E(adds_reg, 0, 0, 6); E(adds_imm8, 0, V.O_PAR)
    E(movs_imm, 3, 0)
    a.label("ma_v"); E(mov_reg, 1, 3); E(adds_imm8, 1, 6); E(ldrb_reg, 2, 5, 1); E(strb_reg, 2, 0, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 26); E(b_cond, "ma_v", "lo")
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ma_s", "eq")
    E(lsls_imm, 1, 4, 3); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, V.V2_OFF)
    E(movs_imm, 3, 0)
    a.label("ma_w"); E(mov_reg, 1, 3); E(adds_imm8, 1, 32); E(ldrb_reg, 2, 5, 1); E(strb_reg, 2, 0, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "ma_w", "lo")
    a.label("ma_s")
    if LSHAPE:                                                                                               # the LFO shape (version 2), else the reverse saw
        E(movs_imm, 2, 41); E(ldrb_reg, 0, 5, 2); E(movs_imm, 1, 0); E(cmp_imm, 0, 2); E(b_cond, "ma_ls", "ne")
        E(movs_imm, 2, 42); E(ldrb_reg, 1, 5, 2); E(cmp_imm, 1, V.LS_N); E(b_cond, "ma_ls", "lo"); E(movs_imm, 1, 0)
        a.label("ma_ls"); E(mov_reg, 0, 4); E(bl, L["c_vlsset"])
    E(movs_imm, 1, 1); E(ands_reg, 7, 1)                                                                     # r7 = the mode on
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, L["c_vset"])                                                  # on: every value marked to be sent
    E(cmp_imm, 7, 0); E(b_cond, "ma_on", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_vset"]); E(b, "ma_pg")
    a.label("ma_on")                                                                                         # the patch flip of the track goes off, as pad 27 does
    E(bl, L["c_settings"]); E(cmp_imm, 0, 0); E(b_cond, "ma_pg", "eq")
    E(movs_imm, 1, 2); E(bl, V.PARAM_PTR); E(ldr_imm, 1, 0, 0)
    E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 26); E(lsls_reg, 3, 4); E(bics_reg, 1, 3); E(str_imm, 1, 0, 0)
    E(bl, L["c_settings"]); E(bl, V.COMMIT)
    a.label("ma_pg")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_vsetpage"])
    E(pop_list, [4, 5, 6, 7], pc=True)

    def slot_ofs(rd, rs):                                                             # rd = 512 x (slot & 7)
        E(lsls_imm, rd, rs, 29); E(lsrs_imm, rd, rd, 20)

    def mark(slot_reg, last):                                                         # the cache: the bits read again, the last slot
        zc[0] += 1; n = f"_k{zc[0]}"
        E(bl, "c_mpc"); E(cmp_imm, 0, 0); E(b_cond, n, "eq")
        E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 7)
        if last == "set": E(mov_reg, 1, slot_reg); E(adds_imm8, 1, 1); E(strb_imm, 1, 0, 6)
        else:
            E(ldrb_imm, 1, 0, 6); E(mov_reg, 2, slot_reg); E(adds_imm8, 2, 1); E(cmp_reg, 1, 2); E(b_cond, n, "ne"); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 6)
        a.label(n)

    # ---- c_mpload(r0 = track, r1 = slot): the slot's patch into the track (nothing when the slot is empty or damaged)
    a.label("c_mpload")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 6, 0)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 5, 3); slot_ofs(1, 5); imm32(2, OFF); E(adds_reg, 1, 1, 2); imm32(2, BUF); E(movs_imm, 3, DATA); E(bl, "c_mpr")
    E(cmp_imm, 0, 0); E(b_cond, "mld_u", "ne"); E(cmp_imm, 1, DATA); E(b_cond, "mld_u", "ne")
    imm32(0, BUF); E(ldr_imm, 0, 0, 0); imm32(1, MAGIC4); E(cmp_reg, 0, 1); E(b_cond, "mld_u", "ne")
    E(bl, "c_mpsum"); imm32(1, BUF); E(movs_imm, 2, 40); E(ldrb_reg, 1, 1, 2); E(cmp_reg, 0, 1); E(b_cond, "mld_u", "ne")
    E(mov_reg, 0, 4); E(bl, "c_mpapply"); E(movs_imm, 6, 1)
    a.label("mld_u")
    E(bl, PK.BUF_UNLOCK)
    E(cmp_imm, 6, 0); E(b_cond, "mld_x", "eq")
    mark(5, "set")
    imm32(0, V.SETOBJ); E(bl, V.SAVE_FN)
    a.label("mld_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_mpsave(r0 = track, r1 = slot): the track's engine into the slot; the record (and the ones before it) made of the Initial Patch when missing
    a.label("c_mpsave")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 5, 3); E(bl, "c_mpsz"); E(mov_reg, 6, 0)                          # r6 = the bank's size
    slot_ofs(7, 5)                                                                    # r7 = the record's offset
    imm32(0, BUF + 512); E(movs_imm, 1, 1); E(lsls_imm, 1, 1, 9); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    imm32(0, OFF); E(adds_reg, 0, 0, 7); E(cmp_reg, 6, 0); bc("msv_h", "hs")
    E(lsls_imm, 0, 6, 23); E(lsrs_imm, 0, 0, 23); E(cmp_imm, 0, 0); E(b_cond, "msv_l", "eq")       # the last record has no padding yet: 0xFF up to 512
    E(movs_imm, 3, 1); E(lsls_imm, 3, 3, 9); E(subs_reg, 3, 3, 0)
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 6); imm32(2, BUF + 512); E(bl, "c_mpw"); E(cmp_imm, 0, 0); bc("msv_x", "ne")
    imm32(0, 511); E(adds_reg, 6, 6, 0); E(lsrs_imm, 6, 6, 9); E(lsls_imm, 6, 6, 9)
    a.label("msv_l")                                                                  # the records from the bank's end to this one: the Initial Patch
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 6); imm32(2, PK.INIT_PATCH); imm32(3, PK.PATCH_SZ); E(bl, "c_mpw"); E(cmp_imm, 0, 0); bc("msv_x", "ne")
    E(cmp_reg, 6, 7); bc("msv_h", "hs")
    E(lsrs_imm, 0, 5, 3); imm32(1, OFF); E(adds_reg, 1, 1, 6); imm32(2, BUF + 512); E(movs_imm, 3, LEN); E(bl, "c_mpw"); E(cmp_imm, 0, 0); bc("msv_x", "ne")
    E(movs_imm, 0, 1); E(lsls_imm, 0, 0, 9); E(adds_reg, 6, 6, 0); E(b, "msv_l")
    a.label("msv_h")
    imm32(0, BUF); E(movs_imm, 1, LEN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(mov_reg, 0, 4); E(bl, "c_mpgather")
    E(lsrs_imm, 0, 5, 3); imm32(1, OFF); E(adds_reg, 1, 1, 7); imm32(2, BUF); E(movs_imm, 3, LEN); E(bl, "c_mpw"); E(cmp_imm, 0, 0); bc("msv_x", "ne")
    mark(5, "set")
    a.label("msv_x")
    E(bl, PK.BUF_UNLOCK)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mpclear(r0 = slot): the slot's padding back to 0xFF (only what the file holds of it)
    a.label("c_mpclear")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 0)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 5, 3); E(bl, "c_mpsz"); E(mov_reg, 6, 0)
    slot_ofs(4, 5); imm32(0, OFF); E(adds_reg, 4, 4, 0)                               # r4 = the padding's offset
    E(cmp_reg, 6, 4); bc("mcl_x", "ls")
    E(subs_reg, 6, 6, 4); E(cmp_imm, 6, LEN); E(b_cond, "mcl_n", "ls"); E(movs_imm, 6, LEN)
    a.label("mcl_n")
    imm32(0, BUF); E(movs_imm, 1, LEN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 4); imm32(2, BUF); E(mov_reg, 3, 6); E(bl, "c_mpw")
    mark(5, "clr")
    a.label("mcl_x")
    E(bl, PK.BUF_UNLOCK)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_mprst(r0 = track, r1 = page 0..4): the values of that knob page (both layers) back to their defaults, sent again, saved
    a.label("c_mprst")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 1); E(b_cond, "mr_t", "ne")                                         # page 2 with the granular engine: its own table
    E(mov_reg, 0, 4); E(movs_imm, 1, 2); E(bl, L["c_vflag"]); E(cmp_imm, 0, 0); E(b_cond, "mr_t", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_vdbit"]); E(cmp_imm, 0, 0); E(b_cond, "mr_t", "ne")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 2); E(bl, L["c_vdbit"]); E(cmp_imm, 0, 0); E(b_cond, "mr_t", "eq")
    E(movs_imm, 5, 5)
    a.label("mr_t")
    E(lsls_imm, 5, 5, 4); imm32(0, t_rows); E(adds_reg, 5, 5, 0)                      # r5 = the page's codes
    E(movs_imm, 6, 0)
    a.label("mr_l")
    E(ldrb_reg, 7, 5, 6); E(cmp_imm, 7, 0); E(b_cond, "mr_n", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, L["c_vvaddr"])
    imm32(1, t_def - 1); E(ldrb_reg, 1, 1, 7); E(strb_imm, 1, 0, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 7); E(bl, L["c_vmark"])
    a.label("mr_n")
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 16); E(b_cond, "mr_l", "lo")
    imm32(0, V.SETOBJ); E(bl, V.SAVE_FN)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mppad (the view's slot 0: view, pad, velocity): pads 9-24 = the slots; Clear + a page pad (1-5, the mode on) = that page's defaults
    a.label("c_mppad")
    E(cmp_imm, 1, 4); E(b_cond, "mp_ns", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_mpon"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); E(b_cond, "mp_fp", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "mp_fp", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(lsls_imm, 0, 0, 31); E(b_cond, "mp_fp", "pl")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_mprst")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("mp_ns")
    E(cmp_imm, 1, 8); E(b_cond, "mp_f", "lo"); E(cmp_imm, 1, 23); E(b_cond, "mp_f", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_mpon"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); E(b_cond, "mp_fp", "eq")
    E(bl, "c_mpc"); E(mov_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "mp_fp", "eq")
    E(ldrb_imm, 0, 6, 3); E(lsls_imm, 0, 0, 4); E(subs_imm8, 5, 8); E(adds_reg, 5, 5, 0)        # r5 = the slot
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 7, 0, 0)
    E(movs_imm, 0, 2); E(tst_reg, 7, 0); E(b_cond, "mp_nd", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_mpsave"); E(b, "mp_e")
    a.label("mp_nd")
    E(movs_imm, 0, 1); E(tst_reg, 7, 0); E(b_cond, "mp_nc", "eq")
    E(mov_reg, 0, 5); E(bl, "c_mpclear"); E(b, "mp_e")
    a.label("mp_nc")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_mpload")
    a.label("mp_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("mp_fp"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.label("mp_f"); E(b_w, prev["pad"])

    # ---- c_mpbtn (the controller's button press: ctrl, id): Octave down / up = the next / previous page while the slots are on the screen
    a.label("c_mpbtn")
    E(cmp_imm, 1, ID_DOWN); E(b_cond, "mb_f", "lo"); E(cmp_imm, 1, ID_UP); E(b_cond, "mb_f", "hi")
    E(push_list, [0, 1, 4], lr=True)
    E(mov_reg, 4, 1)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mb_fp", "ne")
    E(bl, "c_mpon"); E(cmp_imm, 0, 0xFF); E(b_cond, "mb_fp", "eq")
    E(bl, "c_mpc"); E(cmp_imm, 0, 0); E(b_cond, "mb_fp", "eq")
    E(ldrb_imm, 1, 0, 3)
    E(cmp_imm, 4, ID_UP); E(b_cond, "mb_dn", "ne")
    E(cmp_imm, 1, 0); E(b_cond, "mb_e", "eq"); E(subs_imm8, 1, 1); E(b, "mb_s")
    a.label("mb_dn")
    E(cmp_imm, 1, PAGES - 1); E(b_cond, "mb_e", "hs"); E(adds_imm8, 1, 1)
    a.label("mb_s"); E(strb_imm, 1, 0, 3)
    a.label("mb_e"); E(pop_list, [0, 1, 4], pc=True)
    a.label("mb_fp"); E(raw, popw([0, 1, 4], lr=True))
    a.label("mb_f"); E(b_w, prev["btn"])

    # ---- c_mpledtask (the LED task calls: ctrl, frame): the chain, then Octave down / up lit when there is a next / previous page
    a.label("c_mpledtask")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_mpon"); E(cmp_imm, 0, 0xFF); E(b_cond, "mt_x", "eq")
    E(bl, "c_mpc"); E(cmp_imm, 0, 0); E(b_cond, "mt_x", "eq")
    E(ldrb_imm, 4, 0, 3)
    E(movs_imm, 2, 0); E(cmp_imm, 4, 0); E(b_cond, "mt_u", "eq"); E(movs_imm, 2, COL_BTN)
    a.label("mt_u"); E(movs_imm, 0, 2 * LED_UP); E(strh_reg, 2, 5, 0)
    E(movs_imm, 2, 0); E(cmp_imm, 4, PAGES - 1); E(b_cond, "mt_d", "hs"); E(movs_imm, 2, COL_BTN)
    a.label("mt_d"); E(movs_imm, 0, 2 * LED_DOWN); E(strh_reg, 2, 5, 0)
    a.label("mt_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_mphmask (the container's slot 8: view) -> the held buttons it accepts; + Duplicate in the Preset view of MIDI 1 / 2
    a.label("c_mphmask")
    E(push_list, [4], lr=True)
    E(bl, prev["hmask"]); E(mov_reg, 4, 0)
    imm32(1, MGR); E(ldrb_w, 1, 1, V.S_CUR)
    for v in SUBS: E(cmp_imm, 1, v); E(b_cond, "mh_d", "eq")
    E(b, "mh_x")
    a.label("mh_d"); E(movs_imm, 0, 2); E(orrs_reg, 4, 0)
    a.label("mh_x"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the template view's slots 0 / 7, the head of the button chain, the two LED task calls and the container's slot 8."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_gfst=lab("sc17", "c_gfst"), c_shift=lab("sc15", "c_shift"), c_settings=lab("sc06", "c_settings"),
             c_curpack=lab("packio", "c_curpack"))
    for n in ("c_edact", "c_sdscr", "c_sdnib", "c_sdsetnib", "c_vset", "c_vsetpage", "c_von", "c_vflag", "c_vdbit", "c_vvaddr", "c_vmark"): L[n] = lab("vcf20", n)
    if LSHAPE:
        for n in ("c_vlsh", "c_vlsset"): L[n] = lab("vcf20", n)
    prev = dict(pad=u(TMPL_VT) & ~1, leds=u(TMPL_VT + 28) & ~1, btn=bw_target(img, BTN_ENTRY, BASE), hmask=u(PK.CT_VT + 0x20) & ~1,
                ledtask=lab("packio", "c_pkled"))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, TMPL_VT - BASE, labels["c_mppad"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 28 - BASE, labels["c_mpleds"] | 1)
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_mpbtn"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_mpledtask"])
    struct.pack_into("<I", img, PK.CT_VT + 0x20 - BASE, labels["c_mphmask"] | 1)
    return labels, code, prev
