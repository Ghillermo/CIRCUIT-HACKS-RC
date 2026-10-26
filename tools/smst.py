"""SC46.8 (the user, 2026-10-25: «Ruta para elegir el segundo sample» · «Shift+sample: selección silenciosa. Shift+el mismo sample ya seleccionado:
abre selección del segundo sample (se vuelve al primero con shift+sample2 ya seleccionado)» · «manteniendo la distancia en caso de que se cambie el
primero»): the right sample of the stereo sample mode (vcf21_dsp.use_smstereo2) in smpick's picker (MIDI 1 / 2 in the sample mode, the expanded Note
view, rows 3-4 = the samples).

  * the right = the track's sample + K (mod 64); K per track (default 1), written into the DSP (X:OSB0 + 48 t + SM_K) by a head of the DSP service
    chain when it changes and every 64 ms (the DSP's boot clears that area);
  * Shift + a sample = the track's sample without the sound (silent); Shift + the track's sample = the picker chooses the second sample; there a tap
    = the second (K = the distance) and it sounds (the note through the engine: the pair), Shift + a sample = the second without the sound, Shift +
    the second = back to the first; a step held + a sample = the flip, as before (a flip = the left; the right follows at K);
  * LEDs (over smpick's): choosing the first, the second violet (with the stereo width up, WAVE > 0); choosing the second, it blinks cyan and the
    first is violet; with Shift held the pad that switches (the one chosen) yellow (the Shift convention);
  * saved with the own-synth patches (and so with the project, projsyn): padding + 121 = 0xB5, K, 0x5A + 0xB5 + K (fmeng's gather / apply wrapped);
    a patch without it = K 1.  The picker's mode is RAM only (back to the first when the picker leaves the screen).
RAM: modmx.MXR + 0x600 (+0 "SMS1", +4 / +5 K, +6 the mode bits, +8 / +9 K sent + 1, +10 the tick count, +11 the Shift pad + 1 whose
release is swallowed: no note-off).  In the hole (it writes no card itself)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_imm8, subs_reg, eors_reg,
                   bics_reg)
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
import smpick as SP  # noqa: E402
import build_sc14 as S14  # noqa: E402

SMS = MX.MXR + 0x600
SIG = 0x31534D53                      # "SMS1"
O_K, O_MODE, O_SENT, O_CNT, O_SW = 4, 6, 8, 10, 11   # (+ 11: the pad + 1 whose release is swallowed)
POFS, PTAG = 121, 0xB5                # the padding: after fmeng's (100..120)
DSP_WRITE = 0x080292F8
CODE_SMP, CODE_WAVE = 25, 19
COL_R, COL_RSEL, COL_SH = 0x49, 0x4F, 0x2D   # the second violet; being chosen: cyan blinking (0x4F); with Shift: yellow
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_f{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    RET = h(0x4770)

    # ---- c_ssst() -> r0 = SMS, set up at the first use (K 1, 1); clobbers r1, r2
    a.label("c_ssst")
    imm32(0, SMS); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 8); E(movs_imm, 1, 1); E(strb_imm, 1, 0, O_K); E(strb_imm, 1, 0, O_K + 1)
    E(str_imm, 2, 0, 0)
    a.label("st_x"); E(raw, RET)

    # ---- c_ssk(r0 = track) -> r0 = its K; clobbers r1, r2
    a.label("c_ssk")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_ssst"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, O_K); E(pop_list, [4], pc=True)

    # ---- c_ssval(r0 = track, r1 = code) -> r0 = its stored value (the engine's byte); clobbers r1-r3
    a.label("c_ssval")
    E(push_list, [4], lr=True); E(bl, L["c_vvaddr"]); E(ldrb_imm, 0, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_sstick: the head of the DSP service chain: K of each track into the DSP when it changes and every 64 ms; the mode off without the picker
    a.label("c_sstick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6], lr=True))
    E(bl, "c_ssst"); E(mov_reg, 6, 0)
    E(ldrb_imm, 0, 6, O_CNT); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, O_CNT); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(mov_reg, 5, 0)   # r5 = 0: the refresh
    E(bl, L["c_spk"]); E(mov_reg, 4, 0)                                                   # the picker's track (0xFF none)
    for t in (0, 1):
        n = f"tk{t}"
        E(cmp_imm, 4, t); E(b_cond, n + "m", "eq")                                        # not on the screen: the first again
        E(ldrb_imm, 0, 6, O_MODE); E(movs_imm, 1, 1 << t); E(bics_reg, 0, 1); E(strb_imm, 0, 6, O_MODE)
        a.label(n + "m")
        E(ldrb_imm, 1, 6, O_K + t); E(adds_imm8, 1, 1); E(ldrb_imm, 0, 6, O_SENT + t); E(cmp_reg, 0, 1); E(b_cond, n + "w", "ne")
        E(cmp_imm, 5, 0); E(b_cond, n + "x", "ne")
        a.label(n + "w"); E(strb_imm, 1, 6, O_SENT + t); E(subs_imm8, 1, 1)
        E(lsls_imm, 1, 1, 8); imm32(2, VD.OSB0 + 48 * t + VD.SM_K); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
        a.label(n + "x")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, prev["svc"])

    # ---- c_sspad (the container's slot 0: obj, pad, velocity): the picker's samples with Shift, and the second sample's choice
    a.label("c_sspad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(cmp_imm, 1, 16); bc("sp_f", "lo")
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); bc("sp_f", "eq"); E(mov_reg, 7, 0)              # r7 = the track
    E(bl, L["c_spst"]); E(cmp_imm, 0, 0); bc("sp_f", "eq")
    E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0); bc("sp_f", "ne")                                # a step held: the flip (smpick)
    E(ldrb_imm, 4, 0, 0); E(movs_imm, 1, 3); E(ands_reg, 4, 1); E(lsls_imm, 4, 4, 4); E(ldr_sp, 1, 4); E(adds_reg, 4, 4, 1); E(subs_imm8, 4, 16)   # r4 = the sample
    E(mov_reg, 0, 7); E(movs_imm, 1, CODE_SMP); E(bl, "c_ssval"); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(mov_reg, 5, 0)   # r5 = the first
    E(bl, "c_ssst"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 7); E(bl, "c_ssbit"); E(ldrb_imm, 1, 6, O_MODE); E(ands_reg, 0, 1); E(mov_reg, 3, 0)          # r3 = the mode bit (0: the first)
    E(push_list, [3]); E(bl, L["c_shift"]); E(pop_list, [3]); E(cmp_imm, 0, 0); E(b_cond, "sp_ns", "eq")
    # with Shift: no note, its release swallowed
    E(ldr_sp, 0, 4); E(adds_imm8, 0, 1); E(strb_imm, 0, 6, O_SW)
    E(cmp_imm, 3, 0); E(b_cond, "sp_s2", "ne")
    E(cmp_reg, 4, 5); E(b_cond, "sp_sil", "ne")
    E(mov_reg, 0, 7); E(bl, "c_ssbit"); E(ldrb_imm, 1, 6, O_MODE); E(orrs_reg, 1, 0); E(strb_imm, 1, 6, O_MODE); E(b, "sp_x")   # Shift + the first: choose the second
    a.label("sp_sil")                                                                         # Shift + another: the first, silent
    E(mov_reg, 0, 7); E(movs_imm, 1, CODE_SMP); E(bl, L["c_vvaddr"]); E(strb_imm, 4, 0, 0)
    E(mov_reg, 0, 7); E(movs_imm, 1, CODE_SMP); E(bl, L["c_vmark"]); E(bl, L["c_vsave"]); E(b, "sp_x")
    a.label("sp_s2")                                                                          # choosing the second, with Shift
    E(mov_reg, 0, 7); E(bl, "c_ssk"); E(adds_reg, 0, 0, 5); E(movs_imm, 1, 63); E(ands_reg, 0, 1)
    E(cmp_reg, 4, 0); E(b_cond, "sp_k", "ne")
    E(mov_reg, 0, 7); E(bl, "c_ssbit"); E(ldrb_imm, 1, 6, O_MODE); E(bics_reg, 1, 0); E(strb_imm, 1, 6, O_MODE); E(b, "sp_x")   # Shift + the second: the first
    a.label("sp_k")                                                                           # the second, silent: K = s - first
    E(subs_reg, 0, 4, 5); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(adds_reg, 1, 6, 7); E(strb_imm, 0, 1, O_K); E(b, "sp_x")
    a.label("sp_ns")                                                                          # without Shift: choosing the first = smpick's
    E(cmp_imm, 3, 0); bc("sp_f", "eq")
    E(subs_reg, 0, 4, 5); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(adds_reg, 1, 6, 7); E(strb_imm, 0, 1, O_K)      # the second and it sounds (the pair)
    E(mov_reg, 0, 7); E(movs_imm, 1, 1); E(ldr_sp, 2, 8); E(bl, L["c_spnote"])
    a.label("sp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("sp_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_ssrel (the container's slot 1: obj, pad): the release of a pad pressed with Shift here: swallowed (no note-off)
    a.label("c_ssrel")
    E(push_list, [0, 1, 2, 4], lr=True); E(mov_reg, 4, 1)
    E(bl, "c_ssst"); E(ldrb_imm, 1, 0, O_SW); E(adds_imm8, 4, 1); E(cmp_reg, 1, 4); E(b_cond, "rl_p", "ne")
    E(movs_imm, 1, 0); E(strb_imm, 1, 0, O_SW); E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("rl_p"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["rel"])

    # ---- c_ssbit(r0 = track) -> r0 = its mode bit (1 << track)
    a.label("c_ssbit")
    E(movs_imm, 1, 1); E(cmp_imm, 0, 0); E(b_cond, "sb_x", "eq"); E(movs_imm, 1, 2)
    a.label("sb_x"); E(mov_reg, 0, 1); E(raw, RET)

    # ---- c_ssleds (the container's slot 7: obj -> the LED buffer): smpick's, then the first / the second on the page
    a.label("c_ssleds")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_spk"]); E(cmp_imm, 0, 0xFF); bc("le_x", "eq"); E(mov_reg, 7, 0)
    E(bl, L["c_spst"]); E(cmp_imm, 0, 0); bc("le_x", "eq"); E(ldrb_imm, 6, 0, 0); E(movs_imm, 1, 3); E(ands_reg, 6, 1)   # r6 = the page
    E(ldrb_imm, 0, 0, 1); E(cmp_imm, 0, 0); bc("le_x", "ne")                                # a step held: smpick's
    E(mov_reg, 0, 7); E(movs_imm, 1, CODE_SMP); E(bl, "c_ssval"); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(mov_reg, 4, 0)   # r4 = the first
    E(mov_reg, 0, 7); E(bl, "c_ssk"); E(adds_reg, 0, 0, 4); E(movs_imm, 1, 63); E(ands_reg, 0, 1); E(mov_reg, 3, 0)          # r3 = the second
    E(bl, "c_ssst"); E(ldrb_imm, 0, 0, O_MODE); E(push_list, [0]); E(mov_reg, 0, 7); E(bl, "c_ssbit"); E(pop_list, [1]); E(ands_reg, 0, 1)
    E(cmp_imm, 0, 0); bc("le_s2", "ne")
    # choosing the first: Shift = the first yellow; the second violet with the width up
    E(push_list, [3]); E(bl, L["c_shift"]); E(pop_list, [3]); E(cmp_imm, 0, 0); E(b_cond, "le_n1", "eq")
    E(mov_reg, 0, 4); E(movs_imm, 1, COL_SH); E(bl, "c_ssput")
    a.label("le_n1")
    E(cmp_reg, 3, 4); bc("le_x", "eq")
    E(push_list, [3]); E(mov_reg, 0, 7); E(movs_imm, 1, CODE_WAVE); E(bl, "c_ssval"); E(pop_list, [3]); E(cmp_imm, 0, 0); bc("le_x", "eq")
    E(mov_reg, 0, 3); E(movs_imm, 1, COL_R); E(bl, "c_ssput"); E(b, "le_x")
    a.label("le_s2")                                                                          # choosing the second: it blinks cyan (Shift: yellow), the first violet
    E(cmp_reg, 3, 4); E(b_cond, "le_s3", "eq"); E(mov_reg, 0, 4); E(movs_imm, 1, COL_R); E(bl, "c_ssput")
    a.label("le_s3")
    E(push_list, [3]); E(bl, L["c_shift"]); E(pop_list, [3]); E(movs_imm, 1, COL_RSEL); E(cmp_imm, 0, 0); E(b_cond, "le_s4", "eq"); E(movs_imm, 1, COL_SH)
    a.label("le_s4"); E(mov_reg, 0, 3); E(bl, "c_ssput")
    a.label("le_x"); E(mov_reg, 0, 5); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_ssput(r0 = sample, r1 = colour; r5 = the buffer, r6 = the page): the sample's pad when it is on the page; clobbers r0, r2
    a.label("c_ssput")
    E(lsrs_imm, 2, 0, 4); E(cmp_reg, 2, 6); E(b_cond, "pu_x", "ne")
    E(movs_imm, 2, 15); E(ands_reg, 0, 2); E(adds_imm8, 0, 16); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    a.label("pu_x"); E(raw, RET)

    # ---- c_ssgath(r0 = track) in c_mpsave: fmeng's gather, then K at padding + 121
    a.label("c_ssgath")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, "c_ssk"); imm32(1, PK.BUF + POFS)
    E(movs_imm, 2, PTAG); E(strb_imm, 2, 1, 0); E(strb_imm, 0, 1, 1); E(adds_imm8, 0, (0x5A + PTAG) & 0xFF); E(strb_imm, 0, 1, 2)
    E(pop_list, [4, 5], pc=True)

    # ---- c_ssappl(r0 = track) in c_mpload (r5 = the slot): fmeng's apply, then K from the padding (none: 1)
    a.label("c_ssappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, 3); E(bl, L["c_mpr"])
    E(movs_imm, 6, 1)                                                                           # r6 = K (1 without it)
    E(cmp_imm, 0, 0); E(b_cond, "ap_w", "ne"); E(cmp_imm, 1, 3); E(b_cond, "ap_w", "ne")
    imm32(2, PK.BUF + POFS); E(ldrb_imm, 0, 2, 0); E(cmp_imm, 0, PTAG); E(b_cond, "ap_w", "ne")
    E(ldrb_imm, 0, 2, 1); E(ldrb_imm, 1, 2, 2); E(adds_imm8, 0, (0x5A + PTAG) & 0xFF); E(movs_imm, 3, 0xFF); E(ands_reg, 0, 3)
    E(cmp_reg, 0, 1); E(b_cond, "ap_w", "ne"); E(ldrb_imm, 6, 2, 1); E(movs_imm, 0, 63); E(ands_reg, 6, 0)
    a.label("ap_w")
    E(bl, "c_ssst"); E(adds_reg, 0, 0, 4); E(strb_imm, 6, 0, O_K)
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads: the DSP service chain, the tracks' container's slots 0 / 1 / 7; fmeng's gather / apply calls in
    c_mpsave / c_mpload."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vvaddr", "c_vmark", "c_vsave")}
    L["c_shift"] = lab("sc15", "c_shift")
    for k in ("c_spk", "c_spst", "c_spnote"): L[k] = lab("smpick", k)
    for k in ("c_mpr", "c_mpload", "c_mpsave"): L[k] = lab("mpatch", k)
    for k in ("c_fmgath", "c_fmappl"): L[k] = lab("fmeng", k)
    CT = SP.CONT_VT
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), pad=u(CT) & ~1, rel=u(CT + 4) & ~1, leds=u(CT + 28) & ~1, gath=L["c_fmgath"], appl=L["c_fmappl"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for site_of, orig, ours in ((L["c_mpsave"], L["c_fmgath"], "c_ssgath"), (L["c_mpload"], L["c_fmappl"], "c_ssappl")):
        s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_sstick"])
    struct.pack_into("<I", img, CT - BASE, labels["c_sspad"] | 1)
    struct.pack_into("<I", img, CT + 4 - BASE, labels["c_ssrel"] | 1)
    struct.pack_into("<I", img, CT + 28 - BASE, labels["c_ssleds"] | 1)
    return labels, code, prev
