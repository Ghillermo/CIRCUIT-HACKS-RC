"""SC52.6 (the user, 2026-11-06: «Reordena la interfaz de la fila superior: Asignadas (automatizables y no auto), Osc1, osc2, filtrovca, modulación»;
chosen: «1 Asignadas, 2 OSC1, 3 OSC2, 4 Filtro/VCA, 5 Mod»): in the Preset view of MIDI 1 / 2 with the own synth on (no CC editor, no step-drummer
view), pad 1 and pad 4 of the page row change places: pad 1 = the assigned (sequenceable) knobs, Shift + pad 1 = the non-sequenceable ones, pad 4 =
the VCA / VCF page.  The outermost heads of the template view's slots 0 (press), 1 (release) and 7 (the LED buffer): a press / release of pad 1 / 4
goes on as the other one, and the buffer's two halfwords are exchanged; everything under them (the pages, Clear + page pad, a page held, Shift's
colours) is unchanged."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, ldrb_imm, ldrh_imm, mov_reg, movs_imm, pop_list, push_list, h, raw, strh_imm, ands_reg)  # noqa: E402
import mpatch as MP  # noqa: E402

A, B = 0, 3                                   # pad 1, pad 4


FMOV = False                                  # (use_fmov)


def use_fmov():
    """SC52.8 (found in emu_fm8.py on Beta 5.30): no exchange while an overlay of the FM page is shown (Shift + K1's algorithms take pads 1-32:
    pads 1 / 4 were exchanged there)."""
    global FMOV
    FMOV = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    # ---- c_rsok(r0 = the view) -> r0 = 1 when the page row is on the pads (the own synth on, no editor, no step-drummer view); clobbers r1-r3
    a.label("c_rsok")
    E(push_list, [4], lr=True)
    E(ldrb_imm, 4, 0, 0x10); E(movs_imm, 1, 1); E(ands_reg, 4, 1)
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")
    if FMOV: E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(bl, L["c_fmovk"]); E(cmp_imm, 0, 0); E(b_cond, "ok_0", "ne")      # (FMOV) an FM overlay shown
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("ok_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    def head(lab, prv):
        # ---- (view, pad, ...): pad 1 / 4 go on as the other one
        a.label(lab)
        E(cmp_imm, 1, A); E(b_cond, lab + "_m", "eq"); E(cmp_imm, 1, B); E(b_cond, lab + "_m", "eq"); E(b_w, prv)
        a.label(lab + "_m")
        E(push_list, [0, 1, 2, 3], lr=True); E(bl, "c_rsok"); E(cmp_imm, 0, 0); E(pop_list, [0, 1, 2, 3])
        E(raw, h(0xBC08) + h(0x469E))                                           # pop {r3}; mov lr, r3 (the caller's)
        E(b_cond, lab + "_g", "eq")
        E(movs_imm, 3, A + B); E(raw, h(0x1A59))                                # subs r1, r3, r1: 1 <-> 4
        a.label(lab + "_g"); E(b_w, prv)
    head("c_rspad", prev["pad"])
    head("c_rsrel", prev["rel"])

    # ---- c_rsleds (slot 7: view) -> r0 = the LED buffer, pads 1 / 4 exchanged
    a.label("c_rsleds")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, "c_rsok"); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    E(ldrh_imm, 0, 5, 2 * A); E(ldrh_imm, 1, 5, 2 * B); E(strh_imm, 1, 5, 2 * A); E(strh_imm, 0, 5, 2 * B)
    a.label("rl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_edact", "c_sdview")}
    if FMOV: L.update({k: lab("fmeng", k) for k in ("c_fmblk", "c_fmovk")})
    TP = MP.TMPL_VT
    prev = dict(pad=u(TP) & ~1, rel=u(TP + 4) & ~1, leds=u(TP + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, TP - BASE, labels["c_rspad"] | 1)
    struct.pack_into("<I", img, TP + 4 - BASE, labels["c_rsrel"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_rsleds"] | 1)
    return labels, code, prev
