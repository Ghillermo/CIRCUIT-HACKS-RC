"""The FM algorithm map (SC56.3 / Beta 5.48; the user, 2026-11-11: «cómo podemos mostrar de forma más clara qué hace un algoritmo FM? qué
operadores modulan a otros, relaciones armónicas... algo con pads y colores que el usuario pueda mover»; mockups fm_algorithm_pad_map_rows):

  * on the FM page (the 8-operator FM of MIDI 1 / 2, fm8ui), pad 7 held ½ s = the map until it is let go; a tap pins / unpins it (from another
    page a tap still opens the FM page); Shift + pad 7 = the algorithm list (pad 7 held before); Clear + pad 7 = the voicing, as before;
  * the map on pads 9-32 (rows 2-4): each row = whole paths leaf -> ... -> carrier read left (modulator) to right (carrier), right-aligned; paths
    share a row with at least one dark pad between them («dos ondas separadas por uno o más espacios: no interacción»); an operator on several
    paths is drawn on each; longest paths first, first fit (the 56 algorithms fit in 3 rows; what does not fit is left out);
  * colour = the ratio: integer green, x.5 teal, any other orange (inharmonic), fixed frequency red; the feedback operator violet; steady when
    its output level (feedback amount) is at least half, dim below; the picked operator pulses on every copy (the palette's pulse codes of the
    same family);
  * a tap on an operator picks it (the FM page's knobs edit it); Shift + operator = muted while the map is shown (dark, not saved); one held +
    a tap on another (any copy) = the link held -> tapped on / off = a custom algorithm (index NALG) in the patch; while one is held its targets
    are white, its sources steady, the rest dim, and the map keeps its layout until it is let go.

The custom algorithm lives in the parameters' spare bytes (saved with the patch / project like the rest, discrete for the morph): + 21 of
operator k = the operators that modulate it (bit s), GLB + 13 = feedback source | destination << 4 (15 = none), GLB + 14 = 0xC0 | N.  An
operator with no target is a carrier.  fm8arm's c_fmalg builds its 16-byte entry into the track block's + 240 (free bytes) for that index.
A link that would close a loop is refused.

RAM FMAP (free: S514D, 0x2004F4B0-0x2004F7FF): + 0 "FMM1"; track t at + 16 + 48 t: + 0..23 the drawn layout (operator + 1), + 24 mode (bit 0
pinned, bit 1 pad 7 held), + 25 the held operator + 1, + 26 pad 7's press (bit 0 ours, bit 1 was pinned, bit 2 on the FM page), + 27 the
muted operators, + 28 pad 7's press time, + 32 the last frame the map was drawn.  Scratch + 0x80 (the layout's walk).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg,  # noqa: E402
                   ldrb_w, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw,
                   str_imm, strb_imm, strb_reg, strb_w, strh_imm, strh_reg, subs_imm8, subs_reg, tst_reg, eors_reg)
import fm8 as F  # noqa: E402
import fmeng as FE  # noqa: E402
import mpatch as MP  # noqa: E402
import vcf21 as V  # noqa: E402

INV = V.INV
RET = h(0x4770)
FMAP = 0x2004F500
SIG = 0x314D4D46                                  # "FMM1"
TS, T0 = 48, 16
O_MODE, O_HELD, O_PR, O_MUTE, O_TIME, O_STAMP = 24, 25, 26, 27, 28, 32
SCR = FMAP + 0x80                                 # stk[8], nxt[8], used[3]
END = FMAP + 0x80 + 24
HOLD_MS, FRESH_MS = 500, 300
SPARE = 21                                        # an operator's + 21: the operators that modulate it (custom algorithm)
G_CFB, G_CN = 13, 14                              # GLB + 13 feedback src | dst << 4, GLB + 14 0xC0 | N
CUS = 0xC0
ENT = 240                                         # a track block's + 240: the custom algorithm's entry
FM8R, TB0 = 0x2004C600, 0x100
# colour families: (steady, dim, pulse): green, teal, orange, red, violet (palette families steady / dim / blink / pulse; red's to confirm)
FAM = [(0x17, 0x18, 0x1A), (0x4D, 0x4E, 0x50), (0x45, 0x46, 0x48), (0x53, 0x54, 0x5A), (0x49, 0x4A, 0x4C)]
WHITE = 0x01
PADNO = FE.PADNO                                  # pad 7
PAGE = FE.PAGE
assert END <= 0x2004F800


# ---------------------------------------------------------------------------------------------------------------------------- the model
def layout(entry):
    """entry (16 bytes, fm8.alg_of's) -> 24 cells (operator + 1 or 0) for pads 9-32, as the ARM draws them"""
    n, car = entry[0], entry[1]
    src = list(entry[8:16])
    grid, used, paths = [0] * 24, [0, 0, 0], []
    for c in range(8):
        if not (car >> c & 1) or c >= n: continue
        def walk(o, p):
            kids = [s for s in range(8) if src[o] >> s & 1 and s not in p and s != o]
            if not kids: paths.append(p + [o]); return
            for s in kids: walk(s, p + [o])
        walk(c, [])
    for L in range(8, 0, -1):
        for p in paths:
            if len(p) != L: continue
            for r in range(3):
                if used[r] + L <= 8:
                    for i, o in enumerate(p): grid[8 * r + 8 - used[r] - 1 - i] = o + 1
                    used[r] += L + 1
                    break
    return grid


def ratio_family(mode, crs, fine):
    if mode: return 3
    v = (100 + fine) if crs == 0 else 2 * crs * (100 + fine)
    return 0 if v % 200 == 0 else 1 if v % 100 == 0 else 2


def custom_entry(params):
    n = params[F.GLB + G_CN] & 15
    n = 8 if n > 8 else n
    full = (1 << n) - 1
    src = [params[F.OPB * k + SPARE] & full if k < n else 0 for k in range(8)]
    anymod = 0
    for s in src: anymod |= s
    fb = params[F.GLB + G_CFB]
    fs, fd = fb & 15, fb >> 4
    return bytes([n, full & ~anymod, 0xFF if fs == 15 else fs, 0xFF if fd == 15 else fd, 0, 4, full, 0] + src)


# ---------------------------------------------------------------------------------------------------------------------------- the code
LRRAM = False               # (SC56.7) c_mmled: LR in RAM while the chain below runs (the LED task's stack, issue #22)
LR_SLOT = 0x2004FAC8        # 4 B (free: after knobhold's 0x2004F900..0x2004FAA7, below 0x2004FC00)


def use_lrram():
    """SC56.7 / Beta 5.52 (fix, issue #22 of the public repository: «Beta 5.48 – Circuit Tracks crashes when opening MIDI 1/2 presets»): c_mmled
    (slot 7 of the template view = MIDI 1 / 2's Preset view) pushed 36 B before calling the chain below it, 1 804 -> 1 840 B of the LED task's
    stack in emulation (SC54 reset the unit there at 1 808).  Now LR goes to RAM (LR_SLOT) while the chain runs, the registers are pushed after."""
    global LRRAM
    LRRAM = True


def arm_code(base, L, prev, fmalg_back):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def lab(n): a.label(n)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))

    # ---- c_mmst(r0 = track) -> r0 = its state (FMAP + 16 + 48 t), the RAM set up at the first use; clobbers r1-r3
    lab("c_mmst")
    imm32(1, FMAP); E(ldr_imm, 2, 1, 0); imm32(3, SIG); E(cmp_reg, 2, 3); E(b_cond, "ms_ok", "eq")
    E(movs_imm, 2, 0); E(movs_imm, 3, (END - FMAP) // 4)
    lab("ms_z"); E(str_imm, 2, 1, 0); E(adds_imm8, 1, 4); E(subs_imm8, 3, 1); E(b_cond, "ms_z", "ne")
    imm32(1, FMAP); imm32(3, SIG); E(str_imm, 3, 1, 0)
    lab("ms_ok"); E(movs_imm, 2, TS); E(muls, 0, 2); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, T0); E(raw, RET)

    # ---- c_mmshow(r0 = track) -> r0 = 1 while the map is shown (FM page, no list, no algorithm overlay, pinned or pad 7 held); clobbers r1-r3
    lab("c_mmshow")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_fmpg"]); E(cmp_imm, 0, 0); E(b_cond, "sh_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(mov_reg, 5, 0)
    E(ldrb_w, 0, 5, L["B_P7"]); E(cmp_imm, 0, 0); E(b_cond, "sh_0", "ne")
    E(mov_reg, 0, 5); E(bl, L["c_fmovk"]); E(cmp_imm, 0, 5); E(b_cond, "sh_0", "eq")
    E(mov_reg, 0, 4); E(bl, "c_mmst"); E(ldrb_imm, 0, 0, O_MODE); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(b_cond, "sh_0", "eq")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    lab("sh_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_mmpad (slot 0 of the template view: view, pad, velocity)
    lab("c_mmpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("mp_prev", "hi"); E(mov_reg, 4, 0)
    E(cmp_imm, 5, PADNO); bc("mp_map", "ne")
    # pad 7: FM on, no CC editor, no step-drummer view, no Shift / Clear
    E(mov_reg, 0, 4); E(bl, L["c_fmact"]); E(cmp_imm, 0, 0); bc("mp_prev", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_edact"]); E(cmp_imm, 0, 0); bc("mp_prev", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_sdview"]); E(cmp_imm, 0, 0); bc("mp_prev", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); bc("mp_prev", "ne")
    E(bl, L["c_mxclrh"]); E(cmp_imm, 0, 0); bc("mp_prev", "ne")
    E(mov_reg, 0, 4); E(bl, "c_mmst"); E(mov_reg, 6, 0)
    E(movs_imm, 7, 1); E(ldrb_imm, 0, 6, O_MODE); E(movs_imm, 1, 1); E(tst_reg, 0, 1); E(b_cond, "p7_np", "eq"); E(movs_imm, 7, 3)
    lab("p7_np")
    E(mov_reg, 0, 4); E(bl, L["c_fmpg"]); E(cmp_imm, 0, 0); E(b_cond, "p7_og", "eq"); E(adds_imm8, 7, 4); E(b, "p7_st")
    lab("p7_og"); E(mov_reg, 0, 4); E(movs_imm, 1, PAGE); E(bl, L["c_vsetpage"])
    lab("p7_st"); E(strb_imm, 7, 6, O_PR)
    E(ldrb_imm, 0, 6, O_MODE); E(movs_imm, 1, 2); E(orrs_reg, 0, 1); E(strb_imm, 0, 6, O_MODE)
    now(0); E(str_imm, 0, 6, O_TIME)
    E(b, "mp_x")
    lab("mp_map")                                                                        # pads 9-32 while the map is shown
    E(cmp_imm, 5, 8); bc("mp_prev", "lo"); E(cmp_imm, 5, 31); bc("mp_prev", "hi")
    E(mov_reg, 0, 4); E(bl, "c_mmshow"); E(cmp_imm, 0, 0); bc("mp_prev", "eq")
    E(mov_reg, 0, 4); E(bl, "c_mmst"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(ldrb_reg, 7, 6, 0); E(cmp_imm, 7, 0); bc("mp_x", "eq")    # r7 = operator + 1
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "mp_ns", "eq")
    E(subs_imm8, 7, 1); E(movs_imm, 0, 1); E(lsls_reg, 0, 7); E(ldrb_imm, 1, 6, O_MUTE); E(eors_reg, 1, 0); E(strb_imm, 1, 6, O_MUTE); E(b, "mp_x")
    lab("mp_ns")
    E(ldrb_imm, 0, 6, O_HELD); E(cmp_imm, 0, 0); E(b_cond, "mp_lk", "ne")
    E(strb_imm, 7, 6, O_HELD)                                                            # the first: held and picked
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(subs_imm8, 7, 1); E(strb_w, 7, 0, L["B_SEL"]); E(b, "mp_x")
    lab("mp_lk"); E(cmp_reg, 0, 7); E(b_cond, "mp_x", "eq")                              # another: the link held -> tapped
    E(subs_imm8, 0, 1); E(mov_reg, 1, 0); E(subs_imm8, 7, 1); E(mov_reg, 2, 7); E(mov_reg, 0, 4); E(bl, "c_mmlink")
    lab("mp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    lab("mp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_mmrel (slot 1 of the template view: view, pad)
    lab("c_mmrel")
    E(push_list, [0, 1, 2, 4, 5, 6], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("mr_prev", "hi"); E(mov_reg, 4, 0)
    E(bl, "c_mmst"); E(mov_reg, 6, 0)
    E(cmp_imm, 5, PADNO); E(b_cond, "mr_map", "ne")
    E(ldrb_imm, 2, 6, O_PR); E(movs_imm, 0, 1); E(tst_reg, 2, 0); bc("mr_prev", "eq")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_PR)
    E(ldrb_imm, 1, 6, O_MODE); E(movs_imm, 0, 2); E(bics_reg, 1, 0)                       # pad 7 no longer held
    now(0); E(ldr_imm, 3, 6, O_TIME); E(subs_reg, 0, 0, 3); imm32(3, HOLD_MS); E(cmp_reg, 0, 3); E(b_cond, "mr_w", "hs")
    E(movs_imm, 0, 2); E(tst_reg, 2, 0); E(b_cond, "mr_pin", "eq")                       # a tap: pinned -> off
    E(movs_imm, 0, 1); E(bics_reg, 1, 0); E(b, "mr_w")
    lab("mr_pin"); E(movs_imm, 0, 4); E(tst_reg, 2, 0); E(b_cond, "mr_w", "eq"); E(movs_imm, 0, 1); E(orrs_reg, 1, 0)    # on the FM page: pinned
    lab("mr_w"); E(strb_imm, 1, 6, O_MODE); E(b, "mr_prev")
    lab("mr_map")
    E(ldrb_imm, 1, 6, O_HELD); E(cmp_imm, 1, 0); bc("mr_prev", "eq")
    E(cmp_imm, 5, 8); bc("mr_prev", "lo"); E(cmp_imm, 5, 31); bc("mr_prev", "hi")
    E(mov_reg, 0, 5); E(subs_imm8, 0, 8); E(ldrb_reg, 0, 6, 0); E(cmp_reg, 0, 1); bc("mr_x", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HELD)
    lab("mr_x"); E(pop_list, [0, 1, 2, 4, 5, 6], pc=True)
    lab("mr_prev"); E(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); E(b_w, prev["rel"])

    # ---- c_mmlink(r0 = track, r1 = a, r2 = b): a modulates b on / off (a custom algorithm; a loop refused); clobbers r0-r3
    lab("c_mmlink")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 6, 1); E(mov_reg, 7, 2)
    E(bl, L["c_fmblk"]); E(mov_reg, 4, 0); E(bl, L["c_fmalg"]); E(mov_reg, 5, 0)        # r4 = block, r5 = its entry
    E(ldrb_imm, 0, 5, 0); E(cmp_reg, 6, 0); bc("lk_x", "hs"); E(cmp_reg, 7, 0); bc("lk_x", "hs"); E(cmp_reg, 6, 7); bc("lk_x", "eq")
    E(ldrb_w, 1, 4, F.GLB + F.G_ALG); E(cmp_imm, 1, F.NALG); E(b_cond, "lk_cv", "ne")
    E(ldrb_w, 1, 4, F.GLB + G_CN); E(lsrs_imm, 1, 1, 4); E(cmp_imm, 1, CUS >> 4); E(b_cond, "lk_ed", "eq")
    lab("lk_cv")                                                                         # to the custom algorithm: the entry's routing
    E(movs_imm, 1, 0)
    lab("lk_cl"); E(adds_imm8, 1, 8); E(ldrb_reg, 2, 5, 1); E(subs_imm8, 1, 8)
    E(movs_imm, 3, F.OPB); E(muls, 3, 1); E(adds_reg, 3, 3, 4); E(strb_imm, 2, 3, SPARE)
    E(adds_imm8, 1, 1); E(cmp_imm, 1, 8); E(b_cond, "lk_cl", "lo")
    E(ldrb_imm, 1, 5, F.A_FBS); E(cmp_imm, 1, 15); E(b_cond, "lk_f1", "ls"); E(movs_imm, 1, 15)
    lab("lk_f1"); E(ldrb_imm, 2, 5, F.A_FBD); E(cmp_imm, 2, 15); E(b_cond, "lk_f2", "ls"); E(movs_imm, 2, 15)
    lab("lk_f2"); E(lsls_imm, 2, 2, 4); E(orrs_reg, 1, 2); E(strb_w, 1, 4, F.GLB + G_CFB)
    E(ldrb_imm, 1, 5, 0); E(movs_imm, 2, CUS); E(orrs_reg, 1, 2); E(strb_w, 1, 4, F.GLB + G_CN)
    E(movs_imm, 1, F.NALG); E(strb_w, 1, 4, F.GLB + F.G_ALG)
    lab("lk_ed")
    E(movs_imm, 0, F.OPB); E(muls, 0, 7); E(adds_reg, 5, 0, 4)                            # r5 = b's parameters
    E(ldrb_imm, 1, 5, SPARE); E(movs_imm, 2, 1); E(lsls_reg, 2, 6); E(tst_reg, 1, 2); E(b_cond, "lk_on", "eq")
    E(bics_reg, 1, 2); E(strb_imm, 1, 5, SPARE); E(b, "lk_d")                            # on -> off
    lab("lk_on")                                                                         # a loop? reach = what b reaches downstream
    E(movs_imm, 2, 1); E(lsls_reg, 2, 7); E(movs_imm, 3, 8)                              # r2 = reach, r3 = passes
    lab("lk_p"); E(movs_imm, 0, 0)
    lab("lk_j"); E(push_list, [3]); E(movs_imm, 3, F.OPB); E(muls, 3, 0); E(adds_reg, 3, 3, 4); E(ldrb_imm, 3, 3, SPARE)
    E(tst_reg, 3, 2); E(pop_list, [3]); E(b_cond, "lk_jn", "eq")
    E(push_list, [3]); E(movs_imm, 3, 1); E(lsls_reg, 3, 0); E(orrs_reg, 2, 3); E(pop_list, [3])
    lab("lk_jn"); E(adds_imm8, 0, 1); E(cmp_imm, 0, 8); E(b_cond, "lk_j", "lo")
    E(subs_imm8, 3, 1); E(b_cond, "lk_p", "ne")
    E(lsrs_reg, 2, 6); E(movs_imm, 3, 1); E(tst_reg, 2, 3); bc("lk_x", "ne")             # a reaches b's targets: refused
    E(movs_imm, 2, 1); E(lsls_reg, 2, 6); E(orrs_reg, 1, 2); E(strb_imm, 1, 5, SPARE)
    lab("lk_d"); E(movs_imm, 0, 1); E(strb_w, 0, 4, L["B_DIRTY"])
    lab("lk_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_mcalg (the head of fm8arm's c_fmalg, r0 = block): the custom algorithm's entry (block + 240); clobbers r1
    lab("c_mcalg")
    E(ldrb_w, 1, 0, F.GLB + F.G_ALG); E(cmp_imm, 1, F.NALG); E(b_cond, "ca_c", "eq")
    lab("ca_back"); E(mov_reg, 0, 1); E(b_w, fmalg_back)
    lab("ca_c")
    E(ldrb_w, 1, 0, F.GLB + G_CN); E(lsrs_imm, 1, 1, 4); E(cmp_imm, 1, CUS >> 4); E(b_cond, "ca_ok", "eq")
    lab("ca_0"); E(movs_imm, 1, 0); E(b, "ca_back")
    lab("ca_ok")
    imm32(1, FM8R + TB0); E(cmp_reg, 0, 1); E(b_cond, "ca_0", "lo"); imm32(1, FM8R + TB0 + 0x200); E(cmp_reg, 0, 1); E(b_cond, "ca_0", "hs")
    E(push_list, [2, 3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(movs_imm, 5, ENT); E(adds_reg, 5, 5, 4)                           # r4 = block, r5 = the entry
    E(ldrb_w, 6, 4, F.GLB + G_CN); E(movs_imm, 1, 15); E(ands_reg, 6, 1); E(cmp_imm, 6, 8); E(b_cond, "ca_n", "ls"); E(movs_imm, 6, 8)
    lab("ca_n"); E(strb_imm, 6, 5, 0)                                                    # r6 = N
    E(movs_imm, 7, 1); E(lsls_reg, 7, 6); E(subs_imm8, 7, 1)                              # r7 = full
    E(movs_imm, 2, 0); E(movs_imm, 3, 0)                                                  # r2 = k, r3 = any modulator
    lab("ca_k"); E(movs_imm, 0, 0); E(cmp_reg, 2, 6); E(b_cond, "ca_kw", "hs")
    E(movs_imm, 0, F.OPB); E(muls, 0, 2); E(adds_reg, 0, 0, 4); E(ldrb_imm, 0, 0, SPARE); E(ands_reg, 0, 7); E(orrs_reg, 3, 0)
    lab("ca_kw"); E(adds_imm8, 2, 8); E(strb_reg, 0, 5, 2); E(subs_imm8, 2, 8); E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "ca_k", "lo")
    E(mov_reg, 0, 7); E(bics_reg, 0, 3); E(strb_imm, 0, 5, F.A_CAR); E(strb_imm, 7, 5, F.A_USED)
    E(ldrb_w, 0, 4, F.GLB + G_CFB); E(movs_imm, 1, 15); E(ands_reg, 1, 0); E(cmp_imm, 1, 15); E(b_cond, "ca_s", "ne"); E(movs_imm, 1, 0xFF)
    lab("ca_s"); E(strb_imm, 1, 5, F.A_FBS); E(lsrs_imm, 1, 0, 4); E(cmp_imm, 1, 15); E(b_cond, "ca_d", "ne"); E(movs_imm, 1, 0xFF)
    lab("ca_d"); E(strb_imm, 1, 5, F.A_FBD)
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, F.A_NZ); E(strb_imm, 0, 5, 7); E(movs_imm, 0, 4); E(strb_imm, 0, 5, F.A_FAM)
    E(mov_reg, 0, 5); E(pop_list, [2, 3, 4, 5, 6, 7], pc=True)

    # ---- c_mmol (in fm8arm's operator loop, instead of "ldrb r2, [r1, #O_OL]; cmp r2, #0"; r1 = the operator, r5 = block, r8 = k):
    #      r2 = its output level, 0 while it is muted on a shown map; the flags of cmp r2, #0; clobbers r0, r3
    lab("c_mmol")
    E(ldrb_imm, 2, 1, F.O_OL)
    imm32(0, FM8R + TB0); E(mov_reg, 3, 5); E(subs_reg, 3, 3, 0); E(lsrs_imm, 3, 3, 8); E(cmp_imm, 3, 1); E(b_cond, "ol_x", "hi")
    imm32(0, FMAP); E(ldr_imm, 0, 0, 0); E(push_list, [1]); imm32(1, SIG); E(cmp_reg, 0, 1); E(pop_list, [1]); E(b_cond, "ol_x", "ne")
    E(movs_imm, 0, TS); E(muls, 3, 0); imm32(0, FMAP + T0); E(adds_reg, 3, 3, 0)          # r3 = the track's state
    E(ldrb_imm, 0, 3, O_MUTE); E(push_list, [1]); E(mov_reg, 1, 8); E(lsrs_reg, 0, 1); E(pop_list, [1]); E(lsrs_imm, 0, 0, 1); E(b_cond, "ol_x", "cc")
    E(ldr_imm, 3, 3, O_STAMP); now(0); E(subs_reg, 0, 0, 3); imm32(3, FRESH_MS); E(cmp_reg, 0, 3); E(b_cond, "ol_x", "hs")
    E(movs_imm, 2, 0)
    lab("ol_x"); E(cmp_imm, 2, 0); E(raw, RET)

    # ---- c_mmlay(r0 = track, r1 = state): the layout of its algorithm into the state's 24 cells; clobbers r0-r3
    #      r4 = state, r5 = entry, r6 = SCR, r7 = depth, r8 = in path, r9 = L, r10 = carrier, r11 = visits
    lab("c_mmlay")
    E(raw, h(0xE92D) + h(0x4FF0))                                                        # push.w {r4-r11, lr}
    E(mov_reg, 4, 1); E(bl, L["c_fmblk"]); E(bl, L["c_fmalg"]); E(mov_reg, 5, 0); imm32(6, SCR)
    E(movs_imm, 0, 0); E(movs_imm, 1, 0)
    lab("ly_z"); E(strb_reg, 0, 4, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, 24); E(b_cond, "ly_z", "lo")
    E(strb_imm, 0, 6, 16); E(strb_imm, 0, 6, 17); E(strb_imm, 0, 6, 18)
    E(movs_imm, 0, 8); E(mov_reg, 9, 0)
    lab("ly_L")
    E(movs_imm, 0, 0); E(mov_reg, 10, 0)
    lab("ly_c")
    E(mov_reg, 0, 10); E(ldrb_imm, 1, 5, 0); E(cmp_reg, 0, 1); bc("ly_cn", "hs")
    E(ldrb_imm, 1, 5, F.A_CAR); E(lsrs_reg, 1, 0); E(lsrs_imm, 1, 1, 1); bc("ly_cn", "cc")
    E(strb_imm, 0, 6, 0); E(movs_imm, 1, 0); E(strb_imm, 1, 6, 8); E(movs_imm, 7, 0)     # stk[0] = c, nxt[0] = 0, depth 0
    E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(mov_reg, 8, 1)                                 # in path
    E(movs_imm, 1, 0); E(mov_reg, 11, 1)
    E(adds_imm8, 0, 8); E(ldrb_reg, 1, 5, 0); E(mov_reg, 2, 8); E(bics_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "ly_lp", "ne")
    E(bl, "c_mmemit"); E(b, "ly_cn")                                                   # a lone carrier
    lab("ly_lp")
    E(mov_reg, 0, 11); E(adds_imm8, 0, 1); E(mov_reg, 11, 0); E(cmp_imm, 0, 255); bc("ly_cn", "hs")
    E(ldrb_reg, 0, 6, 7); E(adds_imm8, 0, 8); E(ldrb_reg, 1, 5, 0); E(mov_reg, 2, 8); E(bics_reg, 1, 2)     # r1 = avail of stk[d]
    E(adds_imm8, 7, 8); E(ldrb_reg, 2, 6, 7); E(subs_imm8, 7, 8)                          # r2 = nxt[d]
    lab("ly_f"); E(cmp_imm, 2, 8); E(b_cond, "ly_pop", "hs")
    E(mov_reg, 0, 1); E(lsrs_reg, 0, 2); E(lsrs_imm, 0, 0, 1); E(b_cond, "ly_got", "cs"); E(adds_imm8, 2, 1); E(b, "ly_f")
    lab("ly_got")
    E(adds_imm8, 2, 1); E(adds_imm8, 7, 8); E(strb_reg, 2, 6, 7); E(subs_imm8, 7, 8); E(subs_imm8, 2, 1)    # nxt[d] = s + 1
    E(adds_imm8, 7, 1); E(strb_reg, 2, 6, 7); E(movs_imm, 0, 0); E(adds_imm8, 7, 8); E(strb_reg, 0, 6, 7); E(subs_imm8, 7, 8)
    E(movs_imm, 0, 1); E(lsls_reg, 0, 2); E(mov_reg, 1, 8); E(orrs_reg, 1, 0); E(mov_reg, 8, 1)
    E(mov_reg, 0, 2); E(adds_imm8, 0, 8); E(ldrb_reg, 0, 5, 0); E(bics_reg, 0, 1); E(cmp_imm, 0, 0); bc("ly_lp", "ne")
    E(bl, "c_mmemit")                                                                      # a leaf: emitted, then popped
    lab("ly_pop")
    E(ldrb_reg, 0, 6, 7); E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(mov_reg, 0, 8); E(bics_reg, 0, 1); E(mov_reg, 8, 0)
    E(cmp_imm, 7, 0); E(b_cond, "ly_cn", "eq"); E(subs_imm8, 7, 1); E(b, "ly_lp")
    lab("ly_cn")
    E(mov_reg, 0, 10); E(adds_imm8, 0, 1); E(mov_reg, 10, 0); E(cmp_imm, 0, 8); bc("ly_c", "lo")
    E(mov_reg, 0, 9); E(subs_imm8, 0, 1); E(mov_reg, 9, 0); bc("ly_L", "ne")
    E(raw, h(0xE8BD) + h(0x8FF0))                                                        # pop.w {r4-r11, pc}

    # ---- c_mmemit (from c_mmlay: the path stk[0..r7], length r7 + 1): placed when its length is r9 (first fit); clobbers r0-r3
    lab("c_mmemit")
    E(push_list, [7], lr=True)
    E(adds_imm8, 7, 1); E(cmp_reg, 7, 9); E(b_cond, "em_x", "ne")                          # r7 = length
    E(movs_imm, 3, 0)
    lab("em_r"); E(adds_imm8, 3, 16); E(ldrb_reg, 2, 6, 3); E(subs_imm8, 3, 16)            # r2 = used[r]
    E(adds_reg, 0, 2, 7); E(cmp_imm, 0, 8); E(b_cond, "em_put", "ls")
    E(adds_imm8, 3, 1); E(cmp_imm, 3, 3); E(b_cond, "em_r", "lo"); E(b, "em_x")
    lab("em_put")
    E(adds_imm8, 0, 1); E(adds_imm8, 3, 16); E(strb_reg, 0, 6, 3); E(subs_imm8, 3, 16)    # used[r] += L + 1
    E(lsls_imm, 3, 3, 3); E(adds_imm8, 3, 7); E(subs_reg, 3, 3, 2)                         # r3 = 8 r + 7 - used: the carrier's cell
    E(movs_imm, 1, 0)
    lab("em_i"); E(ldrb_reg, 0, 6, 1); E(adds_imm8, 0, 1); E(strb_reg, 0, 4, 3); E(subs_imm8, 3, 1)
    E(adds_imm8, 1, 1); E(cmp_reg, 1, 7); E(b_cond, "em_i", "lo")
    lab("em_x"); E(pop_list, [7], pc=True)

    # ---- c_mmled (slot 7 of the template view: view) -> r0 = the LED buffer; the map over pads 9-32, pad 7 bright
    lab("c_mmled")
    if LRRAM:
        imm32(1, LR_SLOT); E(raw, h(0xF8C1) + h(0xE000))                                  # str.w lr, [r1]
        E(bl, prev["leds"]); E(raw, h(0xE92D) + h(0x0FF0)); E(mov_reg, 5, 0)                # push.w {r4-r11}
    else:
        E(raw, h(0xE92D) + h(0x4FF0))
        E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("le_x", "hi"); E(mov_reg, 4, 0)
    E(bl, "c_mmst"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, "c_mmshow"); E(cmp_imm, 0, 0); E(b_cond, "le_on", "ne")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_HELD); E(strb_imm, 0, 6, O_MUTE); E(b, "le_x")
    lab("le_on")
    now(0); E(ldr_imm, 1, 6, O_STAMP); E(str_imm, 0, 6, O_STAMP); E(subs_reg, 0, 0, 1); imm32(1, FRESH_MS); E(cmp_reg, 0, 1); E(b_cond, "le_fr", "lo")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, O_MUTE)                                        # back after a while: nothing muted
    lab("le_fr")
    E(ldrb_imm, 0, 6, O_HELD); E(cmp_imm, 0, 0); E(b_cond, "le_nl", "ne")
    E(mov_reg, 0, 4); E(mov_reg, 1, 6); E(bl, "c_mmlay")
    lab("le_nl")
    E(movs_imm, 0, FE.COL_FM[0]); E(strh_imm, 0, 5, 2 * PADNO)
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(mov_reg, 7, 0); E(bl, L["c_fmalg"]); E(mov_reg, 8, 0)    # r7 = block, r8 = entry
    E(movs_imm, 0, 0); E(mov_reg, 9, 0)                                                   # r9 = cell
    lab("le_c")
    E(mov_reg, 1, 9); E(ldrb_reg, 0, 6, 1); E(movs_imm, 3, 0); E(cmp_imm, 0, 0); bc("le_w", "eq")
    E(subs_imm8, 0, 1); E(mov_reg, 10, 0)                                                 # r10 = o
    E(ldrb_imm, 1, 6, O_MUTE); E(lsrs_reg, 1, 0); E(lsrs_imm, 1, 1, 1); bc("le_w", "cs")   # muted: dark
    # the family (r2 = 3 x family) and the level (r11 = 1 when at least half)
    E(mov_reg, 1, 8); E(ldrb_imm, 1, 1, F.A_FBS); E(cmp_reg, 1, 0); E(b_cond, "le_rt", "ne")
    E(movs_imm, 2, 12); E(ldrb_w, 1, 7, F.GLB + F.G_FB); E(cmp_imm, 1, 64); E(b, "le_lv")
    lab("le_rt")
    E(movs_imm, 1, F.OPB); E(muls, 1, 0); E(adds_reg, 1, 1, 7)                            # r1 = the operator's parameters
    E(movs_imm, 2, 9); E(ldrb_imm, 3, 1, F.O_MODE); E(cmp_imm, 3, 0); E(b_cond, "le_ol", "ne")
    E(ldrb_imm, 2, 1, F.O_FINE); E(adds_imm8, 2, 100); E(ldrb_imm, 3, 1, F.O_CRS); E(cmp_imm, 3, 0); E(b_cond, "le_v", "eq")
    E(lsls_imm, 3, 3, 1); E(muls, 2, 3)
    lab("le_v")                                                                          # r2 = 200 x ratio: % 200 green, % 100 teal, else orange
    E(movs_imm, 3, 200); E(raw, udiv(0, 2, 3)); E(muls, 0, 3); E(subs_reg, 0, 2, 0); E(movs_imm, 3, 0); E(cmp_imm, 0, 0); E(b_cond, "le_f", "eq")
    E(movs_imm, 3, 3); E(cmp_imm, 0, 100); E(b_cond, "le_f", "eq"); E(movs_imm, 3, 6)
    lab("le_f"); E(mov_reg, 2, 3)
    lab("le_ol"); E(ldrb_imm, 3, 1, F.O_OL); E(cmp_imm, 3, 50)
    lab("le_lv"); E(movs_imm, 3, 0); E(b_cond, "le_l0", "lo"); E(movs_imm, 3, 1)
    lab("le_l0"); E(mov_reg, 11, 3)
    E(ldrb_imm, 1, 6, O_HELD); E(cmp_imm, 1, 0); E(b_cond, "le_sel", "eq")
    E(subs_imm8, 1, 1); E(mov_reg, 0, 10); E(cmp_reg, 0, 1); E(b_cond, "le_pu", "eq")      # the held one: pulse
    E(mov_reg, 3, 8); E(adds_reg, 3, 3, 0); E(ldrb_imm, 3, 3, 8); E(lsrs_reg, 3, 1); E(lsrs_imm, 3, 3, 1); E(b_cond, "le_wh", "cs")   # its target: white
    E(mov_reg, 3, 8); E(adds_reg, 3, 3, 1); E(ldrb_imm, 3, 3, 8); E(lsrs_reg, 3, 0); E(lsrs_imm, 3, 3, 1); E(b_cond, "le_tb", "cs")   # its source: steady
    E(b, "le_dm")
    lab("le_sel"); E(ldrb_w, 1, 7, L["B_SEL"]); E(mov_reg, 0, 10); E(cmp_reg, 0, 1); E(b_cond, "le_pu", "eq")   # the picked one: pulse
    E(mov_reg, 0, 11); E(cmp_imm, 0, 0); E(b_cond, "le_tb", "ne")
    lab("le_dm"); E(adds_imm8, 2, 1); E(b, "le_tb")
    lab("le_pu"); E(adds_imm8, 2, 2); E(b, "le_tb")
    lab("le_wh"); E(movs_imm, 3, WHITE); E(b, "le_w")
    lab("le_tb"); E(movs_imm, 3, 0)                                                      # r3 = FAM[r2]
    for i, code in enumerate(c_ for fam in FAM for c_ in fam):
        E(cmp_imm, 2, i); E(b_cond, f"le_t{i}", "ne"); E(movs_imm, 3, code); lab(f"le_t{i}")
    lab("le_w"); E(mov_reg, 0, 9); E(adds_imm8, 0, 8); E(lsls_imm, 0, 0, 1); E(strh_reg, 3, 5, 0)
    E(mov_reg, 0, 9); E(adds_imm8, 0, 1); E(mov_reg, 9, 0); E(cmp_imm, 0, 24); bc("le_c", "lo")
    lab("le_x"); E(mov_reg, 0, 5)
    if LRRAM: E(raw, h(0xE8BD) + h(0x0FF0)); imm32(1, LR_SLOT); E(raw, h(0xF8D1) + h(0xF000))  # pop.w {r4-r11}; ldr.w pc, [r1]
    else: E(raw, h(0xE8BD) + h(0x8FF0))
    return a.assemble()


