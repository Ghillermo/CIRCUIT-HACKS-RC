"""SC47.5 (the user, 2026-10-26: «implementa portamento. asigna el toggle al pad 32, sin shift: retrig/legato/portamento/poly/unison. con un
desplegable como el modo de voz»): the voice mode of the own synth of MIDI 1 / 2 on a row, like the engines' row of pad 27 (modesel).

The MIDI Preset view (the template view, mpatch.TMPL_VT), with the engine on:
  * pad 32 alone (no Shift / Clear / Duplicate) opens / closes the row; it shows the current mode's colour (green retrigger, yellow legato, cyan
    portamento, magenta poly, orange unison);
  * while open: pads 17-21 = the five modes (the current one bright, the others dim); a press = that mode (poly.c_vmset); pads 9-16 and 22-24 dark,
    their presses swallowed (they would load patches); pad 27 closes ours and opens the engines'; the row closes by itself when the view's LEDs
    have not been asked for in CLOSE_MS (another view);
  * while open: K1 = the portamento's time (cyan, 0 = none .. ~2 s), K2 = the unison's detune (orange, 0 .. +-50 cents for the outer voices);
    the knobs' LEDs show them;
  * Shift + pad 29 still steps through the five modes (it was retrigger -> legato -> poly); with Shift its LED shows the mode.
The glide: a head of the DSP service chain writes each track's coefficient to OSC2 + vcf21_dsp.GK_OFF (GK[time] in portamento, else 0) when it
changes and every 500 ms (the DSP's word is not cleared at boot).  Saved with the own-synth patches (and so with the project, projsyn): padding
+ 126..129 = PTAG, 0x50 | mode, time, detune (smst's gather / apply wrapped); a patch without them keeps the current ones.
RAM: poly.VMR (+ 0 the open track + 1, + 4 the time of the last LED call, + 8 + t the time, + 10 + t the detune, + 12 "VMD1", + 16 + 4 t the
coefficient written, + 24 the last refresh).  In the hole (no card: mpatch writes it)."""
from __future__ import annotations
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm3, adds_imm8, adds_reg, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldr_sp, ldrb_imm, ldrb_reg,  # noqa: E402
                   lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, strh_reg,
                   subs_imm8, subs_reg, ldrb_w)
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import mpatch as MP  # noqa: E402
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
import modesel as MS  # noqa: E402
import poly as PL  # noqa: E402
import fmeng as FE  # noqa: E402
import build_sc14 as S14  # noqa: E402

RAM = PL.VMR
SIG = 0x31444D56                          # "VMD1"
PAD, PAD29, PAD27, ROW = 31, 28, 26, 16   # pad 32, pad 29, pad 27; pads 17-21: the modes
N = PL.MODE_N
V2 = False                                # SC47.6 (use_v2)
V3 = False                                # SC47.7 (use_v3)
ORDER = (0, 1, 2, 4, 5, 6, 7, 3)          # (V3) the pads 17-24 -> the modes: retrigger, legato, glide, uni retrig, uni legato, uni glide,
                                          # uni always-glide, poly
CLOSE_MS, REFRESH_MS = 300, 500
COLS = ((0x17, 0x18), (0x2D, 0x2E), (0x4D, 0x4E), (0x32, 0x37), (0x09, 0x0A))   # bright / dim: retrigger, legato, portamento, poly, unison
KCOL = (0x4D, 0x09)                       # K1 the time (cyan), K2 the detune (orange)
GL_DEF, DT_DEF = 48, 40
POFS, PTAG = 126, 0xB6                    # the padding: after smst's (121..123) and projsyn's sum in its image (124 / 125)
DSP_WRITE = 0x080292F8
INV = V.INV


def use_v2():
    """SC47.6 (the user, 2026-10-26: «Add uni retrig, uni portamento and uni glide»; poly.use_v5): seven modes on pads 17-23 (uni retrig blue,
    uni portamento light blue, uni glide violet); the glide's coefficient in portamento, uni portamento and uni glide."""
    global V2, N, COLS
    assert PL.V5
    V2 = True
    N = PL.MODE_N
    COLS = COLS + ((0x13, 0x14), (0x49, 0x4A))


