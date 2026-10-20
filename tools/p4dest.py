"""SC44.9 (the user, 2026-10-19: «permite reasignar los destinos de la vista de secuenciables (mismo layout que mod matrix)», «guardados por parche»;
with him: Shift + knob = the destination, the knob alone the value as before): the destinations of knob page 4 of the own engine of MIDI 1 / 2
(the sequenceable parameters: KNOB_CODES_D, the 8 automation lanes).

vcf21.use_p4dest(RAM): page 4's 8 codes (plain layer) come from RAM per track (vcf21.P4RAM + 8 t, LANE_TAB the first time), and so do the lanes'
codes: recording (c_vcc_rec) and playback (c_vapply) follow the row, Clear + a knob to the left clears the knob's lane (c_vlane).
Here, the heads of slots 4 / 7 of the macro handlers (in front of modmx's c_mxknob / c_mxkleds):
  * page 4 (vcf21's page 3: mode on, no CC editor, no step-drummer view), Shift + K1..K8 = the knob's destination: the matrix's list (modmx's
    dcode: every code of the knob pages, in page order, 33), a slow knob (DIV events a step; an accumulator for the knob touched last), clamped
    at both ends; Clear held, then Shift + knob = back to its default (LANE_TAB; Shift + Clear is the stock's / countin's metronome); a destination changed sends nothing (the values stay, the lane's
    automation now moves the new destination);
  * the knob LEDs with Shift on page 4: the colour of the destination's page (modmx's dcol: the page pads' colours), full brightness.
Saved with the own-synth patches: 12 bytes at padding + 88 (after modmx's matrix): "P4", version 1, the 8 codes, a check byte (0x5A + the 11
bytes); modmx's c_mxgath / c_mxappl calls in c_mpsave / c_mpload wrapped; a patch without them loads LANE_TAB.  psave.XLEN = 100 (the exchange and
the copy between packs carry them).  RAM: modmx.MXR + 0x160 (vcf21.P4RAM: 16 codes + signature) and + 0x178 (the accumulator, its knob)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, strb_reg, strh_reg, subs_imm8, subs_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402

RAM = MX.MXR + 0x160                  # vcf21.P4RAM: 8 codes per track, the signature at + 16
ST = MX.MXR + 0x178                   # + 0 the accumulator (s8), + 1 its knob (t << 4 | k, 0xFF none)
PAGE = 3                              # vcf21's page index of page 4 (KNOB_CODES_D)
DIV = 4                               # knob events per destination
POFS, PLEN = 88, 12                   # in the padding: after modmx's matrix (64..87)
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrsb_reg(rt, rn, rm): return h(0x5600 | rm << 6 | rn << 3 | rt)
def sdiv(rd, rn, rm): return h(0xFB90 | rn) + h(0xF0F0 | rd << 8 | rm)
def muls_(rd, rm): return h(0x4340 | rm << 3 | rd)


def arm_code(base, L, prev, nd):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    a.label("p4_lt"); E(raw, bytes(V.LANE_TAB))                                    # the defaults

    # ---- c_p4pg(r0 = track) -> r0 = 1 when page 4 of the track is the one the knobs move (mode on, no CC editor, no step-drummer view)
    a.label("c_p4pg")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "pg_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vpage"]); E(cmp_imm, 0, PAGE); E(b_cond, "pg_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("pg_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_p4idx(r0 = code) -> r0 = its index in the matrix's list (0 when it is not there); clobbers r1-r3
    a.label("c_p4idx")
    imm32(1, L["t_dcode"]); E(movs_imm, 2, 0)
    a.label("ix_l"); E(ldrb_reg, 3, 1, 2); E(cmp_reg, 3, 0); E(b_cond, "ix_f", "eq"); E(adds_imm8, 2, 1); E(cmp_imm, 2, nd); E(b_cond, "ix_l", "lo")
    E(movs_imm, 2, 0)
    a.label("ix_f"); E(mov_reg, 0, 2); E(raw, h(0x4770))

    # ---- c_p4knob (slot 4 of the macro handlers: obj, knob, delta): Shift on page 4 = the knob's destination, else the previous slot
    a.label("c_p4knob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kn_prev", "hi"); E(mov_reg, 6, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(mov_reg, 0, 6); E(bl, "c_p4pg"); E(cmp_imm, 0, 0); bc("kn_prev", "eq")
    E(ldr_sp, 5, 4); E(movs_imm, 0, 7); E(ands_reg, 5, 0)                          # r5 = knob 0..7
    E(mov_reg, 0, 6); E(bl, L["c_vrow"]); E(adds_reg, 4, 0, 5)                      # r4 = the knob's code in the row
    E(bl, L["c_mxclrh"]); E(cmp_imm, 0, 0); E(b_cond, "kn_ac", "eq")             # Clear held (the controller's: with Shift the handler never sees it)
    imm32(1, base); E(ldrb_reg, 0, 1, 5); E(strb_imm, 0, 4, 0); E(b, "kn_x")        # Clear: the default
    a.label("kn_ac")
    imm32(7, ST); E(lsls_imm, 1, 6, 4); E(orrs_reg, 1, 5); E(ldrb_imm, 2, 7, 1); E(cmp_reg, 2, 1); E(b_cond, "kn_sm", "eq")
    E(strb_imm, 1, 7, 1); E(movs_imm, 2, 0); E(strb_imm, 2, 7, 0)
    a.label("kn_sm")
    E(movs_imm, 2, 0); E(raw, ldrsb_reg(2, 7, 2)); E(ldr_sp, 3, 8); E(adds_reg, 2, 2, 3)
    E(movs_imm, 3, DIV); E(raw, sdiv(0, 2, 3)); E(raw, muls_(3, 0)); E(subs_reg, 2, 2, 3); E(strb_imm, 2, 7, 0)
    E(cmp_imm, 0, 0); E(b_cond, "kn_x", "eq"); E(mov_reg, 5, 0)                    # r5 = steps
    E(ldrb_imm, 0, 4, 0); E(bl, "c_p4idx"); E(adds_reg, 0, 0, 5)
    E(cmp_imm, 0, 0); E(b_cond, "kn_q1", "ge"); E(movs_imm, 0, 0)
    a.label("kn_q1"); E(cmp_imm, 0, nd - 1); E(b_cond, "kn_q2", "le"); E(movs_imm, 0, nd - 1)
    a.label("kn_q2"); imm32(1, L["t_dcode"]); E(ldrb_reg, 0, 1, 0); E(strb_imm, 0, 4, 0)
    a.label("kn_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("kn_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_p4kleds (slot 7 of the macro handlers: obj) -> r0 = the knob LED buffer: Shift on page 4 = the destinations' page colours
    a.label("c_p4kleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, "c_p4pg"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(mov_reg, 0, 6); E(bl, L["c_vrow"]); E(mov_reg, 4, 0); E(movs_imm, 6, 0)
    a.label("kl_l")
    E(ldrb_reg, 0, 4, 6); E(bl, "c_p4idx"); imm32(1, L["t_dcol"]); E(ldrb_reg, 1, 1, 0)
    E(movs_imm, 0, 129); E(lsls_imm, 0, 0, 8); E(orrs_reg, 0, 1); E(lsls_imm, 1, 6, 1); E(strh_reg, 0, 5, 1)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "kl_l", "lo")
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_p4sum(r0 = 12 bytes) -> r0 = 0x5A + bytes 0..10, a byte; clobbers r1-r3
    a.label("c_p4sum")
    E(movs_imm, 1, 0x5A); E(movs_imm, 2, 0)
    a.label("su_l"); E(ldrb_reg, 3, 0, 2); E(adds_reg, 1, 1, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, PLEN - 1); E(b_cond, "su_l", "lo")
    E(movs_imm, 0, 0xFF); E(ands_reg, 0, 1); E(raw, h(0x4770))

    # ---- c_p4gath(r0 = track) in c_mpsave: modmx's gather (mpatch's and the matrix), then the destinations at padding + 88
    a.label("c_p4gath")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(mov_reg, 5, 0); imm32(6, PK.BUF + POFS)
    E(movs_imm, 0, ord("P")); E(strb_imm, 0, 6, 0); E(movs_imm, 0, ord("4")); E(strb_imm, 0, 6, 1); E(movs_imm, 0, 1); E(strb_imm, 0, 6, 2)
    E(movs_imm, 7, 0)
    a.label("ga_l"); E(ldrb_reg, 0, 5, 7); E(adds_imm8, 7, 3); E(strb_reg, 0, 6, 7); E(subs_imm8, 7, 2); E(cmp_imm, 7, 8); E(b_cond, "ga_l", "lo")
    E(mov_reg, 0, 6); E(bl, "c_p4sum"); E(strb_imm, 0, 6, PLEN - 1)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_p4appl(r0 = track) in c_mpload (r5 = the slot there): modmx's apply, then the patch's destinations (none or not valid: the defaults)
    a.label("c_p4appl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, prev["appl"])
    E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(mov_reg, 5, 0)                          # r5 = the row
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)               # r0 = the bank, r1 = (slot & 7) x 512
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, PLEN); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + POFS)
    E(cmp_imm, 0, 0); E(b_cond, "ap_d", "ne"); E(cmp_imm, 1, PLEN); E(b_cond, "ap_d", "ne")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, ord("P")); E(b_cond, "ap_d", "ne"); E(ldrb_imm, 0, 6, 1); E(cmp_imm, 0, ord("4")); E(b_cond, "ap_d", "ne")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, 1); E(b_cond, "ap_d", "ne")
    E(mov_reg, 0, 6); E(bl, "c_p4sum"); E(ldrb_imm, 1, 6, PLEN - 1); E(cmp_reg, 0, 1); E(b_cond, "ap_d", "ne")
    E(adds_imm8, 6, 3); E(b, "ap_c")                                                  # r6 = the patch's 8 codes
    a.label("ap_d"); imm32(6, base)                                                   # r6 = the defaults
    a.label("ap_c"); E(movs_imm, 7, 0)
    a.label("ap_l")
    E(ldrb_reg, 0, 6, 7); E(push_list, [0]); E(bl, "c_p4idx"); imm32(1, L["t_dcode"]); E(ldrb_reg, 0, 1, 0); E(pop_list, [1])
    E(cmp_reg, 0, 1); E(b_cond, "ap_ok", "eq")
    imm32(1, base); E(ldrb_reg, 1, 1, 7)                                              # not one of the destinations: the default
    a.label("ap_ok"); E(strb_reg, 1, 5, 7)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "ap_l", "lo")
    E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the macro handlers' slots 4 / 7; modmx's gather / apply calls in c_mpsave / c_mpload."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vtrack", "c_von", "c_edact", "c_sdview", "c_vpage", "c_vrow")}
    L["c_shift"] = lab("sc15", "c_shift")
    for k in ("c_mpr", "c_mpload", "c_mpsave"): L[k] = lab("mpatch", k)
    for k in ("t_dcode", "t_dcol", "c_mxgath", "c_mxappl", "c_mxclrh"): L[k] = lab("modmx", k)
    nd = int(report["modmx"]["prev"]["pmax"], 16) // MX.ZONE
    KN = V.AC64_VT
    prev = dict(knob=u(KN + 16) & ~1, kleds=u(KN + 28) & ~1, gath=L["c_mxgath"], appl=L["c_mxappl"])
    code, labels = arm_code(base_addr, L, prev, nd)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000 or base_addr < 0x08018800          # in the hole: hole.add moves it back
    for site_of, orig, ours in ((L["c_mpsave"], L["c_mxgath"], "c_p4gath"), (L["c_mpload"], L["c_mxappl"], "c_p4appl")):
        s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_p4knob"] | 1)
    struct.pack_into("<I", img, KN + 28 - BASE, labels["c_p4kleds"] | 1)
    prev.update(nd=nd)
    return labels, code, prev
