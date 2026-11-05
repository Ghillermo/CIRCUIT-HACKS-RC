"""SC52.1: the wavetable engine of the MIDI 1 / 2 own synth, the ARM side (the user, 2026-11-05: «Select wavetables in engine mode. Knob layout on
osc1 and osc2 views»; then «grouped tables», «build your own table, pre-filled», «One table, two positions», «Load Nova, add samples», sand; «I leave
the options up to you»).  DSP: vcf21_dsp.use_wavetable (core 0 reads the track's table), granular_dsp.use_wtcopy (core 1 copies a frame).

  * Engine row pad 21 (modesel's row open) = the oscillator (modesel's pad 19, run down the chain) + the wavetable on, FM off; any other pad of the
    row (17-24) = the wavetable off.  The wavetable plays while it is on, the engine is the oscillator (c_msmode = 2) and FM is off.  A first turn-on
    with an empty table fills it with Nova table DEF_T («pre-filled»).
  * The table: up to 9 frames, one per patch, both oscillators (each its position: K7 of the OSC 1 / OSC 2 pages, vcf21's WAVE codes).  A frame =
    a Nova table's frame (t x 9 + f, t = stock wave 14 + t) or a sample's single cycle (144 + s; sample frames are not copied yet: NOTAS).
  * With the wavetable playing: pad 7 held = pads 9-24 the 16 Nova tables (sand; bright = the one the table is), a tap fills the table with its
    9 frames; pad 8 held = pads 9-32 the samples 24 p .. 24 p + 23 (Octave ▼ / ▲ = the page p 0..2, while pad 8 is held), a tap adds the sample's
    frame at the end (up to 9) or takes it out; pads 7 / 8 sand, bright while held; pad 21 of the row sand, bright when playing (and pad 19 dim).
  * The DSP service tick (the head of the chain): per track, X:OSC2 + WT_N = the frames while playing, else 0 (and WT_B = the table's Y base);
    one copy at a time: a frame whose slot holds something else -> core 1's command (X:$5211.. source, destination, words; $5210 = a new seq), done
    when X:$5214 = the seq.
  * The patch: padding + 150..162 = 0xB7, on, frames, the 9 frames, a check byte (mpatch's save / load, around vmode's gather / apply; psave /
    xpatch move it: their XLEN = 163).  The project: projsyn keeps the padding's first 150 bytes only: its RAM image IMG[t] + 150.. goes to bytes
    8..39 of the settings of MIDI 2's pattern 5 + t (0xCA, t, the 13 bytes) on a save, and comes back before projsyn's restore.
RAM WTR: + 0 "WTR1", + 4 the seq, + 5 the job (0xFF none, else track << 4 | slot), + 6 the sample page; track t at + 0x10 + 0x20 t: + 0 on, + 1 frames,
+ 2..10 the frames, + 11..19 what each DSP slot holds (0xFE unknown), + 20 the WT_N last written (0xFF unknown)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, str_imm, strb_imm, strb_reg, strh_reg, subs_imm8, subs_reg)
import mpatch as MP  # noqa: E402
import modesel as MS  # noqa: E402
import packio as PK  # noqa: E402
import projsyn as PS  # noqa: E402
import persist19 as P19  # noqa: E402
import build_sc14 as S14  # noqa: E402
import vcf21 as V  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
import granular_dsp as GD  # noqa: E402
import fm8arm as FA  # noqa: E402

WTR = 0x2004F400
SIG = 0x31525457                          # "WTR1"
TB0, TBS = 0x10, 0x20
T_ON, T_N, T_F, T_L, T_SENT = 0, 1, 2, 11, 20
NF = 9
DEF_T = 6                                 # the pre-fill: Nova table 6 (the stock's wave 20, digital saw-square)
NOVA0, NOVA_T, FRAME = 0x1B4000, 0x28800, VD.WT_FRAME     # core 1's X: Nova table t at NOVA0 + t NOVA_T (stock waves 14-29), frame f at + f FRAME
WT_Y = (0x520000, 0x548800)               # the tables in external Y (packio.IMP_HI lowered to 0x520000)
COL = (0x6D, 0x69)                        # sand bright / dim (the user)
ROWPAD, OSCPAD = 20, 18                   # pad 21 (the wavetable), pad 19 (the oscillator)
DSPW, DSPR = 0x080292F8, 0x08029344       # (core, value << 8, address) / (core, address) -> the word << 8
REC_AT, REC_N, REC_SIG = 150, 13, 0xB7    # the padding's record
PJ_SIG, PJ_PAT = 0xCA, 5                  # the project's block: MIDI 2's pattern 5 + t
PJ_AREA = PS.AREA + 8 * PS.PSIZE + PS.SET + PS.BYTE0     # MIDI 2's pattern 0, settings + 8, in the record
RET = h(0x4770)
POP_LR = h(0xBC08) + h(0x469E)            # pop {r3}; mov lr, r3


SMPCYC = False                                    # SC52.2 (use_smpcyc)
ROWFIX = False                                    # SC52.2 (use_rowfix)


def use_rowfix():
    """SC52.2 (the user, 2026-11-05: «al desplegar el selector de motores, pads 7 y 8 se leen aunque estén apagados, y apagan el selector WT
    (pad21)»): with the engine row open, pads 7 / 8 (dark) were FM's list keys even with FM off: held, pad 21 went dark and the row's pads went
    past us.  Now with FM off they do nothing there, and pad 21 / the row stay ours while they are held."""
    global ROWFIX
    ROWFIX = True


def use_smpcyc():
    """SC52.2 (found answering the user's «en WT, qué hace el pad 8 de vistas?»): SC52.1 marked a sample's frame as there without copying it (the
    slot kept what it held); now its copy is core 1's sample job (source = bit 23 | the sample, granular_dsp.use_wtcopy: the single cycle at the
    sample's pitch, 18 levels), the same job / seq as a Nova frame's."""
    global SMPCYC
    SMPCYC = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def bc(target, cond):
        zc[0] += 1; n = f"_w{zc[0]}"
        E(b_cond, n, V.INV[cond]); E(b, target); a.label(n)
    def held(rd, pad):                                                         # rd = the pad held (bit), flags: ne = held
        imm32(rd, MP.MGR + 0x84); E(ldr_imm, rd, rd, 0); E(lsrs_imm, rd, rd, pad + 1); E(raw, h(0x4140 | rd << 3 | rd))   # adcs rd, rd: carry -> bit 0
        E(lsls_imm, rd, rd, 31)

    # ---- c_wtst() -> r0 = WTR (made the first time: tables empty, slots unknown); clobbers r1-r3
    a.label("c_wtst")
    imm32(0, WTR); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0); E(str_imm, 1, 0, 4); E(movs_imm, 1, 0xFF); E(strb_imm, 1, 0, 5)
    for t in range(2):
        E(mov_reg, 3, 0); E(adds_imm8, 3, TB0 + TBS * t)
        E(movs_imm, 1, 0); E(strb_imm, 1, 3, T_ON); E(strb_imm, 1, 3, T_N)
        E(movs_imm, 1, 0xFE)
        for k in range(NF): E(strb_imm, 1, 3, T_L + k)
        E(movs_imm, 1, 0xFF); E(strb_imm, 1, 3, T_SENT)
    a.label("st_x"); E(raw, RET)

    # ---- c_wttb(r0 = track) -> r0 = its block; clobbers r1-r3
    a.label("c_wttb")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_wtst")
    E(lsls_imm, 1, 4, 5); E(adds_reg, 0, 0, 1); E(adds_imm8, 0, TB0); E(pop_list, [4], pc=True)

    # ---- c_wtact(r0 = track) -> r0 = 1 when the wavetable plays (on, the oscillator, FM off); clobbers r1-r3
    a.label("c_wtact")
    E(push_list, [4, 5], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_wttb"); E(ldrb_imm, 0, 0, T_ON); E(cmp_imm, 0, 0); E(b_cond, "ac_0", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_msmode"]); E(cmp_imm, 0, 2); E(b_cond, "ac_0", "ne")
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(movs_imm, 1, FA.B_ON); E(ldrb_reg, 0, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "ac_0", "ne")
    E(movs_imm, 0, 1); E(pop_list, [4, 5], pc=True)
    a.label("ac_0"); E(movs_imm, 0, 0); E(pop_list, [4, 5], pc=True)

    # ---- c_wtfill(r0 = the block, r1 = Nova table): its 9 frames; clobbers r1-r3
    a.label("c_wtfill")
    E(movs_imm, 2, NF); E(muls, 1, 2); E(movs_imm, 2, 0)
    a.label("wf_l"); E(adds_reg, 3, 0, 2); E(strb_imm, 1, 3, T_F); E(adds_imm8, 1, 1); E(adds_imm8, 2, 1); E(cmp_imm, 2, NF); E(b_cond, "wf_l", "lo")
    E(strb_imm, 2, 0, T_N); E(raw, RET)

    # ---- c_wtw(r0 = X address, r1 = value): core 0's X word; clobbers r0-r3, r12
    a.label("c_wtw")
    E(mov_reg, 2, 0); E(lsls_imm, 1, 1, 8); E(movs_imm, 0, 0); E(b_w, DSPW)

    # ---- c_wttick (the head of the DSP service chain): per track the frames to core 0, one copy at a time
    a.label("c_wttick")
    E(raw, h(0xE92D) + h(0x5FFF))                                                   # push.w {r0-r12, lr}
    E(bl, "c_wtst"); E(mov_reg, 7, 0)
    E(ldrb_imm, 0, 7, 5); E(cmp_imm, 0, 0xFF); E(b_cond, "tk_nj", "eq")             # a job: done?
    imm32(1, GD.WC_X + 4); E(movs_imm, 0, 0); E(bl, DSPR); E(lsrs_imm, 0, 0, 8); E(ldrb_imm, 1, 7, 4); E(lsls_imm, 0, 0, 24); E(lsrs_imm, 0, 0, 24)
    E(cmp_reg, 0, 1); bc("tk_nj", "ne")                                              # (not yet: the tracks' WT_N still go)
    E(ldrb_imm, 0, 7, 5); E(lsrs_imm, 1, 0, 4); E(lsls_imm, 1, 1, 5); E(adds_reg, 1, 1, 7); E(adds_imm8, 1, TB0)   # r1 = the track's block
    E(lsls_imm, 0, 0, 28); E(lsrs_imm, 0, 0, 28); E(adds_reg, 1, 1, 0); E(ldrb_imm, 2, 1, T_F); E(strb_imm, 2, 1, T_L)   # the slot holds it now
    E(movs_imm, 0, 0xFF); E(strb_imm, 0, 7, 5)
    a.label("tk_nj")
    E(movs_imm, 4, 0)
    a.label("tk_t")                                                                   # r4 = the track, r5 = its block, r6 = WT_N to write
    E(lsls_imm, 5, 4, 5); E(adds_reg, 5, 5, 7); E(adds_imm8, 5, TB0)
    E(mov_reg, 0, 4); E(bl, "c_wtact"); E(movs_imm, 6, 0); E(cmp_imm, 0, 0); bc("tk_s", "eq")
    E(ldrb_imm, 6, 5, T_N)
    E(ldrb_imm, 0, 7, 5); E(cmp_imm, 0, 0xFF); bc("tk_s", "ne")                     # a copy in flight: no other
    E(movs_imm, 3, 0)
    a.label("tk_k"); E(cmp_reg, 3, 6); bc("tk_s", "hs")
    E(adds_reg, 0, 5, 3); E(ldrb_imm, 1, 0, T_F); E(ldrb_imm, 2, 0, T_L); E(cmp_reg, 1, 2); E(b_cond, "tk_cp", "ne")
    E(adds_imm8, 3, 1); E(b, "tk_k")
    a.label("tk_cp")                                                                  # slot r3 <- frame r1
    if SMPCYC:
        E(lsls_imm, 0, 4, 4); E(adds_reg, 0, 0, 3); E(strb_imm, 0, 7, 5)              # the job
        E(mov_reg, 8, 3)                                                               # (mov r8, r3: below)
        E(cmp_imm, 1, 144); E(b_cond, "tk_nv", "lo")
        E(subs_imm8, 1, 144); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 23); E(raw, h(0x4311)); E(b, "tk_src")   # orrs r1, r2: core 1's sample job (bit 23 | s)
        a.label("tk_nv")
    else:
        E(cmp_imm, 1, 144); E(b_cond, "tk_nv", "lo"); E(strb_imm, 1, 0, T_L); E(b, "tk_s")   # a sample's frame: not copied yet (the slot as it is)
        a.label("tk_nv")
        E(lsls_imm, 0, 4, 4); E(adds_reg, 0, 0, 3); E(strb_imm, 0, 7, 5)              # the job
        E(mov_reg, 8, 3)                                                               # (mov r8, r3: below)
    E(movs_imm, 2, 0)
    a.label("tk_dv"); E(cmp_imm, 1, NF); E(b_cond, "tk_dd", "lo"); E(subs_imm8, 1, NF); E(adds_imm8, 2, 1); E(b, "tk_dv")   # r2 = the Nova table, r1 = its frame
    a.label("tk_dd")
    imm32(0, NOVA_T); E(muls, 2, 0); imm32(0, FRAME); E(muls, 1, 0); E(adds_reg, 1, 1, 2); imm32(0, NOVA0); E(adds_reg, 1, 1, 0)
    if SMPCYC: a.label("tk_src")
    imm32(0, GD.WC_X + 1); E(bl, "c_wtw")                                              # the source
    E(mov_reg, 3, 8); imm32(0, FRAME); E(muls, 3, 0); imm32(1, WT_Y[0]); E(cmp_imm, 4, 0); E(b_cond, "tk_y0", "eq"); imm32(1, WT_Y[1])
    a.label("tk_y0"); E(adds_reg, 1, 1, 3); imm32(0, GD.WC_X + 2); E(bl, "c_wtw")      # the destination
    imm32(1, FRAME); imm32(0, GD.WC_X + 3); E(bl, "c_wtw")                             # the words
    E(ldrb_imm, 1, 7, 4); E(adds_imm8, 1, 1); E(lsls_imm, 1, 1, 24); E(lsrs_imm, 1, 1, 24); E(strb_imm, 1, 7, 4); imm32(0, GD.WC_X); E(bl, "c_wtw")
    a.label("tk_s")                                                                    # WT_N (and WT_B) when it changes
    E(ldrb_imm, 0, 5, T_SENT); E(cmp_reg, 0, 6); E(b_cond, "tk_n", "eq")
    E(strb_imm, 6, 5, T_SENT)
    imm32(1, WT_Y[0]); E(cmp_imm, 4, 0); E(b_cond, "tk_b0", "eq"); imm32(1, WT_Y[1])
    a.label("tk_b0"); E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.WT_B); E(adds_reg, 0, 0, 2); E(bl, "c_wtw")
    E(movs_imm, 0, 48); E(muls, 0, 4); imm32(2, VD.OS2B0 + VD.WT_N); E(adds_reg, 0, 0, 2); E(mov_reg, 1, 6); E(bl, "c_wtw")
    a.label("tk_n"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); bc("tk_t", "lo")
    a.label("tk_tr")
    E(raw, h(0xE8BD) + h(0x5FFF)); E(b_w, prev["svc"])                                   # pop.w {r0-r12, lr}; the chain

    # ---- c_wtpad (slot 0 of the template view: view, pad, velocity)
    a.label("c_wtpad")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True); E(mov_reg, 5, 1)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("wp_p", "hi"); E(mov_reg, 4, 0)            # r4 = the track
    E(bl, "c_wttb"); E(mov_reg, 6, 0)                                                    # r6 = its block
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0)
    E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 0, 1); E(b_cond, "wp_nr", "ne")
    def fmoff(lab_):                                                                     # (ROWFIX) FM off (the track r4) -> to lab_
        E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(movs_imm, 1, FA.B_ON); E(ldrb_reg, 0, 0, 1); E(cmp_imm, 0, 0); bc(lab_, "eq")
    if ROWFIX:                                                                           # pads 7 / 8 (dark with the row open): nothing unless FM is on
        E(cmp_imm, 5, 6); E(b_cond, "wp_78", "eq"); E(cmp_imm, 5, 7); E(b_cond, "wp_r", "ne")
        a.label("wp_78"); fmoff("wp_x"); E(b, "wp_p")
        a.label("wp_r")
    E(cmp_imm, 5, 16); bc("wp_p", "lo"); E(cmp_imm, 5, 23); bc("wp_p", "hi")            # the row: 17-24 (not under FM's lists: pad 7 / 8 held)
    if ROWFIX: fmoff("wp_nh")                                                             # (FM's lists only with FM on)
    held(0, 6); bc("wp_p", "ne"); held(0, 7); bc("wp_p", "ne")
    if ROWFIX: a.label("wp_nh")
    E(movs_imm, 0, 0); E(strb_imm, 0, 6, T_ON)
    E(cmp_imm, 5, ROWPAD); bc("wp_p", "ne")
    E(raw, h(0x9800)); E(movs_imm, 1, OSCPAD); E(raw, h(0x9A02)); E(bl, prev["pad"])    # the oscillator, by modesel (ldr r0, [sp]; ldr r2, [sp, #8])
    E(movs_imm, 0, 1); E(strb_imm, 0, 6, T_ON)
    E(ldrb_imm, 0, 6, T_N); E(cmp_imm, 0, 0); E(b_cond, "wp_ff", "ne"); E(mov_reg, 0, 6); E(movs_imm, 1, DEF_T); E(bl, "c_wtfill")   # pre-filled
    a.label("wp_ff")
    E(mov_reg, 0, 4); E(bl, L["c_fmblk"]); E(movs_imm, 1, FA.B_ON); E(movs_imm, 2, 0); E(strb_reg, 2, 0, 1)
    E(movs_imm, 1, FA.B_DIRTY); E(movs_imm, 2, 1); E(strb_reg, 2, 0, 1)
    E(b, "wp_x")
    a.label("wp_nr")                                                                     # the row closed: the lists while playing
    E(mov_reg, 0, 4); E(bl, "c_wtact"); E(cmp_imm, 0, 0); bc("wp_p", "eq")
    E(cmp_imm, 5, 6); E(b_cond, "wp_x", "eq"); E(cmp_imm, 5, 7); E(b_cond, "wp_x", "eq")  # pads 7 / 8: held keys
    held(0, 6); bc("wp_n7", "eq")
    E(cmp_imm, 5, 8); bc("wp_x", "lo"); E(cmp_imm, 5, 23); bc("wp_x", "hi")
    E(mov_reg, 0, 6); E(subs_imm8, 5, 8); E(mov_reg, 1, 5); E(bl, "c_wtfill"); E(b, "wp_x")   # a Nova table
    a.label("wp_n7")
    held(0, 7); bc("wp_p", "eq")
    E(cmp_imm, 5, 8); bc("wp_x", "lo")
    E(subs_imm8, 5, 8); imm32(0, WTR); E(ldrb_imm, 0, 0, 6); E(movs_imm, 1, 24); E(muls, 0, 1); E(adds_reg, 5, 5, 0); E(adds_imm8, 5, 144)   # the code
    E(cmp_imm, 5, 144 + 63); bc("wp_x", "hi")                                          # (samples 0..63)
    E(ldrb_imm, 1, 6, T_N); E(movs_imm, 2, 0)                                           # in the table?  out
    a.label("wp_sl"); E(cmp_reg, 2, 1); E(b_cond, "wp_sa", "hs"); E(adds_reg, 3, 6, 2); E(ldrb_imm, 0, 3, T_F); E(cmp_reg, 0, 5); E(b_cond, "wp_so", "eq")
    E(adds_imm8, 2, 1); E(b, "wp_sl")
    a.label("wp_so")                                                                     # take it out: the next ones move down
    E(adds_imm8, 2, 1); E(cmp_reg, 2, 1); E(b_cond, "wp_sd", "hs"); E(adds_reg, 3, 6, 2); E(ldrb_imm, 0, 3, T_F); E(subs_imm8, 3, 1); E(strb_imm, 0, 3, T_F); E(b, "wp_so")
    a.label("wp_sd"); E(subs_imm8, 1, 1); E(strb_imm, 1, 6, T_N); E(b, "wp_x")
    a.label("wp_sa"); E(cmp_imm, 1, NF); E(b_cond, "wp_x", "hs"); E(adds_reg, 3, 6, 1); E(strb_imm, 5, 3, T_F); E(adds_imm8, 1, 1); E(strb_imm, 1, 6, T_N)
    a.label("wp_x"); E(pop_list, [0, 1, 2, 4, 5, 6, 7], pc=True)
    a.label("wp_p"); E(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); E(b_w, prev["pad"])

    # ---- c_wtled (slot 7 of the template view: view) -> r0 = the LED buffer
    a.label("c_wtled")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("wl_x", "hi"); E(mov_reg, 4, 0)
    E(bl, "c_wttb"); E(mov_reg, 6, 0)
    E(mov_reg, 0, 4); E(bl, "c_wtact"); E(mov_reg, 7, 0)                                  # r7 = playing
    imm32(1, MS.RAM); E(ldrb_imm, 1, 1, 0); E(mov_reg, 0, 4); E(adds_imm8, 0, 1); E(cmp_reg, 0, 1); E(b_cond, "wl_nr", "ne")
    if ROWFIX: fmoff("wl_nh")                                                             # (FM's lists over the row: only with FM on)
    held(0, 6); bc("wl_x", "ne"); held(0, 7); bc("wl_x", "ne")                            # (FM's lists over the row)
    if ROWFIX: a.label("wl_nh")
    E(movs_imm, 0, COL[1]); E(cmp_imm, 7, 0); E(b_cond, "wl_rd", "eq"); E(movs_imm, 0, COL[0])
    E(movs_imm, 1, MS.COLS[2][1]); E(movs_imm, 2, 2 * OSCPAD); E(strh_reg, 1, 5, 2)     # the oscillator's pad dim
    a.label("wl_rd"); E(movs_imm, 2, 2 * ROWPAD); E(strh_reg, 0, 5, 2); E(b, "wl_x")
    a.label("wl_nr")
    E(cmp_imm, 7, 0); bc("wl_x", "eq")
    for pd in (6, 7):                                                                     # pads 7 / 8: sand, bright while held
        E(movs_imm, 1, COL[1]); held(0, pd); E(b_cond, f"wl_h{pd}", "eq"); E(movs_imm, 1, COL[0])
        a.label(f"wl_h{pd}"); E(movs_imm, 2, 2 * pd); E(strh_reg, 1, 5, 2)
    held(0, 6); bc("wl_n7", "eq")                                                         # the Nova tables
    E(movs_imm, 7, 0)
    a.label("wl_tl")
    E(movs_imm, 1, COL[1]); E(ldrb_imm, 0, 6, T_N); E(cmp_imm, 0, NF); E(b_cond, "wl_tc", "ne")
    E(movs_imm, 2, NF); E(muls, 2, 7); E(movs_imm, 3, 0)
    a.label("wl_tm"); E(adds_reg, 0, 6, 3); E(ldrb_imm, 0, 0, T_F); E(cmp_reg, 0, 2); E(b_cond, "wl_tc", "ne"); E(adds_imm8, 2, 1); E(adds_imm8, 3, 1)
    E(cmp_imm, 3, NF); E(b_cond, "wl_tm", "lo"); E(movs_imm, 1, COL[0])
    a.label("wl_tc"); E(adds_imm8, 7, 8); E(lsls_imm, 2, 7, 1); E(strh_reg, 1, 5, 2); E(subs_imm8, 7, 7); E(cmp_imm, 7, 16); E(b_cond, "wl_tl", "lo")
    E(movs_imm, 1, 0); E(movs_imm, 2, 2 * 24)
    a.label("wl_tz"); E(strh_reg, 1, 5, 2); E(adds_imm8, 2, 2); E(cmp_imm, 2, 64); E(b_cond, "wl_tz", "lo"); E(b, "wl_x")
    a.label("wl_n7")
    held(0, 7); bc("wl_x", "eq")                                                          # the samples of the page
    imm32(0, WTR); E(ldrb_imm, 0, 0, 6); E(movs_imm, 1, 24); E(muls, 0, 1); E(adds_imm8, 0, 144); E(mov_reg, 7, 0)   # r7 = the first code
    E(movs_imm, 4, 0)
    a.label("wl_sl")
    E(movs_imm, 1, COL[1]); E(adds_reg, 0, 7, 4); E(ldrb_imm, 2, 6, T_N); E(movs_imm, 3, 0)
    a.label("wl_sm"); E(cmp_reg, 3, 2); E(b_cond, "wl_sc", "hs"); E(push_list, [0]); E(adds_reg, 0, 6, 3); E(ldrb_imm, 0, 0, T_F); E(raw, h(0x4684))   # mov r12, r0
    E(pop_list, [0]); E(raw, h(0x4560)); E(b_cond, "wl_sb", "eq"); E(adds_imm8, 3, 1); E(b, "wl_sm")      # cmp r0, r12
    a.label("wl_sb"); E(movs_imm, 1, COL[0])
    a.label("wl_sc"); E(adds_imm8, 4, 8); E(lsls_imm, 2, 4, 1); E(strh_reg, 1, 5, 2); E(subs_imm8, 4, 7); E(cmp_imm, 4, 24); E(b_cond, "wl_sl", "lo")
    a.label("wl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_wtbtn (the controller's button press head: ctrl, id): Octave with pad 8 held while playing = the sample page
    a.label("c_wtbtn")
    E(push_list, [0, 1, 4, 5], lr=True); E(mov_reg, 5, 1)
    E(cmp_imm, 5, 19); E(b_cond, "wb_o", "eq"); E(cmp_imm, 5, 20); bc("wb_p", "ne")
    a.label("wb_o")
    held(0, 7); bc("wb_p", "eq")
    E(bl, L["c_mpon"]); E(cmp_imm, 0, 1); bc("wb_p", "hi"); E(bl, "c_wtact"); E(cmp_imm, 0, 0); bc("wb_p", "eq")
    imm32(4, WTR); E(ldrb_imm, 0, 4, 6)
    E(cmp_imm, 5, 19); E(b_cond, "wb_up", "ne"); E(cmp_imm, 0, 0); E(b_cond, "wb_s", "eq"); E(subs_imm8, 0, 1); E(b, "wb_s")
    a.label("wb_up"); E(cmp_imm, 0, 2); E(b_cond, "wb_s", "hs"); E(adds_imm8, 0, 1)
    a.label("wb_s"); E(strb_imm, 0, 4, 6); E(pop_list, [0, 1, 4, 5], pc=True)
    a.label("wb_p"); E(raw, popw([0, 1, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_wtgath(r0 = track) in c_mpsave: vmode's gather, then the record at padding + REC_AT
    a.label("c_wtgath")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0); E(bl, prev["gath"])
    E(mov_reg, 0, 4); E(bl, "c_wttb"); E(mov_reg, 5, 0); imm32(6, PK.BUF + REC_AT)
    E(movs_imm, 0, REC_SIG); E(strb_imm, 0, 6, 0); E(ldrb_imm, 0, 5, T_ON); E(strb_imm, 0, 6, 1); E(ldrb_imm, 0, 5, T_N); E(strb_imm, 0, 6, 2)
    for k in range(NF): E(ldrb_imm, 0, 5, T_F + k); E(strb_imm, 0, 6, 3 + k)
    E(mov_reg, 0, 6); E(bl, "c_wtsum"); E(strb_imm, 0, 6, REC_N - 1)
    E(pop_list, [4, 5, 6], pc=True)
    # c_wtsum(r0 = a record) -> r0 = its check byte (0x5A + bytes 0..11); clobbers r1-r3
    a.label("c_wtsum")
    E(movs_imm, 1, 0); E(movs_imm, 2, 0x5A)
    a.label("su_l"); E(ldrb_reg, 3, 0, 1); E(adds_reg, 2, 2, 3); E(adds_imm8, 1, 1); E(cmp_imm, 1, REC_N - 1); E(b_cond, "su_l", "lo")
    E(lsls_imm, 0, 2, 24); E(lsrs_imm, 0, 0, 24); E(raw, RET)

    # ---- c_wtappl(r0 = track) in c_mpload: vmode's apply, then the record (none / damaged: the wavetable off)
    a.label("c_wtappl")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(mov_reg, 7, 5); E(bl, prev["appl"])        # r7 = the slot (c_mpload's r5)
    E(lsrs_imm, 0, 7, 3); E(lsls_imm, 1, 7, 29); E(lsrs_imm, 1, 1, 20); imm32(2, MP.OFF + REC_AT); E(adds_reg, 1, 1, 2)   # its record: read here
    imm32(2, PK.BUF + REC_AT); E(movs_imm, 3, REC_N); E(bl, L["c_mpr"])
    imm32(6, PK.BUF + REC_AT); E(cmp_imm, 0, 0); E(b_cond, "ap_r", "eq"); E(movs_imm, 0, 0); E(strb_imm, 0, 6, 0)   # not read: no record
    a.label("ap_r")
    E(mov_reg, 0, 4); E(bl, "c_wttb"); E(mov_reg, 5, 0)
    E(movs_imm, 0, 0); E(strb_imm, 0, 5, T_ON)
    E(ldrb_imm, 0, 6, 0); E(cmp_imm, 0, REC_SIG); E(b_cond, "ap_x", "ne")
    E(mov_reg, 0, 6); E(bl, "c_wtsum"); E(ldrb_imm, 1, 6, REC_N - 1); E(cmp_reg, 0, 1); E(b_cond, "ap_x", "ne")
    E(ldrb_imm, 0, 6, 2); E(cmp_imm, 0, NF); E(b_cond, "ap_x", "hi"); E(strb_imm, 0, 5, T_N)
    for k in range(NF): E(ldrb_imm, 0, 6, 3 + k); E(strb_imm, 0, 5, T_F + k)
    E(ldrb_imm, 0, 6, 1); E(strb_imm, 0, 5, T_ON)
    a.label("ap_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_wtblk(r0 = track) -> r0 = its project block (MIDI 2's pattern 5 + t, settings + 8), 0 = no record; clobbers r1-r3
    a.label("c_wtblk")
    imm32(2, PS.SESSION_OBJ); E(ldr_imm, 2, 2, 0x14); E(cmp_imm, 2, 0); E(b_cond, "bk_0", "eq")
    E(adds_imm8, 0, PJ_PAT); imm32(1, PS.PSIZE); E(muls, 0, 1); E(adds_reg, 0, 0, 2); imm32(1, PJ_AREA); E(adds_reg, 0, 0, 1); E(raw, RET)
    a.label("bk_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_wtsave (the bl to the stock's save, its head): projsyn's images' records into the project's blocks, then the chain
    a.label("c_wtsave")
    E(raw, h(0xE92D) + h(0x40FF))                                                       # push.w {r0-r7, lr}
    imm32(0, PS.STR); E(ldr_imm, 1, 0, PS.O_SIG); imm32(2, PS.STSIG); E(cmp_reg, 1, 2); E(b_cond, "sv_n", "ne")
    E(ldrb_imm, 1, 0, PS.O_VALID); E(cmp_imm, 1, 0); E(b_cond, "sv_n", "eq")
    E(movs_imm, 4, 0)
    a.label("sv_t"); E(mov_reg, 0, 4); E(bl, "c_wtblk"); E(cmp_imm, 0, 0); E(b_cond, "sv_n", "eq")
    E(movs_imm, 1, PJ_SIG); E(strb_imm, 1, 0, 0); E(strb_imm, 4, 0, 1)
    imm32(1, PS.IMG0 + REC_AT); E(movs_imm, 2, PS.IMG_SZ); E(muls, 2, 4); E(adds_reg, 1, 1, 2); E(movs_imm, 2, 0)
    a.label("sv_c"); E(ldrb_reg, 3, 1, 2)
    E(adds_reg, 6, 0, 2); E(strb_imm, 3, 6, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, REC_N); E(b_cond, "sv_c", "lo")
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "sv_t", "lo")
    a.label("sv_n"); E(raw, h(0xE8BD) + h(0x40FF)); E(b_w, prev["save"])

    # ---- c_wtld (the LED task's call, its head): a project load's restore pending (projsyn's) = the blocks into its images first; the chain
    a.label("c_wtld")
    E(raw, h(0xE92D) + h(0x40FF))
    imm32(0, PS.STR); E(ldr_imm, 1, 0, PS.O_SIG); imm32(2, PS.STSIG); E(cmp_reg, 1, 2); E(b_cond, "ld_n", "ne")
    E(ldrb_imm, 1, 0, PS.O_PEND); E(cmp_imm, 1, 0); E(b_cond, "ld_n", "eq")
    imm32(0, V.HAL_TICK); E(ldr_imm, 0, 0, 0); imm32(1, PS.BOOT_MS); E(cmp_reg, 0, 1); E(b_cond, "ld_n", "lo")
    E(movs_imm, 4, 0)
    a.label("ld_t"); E(mov_reg, 0, 4); E(bl, "c_wtblk"); E(cmp_imm, 0, 0); E(b_cond, "ld_n", "eq")
    imm32(1, PS.IMG0 + REC_AT); E(movs_imm, 2, PS.IMG_SZ); E(muls, 2, 4); E(adds_reg, 1, 1, 2); E(movs_imm, 2, 0)
    E(ldrb_imm, 3, 0, 0); E(cmp_imm, 3, PJ_SIG); E(b_cond, "ld_z", "ne"); E(ldrb_imm, 3, 0, 1); E(cmp_reg, 3, 4); E(b_cond, "ld_z", "ne")
    a.label("ld_c"); E(adds_reg, 6, 0, 2); E(ldrb_imm, 3, 6, 2); E(strb_reg, 3, 1, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, REC_N); E(b_cond, "ld_c", "lo"); E(b, "ld_e")
    a.label("ld_z"); E(movs_imm, 3, 0); E(strb_reg, 3, 1, 2); E(adds_imm8, 2, 1); E(cmp_imm, 2, REC_N); E(b_cond, "ld_z", "lo")   # none: the wavetable off
    a.label("ld_e"); E(adds_imm8, 4, 1); E(cmp_imm, 4, 2); E(b_cond, "ld_t", "lo")
    a.label("ld_n"); E(raw, h(0xE8BD) + h(0x40FF)); E(b_w, prev["led"])
    return a.assemble()


def install(img, report, base_addr):
    """dspz.add (after fm8): the heads of the template view's slots 0 / 7, the button press, the DSP service chain, mpatch's gather / apply sites
    (vmode's), the save call and the LED calls (fm8store's)."""
    import ct_fw
    import modmx as MX
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_mpon=lab("mpatch", "c_mpon"), c_mpr=lab("mpatch", "c_mpr"), c_msmode=lab("modesel", "c_msmode"), c_fmblk=lab("fm8", "c_fmblk"))
    TP = MP.TMPL_VT
    mpsave, mpload = lab("mpatch", "c_mpsave"), lab("mpatch", "c_mpload")
    gath, appl = lab("vmode", "c_vmgath"), lab("vmode", "c_vmappl")
    prev = dict(pad=u(TP) & ~1, leds=u(TP + 28) & ~1, btn=MP.bw_target(img, MP.BTN_ENTRY, BASE), svc=MP.bw_target(img, S14.SVC_HOOK, BASE),
                gath=gath, appl=appl, save=MX.bl_target(img, P19.SAVE_CALL, BASE), led=MX.bl_target(img, PK.LED_CALLS[0], BASE))
    assert all(MX.bl_target(img, c, BASE) == prev["led"] for c in PK.LED_CALLS)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    struct.pack_into("<I", img, TP - BASE, labels["c_wtpad"] | 1)
    struct.pack_into("<I", img, TP + 28 - BASE, labels["c_wtled"] | 1)
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_wtbtn"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_wttick"])
    for site_of, orig, ours in ((mpsave, gath, "c_wtgath"), (mpload, appl, "c_wtappl")):
        s = MX.bl_sites(img, site_of, site_of + 0x120, orig, BASE)
        assert len(s) == 1, (hex(site_of), [hex(x) for x in s])
        img[s[0] - BASE:s[0] - BASE + 4] = bl(s[0], labels[ours])
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_wtsave"])
    for c in PK.LED_CALLS: img[c - BASE:c - BASE + 4] = bl(c, labels["c_wtld"])
    return labels, code, prev
