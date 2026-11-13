"""SC57.1 / Beta 5.56 (the user, 2026-11-12: «master fx view should be able to be held and drop back to previous view, like the other views and
pages»; chosen: «Hold Mixer in Mixer»): the interface rule «a tap keeps a view, held ½ s or more it shows only until you let go» for Master FX.

Master FX is a mode of the Mixer view (build_sc17, use_mixer14: Mixer pressed in the Mixer toggles the block's S_MODE; from any other view Mixer
goes to the Mixer).  The stock's own hold-to-return (the release's 0x08033724: [ctrl + 0x154 + id], mask 0x0664FFFF) never sees that toggle, which
returns before the stock's case.

  * a new head of the button chain (0x08033320): Mixer (id 14) with the Mixer view on the screen = the mode before, the time, armed (RAM);
  * a new head of the button release (0x0803381A): Mixer, armed, held HOLD_MS or more, still the Mixer view and the mode changed by that press =
    the mode before back (S_MODE, S_HELD 0, as c_mixbtn's toggle).  So in the Mixer, Mixer held = Master FX until you let go; in Master FX, Mixer
    held = the Mixer until you let go.  A tap toggles as before.

RAM MFR (12 B, signed "MFH1": + 4 armed, + 5 the mode before, + 8 the time); the RAM is not cleared at power-on.  In dspz's gap (dspz.add).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, str_imm, strb_imm, subs_reg)
import mpatch as MP  # noqa: E402
import vcf21 as V  # noqa: E402
import build_sc17 as S17  # noqa: E402

MFR = 0x2004FAD0                                              # after fmmap's LR (0x2004FAC8, 4 B), below 0x2004FC00
RSIG = 0x3148464D                                             # "MFH1"
HOLD_MS = 500
ID_MIXER = 14
BTN_REL = 0x0803381A
MIX_VT = S17.MIX2["MIX_VT"]                                   # the Mixer view's vtable (use_mixer14)
S_MODE, S_HELD = S17.S_MODE, S17.S_HELD


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def inmixer(lab):                                         # (r4 = ctrl) the Mixer view on the screen, else to lab; clobbers r0, r1
        E(ldr_imm, 0, 4, 0x6C); E(cmp_imm, 0, 0); E(b_cond, lab, "eq"); E(ldr_imm, 0, 0, 0); imm32(1, MIX_VT); E(cmp_reg, 0, 1); E(b_cond, lab, "ne")

    # ---- c_mhbtn (the button press head: ctrl, id)
    a.label("c_mhbtn")
    E(cmp_imm, 1, ID_MIXER); E(b_cond, "mb_f", "ne")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 4, 0)
    inmixer("mb_x")
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "mb_x", "eq")
    E(ldrb_imm, 5, 0, S_MODE)
    imm32(0, MFR); imm32(1, RSIG); E(str_imm, 1, 0, 0); E(strb_imm, 5, 0, 5); E(movs_imm, 1, 1); E(strb_imm, 1, 0, 4); now(1); E(str_imm, 1, 0, 8)
    a.label("mb_x"); E(raw, popw([0, 1, 4, 5], lr=True))
    a.label("mb_f"); E(b_w, prev["btn"])

    # ---- c_mhrel (the button release head: ctrl, id)
    a.label("c_mhrel")
    E(cmp_imm, 1, ID_MIXER); E(b_cond, "mr_f", "ne")
    E(push_list, [0, 1, 4, 5, 6], lr=True); E(mov_reg, 4, 0)
    imm32(6, MFR); E(ldr_imm, 0, 6, 0); imm32(1, RSIG); E(cmp_reg, 0, 1); E(b_cond, "mr_x", "ne")
    E(ldrb_imm, 0, 6, 4); E(cmp_imm, 0, 0); E(b_cond, "mr_x", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 4)                                            # done with this press
    now(0); E(ldr_imm, 1, 6, 8); E(subs_reg, 0, 0, 1); E(movw, 1, HOLD_MS); E(cmp_reg, 0, 1); E(b_cond, "mr_x", "lo")
    inmixer("mr_x")
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "mr_x", "eq")
    E(ldrb_imm, 1, 6, 5); E(ldrb_imm, 2, 0, S_MODE); E(cmp_reg, 1, 2); E(b_cond, "mr_x", "eq")   # the press did not toggle: nothing
    E(strb_imm, 1, 0, S_MODE); E(movs_imm, 1, 0); E(strb_imm, 1, 0, S_HELD)            # held: the mode before back
    a.label("mr_x"); E(raw, popw([0, 1, 4, 5, 6], lr=True))
    a.label("mr_f"); E(b_w, prev["rel"])
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); the heads of the button press and release."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16))
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), rel=MP.bw_target(img, BTN_REL, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_mhbtn"])
    img[BTN_REL - BASE:BTN_REL - BASE + 4] = b_w(BTN_REL, labels["c_mhrel"])
    assert MFR + 12 <= 0x2004FC00
    return labels, code, prev
