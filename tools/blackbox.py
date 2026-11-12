"""Black box (SC56.6 / Beta 5.51 on; the user, 2026-11-12: «If this happens again, is there any way to narrow down the issue? A RAM dump? Context
info?» -> «Build it in the firmware and app»).  A tester saw Beta 5.29 stop updating and answering the panel twice while switching views (sound and
transport went on, Play did not stop).  The firmware runs FreeRTOS (PendSV 0x0801D954, pxCurrentTCB at 0x20006138, TCB 0x5C B): the panel's task
(the LED task, the controller's pad / knob / button entries) is not the main loop's (the DSP service, the sequencer), so the main loop can watch it.

  * Breadcrumbs (nothing on the stack while the code below runs): every button press / release, pad press / release and knob event (a knob's
    repeats fold into one entry) -> a ring of 16 x (time, kind, id, the view's address & 0xFFFF), the task and SP of the last one; the LED task's
    two calls -> the start / end time of each frame, its count, the task (pxCurrentTCB) and SP at the call.
  * Watchdog (the head of the DSP service chain, the main loop, every ms): playing since before the last frame and no frame for STALL_MS = a hang:
    the record is frozen (time, the stall, the view, 64 + 32 B of the controller, the LED task's TCB and 384 B of its stack from the saved stack
    pointer, 176 B of the input task's stack, its saved PC / LR 8 times 50 ms apart), then the unit restarts (SCB AIRCR SYSRESETREQ).  A restart keeps
    the RAM (an install restarts the same way): for the first 30 s after it, Save blinks violet.  Stopped: never (long card work, Components).
  * Read over USB (SysEx, in front of fwid's): F0 7D 43 54 01 seq c 00 + 128 x 00 + F7 (137 B) -> F0 7D 43 54 41 seq c 01 + the 64 bytes of chunk
    c (0..15) as 128 nibbles (high first) + F7; F0 7D 43 54 02 seq + 7 x 00 + F7 = clear (-> 42 seq 01 ..); 03 = freeze now without a restart, for
    a hang where USB still answers (-> 43 seq 01 state ..).  tools/sd_app.html: «Caja negra…».
  * Nothing frozen = it keeps recording; frozen = nothing more is recorded until it is cleared.

RAM BB = 0x2004F000..0x2004F3FF (free: between loadcache's 0x2004EFB0 and wtui's 0x2004F400), signed "BBX1".  Layout: OFF below (the app reads it).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, ldrh_imm, lsls_imm, lsrs_imm,  # noqa: E402
                   mov_reg, movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_imm, strh_imm, subs_reg, subs_imm8)
import rdiag as RD  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

BB, SIZE = 0x2004F000, 0x400
SIG = 0x31584242                                              # "BBX1"
FMT = 1
HAL_TICK, CUR_TCB, MGR = 0x2000081C, 0x20006138, 0x20040B10
TRANSPORT, PARAM_GET = 0x20011034, 0x0803542C
AIRCR, RESET_KEY = 0xE000ED0C, 0x05FA0004
STALL_MS, SAMPLE_MS, NSAMP, SHOW_MS = 15000, 50, 8, 30000
LED_SAVE, COL_SHOW = 57, 0x49                                 # Save, violet
ST_FROZEN, ST_RESET, ST_MANUAL, ST_PLAY = 1, 2, 4, 8
K_PRESS, K_RELEASE, K_PAD, K_PADUP, K_KNOB = 1, 2, 3, 4, 5
ENTRIES = ((0x08033320, K_PRESS), (0x0803381A, K_RELEASE), (0x08033282, K_PAD), (0x080332FE, K_PADUP), (0x08033848, K_KNOB))
PROLOGUES = {bytes.fromhex("70b50646"), bytes.fromhex("38b50446"), bytes.fromhex("70b50446")}
OFF = dict(sig=0, st=4, fmt=5, ns=6, ri=7, ft=8, stall=12, view=16, ltos=20, itos=24, lf0=28, lf1=32, lfn=36, lsp=40, ltcb=44, itcb=48, isp=52,
           play=56, lr=60, fr=64, now=68, itime=72, pc=80, mgr1=144, mgr2=208, ring=240, tcb=368, stk1=464, stk2=848)
O = type("O", (), {k.upper(): v for k, v in OFF.items()})
N_RING, RING_E = 16, 8
MGR1, N_MGR1, MGR2, N_MGR2, N_TCB, N_STK1, N_STK2 = 0x60, 64, 0x140, 32, 92, 384, 176
assert O.MGR1 + N_MGR1 == O.MGR2 and O.MGR2 + N_MGR2 == O.RING and O.RING + N_RING * RING_E == O.TCB and O.TCB + N_TCB <= O.STK1
assert O.STK1 + N_STK1 == O.STK2 and O.STK2 + N_STK2 == SIZE and O.PC + 8 * NSAMP <= O.MGR1
assert BB >= 0x2004EFB0 and BB + SIZE <= 0x2004F400
RAM_LO, RAM_HI = 0x20000000, 0x20050000
LEN_READ, LEN_CMD = 137, 14
CHUNK = 64
assert SIZE // CHUNK <= 16 and LEN_READ == 8 + 2 * CHUNK + 1


def W(rt, rn, imm, op): return h(op | rn) + h(rt << 12 | imm)
def ldr_w(rt, rn, imm): return W(rt, rn, imm, 0xF8D0)
def str_w(rt, rn, imm): return W(rt, rn, imm, 0xF8C0)
def ldrb_w(rt, rn, imm): return W(rt, rn, imm, 0xF890)
def strb_w(rt, rn, imm): return W(rt, rn, imm, 0xF880)
def strh_w(rt, rn, imm): return W(rt, rn, imm, 0xF8A0)
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def mov_from_sp(rd): return h(0x4668 | rd)                   # mov rd, sp (rd < 8)
DSB = h(0xF3BF) + h(0x8F4F)
RET = h(0x4770)
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi", "mi": "pl", "pl": "mi"}


def arm_code(base, prev, conts, sx_cont, router_ptr):
    a = Asm(base)
    E = a.emit
    zc = [0]
    def bc(target, cond):                                     # a conditional branch of any reach
        zc[0] += 1; n = f"_b{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def now(rd): imm32(rd, HAL_TICK); E(ldr_imm, rd, rd, 0)

    # ---- c_bbst() -> r0 = BB, signed (zeroed and signed the first time); clobbers r1-r3
    a.label("c_bbst")
    imm32(0, BB); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, 0); E(movs_imm, 3, 4)
    a.label("st_z"); E(raw, h(0x50C1)); E(adds_imm8, 3, 4); E(movw, 2, SIZE); E(cmp_reg, 3, 2); E(b_cond, "st_z", "lo")   # str r1, [r0, r3]
    imm32(2, SIG); E(str_imm, 2, 0, 0); E(movs_imm, 1, FMT); E(strb_imm, 1, 0, O.FMT)
    a.label("st_x"); E(raw, RET)

    # ---- c_bbval(r0 = address, r1 = length) -> r0 = the address if [r0, r0 + r1) is RAM and r0 is word-aligned, else 0; clobbers r2
    a.label("c_bbval")
    E(lsls_imm, 2, 0, 30); E(b_cond, "vl_0", "ne")
    imm32(2, RAM_LO); E(cmp_reg, 0, 2); E(b_cond, "vl_0", "lo")
    E(raw, h(0x1842)); imm32(1, RAM_HI); E(cmp_reg, 2, 1); E(b_cond, "vl_0", "hi")      # adds r2, r0, r1
    E(raw, RET)
    a.label("vl_0"); E(movs_imm, 0, 0); E(raw, RET)

    # ---- c_bbcpy(r0 = dst, r1 = src, r2 = n, a multiple of 4): words; an invalid source = zeros; clobbers r0-r3
    a.label("c_bbcpy")
    E(push_list, [4, 5, 6], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(mov_reg, 0, 5); E(mov_reg, 1, 6); E(bl, "c_bbval"); E(mov_reg, 5, 0)
    E(movs_imm, 3, 0)
    a.label("cp_l"); E(cmp_reg, 3, 6); E(b_cond, "cp_x", "hs")
    E(movs_imm, 0, 0); E(cmp_imm, 5, 0); E(b_cond, "cp_w", "eq"); E(raw, h(0x58E8))     # ldr r0, [r5, r3]
    a.label("cp_w"); E(raw, h(0x50E0)); E(adds_imm8, 3, 4); E(b, "cp_l")               # str r0, [r4, r3]
    a.label("cp_x"); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_bbtos(r0 = TCB) -> r0 = its saved stack pointer (pxTopOfStack) if the TCB and it are RAM, else 0; clobbers r1-r2
    a.label("c_bbtos")
    E(push_list, [], lr=True)
    E(movs_imm, 1, 0x5C); E(bl, "c_bbval"); E(cmp_imm, 0, 0); E(b_cond, "ts_x", "eq")
    E(ldr_imm, 0, 0, 0); E(movs_imm, 1, 0x80); E(bl, "c_bbval")
    a.label("ts_x"); E(pop_list, [], pc=True)

    # ---- c_bbsmp(r4 = BB): the LED task's saved PC / LR (its pxTopOfStack: r4-r11, EXC_RETURN, s16-s31 when bit 4 of EXC_RETURN is 0, then the
    #      exception frame: r0-r3, r12, LR, PC) -> sample ns; ns + 1 (up to NSAMP); clobbers r0-r3
    a.label("c_bbsmp")
    E(push_list, [5], lr=True)
    E(ldrb_imm, 5, 4, O.NS); E(cmp_imm, 5, NSAMP); E(b_cond, "sm_x", "hs")
    E(ldr_imm, 0, 4, O.LTCB); E(bl, "c_bbtos"); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(cmp_imm, 0, 0); E(b_cond, "sm_w", "eq")
    E(ldr_imm, 3, 0, 32); E(adds_imm8, 0, 36); E(lsls_imm, 3, 3, 27); E(b_cond, "sm_f", "mi"); E(adds_imm8, 0, 64)   # bit 4 clear: the FP registers
    a.label("sm_f"); E(movs_imm, 1, 32); E(bl, "c_bbval"); E(movs_imm, 1, 0); E(movs_imm, 2, 0); E(cmp_imm, 0, 0); E(b_cond, "sm_w", "eq")
    E(ldr_imm, 1, 0, 24); E(ldr_imm, 2, 0, 20)
    a.label("sm_w"); E(lsls_imm, 3, 5, 3); E(adds_reg, 3, 3, 4); E(str_imm, 1, 3, O.PC); E(str_imm, 2, 3, O.PC + 4)
    E(adds_imm8, 5, 1); E(strb_imm, 5, 4, O.NS)
    a.label("sm_x"); E(pop_list, [5], pc=True)

    # ---- c_bbfrz(r0 = state): freeze the record (state written first: the recorders stop), clobbers r0-r3
    a.label("c_bbfrz")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(bl, "c_bbst"); E(mov_reg, 4, 0); E(strb_imm, 6, 4, O.ST)
    now(5); E(str_imm, 5, 4, O.FT); E(ldr_imm, 0, 4, O.LF1); E(subs_reg, 0, 5, 0); E(str_imm, 0, 4, O.STALL)
    imm32(1, MGR); E(ldr_imm, 0, 1, 0x6C); E(str_imm, 0, 4, O.VIEW)
    def cpy(dst_off, src_reg_setup, n):
        E(movw, 0, dst_off); E(adds_reg, 0, 0, 4); src_reg_setup(); E(movw, 2, n); E(bl, "c_bbcpy")
    cpy(O.MGR1, lambda: imm32(1, MGR + MGR1), N_MGR1)
    cpy(O.MGR2, lambda: imm32(1, MGR + MGR2), N_MGR2)
    cpy(O.TCB, lambda: E(ldr_imm, 1, 4, O.LTCB), N_TCB)
    E(ldr_imm, 0, 4, O.LTCB); E(bl, "c_bbtos"); E(mov_reg, 6, 0); E(str_imm, 6, 4, O.LTOS)
    cpy(O.STK1, lambda: E(mov_reg, 1, 6), N_STK1)
    E(movs_imm, 7, 0); E(ldr_imm, 0, 4, O.ITCB); E(ldr_imm, 1, 4, O.LTCB); E(cmp_reg, 0, 1); E(b_cond, "fz_o", "ne")
    E(cmp_imm, 6, 0); E(b_cond, "fz_t", "eq"); E(movw, 7, N_STK1); E(adds_reg, 7, 7, 6); E(b, "fz_t")   # the same task: its stack goes on
    a.label("fz_o"); E(bl, "c_bbtos"); E(mov_reg, 7, 0)
    a.label("fz_t"); E(str_imm, 7, 4, O.ITOS)
    cpy(O.STK2, lambda: E(mov_reg, 1, 7), N_STK2)
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, O.NS); E(bl, "c_bbsmp")
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_bbtick (the head of the DSP service chain: the main loop, every ms)
    a.label("c_bbtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_bbst"); E(mov_reg, 4, 0); now(5)
    E(ldrb_imm, 6, 4, O.ST)
    E(ldr_imm, 1, 4, O.NOW); E(str_imm, 5, 4, O.NOW); E(cmp_reg, 1, 5); E(b_cond, "tk_s", "ls")
    E(lsls_imm, 0, 6, 31); E(b_cond, "tk_s", "mi")                                      # a restart, not frozen: this boot's frames from 0
    E(movs_imm, 0, 0); E(str_imm, 0, 4, O.LF0); E(str_imm, 0, 4, O.LF1); E(str_imm, 0, 4, O.LFN); E(str_imm, 0, 4, O.PLAY)
    a.label("tk_s")
    E(lsls_imm, 0, 6, 31); E(b_cond, "tk_live", "pl")
    E(movs_imm, 0, ST_MANUAL | ST_RESET); E(raw, h(0x4230)); bc("tk_x", "ne")             # tst r0, r6
    E(ldrb_imm, 7, 4, O.NS); E(cmp_imm, 7, NSAMP); E(b_cond, "tk_rs", "hs")
    E(ldr_imm, 0, 4, O.FT); E(subs_reg, 0, 5, 0); E(movs_imm, 1, SAMPLE_MS); E(raw, h(0x4379))   # muls r1, r7
    E(cmp_reg, 0, 1); bc("tk_x", "lo"); E(bl, "c_bbsmp"); E(b, "tk_x")
    a.label("tk_rs"); E(movs_imm, 0, ST_RESET); E(raw, h(0x4330)); E(strb_imm, 0, 4, O.ST)     # orrs r0, r6
    E(raw, DSB); imm32(0, AIRCR); imm32(1, RESET_KEY); E(str_imm, 1, 0, 0); E(raw, DSB)
    a.label("tk_hang"); E(b, "tk_hang")
    a.label("tk_live")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(ldrb_imm, 0, 0, 0)
    E(ldr_imm, 1, 4, O.PLAY); E(cmp_imm, 0, 0); E(b_cond, "tk_p", "ne")
    E(str_imm, 0, 4, O.PLAY); E(b, "tk_x")
    a.label("tk_p"); E(cmp_imm, 1, 0); E(b_cond, "tk_pp", "ne"); E(movs_imm, 1, 1); E(raw, h(0x4329)); E(str_imm, 1, 4, O.PLAY); E(b, "tk_x")   # orrs r1, r5
    a.label("tk_pp")
    E(ldr_imm, 0, 4, O.LFN); E(cmp_imm, 0, 0); E(b_cond, "tk_x", "eq")
    E(ldr_imm, 0, 4, O.LF1); E(cmp_reg, 0, 5); E(b_cond, "tk_x", "hi"); E(cmp_reg, 1, 0); E(b_cond, "tk_x", "hi")
    E(subs_reg, 0, 5, 0); E(movw, 1, STALL_MS); E(cmp_reg, 0, 1); E(b_cond, "tk_x", "lo")
    E(movs_imm, 0, ST_FROZEN | ST_PLAY); E(bl, "c_bbfrz")
    a.label("tk_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_bbled (the LED task's two calls: ctrl, frame): LR / frame in RAM, nothing on the stack while the chain runs; the frame's start / end, the
    #      task and SP; Save blinking violet for SHOW_MS after the watchdog's restart
    a.label("c_bbled")
    imm32(12, BB); E(raw, str_w(14, 12, O.LR)); E(raw, str_w(1, 12, O.FR))
    E(raw, ldr_w(2, 12, 0)); imm32(3, SIG); E(cmp_reg, 2, 3); E(b_cond, "ld_c", "ne")
    E(raw, ldrb_w(2, 12, O.ST)); E(lsls_imm, 2, 2, 31); E(b_cond, "ld_c", "mi")
    now(3); E(raw, str_w(3, 12, O.LF0)); E(raw, mov_from_sp(3)); E(raw, str_w(3, 12, O.LSP))
    imm32(3, CUR_TCB); E(ldr_imm, 3, 3, 0); E(raw, str_w(3, 12, O.LTCB))
    a.label("ld_c"); E(bl, prev["ledtask"])
    E(push_list, [0, 4, 5, 6, 7])
    imm32(4, BB); now(5)
    E(ldr_imm, 0, 4, 0); imm32(1, SIG); E(cmp_reg, 0, 1); E(b_cond, "ld_x", "ne")
    E(ldrb_imm, 6, 4, O.ST); E(lsls_imm, 0, 6, 31); E(b_cond, "ld_f", "mi")
    E(str_imm, 5, 4, O.LF1); E(ldr_imm, 0, 4, O.LFN); E(adds_imm8, 0, 1); E(str_imm, 0, 4, O.LFN)
    a.label("ld_f")
    E(movs_imm, 0, ST_RESET); E(raw, h(0x4230)); E(b_cond, "ld_x", "eq")                  # tst r0, r6
    E(movw, 0, SHOW_MS); E(cmp_reg, 5, 0); E(b_cond, "ld_x", "hs")
    E(movs_imm, 1, 0); E(lsls_imm, 0, 5, 24); E(b_cond, "ld_d", "pl"); E(movs_imm, 1, COL_SHOW)   # bit 7 of the ms: 128 ms on / off
    a.label("ld_d"); E(ldr_imm, 0, 4, O.FR); E(movs_imm, 2, 2 * LED_SAVE); E(raw, h(0x5281))       # strh r1, [r0, r2]
    a.label("ld_x"); E(pop_list, [0, 4, 5, 6, 7])
    imm32(12, BB); E(raw, ldr_w(14, 12, O.LR)); E(raw, RET)

    # ---- c_bbrec(r2 = kind, r3 = id): one breadcrumb (the head pushed r0-r6 / LR; r1 = the caller's SP); a knob's repeats fold
    a.label("c_bbrec")
    imm32(4, BB); E(ldr_imm, 0, 4, 0); imm32(5, SIG); E(cmp_reg, 0, 5); E(b_cond, "rc_x", "ne")
    E(ldrb_imm, 0, 4, O.ST); E(lsls_imm, 0, 0, 31); E(b_cond, "rc_x", "mi")
    now(5); E(str_imm, 5, 4, O.ITIME); E(str_imm, 1, 4, O.ISP)
    imm32(0, CUR_TCB); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 4, O.ITCB)
    E(ldrb_imm, 6, 4, O.RI)
    E(cmp_imm, 2, K_KNOB); E(b_cond, "rc_n", "ne")
    E(subs_imm8, 6, 1); E(lsls_imm, 6, 6, 28); E(lsrs_imm, 6, 6, 28)                      # the previous entry
    E(lsls_imm, 0, 6, 3); E(adds_reg, 0, 0, 4); E(adds_imm8, 0, O.RING)
    E(ldrb_imm, 1, 0, 4); E(cmp_imm, 1, K_KNOB); E(b_cond, "rc_p", "ne"); E(ldrb_imm, 1, 0, 5); E(cmp_reg, 1, 3); E(b_cond, "rc_p", "ne")
    E(str_imm, 5, 0, 0); E(b, "rc_x")
    a.label("rc_p"); E(ldrb_imm, 6, 4, O.RI)
    a.label("rc_n")
    E(lsls_imm, 0, 6, 3); E(adds_reg, 0, 0, 4); E(adds_imm8, 0, O.RING)
    E(str_imm, 5, 0, 0); E(strb_imm, 2, 0, 4); E(strb_imm, 3, 0, 5)
    imm32(1, MGR); E(ldr_imm, 1, 1, 0x6C); E(strh_imm, 1, 0, 6)
    E(adds_imm8, 6, 1); E(lsls_imm, 6, 6, 28); E(lsrs_imm, 6, 6, 28); E(strb_imm, 6, 4, O.RI)
    a.label("rc_x"); E(raw, RET)

    # ---- the input heads: r0-r6 / LR pushed, the breadcrumb, popped, then what was at the entry (another module's b.w, or the stock's 4 bytes)
    for (addr, kind), cont in zip(ENTRIES, conts):
        lab = f"c_bbin{kind}"
        a.label(lab)
        E(raw, pushw([0, 1, 2, 3, 4, 5, 6], lr=True))
        E(movs_imm, 2, kind); E(mov_reg, 3, 1); E(raw, mov_from_sp(1)); E(bl, "c_bbrec")
        E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True))
        if isinstance(cont, int): E(b_w, cont)
        else: E(raw, cont); E(b_w, addr + 4)

    # ---- c_bbsx (the incoming SysEx dispatcher, in front of fwid's c_fwin): read a chunk, clear, freeze now; anything else goes on
    a.label("c_bbsx")
    E(push_list, [0, 1, 2, 3, 4, 5, 6], lr=True)
    E(ldr_imm, 4, 1, 0); E(ldr_imm, 5, 1, 4); E(mov_reg, 6, 0)
    for i, v in enumerate(RD.SIG):
        E(ldrb_imm, 3, 4, i); E(cmp_imm, 3, v); bc("sx_fwd", "ne")
    E(ldrb_imm, 3, 4, 4)
    E(cmp_imm, 3, 1); E(b_cond, "sx_c1", "ne"); E(cmp_imm, 5, LEN_READ); bc("sx_fwd", "ne"); E(b, "sx_rd")
    a.label("sx_c1"); E(cmp_imm, 5, LEN_CMD); bc("sx_fwd", "ne")
    E(cmp_imm, 3, 2); E(b_cond, "sx_clr", "eq"); E(cmp_imm, 3, 3); bc("sx_fwd", "ne")
    # 03: freeze now (manual) unless frozen
    E(bl, "c_bbst"); E(ldrb_imm, 1, 0, O.ST); E(lsls_imm, 1, 1, 31); E(b_cond, "sx_f", "mi")
    E(movs_imm, 0, ST_FROZEN | ST_MANUAL); E(bl, "c_bbfrz")
    a.label("sx_f"); E(bl, "c_bbst"); E(ldrb_imm, 1, 0, O.ST); E(strb_imm, 1, 4, 7); E(b, "sx_ok")
    # 02: clear (the signature kept)
    a.label("sx_clr")
    E(bl, "c_bbst"); E(movs_imm, 1, 0); E(movs_imm, 3, 4)
    a.label("sx_cz"); E(raw, h(0x50C1)); E(adds_imm8, 3, 4); E(movw, 2, SIZE); E(cmp_reg, 3, 2); E(b_cond, "sx_cz", "lo")
    E(movs_imm, 1, FMT); E(strb_imm, 1, 0, O.FMT); E(movs_imm, 1, 0); E(strb_imm, 1, 4, 7)
    a.label("sx_ok")
    E(ldrb_imm, 3, 4, 4); E(adds_imm8, 3, 0x40); E(strb_imm, 3, 4, 4); E(movs_imm, 3, 1); E(strb_imm, 3, 4, 6)
    E(movs_imm, 3, 0)
    for k in range(8, LEN_CMD - 1): E(strb_imm, 3, 4, k)
    E(movs_imm, 3, 0xF7); E(strb_imm, 3, 4, LEN_CMD - 1); E(movs_imm, 5, LEN_CMD); E(b, "sx_send")
    # 01: chunk c (byte 6) as nibbles from byte 8
    a.label("sx_rd")
    E(movs_imm, 3, 0x41); E(strb_imm, 3, 4, 4)
    E(bl, "c_bbst"); E(ldrb_imm, 1, 4, 6); E(movs_imm, 2, 0); E(cmp_imm, 1, SIZE // CHUNK); E(b_cond, "sx_r0", "hs"); E(movs_imm, 2, 1)
    a.label("sx_r0"); E(strb_imm, 2, 4, 7)
    E(lsls_imm, 1, 1, 6); E(adds_reg, 1, 1, 0)                                          # r1 = BB + 64 c
    E(mov_reg, 0, 4); E(adds_imm8, 0, 8); E(movs_imm, 3, 0)
    a.label("sx_rl")
    E(movs_imm, 5, 0); E(cmp_imm, 2, 0); E(b_cond, "sx_rz", "eq"); E(raw, h(0x5CCD))      # ldrb r5, [r1, r3]
    a.label("sx_rz"); E(lsrs_imm, 2, 5, 4); E(strb_imm, 2, 0, 0); E(lsls_imm, 5, 5, 28); E(lsrs_imm, 5, 5, 28); E(strb_imm, 5, 0, 1)
    E(ldrb_imm, 2, 4, 7); E(adds_imm8, 0, 2); E(adds_imm8, 3, 1); E(cmp_imm, 3, CHUNK); E(b_cond, "sx_rl", "lo")
    E(movs_imm, 3, 0xF7); E(strb_imm, 3, 0, 0); E(movs_imm, 5, LEN_READ)
    a.label("sx_send")
    E(raw, h(0xB082)); E(raw, h(0x9400)); E(raw, h(0x9501))                               # sub sp, #8; str r4, [sp]; str r5, [sp, #4]
    imm32(0, router_ptr); E(ldr_imm, 0, 0, 0)
    E(movs_imm, 1, 1); E(raw, h(0x40B1))                                                  # lsls r1, r6 -> 1 << port
    E(raw, h(0xAA00)); E(bl, RD.ROUTER)                                                   # add r2, sp, #0
    E(raw, h(0xB002))                                                                     # add sp, #8
    E(pop_list, [0, 1, 2, 3, 4, 5, 6], pc=True)
    a.label("sx_fwd")
    E(raw, popw([0, 1, 2, 3, 4, 5, 6], lr=True)); E(b_w, sx_cont)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; hooks: the DSP service chain's head, the LED task's two calls, the controller's five input entries, the SysEx dispatcher
    (in front of fwid)."""
    import ct_fw
    import struct
    BASE = ct_fw.APP_BASE
    old = lambda a_: bytes(img[a_ - BASE:a_ - BASE + 4])
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    conts = []
    for addr, kind in ENTRIES:
        cur = old(addr)
        if cur in PROLOGUES: conts.append(cur)
        else: conts.append(MP.bw_target(img, addr, BASE))
    fw = int(report["fwid"]["labels"]["c_fwin"], 16)
    assert old(RD.HOOK) == RD.b_w(RD.HOOK, fw), old(RD.HOOK).hex()
    router_ptr = struct.unpack_from("<I", img, RD.ROUTER_LIT - BASE)[0]
    code, labels = arm_code(base_addr, prev, conts, fw, router_ptr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_bbtick"])
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_bbled"])
    for addr, kind in ENTRIES:
        img[addr - BASE:addr - BASE + 4] = b_w(addr, labels[f"c_bbin{kind}"])
    img[RD.HOOK - BASE:RD.HOOK - BASE + 4] = b_w(RD.HOOK, labels["c_bbsx"])
    out = dict(prev, sx_cont=fw, bb=BB)
    for (addr, kind), c in zip(ENTRIES, conts):
        if isinstance(c, int): out[f"in{kind}"] = c
    return labels, code, out
