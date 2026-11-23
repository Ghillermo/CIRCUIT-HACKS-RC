"""Alpha 7.31 (the user, 2026-11-22: «shift + mixer should enter master fx too (all alt, press twice, views also open with shift)»): the rule
«a view that opens by pressing its button twice also opens with Shift + that button» where the stock drops the Shift press.

  * Shift + Mixer (id 14; not in the stock's Shift mask, so the stock drops it) = Master FX: outside the Mixer view two presses (the Mixer, then
    Master FX: build_sc17's use_mixer14 toggles S_MODE on a press in the Mixer), in the Mixer view one press (Mixer <-> Master FX, as a press).
    The presses go through the whole chain with the Shift byte at 0 (the read copy of p0 of [ctrl + 0xC]), put back after (as dblpress).
    Not in the Setup view, not with Clear / Duplicate held.
(Shift + Synth 1 / 2 / MIDI 1 / 2 = dblpress, SC48.3; Scales = cscale.use_dbl; Velocity, Note, Gate, Pattern Settings: the stock's own Shift.)

A head of the button press (0x08033320), the outermost.  No RAM.  In dspz's gap (dspz.add)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, strb_imm)
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import pgmch as PG  # noqa: E402
import build_sc17 as S17  # noqa: E402

PARAM_GET = 0x0803542C
ID_MIXER = 14
MIX_VT = S17.MIX2["MIX_VT"]


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def press(i):                                                                     # a press and a release through the whole chain (r4 = ctrl)
        E(mov_reg, 0, 4); E(movs_imm, 1, i); E(bl, prev["btn"]); E(mov_reg, 0, 4); E(movs_imm, 1, i); E(bl, SV.BTN_REL)

    # ---- c_svbtn (the head of the button press: ctrl, id)
    a.label("c_svbtn")
    E(cmp_imm, 1, ID_MIXER); E(b_cond, "sv_f", "ne")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(mov_reg, 6, 0)      # r6 = the Shift byte
    E(ldrb_imm, 5, 6, 0); E(cmp_imm, 5, 0); E(b_cond, "sv_x", "eq")
    E(ldr_imm, 0, 4, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "sv_x", "eq")
    E(ldr_imm, 0, 4, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(raw, h(0x4208)); E(b_cond, "sv_x", "ne")                     # (tst r0, r1) Clear / Duplicate held
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)                                           # Shift off while we press
    E(ldr_imm, 0, 4, 0x6C); E(cmp_imm, 0, 0); E(b_cond, "sv_2", "eq"); E(ldr_imm, 0, 0, 0); imm32(1, MIX_VT); E(cmp_reg, 0, 1); E(b_cond, "sv_1", "eq")
    a.label("sv_2"); press(ID_MIXER)                                                  # not in the Mixer: the Mixer first
    a.label("sv_1"); press(ID_MIXER)                                                  # Mixer <-> Master FX
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(strb_imm, 5, 0, 0)  # Shift back
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("sv_x"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True))
    a.label("sv_f"); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap); the outermost head of the button press."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(btn=MP.bw_target(img, MP.BTN_ENTRY, BASE))
    code, labels = arm_code(base_addr, {}, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_svbtn"])
    return labels, code, prev
