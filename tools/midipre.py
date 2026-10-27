"""SC48 / Beta 3.37 (the user, 2026-10-27: «añade un acceso a preset view de sintes en doble pulsación en pad MIDI» · «con el pad 27 en gris
cuando off» · «doble pulsación abre la misma vista que preset. Esta vista es única y su pad 27 desactivado se ve gris»): the MIDI tracks' Preset
view (where the own synth lives) one gesture away.

  * the head of the button press (0x08033320: ctrl, id): MIDI 1 / MIDI 2 (ids 2 / 3) pressed twice within DOUBLE_MS = the second press goes to the
    stock as always, then a press and a release of Preset (id 8) through the controller (the whole chain: what the Preset button does); not with
    Shift, Clear or Duplicate held, not in the Setup view, not with the track's CC editor open (its track button saves there); any other button
    forgets the first press;
  * the head of slot 7 of the template view (the MIDI Preset view): with the track's engine off (no CC editor, no step-drummer view on the screen)
    an unlit pad 27 = dim white 0x02 (the "off" colour of modesel's engine row).
RAM: modmx.MXR + 0x1AA0 (12 B, signed "MPV1": + 4 the last id, + 8 its time).  In the hole (no card).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, str_imm, strb_imm, strh_imm, subs_imm8, subs_reg, tst_reg)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import pgmch as PG  # noqa: E402
import vcf21 as V  # noqa: E402

RAM = MX.MXR + 0x1AA0                   # + 0 "MPV1", + 4 the last id (0xFF none), + 8 its time
RSIG = 0x3156504D
IDS = (2, 3)                            # MIDI 1 / MIDI 2
PRESET = 8
DOUBLE_MS = 400
PAD = 26                                # pad 27
COL_OFF = 0x02
PARAM_GET = 0x0803542C


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)

    # ---- c_mqram() -> r0 = our RAM (set up the first time); clobbers r1, r2
    a.label("c_mqram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "mr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0xFF); E(str_imm, 1, 0, 4); E(movs_imm, 1, 0); E(str_imm, 1, 0, 8)
    a.label("mr_x"); E(raw, h(0x4770))

    # ---- c_mqbtn (the button press: ctrl, id): MIDI 1 / 2 twice = their Preset view
    a.label("c_mqbtn")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_mqram"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, IDS[0]); E(b_cond, "mb_no", "lo"); E(cmp_imm, 5, IDS[1]); E(b_cond, "mb_no", "hi")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "mb_no", "ne")      # Shift
    E(ldr_imm, 0, 4, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "mb_no", "eq")
    E(ldr_imm, 0, 4, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(tst_reg, 0, 1); E(b_cond, "mb_no", "ne")                                                  # Clear / Duplicate
    E(mov_reg, 0, 5); E(subs_imm8, 0, IDS[0]); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "mb_no", "ne")    # its CC editor
    E(ldr_imm, 0, 6, 4); E(cmp_reg, 0, 5); E(b_cond, "mb_first", "ne")
    now(0); E(ldr_imm, 1, 6, 8); E(subs_reg, 0, 0, 1); E(movw, 1, DOUBLE_MS); E(cmp_reg, 0, 1); E(b_cond, "mb_first", "hi")
    E(movs_imm, 0, 0xFF); E(str_imm, 0, 6, 4)                                                                      # the second press
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, prev["btn"])
    E(mov_reg, 0, 4); E(movs_imm, 1, PRESET); E(bl, SV.BTN)
    E(mov_reg, 0, 4); E(movs_imm, 1, PRESET); E(bl, SV.BTN_REL)
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("mb_first"); E(str_imm, 5, 6, 4); now(0); E(str_imm, 0, 6, 8); E(b, "mb_p")
    a.label("mb_no"); E(movs_imm, 0, 0xFF); E(str_imm, 0, 6, 4)
    a.label("mb_p"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])

    # ---- c_mqled (slot 7 of the template view: view) -> r0 = the LED buffer: pad 27 dim white with the engine off
    a.label("c_mqled")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "ml_x", "hi"); E(mov_reg, 6, 0)            # r6 = the track
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "ne")
    E(mov_reg, 0, 6); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "ml_x", "ne")
    E(bl, L["c_sdscr"]); E(cmp_reg, 0, 6); E(b_cond, "ml_x", "eq")
    E(raw, h(0x8800 | (PAD * 2 // 2) << 6 | 5 << 3 | 0))                                                         # ldrh r0, [r5, #2 * PAD]
    E(cmp_imm, 0, 0); E(b_cond, "ml_x", "ne")
    E(movs_imm, 0, COL_OFF); E(strh_imm, 0, 5, 2 * PAD)
    a.label("ml_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the button press, the head of the template view's slot 7."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_edact", "c_sdscr")}
    L["c_mpon"] = lab("mpatch", "c_mpon")
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), leds=u(MP.TMPL_VT + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = bw_enc(SV.BTN, labels["c_mqbtn"])
    struct.pack_into("<I", img, MP.TMPL_VT + 28 - BASE, labels["c_mqled"] | 1)
    assert RAM + 12 <= MX.MXR + 0x1B00
    return labels, code, prev
