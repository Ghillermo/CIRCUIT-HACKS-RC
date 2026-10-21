"""SC45.9 (a fix to p4dest; the user, 2026-10-21: «en MIDI1/2 la vista de destinos de Knobs seleccionados no se muestra en los pads, como lo hace mod
Matrix»): while Shift + a knob of page 4 picks its destination, pads 9-24 show where that destination lives, as modmx's overlay does.

modmx (a source knob turning): pads 9-24 of the MIDI Preset view, OVL_MS after the last event = the destination's page pad bright, pads 9-16 / 17-24
= that page's K1..K8 / Shift + K1..K8 (dim the ones with a parameter, bright the destination); presses on pads 9-24 swallowed meanwhile (else they
load patches).  p4dest (Shift + K on page 4 = the lane's destination code, in vcf21's row [c_vrow(t) + k]) drew nothing there.
  * a head of the macro handlers' slot 4 (in front of p4dest's c_p4knob): Shift on page 4 (p4dest's c_p4pg) = this knob and the time noted;
  * heads of the MIDI Preset view's slots 0 / 7 (mpatch.TMPL_VT, in front of modmx's): while it is on (the knob's track on the screen, page 4 still
    the knobs', under OVL_MS), pads 9-24 swallowed / the overlay of the knob's destination (modmx's tables t_dmap, t_rows, t_pdim, t_pbri).
RAM: modmx.MXR + 0x17A (the knob, t << 4 | k), + 0x17B (a marker), + 0x17C (the time).  In the hole.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg, lsls_imm,  # noqa: E402
                   lsrs_imm, mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_reg, subs_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402

OVR = MX.MXR + 0x17A                  # + 0 the knob (t << 4 | k), + 1 the marker, + 2 the time (u32, at MXR + 0x17C)
MARK = 0xA5
TIME = MX.MXR + 0x17C               # the time (u32)
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def bc(target, cond):
        zc[0] += 1; n = f"_o{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_poknob (slot 4 of the macro handlers: obj, knob, delta): Shift on page 4 = noted, then p4dest's
    a.label("c_poknob")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("ok_prev", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("ok_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_p4pg"]); E(cmp_imm, 0, 0); bc("ok_prev", "eq")
    E(ldr_sp, 1, 4); E(movs_imm, 0, 7); E(ands_reg, 1, 0); E(lsls_imm, 0, 4, 4); E(orrs_reg, 0, 1)
    imm32(2, OVR); E(strb_imm, 0, 2, 0); E(movs_imm, 0, MARK); E(strb_imm, 0, 2, 1); now(0); imm32(2, TIME); E(str_imm, 0, 2, 0)
    a.label("ok_prev"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["knob"])

    # ---- c_poon() -> r0 = the knob (k) whose overlay is shown on the Preset view on the screen, or 0xFF; clobbers r1-r3
    a.label("c_poon")
    E(push_list, [4, 5], lr=True)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "on_0", "hi"); E(mov_reg, 4, 0)
    imm32(5, OVR); E(ldrb_imm, 0, 5, 1); E(cmp_imm, 0, MARK); E(b_cond, "on_0", "ne")
    E(ldrb_imm, 0, 5, 0); E(lsrs_imm, 0, 0, 4); E(cmp_reg, 0, 4); E(b_cond, "on_0", "ne")
    imm32(1, TIME); E(ldr_imm, 1, 1, 0); now(2); E(subs_reg, 2, 2, 1); imm32(1, MX.OVL_MS); E(cmp_reg, 2, 1); E(b_cond, "on_0", "hs")
    E(mov_reg, 0, 4); E(bl, L["c_p4pg"]); E(cmp_imm, 0, 0); E(b_cond, "on_0", "eq")
    E(ldrb_imm, 0, 5, 0); E(movs_imm, 1, 7); E(ands_reg, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("on_0"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5], pc=True)

    # ---- c_popad (the MIDI Preset view's slot 0: view, pad, velocity): pads 9-24 swallowed under the overlay
    a.label("c_popad")
    E(push_list, [0, 1, 2], lr=True)
    E(cmp_imm, 1, 8); bc("op_prev", "lo"); E(cmp_imm, 1, 23); bc("op_prev", "hi")
    E(bl, "c_poon"); E(cmp_imm, 0, 0xFF); bc("op_prev", "eq")
    E(pop_list, [0, 1, 2], pc=True)
    a.label("op_prev"); E(raw, popw([0, 1, 2], lr=True)); E(b_w, prev["pad"])

    # ---- c_poleds (the MIDI Preset view's slot 7: view) -> r0 = the LED buffer: the overlay of the knob's destination on pads 9-24
    a.label("c_poleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_poon"); E(cmp_imm, 0, 0xFF); bc("ol_x", "eq"); E(mov_reg, 7, 0)
    E(bl, L["c_mpon"]); E(bl, L["c_vrow"]); E(ldrb_reg, 0, 0, 7)                   # r0 = the knob's destination code
    E(bl, L["c_p4idx"]); imm32(1, L["t_dmap"]); E(ldrb_reg, 4, 1, 0)                # r4 = page << 4 | index
    E(lsrs_imm, 0, 4, 4); E(lsls_imm, 0, 0, 4); imm32(6, L["t_rows"]); E(adds_reg, 6, 6, 0)   # r6 = the page's 16 codes
    E(movs_imm, 7, 0)
    a.label("ol_l")
    E(ldrb_reg, 0, 6, 7); E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "ol_put", "eq")
    E(lsrs_imm, 2, 4, 4); imm32(3, L["t_pdim"]); E(ldrb_reg, 1, 3, 2)
    E(movs_imm, 3, 15); E(ands_reg, 3, 4); E(cmp_reg, 3, 7); E(b_cond, "ol_put", "ne")
    imm32(3, L["t_pbri"]); E(ldrb_reg, 1, 3, 2)
    a.label("ol_put"); E(mov_reg, 0, 7); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 1, 5, 0)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 16); E(b_cond, "ol_l", "lo")
    E(lsrs_imm, 2, 4, 4); imm32(3, L["t_pbri"]); E(ldrb_reg, 1, 3, 2); E(lsls_imm, 0, 2, 1); E(strh_reg, 1, 5, 0)   # the destination's page pad
    a.label("ol_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of the macro handlers' slot 4 and of the MIDI Preset view's slots 0 / 7."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vtrack", "c_vrow")}
    L["c_shift"] = lab("sc15", "c_shift"); L["c_mpon"] = lab("mpatch", "c_mpon")
    for k in ("c_p4pg", "c_p4idx"): L[k] = lab("p4dest", k)
    for k in ("t_dmap", "t_rows", "t_pdim", "t_pbri"): L[k] = lab("modmx", k)
    KN, TP = V.AC64_VT, MP.TMPL_VT
    prev = dict(knob=u(KN + 16) & ~1, pad=u(TP) & ~1, leds=u(TP + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert OVR == MX.MXR + 0x17A and OVR + 6 <= MX.MXR + 0x180
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_poknob"] | 1)
    struct.pack_into("<I", img, TP - BASE, labels["c_popad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_poleds"] | 1)
    return labels, code, prev
