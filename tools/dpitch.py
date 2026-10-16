"""SC43.5 (the user, 2026-10-17: «Keep k1 chromatic, make s+k6 continuous pitch. Stock saved pitch affects continuous pitch, not chromatic»): the
drum pitch in two parts.

The stock (read in the firmware): a drum's Pitch (stock parameter, 0..127, 64 = the sample as it is; saved, automated, its CC) is a LINEAR rate
change: word = (256 + 2 x trunc(1.5 x (P - 64))) << 8 (0.25 .. 1.73 x).  SC09 turned it into semitones (word = 0x10000 x 2^((P - 64) / 12)), SC12
multiplies by the chromatic view's cents (c_conv0..3 at the 4 drum DSP handlers' calls 0x080287FA, 0x08028896, 0x0802892A, 0x080289BE), SC08 / SC11
make the chromatic view's pads set P = 64 + bias + the note (and record it), SC11 sets the bias from P when the view opens.

Ours:
  * a chromatic value S per drum (0..127, 64 = none; the record's tail + 48: 0xD5, S of the four drums, a check byte; saved with the project; 64
    without the block);
  * the pitch word = the stock's linear word of P x 2^((S - 64) / 12) x the cents: the four calls go to c_dpc0..3, which runs SC12's c_conv(d) on S
    and multiplies by the linear factor of P;
  * K1 (no Shift) = S, one semitone a step (in the chromatic view also the keyboard's bias, as SC11's); Clear + K1 right = 64 (and the pitch
    envelope, its Shift layer, back to 0); Shift + K6 = the stock Pitch through the stock handler (continuous, as the original); Clear + K6 right =
    also P back to 64 (as a received CC);
  * the chromatic view's pads set S (live: the step is not recorded) and the bias starts from S when the view opens;
  * LEDs: K1 = |S - 64| x 2 in the drum's colour (dim at 64); with Shift K6 = |P - 64| x 2.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm, ldrb_w, ldrh_imm, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, strb_imm, strb_w, strh_imm, subs_imm8, subs_reg)
import build_sc12 as S12  # noqa: E402

SESSION_OBJ, TAIL, O_BLK, MAGIC = 0x2003D71C, 0x27024, 48, 0xD5
MH_VT = 0x0805AADC
DK_STOCK = 0x0804FCC4                                    # the stock drum knob handler (obj, knob, delta): knob 1 = Pitch
MARK_DIRTY, PARAM_GET, PARAM_SET, CTX = 0x0803BDCC, 0x0803542C, 0x08034D92, 0x200069E4
BIAS, FLAG = 0x52, 0x51
DP_OLD = bytes.fromhex("e06894f82410043903681b689847")  # SC11's c_dpad2 at dp_c2: ldr r0, [r4, #0xc]; ldrb.w r1, [r4, #0x24]; subs r1, #4; ...; blx r3
DRUM_COL = (0x45, 0x2D, 0x49, 0x4D)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)
    E(raw, bytes(DRUM_COL)); t_col = base

    # ---- c_dpblk() -> r0 = the block (the tail + 48), or 0; clobbers r1
    a.label("c_dpblk")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "pb_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    a.label("pb_x"); E(raw, RET)

    # ---- c_dpok(r0 = the block) -> r0 = 1 when it holds ours; clobbers r1-r3
    a.label("c_dpok")
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, MAGIC); E(b_cond, "po_n", "ne")
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 0, 1 + k); E(eors_reg, 1, 2)
    E(ldrb_imm, 2, 0, 5); E(cmp_reg, 1, 2); E(b_cond, "po_n", "ne")
    E(movs_imm, 0, 1); E(raw, RET)
    a.label("po_n"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_dpnow(r0 = drum) -> r0 = its S (64 without the block); clobbers r1-r3
    a.label("c_dpnow")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(bl, "c_dpblk"); E(mov_reg, 5, 0); E(cmp_imm, 0, 0); E(b_cond, "pn_d", "eq")
    E(bl, "c_dpok"); E(cmp_imm, 0, 0); E(b_cond, "pn_d", "eq")
    E(adds_reg, 0, 5, 4); E(ldrb_imm, 0, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("pn_d"); E(movs_imm, 0, 64); E(pop_list, [4, 5], pc=True)

    # ---- c_dpput(r0 = drum, r1 = S 0..127): the block made when missing (64s), the drum's pitch sent again; clobbers r0-r3
    a.label("c_dpput")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_dpblk"); E(mov_reg, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "pp_x", "eq")
    E(bl, "c_dpok"); E(cmp_imm, 0, 0); E(b_cond, "pp_ok", "ne")
    E(movs_imm, 0, MAGIC); E(strb_imm, 0, 6, 0); E(movs_imm, 0, 64)
    for k in range(4): E(strb_imm, 0, 6, 1 + k)
    a.label("pp_ok")
    E(adds_reg, 0, 6, 4); E(strb_imm, 5, 0, 1)
    E(movs_imm, 1, 0x5A)
    for k in range(4): E(ldrb_imm, 2, 6, 1 + k); E(eors_reg, 1, 2)
    E(strb_imm, 1, 6, 5)
    E(lsls_imm, 1, 4, 3); E(subs_reg, 1, 1, 4); E(adds_imm8, 1, 2); E(movs_imm, 0, 0x10); E(bl, MARK_DIRTY)   # (0x10, 7 d + 2): the drum's group again
    a.label("pp_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_dpc0..3 (the drum DSP handlers' bl c_conv(d): r0 = P) -> r0 = the word: c_conv(d) of S, x the linear factor of P
    for d in range(4):
        a.label(f"c_dpc{d}")
        E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(movs_imm, 0, d); E(b, "dc_t")
    a.label("dc_t")
    E(raw, h(0xB401))                                                                  # push {r0}: the drum
    E(bl, "c_dpnow"); E(raw, h(0xBC02))                                                # pop {r1}
    E(lsls_imm, 1, 1, 4); imm32(2, L["c_conv0"]); E(adds_reg, 1, 1, 2); E(adds_imm8, 1, 1)   # c_conv0 + 16 d (thumb)
    E(raw, h(0x4788))                                                                  # blx r1: SC12's word of S (cents too)
    E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(subs_imm8, 0, 64)                                              # d = P - 64; t = d + trunc(d / 2)
    E(mov_reg, 1, 0); E(cmp_imm, 1, 0); E(b_cond, "dc_p", "ge"); E(raw, h(0x4249)); E(lsrs_imm, 1, 1, 1); E(raw, h(0x4249)); E(b, "dc_q")   # negs r1
    a.label("dc_p"); E(lsrs_imm, 1, 1, 1)
    a.label("dc_q"); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, 128); E(lsls_imm, 0, 0, 1)    # 256 + 2 t
    E(muls, 0, 5); E(lsrs_imm, 0, 0, 8)
    imm32(1, 0x7FFFFF); E(cmp_reg, 0, 1); E(b_cond, "dc_x", "ls"); E(mov_reg, 0, 1)
    a.label("dc_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_dpdrum(r0 = a macro handler) -> r0 = its drum 0..3, or 0xFF (SC11's: (byte + 0x30) - 40) / 5); clobbers r1
    a.label("c_dpdrum")
    E(ldrb_w, 0, 0, 0x30); E(subs_imm8, 0, 40); E(movs_imm, 1, 0)
    a.label("dd_l"); E(cmp_imm, 0, 5); E(b_cond, "dd_e", "lo"); E(subs_imm8, 0, 5); E(adds_imm8, 1, 1); E(b, "dd_l")
    a.label("dd_e"); E(mov_reg, 0, 1); E(cmp_imm, 0, 3); E(b_cond, "dd_x", "ls"); E(movs_imm, 0, 0xFF)
    a.label("dd_x"); E(raw, RET)

    # ---- c_dpknob (the drum macro handlers' slot 4: handler, knob, delta): K1 = S, Shift + K6 = the stock Pitch, Clear + K6 = P back to 64 too
    a.label("c_dpknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, "c_dpdrum"); E(cmp_imm, 0, 3); E(b_cond, "dk_f", "hi"); E(mov_reg, 7, 0)       # r7 = the drum
    E(bl, L["c_shift"]); E(mov_reg, 4, 0)                                               # r4 = Shift
    E(cmp_imm, 5, 0); E(b_cond, "dk_6", "ne"); E(cmp_imm, 4, 0); E(b_cond, "dk_f", "ne")  # Shift + K1: the chain (pitch envelope / the cents)
    E(raw, h(0x9800)); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "dk_s", "eq")  # ldr r0, [sp]: Clear held?
    E(cmp_imm, 6, 0); E(b_cond, "dk_e", "le")
    E(mov_reg, 0, 7); E(movs_imm, 1, 64); E(bl, "c_dpput")
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(bl, L["c_dzero"])                            # its Shift layer (the pitch envelope)
    E(raw, h(0x9800)); E(movs_imm, 1, 0); E(movs_imm, 2, 1); E(bl, L["c_clr_set"])       # blue
    E(b, "dk_e")
    a.label("dk_s")                                                                     # S += delta, 0..127; in the chromatic view the bias too
    E(mov_reg, 0, 7); E(bl, "c_dpnow"); E(adds_reg, 1, 0, 6)
    E(cmp_imm, 1, 0); E(b_cond, "dk_l", "ge"); E(movs_imm, 1, 0)
    a.label("dk_l"); E(cmp_imm, 1, 127); E(b_cond, "dk_h", "le"); E(movs_imm, 1, 127)
    a.label("dk_h"); E(subs_reg, 6, 1, 0); E(mov_reg, 0, 7); E(bl, "c_dpput")            # r6 = the change applied
    E(mov_reg, 0, 7); E(bl, L["c_dview"]); E(cmp_imm, 0, 0); E(b_cond, "dk_e", "eq")
    E(ldrb_w, 1, 0, FLAG); E(lsls_imm, 1, 1, 31); E(b_cond, "dk_e", "eq")
    E(ldrb_w, 1, 0, BIAS); E(raw, sxtb(1, 1)); E(adds_reg, 1, 1, 6); E(strb_w, 1, 0, BIAS)
    E(b, "dk_e")
    a.label("dk_6")
    E(cmp_imm, 5, 5); E(b_cond, "dk_f", "ne")
    E(cmp_imm, 4, 0); E(b_cond, "dk_6c", "eq")
    E(raw, h(0x9800)); E(movs_imm, 1, 1); E(mov_reg, 2, 6); E(bl, DK_STOCK); E(b, "dk_e")    # Shift + K6: the stock Pitch
    a.label("dk_6c")                                                                    # K6 with Clear right: P back to 64 as well, then the chain
    E(raw, h(0x9800)); E(bl, L["c_clr_held"]); E(cmp_imm, 0, 0); E(b_cond, "dk_f", "eq"); E(cmp_imm, 6, 0); E(b_cond, "dk_f", "le")
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0); E(adds_imm8, 0, 4)
    E(movs_imm, 1, 0x10); E(lsls_imm, 2, 7, 3); E(subs_reg, 2, 2, 7); E(adds_imm8, 2, 2); E(movs_imm, 3, 64); E(bl, PARAM_SET)
    a.label("dk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])
    a.label("dk_e"); E(raw, h(0xB003)); E(pop_list, [4, 5, 6, 7], pc=True)                  # add sp, #12

    # ---- c_dppad(r0 = the chromatic drum view, r1 = the note's value): S (instead of SC11's Pitch); clobbers r0-r3
    a.label("c_dppad")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(movs_imm, 0, 0)
    a.label("dv_l")
    E(push_list, [0]); E(bl, L["c_dview"]); E(pop_list, [1]); E(cmp_reg, 0, 4); E(b_cond, "dv_y", "eq")
    E(adds_imm8, 1, 1); E(mov_reg, 0, 1); E(cmp_imm, 0, 4); E(b_cond, "dv_l", "lo"); E(pop_list, [4, 5], pc=True)
    a.label("dv_y"); E(mov_reg, 0, 1); E(mov_reg, 1, 5); E(bl, "c_dpput")
    E(pop_list, [4, 5], pc=True)

    # ---- c_dpled (the drum macro handlers' slot 7: handler -> the LED buffer): K1 = S; with Shift K6 = P (|v - 64| x 2, dim at 64)
    a.label("c_dpled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_dpdrum"); E(cmp_imm, 0, 3); E(b_cond, "dl_x", "hi"); E(mov_reg, 7, 0)
    imm32(1, t_col); E(adds_reg, 1, 1, 7); E(ldrb_imm, 6, 1, 0)                           # r6 = the drum's colour
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "dl_s", "ne")
    E(mov_reg, 0, 7); E(bl, "c_dpnow"); E(movs_imm, 1, 0); E(b, "dl_w")
    a.label("dl_s")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(movs_imm, 1, 10)   # P; position 5
    a.label("dl_w")
    E(subs_imm8, 0, 64); E(b_cond, "dl_p", "pl"); E(raw, h(0x4240))                        # negs r0, r0
    a.label("dl_p"); E(lsls_imm, 0, 0, 1); E(cmp_imm, 0, 127); E(b_cond, "dl_c", "ls"); E(movs_imm, 0, 127)
    a.label("dl_c"); E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 6); E(raw, h(0x5268))   # strh r0, [r5, r1]
    a.label("dl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the four conversion calls, slots 4 / 7 of the drum macro handlers, SC11's pad setter call and its bias start."""
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_conv0=lab("sc12", "c_conv0"), c_dview=lab("sc11", "c_dview"), c_shift=lab("sc15", "c_shift"),
             c_clr_held=lab("persist19", "c_clr_held"), c_clr_set=lab("persist19", "c_clr_set"), c_dzero=lab("persist19", "c_dzero"))
    for d in range(1, 4): assert lab("sc12", f"c_conv{d}") == L["c_conv0"] + 16 * d
    prev = dict(knob=u(MH_VT + 16) & ~1, leds=u(MH_VT + 28) & ~1)
    for d, c in enumerate(S12.CALLS):
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, lab("sc12", f"c_conv{d}")), hex(c)
    pad_at = lab("sc11", "dp_c2"); assert bytes(img[pad_at - BASE:pad_at - BASE + 14]) == DP_OLD, hex(pad_at)
    bias_at = lab("sc11", "c_shbtn2") + 0x38; assert bytes(img[bias_at - BASE:bias_at - BASE + 4]) == bl_enc(bias_at, lab("sc11", "c_pitchnow")), hex(bias_at)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for d, c in enumerate(S12.CALLS):
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels[f"c_dpc{d}"])
    struct.pack_into("<I", img, MH_VT + 16 - BASE, labels["c_dpknob"] | 1)
    struct.pack_into("<I", img, MH_VT + 28 - BASE, labels["c_dpled"] | 1)
    img[pad_at - BASE:pad_at - BASE + 14] = h(0x4620) + h(0x4611) + bl_enc(pad_at + 4, labels["c_dppad"]) + h(0xBF00) * 3   # mov r0, r4; mov r1, r2; bl
    img[bias_at - BASE:bias_at - BASE + 4] = bl_enc(bias_at, labels["c_dpnow"])
    return labels, code, prev
