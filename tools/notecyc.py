"""SC48 / Beta 3.37 (the user, 2026-10-27: «otro cambio: cuando el step sequencer está activo, note togglea entre notas, notas expandidas y step
seq»): with the step-drummer on in MIDI 1 / 2 (vcf21's c_sden: bit 0 of its nibble and the engine on; the synths' step-drummer has no on / off of
its own, so they keep the stock's Note), the Note button cycles Note -> expanded Note -> the step-drummer view -> Note.

The head of the button press (0x08033320: ctrl, id), Note (id 9) only, not with Shift / Clear / Duplicate, not in the Setup view; the controller's
subview [ctrl + 0x152] = 9 x track + view (1 = Note, 6 = expanded Note, 0 = Preset); vcf21's track: MIDI 1 / 2 = 0 / 1, Synth 1 / 2 = 2 / 3:
  * the step-drummer view on the screen (c_sdscr = the track): its open flag (F_SDOPEN) cleared, then the stock (from the Preset view: Note);
  * the expanded Note view: F_SDOPEN set, then Preset pressed and released (the template view shows the step-drummer), the press swallowed;
  * anything else (the Note view, a track without the step-drummer): the stock as always.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_w, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, subs_imm8, tst_reg)
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import pgmch as PG  # noqa: E402
import vcf21 as V  # noqa: E402

NOTE_BTN, PRESET = 9, 8
CUR = 0x152
SUB_NOTE, SUB_EXP = 1, 6
VT_OF = {2: 0, 3: 1}                       # controller track -> vcf21's track (MIDI 1 / 2)
PARAM_GET = 0x0803542C


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_ncbtn (the button press: ctrl, id)
    a.label("c_ncbtn")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(cmp_imm, 5, NOTE_BTN); E(b_cond, "nc_p", "ne")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "nc_p", "ne")      # Shift
    E(ldr_imm, 0, 4, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "nc_p", "eq")
    E(ldr_imm, 0, 4, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(tst_reg, 0, 1); E(b_cond, "nc_p", "ne")                                                   # Clear / Duplicate
    E(ldrb_w, 0, 4, CUR); E(movs_imm, 6, 0)                                                                        # r6 = the track, r0 = the view
    a.label("nc_d"); E(cmp_imm, 0, 9); E(b_cond, "nc_t", "lo"); E(subs_imm8, 0, 9); E(adds_imm8, 6, 1); E(b, "nc_d")
    a.label("nc_t"); E(mov_reg, 5, 0)                                                                              # r5 = the view
    E(mov_reg, 0, 6); E(bl, "c_ncvt"); E(cmp_imm, 0, 0xFF); E(b_cond, "nc_p", "eq")
    E(bl, L["c_sden"]); E(cmp_imm, 0, 0); E(b_cond, "nc_p", "eq")                                              # not on: the stock
    E(bl, L["c_sdscr"]); E(mov_reg, 2, 0); E(mov_reg, 0, 6); E(bl, "c_ncvt"); E(cmp_reg, 0, 2); E(b_cond, "nc_e", "ne")
    E(movs_imm, 0, V.F_SDOPEN); E(movs_imm, 1, 0); E(bl, L["c_sdfset"]); E(b, "nc_p")                            # on the screen: closed, then Note
    a.label("nc_e"); E(cmp_imm, 5, SUB_EXP); E(b_cond, "nc_p", "ne")
    E(movs_imm, 0, V.F_SDOPEN); E(movs_imm, 1, 1); E(bl, L["c_sdfset"])
    E(movs_imm, 5, PRESET)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN_REL)
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("nc_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])

    # ---- c_ncvt(r0 = the controller's track) -> r0 = vcf21's track (0xFF: not a note track with a step-drummer); clobbers r1
    a.label("c_ncvt")
    for ct, vt in VT_OF.items():
        E(movs_imm, 1, vt); E(cmp_imm, 0, ct); E(b_cond, "cv_x", "eq")
    E(movs_imm, 1, 0xFF)
    a.label("cv_x"); E(mov_reg, 0, 1); E(raw, h(0x4770))
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the button press."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_sden", "c_sdscr", "c_sdfset")}
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = bw_enc(SV.BTN, labels["c_ncbtn"])
    return labels, code, prev
