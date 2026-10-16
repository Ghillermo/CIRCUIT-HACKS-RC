"""SC42.5 (the user, 2026-10-16: «sidechain parameter knobs on drums don't show the right color or respond to the knob changes»): K1-K4 of the
Sidechain view on SC16's drum pages.

SC16 (build_sc16.py) adds two pages of drums to the Sidechain view; its state (c_gst() + 24): [4 + d] the preset of drum d, [8 + d] its trigger
drum, [12] the page (0 = the stock's, 2 / 3 = the drums'), [13] the drum touched last; its handler of the project's group 0x20 (c_scgrp, entry 5 of
0x0805B3B0) writes each drum's preset (attack and hold / decay through the stock's converters 0x08028764 / 0x08028778, depth << 24) to the DSP block
X:$3A10 + 9 d + 1..4 (c_wr: r1 value, r2 offset, r5 drum).  sckn.py (K1-K4 there) only knew the note tracks' pages: on a drum page the knobs went on
moving the last note track's values, in its colour.

Ours: four free values per drum in the session record's tail + 968 ("SD", a bit per drum = its own values, 16 values: saved with the project):
  * the container's slot 4 (in front of sckn): on a drum page K1-K4 move the values of the drum touched last (starting from its preset's), then
    MARK_DIRTY(0x20, 26) (as SC16 does), so the group handler sends them; K5-K8 go on to the chain;
  * the group handler: SC16's, then each drum with its own values: those;
  * the Sidechain view's slot 0 (in front of sckn): a preset pad of a drum page = that drum back to its presets (the bit cleared);
  * the LED task: on a drum page K1-K4 = the four values in the drum's colour (bright = value).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, ldrb_w, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, strb_reg, strh_reg, subs_imm8, subs_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import build_sc16 as S16  # noqa: E402

SC_VT, CT_VT = 0x0805AC2C, 0x0805A62C
MODE_OFF, MODE_SC = 0x18C, 7
MARK_DIRTY = 0x0803BDCC
SESSION_OBJ, TAIL, O_BLK = 0x2003D71C, 0x27024, 968                # "SD", the bits, 0, then 4 x 4 values (attack, hold, decay, depth)
COL = (0x45, 0x2D, 0x49, 0x4D)                                     # drums 1-4


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    E(raw, bytes(COL)); t_col = base

    # ---- c_sdb() -> r0 = our block (made when missing), or 0; clobbers r1, r2
    a.label("c_sdb")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "sb_x", "eq")
    imm32(1, TAIL + O_BLK); E(adds_reg, 0, 0, 1)
    E(ldrb_imm, 1, 0, 0); E(cmp_imm, 1, 0x53); E(b_cond, "sb_m", "ne"); E(ldrb_imm, 1, 0, 1); E(cmp_imm, 1, 0x44); E(b_cond, "sb_x", "eq")
    a.label("sb_m")
    E(movs_imm, 1, 0x53); E(strb_imm, 1, 0, 0); E(movs_imm, 1, 0x44); E(strb_imm, 1, 0, 1); E(movs_imm, 1, 0); E(strb_imm, 1, 0, 2)
    a.label("sb_x"); E(raw, h(0x4770))

    # ---- c_sdst() -> r0 = SC16's state (0 without it); clobbers r1-r3
    a.label("c_sdst")
    E(raw, h(0xB500)); E(bl, L["c_scst"]); E(raw, h(0xBD00))

    # ---- c_sdval(r0 = drum, r1 = 0..3) -> r0 = the value now (its own, or its preset's); clobbers r1-r3
    a.label("c_sdval")
    E(push_list, [4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, "c_sdb"); E(cmp_imm, 0, 0); E(b_cond, "sv_p", "eq")
    E(ldrb_imm, 1, 0, 2); E(raw, h(0x40E1)); E(lsls_imm, 1, 1, 31); E(b_cond, "sv_p", "pl")              # lsrs r1, r4: its bit
    E(lsls_imm, 1, 4, 2); E(adds_reg, 1, 1, 5); E(adds_reg, 0, 0, 1); E(ldrb_imm, 0, 0, 4); E(pop_list, [4, 5], pc=True)
    a.label("sv_p")                                                                                    # the preset's
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "sv_0", "eq")
    E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, 4); E(movs_imm, 1, 7); E(raw, h(0x4008)); E(lsls_imm, 0, 0, 2)   # ands r0, r1
    imm32(1, L["preset_table"]); E(adds_reg, 0, 0, 1); E(ldrb_reg, 0, 0, 5); E(pop_list, [4, 5], pc=True)
    a.label("sv_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_sdpage() -> r0 = the drum of the drum page's choice (0..3), or 0xFF (another page, or the view not shown); clobbers r1-r3
    a.label("c_sdpage")
    E(raw, h(0xB500))
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "sp_n", "eq")
    E(ldrb_imm, 1, 0, 12); E(cmp_imm, 1, 2); E(b_cond, "sp_n", "lo"); E(ldrb_imm, 0, 0, 13); E(cmp_imm, 0, 3); E(b_cond, "sp_n", "hi")
    E(raw, h(0xBD00))
    a.label("sp_n"); E(movs_imm, 0, 0xFF); E(raw, h(0xBD00))

    # ---- c_sdknob (the container's slot 4: container, knob, delta)
    a.label("c_sdknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(ldrb_w, 3, 0, MODE_OFF); E(cmp_imm, 3, MODE_SC); E(b_cond, "dk_f", "ne")
    E(cmp_imm, 1, 4); E(b_cond, "dk_f", "hs")
    E(bl, "c_sdpage"); E(cmp_imm, 0, 0xFF); E(b_cond, "dk_f", "eq"); E(mov_reg, 4, 0)                   # r4 = the drum
    E(bl, "c_sdb"); E(cmp_imm, 0, 0); E(b_cond, "dk_x", "eq"); E(mov_reg, 7, 0)
    E(ldrb_imm, 0, 7, 2); E(raw, h(0x40E0)); E(lsls_imm, 0, 0, 31); E(b_cond, "dk_own", "mi")          # lsrs r0, r4
    E(movs_imm, 6, 0)                                                                                  # first: its preset's four values
    a.label("dk_i"); E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_sdval"); E(lsls_imm, 1, 4, 2); E(adds_reg, 1, 1, 6); E(adds_reg, 1, 1, 7)
    E(strb_imm, 0, 1, 4); E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "dk_i", "lo")
    E(movs_imm, 0, 1); E(raw, h(0x40A0)); E(ldrb_imm, 1, 7, 2); E(orrs_reg, 1, 0); E(strb_imm, 1, 7, 2)    # lsls r0, r4: its bit
    a.label("dk_own")
    E(raw, h(0x9901)); E(lsls_imm, 2, 4, 2); E(adds_reg, 2, 2, 1); E(adds_reg, 2, 2, 7)                   # ldr r1, [sp, #4]: r2 = the value's byte - 4
    E(ldrb_imm, 0, 2, 4); E(raw, h(0x9902)); E(adds_reg, 0, 0, 1)                                       # ldr r1, [sp, #8]: + delta
    E(cmp_imm, 0, 0); E(b_cond, "dk_l", "ge"); E(movs_imm, 0, 0)
    a.label("dk_l"); E(cmp_imm, 0, 127); E(b_cond, "dk_h", "le"); E(movs_imm, 0, 127)
    a.label("dk_h"); E(strb_imm, 0, 2, 4)
    E(movs_imm, 0, 0x20); E(movs_imm, 1, 26); E(bl, MARK_DIRTY)                                         # (the interface task, as SC16)
    a.label("dk_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("dk_f"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_sdgrp (the project group 5's handler): SC16's, then the drums with their own values
    a.label("c_sdgrp")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["grp"])
    E(bl, "c_sdb"); E(cmp_imm, 0, 0); E(b_cond, "dg_x", "eq"); E(mov_reg, 7, 0)
    E(movs_imm, 5, 0)                                                                                  # (c_wr wants the drum in r5)
    a.label("dg_l")
    E(ldrb_imm, 0, 7, 2); E(raw, h(0x40E8)); E(lsls_imm, 0, 0, 31); E(b_cond, "dg_n", "pl")            # lsrs r0, r5
    E(lsls_imm, 6, 5, 2); E(adds_reg, 6, 6, 7)                                                         # r6 + 4 = its four values
    for off, conv in ((0, S16.CONV_ATK), (1, S16.CONV_HD), (2, S16.CONV_HD)):
        E(ldrb_imm, 0, 6, 4 + off); E(bl, conv); E(mov_reg, 1, 0); E(movs_imm, 2, off + 1); E(bl, L["c_wr"])
    E(ldrb_imm, 1, 6, 7); E(lsls_imm, 1, 1, 24); E(movs_imm, 2, 4); E(bl, L["c_wr"])
    a.label("dg_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, 4); E(b_cond, "dg_l", "lo")
    a.label("dg_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_sdpad (the Sidechain view's slot 0: view, pad, velocity): a preset pad of a drum page = that drum back to its presets
    a.label("c_sdpad")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(cmp_imm, 1, 16); E(b_cond, "dp_f", "lo"); E(cmp_imm, 1, 32); E(b_cond, "dp_f", "hs")
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "dp_f", "eq")
    E(ldrb_imm, 1, 0, 12); E(cmp_imm, 1, 2); E(b_cond, "dp_f", "lo")
    E(subs_imm8, 1, 2); E(lsls_imm, 1, 1, 1); E(raw, h(0x9A01)); E(subs_imm8, 2, 16); E(lsrs_imm, 2, 2, 3); E(adds_reg, 4, 1, 2)   # ldr r2, [sp, #4]
    E(bl, "c_sdb"); E(cmp_imm, 0, 0); E(b_cond, "dp_f", "eq")
    E(movs_imm, 1, 1); E(raw, h(0x40A1)); E(ldrb_imm, 2, 0, 2); E(raw, h(0x438A)); E(strb_imm, 2, 0, 2)    # lsls r1, r4; bics r2, r1
    a.label("dp_f"); E(raw, popw([0, 1, 2, 4], lr=True)); E(b_w, prev["pad"])

    # ---- c_sdledtask (the LED task calls: ctrl, frame): the chain; on a drum page K1-K4 = the drum's four values in its colour
    a.label("c_sdledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, L["c_skon"]); E(cmp_imm, 0, 0); E(b_cond, "dl_x", "eq")
    E(bl, "c_sdpage"); E(cmp_imm, 0, 0xFF); E(b_cond, "dl_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, t_col); E(ldrb_reg, 7, 0, 4)
    E(movs_imm, 6, 0)
    a.label("dl_l")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_sdval"); E(movs_imm, 1, 0x7F); E(raw, h(0x4008))       # ands r0, r1
    E(adds_imm8, 0, 2); E(lsls_imm, 2, 0, 8); E(orrs_reg, 2, 7)
    E(mov_reg, 0, 6); E(adds_imm8, 0, 60); E(lsls_imm, 0, 0, 1); E(strh_reg, 2, 5, 0)
    E(adds_imm8, 6, 1); E(cmp_imm, 6, 4); E(b_cond, "dl_l", "lo")
    a.label("dl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; entry 5 of the group table, slot 0 of the Sidechain view, slot 4 of the container, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_scst=lab("sc16", "c_scst"), c_wr=lab("sc16", "c_wr"), preset_table=int(report["sc16"]["preset_table"], 16),
             c_skon=lab("sckn", "c_skon"))
    prev = dict(grp=u(S16.GROUP_TAB + 5 * 4) & ~1, pad=u(SC_VT) & ~1, knob=u(CT_VT + 16) & ~1, ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert prev["grp"] == lab("sc16", "c_scgrp"), hex(prev["grp"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, S16.GROUP_TAB + 5 * 4 - BASE, labels["c_sdgrp"] | 1)
    struct.pack_into("<I", img, SC_VT - BASE, labels["c_sdpad"] | 1)
    struct.pack_into("<I", img, CT_VT + 16 - BASE, labels["c_sdknob"] | 1)
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_sdledtask"])
    return labels, code, prev
