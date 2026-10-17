"""SC43.8 (the user, 2026-10-17: «revisa el guardado de sintes propios y granular, hay parametros que no parecen cargarse al reiniciar, especialmente
los shift»): the own engine of MIDI 1 / 2 keeps everything over a power cycle.

The stock / vcf21: the engine's state is the unit's, in the 75 reserved bytes at the end of the 128-byte settings record (SETOBJ + 8 .. + 0x87),
which the stock writes in 0x0802D2AC with 0x0803C920(storage, item, 0, SETOBJ + 8, [sp] = 0x80) (the main loop waits for it).  Codes 1..26 live
there; the codes 27..34 (the OSC 2 page, the granular page's Shift + K1-K5 / K7, the oscillator page's Shift + K2 / K3) live in RAM (the Master FX
block + 180, 8 a track), and the toggles of pads 28 / 29 (two oscillators, the chain order) and the knob page are bits of the runtime RT block
(TAIL + O_RT, 8 a track: bit 7 of RT_VEL / RT_NOTE, bits 1-2 of RT_TAG).  At power-up vcf21's first tick (c_vtick, the Master FX block's byte 179
bit 3 clear) zeroes the RT block, its save timer (O_SAVED) and the editor's bytes (O_ED, O_ED + 1) and puts the defaults into codes 27..34: all
of that was lost at every power-up.

Ours (vcf21.use_v2save makes their changes ask for the save too):
  * the bl 0x0803C920 of the save -> c_eswr: the record is copied onto the stack and the copy written instead, with, in the bytes of the runtime
    state (zeroed at power-up anyway): TAIL + O_RT + 8 t + k = code 27 + k of track t; O_SAVED = the toggles (bits 0 / 1 two oscillators of
    MIDI 1 / 2, 2 / 3 their chain order, 4-5 / 6-7 their knob page); O_ED = 0xE7; O_ED + 1 = (the sum of those 17 bytes) ^ 0x5A;
  * a new head of the DSP service chain -> c_esboot: while vcf21 has not initialised (byte 179 bit 3 clear), those 19 bytes are kept on the stack;
    after the chain (vcf21's first tick) with the signature and the sum right, codes 27..34 and the bits come back (ACT marked to be sent again:
    the DSP gets the oscillators and the order; the sweep sends codes 27..34).  A record written by an older firmware fails the signature: the
    defaults, as before.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_sp, strb_imm, strb_reg, sub_sp_imm, add_sp_imm,
                   ands_reg, bics_reg, tst_reg)
import vcf21 as V  # noqa: E402
import build_sc14 as S14  # noqa: E402
import mpatch as MP  # noqa: E402

SAVE_FN, WRITE = 0x0802D2AC, 0x0803C920
SIG, SUMX = 0xE7, 0x5A
REC = V.SETOBJ + 8                                   # the record the stock writes (0x80 bytes)
T_IN_REC = V.TAIL - REC                              # 0x35
MOV_R6_SP = h(0x466E)


def ldrb_w_(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    O_RT, O_SV, O_ED, V2 = V.O_RT, V.O_SAVED, V.O_ED, V.V2_OFF
    assert O_RT + 16 <= O_SV and O_ED + 1 < 75 and O_ED != O_SV

    # ---- c_estog() -> r0 = the toggles byte from the live RT blocks; clobbers r1-r3
    a.label("c_estog")
    E(movs_imm, 0, 0); imm32(2, V.TAIL + O_RT)
    for t in (0, 1):
        E(ldrb_imm, 1, 2, 8 * t + V.RT_VEL); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, t); E(orrs_reg, 0, 1)
        E(ldrb_imm, 1, 2, 8 * t + V.RT_NOTE); E(lsrs_imm, 1, 1, 7); E(lsls_imm, 1, 1, 2 + t); E(orrs_reg, 0, 1)
        E(ldrb_imm, 1, 2, 8 * t + V.RT_TAG); E(movs_imm, 3, 6); E(ands_reg, 1, 3); E(lsls_imm, 1, 1, 3 + 2 * t); E(orrs_reg, 0, 1)   # bits 1-2 -> 4-5 / 6-7
    E(raw, h(0x4770))

    # ---- c_eswr (the save's bl 0x0803C920: storage, item, 0, buffer, [sp] size): the record with our bytes
    a.label("c_eswr")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 140)                         # sp + 0 the size argument, + 4 the copy (128), + 132 r0, + 136 r1
    E(ldr_sp, 4, 160)                                                               # the caller's [sp]: the size
    imm32(5, REC); E(cmp_reg, 3, 5); E(b_cond, "ew_d", "ne"); E(cmp_imm, 4, 0x80); E(b_cond, "ew_d", "ne")
    E(str_sp, 0, 132); E(str_sp, 1, 136)
    E(raw, h(0xA901)); E(movs_imm, 6, 0)                                            # add r1, sp, #4
    a.label("ew_c"); E(raw, h(0x599F)); E(raw, h(0x518F)); E(adds_imm8, 6, 4); E(cmp_imm, 6, 0x80); E(b_cond, "ew_c", "lo")   # ldr r7, [r3, r6]; str r7, [r1, r6]
    E(mov_reg, 5, 1); E(adds_imm8, 5, T_IN_REC)                                     # r5 = the copy's tail
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ew_w", "eq")
    imm32(1, V2); E(adds_reg, 4, 0, 1)                                              # r4 = codes 27..34 of track 0 (track 1 = + 8)
    E(movs_imm, 6, 0); E(movs_imm, 7, 0)                                            # r6 = the sum, r7 = k
    E(mov_reg, 2, 5); E(adds_imm8, 2, O_RT)
    a.label("ew_v"); E(ldrb_reg, 0, 4, 7); E(strb_reg, 0, 2, 7); E(adds_reg, 6, 6, 0); E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "ew_v", "lo")
    E(bl, "c_estog"); E(raw, strb_w_(0, 5, O_SV)); E(adds_reg, 6, 6, 0)
    E(movs_imm, 0, SIG); E(raw, strb_w_(0, 5, O_ED))
    E(movs_imm, 0, SUMX); E(eors_reg, 0, 6); E(raw, strb_w_(0, 5, O_ED + 1))
    a.label("ew_w")
    E(ldr_sp, 0, 132); E(ldr_sp, 1, 136); E(movs_imm, 2, 0); E(raw, h(0xAB01))        # add r3, sp, #4
    E(movs_imm, 4, 0x80); E(str_sp, 4, 0); E(bl, WRITE)
    E(add_sp_imm, 140); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ew_d")                                                                 # not the settings record: as the stock
    E(str_sp, 4, 0); E(bl, WRITE); E(add_sp_imm, 140); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_esboot (the head of the DSP service chain): before vcf21's first tick, our bytes kept; after it, back
    a.label("c_esboot")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True); E(sub_sp_imm, 28)              # sp + 0..18 our bytes, + 20 the chain's r0; sp + 28.. r0-r3 at entry
    E(bl, L["c_gfst"]); E(mov_reg, 4, 0); E(movs_imm, 7, 0); E(cmp_imm, 4, 0); E(b_cond, "eb_go", "eq")
    E(raw, ldrb_w_(0, 4, V.FLAGS_BYTE)); E(movs_imm, 1, V.B_BOOT); E(tst_reg, 0, 1); E(b_cond, "eb_go", "ne")
    E(movs_imm, 7, 1); E(raw, MOV_R6_SP); imm32(2, V.TAIL + O_RT); E(movs_imm, 3, 0)
    a.label("eb_k"); E(ldrb_reg, 0, 2, 3); E(strb_reg, 0, 6, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "eb_k", "lo")
    imm32(2, V.TAIL)
    for i, off in enumerate((O_SV, O_ED, O_ED + 1)):
        E(raw, ldrb_w_(0, 2, off)); E(strb_imm, 0, 6, 16 + i)
    a.label("eb_go")
    E(ldr_sp, 0, 28); E(ldr_sp, 1, 32); E(ldr_sp, 2, 36); E(ldr_sp, 3, 40)
    E(bl, prev["svc"]); E(str_sp, 0, 20)
    E(cmp_imm, 7, 0); E(b_cond, "eb_x", "eq")
    E(raw, ldrb_w_(0, 4, V.FLAGS_BYTE)); E(movs_imm, 1, V.B_BOOT); E(tst_reg, 0, 1); E(b_cond, "eb_x", "eq")   # vcf21 did not initialise
    E(raw, MOV_R6_SP)
    E(ldrb_imm, 0, 6, 17); E(cmp_imm, 0, SIG); E(b_cond, "eb_x", "ne")
    E(movs_imm, 3, 0); E(movs_imm, 5, 0)
    a.label("eb_s"); E(ldrb_reg, 0, 6, 3); E(adds_reg, 5, 5, 0); E(adds_imm8, 3, 1); E(cmp_imm, 3, 17); E(b_cond, "eb_s", "lo")
    E(movs_imm, 0, SUMX); E(eors_reg, 0, 5); E(movs_imm, 1, 0xFF); E(ands_reg, 0, 1); E(ldrb_imm, 1, 6, 18); E(cmp_reg, 0, 1); E(b_cond, "eb_x", "ne")
    imm32(1, V2); E(adds_reg, 2, 4, 1); E(movs_imm, 3, 0)                           # codes 27..34 back
    a.label("eb_v"); E(ldrb_reg, 0, 6, 3); E(strb_reg, 0, 2, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, 16); E(b_cond, "eb_v", "lo")
    E(ldrb_imm, 5, 6, 16); imm32(2, V.TAIL + O_RT)                                  # r5 = the toggles
    for t in (0, 1):
        for fld, bit in ((V.RT_VEL, t), (V.RT_NOTE, 2 + t)):
            E(ldrb_imm, 1, 2, 8 * t + fld); E(lsls_imm, 0, 5, 31 - bit); E(lsrs_imm, 0, 0, 31); E(lsls_imm, 0, 0, 7); E(orrs_reg, 1, 0); E(strb_imm, 1, 2, 8 * t + fld)
        E(ldrb_imm, 1, 2, 8 * t + V.RT_TAG); E(movs_imm, 0, 6); E(bics_reg, 1, 0)
        E(lsls_imm, 0, 5, 26 - 2 * t); E(lsrs_imm, 0, 0, 30); E(lsls_imm, 0, 0, 1); E(orrs_reg, 1, 0); E(strb_imm, 1, 2, 8 * t + V.RT_TAG)
        E(ldrb_imm, 1, 2, 8 * t + V.RT_AUX); E(movs_imm, 0, 1); E(orrs_reg, 1, 0); E(strb_imm, 1, 2, 8 * t + V.RT_AUX)   # ACT again
    a.label("eb_x")
    E(ldr_sp, 0, 20); E(add_sp_imm, 44); E(pop_list, [4, 5, 6, 7], pc=True)        # (28 + the four entry registers)
    return a.assemble()


def write_site(img, base):
    """the bl 0x0803C920 inside the stock save"""
    from thumb import bl as bl_enc
    for off in range(0, 0x60, 2):
        a_ = SAVE_FN + off
        if bytes(img[a_ - base:a_ - base + 4]) == bl_enc(a_, WRITE):
            return a_
    raise AssertionError("no bl 0x0803C920 in the save")


def install(img, report, base_addr):
    """Append the code; the save's write call, the head of the DSP service chain."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    L = dict(c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16))
    site = write_site(img, BASE)
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), site=site)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_eswr"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_esboot"])
    return labels, code, prev
