"""SC45 (the user, 2026-10-19: «En selector de modo sinte midi (pad 27) tras un toque, abrir vista en row 3 con opciones (mantener colores) tocar el
pad 27 otra vez cierra la vista y recupera lista de parches»; with him: choosing a mode leaves the view open): the own engine's modes of MIDI 1 / 2
on a row.

The MIDI Preset view (the template view, mpatch.TMPL_VT): pad 27 alone (no Shift / Clear / Duplicate) opens / closes the mode row instead of
stepping to the next mode (vcf21's vp_tri: off -> line in -> oscillator -> VA-drum -> granular -> sample -> FX sequencer -> off).  While open:
  * pads 17-23 = the seven modes in that order, in the colours pad 27 shows for each (off = dim white), the current one bright, the others dim;
    a press = that mode: vp_tri is run (the previous slot 0, pad 27) until the mode is the chosen one, so every mode is set as the stock cycle sets
    it (the page, the patch flip, the step-drummer of the FX sequencer, the settings save);
  * pads 9-16 and 24 dark, their presses swallowed (they would load patches); pad 27 another time closes the row and the patches come back;
  * the row closes by itself when the view's LEDs have not been asked for in CLOSE_MS (another view).
The mode now = c_von, the oscillator source (c_vflag bit 2), the VA-drum bits (c_vdbit t / t + 2): off; line in (no oscillator, no bits);
oscillator; VA-drum (oscillator + bit t); granular (oscillator + bit t + 2); sample (no oscillator, bit t + 2); FX sequencer (no oscillator, bit t).
RAM: modmx.MXR + 0x1A0: + 0 the open track + 1 (0 = closed), + 4 the time of the last LED call."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, strh_reg, subs_reg)
import vcf21 as V  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402

RAM = MX.MXR + 0x1A0
PAD = 26                                  # pad 27
ROW = 16                                  # pads 17-23: the modes
CLOSE_MS = 300
COLS = ((0x01, 0x02), (0x2B, 0x2C), (0x17, 0x18), (0x45, 0x46), (0x32, 0x37), (0x4D, 0x4E), (0x09, 0x0A))   # bright / dim per mode
INV = V.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    a.label("ms_cols"); E(raw, bytes(c for pair in COLS for c in pair))

    # ---- c_msmode(r0 = track 0 / 1) -> r0 = the mode 0..6; clobbers r1-r3
    a.label("c_msmode")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "mm_0", "eq")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 2); E(bl, L["c_vdbit"]); E(mov_reg, 5, 0)          # r5 = bit t + 2
    E(mov_reg, 0, 4); E(movs_imm, 1, 2); E(bl, L["c_vflag"]); E(cmp_imm, 0, 0); E(b_cond, "mm_no", "eq")
    E(cmp_imm, 5, 0); E(b_cond, "mm_4", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vdbit"]); E(cmp_imm, 0, 0); E(b_cond, "mm_3", "ne")
    E(movs_imm, 0, 2); E(pop_list, [4, 5], pc=True)
    a.label("mm_no")
    E(cmp_imm, 5, 0); E(b_cond, "mm_5", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_vdbit"]); E(cmp_imm, 0, 0); E(b_cond, "mm_6", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    for lab, v in (("mm_0", 0), ("mm_3", 3), ("mm_4", 4), ("mm_5", 5), ("mm_6", 6)):
        a.label(lab); E(movs_imm, 0, v); E(pop_list, [4, 5], pc=True)

    # ---- c_msheld() -> r0 = Shift, Clear or Duplicate held (any); clobbers r1-r3
    a.label("c_msheld")
    E(push_list, [], lr=True)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mh_x", "ne")
    imm32(0, MP.MGR); E(ldr_imm, 0, 0, 0x20); E(ldr_imm, 0, 0, 0xC); E(movs_imm, 1, 0); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(movs_imm, 1, 3); E(raw, h(0x4008))                                                     # ands r0, r1: Clear / Duplicate
    a.label("mh_x"); E(pop_list, [], pc=True)

    # ---- c_mspad (slot 0 of the template view: view, pad, velocity)
    a.label("c_mspad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("sp_prev", "hi"); E(mov_reg, 4, 0)            # r4 = the track
    imm32(6, RAM); E(ldrb_imm, 7, 6, 0)                                                      # r7 = the open track + 1
    E(cmp_imm, 5, PAD); E(b_cond, "sp_nt", "ne")
    E(bl, "c_msheld"); E(cmp_imm, 0, 0); bc("sp_prev", "ne")
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 7, 0); E(b_cond, "sp_cl", "eq")        # open for this track: close
    E(strb_imm, 0, 6, 0); now(1); E(str_imm, 1, 6, 4); E(b, "sp_x")
    a.label("sp_cl"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "sp_x")
    a.label("sp_nt")                                                                          # another pad: only while open for this track
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 7, 0); bc("sp_prev", "ne")
    E(cmp_imm, 5, 8); bc("sp_prev", "lo"); E(cmp_imm, 5, 23); bc("sp_prev", "hi")
    E(cmp_imm, 5, ROW); E(b_cond, "sp_x", "lo"); E(cmp_imm, 5, ROW + 6); E(b_cond, "sp_x", "hi")
    E(movs_imm, 0, ROW); E(subs_reg, 5, 5, 0)                                                # r5 = the chosen mode
    E(movs_imm, 7, 8)                                                                         # at most 7 steps of the cycle
    a.label("sp_l")
    E(mov_reg, 0, 4); E(bl, "c_msmode"); E(cmp_reg, 0, 5); E(b_cond, "sp_x", "eq")
    E(raw, h(0x9800)); E(movs_imm, 1, PAD); E(raw, h(0x9A02)); E(bl, prev["pad"])          # ldr r0, [sp]; ldr r2, [sp, #8]: the view, its velocity
    E(raw, h(0x3F01)); E(b_cond, "sp_l", "ne")                                               # subs r7, #1
    a.label("sp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("sp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_msleds (slot 7 of the template view: view) -> r0 = the LED buffer: the mode row while open
    a.label("c_msleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("ml_x", "hi"); E(mov_reg, 4, 0)
    imm32(6, RAM); E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, 0); bc("ml_x", "eq")
    E(ldr_imm, 1, 6, 4); now(2); E(str_imm, 2, 6, 4); E(raw, h(0x1A52))                     # subs r2, r2, r1: since the last call
    imm32(1, CLOSE_MS); E(cmp_reg, 2, 1); E(b_cond, "ml_go", "ls")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "ml_x")                                   # not shown for a while: closed
    a.label("ml_go")
    E(raw, h(0x3801)); E(cmp_reg, 0, 4); bc("ml_x", "ne")                                   # subs r0, #1: open for this track?
    E(movs_imm, 1, 0); E(movs_imm, 2, 8)
    a.label("ml_d"); E(lsls_imm, 3, 2, 1); E(strh_reg, 1, 5, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 24); E(b_cond, "ml_d", "lo")
    E(mov_reg, 0, 4); E(bl, "c_msmode"); E(mov_reg, 6, 0); E(movs_imm, 7, 0)
    a.label("ml_m")
    imm32(1, base); E(lsls_imm, 2, 7, 1); E(adds_reg, 1, 1, 2); E(ldrb_imm, 2, 1, 1); E(cmp_reg, 7, 6); E(b_cond, "ml_c", "ne"); E(ldrb_imm, 2, 1, 0)
    a.label("ml_c"); E(movs_imm, 3, ROW); E(adds_reg, 3, 3, 7); E(lsls_imm, 3, 3, 1); E(strh_reg, 2, 5, 3)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 7); E(b_cond, "ml_m", "lo")
    a.label("ml_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add); the heads of slots 0 / 7 of the template view."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_vflag", "c_vdbit")}
    L["c_shift"] = lab("sc15", "c_shift")
    L["c_mpon"] = lab("mpatch", "c_mpon")
    TP = MP.TMPL_VT
    prev = dict(pad=u(TP) & ~1, leds=u(TP + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, TP - BASE, labels["c_mspad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_msleds"] | 1)
    return labels, code, prev
