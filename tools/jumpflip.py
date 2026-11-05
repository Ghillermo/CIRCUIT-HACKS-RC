"""SC51.6 / Beta 5.19 (the user, 2026-11-04: «make the second row (step flip destination) appear on the patch-flipping mode. Enabling patch flip works as usual,
but the destinations are shown in the third row, picking one of these destinations enables step flip mode»; then: pad 26 = all off, the lit destination again
= back to patch flip; the destinations leave the engine row; pads 9-16 dark with either flip mode): the jump sequencer's target (jumpseq: «step flip») is
chosen from the patch flip mode of the MIDI 1 / 2 Preset view.

  * patch flip on (pad 26, the stock's toggle, unchanged): pads 17-24 = the eight tracks in the order of the track buttons and their colours (0x08056464:
    [1 + t] bright, [9 + t] dim), the track itself dark; pads 9-16 dark (no own-synth patches: the engine is off);
  * a destination = step flip: the jump target (jumpseq's record bytes, with its signature) and patch flip off; another destination changes it; the lit one
    again = patch flip again (no target); pad 26 = all off (no target, patch flip stays off).  In step flip pad 26 blinks in the target's colour (256 ms,
    as pad 27 did) and pad 27 is the engine's off colour (0x02);
  * the engine row (pad 27) no longer points: its pads 9-16 are dark and do nothing;
  * an engine coming on still clears the target (jumpseq's LEDs);
  * the two exclude each other (the user: «step flip and patch flip settings exclude eachother»): found both on (a project loaded with a target while patch
    flip was on), step flip wins and patch flip's bit goes off (the template view's LEDs).
Slot 0 / 7 of the template view (0x0805AE5C), ahead of jumpseq's c_jspad / c_jsled.  No RAM of its own.  In dspz's gap (dspz.add).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, eors_reg, h, ldr_imm, ldrb_imm, ldrh_reg, lsls_imm, lsls_reg,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, orrs_reg, bics_reg, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_imm, strh_reg, subs_imm8)
import mpatch as MP  # noqa: E402
import modesel as MS  # noqa: E402
import jumpseq as JS  # noqa: E402
import build_sc06 as S6  # noqa: E402

DEST = 16                                   # pads 17-24
COL_OFF = 0x02                              # the engine's off colour (midipre / modesel)
RET = h(0x4770)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    PF = S6.PF_PAD
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_jfst(r0 = 0 MIDI 1 / 1 MIDI 2) -> r0 = 0 neither, 1 patch flip, 2 step flip (a target); clobbers r1-r3
    a.label("c_jfst")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, JS.CAVE); E(cmp_imm, 0, 0); E(b_cond, "st_pf", "eq"); E(movs_imm, 0, 2); E(pop_list, [4], pc=True)
    a.label("st_pf")
    E(bl, L["c_settings"]); E(cmp_imm, 0, 0); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, 2); E(bl, S6.PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 5); E(raw, h(0x1B09)); E(lsls_reg, 0, 1)                     # subs r1, r1, r4; bit 26 + m -> bit 31
    E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "st_1", "ge"); E(movs_imm, 1, 1)
    a.label("st_1"); E(mov_reg, 0, 1)
    a.label("st_x"); E(pop_list, [4], pc=True)

    # ---- c_jfpf(r0 = m, r1 = 0 off / 1 on): patch flip's bit (26 + m of the settings' parameter 2), committed; clobbers r0-r3
    a.label("c_jfpf")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    E(bl, L["c_settings"]); E(cmp_imm, 0, 0); E(b_cond, "pf_x", "eq")
    E(movs_imm, 1, 2); E(bl, S6.PARAM_PTR); E(ldr_imm, 1, 0, 0)
    E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 26); E(lsls_reg, 2, 4); E(bics_reg, 1, 2)
    E(cmp_imm, 5, 0); E(b_cond, "pf_w", "eq"); E(orrs_reg, 1, 2)
    a.label("pf_w"); E(str_imm, 1, 0, 0)
    E(bl, L["c_settings"]); E(bl, S6.COMMIT)
    a.label("pf_x"); E(pop_list, [4, 5], pc=True)

    # ---- c_jfpad (slot 0 of the template view: view, pad, velocity)
    a.label("c_jfpad")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "jf_p", "hi"); E(mov_reg, 4, 0)    # r4 = m
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm3, 0, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "jf_nr", "ne")
    E(cmp_imm, 5, JS.ROW); E(b_cond, "jf_p", "lo"); E(cmp_imm, 5, JS.ROW + 7); E(b_cond, "jf_s", "ls")   # the engine row: pads 9-16 do nothing
    E(b, "jf_p")
    a.label("jf_nr")
    E(mov_reg, 0, 4); E(bl, "c_jfst"); E(cmp_imm, 0, 0); E(b_cond, "jf_p", "eq"); E(mov_reg, 6, 0)   # r6 = 1 / 2
    E(cmp_imm, 5, PF); E(b_cond, "jf_n26", "ne")
    E(cmp_imm, 6, 2); E(b_cond, "jf_p", "ne")                                      # patch flip: the stock's toggle
    E(movs_imm, 0, 0); E(b, "jf_set")                                              # step flip: all off
    a.label("jf_n26")
    E(cmp_imm, 5, 8); E(b_cond, "jf_p", "lo"); E(cmp_imm, 5, DEST + 7); E(b_cond, "jf_p", "hi")
    E(cmp_imm, 5, DEST); E(b_cond, "jf_s", "lo")                                   # pads 9-16: nothing
    E(subs_imm8, 5, DEST); E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 5); E(b_cond, "jf_s", "eq")   # its own track
    E(adds_imm8, 5, 1); E(mov_reg, 0, 4); E(bl, JS.CAVE); E(cmp_reg, 0, 5); E(b_cond, "jf_new", "ne")
    E(movs_imm, 0, 0); E(bl, "jf_tg"); E(mov_reg, 0, 4); E(movs_imm, 1, 1); E(bl, "c_jfpf"); E(b, "jf_s")   # the lit one: patch flip again
    a.label("jf_new"); E(mov_reg, 0, 5); E(bl, "jf_tg"); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_jfpf"); E(b, "jf_s")
    a.label("jf_set"); E(bl, "jf_tg")
    a.label("jf_s"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    a.label("jf_p"); E(pop_list, [0, 1, 2, 4, 5, 6]); E(raw, JS.POP_LR); E(b_w, prev["pad"])
    # jf_tg(r0 = the target + 1, r4 = m): jumpseq's record byte (its signature written first); clobbers r0-r3
    a.label("jf_tg")
    E(push_list, [0], lr=True); E(bl, JS.L_JSAD); E(b_cond, "tg_k", "eq"); E(movs_imm, 0, 0); E(strh_imm, 0, 1, 0); E(movs_imm, 0, JS.SIG); E(strb_imm, 0, 1, 2)
    a.label("tg_k"); E(pop_list, [0]); E(strb_reg, 0, 1, 4); E(pop_list, [], pc=True)

    # ---- c_jfled (slot 7 of the template view: view) -> r0 = the LED buffer
    a.label("c_jfled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "ld_x", "hi"); E(mov_reg, 4, 0)
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm3, 0, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "ld_nr", "ne")
    E(movs_imm, 6, 0); E(b, "ld_dk")                                                # the engine row: pads 9-16 dark
    a.label("ld_nr")
    E(mov_reg, 0, 4); E(bl, "c_jfst"); E(cmp_imm, 0, 0); E(b_cond, "ld_x", "eq"); E(mov_reg, 6, 0)
    a.label("ld_dk")
    E(movs_imm, 0, 0); E(movs_imm, 1, 2 * 8)
    a.label("ld_z"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 2 * 16); E(b_cond, "ld_z", "lo")
    E(cmp_imm, 6, 0); E(b_cond, "ld_x", "eq")
    E(mov_reg, 0, 4); E(bl, JS.CAVE); E(mov_reg, 6, 0); imm32(7, JS.PAL)              # r6 = the target + 1
    E(movs_imm, 3, 0)
    a.label("ld_l")
    E(lsls_imm, 1, 3, 1); E(adds_imm8, 1, 2 * DEST); E(adds_imm3, 2, 3, 1); E(lsls_imm, 2, 2, 1)   # r1 = the pad's place, r2 = the bright colour's
    E(adds_imm3, 0, 3, 1); E(cmp_reg, 0, 6); E(b_cond, "ld_b", "eq"); E(adds_imm8, 2, 16)
    a.label("ld_b"); E(ldrh_reg, 2, 7, 2)
    E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 3); E(b_cond, "ld_o", "ne"); E(movs_imm, 2, 0)   # its own track: no light
    a.label("ld_o"); E(strh_reg, 2, 5, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "ld_l", "lo")
    E(cmp_imm, 6, 0); E(b_cond, "ld_x", "eq")                                        # step flip: pad 26 blinks in its colour, pad 27 off
    E(bl, L["c_settings"]); E(cmp_imm, 0, 0); E(b_cond, "ld_nb", "eq")             # (the two exclude each other: a project loaded with a target and
    E(movs_imm, 1, 2); E(bl, S6.PARAM_GET); E(ldr_imm, 0, 0, 0)                     #  patch flip on = step flip wins, patch flip off)
    E(movs_imm, 1, 5); E(raw, h(0x1B09)); E(lsls_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "ld_nb", "ge")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, "c_jfpf")
    a.label("ld_nb")
    E(lsls_imm, 2, 6, 1)
    E(movs_imm, 3, JS.HAL_TICK >> 24); E(lsls_imm, 3, 3, 24); E(raw, h(0xF8D0 | 3) + h(3 << 12 | JS.HAL_TICK & 0xFFF)); E(lsls_imm, 3, 3, 23); E(b_cond, "ld_k", "pl"); E(adds_imm8, 2, 16)
    a.label("ld_k"); E(ldrh_reg, 2, 7, 2); E(movs_imm, 1, 2 * PF); E(strh_reg, 2, 5, 1)
    E(movs_imm, 2, COL_OFF); E(movs_imm, 1, 2 * MS.PAD); E(strh_reg, 2, 5, 1)
    a.label("ld_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """After dspz (dspz.add): slots 0 / 7 of the template view, ahead of jumpseq's."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    assert JS.V2 and (u(MP.TMPL_VT) & ~1) == lab("jumpseq", "c_jspad") and (u(MP.TMPL_VT + 28) & ~1) == lab("jumpseq", "c_jsled")
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_settings=lab("sc06", "c_settings"))
    JS.L_JSAD = lab("jumpseq", "c_jsad")
    prev = dict(pad=u(MP.TMPL_VT) & ~1, leds=u(MP.TMPL_VT + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, MP.TMPL_VT - BASE, labels["c_jfpad"] | 1)
    struct.pack_into("<I", img, MP.TMPL_VT + 28 - BASE, labels["c_jfled"] | 1)
    return labels, code, prev
