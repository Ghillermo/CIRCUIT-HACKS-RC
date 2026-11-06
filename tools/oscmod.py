"""SC52.4 (the user, 2026-11-06: OSC 1's page «5: lfo FM / env FM, 6: lfo Ring / env Ring, 8: lfo mix / env mix»): the LFO / envelope depths to the
two oscillators' interactions (FM, RING, MIX) of the MIDI 1 / 2 own synth; the DSP side is vcf21_dsp.use_osc4 (OM_T + 48 t + 0..5).

  * OSC 1's page (vcf21's page 2: mode on, no CC editor, no step-drummer view, not the granular page): K8 = LFO -> MIX, K6 = LFO -> RING,
    K5 = LFO -> FM; with Shift the envelope's.  -64..63 (0 = none); Clear held + the knob = 0.  The knob LEDs: the track's colour, the distance
    from 0 (as vcf21's bipolar knobs).  vcf21.use_osc4 leaves those knobs without a code.
  * The DSP service tick (the head of its chain): one of the 12 depths a tick, written to core 0's X when it differs from the last written
    (0x080292F8 from the tick, as the stock's).
  * The patch (mpatch's save / load, around wtui's gather / apply): padding + 163..170 = 0xC4, the 6 depths, a check byte (0x5A + the 7 bytes);
    psave / xpatch move it (XLEN = 171); the project: wtui's block carries it (wtui.PJ_N = 21).  A patch without it (any older firmware) = no
    depths and its FM (code 33, 0..127 = none .. full, OSC 2 -> OSC 1) moved to the new knob: 64 + k, 508 k^2 <= 3969 v (the same amount on the
    curve 4 t^2, t = k / 63).
RAM OMR: + 0 "OMR1", + 4 the depths (track t at + 6 t: LFO -> MIX, env -> MIX, LFO / env -> RING, LFO / env -> FM), + 16 the last written,
+ 28 the cursor."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm, subs_imm8, orrs_reg)
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import build_sc14 as S14  # noqa: E402

OMR = 0x2004F480
SIG = 0x31524D4F                          # "OMR1"
REC_AT, REC_N, REC_SIG = 163, 8, 0xC4     # the padding's block
DSPW = 0x080292F8
RET = h(0x4770)
KN = ((7, 0), (5, 2), (4, 4))
LEFT = False                              # SC52.6: the left half in the lighter shade (persist19.use_leftcol), the centre dim             # knob -> its pair (MIX, RING, FM) in vcf21_dsp's OM_T order


def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)
def asrs_imm(rd, rm, imm): return h(0x1000 | (imm & 31) << 6 | rm << 3 | rd)
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_o{zc[0]}"
        E(b_cond, n, V.INV[cond]); E(b, target); a.label(n)

    # ---- c_omst() -> r0 = OMR (the first time: the signature, the depths 0, the last written unknown); clobbers r1-r3
    a.label("c_omst")
    imm32(0, OMR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(movs_imm, 2, 0x7F)
    for k in range(12): E(strb_imm, 1, 0, 4 + k); E(strb_imm, 2, 0, 16 + k)
    E(strb_imm, 1, 0, 28)
    a.label("st_x"); E(raw, RET)

    # ---- c_omdep(r0 = track) -> r0 = its 6 depths; clobbers r1-r3
    a.label("c_omdep")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_omst"); E(adds_imm8, 0, 4)
    E(movs_imm, 1, 6); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(pop_list, [4], pc=True)

    # ---- c_omok(r0 = track) -> r0 = 1 with OSC 1's page of the engine on the knobs; clobbers r1-r3
    a.label("c_omok")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_grpg"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, 1); E(b_cond, "ok_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ok_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_omsel(r0 = knob 0..7) -> r0 = its pair's index + Shift (0xFF: not one of ours); clobbers r1-r3
    a.label("c_omsel")
    E(push_list, [4], lr=True)
    for k, i in KN: E(movs_imm, 4, i); E(cmp_imm, 0, k); E(b_cond, "sl_f", "eq")
    E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)
    a.label("sl_f"); E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "sl_x", "eq"); E(adds_imm8, 4, 1)
    a.label("sl_x"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_omknob (slot 4 of the macro handlers: obj, knob, delta)
    a.label("c_omknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_omok"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 0, 4); E(movs_imm, 1, 7); E(raw, h(0x4008)); E(bl, "c_omsel"); E(cmp_imm, 0, 0xFF); bc("kn_prev", "eq")   # ands r0, r1
    E(mov_reg, 5, 0); E(mov_reg, 0, 6); E(bl, "c_omdep"); E(adds_reg, 7, 0, 5)                 # r7 = the depth's byte
    E(bl, L["c_mxclrh"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "kn_s", "ne")          # Clear held: 0
    E(raw, ldrsb_reg(1, 7, 1)); E(ldr_sp, 0, 8); E(adds_reg, 1, 1, 0); E(adds_imm8, 1, 64)
    E(cmp_imm, 1, 0); E(b_cond, "kn_lo", "ge"); E(movs_imm, 1, 0)
    a.label("kn_lo"); E(cmp_imm, 1, 127); E(b_cond, "kn_hi", "le"); E(movs_imm, 1, 127)
    a.label("kn_hi"); E(subs_imm8, 1, 64)
    a.label("kn_s"); E(strb_imm, 1, 7, 0)
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_omkleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: our three knobs on OSC 1's page
    a.label("c_omkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, "c_omok"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    for k, _i in KN:
        E(movs_imm, 0, k); E(bl, "c_omsel"); E(mov_reg, 4, 0)
        E(mov_reg, 0, 6); E(bl, "c_omdep"); E(raw, ldrsb_reg(0, 0, 4))
        if LEFT:                                                                    # (SC52.6) left: the mark 0x82 + |v|; the centre dim
            E(cmp_imm, 0, 0); E(b_cond, f"kl_p{k}", "ge"); E(raw, h(0x43C0)); E(adds_imm8, 0, 0x82); E(b, f"kl_q{k}")
            a.label(f"kl_p{k}"); E(lsls_imm, 0, 0, 1); E(cmp_imm, 0, 16); E(b_cond, f"kl_r{k}", "hs"); E(movs_imm, 0, 16)
            a.label(f"kl_r{k}"); E(adds_imm8, 0, 2)
            a.label(f"kl_q{k}"); E(lsls_imm, 0, 0, 8)
        else:
            E(cmp_imm, 0, 0); E(b_cond, f"kl_p{k}", "ge"); E(raw, h(0x43C0))                        # mvns r0, r0
            a.label(f"kl_p{k}"); E(lsls_imm, 0, 0, 1); E(adds_imm8, 0, 2); E(lsls_imm, 0, 0, 8)
        E(movs_imm, 1, V.COL_TRACK[0]); E(cmp_imm, 6, 0); E(b_cond, f"kl_c{k}", "eq"); E(movs_imm, 1, V.COL_TRACK[1])
        a.label(f"kl_c{k}"); E(orrs_reg, 0, 1); E(strh_imm, 0, 5, 2 * k)
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_omtick (the head of the DSP service chain): one depth a tick to core 0 when it changed
    a.label("c_omtick")
    E(raw, h(0xE92D) + h(0x5FFF))                                                   # push.w {r0-r12, lr}
    E(bl, "c_omst"); E(mov_reg, 4, 0)
    E(ldrb_imm, 5, 4, 28); E(mov_reg, 1, 5); E(adds_imm8, 1, 1)
    E(cmp_imm, 1, 12); E(b_cond, "tk_c", "lo"); E(movs_imm, 1, 0)
    a.label("tk_c"); E(strb_imm, 1, 4, 28)
    E(adds_reg, 6, 4, 5); E(ldrb_imm, 0, 6, 4); E(ldrb_imm, 1, 6, 16); E(cmp_reg, 0, 1); E(b_cond, "tk_x", "eq")
    E(strb_imm, 0, 6, 16)
    E(lsls_imm, 1, 0, 24); E(raw, asrs_imm(1, 1, 16))                               # the value << 8, signed
    imm32(2, VD.OM_T); E(adds_reg, 2, 2, 5); E(cmp_imm, 5, 6); E(b_cond, "tk_a", "lo"); E(adds_imm8, 2, V.VBS - 6)                  # track 1: + 48 - 6
    a.label("tk_a"); E(movs_imm, 0, 0); E(bl, DSPW)
    a.label("tk_x"); E(raw, popw(list(range(13)), lr=True)); E(b_w, prev["svc"])

    return a.assemble()


def arm_code_b(base, L, prev):
    """the patch's part (in a dspz gap): c_omsum, c_omgath, c_omappl"""
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_omsum(r0 = the block) -> r0 = 0x5A + bytes 0..6; clobbers r1-r3
    a.label("c_omsum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    a.label("su_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, REC_N - 1); E(b_cond, "su_l", "lo")
    E(lsls_imm, 0, 2, 24); E(lsrs_imm, 0, 0, 24); E(raw, RET)

    # ---- c_omgath(r0 = track) in c_mpsave: wtui's gather, then the block at padding + REC_AT
    a.label("c_omgath")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, L["c_omdep"]); E(mov_reg, 5, 0); imm32(6, PK.BUF + REC_AT)
    E(movs_imm, 0, REC_SIG); E(strb_imm, 0, 6, 0)
    for i in range(6): E(ldrb_imm, 0, 5, i); E(strb_imm, 0, 6, 1 + i)
    E(mov_reg, 0, 6); E(bl, "c_omsum"); E(strb_imm, 0, 6, REC_N - 1)
    E(pop_list, [4, 5, 6], pc=True)

    # ---- c_omappl(r0 = track) in c_mpload (r5 = the slot there): wtui's apply, then the block (none: no depths, FM moved to the new knob)
    a.label("c_omappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5); E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20); imm32(2, MP.OFF + REC_AT); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + REC_AT); E(movs_imm, 3, REC_N); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + REC_AT)
    E(cmp_imm, 0, 0); E(b_cond, "ap_n", "ne"); E(cmp_imm, 1, REC_N); E(b_cond, "ap_n", "ne")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, REC_SIG); E(b_cond, "ap_n", "ne")
    E(mov_reg, 0, 6); E(bl, "c_omsum"); E(ldrb_imm, 1, 6, REC_N - 1); E(cmp_reg, 0, 1); E(b_cond, "ap_n", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_omdep"])
    for i in range(6): E(ldrb_imm, 1, 6, 1 + i); E(strb_imm, 1, 0, i)
    E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ap_n")                                                                 # an older patch: no depths; FM v -> 64 + k
    E(mov_reg, 0, 4); E(bl, L["c_omdep"]); E(movs_imm, 1, 0)
    for i in range(6): E(strb_imm, 1, 0, i)
    E(mov_reg, 0, 4); E(movs_imm, 1, 33); E(bl, L["c_vvaddr"]); E(mov_reg, 6, 0)
    E(ldrb_imm, 1, 6, 0); E(movw, 2, 3969); E(muls, 1, 2)                           # r1 = 3969 v
    E(movs_imm, 0, 0)
    a.label("ap_k"); E(adds_imm8, 0, 1); E(mov_reg, 2, 0); E(muls, 2, 0); E(movw, 3, 508); E(muls, 2, 3)
    E(cmp_reg, 2, 1); E(b_cond, "ap_k", "ls")
    E(adds_imm8, 0, 63); E(strb_imm, 0, 6, 0)                                       # 64 + (k - 1)
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr; the heads of the macro handlers' slots 4 / 7, the DSP service chain, wtui's gather / apply sites in c_mpsave /
    c_mpload."""
    import ct_fw
    import modmx as MX
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vtrack", "c_von", "c_edact", "c_sdview", "c_grpg", "c_vpage", "c_vvaddr")}
    L.update(c_shift=lab("sc15", "c_shift"), c_mxclrh=lab("modmx", "c_mxclrh"), c_mpr=lab("mpatch", "c_mpr"))
    KV = V.AC64_VT
    prev = dict(knob=u(KV + 16) & ~1, kleds=u(KV + 28) & ~1, svc=MP.bw_target(img, S14.SVC_HOOK, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, KV + 16 - BASE, labels["c_omknob"] | 1)
    struct.pack_into("<I", img, KV + 28 - BASE, labels["c_omkleds"] | 1)
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_omtick"])
    return labels, code, prev


class Patch:
    """dspz.add's module for the patch's part (after install: c_omdep from the report)"""
    @staticmethod
    def install(img, report, base_addr):
        import ct_fw
        import modmx as MX
        BASE = ct_fw.APP_BASE
        lab = lambda m, k: int(report[m]["labels"][k], 16)
        L = dict(c_omdep=lab("oscmod", "c_omdep"), c_mpr=lab("mpatch", "c_mpr"), c_vvaddr=lab("vcf20", "c_vvaddr"))
        mpsave, mpload = lab("mpatch", "c_mpsave"), lab("mpatch", "c_mpload")
        gath, appl = lab("wtui", "c_wtgath"), lab("wtui", "c_wtappl")
        prev = dict(gath=gath, appl=appl)
        code, labels = arm_code_b(base_addr, L, prev)
        img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
        while len(img) % 4:
            img += bytes([0xFF])
        for site_of, orig, ours in ((mpsave, gath, "c_omgath"), (mpload, appl, "c_omappl")):
            s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
            assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
            img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
        return labels, code, prev
