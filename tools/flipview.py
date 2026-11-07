"""SC52.9 (the user, 2026-11-07: «Para aclarar la interfaz … el modo patch flip (pad 26) ahora: muestra los destinos de step flip en la fila 2 cuando
se activa step flip. En la fila 3 permite elegir entre modos (excluyentes): patch flip (PGM seq), Step flip (en el futuro, también morph, no la dibujes)»;
chosen: «pad 26 solo abre / cierra la vista», «pad 17 PGM seq, pad 18 Step flip», «step flip sin destino = el último usado»): the flip view of the
MIDI 1 / 2 Preset view, in place of jumpflip's (SC51.6).

  * pad 26 alone (no Shift / Clear / Duplicate) opens / closes the view; the mode does not change.  Open: pad 26 white; it closes by itself when the
    view's LEDs have not been asked for in CLOSE_MS (another view) and when the engine row (pad 27) opens; opening it closes the engine row;
  * row 3: pad 17 = patch flip (PGM seq) in pad 26's own colour (the stock toggle's on / off), pad 18 = step flip in the target's colour (bright when
    on, dim when off); a tap = that mode (the other off), the lit one again = off; pads 19-24 dark (pad 19 kept for morph), their taps swallowed;
  * row 2 with step flip on: the eight tracks (their colours, the target bright, the own track dark); a tap = the target; without step flip dark;
  * step flip on without a target chosen = the last target used (RAM; at power-up Synth 1);
  * view closed: the pads are the view's own (jumpflip's destinations on row 3 are gone); with step flip pad 26 blinks in the target's colour and
    pad 27 is the engine's off colour (as before); the two modes still exclude each other (a project loaded with both: step flip wins).
The outermost heads of the template view's slots 0 / 7; below them jumpflip is skipped (its previous slots); jumpflip's c_jfst / c_jfpf / jf_tg are
called (the settings' commit runs from jumpflip, in dspz's gap: lazysave sees the mod).  RAM modmx.MXR + 0x22B0: + 0 "FLV1", + 4 the open track + 1,
+ 5 / + 6 the last target + 1 of MIDI 1 / 2, + 8 the time of the last LED call.  In the hole (hole.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrh_imm, ldrh_reg, lsls_imm, lsls_reg,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, strh_reg, subs_imm8, subs_reg)
import mpatch as MP  # noqa: E402
import modesel as MS  # noqa: E402
import modmx as MX  # noqa: E402
import jumpseq as JS  # noqa: E402
import jumpflip as JF  # noqa: E402
import build_sc06 as S6  # noqa: E402

RAM = MX.MXR + 0x22B0
SIG = 0x31564C46                            # "FLV1"
O_OPEN, O_LAST, O_T = 4, 5, 8
CLOSE_MS = 300
P_PGM, P_STEP = 16, 17                      # pads 17 / 18
WHITE = 0x01
RET = h(0x4770)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    PF = S6.PF_PAD
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, JS.HAL_TICK); E(ldr_imm, rd, rd, 0)

    # ---- c_fvst() -> r0 = RAM (the first time: the signature, closed, no last targets); clobbers r1, r2
    a.label("c_fvst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "fs_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, O_OPEN); E(str_imm, 1, 0, O_T)
    a.label("fs_x"); E(raw, RET)

    # ---- c_fvlast(r0 = m) -> r0 = the last target + 1 (none: 1, Synth 1); clobbers r1-r3
    a.label("c_fvlast")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_fvst")
    E(raw, h(0x1900 | 4 << 6 | 0 << 3 | 0)); E(ldrb_imm, 0, 0, O_LAST)                # adds r0, r0, r4
    E(cmp_imm, 0, 0); E(b_cond, "fl_x", "ne"); E(movs_imm, 0, 1)
    a.label("fl_x"); E(pop_list, [4], pc=True)

    # ---- c_fvpad (slot 0 of the template view: view, pad, velocity)
    a.label("c_fvpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "fp_p", "hi"); E(mov_reg, 4, 0)       # r4 = m
    E(bl, "c_fvst"); E(mov_reg, 6, 0)
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm3, 0, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "fp_nr", "ne")
    E(cmp_imm, 5, JS.ROW); E(b_cond, "fp_p", "lo"); E(cmp_imm, 5, JS.ROW + 7); E(b_cond, "fp_s", "ls"); E(b, "fp_p")   # the engine row: pads 9-16 nothing
    a.label("fp_nr")
    E(cmp_imm, 5, PF); E(b_cond, "fp_n26", "ne")
    E(bl, L["c_msheld"]); E(cmp_imm, 0, 0); E(b_cond, "fp_p", "ne")
    E(adds_imm3, 1, 4, 1); E(ldrb_imm, 0, 6, O_OPEN); E(cmp_reg, 0, 1); E(b_cond, "fp_op", "ne")
    E(movs_imm, 1, 0)
    a.label("fp_op"); E(strb_imm, 1, 6, O_OPEN); E(b, "fp_s")
    a.label("fp_n26")
    E(adds_imm3, 1, 4, 1); E(ldrb_imm, 0, 6, O_OPEN); E(cmp_reg, 0, 1); E(b_cond, "fp_p", "ne")
    E(cmp_imm, 5, 8); E(b_cond, "fp_p", "lo"); E(cmp_imm, 5, 23); E(b_cond, "fp_p", "hi")
    E(mov_reg, 0, 4); E(bl, L["c_jfst"]); E(mov_reg, 7, 0)                                  # r7 = 0 / 1 patch flip / 2 step flip
    E(cmp_imm, 5, P_PGM); E(b_cond, "fp_np", "ne")
    E(cmp_imm, 7, 1); E(b_cond, "fp_pon", "ne")
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_jfpf"]); E(b, "fp_s")                # patch flip again: off
    a.label("fp_pon"); E(movs_imm, 0, 0); E(bl, L["jf_tg"]); E(bl, "fp_tog"); E(b, "fp_s")    # (no target first) the stock toggle: patch flip on, the engine off
    a.label("fp_np")
    E(cmp_imm, 5, P_STEP); E(b_cond, "fp_ns", "ne")
    E(cmp_imm, 7, 2); E(b_cond, "fp_son", "ne")
    E(movs_imm, 0, 0); E(bl, L["jf_tg"]); E(b, "fp_s")                                   # step flip again: off
    a.label("fp_son"); E(cmp_imm, 7, 1); E(b_cond, "fp_s1", "eq"); E(bl, "fp_tog")        # through patch flip (the engine off, as pad 26 did), then the target
    a.label("fp_s1"); E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_jfpf"]); E(mov_reg, 0, 4); E(bl, "c_fvlast"); E(bl, L["jf_tg"]); E(b, "fp_s")
    a.label("fp_ns")
    E(cmp_imm, 5, 16); E(b_cond, "fp_s", "hs")                                           # pads 19-24: nothing
    E(cmp_imm, 7, 2); E(b_cond, "fp_s", "ne")                                            # row 2 without step flip: nothing
    E(subs_imm8, 5, 8); E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 5); E(b_cond, "fp_s", "eq")   # its own track
    E(adds_imm8, 5, 1)
    E(raw, h(0x1900 | 4 << 6 | 6 << 3 | 1)); E(strb_imm, 5, 1, O_LAST)                    # adds r1, r6, r4: the last target
    E(mov_reg, 0, 5); E(bl, L["jf_tg"])
    a.label("fp_s"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    # fp_tog: pad 26's press below us (vcf21 turns the engine off, the stock toggle turns patch flip on); [sp + 4] = the view, [sp + 12] the velocity
    a.label("fp_tog")
    E(push_list, [], lr=True); E(raw, h(0x9801)); E(movs_imm, 1, PF); E(raw, h(0x9A03)); E(bl, prev["pad"]); E(pop_list, [], pc=True)   # ldr r0, [sp, #4]; ldr r2, [sp, #12]
    a.label("fp_p"); E(pop_list, [0, 1, 2, 4, 5, 6, 7]); E(raw, JS.POP_LR); E(b_w, prev["pad"])

    # ---- c_fvled (slot 7 of the template view: view) -> r0 = the LED buffer
    a.label("c_fvled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); E(b_cond, "fl_xx", "hi"); E(mov_reg, 4, 0)
    E(bl, "c_fvst"); E(mov_reg, 6, 0)
    now(0); E(ldr_imm, 1, 6, O_T); E(str_imm, 0, 6, O_T); E(subs_reg, 0, 0, 1); E(movw, 1, CLOSE_MS); E(cmp_reg, 0, 1); E(b_cond, "fv_k", "ls")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_OPEN)
    a.label("fv_k")
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(adds_imm3, 0, 4, 1); E(cmp_reg, 0, 1); E(b_cond, "fv_nr", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_OPEN); E(movs_imm, 1, 2 * 8)                   # the engine row: ours closed, pads 9-16 dark
    a.label("fv_z"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 2 * 16); E(b_cond, "fv_z", "lo")
    E(b, "fl_xx")
    a.label("fv_nr")
    E(mov_reg, 0, 4); E(bl, L["c_jfst"]); E(mov_reg, 7, 0)
    E(cmp_imm, 7, 2); E(b_cond, "fv_nsf", "ne")                                          # step flip: patch flip off if both; pad 26 blinks, pad 27 off
    E(bl, L["c_settings"]); E(cmp_imm, 0, 0); E(b_cond, "fv_nb", "eq")
    E(movs_imm, 1, 2); E(bl, S6.PARAM_GET); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 5); E(raw, h(0x1B09)); E(lsls_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "fv_nb", "ge")   # subs r1, r1, r4; bit 26 + m
    E(mov_reg, 0, 4); E(movs_imm, 1, 0); E(bl, L["c_jfpf"])
    a.label("fv_nb")
    E(mov_reg, 0, 4); E(bl, JS.CAVE); E(lsls_imm, 2, 0, 1)
    now(3); E(lsls_imm, 3, 3, 23); E(b_cond, "fv_bk", "pl"); E(adds_imm8, 2, 16)
    a.label("fv_bk"); imm32(3, JS.PAL); E(ldrh_reg, 2, 3, 2); E(strh_imm, 2, 5, 2 * PF)
    E(movs_imm, 2, JF.COL_OFF); E(strh_imm, 2, 5, 2 * MS.PAD)
    a.label("fv_nsf")
    E(adds_imm3, 1, 4, 1); E(ldrb_imm, 0, 6, O_OPEN); E(cmp_reg, 0, 1); E(b_cond, "fl_xx", "ne")
    # ---- the view open: rows 2 / 3
    E(ldrh_imm, 6, 5, 2 * PF)                                                            # r6 = pad 26's colour (patch flip's on / off, the stock toggle's)
    E(movs_imm, 0, WHITE); E(strh_imm, 0, 5, 2 * PF)
    E(movs_imm, 0, 0); E(movs_imm, 1, 2 * 8)
    a.label("fv_c"); E(strh_reg, 0, 5, 1); E(adds_imm8, 1, 2); E(cmp_imm, 1, 2 * 24); E(b_cond, "fv_c", "lo")
    E(cmp_imm, 7, 2); E(b_cond, "fv_pg", "ne"); E(movs_imm, 6, JF.COL_OFF)               # step flip: patch flip's pad dim (its bit off)
    a.label("fv_pg"); E(strh_imm, 6, 5, 2 * P_PGM)
    E(mov_reg, 0, 4); E(cmp_imm, 7, 2); E(b_cond, "fv_lt", "eq"); E(bl, "c_fvlast"); E(b, "fv_tc")
    a.label("fv_lt"); E(bl, JS.CAVE)
    a.label("fv_tc"); E(mov_reg, 6, 0); E(lsls_imm, 2, 0, 1); E(cmp_imm, 7, 2); E(b_cond, "fv_tb", "eq"); E(adds_imm8, 2, 16)
    a.label("fv_tb"); imm32(3, JS.PAL); E(ldrh_reg, 2, 3, 2); E(strh_imm, 2, 5, 2 * P_STEP)
    E(cmp_imm, 7, 2); E(b_cond, "fl_xx", "ne")
    E(movs_imm, 3, 0)                                                                    # row 2: the tracks (r6 = the target + 1)
    a.label("fv_l")
    E(lsls_imm, 1, 3, 1); E(adds_imm8, 1, 2 * 8); E(adds_imm3, 2, 3, 1); E(lsls_imm, 2, 2, 1)
    E(adds_imm3, 0, 3, 1); E(cmp_reg, 0, 6); E(b_cond, "fv_b", "eq"); E(adds_imm8, 2, 16)
    a.label("fv_b"); imm32(7, JS.PAL); E(ldrh_reg, 2, 7, 2)
    E(adds_imm3, 0, 4, 2); E(cmp_reg, 0, 3); E(b_cond, "fv_o", "ne"); E(movs_imm, 2, 0)
    a.label("fv_o"); E(strh_reg, 2, 5, 1); E(adds_imm8, 3, 1); E(cmp_imm, 3, 8); E(b_cond, "fv_l", "lo")
    a.label("fl_xx"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """hole.add, after rowswap: the outermost heads of the template view's slots 0 / 7; below them, jumpflip's previous slots (jumpflip skipped)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_settings=lab("sc06", "c_settings"), c_msheld=lab("modesel", "c_msheld"),
             c_jfst=lab("jumpflip", "c_jfst"), c_jfpf=lab("jumpflip", "c_jfpf"), jf_tg=lab("jumpflip", "jf_tg"))
    jp = {k: int(v, 16) for k, v in report["jumpflip"]["prev"].items()}
    prev = dict(pad=jp["pad"], leds=jp["leds"])
    code, labels = arm_code(base_addr, L, prev)
    n0 = len(img)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    # whoever goes on to jumpflip's slots (the vtable or the head above it: fm8ui's) goes on to ours; ours skip jumpflip
    from thumb import b_w as bw_enc, bl as bl_enc
    jl = dict(pad=lab("jumpflip", "c_jfpad"), leds=lab("jumpflip", "c_jfled"))
    ours = dict(pad=labels["c_fvpad"], leds=labels["c_fvled"])
    for k, slot in (("pad", MP.TMPL_VT), ("leds", MP.TMPL_VT + 28)):
        n = 0
        if (u(slot) & ~1) == jl[k]: struct.pack_into("<I", img, slot - BASE, ours[k] | 1); n += 1
        for at in range(0x0805CDDC, BASE + n0 - 4, 2):
            o = at - BASE
            w = bytes(img[o:o + 4])
            if w == bw_enc(at, jl[k]): img[o:o + 4] = bw_enc(at, ours[k]); n += 1
            elif w == bl_enc(at, jl[k]): img[o:o + 4] = bl_enc(at, ours[k]); n += 1
        assert n == 1, (k, n)
    return labels, code, prev
