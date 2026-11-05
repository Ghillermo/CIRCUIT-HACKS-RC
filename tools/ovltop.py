"""SC52.2 / Beta 5.25 (the user, 2026-11-05: «en las vistas asignables (secuenciable y no secuenciable), la interfaz de selección tiene que ser la
misma que la de mod matrix (shift muestra los pads destino con sus colores y posiciones)»; on the device «No se muestra en el grid de pads el
destino», «creo que el problema es la vista del selector de motores y el nuevo row 2 apagado. Probablemente el orden de dibujado sea incorrecto»):
the destination overlays (the mod matrix's source knob, modmx; Shift + a knob of page 4 / the non-sequenceable page, p4ovl) were painted deep in the
MIDI Preset view's LED chain; the heads installed after them (modesel's engine row with pads 9-16 dark, jumpflip's flip modes with pads 9-16 dark,
fm8ui, wtui) painted over pads 9-24.  Now the outermost heads of the template view's slots 0 / 7:
  * slot 7: the chain, then the overlay again on pads 9-24 (modmx's tables: the destination's page pad bright, its 16 knobs dim with a parameter,
    the destination bright), the matrix's when shown, else p4ovl's;
  * slot 0: pads 9-24 swallowed while an overlay is shown (else the engine row / a flip would take them).
No RAM of its own.  dspz.add, the last head of the template view.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldrb_imm, ldrb_reg, ldrh_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, strh_reg, subs_imm8)
import mpatch as MP  # noqa: E402
import modmx as MX  # noqa: E402
import vcf21 as V  # noqa: E402

INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_t{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_otdst() -> r0 = page << 4 | index of the destination whose overlay is shown on the Preset view on the screen, or 0xFF; clobbers r1-r3
    a.label("c_otdst")
    E(push_list, [4, 5], lr=True)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("od_n", "hi"); E(mov_reg, 4, 0)
    E(bl, L["c_mxovl"]); E(cmp_imm, 0, 0); bc("od_p4", "eq")                              # the matrix's source knob
    E(bl, L["c_mxst"]); E(ldrb_imm, 5, 0, MX.G_OVK); E(movs_imm, 1, 7); E(ands_reg, 5, 1)
    E(mov_reg, 0, 4); E(bl, L["c_mxblk"]); E(lsls_imm, 1, 5, 1); E(ldrh_reg, 0, 0, 1); E(cmp_imm, 0, 0); bc("od_n", "eq")
    E(subs_imm8, 0, 1); E(lsrs_imm, 0, 0, 4); E(b, "od_m")
    a.label("od_p4")                                                                     # Shift + a knob of page 4 / the non-sequenceable page
    E(bl, L["c_poon"]); E(cmp_imm, 0, 0xFF); bc("od_n", "eq"); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_p4row"]); E(ldrb_reg, 0, 0, 5); E(bl, L["c_p4idx"])
    a.label("od_m"); imm32(1, L["t_dmap"]); E(ldrb_reg, 0, 1, 0); E(pop_list, [4, 5], pc=True)
    a.label("od_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4, 5], pc=True)

    # ---- c_otpad (the template view's slot 0, the outermost head: view, pad, velocity): pads 9-24 swallowed under an overlay
    a.label("c_otpad")
    E(push_list, [0, 1, 2], lr=True)
    E(cmp_imm, 1, 8); bc("op_p", "lo"); E(cmp_imm, 1, 23); bc("op_p", "hi")
    E(bl, "c_otdst"); E(cmp_imm, 0, 0xFF); bc("op_p", "eq")
    E(pop_list, [0, 1, 2], pc=True)
    a.label("op_p"); E(raw, popw([0, 1, 2], lr=True)); E(b_w, prev["pad"])

    # ---- c_otled (the template view's slot 7, the outermost head: view) -> r0 = the LED buffer: the chain, then the overlay on top
    a.label("c_otled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, "c_otdst"); E(cmp_imm, 0, 0xFF); bc("ol_x", "eq"); E(mov_reg, 4, 0)           # r4 = page << 4 | index
    E(lsrs_imm, 0, 4, 4); E(lsls_imm, 0, 0, 4); imm32(6, L["t_rows"]); E(raw, h(0x1836))   # adds r6, r6, r0: the page's 16 codes
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
    """dspz.add, after every other head of the template view (wtui): its slots 0 / 7."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_poon=lab("p4ovl", "c_poon"), c_p4row=lab("p4dest", "c_p4row"), c_p4idx=lab("p4dest", "c_p4idx"))
    for k in ("c_mxovl", "c_mxst", "c_mxblk", "t_dmap", "t_rows", "t_pdim", "t_pbri"): L[k] = lab("modmx", k)
    TP = MP.TMPL_VT
    prev = dict(pad=u(TP) & ~1, leds=u(TP + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, TP - BASE, labels["c_otpad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_otled"] | 1)
    return labels, code, prev
