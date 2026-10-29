"""Circuit Tracks 4486 — SC16 = SC15 + side-chain on the drum tracks (SC13 redone safely).

UI (Side Chain View, Shift + FX), as SC13:
  stock pages Synth 1/2 -> MIDI 1/2 with the down/up buttons; two more pages below: Drums 1/2, Drums 3/4.
  On a drum page: rows 3 / 4 = OFF + 7 presets (stock presets) for the two drums of the page,
  top row pads 5-8 = trigger drum for the drum chosen last.  Entering the view with a drum track
  selected opens that drum's page.  Not saved: power-up -> all OFF, trigger = drum 1.

What made SC13 reboot, and what SC16 does instead:
  * SC13 kept its DSP blocks in X:$EB..$10F and cleared it at init: that is the DSP voice-slot table
    (X:$EB..$15A; slot 0 word 0 = routine address) -> jsr $0.  SC16: blocks at X:$3A10 + 9k
    (X:$3339..$3BFF is unused: tools/dsp_free_scan.py); the SC10 flag stays at X:$3A00 (SC14.2).
  * SC13 put DSP code in the P:$54..$7F interrupt vectors.  SC16 appends its DSP code right after
    the stock program (P:$2A5E..): the core-0 bootstrap block is copied to the end of the ARM image
    with a larger word count and the loader pointer (0x08029700) is redirected.  The boot stub sets
    OMR MS=1 (memory switch), which gives at least 16K words of program RAM.
  * SC13 kept its ARM state at 0x2004E000 (beyond the heap, possibly the boot stack).  SC16 widens
    SC14's heap-top reservation by 16 bytes (SC14 block at 0x20044E28, SC16 block right after it);
    if the reservation is not possible the side-chain stays off and the view behaves as stock.
  * getblk / advance are inlined in both hooks (2 fewer DSP stack levels); the init clear uses a
    do loop instead of rep.

DSP core 0:
  X:$3A10 + 9k   drum k block: [trigger, attack, hold, decay, depth, state0..3]
  P:$10B         jsr sc_init (SC15's clears + X:$3A10..$3A33, r0 = $2028)
  P:$218E        jsr mixhook : drum about to be mixed: depth != 0 -> advance envelope (stock func_0012bb,
                 state X <-> Y:$2048, output Y:$2028 scratch), multiply X:$2C02, bit 1 = advanced
  P:$21AB        jmp $FD -> jmp idle (trampoline after SC15's code, short jumps reach < $1000): end of every drum voice: not advanced this block -> advance anyway
  Trigger: the ARM drum trigger tail sets word 0 = 1 in every block whose trigger drum just fired.
"""
from __future__ import annotations

import json
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ct_fw  # noqa: E402
import build_sc14 as s14  # noqa: E402
S14_ST_OLD = s14.ST
s14.ST = S14_ST_OLD - 16              # 0x20044E28: SC14 block (24 B) + SC16 block (16 B) below the old heap limit
import build_sc15 as s15  # noqa: E402
import build_sc10 as s10  # noqa: E402
import build_shared_channels as sc  # noqa: E402
import build_sc04 as s4  # noqa: E402
import dsp56 as D  # noqa: E402
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, str_imm, strb_imm, adds_imm8, adds_imm3, subs_imm8,
                   adds_reg, ands_reg, orrs_reg, ldrh_reg, strh_reg, strh_imm, cbz, raw, h, ldrb_w)

BASE = ct_fw.APP_BASE
NAME = "SC16"
MARKER = b"SC16"
T = s15.T

# ---------------- DSP
DSP_TABLE = 0x08029700
STOCK_WORDS = s10.DSP0_WORDS          # 0x2A5E
CODE_P = STOCK_WORDS                  # new DSP code right after the stock program
CODE_P_END = 0x3000                   # stay well inside 16K words of program RAM
INIT_LABEL = "sc_init"                # (gentab, SC49.7) the routine P:$10B calls: "init2" builds the tables, then sc_init
BLK = 0x3A10                          # X:$3A10 + 9k
CLR_FROM, CLR_N = 0x3A00, 0x34        # X:$3A00..$3A33 (SC10 flag, SC15 modes, drum blocks)
ENV, STATE, SAVE_R5 = 0x2028, 0x2048, 0x204C
FUNC_12BB = 0x12BB
MIX_HOOK = 0x218E                     # move #>$2e70,r0 (2 words)
IDLE_HOOK = 0x21AB                    # rts ending every drum voice

