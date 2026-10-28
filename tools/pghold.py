"""SC48.3 / Beta 3.40 (the user's interface rules, 2026-10-28: «Picking a page or view. A tap keeps it, and holding it for ½ s or more shows it
only until you let go»; asked: «All knob pages»): the knob pages of MIDI 1 / 2's own synth (the page pads 1-7 and Shift + pad 4 of the MIDI
Preset view) follow it.

  * the head of slot 0 of the template view (view, pad, velocity): pads 1-8: the track's knob page before and after the chain (vcf21's c_vpage);
    when the press changed it, the track, the pad, the page before and the time go to our RAM;
  * the head of slot 1 (the pad release: view, pad): the same pad of the same track released HOLD_MS or more after = the page before back
    (c_vsetpage); a shorter press keeps the new page.  A press that did not change the page (pad 8's starters, pad 7 held on the FM page for
    its algorithms) leaves nothing to undo.

RAM: modmx.MXR + 0x1E60 (12 B, signed "PGH1": + 4 the track, + 5 the pad (0xFF none), + 6 the page before, + 8 the time).  In the hole.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, str_imm, str_sp, strb_imm, subs_reg)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import vcf21 as V  # noqa: E402

RAM = MX.MXR + 0x1E60
RSIG = 0x31484750                                             # "PGH1"
HOLD_MS = 500
N_PADS = 8                                                    # the page row: pads 1-8 (indices 0..7)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def track(rd, view): E(ldrb_imm, rd, view, 0x10); E(movs_imm, 3, 1); E(raw, h(0x4018 | rd))   # rd = [view + 0x10] & 1 (ands rd, r3)

    # ---- c_phpad (slot 0 of the template view: view, pad, velocity)
    a.label("c_phpad")
    E(cmp_imm, 1, N_PADS); E(b_cond, "hp_f", "hs")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    track(6, 4); E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(mov_reg, 7, 0)             # r7 = the page before
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(ldr_sp, 2, 8); E(bl, prev["pad"]); E(str_sp, 0, 0)   # the chain; its r0 kept
    E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(cmp_reg, 0, 7); E(b_cond, "hp_x", "eq")
    imm32(0, RAM); imm32(1, RSIG); E(str_imm, 1, 0, 0)
    E(strb_imm, 6, 0, 4); E(strb_imm, 5, 0, 5); E(strb_imm, 7, 0, 6); now(1); E(str_imm, 1, 0, 8)
    a.label("hp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("hp_f"); E(b_w, prev["pad"])

    # ---- c_phrel (slot 1 of the template view: view, pad)
    a.label("c_phrel")
    E(push_list, [0, 1, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(6, RAM); E(ldr_imm, 0, 6, 0); imm32(1, RSIG); E(cmp_reg, 0, 1); E(b_cond, "hr_x", "ne")
    E(ldrb_imm, 0, 6, 5); E(cmp_reg, 0, 5); E(b_cond, "hr_x", "ne")
    track(0, 4); E(ldrb_imm, 1, 6, 4); E(cmp_reg, 0, 1); E(b_cond, "hr_x", "ne")
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 6, 5)                                         # done with this press
    now(0); E(ldr_imm, 1, 6, 8); E(subs_reg, 0, 0, 1); E(movw, 1, HOLD_MS); E(cmp_reg, 0, 1); E(b_cond, "hr_x", "lo")
    E(ldrb_imm, 0, 6, 4); E(ldrb_imm, 1, 6, 6); E(bl, L["c_vsetpage"])               # held: the page before back
    a.label("hr_x"); E(raw, popw([0, 1, 4, 5, 6], lr=True)); E(b_w, prev["rel"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of slots 0 / 1 of the template view."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = {k: int(report["vcf20"]["labels"][k], 16) for k in ("c_vpage", "c_vsetpage")}
    prev = dict(pad=u(MP.TMPL_VT) & ~1, rel=u(MP.TMPL_VT + 4) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, MP.TMPL_VT - BASE, labels["c_phpad"] | 1)
    struct.pack_into("<I", img, MP.TMPL_VT + 4 - BASE, labels["c_phrel"] | 1)
    assert RAM + 12 <= MX.MXR + 0x2000
    return labels, code, prev
