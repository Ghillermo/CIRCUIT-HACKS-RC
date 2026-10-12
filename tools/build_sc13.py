"""Circuit Tracks 4486 — SC13 = SC12 + side-chain on the drum tracks (triggered by drums).

UI (Side Chain View, Shift + FX):
  stock pages Synth 1/2 -> MIDI 1/2 with the down/up buttons; SC13 adds two more pages below:
  Drums 1/2 and Drums 3/4.  On a drum page:
    rows 3 / 4  : OFF + 7 presets (same presets as stock) for the two drums of the page
    top row 5-8 : trigger drum for the drum chosen last (row pressed last; first row on entry)
  Entering the view with a drum track selected opens that drum's page.
  Not saved: power-up -> all OFF, trigger = drum 1.

ARM state (RAM 0x2004E000, beyond the heap limit 0x20044E58 and below the main stack 0x2004FE00;
never written in stock — power-up garbage in the live dumps):
  +0 magic, +4 preset[4], +8 src[4], +12 dpage (0 = stock pages, 2 / 3 = drum pages), +13 chosen drum.
  The stock page store only ever holds 0/1 (it may be persisted), the drum pages live in RAM.

DSP core 0:
  X:$EB          SC10 FX-return flags (moved from X:$EC)
  X:$EC + 9k     drum k side-chain block: [trigger, attack, hold, decay, depth, state0..3]
                 (params as the stock synth side-chain X:$3F2 block, state copied to Y:$2048 for func_0012bb)
  P:$80 (SC10 init_hook, jsr'd at DSP start)  clears X:$EB..$10F (rep)
  P:$218E  jsr mixhook: drum d about to be mixed: if depth != 0, advance the envelope (stock func_0012bb,
           state copied X <-> Y:$2048, output Y:$2028 scratch) and multiply the mono signal X:$2C02
           (before dry / reverb / delay); mark the block "advanced" (bit 1 of word 0).
  P:$21AB  jmp idle (was the rts ending every drum voice, also the early exit of a silent voice):
           if the envelope of this drum was not advanced this block, advance it anyway, so the ducking
           runs in time even while the ducked drum is silent.
  Trigger: the ARM drum-trigger function also writes block word 0 = 1 for every drum-target whose
  trigger drum just fired (DSP consumes it with bclr, like the stock X:$99+d bits).
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc04 as s4  # noqa: E402
import build_sc10 as s10  # noqa: E402
import build_sc12 as s12  # noqa: E402
import dsp56 as D  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, str_imm, strb_imm, adds_imm8, adds_imm3, subs_imm8,
                   subs_imm3, adds_reg, ands_reg, orrs_reg, ldrh_reg, strh_reg, strh_imm, cbz, raw, h, ldrb_w)

BASE = ct_fw.APP_BASE
MARKER = b"SC13"
import sys as _sys; _sys.path.insert(0, __import__("os").path.dirname(__file__))
from dsptool_path import TOOL  # noqa: E402

# ---------------- DSP
FLAGS_NEW = 0xEB
BLK = 0xEC                         # X:$EC + 9k
ENV, STATE, SAVE_R5 = 0x2028, 0x2048, 0x204C
FUNC_12BB = 0x12BB
MIX_HOOK = 0x218E                  # move #>$2e70,r0 (2 words)
IDLE_HOOK = 0x21AB                 # rts ending every drum voice (also the "voice idle" exit)
REG_B, REG_B_END = 0x54, 0x80      # timer / HDI08 / ESAI_1 vectors (disabled: IPRP = 9)
REG_A_END = 0x100                  # after the SC10 code

# ---------------- ARM
ST = 0x2004E000
MAGIC = 0x5C13D5C1
PAL = 0x08056464
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
MARK_DIRTY = 0x0803BDCC
CONV_ATK, CONV_HD = 0x08028764, 0x08028778
SC1_GROUP = 0x08028C9C             # project group 5: Synth 1 side-chain (+ level / pan)
GROUP_TAB = 0x0805B3B0
TRIG_TAIL = 0x08051B7C             # b.w DSP_WRITE  (X:$99+d = 0xF in the drum trigger function)
VIEW_VT = 0x0805AC2C               # Side Chain view: slot 0 pad, slot 7 getLeds
VIEW_PAD, VIEW_LEDS = 0x0804D6FE, 0x0804D77A
PG_VT_SLOT8 = 0x0805AA8C           # pager slot 8: paint up/down LEDs (this = pager)
PG_VT_LST = 0x0805AA98             # pager store-listener interface slot (this = pager + 8)
PG_DOWN, PG_UP = 0x0804FB66, 0x0804FB86
CONT_DOWN_BW, CONT_UP_BW = 0x08043664, 0x08043702
ENTRY = 0x0804352A                 # cmp r0,#4 ; bge 0x08043598   (mode change, r0 = track, r5 = container)
ENTRY_GE, ENTRY_LT = 0x08043598, 0x0804352E
# stock presets (attack, hold, decay, depth) for OFF and 1..7 (read from the Synth 1 row in emulation)
PRESETS = [(0, 50, 70, 0), (5, 50, 80, 80), (5, 70, 70, 100), (5, 85, 70, 115),
           (5, 90, 75, 123), (5, 90, 85, 127), (5, 95, 95, 127), (5, 102, 95, 127)]


def popw(regs, lr=False):
    m = sum(1 << r for r in regs) | (1 << 14 if lr else 0)
    return h(0xE8BD) + h(m)


# ---------------------------------------------------------------- DSP assembler helpers
_cache = {}


def dasm(lines):
    todo = [l for l in lines if l not in _cache]
    if todo:
        import dspasm_cache
        for l, ws in zip(todo, dspasm_cache.assemble(todo)): _cache[l] = ws
    return [w for l in lines for w in _cache[l]]


def ddis(words):
    lines, i = [], 0
    while i < len(words):
        lines.append("%06x %06x" % (words[i], words[i + 1] if i + 1 < len(words) else 0)); i += 1
    try:
        out = subprocess.run([TOOL, "dis"], input="\n".join(lines) + "\n", capture_output=True, text=True).stdout.splitlines()
    except OSError:                                                   # no dsptool: no listing (the image does not depend on it)
        return []
    res, i = [], 0
    while i < len(words):
        n, txt = out[i].split(" ", 1)
        res.append(txt.strip()); i += int(n)
    return res


def T(text):        # one text instruction (encoded by dsp56kEmu's assembler, checked with its disassembler)
    return dasm([text])


def do_imm(n, last): return [0x060080 | (n & 0xFF) << 8 | (n >> 8) & 0xF, last]
def jeq_s(t): assert t < 0x1000; return [0x0EA000 | t]          # jeq  (short, 12-bit absolute)
def jcs_s(t): assert t < 0x1000; return [0x0E8000 | t]          # jcs  (short)
def jmp_s(t): assert t < 0x1000; return [0x0C0000 | t]          # jmp  (short)


def dsp_region_b():
    """subroutines: getblk (r0 = block of the current drum, a = depth, Z if off) and advance (envelope)."""
    a = D.Asm(REG_B)
    a.label("getblk")                                                       # x:$1ed6 = $9f + d
    a.emit(T("move x:>$1ed6,b")); a.emit(T("move b1,x0")); a.emit(T("asl #3,b,b")); a.emit(T("add x0,b"))
    a.emit(T("add #>$%x,b" % ((BLK - 9 * 0x9F) & 0xFFFFFF)))               # 9 * ($9f + d) - 9 * $9f + $ec
    a.emit(T("move b1,r0")); a.emit(D.NOP)
    a.emit([0x02109E])                                                      # move x:(r0+$4),a   (depth)
    a.emit(T("tst a")); a.emit(D.RTS)
    a.label("advance")                                                      # envelope of block r0 -> Y:$2028
    a.emit([0x040051])                                                      # lua (r0+$5),r1
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(do_imm, 4, "ad_c1")
    a.emit(T("move x:(r1)+,x0"))
    a.label("ad_c1"); a.emit(T("move x0,y:(r4)+"))
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(T("move y:(r4),a"))           # phase
    a.emit(T("move #>$2,x0")); a.emit([0x0A6000])                           # bclr #0,x:(r0)  (trigger)
    a.emit(T("tfr x0,a ifcs")); a.emit([0x0204F6])                          # move y:(r4+$1),y0
    a.emit(T("move #>$%x,r5" % ENV)); a.emit(D.jsr(FUNC_12BB))
    a.emit([0x040051])                                                      # lua (r0+$5),r1
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(do_imm, 4, "ad_c2")
    a.emit(T("move y:(r4)+,x0"))
    a.label("ad_c2"); a.emit(T("move x0,x:(r1)+"))
    a.emit(D.RTS)
    return a


def dsp_region_a(base, lb):
    a = D.Asm(base)
    a.label("mixhook")                                                      # P:$218E: drum voice about to be mixed
    a.emit(T("move r5,y:>$%x" % SAVE_R5))
    a.emit(D.jsr(lb["getblk"])); a.emit(jeq_s, "mh_out")
    a.emit(D.jsr(lb["advance"]))
    a.emit([0x0A6021])                                                      # bset #1,x:(r0)  (advanced this block)
    a.emit(T("move #>$2c02,r1")); a.emit(T("move #>$%x,r5" % ENV))
    a.emit(D.do_x, 0x3A, "mh_c3")
    a.emit([0xF0A100])                                                      # move x:(r1),x0  y:(r5)+,y0
    a.emit(D.MPY_Y0X0_A)
    a.label("mh_c3"); a.emit(T("move a,x:(r1)+"))
    a.label("mh_out")
    a.emit(T("move y:>$%x,r5" % SAVE_R5)); a.emit(T("move #>$2e70,r0")); a.emit(D.RTS)
    a.label("idle")                                                         # P:$21AB (end of every drum voice)
    a.emit(T("move r5,y:>$%x" % SAVE_R5))
    a.emit(D.jsr(lb["getblk"])); a.emit(jeq_s, "id_out")
    a.emit([0x0A6001]); a.emit(jcs_s, "id_out")                             # bclr #1,x:(r0): mixed -> done
    a.emit(D.jsr(lb["advance"]))                                            # silent voice: keep the envelope running
    a.label("id_out")
    a.emit(T("move y:>$%x,r5" % SAVE_R5)); a.emit(D.RTS)
    return a


def init_words():           # replaces SC10's 7-word init_hook at P:$80 (jsr'd from P:$10B)
    return (D.CLR_A + T("move #$%x,r0" % FLAGS_NEW) + T("rep #%d" % (0x110 - FLAGS_NEW))
            + T("move a,x:(r0)+") + D.move_imm_r(0, 0x2028) + D.RTS)


def two_region(a_base):
    wb, lb = dsp_region_b().assemble()
    wa, la = dsp_region_a(a_base, lb).assemble()
    return wa, la, wb, lb


# ---------------------------------------------------------------- ARM
def arm_code(base):
    a = Asm(base)
    # ---- c_scst: r0 = state (validated); clobbers r1, r2
    a.label("c_scst")
    a.emit(movw, 0, ST & 0xFFFF); a.emit(movt, 0, ST >> 16)
    a.emit(ldr_imm, 1, 0, 0)
    a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "st_ok", "eq")
    a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 0, 4); a.emit(str_imm, 1, 0, 8); a.emit(str_imm, 1, 0, 12)
    a.emit(str_imm, 2, 0, 0)
    a.label("st_ok"); a.emit(raw, h(0x4770))                                  # bx lr

    # ---- c_wr: DSP_WRITE(0, r1, BLK + 9*r5 + r2)
    a.label("c_wr")
    a.emit(lsls_imm, 0, 5, 3); a.emit(adds_reg, 0, 0, 5); a.emit(adds_reg, 2, 2, 0)
    a.emit(adds_imm8, 2, BLK); a.emit(movs_imm, 0, 0); a.emit(b_w, DSP_WRITE)

    # ---- c_scgrp: project group 5 handler = stock + the 4 drum side-chain parameter sets
    a.label("c_scgrp")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(bl, SC1_GROUP)
    a.emit(bl, "c_scst"); a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0)
    a.label("gr_l")
    a.emit(adds_reg, 0, 4, 5); a.emit(ldrb_imm, 6, 0, 4); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 6, 1)
    a.emit(lsls_imm, 6, 6, 2)
    a.emit(movw, 1, 0); a.emit(movt, 1, 0)                                    # patched: preset table
    a.label("gr_tab_fix")
    a.emit(adds_reg, 6, 6, 1)
    for off, conv in ((0, CONV_ATK), (1, CONV_HD), (2, CONV_HD)):
        a.emit(ldrb_imm, 0, 6, off); a.emit(bl, conv); a.emit(mov_reg, 1, 0)
        a.emit(movs_imm, 2, off + 1); a.emit(bl, "c_wr")
    a.emit(ldrb_imm, 1, 6, 3); a.emit(lsls_imm, 1, 1, 24); a.emit(movs_imm, 2, 4); a.emit(bl, "c_wr")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 4); a.emit(b_cond, "gr_l", "lo")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_trig: tail of the drum trigger function (r0 = 0, r1 = 0xF00, r2 = 0x99 + d)
    a.label("c_trig")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 2); a.emit(subs_imm8, 4, 0x99)
    a.emit(bl, DSP_WRITE)
    a.emit(bl, "c_scst"); a.emit(mov_reg, 6, 0); a.emit(movs_imm, 5, 0)
    a.label("tg_l")
    a.emit(adds_reg, 0, 6, 5); a.emit(ldrb_imm, 1, 0, 4); a.emit(cbz, "tg_n", 1)
    a.emit(ldrb_imm, 1, 0, 8); a.emit(cmp_reg, 1, 4); a.emit(b_cond, "tg_n", "ne")
    a.emit(movs_imm, 1, 1); a.emit(lsls_imm, 1, 1, 8); a.emit(movs_imm, 2, 0); a.emit(bl, "c_wr")
    a.label("tg_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 4); a.emit(b_cond, "tg_l", "lo")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_scpad: Side Chain view slot 0 (view, pad, vel)
    a.label("c_scpad")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, "c_scst"); a.emit(ldrb_imm, 3, 0, 12); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "sp_d", "ne")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, VIEW_PAD)
    a.label("sp_d")
    a.emit(mov_reg, 4, 0); a.emit(subs_imm8, 3, 2); a.emit(lsls_imm, 3, 3, 1)  # r3 = first drum of the page
    a.emit(cmp_imm, 5, 4); a.emit(b_cond, "sp_out", "lo")
    a.emit(cmp_imm, 5, 8); a.emit(b_cond, "sp_src", "lo")
    a.emit(cmp_imm, 5, 16); a.emit(b_cond, "sp_out", "lo")
    a.emit(cmp_imm, 5, 32); a.emit(b_cond, "sp_out", "hs")
    a.emit(subs_imm8, 5, 16); a.emit(lsrs_imm, 2, 5, 3); a.emit(adds_reg, 3, 3, 2)
    a.emit(movs_imm, 2, 7); a.emit(ands_reg, 5, 2)
    a.emit(adds_reg, 0, 4, 3); a.emit(strb_imm, 5, 0, 4); a.emit(strb_imm, 3, 4, 13)
    a.emit(b, "sp_send")
    a.label("sp_src")
    a.emit(subs_imm8, 5, 4); a.emit(ldrb_imm, 3, 4, 13); a.emit(adds_reg, 0, 4, 3); a.emit(strb_imm, 5, 0, 8)
    a.label("sp_send")
    a.emit(movs_imm, 0, 0x20); a.emit(movs_imm, 1, 26); a.emit(bl, MARK_DIRTY)
    a.label("sp_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_scleds: Side Chain view slot 7 (getLeds)
    a.label("c_scleds")
    a.emit(push_list, [3, 4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(mov_reg, 5, 0)
    a.emit(ldrb_imm, 0, 5, 12); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_d", "ne")
    a.emit(mov_reg, 0, 4); a.emit(raw, popw([3, 4, 5, 6, 7], lr=True)); a.emit(b_w, VIEW_LEDS)
    a.label("sl_d")
    a.emit(ldr_imm, 6, 4, 4); a.emit(ldr_imm, 6, 6, 0)
    a.emit(movw, 7, PAL & 0xFFFF); a.emit(movt, 7, PAL >> 16)
    a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
    a.label("sl_clr"); a.emit(lsls_imm, 2, 1, 1); a.emit(strh_reg, 0, 6, 2)
    a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 32); a.emit(b_cond, "sl_clr", "lo")
    # top row pads 4..7: trigger drum of the chosen drum
    a.emit(ldrb_imm, 3, 5, 13); a.emit(adds_reg, 0, 5, 3); a.emit(ldrb_imm, 2, 0, 8)
    a.emit(movs_imm, 1, 0)
    a.label("sl_src")
    a.emit(movs_imm, 0, 0x13); a.emit(cmp_reg, 1, 2); a.emit(b_cond, "sl_s1", "ne")
    a.emit(adds_imm3, 0, 3, 5)
    a.label("sl_s1")
    a.emit(lsls_imm, 0, 0, 1); a.emit(ldrh_reg, 0, 7, 0)
    a.emit(adds_imm3, 4, 1, 4); a.emit(lsls_imm, 4, 4, 1); a.emit(strh_reg, 0, 6, 4)
    a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 4); a.emit(b_cond, "sl_src", "lo")
    # rows 3 / 4
    a.emit(ldrb_imm, 3, 5, 12); a.emit(subs_imm8, 3, 2); a.emit(lsls_imm, 3, 3, 1)
    a.emit(movs_imm, 1, 0)
    a.label("sl_row")
    a.emit(lsrs_imm, 2, 1, 3); a.emit(adds_reg, 2, 2, 3)                     # r2 = drum
    a.emit(adds_reg, 0, 5, 2); a.emit(ldrb_imm, 0, 0, 4)                     # r0 = preset
    a.emit(movs_imm, 4, 7); a.emit(ands_reg, 4, 1)                           # r4 = column
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "sl_col", "ne")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_offon", "eq")
    a.emit(movs_imm, 0, 0x46); a.emit(b, "sl_put")
    a.label("sl_offon"); a.emit(movs_imm, 0, 0x19); a.emit(b, "sl_put")
    a.label("sl_col")
    a.emit(cmp_reg, 4, 0); a.emit(b_cond, "sl_dim", "ne")
    a.emit(adds_imm3, 0, 2, 5); a.emit(b, "sl_put")
    a.label("sl_dim"); a.emit(mov_reg, 0, 2); a.emit(adds_imm8, 0, 0xD)
    a.label("sl_put")
    a.emit(lsls_imm, 0, 0, 1); a.emit(ldrh_reg, 0, 7, 0)
    a.emit(mov_reg, 4, 1); a.emit(adds_imm8, 4, 16); a.emit(lsls_imm, 4, 4, 1)
    a.emit(strh_reg, 0, 6, 4)
    a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 16); a.emit(b_cond, "sl_row", "lo")
    a.emit(mov_reg, 0, 6)
    a.emit(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_pgpaint(pager): up / down button LEDs
    a.label("c_pgpaint")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(ldrb_imm, 5, 0, 12)
    a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(orrs_reg, 0, 5)
    a.emit(movw, 6, PAL & 0xFFFF); a.emit(movt, 6, PAL >> 16)
    a.emit(ldr_imm, 1, 4, 4); a.emit(ldr_imm, 1, 1, 0)
    # buffer[0] = down, buffer[1] = up; palette 0x25A = lit, 0x25C = unlit (as stock 0x0804FBBA)
    a.emit(movw, 2, 0x25A); a.emit(cmp_imm, 5, 3); a.emit(b_cond, "pp_d", "ne"); a.emit(movw, 2, 0x25C)
    a.label("pp_d"); a.emit(ldrh_reg, 2, 6, 2); a.emit(strh_imm, 2, 1, 0)
    a.emit(movw, 2, 0x25C); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pp_u", "eq"); a.emit(movw, 2, 0x25A)
    a.label("pp_u"); a.emit(ldrh_reg, 2, 6, 2); a.emit(strh_imm, 2, 1, 2)
    a.emit(pop_list, [4, 5, 6], pc=True)
    a.label("c_pglst")                                                        # pager store listener (this = obj+8)
    a.emit(subs_imm8, 0, 8); a.emit(b, "c_pgpaint")

    # ---- c_pgdn / c_pgup (pager in r0)
    for name, stock, is_dn in (("c_pgdn", PG_DOWN, True), ("c_pgup", PG_UP, False)):
        a.label(name)
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(mov_reg, 5, 0); a.emit(ldrb_imm, 6, 5, 12)
        a.emit(cmp_imm, 6, 0); a.emit(b_cond, name + "_d", "ne")
        if is_dn:
            a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
            a.emit(cmp_imm, 0, 1); a.emit(b_cond, name + "_to2", "eq")
        a.emit(mov_reg, 0, 4); a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, stock)
        if is_dn:
            a.label(name + "_to2"); a.emit(movs_imm, 6, 2); a.emit(movs_imm, 1, 0); a.emit(b, name + "_set")
            a.label(name + "_d")
            a.emit(cmp_imm, 6, 3); a.emit(b_cond, name + "_out", "hs")
            a.emit(movs_imm, 6, 3); a.emit(movs_imm, 1, 2)
        else:
            a.label(name + "_d")
            a.emit(movs_imm, 1, 0)
            a.emit(cmp_imm, 6, 3); a.emit(b_cond, name + "_to0", "ne")
            a.emit(movs_imm, 6, 2); a.emit(b, name + "_set")
            a.label(name + "_to0"); a.emit(movs_imm, 6, 0)
        a.label(name + "_set")
        a.emit(strb_imm, 6, 5, 12); a.emit(strb_imm, 1, 5, 13)
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_pgpaint")
        a.label(name + "_out")
        a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_scentry: mode change (r0 = selected track, r5 = container, mode already stored)
    a.label("c_scentry")
    a.emit(push_list, [0, 1])
    a.emit(ldrb_w, 1, 5, 0x18C); a.emit(cmp_imm, 1, 7); a.emit(b_cond, "ce_out", "ne")
    a.emit(bl, "c_scst")
    a.emit(raw, h(0x9900))                                                    # ldr r1,[sp,#0]  (track)
    a.emit(movs_imm, 2, 0); a.emit(movs_imm, 3, 0)
    a.emit(subs_imm8, 1, 4); a.emit(b_cond, "ce_set", "lo")                  # synth / MIDI track -> stock pages
    a.emit(cmp_imm, 1, 4); a.emit(b_cond, "ce_out", "hs")
    a.emit(mov_reg, 3, 1); a.emit(lsrs_imm, 2, 1, 1); a.emit(adds_imm8, 2, 2)
    a.label("ce_set")
    a.emit(strb_imm, 2, 0, 12); a.emit(strb_imm, 3, 0, 13)
    a.label("ce_out")
    a.emit(pop_list, [0, 1])
    a.emit(cmp_imm, 0, 4); a.emit(b_cond, "ce_lt", "lt")
    a.emit(b_w, ENTRY_GE)
    a.label("ce_lt"); a.emit(b_w, ENTRY_LT)
    return a.assemble()


def build(stock: bytes, listing: Path):
    s10.FLAGS = FLAGS_NEW                             # SC10 flags move to X:$EB (X:$EC.. = drum blocks)
    img12, report = s12.build(stock, listing)
    img = bytearray(img12)
    img[sc.MARK_OFF:sc.MARK_OFF + 4] = MARKER

    # ---------------- DSP
    P = [int.from_bytes(img[s10.p_off(p):s10.p_off(p) + 3], 'big') for p in range(s10.DSP0_WORDS)]
    sc10_words = report["sc10"]["dsp_words"]
    a_base = s10.CODE_BASE + sc10_words
    assert all(x == 0 for x in P[a_base:REG_A_END]) and all(x == 0 for x in P[REG_B:REG_B_END])
    assert P[MIX_HOOK:MIX_HOOK + 2] == [0x60F400, 0x002E70]
    assert P[0x10B:0x10D] == D.jsr(int(report["sc10"]["dsp_labels"]["init_hook"], 16))
    init_hook = int(report["sc10"]["dsp_labels"]["init_hook"], 16)
    assert init_hook == s10.CODE_BASE and P[init_hook:init_hook + 7] == (
        D.move_imm_x('x0', 0) + D.st_abs('x', 'x0', FLAGS_NEW) + D.move_imm_r(0, 0x2028) + D.RTS)
    wa, la, wb, lb = two_region(a_base)
    assert a_base + len(wa) <= REG_A_END and REG_B + len(wb) <= REG_B_END, (len(wa), len(wb))
    P[a_base:a_base + len(wa)] = wa
    P[REG_B:REG_B + len(wb)] = wb
    iw = init_words(); assert len(iw) == 7
    P[init_hook:init_hook + 7] = iw
    P[MIX_HOOK:MIX_HOOK + 2] = D.jsr(la["mixhook"])
    assert P[IDLE_HOOK] == 0x00000C
    P[IDLE_HOOK] = jmp_s(la["idle"])[0]
    for p in range(s10.DSP0_WORDS):
        img[s10.p_off(p):s10.p_off(p) + 3] = P[p].to_bytes(3, 'big')

    # ---------------- ARM
    def text(addr, n):
        return "|".join(sc.disasm(bytes(stock[addr - BASE:addr - BASE + n]), addr))
    assert text(ENTRY, 4) == "cmp r0, #4|bge #0x8043598", text(ENTRY, 4)
    assert text(TRIG_TAIL, 4) == "b.w #0x80292f8", text(TRIG_TAIL, 4)
    assert text(CONT_DOWN_BW, 4) == "b.w #0x804fb66" and text(CONT_UP_BW, 4) == "b.w #0x804fb86"
    targets = s4.branch_targets(listing)
    assert ENTRY + 2 not in targets
    assert struct.unpack_from("<I", img, GROUP_TAB + 5 * 4 - BASE)[0] == SC1_GROUP | 1
    assert struct.unpack_from("<I", img, VIEW_VT - BASE)[0] == VIEW_PAD | 1
    assert struct.unpack_from("<I", img, VIEW_VT + 0x1C - BASE)[0] == VIEW_LEDS | 1
    assert struct.unpack_from("<I", img, PG_VT_SLOT8 - BASE)[0] == 0x0804FBB9
    assert struct.unpack_from("<I", img, PG_VT_LST - BASE)[0] == 0x0804FBB5
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext)
    tab = (ext + len(code) + 3) & ~3
    fix = labels["gr_tab_fix"] - 8
    code = bytearray(code)
    code[fix - ext:fix - ext + 8] = movw(1, tab & 0xFFFF) + movt(1, tab >> 16)
    img[ENTRY - BASE:ENTRY - BASE + 4] = b_w(ENTRY, labels["c_scentry"])
    img[TRIG_TAIL - BASE:TRIG_TAIL - BASE + 4] = b_w(TRIG_TAIL, labels["c_trig"])
    img[CONT_DOWN_BW - BASE:CONT_DOWN_BW - BASE + 4] = b_w(CONT_DOWN_BW, labels["c_pgdn"])
    img[CONT_UP_BW - BASE:CONT_UP_BW - BASE + 4] = b_w(CONT_UP_BW, labels["c_pgup"])
    struct.pack_into("<I", img, GROUP_TAB + 5 * 4 - BASE, labels["c_scgrp"] | 1)
    struct.pack_into("<I", img, VIEW_VT - BASE, labels["c_scpad"] | 1)
    struct.pack_into("<I", img, VIEW_VT + 0x1C - BASE, labels["c_scleds"] | 1)
    struct.pack_into("<I", img, PG_VT_SLOT8 - BASE, labels["c_pgpaint"] | 1)
    struct.pack_into("<I", img, PG_VT_LST - BASE, labels["c_pglst"] | 1)
    img += b"\xFF" * (ext - BASE - len(img)) + bytes(code)
    img += b"\xFF" * (tab - BASE - len(img)) + bytes(x for p in PRESETS for x in p)
    while len(img) % 4:
        img += b"\xFF"
    assert len(img) <= 0x70000
    report["D"]["marker"] = MARKER.decode()
    report["sc13"] = dict(dsp_a=hex(a_base), dsp_a_words=len(wa), dsp_b_words=len(wb),
                          dsp_labels={k: hex(v) for k, v in {**la, **lb}.items()},
                          dsp_listing_b=ddis(wb), dsp_listing_a=ddis(wa),
                          arm_start=hex(ext), preset_table=hex(tab),
                          labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc13"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "circuittracks-4486-SC13.bin").write_bytes(img)
    (args.outdir / "circuittracks-4486-SC13.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker="SC13", image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    r = report["sc13"]
    print("dsp A", r["dsp_a"], r["dsp_a_words"], "B $54", r["dsp_b_words"], "arm", r["arm_start"], "image", hex(len(img)))
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
