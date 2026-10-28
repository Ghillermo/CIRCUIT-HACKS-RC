"""SC48.3 / Beta 3.40 (the user, 2026-10-28: «double press on scale = shift+scale, make sure double presses match their shift shortcuts everywhere
else»; chosen: Velocity twice = fixed velocity, and the other way round Shift + Synth / MIDI = what pressing them twice does; Scales: cscale.use_dbl):

  * Velocity pressed while a track's Velocity view is on the screen (sub-mode 9 t + 2 for Synth 1 / 2 and MIDI 1 / 2, 36 + 8 d + 2 for the
    drums) = the stock's Shift + Velocity: bit 1 of parameter 2 of [ctrl + 0x78] toggled (fixed velocity) and committed; the stock's second
    press did nothing;
  * Shift + Synth 1 / 2 (the stock drops Shift + a track button) = what pressing it twice does: the track selected, its Note view if it is not
    on the screen, then the Synth button again (srcview: the synth's source view); Shift + MIDI 1 / 2 = the track selected, then a tap on Preset
    (midipre: the MIDI Preset view).  The presses go through the whole chain with the Shift byte at 0 (the read copy of p0 of [ctrl + 0xC], put
    back after).  Not in the Setup view, not with Clear / Duplicate held, not with the MIDI track's CC editor open.

A head of the button press (0x08033320).  No RAM.  In the hole (no card, no settings).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, muls,  # noqa: E402
                   pop_list, push_list, raw, str_imm, strb_imm, subs_imm8, tst_reg)
import srcview as SV  # noqa: E402
import pgmch as PG  # noqa: E402

PARAM_GET, PARAM_PTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
ID_NOTE, ID_VEL, ID_PRESET = 9, 10, 8
FIXED = 0x78                                                  # [ctrl + 0x78]: parameter 2 bit 1 = fixed velocity (the stock's Shift + Velocity)


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def press(i):                                                                      # a press and a release through the whole chain (r4 = ctrl)
        E(mov_reg, 0, 4); E(movs_imm, 1, i); E(bl, SV.BTN); E(mov_reg, 0, 4); E(movs_imm, 1, i); E(bl, SV.BTN_REL)
    def sub(rd): E(raw, ldrb_w(rd, 4, SV.S_CUR))                                      # rd = the controller's sub-mode (r4 = ctrl)
    def note_sub(rd):                                                                  # rd = 9 * id + 1 (r5 = id)
        E(movs_imm, rd, 9); E(muls, rd, 5); E(adds_imm8, rd, 1)

    # ---- c_dbok (r4 = ctrl) -> r0 = 1: not the Setup view, no Clear / Duplicate held
    a.label("c_dbok")
    E(push_list, [], lr=True)
    E(ldr_imm, 0, 4, PG.MODE_STORE); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, PG.MODE_SETUP); E(b_cond, "ok_0", "eq")
    E(ldr_imm, 0, 4, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(tst_reg, 0, 1); E(b_cond, "ok_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [], pc=True)
    a.label("ok_0"); E(movs_imm, 0, 0); E(pop_list, [], pc=True)

    # ---- c_dbbtn (the head of the button press: ctrl, id)
    a.label("c_dbbtn")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(mov_reg, 6, 0)       # r6 = the Shift byte
    E(cmp_imm, 5, ID_VEL); E(b_cond, "db_v", "eq"); E(cmp_imm, 5, 3); E(b_cond, "db_f", "hi")
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "db_f", "eq")
    E(bl, "c_dbok"); E(cmp_imm, 0, 0); E(b_cond, "db_f", "eq")
    E(cmp_imm, 5, 2); E(b_cond, "db_s", "lo")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 2); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); E(b_cond, "db_f", "ne")   # its CC editor open
    a.label("db_s")
    E(ldrb_imm, 0, 6, 0); E(push_list, [0])                                            # Shift off while we press (put back after)
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN_REL)   # the track
    E(cmp_imm, 5, 2); E(b_cond, "db_m", "hs")
    sub(0); note_sub(1); E(cmp_reg, 0, 1); E(b_cond, "db_n", "eq")
    press(ID_NOTE)                                                                     # its Note view first
    sub(0); note_sub(1); E(cmp_reg, 0, 1); E(b_cond, "db_r", "ne")
    a.label("db_n")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN); E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, SV.BTN_REL)   # the second press
    E(b, "db_r")
    a.label("db_m"); press(ID_PRESET)                                                  # MIDI: a tap on Preset
    a.label("db_r")
    E(ldr_imm, 0, 4, 0xC); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(pop_list, [1]); E(strb_imm, 1, 0, 0)   # Shift back
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)

    a.label("db_v")                                                                    # Velocity: in a Velocity view, without Shift
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); E(b_cond, "db_f", "ne")
    E(bl, "c_dbok"); E(cmp_imm, 0, 0); E(b_cond, "db_f", "eq")
    sub(0); E(cmp_imm, 0, 36); E(b_cond, "dv_d", "hs")
    a.label("dv_9"); E(cmp_imm, 0, 9); E(b_cond, "dv_c", "lo"); E(subs_imm8, 0, 9); E(b, "dv_9")   # sub % 9
    a.label("dv_d"); E(cmp_imm, 0, 68); E(b_cond, "db_f", "hs"); E(subs_imm8, 0, 36); E(movs_imm, 1, 7); E(raw, h(0x4008))   # ands r0, r1
    a.label("dv_c"); E(cmp_imm, 0, 2); E(b_cond, "db_f", "ne")
    E(ldr_imm, 0, 4, FIXED); E(movs_imm, 1, 2); E(bl, PARAM_PTR)                        # the stock's Shift + Velocity
    E(ldr_imm, 1, 0, 0); E(movs_imm, 2, 2); E(raw, h(0x4051)); E(str_imm, 1, 0, 0)     # eors r1, r2
    E(ldr_imm, 0, 4, FIXED); E(bl, COMMIT)
    E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)

    a.label("db_f"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the head of the button press."""
    import ct_fw
    import mpatch as MP
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    L = dict(c_edact=int(report["vcf20"]["labels"]["c_edact"], 16))
    prev = dict(btn=MP.bw_target(img, SV.BTN, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SV.BTN - BASE:SV.BTN - BASE + 4] = bw_enc(SV.BTN, labels["c_dbbtn"])
    return labels, code, prev