# ---------------- ARM
SC_OFF = 24                           # SC16 block = c_gst() + 24
MAGIC = 0x5C16D5C1
PAL = 0x08056464
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
MARK_DIRTY = 0x0803BDCC
CONV_ATK, CONV_HD = 0x08028764, 0x08028778
SC1_GROUP = 0x08028C9C
GROUP_TAB = 0x0805B3B0
TRIG_TAIL = 0x08051B7C
VIEW_VT = 0x0805AC2C
VIEW_PAD, VIEW_LEDS = 0x0804D6FE, 0x0804D77A
PG_VT_SLOT8 = 0x0805AA8C
PG_VT_LST = 0x0805AA98
PG_DOWN, PG_UP = 0x0804FB66, 0x0804FB86
CONT_DOWN_BW, CONT_UP_BW = 0x08043664, 0x08043702
ENTRY = 0x0804352A
ENTRY_GE, ENTRY_LT = 0x08043598, 0x0804352E
PRESETS = [(0, 50, 70, 0), (5, 50, 80, 80), (5, 70, 70, 100), (5, 85, 70, 115),
           (5, 90, 75, 123), (5, 90, 85, 127), (5, 95, 95, 127), (5, 102, 95, 127)]


def popw(regs, lr=False):
    return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def do_imm(n, last): return [0x060080 | (n & 0xFF) << 8 | (n >> 8) & 0xF, last]
def jeq(t): return [0x0AF0AA, t]
def jcs(t): return [0x0AF0A8, t]
def jmp(t): return [0x0AF080, t]


# ---------------------------------------------------------------- DSP
def getblk(a, out):
    """r0 = block of the current drum (x:$1ed6 = $9f + d), a = depth; jeq out if off."""
    a.emit(T("move x:>$1ed6,b")); a.emit(T("move b1,x0")); a.emit(T("asl #3,b,b")); a.emit(T("add x0,b"))
    a.emit(T("add #>$%x,b" % ((BLK - 9 * 0x9F) & 0xFFFFFF)))
    a.emit(T("move b1,r0")); a.emit(D.NOP)
    a.emit([0x02109E])                                                      # move x:(r0+$4),a  (depth)
    a.emit(T("tst a")); a.emit(jeq, out)


def advance(a, tag):
    """envelope of block r0 -> Y:$2028 (stock func_0012bb), state X:(r0+5..8) <-> Y:$2048."""
    a.emit([0x040051])                                                      # lua (r0+$5),r1
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(do_imm, 4, tag + "c1")
    a.emit(T("move x:(r1)+,x0"))
    a.label(tag + "c1"); a.emit(T("move x0,y:(r4)+"))
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(T("move y:(r4),a"))           # phase
    a.emit(T("move #>$2,x0")); a.emit([0x0A6000])                           # bclr #0,x:(r0)  (trigger)
    a.emit(T("tfr x0,a ifcs")); a.emit([0x0204F6])                          # move y:(r4+$1),y0
    a.emit(T("move #>$%x,r5" % ENV)); a.emit(D.jsr(FUNC_12BB))
    a.emit([0x040051])                                                      # lua (r0+$5),r1
    a.emit(T("move #>$%x,r4" % STATE)); a.emit(do_imm, 4, tag + "c2")
    a.emit(T("move y:(r4)+,x0"))
    a.label(tag + "c2"); a.emit(T("move x0,x:(r1)+"))


def dsp_code(base):
    a = D.Asm(base)
    a.label("sc_init")                                                      # P:$10B (was SC15 li_init)
    a.emit(D.CLR_A); a.emit(T("move #>$%x,r0" % CLR_FROM))
    a.emit(do_imm, CLR_N, "in_l")
    a.label("in_l"); a.emit(T("move a,x:(r0)+"))
    a.emit(D.move_imm_r(0, 0x2028)); a.emit(D.RTS)

    a.label("mixhook")                                                      # P:$218E: drum voice about to be mixed
    a.emit(T("move r5,y:>$%x" % SAVE_R5))
    getblk(a, "mh_out")
    advance(a, "mh")
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
    getblk(a, "id_out")
    a.emit([0x0A6001]); a.emit(jcs, "id_out")                               # bclr #1,x:(r0): mixed -> done
    advance(a, "id")                                                        # silent voice: keep the envelope running
    a.label("id_out")
    a.emit(T("move y:>$%x,r5" % SAVE_R5)); a.emit(D.RTS)
    return a.assemble()


