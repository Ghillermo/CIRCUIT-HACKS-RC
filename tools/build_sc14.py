"""Circuit Tracks 4486 — SC14 = SC12 + Master FX (Gater + Auto-Filter on the master), Circuit Rhythm style.

UI: FX View (FX button), row 4 pads 2..8 (pad 1 of row 4 keeps its stock function):
  pad 2..5  Gater 1/4, 1/8, 1/16, 1/32   (square LFO on the master output gain, starts open)
  pad 6     Auto-Filter low-pass, 1 bar  (triangle LFO on the master filter position)
  pad 7     Auto-Filter high-pass, 1 bar
  pad 8     Auto-Filter low-pass, 1/8    (wobble)
  Hold = momentary.  Shift + pad = latch on/off.  One Gater and one Auto-Filter at a time
  (the last pressed of each type wins; releasing it falls back to another held/latched pad).
  Rates follow the project tempo; free-running from the press (like Circuit Rhythm).
  Nothing is saved.  Releasing restores the stock master gain / master filter value.

How (ARM only, except one constant in an existing DSP instruction):
  * main loop: 0x080213AA (b.w 0x08028382, DSP service with the DSP lock held) -> c_gtick -> b.w 0x08028382
    writes X:$DE (master output gain, kind 0x21 idx 7) and X:$CF (master filter position, kind 0x21 idx 0)
    with DSP_WRITE(0, v << 24, addr) only when the value changes; time = HAL tick (ms) at 0x2000081C;
    tempo = store [[[0x200069E4]+0x48]+0x48] p0.
  * FX view vtable 0x0805A6E0: slot 0 press, slot 1 release, slot 7 getLeds.
  * state (24 bytes) at the top of the heap: 0x20044E38..0x20044E57.  The bump allocator limit
    [0x20002B44] (0x20044E58) is lowered to 0x20044E38 on first use, so stock allocations can never
    overlap it; if the heap already reaches that far, Master FX stays disabled.
  * DSP core 0, P:$21D9: asr #$b,a,a -> asr #$6,a,a  (master gain ramp: ~1 block instead of ~64 blocks,
    so the Gater is a real gate).  No new DSP code.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc04 as s4  # noqa: E402
import build_sc10 as s10  # noqa: E402
import build_sc12 as s12  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, str_imm, strb_imm, adds_imm8, subs_imm8, adds_reg,
                   subs_reg, ands_reg, orrs_reg, bics_reg, muls, ldrh_reg, strh_imm, strh_reg, cbz, raw, h)

BASE = ct_fw.APP_BASE
MARKER = b"SC14"

ST = 0x20044E38
HEAP_LIMIT_PTR, HEAP_CUR_PTR = 0x20002B44, 0x20002B48
HEAP_LIMIT = 0x20044E58
MAGIC = 0x6F1D0C14
TICK = 0x2000081C
CTX = 0x200069E4
PARAM_GET = 0x0803542C
GETTER = 0x08036192
DSP_WRITE = 0x080292F8
SVC_HOOK, SVC_NEXT = 0x080213AA, 0x08028382
FX_VT = 0x0805A6E0
FX_PRESS, FX_REL, FX_LEDS = 0x080456C0, 0x0804759A, 0x08045722
DSP_RAMP = 0x21D9                    # asr #$b,a,a in func_0021c4 (master gain ramp)
PAD0 = 25                            # row 4, pad 2
# colours (LED codes): Gater = drum 1 colour, Auto-Filter = Synth 2 colour
GAT_DIM, GAT_ON = 0x46, 0x45
AF_DIM, AF_ON = 0x26, 0x20
GAT_DIV = [1, 2, 4, 8]               # 1/4 .. 1/32 : period = 60000 / bpm / div
AF_MODES = [(0, 4, 0), (1, 4, 0), (0, 0, 1)]   # (hp, beats, half-beat) : LP 1 bar, HP 1 bar, LP 1/8
# state offsets
S_MAGIC, S_HELD, S_LATCH, S_GAT, S_AF, S_T0G, S_T0F, S_LGAIN, S_LPOS = 0, 4, 5, 6, 7, 8, 12, 16, 17


def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def mls(rd, rn, rm, ra): return h(0xFB00 | rn) + h(ra << 12 | 0x10 | rd << 8 | rm)


def popw(regs, lr=False):
    return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base):
    a = Asm(base)
    # ---- c_gst: r0 = state or 0 (disabled); clobbers r1-r3
    a.label("c_gst")
    a.emit(movw, 0, ST & 0xFFFF); a.emit(movt, 0, ST >> 16)
    a.emit(movw, 3, HEAP_LIMIT_PTR & 0xFFFF); a.emit(movt, 3, HEAP_LIMIT_PTR >> 16)
    a.emit(ldr_imm, 1, 3, 0)                                                   # heap limit
    a.emit(cmp_reg, 1, 0); a.emit(b_cond, "gs_res", "ne")
    a.emit(ldr_imm, 1, 0, S_MAGIC); a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "gs_ok", "eq")
    a.emit(b, "gs_init")                                                       # limit already ours: re-init
    a.label("gs_res")
    a.emit(movw, 2, HEAP_LIMIT & 0xFFFF); a.emit(movt, 2, HEAP_LIMIT >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "gs_off", "ne")
    a.emit(ldr_imm, 1, 3, 4)                                                   # heap current
    a.emit(cmp_reg, 1, 0); a.emit(b_cond, "gs_off", "hi")
    a.emit(str_imm, 0, 3, 0)                                                   # limit = ST (reserve)
    a.label("gs_init")
    a.emit(movs_imm, 1, 0)
    for off in (4, 8, 12, 16, 20):
        a.emit(str_imm, 1, 0, off)
    a.emit(movs_imm, 1, 0xFF); a.emit(strb_imm, 1, 0, S_LGAIN); a.emit(strb_imm, 1, 0, S_LPOS)
    a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16); a.emit(str_imm, 2, 0, S_MAGIC)
    a.label("gs_ok"); a.emit(raw, h(0x4770))
    a.label("gs_off"); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))

    # ---- c_now: r0 = ms
    a.label("c_now")
    a.emit(movw, 0, TICK & 0xFFFF); a.emit(movt, 0, TICK >> 16); a.emit(ldr_imm, 0, 0, 0); a.emit(raw, h(0x4770))

    # ---- c_beat: r0 = ms per quarter note = 60000 / bpm  (bpm clamped 30..300)
    a.label("c_beat")
    a.emit(push_list, [4], lr=True)
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x48); a.emit(ldr_imm, 0, 0, 0x48)
    a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 1, 0, 0)
    a.emit(cmp_imm, 1, 30); a.emit(b_cond, "bt_lo", "hs"); a.emit(movs_imm, 1, 30)
    a.label("bt_lo")
    a.emit(movw, 0, 60000); a.emit(raw, udiv(0, 0, 1))
    a.emit(pop_list, [4], pc=True)

    # ---- c_wr2(r1 = value 0..127, r2 = X address): DSP_WRITE(0, v << 24, addr)
    a.label("c_wr2")
    a.emit(lsls_imm, 1, 1, 24); a.emit(movs_imm, 0, 0); a.emit(b_w, DSP_WRITE)

    # ---- c_gtick: main loop (DSP service context)
    a.label("c_gtick")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, "c_gst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "gt_out", "eq")
    a.emit(mov_reg, 4, 0)
    # --- Gater
    a.emit(ldrb_imm, 5, 4, S_GAT); a.emit(cmp_imm, 5, 0); a.emit(b_cond, "gt_g_off", "eq")
    a.emit(bl, "c_beat"); a.emit(mov_reg, 6, 0)                               # r6 = beat ms
    a.emit(subs_imm8, 5, 1); a.emit(movs_imm, 1, 1); a.emit(raw, h(0x40A9))   # lsls r1,r5 -> div  (r1 = 1 << idx)
    a.emit(raw, udiv(6, 6, 1))                                               # period
    a.emit(cmp_imm, 6, 2); a.emit(b_cond, "gt_g_p", "hs"); a.emit(movs_imm, 6, 2)
    a.label("gt_g_p")
    a.emit(bl, "c_now"); a.emit(ldr_imm, 1, 4, S_T0G); a.emit(subs_reg, 0, 0, 1)
    a.emit(raw, udiv(1, 0, 6)); a.emit(raw, mls(0, 1, 6, 0))                 # r0 = elapsed % period
    a.emit(lsrs_imm, 1, 6, 1); a.emit(cmp_reg, 0, 1)
    a.emit(b_cond, "gt_g_closed", "hs")
    a.emit(movs_imm, 0, 0x21); a.emit(movs_imm, 1, 7); a.emit(bl, GETTER)    # open = stock gain
    a.emit(mov_reg, 5, 0); a.emit(b, "gt_g_set")
    a.label("gt_g_closed"); a.emit(movs_imm, 5, 0); a.emit(b, "gt_g_set")
    a.label("gt_g_off")
    a.emit(ldrb_imm, 0, 4, S_LGAIN); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "gt_af", "eq")
    a.emit(movs_imm, 0, 0x21); a.emit(movs_imm, 1, 7); a.emit(bl, GETTER)
    a.emit(mov_reg, 1, 0); a.emit(movs_imm, 2, 0xDE); a.emit(bl, "c_wr2")     # restore stock gain
    a.emit(movs_imm, 0, 0xFF); a.emit(strb_imm, 0, 4, S_LGAIN); a.emit(b, "gt_af")
    a.label("gt_g_set")
    a.emit(ldrb_imm, 0, 4, S_LGAIN); a.emit(cmp_reg, 0, 5); a.emit(b_cond, "gt_af", "eq")
    a.emit(strb_imm, 5, 4, S_LGAIN); a.emit(mov_reg, 1, 5); a.emit(movs_imm, 2, 0xDE); a.emit(bl, "c_wr2")
    # --- Auto-Filter
    a.label("gt_af")
    a.emit(ldrb_imm, 5, 4, S_AF); a.emit(cmp_imm, 5, 0); a.emit(b_cond, "gt_f_off", "eq")
    a.emit(bl, "c_beat"); a.emit(mov_reg, 6, 0)
    a.emit(cmp_imm, 5, 3); a.emit(b_cond, "gt_f_bar", "ne")
    a.emit(lsrs_imm, 6, 6, 1); a.emit(b, "gt_f_p")                            # LP 1/8: period = half beat
    a.label("gt_f_bar"); a.emit(lsls_imm, 6, 6, 2)                            # 1 bar = 4 beats
    a.label("gt_f_p")
    a.emit(cmp_imm, 6, 4); a.emit(b_cond, "gt_f_p2", "hs"); a.emit(movs_imm, 6, 4)
    a.label("gt_f_p2")
    a.emit(bl, "c_now"); a.emit(ldr_imm, 1, 4, S_T0F); a.emit(subs_reg, 0, 0, 1)
    a.emit(raw, udiv(1, 0, 6)); a.emit(raw, mls(0, 1, 6, 0))                 # x = elapsed % period
    a.emit(lsrs_imm, 7, 6, 1)                                                 # half
    a.emit(cmp_reg, 0, 7); a.emit(b_cond, "gt_f_up", "lo")
    a.emit(subs_reg, 0, 6, 0)                                                 # down slope: period - x
    a.label("gt_f_up")
    a.emit(movs_imm, 1, 56); a.emit(muls, 0, 1)                               # depth 56 * x / half
    a.emit(raw, udiv(0, 0, 7))
    a.emit(cmp_imm, 0, 56); a.emit(b_cond, "gt_f_c", "ls"); a.emit(movs_imm, 0, 56)
    a.label("gt_f_c")
    a.emit(movs_imm, 1, 64)
    a.emit(cmp_imm, 5, 2); a.emit(b_cond, "gt_f_hp", "eq")
    a.emit(subs_reg, 5, 1, 0); a.emit(b, "gt_f_set")                          # LP: 64 - sweep
    a.label("gt_f_hp"); a.emit(adds_reg, 5, 1, 0)                             # HP: 64 + sweep
    a.label("gt_f_set")
    a.emit(ldrb_imm, 0, 4, S_LPOS); a.emit(cmp_reg, 0, 5); a.emit(b_cond, "gt_out", "eq")
    a.emit(strb_imm, 5, 4, S_LPOS); a.emit(mov_reg, 1, 5); a.emit(movs_imm, 2, 0xCF); a.emit(bl, "c_wr2")
    a.emit(b, "gt_out")
    a.label("gt_f_off")
    a.emit(ldrb_imm, 0, 4, S_LPOS); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "gt_out", "eq")
    a.emit(movs_imm, 0, 0x21); a.emit(movs_imm, 1, 0); a.emit(bl, GETTER)
    a.emit(mov_reg, 1, 0); a.emit(movs_imm, 2, 0xCF); a.emit(bl, "c_wr2")     # restore stock filter
    a.emit(movs_imm, 0, 0xFF); a.emit(strb_imm, 0, 4, S_LPOS)
    a.label("gt_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, SVC_NEXT)

    # ---- c_gpick(r4 = st, r1 = type 0 gater / 1 AF): active of that type = highest held|latched pad of it, else 0
    a.label("c_gpick")
    a.emit(ldrb_imm, 2, 4, S_HELD); a.emit(ldrb_imm, 3, 4, S_LATCH); a.emit(orrs_reg, 2, 3)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "pk_af", "ne")
    a.emit(movs_imm, 3, 0xF); a.emit(ands_reg, 2, 3); a.emit(movs_imm, 0, 0)
    a.label("pk_g")
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pk_gs", "eq")
    a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 2, 2, 1); a.emit(b, "pk_g")
    a.label("pk_gs")
    a.emit(ldrb_imm, 3, 4, S_GAT); a.emit(cmp_reg, 3, 0); a.emit(b_cond, "pk_ret", "eq")
    a.emit(strb_imm, 0, 4, S_GAT); a.emit(raw, h(0x4770))
    a.label("pk_af")
    a.emit(lsrs_imm, 2, 2, 4); a.emit(movs_imm, 0, 0)
    a.label("pk_f")
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pk_fs", "eq")
    a.emit(adds_imm8, 0, 1); a.emit(lsrs_imm, 2, 2, 1); a.emit(b, "pk_f")
    a.label("pk_fs")
    a.emit(ldrb_imm, 3, 4, S_AF); a.emit(cmp_reg, 3, 0); a.emit(b_cond, "pk_ret", "eq")
    a.emit(strb_imm, 0, 4, S_AF)
    a.label("pk_ret"); a.emit(raw, h(0x4770))

    # ---- c_fxpress(view, pad, vel)
    a.label("c_fxpress")
    a.emit(cmp_imm, 1, PAD0); a.emit(b_cond, "fp_me", "hs"); a.emit(b_w, FX_PRESS)
    a.label("fp_me")
    a.emit(cmp_imm, 1, 32); a.emit(b_cond, "fp_ret", "hs")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(subs_imm8, 1, PAD0); a.emit(mov_reg, 5, 1)                         # r5 = idx 0..6
    a.emit(bl, "c_gst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fp_out", "eq"); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 6, 1); a.emit(raw, h(0x40AE))                            # lsls r6,r5 : bit
    # shift held?
    a.emit(movw, 0, CTX & 0xFFFF); a.emit(movt, 0, CTX >> 16)
    a.emit(ldr_imm, 0, 0, 0); a.emit(ldr_imm, 0, 0, 0x40); a.emit(ldr_imm, 0, 0, 0x0C)
    a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fp_hold", "eq")
    a.emit(ldrb_imm, 0, 4, S_LATCH); a.emit(raw, h(0x4070))                  # eors r0,r6  (toggle latch)
    a.emit(strb_imm, 0, 4, S_LATCH); a.emit(raw, h(0x4230))                  # tst r0,r6
    a.emit(b_cond, "fp_act", "ne")
    a.emit(b, "fp_repick")                                                    # unlatched: fall back
    a.label("fp_hold")
    a.emit(ldrb_imm, 0, 4, S_HELD); a.emit(orrs_reg, 0, 6); a.emit(strb_imm, 0, 4, S_HELD)
    a.label("fp_act")                                                         # activate idx r5 now
    a.emit(bl, "c_now"); a.emit(mov_reg, 1, 0)
    a.emit(cmp_imm, 5, 4); a.emit(b_cond, "fp_af", "hs")
    a.emit(adds_imm8, 5, 1); a.emit(strb_imm, 5, 4, S_GAT); a.emit(str_imm, 1, 4, S_T0G); a.emit(b, "fp_out")
    a.label("fp_af")
    a.emit(subs_imm8, 5, 3); a.emit(strb_imm, 5, 4, S_AF); a.emit(str_imm, 1, 4, S_T0F); a.emit(b, "fp_out")
    a.label("fp_repick")
    a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 5, 4); a.emit(b_cond, "fp_rp", "lo"); a.emit(movs_imm, 1, 1)
    a.label("fp_rp"); a.emit(bl, "c_gpick_t")
    a.label("fp_out")
    a.emit(pop_list, [4, 5, 6], pc=True)
    a.label("fp_ret"); a.emit(raw, h(0x4770))

    # ---- c_gpick_t: c_gpick and restart the time base if the active pad changed
    a.label("c_gpick_t")
    a.emit(push_list, [5, 6, 7], lr=True)
    a.emit(mov_reg, 7, 1)
    a.emit(ldrb_imm, 5, 4, S_GAT); a.emit(ldrb_imm, 6, 4, S_AF)
    a.emit(bl, "c_gpick")
    a.emit(bl, "c_now")
    a.emit(ldrb_imm, 1, 4, S_GAT); a.emit(cmp_reg, 1, 5); a.emit(b_cond, "pt_f", "eq"); a.emit(str_imm, 0, 4, S_T0G)
    a.label("pt_f")
    a.emit(ldrb_imm, 1, 4, S_AF); a.emit(cmp_reg, 1, 6); a.emit(b_cond, "pt_out", "eq"); a.emit(str_imm, 0, 4, S_T0F)
    a.label("pt_out")
    a.emit(pop_list, [5, 6, 7], pc=True)

    # ---- c_fxrel(view, pad, x)
    a.label("c_fxrel")
    a.emit(cmp_imm, 1, PAD0); a.emit(b_cond, "fr_me", "hs"); a.emit(b_w, FX_REL)
    a.label("fr_me")
    a.emit(cmp_imm, 1, 32); a.emit(b_cond, "fp_ret", "hs")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(subs_imm8, 1, PAD0); a.emit(mov_reg, 5, 1)
    a.emit(bl, "c_gst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fr_out", "eq"); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 6, 1); a.emit(raw, h(0x40AE))                            # bit
    a.emit(ldrb_imm, 0, 4, S_HELD); a.emit(bics_reg, 0, 6); a.emit(strb_imm, 0, 4, S_HELD)
    a.emit(movs_imm, 1, 0); a.emit(cmp_imm, 5, 4); a.emit(b_cond, "fr_rp", "lo"); a.emit(movs_imm, 1, 1)
    a.label("fr_rp"); a.emit(bl, "c_gpick_t")
    a.label("fr_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_fxleds(view): stock LEDs + row 4 pads 2..8
    a.label("c_fxleds")
    a.emit(push_list, [3, 4, 5, 6, 7], lr=True)
    a.emit(bl, FX_LEDS); a.emit(mov_reg, 6, 0)                                # r6 = buffer
    a.emit(bl, "c_gst"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "fl_out", "eq"); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 5, 0)
    a.label("fl_l")
    a.emit(cmp_imm, 5, 4); a.emit(b_cond, "fl_af", "hs")
    a.emit(movs_imm, 1, GAT_DIM); a.emit(movs_imm, 2, GAT_ON); a.emit(ldrb_imm, 3, 4, S_GAT)
    a.emit(mov_reg, 0, 5); a.emit(adds_imm8, 0, 1); a.emit(b, "fl_c")           # pad idx + 1 = gater code
    a.label("fl_af")
    a.emit(movs_imm, 1, AF_DIM); a.emit(movs_imm, 2, AF_ON); a.emit(ldrb_imm, 3, 4, S_AF)
    a.emit(mov_reg, 0, 5); a.emit(subs_imm8, 0, 3)                             # pad idx - 3 = AF code
    a.label("fl_c")
    a.emit(cmp_reg, 0, 3); a.emit(b_cond, "fl_s", "ne"); a.emit(mov_reg, 1, 2)
    a.label("fl_s")
    a.emit(mov_reg, 7, 5); a.emit(adds_imm8, 7, PAD0); a.emit(lsls_imm, 7, 7, 1)
    a.emit(strh_reg, 1, 6, 7)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 7); a.emit(b_cond, "fl_l", "lo")
    a.label("fl_out")
    a.emit(mov_reg, 0, 6)
    a.emit(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def build(stock: bytes, listing: Path):
    img12, report = s12.build(stock, listing)
    img = bytearray(img12)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER
    # DSP: master gain ramp
    off = s10.p_off(DSP_RAMP)
    assert int.from_bytes(img[off:off + 3], 'big') == 0x0C1C16
    img[off:off + 3] = (0x0C1C0C).to_bytes(3, 'big')
    # ARM
    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    assert text(SVC_HOOK, 4) == "b.w #0x8028382", text(SVC_HOOK, 4)
    assert [struct.unpack_from("<I", img, FX_VT + 4 * i - BASE)[0] for i in (0, 1, 7)] == [FX_PRESS | 1, FX_REL | 1, FX_LEDS | 1]
    assert text(FX_REL, 2) == "bx lr"
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext)
    img[SVC_HOOK - BASE:SVC_HOOK - BASE + 4] = b_w(SVC_HOOK, labels["c_gtick"])
    for slot, lab in ((0, "c_fxpress"), (1, "c_fxrel"), (7, "c_fxleds")):
        struct.pack_into("<I", img, FX_VT + 4 * slot - BASE, labels[lab] | 1)
    img += b"\xFF" * (ext - BASE - len(img)) + code
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc14"] = dict(arm_start=hex(ext), labels={k: hex(v) for k, v in labels.items()},
                          listing=sc.disasm(code, ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc14"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC14.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC14.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC14", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("arm", report["sc14"]["arm_start"], "image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