def use_v3():
    """SC47.7 (the user, 2026-10-26: «modes and order: retrigger … legato … glide … uni retrig/legato/glide … Poly»): the row in that order (ORDER:
    pad -> mode code; Shift + pad 29 steps in that order too); «Iguala los colores de los modos que se llaman igual»: retrigger / uni retrig
    green, legato / uni legato yellow, glide / uni glide cyan, uni always-glide violet, poly magenta; the glide's coefficient in glide (2), uni
    glide (6) and uni always-glide (7): uni legato (5) moves the voices without sliding."""
    global V3, N, COLS
    assert V2 and PL.V6
    V3 = True
    N = PL.MODE_N
    COLS = ((0x17, 0x18), (0x2D, 0x2E), (0x4D, 0x4E), (0x32, 0x37), (0x17, 0x18), (0x2D, 0x2E), (0x4D, 0x4E), (0x49, 0x4A))


def gk(i):
    """The glide's coefficient a block for the time knob i: tau = 2 ms .. 2 s (exponential), 0 = none."""
    if i == 0:
        return 0
    tau = 0.002 * 1000 ** ((i - 1) / 126)
    return min(0x7FFFFF, round(8388608 * math.exp(-(32 / 48000) / tau)))


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldr_reg(rt, rn, rm): return h(0x5800 | rm << 6 | rn << 3 | rt)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_v{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def now(rd): imm32(rd, V.HAL_TICK); E(ldr_imm, rd, rd, 0)
    RET = h(0x4770)
    T_GK, T_COLS = base, base + 512                                                          # the tables first
    E(raw, struct.pack("<128I", *(gk(i) for i in range(128)))); E(raw, bytes(c for pair in COLS for c in pair) + bytes(2))
    if V3:                                                                                     # (V3) pad -> mode, mode -> pad
        T_ORD = base + 512 + 2 * len(COLS) + 2; T_INV = T_ORD + len(ORDER) + 1
        E(raw, bytes(ORDER) + bytes(1) + bytes(ORDER.index(m) for m in range(N)) + bytes(1))

    # ---- c_vmst() -> r0 = RAM (signed; the defaults at the first use); clobbers r1, r2
    a.label("c_vmst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 12); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 12); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0); E(str_imm, 1, 0, 4); E(str_imm, 1, 0, 16); E(str_imm, 1, 0, 20); E(str_imm, 1, 0, 24)
    imm32(1, GL_DEF | GL_DEF << 8 | DT_DEF << 16 | DT_DEF << 24); E(str_imm, 1, 0, 8)
    a.label("st_x"); E(raw, RET)

    # ---- c_vmopen(r0 = track) -> r0 = 1 while the row is open for it (its LEDs asked for in CLOSE_MS); clobbers r1-r3
    a.label("c_vmopen")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_vmst")
    E(ldrb_imm, 1, 0, 0); E(subs_imm8, 1, 1); E(cmp_reg, 1, 4); E(b_cond, "vo_0", "ne")
    E(ldr_imm, 1, 0, 4); now(2); E(subs_reg, 2, 2, 1); imm32(1, CLOSE_MS); E(cmp_reg, 2, 1); E(b_cond, "vo_0", "hi")
    E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("vo_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_vmfree(r0 = track) -> r0 = 1 when pad 32 is ours: not under fmeng's overlays (pad 7 held: the algorithms; a ratio: pads 9-32); clobbers r1-r3
    a.label("c_vmfree")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0)
    E(bl, L["c_fmpg"]); E(cmp_imm, 0, 0); E(b_cond, "vf_1", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(mov_reg, 4, 0); E(ldrb_w, 1, 0, FE.B_P7); E(cmp_imm, 1, 0); E(b_cond, "vf_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_fmovk"]); E(subs_imm8, 0, 1); E(cmp_imm, 0, 3); E(b_cond, "vf_0", "ls")
    a.label("vf_1"); E(movs_imm, 0, 1); E(pop_list, [4], pc=True)
    a.label("vf_0"); E(movs_imm, 0, 0); E(pop_list, [4], pc=True)

    # ---- c_vmpad (slot 0 of the template view: view, pad, velocity)
    a.label("c_vmpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("vp_prev", "hi"); E(mov_reg, 4, 0)            # r4 = the track
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("vp_prev", "eq")             # the engine off: as before
    E(mov_reg, 0, 4); E(bl, "c_vmfree"); E(cmp_imm, 0, 0); bc("vp_prev", "eq")              # FM's overlays: theirs
    E(bl, "c_vmst"); E(mov_reg, 6, 0); E(ldrb_imm, 7, 6, 0)                                  # r6 = RAM, r7 = the open track + 1
    E(cmp_imm, 5, PAD); E(b_cond, "vp_n32", "ne")
    E(bl, L["c_msheld"]); E(cmp_imm, 0, 0); bc("vp_prev", "ne")
    E(adds_imm3, 0, 4, 1); E(cmp_reg, 7, 0); E(b_cond, "vp_cl", "eq")                       # open for this track: close
    E(strb_imm, 0, 6, 0); now(1); E(str_imm, 1, 6, 4)
    imm32(1, MS.RAM); E(movs_imm, 0, 0); E(strb_imm, 0, 1, 0); E(b, "vp_x")                 # (the engines' row closed)
    a.label("vp_cl"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "vp_x")
    a.label("vp_n32")
    E(cmp_imm, 5, PAD29); E(b_cond, "vp_n29", "ne")                                          # Shift + pad 29: the next mode
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "vp_n29", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_vmget"])
    if V3: imm32(1, T_INV); E(ldrb_reg, 0, 1, 0)                                             # (V3) its pad
    E(adds_imm8, 0, 1); E(cmp_imm, 0, N); E(b_cond, "vp_sm", "lo"); E(movs_imm, 0, 0)
    a.label("vp_sm")
    if V3: imm32(1, T_ORD); E(ldrb_reg, 0, 1, 0)                                             # (V3) the next pad's mode
    E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, L["c_vmset"]); E(b, "vp_x")
    a.label("vp_n29")
    E(adds_imm3, 0, 4, 1); E(cmp_reg, 7, 0); bc("vp_prev", "ne")                            # closed: the others'
    E(cmp_imm, 5, PAD27); E(b_cond, "vp_n27", "ne"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0); E(b, "vp_prev")   # pad 27: ours closed, the engines' opens
    a.label("vp_n27")
    E(cmp_imm, 5, 8); bc("vp_prev", "lo"); E(cmp_imm, 5, 23); bc("vp_prev", "hi")
    E(subs_imm8, 5, ROW); E(cmp_imm, 5, N - 1); E(b_cond, "vp_x", "hi")                     # (below the row: wraps high, swallowed)
    if V3: imm32(1, T_ORD); E(ldrb_reg, 5, 1, 5)                                             # (V3) the pad's mode
    E(mov_reg, 1, 5); E(mov_reg, 0, 4); E(bl, L["c_vmset"])
    a.label("vp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("vp_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_vmleds (slot 7 of the template view: view) -> r0 = the LED buffer: pad 32 (and pad 29 with Shift) = the mode; the row while open
    a.label("c_vmleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("vl_x", "hi"); E(mov_reg, 4, 0)
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); bc("vl_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_vmfree"); E(cmp_imm, 0, 0); bc("vl_x", "eq")                 # FM's overlays: theirs
    E(mov_reg, 0, 4); E(bl, L["c_vmget"]); E(mov_reg, 6, 0)                                 # r6 = the mode
    E(bl, "c_vmcol"); E(movs_imm, 3, 2 * PAD); E(strh_reg, 0, 5, 3)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "vl_ns", "eq")
    E(mov_reg, 0, 6); E(bl, "c_vmcol"); E(movs_imm, 3, 2 * PAD29); E(strh_reg, 0, 5, 3)
    a.label("vl_ns")
    E(bl, "c_vmst"); E(mov_reg, 7, 0); E(ldrb_imm, 0, 7, 0); E(cmp_imm, 0, 0); bc("vl_x", "eq")
    E(ldr_imm, 1, 7, 4); now(2); E(str_imm, 2, 7, 4); E(subs_reg, 2, 2, 1)                  # since the last call
    imm32(1, CLOSE_MS); E(cmp_reg, 2, 1); E(b_cond, "vl_go", "ls")
    E(movs_imm, 0, 0); E(strb_imm, 0, 7, 0); E(b, "vl_x")                                    # not shown for a while: closed
    a.label("vl_go"); E(subs_imm8, 0, 1); E(cmp_reg, 0, 4); bc("vl_x", "ne")
    E(movs_imm, 1, 0); E(movs_imm, 2, 8)
    a.label("vl_d"); E(lsls_imm, 3, 2, 1); E(strh_reg, 1, 5, 3); E(adds_imm8, 2, 1); E(cmp_imm, 2, 24); E(b_cond, "vl_d", "lo")
    E(movs_imm, 7, 0)
    a.label("vl_m")
    if V3: imm32(1, T_ORD); E(ldrb_reg, 3, 1, 7); E(mov_reg, 0, 3); E(bl, "c_vmcol"); E(cmp_reg, 3, 6); E(b_cond, "vl_c", "eq"); E(mov_reg, 0, 1)   # (V3) the pad's mode
    else: E(mov_reg, 0, 7); E(bl, "c_vmcol"); E(cmp_reg, 7, 6); E(b_cond, "vl_c", "eq"); E(mov_reg, 0, 1)   # the current one bright, the others dim
    a.label("vl_c"); E(movs_imm, 3, ROW); E(adds_reg, 3, 3, 7); E(lsls_imm, 3, 3, 1); E(strh_reg, 0, 5, 3)
    E(adds_imm8, 7, 1); E(cmp_imm, 7, N); E(b_cond, "vl_m", "lo")
    a.label("vl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vmcol(r0 = mode) -> r0 = its bright colour, r1 = its dim one; clobbers r2
    a.label("c_vmcol")
    E(lsls_imm, 0, 0, 1); imm32(2, T_COLS); E(adds_reg, 2, 2, 0); E(ldrb_imm, 0, 2, 0); E(ldrb_imm, 1, 2, 1); E(raw, RET)

    # ---- c_vmknob (slot 4 of the macro handlers: obj, knob, delta): while the row is open, K1 = the time, K2 = the detune
    a.label("c_vmknob")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("vk_prev", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_vmopen"); E(cmp_imm, 0, 0); bc("vk_prev", "eq")
    E(ldr_sp, 5, 4); E(movs_imm, 0, 7); E(ands_reg, 5, 0); E(cmp_imm, 5, 1); bc("vk_prev", "hi")
    E(bl, "c_vmst"); E(mov_reg, 4, 0); E(lsls_imm, 0, 5, 1); E(adds_reg, 0, 0, 6); E(adds_imm8, 0, 8); E(adds_reg, 4, 4, 0)   # r4 = + 8 + 2 k + t
    E(ldrb_imm, 0, 4, 0); E(ldr_sp, 1, 8); E(adds_reg, 0, 0, 1)
    E(cmp_imm, 0, 0); E(b_cond, "vk_1", "ge"); E(movs_imm, 0, 0)
    a.label("vk_1"); E(cmp_imm, 0, 127); E(b_cond, "vk_2", "le"); E(movs_imm, 0, 127)
    a.label("vk_2"); E(strb_imm, 0, 4, 0)
    E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("vk_prev"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["knob"])

    # ---- c_vmkleds (slot 7 of the macro handlers: obj) -> r0 = the knobs' LEDs: while the row is open K1 / K2 = the time / the detune
    a.label("c_vmkleds")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(bl, prev["kleds"]); E(mov_reg, 5, 0)
    E(mov_reg, 0, 4); E(bl, L["c_vtrack"]); E(cmp_imm, 0, 1); bc("kl_x", "hi"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 6); E(bl, "c_vmopen"); E(cmp_imm, 0, 0); bc("kl_x", "eq")
    E(bl, "c_vmst"); E(mov_reg, 4, 0)
    for k in (0, 1):                                                                          # brightness 16 + v x 7 / 8, the knob's colour
        E(adds_reg, 0, 4, 6); E(ldrb_imm, 0, 0, 8 + 2 * k); E(movs_imm, 1, 7); E(muls, 0, 1); E(lsrs_imm, 0, 0, 3); E(adds_imm8, 0, 16)
        E(lsls_imm, 0, 0, 8); E(adds_imm8, 0, KCOL[k]); E(strh_imm, 0, 5, 2 * k)
    a.label("kl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vmtick: a head of the DSP service chain: each track's glide coefficient (RAM and DSP writes only)
    a.label("c_vmtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_vmst"); E(mov_reg, 5, 0)
    now(6); E(ldr_imm, 0, 5, 24); E(subs_reg, 0, 6, 0); imm32(1, REFRESH_MS); E(movs_imm, 7, 0); E(cmp_reg, 0, 1); E(b_cond, "tk_0", "lo")
    E(movs_imm, 7, 1); E(str_imm, 6, 5, 24)                                                  # r7 = 1: written again (the DSP's word)
    a.label("tk_0"); E(movs_imm, 4, 0)
    a.label("tk_l")
    E(mov_reg, 0, 4); E(bl, L["c_vmget"]); E(movs_imm, 1, 0); E(cmp_imm, 0, 2)
    if V3: E(b_cond, "tk_gk", "eq"); E(cmp_imm, 0, 6); E(b_cond, "tk_w", "lo"); a.label("tk_gk")      # (V3) glide, uni glide, uni always-glide
    elif V2: E(b_cond, "tk_gk", "eq"); E(cmp_imm, 0, 5); E(b_cond, "tk_w", "lo"); a.label("tk_gk")      # (V2) uni portamento / uni glide too
    else: E(b_cond, "tk_w", "ne")
    E(adds_reg, 0, 5, 4); E(ldrb_imm, 0, 0, 8); E(lsls_imm, 0, 0, 2); imm32(1, T_GK); E(raw, ldr_reg(1, 1, 0))
    a.label("tk_w")                                                                           # r1 = the coefficient
    E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 0, 5); E(ldr_imm, 2, 0, 16); E(cmp_reg, 2, 1); E(b_cond, "tk_s", "ne"); E(cmp_imm, 7, 0); E(b_cond, "tk_n", "eq")
    a.label("tk_s"); E(str_imm, 1, 0, 16)
    E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.GK_OFF); E(adds_reg, 2, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(bl, DSP_WRITE)
    a.label("tk_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "tk_l", "lo")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_vmgath(r0 = track) in c_mpsave: smst's gather, then the mode, the time and the detune at padding + 126
    a.label("c_vmgath")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, L["c_vmget"]); E(adds_imm8, 0, 0x50); imm32(5, PK.BUF + POFS); E(strb_imm, 0, 5, 1)
    E(movs_imm, 0, PTAG); E(strb_imm, 0, 5, 0)
    E(bl, "c_vmst"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 0, 8); E(strb_imm, 1, 5, 2); E(ldrb_imm, 1, 0, 10); E(strb_imm, 1, 5, 3)
    E(pop_list, [4, 5], pc=True)

    # ---- c_vmappl(r0 = track) in c_mpload (r5 = the slot): smst's apply, then the mode, the time and the detune from the padding (none: kept)
    a.label("c_vmappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5)
    E(bl, prev["appl"])
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20)
    imm32(2, MP.OFF + POFS); E(adds_reg, 1, 1, 2)
    imm32(2, PK.BUF + POFS); E(movs_imm, 3, 4); E(bl, L["c_mpr"])
    E(cmp_imm, 0, 0); E(b_cond, "ap_x", "ne"); E(cmp_imm, 1, 4); E(b_cond, "ap_x", "ne")
    imm32(6, PK.BUF + POFS); E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, PTAG); E(b_cond, "ap_x", "ne")
    E(ldrb_imm, 0, 6, 1); E(subs_imm8, 0, 0x50); E(cmp_imm, 0, N - 1); E(b_cond, "ap_x", "hi")
    E(ldrb_imm, 1, 6, 2); E(ldrb_imm, 2, 6, 3); E(orrs_reg, 1, 2); E(lsrs_imm, 1, 1, 7); E(b_cond, "ap_x", "ne")    # both 0..127
    E(mov_reg, 1, 0); E(mov_reg, 0, 4); E(bl, L["c_vmset"])
    E(bl, "c_vmst"); E(adds_reg, 0, 0, 4); E(ldrb_imm, 1, 6, 2); E(strb_imm, 1, 0, 8); E(ldrb_imm, 1, 6, 3); E(strb_imm, 1, 0, 10)
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr (hole.add, after poly); the heads: the template view's slots 0 / 7, the macro handlers' slots 4 / 7, the DSP service
    chain; smst's gather / apply calls in c_mpsave / c_mpload."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_von", "c_vtrack")}
    L["c_shift"] = lab("sc15", "c_shift")
    for k in ("c_mpon", "c_mpr", "c_mpload", "c_mpsave"): L[k] = lab("mpatch", k)
    L["c_msheld"] = lab("modesel", "c_msheld")
    for k in ("c_vmget", "c_vmset"): L[k] = lab("poly", k)
    for k in ("c_ssgath", "c_ssappl"): L[k] = lab("smst", k)
    for k in ("c_fmpg", "c_fmblk", "c_fmovk"): L[k] = lab("fmeng", k)
    TP, KN = MP.TMPL_VT, V.AC64_VT
    prev = dict(pad=u(TP) & ~1, leds=u(TP + 28) & ~1, knob=u(KN + 16) & ~1, kleds=u(KN + 28) & ~1, svc=MP.bw_target(img, S14.SVC_HOOK, BASE),
                gath=L["c_ssgath"], appl=L["c_ssappl"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    for site_of, orig, ours in ((L["c_mpsave"], L["c_ssgath"], "c_vmgath"), (L["c_mpload"], L["c_ssappl"], "c_vmappl")):
        s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_vmtick"])
    struct.pack_into("<I", img, TP - BASE, labels["c_vmpad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_vmleds"] | 1)
    struct.pack_into("<I", img, KN + 16 - BASE, labels["c_vmknob"] | 1)
    struct.pack_into("<I", img, KN + 28 - BASE, labels["c_vmkleds"] | 1)
    if V3: prev["v3"] = 1                                                        # (V3) the tests adopt the order
    return labels, code, prev
