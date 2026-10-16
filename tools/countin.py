"""SC41.8 (the user, 2026-10-15, issue #2 of the public repo: «usa un toggle en el metrónomo: sin metrónomo, con metrónomo, sólo countdown, countdown y
metrónomo»): a count-in of one bar before recording.

The stock (read in the firmware, emulated):
  * Shift + Clear toggles the metronome: the generic parameter setter 0x08031608(0x200109D8, id 0x64, value) writes parameter 3 of the store
    [0x200109D8 + 0x38] (0x20010FAC), whose listener marks the master group 0x21:8 dirty;
  * the click itself: the clock (object 0x20011364: + 0x10 the transport 0x20011034 = p0 playing, p1 recording; + 0x14 the metronome store;
    + 0x18 the tempo store 0x20011404, p1 = BPM) calls 0x0802AB0E on its beats; with the metronome on it sends the DSP the pseudo-group 0xFF:
    0x0803BD58(0xFF, 0, 0x60) -> 0x080497CA -> 0x08028FC2 writes master parameter 0x21:9 into Y:$111 of the DSP, its click trigger (the DSP plays a short
    click and clears it).  0x0803BD58 takes the DSP service semaphore: never from the DSP service tick.

Ours:
  * a new head of the button chain (0x08033320): Shift + Clear walks four states: 0 no metronome, 1 metronome, 2 count-in only, 3 count-in and metronome
    (the metronome through the stock's setter; the count-in = a byte of ours, 0xC1 = on, in the session record's tail + 178, so it goes with the project);
  * Play from stopped with Record armed and the count-in on: the press is kept; the LED task sends a click on each of 4 beats at the project's tempo
    (60000 / BPM ms; the stock's click call, so it is the stock's sound and level) with the Record LED blinking, then presses Play itself (a pass flag
    lets that press through); Play again during the count cancels it; a transport started otherwise cancels it;
  * the Clear LED while Shift is held: yellow = no metronome, green = metronome, orange = count-in only, blue = both.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, muls, pop_list,  # noqa: E402
                   push_list, raw, h, str_imm, strb_imm, strh_imm, subs_reg, adds_imm8)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402
from build_sc14 import udiv  # noqa: E402

MGR = 0x20040B10
BTN_ENTRY, BTN_PRESS, BTN_RELEASE = MP.BTN_ENTRY, 0x08033320, 0x0803381A
ID_CLEAR, ID_PLAY = 23, 17
PARAM_GET, PARAM_WPTR = 0x0803542C, 0x080354FA
SETTER, SET_OBJ, ID_METRO = 0x08031608, 0x200109D8, 0x64
METRO_STORE = 0x20010FAC                                  # [SET_OBJ + 0x38]: parameter 3 = the metronome
TRANSPORT, TEMPO = 0x20011034, 0x20011404                 # p0 playing, p1 recording / p1 = BPM
CLICK = 0x0803BD58                                        # (0xFF, 0, 0x60): the stock's metronome click
HAL_TICK = 0x2000081C
SESSION_OBJ, TAIL = 0x2003D71C, 0x27024
O_FLAG, O_T0, O_N, O_PASS = 178, 180, 184, 185            # tail bytes: 0xC1, 0x1C = count-in on; the count's start time (0 = none); clicks sent; the pass flag
CI_ON, CI_ON2 = 0xC1, 0x1C                                # (the last three are RAM only: put to 0 by each load)
BEATS = 4
LED_REC, LED_CLEAR = 48, 55
COL_REC = 0x53
COLS = (0x2D, 0x17, 0x09, 0x07)                           # state 0..3: yellow, green, orange, blue


def use_cols2():
    """SC42.3 (the user, 2026-10-16): «no click: red, click: green, pre-count only: magenta (blue + red), pre-count and click: cyan (green + blue)»."""
    global COLS
    COLS = (0x53, 0x17, 0x32, 0x4D)


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def ldrb_w_(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
    def strb_w_(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
    def ldr_w_(rt, rn, off): return h(0xF8D0 | rn) + h(rt << 12 | off)
    def str_w_(rt, rn, off): return h(0xF8C0 | rn) + h(rt << 12 | off)

    # ---- c_citail() -> r0 = the record's tail, or 0
    a.label("c_citail")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "ct_x", "eq")
    imm32(1, TAIL); E(raw, h(0x1840))                                                  # adds r0, r0, r1
    a.label("ct_x"); E(raw, h(0x4770))

    # ---- c_cip0(r0 = store, r1 = parameter) -> r0 = its byte (the write copy: the newest)
    a.label("c_cip0")
    E(push_list, [3], lr=True); E(bl, PARAM_WPTR); E(ldrb_imm, 0, 0, 0); E(pop_list, [3], pc=True)

    # ---- c_cistate() -> r0 = 0..3 (bit 0 the metronome, bit 1 the count-in); clobbers r1-r3
    a.label("c_cistate")
    E(push_list, [4], lr=True)
    imm32(0, METRO_STORE); E(movs_imm, 1, 3); E(bl, "c_cip0"); E(movs_imm, 1, 1); E(raw, h(0x4008)); E(mov_reg, 4, 0)   # and r0, r1
    E(bl, "c_citail"); E(cmp_imm, 0, 0); E(b_cond, "cs_x", "eq")
    E(raw, ldrb_w_(1, 0, O_FLAG)); E(cmp_imm, 1, CI_ON); E(b_cond, "cs_x", "ne")
    E(raw, ldrb_w_(1, 0, O_FLAG + 1)); E(cmp_imm, 1, CI_ON2); E(b_cond, "cs_x", "ne"); E(adds_imm8, 4, 2)
    a.label("cs_x"); E(mov_reg, 0, 4); E(pop_list, [4], pc=True)

    # ---- c_cibtn (the head of the button chain: ctrl, id)
    a.label("c_cibtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(mov_reg, 5, 1)
    E(bl, "c_citail"); E(cmp_imm, 0, 0); E(b_cond, "cb_f", "eq"); E(mov_reg, 4, 0)
    E(raw, ldrb_w_(0, 4, O_PASS)); E(cmp_imm, 0, 0); E(b_cond, "cb_f", "ne")             # our own Play press
    E(cmp_imm, 5, ID_CLEAR); E(b_cond, "cb_p", "ne")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "cb_f", "eq")
    E(bl, "c_cistate"); E(adds_imm8, 0, 1); E(movs_imm, 1, 3); E(raw, h(0x4008)); E(mov_reg, 5, 0)    # r5 = the next state
    E(movs_imm, 0, 0); E(movs_imm, 1, 0); E(lsls_imm, 2, 5, 30); E(b_cond, "cb_s", "pl"); E(movs_imm, 0, CI_ON); E(movs_imm, 1, CI_ON2)   # bit 1
    a.label("cb_s"); E(raw, strb_w_(0, 4, O_FLAG)); E(raw, strb_w_(1, 4, O_FLAG + 1))
    imm32(0, SET_OBJ); E(movs_imm, 1, ID_METRO); E(movs_imm, 2, 1); E(raw, h(0x402A))               # ands r2, r5 -> the metronome
    E(bl, SETTER); E(b, "cb_x")
    a.label("cb_p")
    E(cmp_imm, 5, ID_PLAY); E(b_cond, "cb_f", "ne")
    E(raw, ldr_w_(0, 4, O_T0)); E(cmp_imm, 0, 0); E(b_cond, "cb_go", "eq")
    E(movs_imm, 0, 0); E(raw, str_w_(0, 4, O_T0)); E(b, "cb_x")                              # Play during the count: cancelled
    a.label("cb_go")
    E(bl, "c_cistate"); E(lsls_imm, 0, 0, 30); E(b_cond, "cb_f", "pl")                  # no count-in
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, "c_cip0"); E(cmp_imm, 0, 0); E(b_cond, "cb_f", "ne")     # playing already
    imm32(0, TRANSPORT); E(movs_imm, 1, 1); E(bl, "c_cip0"); E(cmp_imm, 0, 0); E(b_cond, "cb_f", "eq")     # Record not armed
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "cb_t", "ne"); E(movs_imm, 0, 1)   # never 0
    a.label("cb_t")
    E(raw, str_w_(0, 4, O_T0)); E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, O_N))
    a.label("cb_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("cb_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_ciledtask (the LED task calls: ctrl, frame): the chain; the count's clicks and its end; the Record and Clear LEDs
    a.label("c_ciledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_citail"); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "eq"); E(mov_reg, 4, 0)
    E(raw, ldr_w_(0, 4, O_T0)); E(cmp_imm, 0, 0); E(b_cond, "cl_sh", "eq")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, "c_cip0"); E(cmp_imm, 0, 0); E(b_cond, "cl_end", "ne")    # started otherwise: no count
    imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, "c_cip0"); E(cmp_imm, 0, 30); E(b_cond, "cl_bt", "hs"); E(movs_imm, 0, 120)
    a.label("cl_bt"); E(mov_reg, 1, 0); imm32(0, 60000); E(raw, udiv(6, 0, 1))                          # r6 = ms per beat
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(raw, ldr_w_(1, 4, O_T0)); E(subs_reg, 7, 0, 1)                # r7 = ms since the press
    E(b_cond, "cl_pos", "pl"); E(movs_imm, 7, 0)                                                         # (a start time of 1 for 0)
    a.label("cl_pos")
    E(raw, udiv(0, 7, 6))                                                                                 # r0 = the beat
    E(cmp_imm, 0, BEATS); E(b_cond, "cl_go", "hs")
    E(raw, ldrb_w_(1, 4, O_N)); E(cmp_reg, 0, 1); E(b_cond, "cl_led", "lo")
    E(adds_imm8, 0, 1); E(raw, strb_w_(0, 4, O_N))
    E(movs_imm, 0, 0xFF); E(movs_imm, 1, 0); E(movs_imm, 2, 0x60); E(bl, CLICK)
    a.label("cl_led")                                                                                     # Record blinks: red the first half of each beat
    E(raw, udiv(0, 7, 6)); E(muls, 0, 6); E(subs_reg, 0, 7, 0); E(lsls_imm, 0, 0, 1)
    E(movs_imm, 1, 0); E(cmp_reg, 0, 6); E(b_cond, "cl_lw", "hs"); E(movs_imm, 1, COL_REC)
    a.label("cl_lw"); E(movs_imm, 0, 2 * LED_REC); E(raw, h(0x5229))                                      # strh r1, [r5, r0]
    E(b, "cl_sh")
    a.label("cl_go")                                                                                      # the bar is over: Play
    E(movs_imm, 0, 0); E(raw, str_w_(0, 4, O_T0)); E(movs_imm, 0, 1); E(raw, strb_w_(0, 4, O_PASS))
    imm32(0, MGR); E(movs_imm, 1, ID_PLAY); E(bl, BTN_PRESS)
    imm32(0, MGR); E(movs_imm, 1, ID_PLAY); E(bl, BTN_RELEASE)
    E(movs_imm, 0, 0); E(raw, strb_w_(0, 4, O_PASS)); E(b, "cl_sh")
    a.label("cl_end"); E(movs_imm, 0, 0); E(raw, str_w_(0, 4, O_T0))
    a.label("cl_sh")                                                                                      # Shift held: the Clear LED = the state
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "cl_x", "eq")
    E(bl, "c_cistate")
    for k, col in enumerate(COLS):
        E(movs_imm, 1, col); E(cmp_imm, 0, k); E(b_cond, "cl_cw", "eq")
    a.label("cl_cw"); E(movs_imm, 0, 2 * LED_CLEAR); E(raw, h(0x5229))
    a.label("cl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)

    # ---- c_ciload (at the end of the stock's "apply session", in front of the others): no count from what a file holds
    a.label("c_ciload")
    E(raw, pushw([0, 1, 2, 3, 12], lr=True))
    E(bl, "c_citail"); E(cmp_imm, 0, 0); E(b_cond, "ci_lx", "eq")
    E(movs_imm, 1, 0); E(raw, str_w_(1, 0, O_T0)); E(raw, strb_w_(1, 0, O_N)); E(raw, strb_w_(1, 0, O_PASS))
    a.label("ci_lx"); E(raw, popw([0, 1, 2, 3, 12], lr=True)); E(b_w, prev["load"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the button chain, the two LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(btn=MP.bw_target(img, BTN_ENTRY, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE), load=MP.bw_target(img, P19.LOAD_END, BASE))
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16))
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_cibtn"])
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_ciload"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_ciledtask"])
    return labels, code, prev