def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)


def _find(img, lo, hi, pat):
    import ct_fw
    BASE = ct_fw.APP_BASE
    at = [i for i in range(lo - BASE, hi - BASE, 2) if img[i:i + len(pat)] == pat]
    assert len(at) == 1, (hex(lo), [hex(x + BASE) for x in at])
    return at[0] + BASE


def install(img, report, base_addr):
    """dspz.add, after every other head of the template view: its slots 0 / 1 / 7; fm8arm's c_fmalg and the operator loop's level read."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    import fm8arm as FA
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_shift=lab("sc15", "c_shift"), c_mxclrh=lab("modmx", "c_mxclrh"),
             c_vsetpage=lab("vcf20", "c_vsetpage"), c_edact=lab("vcf20", "c_edact"), c_sdview=lab("vcf20", "c_sdview"),
             B_P7=FA.B_P7, B_SEL=FA.B_SEL, B_DIRTY=FA.B_DIRTY)
    for k in ("c_fmpg", "c_fmblk", "c_fmovk", "c_fmact", "c_fmalg", "c_fm8run"): L[k] = lab("fm8", k)
    assert FA.FM8R == FM8R and FA.TB0 == TB0
    al = L["c_fmalg"]
    ins = bytes(img[al - BASE:al - BASE + 4])
    assert ins == bytes(h(0xF890) + h(0x0000 | F.GLB + F.G_ALG)), ins.hex()                 # ldrb.w r0, [r0, #200]
    run = L["c_fm8run"]
    olr = _find(img, run, run + 0x400, h(0x7C0A) + h(0x2A00))                              # ldrb r2, [r1, #16]; cmp r2, #0
    TP = MP.TMPL_VT
    prev = dict(pad=u(TP) & ~1, rel=u(TP + 4) & ~1, leds=u(TP + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev, al + 4)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[al - BASE:al - BASE + 4] = b_w(al, labels["c_mcalg"])
    img[olr - BASE:olr - BASE + 4] = bl(olr, labels["c_mmol"])
    struct.pack_into("<I", img, TP - BASE, labels["c_mmpad"] | 1)
    struct.pack_into("<I", img, TP + 4 - BASE, labels["c_mmrel"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_mmled"] | 1)
    prev.update(fmalg=al, olread=olr)
    return labels, code, prev