def relocate_dsp(img: bytearray, extra_words, base):
    """Copy the (patched) core-0 program + new words to the end of the image; redirect the loader."""
    old = struct.unpack_from("<I", img, DSP_TABLE - BASE)[0]
    assert old == s10.DSP0, hex(old)
    o = old - BASE
    n = int.from_bytes(img[o:o + 3], 'big')
    assert n == STOCK_WORDS and int.from_bytes(img[o + 3:o + 6], 'big') == 0
    assert base == n
    prog = bytes(img[o + 6:o + 6 + 3 * n])
    total = n + len(extra_words)
    assert total <= CODE_P_END
    blk = total.to_bytes(3, 'big') + b"\0\0\0" + prog + D.to_bytes(extra_words)
    at = (len(img) + BASE + 3) & ~3
    img += b"\xFF" * (at - BASE - len(img)) + blk
    while len(img) % 4:
        img += b"\xFF"
    struct.pack_into("<I", img, DSP_TABLE - BASE, at)
    return at, total


# ---------------------------------------------------------------- ARM
def arm_code(base, c_gst):
    a = Asm(base)
    # ---- c_scst: r0 = state (validated) or 0 if SC14's reservation is not available; clobbers r1, r2
    a.label("c_scst")
    a.emit(push_list, [3], lr=True)
    a.emit(bl, c_gst); a.emit(cbz, "st_out", 0)
    a.emit(adds_imm8, 0, SC_OFF)
    a.emit(ldr_imm, 1, 0, 0)
    a.emit(movw, 2, MAGIC & 0xFFFF); a.emit(movt, 2, MAGIC >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "st_out", "eq")
    a.emit(movs_imm, 1, 0); a.emit(str_imm, 1, 0, 4); a.emit(str_imm, 1, 0, 8); a.emit(str_imm, 1, 0, 12)
    a.emit(str_imm, 2, 0, 0)
    a.label("st_out"); a.emit(pop_list, [3], pc=True)

    # ---- c_wr: DSP_WRITE(0, r1, BLK + 9*r5 + r2)
    a.label("c_wr")
    a.emit(lsls_imm, 0, 5, 3); a.emit(adds_reg, 0, 0, 5); a.emit(adds_reg, 2, 2, 0)
    a.emit(movw, 0, BLK); a.emit(adds_reg, 2, 2, 0)
    a.emit(movs_imm, 0, 0); a.emit(b_w, DSP_WRITE)

    # ---- c_scgrp: project group 5 handler = stock + the 4 drum side-chain parameter sets
    a.label("c_scgrp")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(bl, SC1_GROUP)
    a.emit(bl, "c_scst"); a.emit(cbz, "gr_out", 0)
    a.emit(mov_reg, 4, 0); a.emit(movs_imm, 5, 0)
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
    a.label("gr_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_trig: tail of the drum trigger function (r0 = 0, r1 = 0xF00, r2 = 0x99 + d)
    a.label("c_trig")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 2); a.emit(subs_imm8, 4, 0x99)
    a.emit(bl, DSP_WRITE)
    a.emit(bl, "c_scst"); a.emit(cbz, "tg_out", 0)
    a.emit(mov_reg, 6, 0); a.emit(movs_imm, 5, 0)
    a.label("tg_l")
    a.emit(adds_reg, 0, 6, 5); a.emit(ldrb_imm, 1, 0, 4); a.emit(cbz, "tg_n", 1)
    a.emit(ldrb_imm, 1, 0, 8); a.emit(cmp_reg, 1, 4); a.emit(b_cond, "tg_n", "ne")
    a.emit(movs_imm, 1, 1); a.emit(lsls_imm, 1, 1, 8); a.emit(movs_imm, 2, 0); a.emit(bl, "c_wr")
    a.label("tg_n")
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, 4); a.emit(b_cond, "tg_l", "lo")
    a.label("tg_out")
    a.emit(pop_list, [4, 5, 6], pc=True)

    # ---- c_scpad: Side Chain view slot 0 (view, pad, vel)
    a.label("c_scpad")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, "c_scst"); a.emit(cbz, "sp_stock", 0)
    a.emit(ldrb_imm, 3, 0, 12); a.emit(cmp_imm, 3, 0); a.emit(b_cond, "sp_d", "ne")
    a.label("sp_stock")
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
    a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(mov_reg, 5, 0); a.emit(cbz, "sl_stock", 0)
    a.emit(ldrb_imm, 0, 5, 12); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sl_d", "ne")
    a.label("sl_stock")
    a.emit(mov_reg, 0, 4); a.emit(raw, popw([3, 4, 5, 6, 7], lr=True)); a.emit(b_w, VIEW_LEDS)
    a.label("sl_d")
    a.emit(ldr_imm, 6, 4, 4); a.emit(ldr_imm, 6, 6, 0)
    a.emit(movw, 7, PAL & 0xFFFF); a.emit(movt, 7, PAL >> 16)
    a.emit(movs_imm, 0, 0); a.emit(movs_imm, 1, 0)
    a.label("sl_clr"); a.emit(lsls_imm, 2, 1, 1); a.emit(strh_reg, 0, 6, 2)
    a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 32); a.emit(b_cond, "sl_clr", "lo")
    a.emit(ldrb_imm, 3, 5, 13); a.emit(adds_reg, 0, 5, 3); a.emit(ldrb_imm, 2, 0, 8)
    a.emit(movs_imm, 1, 0)
    a.label("sl_src")
    a.emit(movs_imm, 0, 0x13); a.emit(cmp_reg, 1, 2); a.emit(b_cond, "sl_s1", "ne")
    a.emit(adds_imm3, 0, 3, 5)
    a.label("sl_s1")
    a.emit(lsls_imm, 0, 0, 1); a.emit(ldrh_reg, 0, 7, 0)
    a.emit(adds_imm3, 4, 1, 4); a.emit(lsls_imm, 4, 4, 1); a.emit(strh_reg, 0, 6, 4)
    a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 4); a.emit(b_cond, "sl_src", "lo")
    a.emit(ldrb_imm, 3, 5, 12); a.emit(subs_imm8, 3, 2); a.emit(lsls_imm, 3, 3, 1)
    a.emit(movs_imm, 1, 0)
    a.label("sl_row")
    a.emit(lsrs_imm, 2, 1, 3); a.emit(adds_reg, 2, 2, 3)
    a.emit(adds_reg, 0, 5, 2); a.emit(ldrb_imm, 0, 0, 4)
    a.emit(movs_imm, 4, 7); a.emit(ands_reg, 4, 1)
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
    a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(movs_imm, 5, 0); a.emit(cbz, "pp_nost", 0)
    a.emit(ldrb_imm, 5, 0, 12)
    a.label("pp_nost")
    a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(orrs_reg, 0, 5)
    a.emit(movw, 6, PAL & 0xFFFF); a.emit(movt, 6, PAL >> 16)
    a.emit(ldr_imm, 1, 4, 4); a.emit(ldr_imm, 1, 1, 0)
    a.emit(movw, 2, 0x25A); a.emit(cmp_imm, 5, 3); a.emit(b_cond, "pp_d", "ne"); a.emit(movw, 2, 0x25C)
    a.label("pp_d"); a.emit(ldrh_reg, 2, 6, 2); a.emit(strh_imm, 2, 1, 0)
    a.emit(movw, 2, 0x25C); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pp_u", "eq"); a.emit(movw, 2, 0x25A)
    a.label("pp_u"); a.emit(ldrh_reg, 2, 6, 2); a.emit(strh_imm, 2, 1, 2)
    a.emit(pop_list, [4, 5, 6], pc=True)
    a.label("c_pglst")
    a.emit(subs_imm8, 0, 8); a.emit(b, "c_pgpaint")

    # ---- c_pgdn / c_pgup (pager in r0)
    for name, stock, is_dn in (("c_pgdn", PG_DOWN, True), ("c_pgup", PG_UP, False)):
        a.label(name)
        a.emit(push_list, [4, 5, 6], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(bl, "c_scst"); a.emit(mov_reg, 5, 0); a.emit(cbz, name + "_st", 0)
        a.emit(ldrb_imm, 6, 5, 12)
        a.emit(cmp_imm, 6, 0); a.emit(b_cond, name + "_d", "ne")
        if is_dn:
            a.emit(ldr_imm, 0, 4, 0xC); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
            a.emit(cmp_imm, 0, 1); a.emit(b_cond, name + "_to2", "eq")
        a.label(name + "_st")
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
    a.emit(bl, "c_scst"); a.emit(cbz, "ce_out", 0)
    a.emit(raw, h(0x9900))                                                    # ldr r1,[sp,#0]  (track)
    a.emit(movs_imm, 2, 0); a.emit(movs_imm, 3, 0)
    a.emit(subs_imm8, 1, 4); a.emit(b_cond, "ce_set", "lo")
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
    img15, report = s15.build(stock, listing)
    img = bytearray(img15)
    img[sc.MARK_OFF:sc.MARK_OFF + 6] = MARKER.ljust(6, b"\0")

    # ---------------- DSP: new code after the stock program, hooks, relocated bootstrap block
    P = [int.from_bytes(img[s10.p_off(p):s10.p_off(p) + 3], 'big') for p in range(STOCK_WORDS)]
    li_init = int(report["sc15"]["dsp_labels"]["li_init"], 16)
    assert P[0x10B:0x10D] == D.jsr(li_init)
    assert P[MIX_HOOK:MIX_HOOK + 2] == [0x60F400, 0x002E70] and P[IDLE_HOOK] == 0x00000C
    words, dl = dsp_code(CODE_P)
    P[0x10B:0x10D] = D.jsr(dl[INIT_LABEL])
    P[MIX_HOOK:MIX_HOOK + 2] = D.jsr(dl["mixhook"])
    # P:$21AB is one word: short jmp (target < $1000) to a 2-word trampoline after SC15's code
    tramp = max(p for p in range(0x80, 0x100) if P[p]) + 1
    assert tramp + 2 <= 0x100 and P[tramp:tramp + 2] == [0, 0], hex(tramp)
    P[tramp:tramp + 2] = jmp(dl["idle"])
    P[IDLE_HOOK] = 0x0C0000 | tramp                                          # jmp <tramp (short)
    for p in range(STOCK_WORDS):
        img[s10.p_off(p):s10.p_off(p) + 3] = P[p].to_bytes(3, 'big')
    dsp_at, dsp_total = relocate_dsp(img, words, CODE_P)

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
    c_gst = int(report["sc14"]["labels"]["c_gst"], 16)
    ext = (len(img) + BASE + 3) & ~3
    code, labels = arm_code(ext, c_gst)
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
    report["sc16"] = dict(idle_trampoline=hex(tramp), sc14_state=hex(s14.ST), sc16_state=hex(s14.ST + SC_OFF), dsp_block=hex(dsp_at),
                          dsp_words=hex(dsp_total), dsp_code=hex(CODE_P), dsp_labels={k: hex(v) for k, v in dl.items()},
                          dsp_listing=__import__("dspasm_cache").dis_listing(words, CODE_P),
                          arm_start=hex(ext), preset_table=hex(tab),
                          labels={k: hex(v) for k, v in labels.items()}, listing=sc.disasm(bytes(code), ext))
    return bytes(img), report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("stock_bin", type=Path)
    ap.add_argument("--listing", type=Path, default=Path(__file__).resolve().parents[1] / "re/app.asm")
    ap.add_argument("-o", "--outdir", type=Path, default=Path("build/sc16"))
    args = ap.parse_args()
    stock = args.stock_bin.read_bytes()
    img, report = build(stock, args.listing)
    syx = ct_fw.encode(img)
    info = ct_fw.decode(syx)
    assert info["image"] == img
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / f"circuittracks-4486-{NAME}.bin").write_bytes(img)
    (args.outdir / f"circuittracks-4486-{NAME}.syx").write_bytes(syx)
    manifest = dict(base="circuittracks-firmware-4486 (1.2.1)", marker=NAME, image_size=hex(len(img)),
                    image_sha256=ct_fw.sha256(img), syx_sha256=ct_fw.sha256(syx), crc32=hex(info["crc"]), report=report)
    (args.outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n".join(report["sc16"]["dsp_listing"]))
    print("image", hex(len(img)), "dsp block", report["sc16"]["dsp_block"], report["sc16"]["dsp_words"])
    print("syx sha", manifest["syx_sha256"], "crc", manifest["crc32"])
