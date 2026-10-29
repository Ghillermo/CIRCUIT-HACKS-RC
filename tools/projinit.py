"""SC49.1 / Beta 3.46 (the user, 2026-10-29: «new shortcut: shift+preset takes current voice to project init»): Shift + Preset = the voice of the
track on the screen back to the project's (the same «Project init» a marked step goes back to: autorel.use_init).

  * Preset = button 8: with Shift the stock drops it at the entry of 0x08033320 (its Shift mask): a head of the button press sees it first and
    swallows it.
  * The track: the track views' container on the screen ([MGR + 0x6C] = CONT) and [MGR + 0x152] < 36: t = [MGR + 0x152] / 9 (Synth 1, Synth 2,
    MIDI 1, MIDI 2, any of their subviews); the drums and the other views: nothing.
  * Synth 1 / 2: the stock's 0x0802FC82(session object, s, 0) = the synth's patch in the session record copied whole into its store and applied
    (the stock's own path after a project load or a patch chosen; the record keeps the project as loaded / last saved: knobs turned since are
    not there).
  * MIDI 1 / 2 with the own engine on: projsyn's restore after a load, for that track (c_ysget: the record's blocks into IMG[t]; c_ysrun(t, 1):
    mpatch's load from it; c_ysrun(t, 0): gathered again); a project without them: the engine's defaults (vcf21.c_vreset, as Clear + MIDI).
    The engine off: nothing (MIDI out only).
  * LEDs: with Shift held and one of those voices on the screen, Preset yellow (the Shift convention); otherwise the stock's (dark with Shift).
RAM: none.  In the hole (no card: the record is in RAM; projsyn's IO goes to RAM)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list,  # noqa: E402
                   push_list, raw, strh_reg, subs_imm8)
import packio as PK  # noqa: E402
import mpatch as MP  # noqa: E402
import srcview as SV  # noqa: E402
import fxdiag as FD  # noqa: E402

MGR, CONT, S_CUR = 0x20040B10, 0x20040DB8, 0x152
PRESET = 8
SESSION_OBJ = 0x2003D71C
SYN_RELOAD = 0x0802FC82                # (this = the session object, synth, 0): the record's patch of that synth into its store, applied
LED_PRESET = 32 + PRESET               # the buttons' panel LEDs = 32 + id
COL_SHIFT = 0x2D                       # yellow


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_pivoice() -> r0 = the voice on the screen: 0 / 1 Synth 1 / 2, 2 / 3 MIDI 1 / 2 with the own engine on; 0xFF none; clobbers r1-r3
    a.label("c_pivoice")
    E(push_list, [4], lr=True)
    imm32(0, MGR); E(ldr_imm, 1, 0, 0x6C); imm32(2, CONT); E(cmp_reg, 1, 2); E(b_cond, "pv_n", "ne")
    E(raw, h(0xF890) + h(1 << 12 | S_CUR))                                            # ldrb.w r1, [r0, #S_CUR]
    E(movs_imm, 4, 0)
    a.label("pv_l"); E(cmp_imm, 1, 9); E(b_cond, "pv_t", "lo"); E(subs_imm8, 1, 9); E(adds_imm8, 4, 1); E(b, "pv_l")
    a.label("pv_t"); E(cmp_imm, 4, 3); E(b_cond, "pv_n", "hi"); E(cmp_imm, 4, 2); E(b_cond, "pv_y", "lo")
    E(mov_reg, 0, 4); E(subs_imm8, 0, 2); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "pv_n", "eq")
    a.label("pv_y"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)
    a.label("pv_n"); E(movs_imm, 0, 0xFF); E(pop_list, [4], pc=True)

    # ---- c_pibtn (the button press: ctrl, id): Shift + Preset = the voice on the screen back to the project's
    a.label("c_pibtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(mov_reg, 4, 0)
    E(cmp_imm, 1, PRESET); E(b_cond, "pb_p", "ne")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "pb_p", "eq")   # Shift
    E(bl, "c_pivoice"); E(cmp_imm, 0, 3); E(b_cond, "pb_p", "hi"); E(mov_reg, 5, 0)
    E(cmp_imm, 5, 2); E(b_cond, "pb_m", "hs")
    imm32(0, SESSION_OBJ); E(ldr_imm, 1, 0, 0x14); E(cmp_imm, 1, 0); E(b_cond, "pb_x", "eq")
    E(mov_reg, 1, 5); E(movs_imm, 2, 0); E(bl, SYN_RELOAD); E(b, "pb_x")                  # Synth 1 / 2
    a.label("pb_m")                                                                      # MIDI 1 / 2
    E(subs_imm8, 5, 2); E(mov_reg, 0, 5); E(bl, L["c_ysget"]); E(cmp_imm, 0, 0); E(b_cond, "pb_d", "eq")
    E(mov_reg, 0, 5); E(movs_imm, 1, 1); E(bl, L["c_ysrun"])
    E(mov_reg, 0, 5); E(movs_imm, 1, 0); E(bl, L["c_ysrun"]); E(b, "pb_x")
    a.label("pb_d"); E(mov_reg, 0, 5); E(bl, L["c_vreset"])
    a.label("pb_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)                               # swallowed
    a.label("pb_p"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_piled (the LED task's calls: ctrl, frame): the chain, then Shift with a voice on the screen = Preset yellow
    a.label("c_piled")
    E(push_list, [4, 5], lr=True); E(mov_reg, 5, 1)
    E(bl, prev["ledtask"])
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "pl_x", "eq")
    E(bl, "c_pivoice"); E(cmp_imm, 0, 3); E(b_cond, "pl_x", "hi")
    E(movs_imm, 0, COL_SHIFT); E(movs_imm, 1, 2 * LED_PRESET); E(strh_reg, 0, 5, 1)
    a.label("pl_x"); E(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the button press, the LED task's calls."""
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_vreset")}
    L.update({k: lab("projsyn", k) for k in ("c_ysget", "c_ysrun")})
    L["c_shift"] = lab("sc15", "c_shift")
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    assert FD.bl_target(img, PK.LED_CALLS[1], BASE) == prev["ledtask"]
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = bw_enc(SV.BTN, labels["c_pibtn"])
    for c in PK.LED_CALLS:
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_piled"])
    return labels, code, prev
