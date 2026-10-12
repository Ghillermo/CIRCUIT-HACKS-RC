"""SC39.4 (the user, 2026-10-12: «guardar patch actual al banco» … «Clear + pad si está disponible (entendido como que "borra" el almacén y lo
sustituye por el patch actual)» … «pide confirmar»): the patch a synth is playing, with its edits (the macro destinations of SC39.3 too), written into
a slot of the pack's bank from the device.  The stock has no panel gesture for it (docs/RELEVO.md, PATCHD): only Components saves patches.

Use (the Preset view of Synth 1 / 2, any of its four pages): Clear + a pad = that slot blinks white; Clear + the same pad again within ~5 s = the
synth's patch is written there (an existing patch is replaced) and the slot becomes the chosen one.  Clear + another pad moves the question to it;
anything else, or the time, drops it.  The stock ignores Clear in that view's pad handler (0x0804D242 never reads the held buttons), so the gesture
was free; without the question open the pad does what it did.

Data: the synths keep their patch in RAM in the bank's own format, 340 bytes (name, category, genre, the parameters), Synth 1 at 0x20010044 and
Synth 2 344 bytes after (each with a pointer to itself in front, checked before writing): what the session saves and 0x08034D92 edits.  The write
is the stock's content API by the helpers of the own-synth patches (mpatch.c_mpsz / c_mpw: the loaded pack by its number): 340 bytes at
512 x (patch % 8) of bank patch / 8, so the 172 bytes of padding of the record (the own-synth patch of MIDI 1 / 2) stay; a slot past the end of the
bank: 0xFF from the end of the file up to it first, as the stock's own save (0x0802FBCC) and packio's FFGAP do (the slots between stay empty).
Then the pad goes on to the chain: the stock chooses the slot (loads what was just written) unless it is the one already chosen.

The own-synth patches of MIDI 1 / 2 (tools/mpatch.py) take the same gesture (the user: «mantén el mismo atajo para guardar patches de sinte propio»
… «y además Duplicate intercambia posiciones»): in the Preset view of MIDI 1 / 2, Clear + a slot pad asks (it blinks white) and Clear + the same pad
again saves the track's engine there (mpatch.c_mpsave; before: Duplicate + pad saved at once and Clear + pad emptied the slot: no gesture empties a
slot now); Duplicate + slot A (it blinks) + slot B = the two own-synth patches change places (64 bytes of the padding: the patch and its name; A must
hold a patch and B's record must exist in its bank; an empty B leaves A empty).  A plain pad loads as before.  This is a hook in front of mpatch's:
SC39.1-SC39.3 do not change.
Also there (the user: «en MIDI 1 y MIDI 2: Clear + MIDI 1 / 2: restablece a parche inicial. Los pads que corresponden a parches vacíos se colorean en
purple»): Clear + the track's own button, with a view of that track on the screen and the CC editor closed = every value of its engine back to the
initial one (vcf21.c_vreset: what Clear + pad 27 did up to SC39; the engine chosen stays); the empty slots are violet (0x49, a steady code) instead
of dark.  And (the user: «durante la selección de patch de usuario, reproduce la tónica de la escala con el patch seleccionado en el momento de
seleccionarlo»): a plain pad that loads a slot plays the root of the scale on that track with the patch just loaded (vcf21.c_sdio, the step-drummer's
audition: a note of the MIDI track, velocity 100) until the pad is let go (the view's slot 1), another pad or any button.

State (no new RAM): 6 bytes of the Master FX block's idle LED buffer after the macro editor's (c_gst() + 124):
    [0] tag  [1] 0x80 | patch or slot (0: nothing asked)  [2] 0 / 1 = asked in Synth 1 / 2, 2 / 3 = asked in MIDI 1 / 2, 4 = Duplicate's slot A
    [3] the pack of slot A  [4..5] the time of the question  [6] 0x80 | the note of the audition (0: none)  [7] its track
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, ldrh_imm, ldrh_reg, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, h, strb_imm, strh_imm, strh_reg, subs_imm8,
                   subs_reg, tst_reg)
import packio as PK  # noqa: E402
import vcf21 as V  # noqa: E402
import macroed as MC  # noqa: E402
import mpatch as MP  # noqa: E402

SP_VT = MC.SP_VT                      # the Preset view of the synths: slot 0 pads, slot 7 LEDs
MGR = MC.MGR
PATCH_RAM, PATCH_RAM_STRIDE = 0x20010044, 344      # the patch of Synth 1 in RAM; Synth 2's follows
ST_OFF, MAGIC = MC.ST_OFF + 4, 0x5A
LIFE = 20                             # the question stays open ~5 s (units of 256 ms)
COL_ASK = 0x01                        # the slot asked about blinks white
COL_A = MP.COL_LIT                     # Duplicate's slot A blinks bright peach
COL_EMPTY = 0x49                       # an empty own-synth slot: violet (steady)
BTN_ENTRY = MP.BTN_ENTRY
K_MIDI, K_DUP = 2, 4
TMPL_VT = MP.TMPL_VT
XLEN = 64                             # an exchange moves the 44 bytes of the patch and the 16 of the name tools/patchtool.py keeps after them (padding + 44)
XBUF = PK.BUF + 128                   # the second patch of an exchange in the shared buffer
INV8 = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_s{zc[0]}"
        E(b_cond, n, INV8[cond]); E(b, target); a.label(n)
    def tick(rd): imm32(rd, PK.HAL_TICK); E(ldr_imm, rd, rd, 0); E(lsrs_imm, rd, rd, 8); E(lsls_imm, rd, rd, 16); E(lsrs_imm, rd, rd, 16)

    # ---- c_psst() -> r0 = the state (tag written when the bytes were someone else's: nothing asked), 0 without the block; clobbers r1-r3
    a.label("c_psst")
    E(push_list, [4], lr=True)
    E(bl, L["c_gst"]); E(cmp_imm, 0, 0); E(b_cond, "ss_x", "eq")
    E(adds_imm8, 0, ST_OFF)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "ss_x", "eq")
    E(movs_imm, 1, MAGIC); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 1); E(strb_imm, 1, 0, 6)
    a.label("ss_x"); E(pop_list, [4], pc=True)

    # ---- c_psaoff(): the note of the audition ends; clobbers r0-r3
    a.label("c_psaoff")
    E(push_list, [4], lr=True)
    E(bl, "c_psst"); E(cmp_imm, 0, 0); E(b_cond, "sa_x", "eq")
    E(ldrb_imm, 3, 0, 6); E(cmp_imm, 3, 0); E(b_cond, "sa_x", "eq")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, 6)
    E(movs_imm, 1, 0x7F); E(ands_reg, 3, 1); E(ldrb_imm, 0, 0, 7); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(bl, L["c_sdio"])
    a.label("sa_x"); E(pop_list, [4], pc=True)

    # ---- c_pson() -> r0 = the synth (0 / 1) whose Preset view (its patches: not the source view, not a step-drummer view) is on the screen, or 0xFF
    a.label("c_pson")
    E(push_list, [4], lr=True)
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "so_n", "ne")
    E(ldrb_w, 2, 0, V.S_CUR)
    E(movs_imm, 4, 0); E(cmp_imm, 2, 0); E(b_cond, "so_t", "eq")
    E(movs_imm, 4, 1); E(cmp_imm, 2, 9); E(b_cond, "so_n", "ne")
    a.label("so_t")
    E(bl, L["c_srcv"]); E(cmp_imm, 0, 0); E(b_cond, "so_n", "ne")
    E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("so_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_pswrite(r0 = synth, r1 = patch 0..127) -> r0 = status (0 = written): the synth's 340 bytes into the slot of the loaded pack's bank
    a.label("c_pswrite")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    imm32(4, PATCH_RAM); E(cmp_imm, 0, 0); E(b_cond, "sw_a", "eq"); imm32(2, PATCH_RAM_STRIDE); E(adds_reg, 4, 4, 2)
    a.label("sw_a")
    E(subs_imm8, 4, 4); E(ldr_imm, 0, 4, 0); E(adds_imm8, 4, 4); E(cmp_reg, 0, 4); E(b_cond, "sw_ok", "eq")   # the pointer to itself in front
    E(movs_imm, 0, 9); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("sw_ok")
    E(lsls_imm, 6, 5, 29); E(lsrs_imm, 6, 6, 20)                                      # r6 = 512 x (patch % 8)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 5, 3); E(bl, L["c_mpsz"]); E(mov_reg, 7, 0)                        # r7 = the bank's size
    E(cmp_reg, 7, 6); E(b_cond, "sw_w", "hs")
    imm32(0, PK.BUF); E(subs_reg, 1, 6, 7); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)    # past its end: 0xFF up to the slot
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 7); imm32(2, PK.BUF); E(subs_reg, 3, 6, 7); E(bl, L["c_mpw"]); E(cmp_imm, 0, 0); E(b_cond, "sw_u", "ne")
    a.label("sw_w")
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 6); E(mov_reg, 2, 4); imm32(3, PK.PATCH_SZ); E(bl, L["c_mpw"])
    a.label("sw_u"); E(mov_reg, 4, 0); E(bl, PK.BUF_UNLOCK); E(mov_reg, 0, 4)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_pspad (the synth Preset view's slot 0: view, pad, velocity): Clear + pad asks, Clear + the same pad again writes
    a.label("c_pspad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_pson"); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); E(b_cond, "sp_f", "eq")
    E(bl, "c_psst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "sp_f", "eq")
    imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 6, 0, 0)
    E(movs_imm, 0, 3); E(ands_reg, 6, 0); E(cmp_imm, 6, 1); E(b_cond, "sp_drop", "ne")    # Clear held and Duplicate not
    E(cmp_imm, 5, 32); E(b_cond, "sp_drop", "hs")
    E(raw, h(0x9800)); E(ldr_imm, 0, 0, 0x20); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)   # (ldr r0, [sp]) the page shown
    E(lsls_imm, 0, 0, 5); E(adds_reg, 5, 5, 0); E(cmp_imm, 5, 128); E(b_cond, "sp_drop", "hs")               # r5 = the patch
    E(movs_imm, 6, 0x80); E(orrs_reg, 6, 5)
    E(ldrb_imm, 0, 7, 1); E(cmp_reg, 0, 6); E(b_cond, "sp_ask", "ne")
    E(ldrb_imm, 0, 7, 2); E(cmp_reg, 0, 4); E(b_cond, "sp_ask", "ne")
    tick(0); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "sp_ask", "hs")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1)                                           # asked and confirmed: write
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_pswrite"); E(cmp_imm, 0, 0); E(b_cond, "sp_e", "ne")
    E(b, "sp_f")                                                                      # written: the stock chooses the slot
    a.label("sp_ask")
    E(strb_imm, 6, 7, 1); E(strb_imm, 4, 7, 2); tick(0); E(strh_imm, 0, 7, 4)
    a.label("sp_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("sp_drop"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1)
    a.label("sp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_psleds (that view's slot 7: view -> the buffer): the slot asked about blinks; the question ends with its time
    a.label("c_psleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_psst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "sl_x", "eq")
    E(ldrb_imm, 0, 7, 1); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "eq")
    E(ldrb_imm, 0, 7, 2); E(cmp_imm, 0, K_MIDI); E(b_cond, "sl_x", "hs")              # (the MIDI views' own)
    tick(0); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "sl_live", "lo")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1); E(b, "sl_x")
    a.label("sl_live")
    E(bl, "c_pson"); E(ldrb_imm, 1, 7, 2); E(cmp_reg, 0, 1); E(b_cond, "sl_x", "ne")
    E(ldr_imm, 0, 6, 0x20); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)                     # the page shown
    E(ldrb_imm, 1, 7, 1); E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2); E(lsrs_imm, 2, 1, 5); E(cmp_reg, 2, 0); E(b_cond, "sl_x", "ne")
    E(movs_imm, 2, 31); E(ands_reg, 1, 2); E(lsls_imm, 1, 1, 1)
    imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 7); E(movs_imm, 2, 1); E(ands_reg, 0, 2)
    E(movs_imm, 2, COL_ASK); E(cmp_imm, 0, 0); E(b_cond, "sl_w", "eq"); E(movs_imm, 2, 0)
    a.label("sl_w"); E(strh_reg, 2, 5, 1)
    a.label("sl_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ================= the own-synth patches of MIDI 1 / 2 =================
    def held(rd):
        imm32(0, MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, rd, 0, 0)
    def pad_ofs(rd, rs):                                                              # rd = 512 x (slot % 8) + 340; clobbers r3
        E(lsls_imm, rd, rs, 29); E(lsrs_imm, rd, rd, 20); imm32(3, MP.OFF); E(adds_reg, rd, rd, 3)

    # ---- c_psxswap(r0 = slot A, r1 = slot B): the two own-synth patches change places (A must hold one; B's record must exist)
    a.label("c_psxswap")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(movs_imm, 0, 5); E(bl, PK.BUF_LOCK)
    E(lsrs_imm, 0, 4, 3); pad_ofs(1, 4); imm32(2, PK.BUF); E(movs_imm, 3, XLEN); E(bl, L["c_mpr"])
    E(cmp_imm, 0, 0); bc("xs_u", "ne"); E(cmp_imm, 1, XLEN); bc("xs_u", "ne")
    imm32(0, PK.BUF); E(ldr_imm, 0, 0, 0); imm32(1, MP.MAGIC4); E(cmp_reg, 0, 1); bc("xs_u", "ne")
    E(lsrs_imm, 0, 5, 3); E(bl, L["c_mpsz"]); E(mov_reg, 6, 0)                        # r6 = the size of B's bank
    pad_ofs(7, 5); E(cmp_reg, 6, 7); bc("xs_u", "lo")                                 # B's record is not there
    imm32(0, XBUF); E(movs_imm, 1, XLEN); E(movs_imm, 2, 0xFF); E(bl, PK.MEMSET)
    E(mov_reg, 0, 7); E(adds_imm8, 0, XLEN); E(cmp_reg, 6, 0); E(b_cond, "xs_w", "lo")     # B's padding is not in the file: empty
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 7); imm32(2, XBUF); E(movs_imm, 3, XLEN); E(bl, L["c_mpr"]); E(cmp_imm, 0, 0); bc("xs_u", "ne")
    a.label("xs_w")
    E(lsrs_imm, 0, 5, 3); E(mov_reg, 1, 7); imm32(2, PK.BUF); E(movs_imm, 3, XLEN); E(bl, L["c_mpw"]); E(cmp_imm, 0, 0); bc("xs_u", "ne")
    E(lsrs_imm, 0, 4, 3); pad_ofs(1, 4); imm32(2, XBUF); E(movs_imm, 3, XLEN); E(bl, L["c_mpw"])
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); E(b_cond, "xs_u", "eq")                      # the slots' bits read again; the last slot follows its patch
    E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 7)
    E(ldrb_imm, 1, 0, 6); E(mov_reg, 2, 4); E(adds_imm8, 2, 1); E(mov_reg, 3, 5); E(adds_imm8, 3, 1)
    E(cmp_reg, 1, 2); E(b_cond, "xs_l1", "ne"); E(strb_imm, 3, 0, 6); E(b, "xs_u")
    a.label("xs_l1"); E(cmp_reg, 1, 3); E(b_cond, "xs_u", "ne"); E(strb_imm, 2, 0, 6)
    a.label("xs_u"); E(bl, PK.BUF_UNLOCK)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_psxpad (the template view's slot 0: view, pad, velocity): pads 9-24 with Clear = ask / save, with Duplicate = A, then B: exchange
    a.label("c_psxpad")
    E(cmp_imm, 1, 8); bc("xp_f", "lo"); E(cmp_imm, 1, 23); bc("xp_f", "hi")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(mov_reg, 4, 0); E(cmp_imm, 4, 0xFF); bc("xp_fp", "eq")
    E(bl, "c_psst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("xp_fp", "eq")
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); bc("xp_fp", "eq")
    E(ldrb_imm, 0, 0, 3); E(lsls_imm, 0, 0, 4); E(subs_imm8, 5, 8); E(adds_reg, 5, 5, 0)        # r5 = the slot
    E(bl, "c_psaoff")
    held(6); E(movs_imm, 0, 3); E(ands_reg, 6, 0); E(cmp_imm, 6, 0); E(b_cond, "xp_h", "ne")
    E(strb_imm, 6, 7, 1)                                                              # a plain pad: nothing asked any more, mpatch loads
    E(raw, h(0x9800)); E(raw, h(0x9901)); E(raw, h(0x9A02)); E(bl, prev["xpad"])      # (ldr r0 / r1 / r2, [sp, #0 / 4 / 8])
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); E(b_cond, "xp_e", "eq")
    E(ldrb_imm, 0, 0, 6); E(mov_reg, 1, 5); E(adds_imm8, 1, 1); E(cmp_reg, 0, 1); E(b_cond, "xp_e", "ne")   # loaded (the last slot is this one)
    E(bl, L["c_sdtonic"]); E(mov_reg, 3, 0)
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 3); E(strb_imm, 0, 7, 6); E(strb_imm, 4, 7, 7)
    E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(movs_imm, 2, 100); E(bl, L["c_sdio"]); E(b, "xp_e")
    a.label("xp_h")
    E(cmp_imm, 6, 1); bc("xp_dup", "ne")
    E(movs_imm, 6, 0x80); E(orrs_reg, 6, 5); E(adds_imm8, 4, K_MIDI)                  # Clear: r6 = the question, r4 = its kind
    E(ldrb_imm, 0, 7, 1); E(cmp_reg, 0, 6); E(b_cond, "xp_ask", "ne")
    E(ldrb_imm, 0, 7, 2); E(cmp_reg, 0, 4); E(b_cond, "xp_ask", "ne")
    tick(0); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "xp_ask", "hs")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1)
    E(mov_reg, 0, 4); E(subs_imm8, 0, K_MIDI); E(mov_reg, 1, 5); E(bl, L["c_mpsave"]); E(b, "xp_e")
    a.label("xp_ask")
    E(strb_imm, 6, 7, 1); E(strb_imm, 4, 7, 2); tick(0); E(strh_imm, 0, 7, 4); E(b, "xp_e")
    a.label("xp_dup")
    E(bl, L["c_curpack"]); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 7, 2); E(cmp_imm, 0, K_DUP); E(b_cond, "xp_a", "ne")
    E(ldrb_imm, 0, 7, 3); E(cmp_reg, 0, 6); E(b_cond, "xp_a", "ne")
    E(ldrb_imm, 0, 7, 1); E(movs_imm, 1, 0x80); E(tst_reg, 0, 1); E(b_cond, "xp_a", "eq")
    E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(movs_imm, 1, 0); E(strb_imm, 1, 7, 1)
    E(cmp_reg, 0, 5); E(b_cond, "xp_e", "eq")                                         # A again: nothing
    E(mov_reg, 1, 5); E(bl, "c_psxswap"); E(b, "xp_e")
    a.label("xp_a")
    E(movs_imm, 0, 0x80); E(orrs_reg, 0, 5); E(strb_imm, 0, 7, 1); E(movs_imm, 0, K_DUP); E(strb_imm, 0, 7, 2); E(strb_imm, 6, 7, 3)
    a.label("xp_e"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("xp_fp"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.label("xp_f"); E(b_w, prev["xpad"])

    # ---- c_psxrel (the template view's slot 1: a pad let go): the audition ends
    a.label("c_psxrel")
    E(push_list, [0, 1, 2, 4], lr=True); E(bl, "c_psaoff"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["xrel"])

    # ---- c_psxleds (the template view's slot 7): the slot asked about blinks white, Duplicate's slot A bright peach
    a.label("c_psxleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["xleds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 0xFF); E(b_cond, "xl_q", "eq")                  # the slots on the screen: the empty ones violet
    E(movs_imm, 3, 8)
    a.label("xl_f")
    E(lsls_imm, 1, 3, 1); E(ldrh_reg, 0, 5, 1); E(cmp_imm, 0, 0); E(b_cond, "xl_fn", "ne"); E(movs_imm, 2, COL_EMPTY); E(strh_reg, 2, 5, 1)
    a.label("xl_fn"); E(adds_imm8, 3, 1); E(cmp_imm, 3, 24); E(b_cond, "xl_f", "lo")
    a.label("xl_q")
    E(bl, "c_psst"); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); bc("xl_x", "eq")
    E(ldrb_imm, 0, 7, 1); E(cmp_imm, 0, 0); bc("xl_x", "eq")
    E(ldrb_imm, 4, 7, 2); E(cmp_imm, 4, K_MIDI); bc("xl_x", "lo")
    E(cmp_imm, 4, K_DUP); E(b_cond, "xl_ask", "ne")
    held(0); E(movs_imm, 1, 2); E(tst_reg, 0, 1); E(b_cond, "xl_drop", "eq")          # Duplicate let go: A forgotten
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 0xFF); bc("xl_x", "eq")
    E(movs_imm, 6, COL_A); E(b, "xl_show")
    a.label("xl_ask")
    tick(0); E(ldrh_imm, 1, 7, 4); E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 16); E(lsrs_imm, 0, 0, 16); E(cmp_imm, 0, LIFE); E(b_cond, "xl_drop", "hs")
    E(bl, L["c_mpon"]); E(adds_imm8, 0, K_MIDI); E(cmp_reg, 0, 4); bc("xl_x", "ne")
    E(movs_imm, 6, COL_ASK); E(b, "xl_show")
    a.label("xl_drop"); E(movs_imm, 0, 0); E(strb_imm, 0, 7, 1); E(b, "xl_x")
    a.label("xl_show")
    E(bl, L["c_mpc"]); E(cmp_imm, 0, 0); E(b_cond, "xl_x", "eq")
    E(ldrb_imm, 0, 0, 3); E(ldrb_imm, 1, 7, 1); E(movs_imm, 2, 0x7F); E(ands_reg, 1, 2); E(lsrs_imm, 2, 1, 4); E(cmp_reg, 2, 0); E(b_cond, "xl_x", "ne")
    E(movs_imm, 2, 15); E(ands_reg, 1, 2); E(adds_imm8, 1, 8); E(lsls_imm, 1, 1, 1)
    imm32(0, PK.HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 7); E(movs_imm, 2, 1); E(ands_reg, 0, 2)
    E(cmp_imm, 0, 0); E(b_cond, "xl_w", "eq"); E(movs_imm, 6, 0)
    a.label("xl_w"); E(strh_reg, 6, 5, 1)
    a.label("xl_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_psbtn (the controller's button press: ctrl, id): Clear + MIDI 1 / 2 in a view of that track = its engine's values back to the initial ones
    a.label("c_psbtn")
    E(push_list, [0, 1, 2, 4], lr=True); E(bl, "c_psaoff"); E(raw, popw([0, 1, 2, 4], lr=True))     # any button ends the audition
    E(cmp_imm, 1, 2); E(b_cond, "sb_f", "lo"); E(cmp_imm, 1, 3); E(b_cond, "sb_f", "hi")
    E(push_list, [0, 1, 4, 5], lr=True); E(raw, h(0xB081))                           # (+ sub sp, #4)
    E(mov_reg, 4, 1); E(subs_imm8, 4, 2)                                              # r4 = the track
    held(5); E(movs_imm, 0, 3); E(ands_reg, 5, 0); E(cmp_imm, 5, 1); E(b_cond, "sb_fp", "ne")   # Clear held, Duplicate not
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); E(ldr_imm, 2, 0, 0x2C); E(cmp_reg, 1, 2); E(b_cond, "sb_fp", "ne")
    E(ldrb_w, 2, 0, V.S_CUR); E(movs_imm, 1, 9); E(mov_reg, 3, 4); E(adds_imm8, 3, 2); E(muls, 1, 3); E(subs_reg, 2, 2, 1)
    E(cmp_imm, 2, 1); E(b_cond, "sb_fp", "hi")                                        # the Preset view or the track view of that track
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "sb_fp", "ne") # (the CC editor: the track button is its own)
    E(mov_reg, 0, 4); E(bl, L["c_vreset"])
    E(raw, h(0xB001)); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("sb_fp"); E(raw, h(0xB001)); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("sb_f"); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the synth Preset view's slots 0 / 7 (in front of the macro editor's)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    L = dict(c_gst=lab("sc14", "c_gst"), c_srcv=lab("packio", "c_srcv"), c_curpack=lab("packio", "c_curpack"))
    L.update({n: lab("mpatch", n) for n in ("c_mpsz", "c_mpr", "c_mpw", "c_mpon", "c_mpc", "c_mpsave")})
    L.update(c_edact=lab("vcf20", "c_edact"), c_vreset=lab("vcf20", "c_vreset"), c_sdio=lab("vcf20", "c_sdio"), c_sdtonic=lab("vcf20", "c_sdtonic"))
    prev = dict(pad=u(SP_VT) & ~1, leds=u(SP_VT + 28) & ~1, xpad=u(TMPL_VT) & ~1, xrel=u(TMPL_VT + 4) & ~1, xleds=u(TMPL_VT + 28) & ~1, btn=MP.bw_target(img, BTN_ENTRY, BASE))
    assert prev["btn"] == lab("macroed", "c_mcbtn")
    assert prev["pad"] == lab("macroed", "c_mcpad") and prev["leds"] == lab("macroed", "c_mcleds")
    assert prev["xpad"] == lab("mpatch", "c_mppad") and prev["xleds"] == lab("mpatch", "c_mpleds")
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SP_VT - BASE, labels["c_pspad"] | 1)
    struct.pack_into("<I", img, SP_VT + 28 - BASE, labels["c_psleds"] | 1)
    struct.pack_into("<I", img, TMPL_VT - BASE, labels["c_psxpad"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 28 - BASE, labels["c_psxleds"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 4 - BASE, labels["c_psxrel"] | 1)
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_psbtn"])
    return labels, code, prev
