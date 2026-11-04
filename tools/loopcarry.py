"""SC51.1 / Beta 5.14 (the user, 2026-11-03: «cuando se cambia entre packs es necesario parar el transporte, pero se puede poner un sample capturado
en modo loop para que siga sonando … al cargar el nuevo pack, el loop se para y el proyecto nuevo no empieza automáticamente»; chosen: option A,
«el loop termina su vuelta»; a load without a loop works as before): the captured sample's latched loop survives a project load.

Why it stopped: every project load (a new pack loads one too) ends in persist19's RESYNC (c_rs, the DSP service tick), whose c_clrall switches every
Master FX effect off and sends the sample the stop command (S_JF: loop / gate off, command 3).  Before that, c_xm_load puts the project's Master FX
slots in RAM, and the sample's 4 knobs (pitch, mode, start, end) live in slot 6's bytes (S_SLOT + 4 x SMP_SLOT): the loop would also change sound.

  * c_lcload (a head of the stock "apply session" end, 0x0802F5B8): with S_JF's latched loop set, its S_JF byte and the sample's 4 knob bytes are kept
    and the state is LOAD;
  * c_lcclr (in place of c_rs's bl c_clrall): state LOAD and the DSP really looping (X:PLAY = 2, the forced loop) = c_clrall, then the new
    project's knob bytes are kept aside (O_NEW), the old ones put back, S_JF's loop and gate put back without the stop (and DIRTY, the same values out
    again): state CARRY.  Anything else = c_clrall as before;
  * Play (no Shift) with CARRY and the transport stopped: the press is kept (state ASK, Play blinks green).  The DSP service tick then writes the
    sampler's MODE = 0 (one-shot) and PLAY = 1 (a plain playback): the loop plays to its end point and stops there (WAIT); when X:PLAY reads 0
    (or after TIMEOUT ms) the LED task presses Play itself (a pass flag lets that press through).  Play again while it waits = stop now and start;
  * the end of a carried loop (Play, or the loop stopped with pad 7 / pad 8 / a slot): the loop is discarded (X:LEN = 0: pad 7 plays nothing until
    the next capture), the new project's knob bytes come back, DIRTY sends them (MODE from K2 again).  A recording started meanwhile ends the carry
    without discarding it.
The capture (Y:$E80000) is outside the pack's sample memory ($580000-$E7FFFF, the loader's limit) and the import memory ($380000-$57EFFF): a pack's own
saved captures (drum samples replaced by a capture and saved, PCM/NN_PCM.wav) load as drum samples there and never touch the loop.
RAM: modmx.MXR + 0x2240: + 0 "LCR1", + 4 state, + 5 S_JF at the load, + 6 pass, + 8 the new project's knob bytes, + 12 the carried ones, + 16 t0.
Installed after dspz in its freed flash (dspz.add).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_reg, ands_reg, b, b_cond, b_w, bics_reg, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, str_imm, strb_imm, subs_reg, tst_reg)
from thumb import bl as bl_enc  # noqa: E402
import modmx as MX  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import persist19 as P19  # noqa: E402
import build_sc14 as S14  # noqa: E402
import build_sc17 as B17  # noqa: E402
import sampler_dsp as SD  # noqa: E402

RAM = MX.MXR + 0x2240
RSIG = 0x3152434C                                       # "LCR1"
O_ST, O_JF, O_PASS, O_NEW, O_OLD, O_T0 = 4, 5, 6, 8, 12, 16
ST_NONE, ST_CARRY, ST_ASK, ST_WAIT, ST_GO, ST_NOW, ST_LOAD = 0, 1, 2, 3, 4, 5, 7
S_JF = B17.S_JF                                          # (in the Master FX block, c_gfst)
KB = B17.S_SLOT + 4 * B17.SMP_SLOT                       # the sample's 4 knob bytes (word aligned)
REC, GATE, LOOP, DIRTY = B17.SMB_REC, B17.SMB_GATE, B17.SMB_LOOP, B17.SMB_DIRTY
DSP_READ = 0x08029344                                    # (core, X address) -> the word << 8
MGR, ID_PLAY = 0x20040B10, 17
BTN_PRESS, BTN_RELEASE = 0x08033320, 0x0803381A
TRANSPORT, PARAM_WPTR = 0x20011034, 0x080354FA
HAL_TICK = 0x2000081C
TIMEOUT = 20000                                          # ms: the longest loop (3.46 s, 2 octaves down) is ~14 s
LED_PLAY, COL_PLAY = 49, 0x17                            # Play blinks green while it waits
assert KB % 4 == 0
KEEP = False
O_PI, O_SS, O_EE = 20, 24, 28                            # (KEEP) the play position at the last tick, the loop's start / end


def use_keep():
    """SC51.3 / Beta 5.16 (the user, 2026-11-04: «haz que el sample capturado no se borre durante el cambio de programa, simplemente al pulsar play
    inicia la reproducción del siguiente proyecto a tiempo y mantiene el sample sonando»): the carried loop is never discarded nor stopped.  Play
    (state ASK) reads the sampler's position (X:PI) and its start / end (X:SS / X:EE: absolute addresses); every DSP service tick reads X:PI again:
    a wrap (the position moved against the loop's direction) or one closer to the end than the last tick's step (the wrap comes before the next
    tick) = GO, and the LED task presses Play: the new project starts on the loop's turn.  The loop goes on as a plain latched loop with its own
    knobs (the new project's knob bytes are not put back: pad 7 never loads a pack's capture).  Play again while it waits = start now; the loop
    stopped by hand = the carry ends (asked: Play anyway); TIMEOUT as before.  One DSP read a tick while it waits."""
    global KEEP
    KEEP = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrb_w(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)
def strb_w(rt, rn, off): return h(0xF880 | rn) + h(rt << 12 | off)
def ldr_w(rt, rn, off): return h(0xF8D0 | rn) + h(rt << 12 | off)
def str_w(rt, rn, off): return h(0xF8C0 | rn) + h(rt << 12 | off)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_lcram() -> r0 = our RAM (cleared the first time); clobbers r1, r2
    a.label("c_lcram")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, RSIG); E(cmp_reg, 1, 2); E(b_cond, "lr_x", "eq")
    E(str_imm, 2, 0, 0); E(movs_imm, 1, 0)
    for o in (4, 8, 12, 16): E(str_imm, 1, 0, o)
    a.label("lr_x"); E(raw, RET)

    # ---- c_lcload: a head of the stock apply-session end (power-up, project load, new project): a latched loop is noted
    a.label("c_lcload")
    E(raw, pushw([0, 1, 2, 3, 4, 12], lr=True))
    E(bl, "c_lcram"); E(mov_reg, 4, 0)
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "ll_x", "eq")
    E(raw, ldrb_w(1, 0, S_JF)); E(movs_imm, 2, LOOP); E(tst_reg, 1, 2); E(b_cond, "ll_x", "eq")
    E(movs_imm, 2, ST_LOAD); E(strb_imm, 2, 4, O_ST); E(strb_imm, 1, 4, O_JF)
    E(raw, ldr_w(1, 0, KB)); E(str_imm, 1, 4, O_OLD)
    a.label("ll_x"); E(raw, popw([0, 1, 2, 3, 4, 12], lr=True)); E(b_w, prev["load"])

    # ---- c_lcclr (in place of c_rs's bl c_clrall; r0 = the Master FX block): the loop goes on
    a.label("c_lcclr")
    E(push_list, [4, 5, 6], lr=True); E(mov_reg, 4, 0)
    E(bl, "c_lcram"); E(mov_reg, 5, 0)
    E(ldrb_imm, 0, 5, O_ST); E(cmp_imm, 0, ST_LOAD); E(b_cond, "lc_p", "ne")
    E(movs_imm, 0, ST_NONE); E(strb_imm, 0, 5, O_ST)
    E(movs_imm, 0, 0); E(movw, 1, SD.PLAY); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8); E(cmp_imm, 0, 2); E(b_cond, "lc_p", "ne")   # not the forced loop
    E(mov_reg, 0, 4); E(bl, L["c_clrall"])
    E(raw, ldr_w(0, 4, KB)); E(str_imm, 0, 5, O_NEW); E(ldr_imm, 0, 5, O_OLD); E(raw, str_w(0, 4, KB))
    E(raw, ldrb_w(0, 4, S_JF)); E(movs_imm, 1, 0x30 | LOOP | GATE); E(bics_reg, 0, 1)
    E(ldrb_imm, 1, 5, O_JF); E(movs_imm, 2, LOOP | GATE); E(ands_reg, 1, 2); E(orrs_reg, 0, 1)
    E(movs_imm, 1, DIRTY); E(orrs_reg, 0, 1); E(raw, strb_w(0, 4, S_JF))
    E(movs_imm, 0, ST_CARRY); E(strb_imm, 0, 5, O_ST)
    E(pop_list, [4, 5, 6], pc=True)
    a.label("lc_p"); E(mov_reg, 0, 4); E(bl, L["c_clrall"]); E(pop_list, [4, 5, 6], pc=True)

    # ---- c_lcbtn (the head of the button chain: ctrl, id): Play with a carried loop and the transport stopped waits for its end
    a.label("c_lcbtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(cmp_imm, 1, ID_PLAY); E(b_cond, "lb_f", "ne")
    E(bl, "c_lcram"); E(mov_reg, 4, 0)
    E(ldrb_imm, 0, 4, O_PASS); E(cmp_imm, 0, 0); E(b_cond, "lb_f", "ne")                                   # our own press
    E(ldrb_imm, 5, 4, O_ST); E(cmp_imm, 5, ST_CARRY); E(b_cond, "lb_f", "lo"); E(cmp_imm, 5, ST_WAIT); E(b_cond, "lb_f", "hi")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "lb_f", "ne")                                         # Shift + Play: the stock's / quant's
    E(cmp_imm, 5, ST_CARRY); E(b_cond, "lb_now", "ne")
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_WPTR); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "lb_f", "ne")   # playing
    E(movs_imm, 0, ST_ASK); E(strb_imm, 0, 4, O_ST); E(b, "lb_x")
    a.label("lb_now"); E(movs_imm, 0, ST_NOW); E(strb_imm, 0, 4, O_ST)                                    # Play again while it waits
    a.label("lb_x"); E(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("lb_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])

    # ---- c_lctick: the head of the DSP service chain (DSP reads / writes allowed, no semaphore)
    a.label("c_lctick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_lcram"); E(mov_reg, 5, 0); E(ldrb_imm, 6, 5, O_ST)
    E(cmp_imm, 6, ST_CARRY); E(b_cond, "lt_out", "lo"); E(cmp_imm, 6, ST_NOW); E(b_cond, "lt_out", "hi"); E(cmp_imm, 6, ST_GO); E(b_cond, "lt_out", "eq")
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); E(b_cond, "lt_out", "eq"); E(mov_reg, 4, 0)
    E(raw, ldrb_w(7, 4, S_JF))
    E(cmp_imm, 6, ST_NOW); E(b_cond, "lt_now", "eq")
    E(movs_imm, 0, LOOP); E(tst_reg, 7, 0); E(b_cond, "lt_gone", "eq")                                     # the loop stopped by hand
    E(cmp_imm, 6, ST_CARRY); E(b_cond, "lt_2", "ne")
    E(movs_imm, 0, REC); E(tst_reg, 7, 0); E(b_cond, "lt_out", "eq")
    E(movs_imm, 0, ST_NONE); E(strb_imm, 0, 5, O_ST); E(b, "lt_keep")                                       # a recording: the carry ends, kept
    a.label("lt_2"); E(cmp_imm, 6, ST_ASK); E(b_cond, "lt_3", "ne")
    if KEEP:                                                                                               # where the loop is, and its ends
        for adr, off in ((SD.PI, O_PI), (SD.SS, O_SS), (SD.EE, O_EE)):
            E(movs_imm, 0, 0); E(movw, 1, adr); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8); E(str_imm, 0, 5, off)
    else:
        E(movs_imm, 0, 0); E(movw, 1, SD.MODE); E(bl, L["c_dw"]); E(movs_imm, 0, 1); E(movw, 1, SD.PLAY); E(bl, L["c_dw"])   # one-shot: to its end
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(str_imm, 0, 5, O_T0); E(movs_imm, 0, ST_WAIT); E(strb_imm, 0, 5, O_ST); E(b, "lt_out")
    a.label("lt_3")                                                                                        # waiting
    if KEEP:                                                                                               # the turn: wrapped, or before the next tick
        E(movs_imm, 0, 0); E(movw, 1, SD.PI); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8)
        E(ldr_imm, 1, 5, O_PI); E(str_imm, 0, 5, O_PI); E(subs_reg, 1, 0, 1)                                # r1 = the step (PI - last)
        E(ldr_imm, 2, 5, O_EE); E(ldr_imm, 3, 5, O_SS); E(cmp_reg, 2, 3); E(b_cond, "lt_fw", "ge")
        E(movs_imm, 3, 0); E(subs_reg, 1, 3, 1); E(subs_reg, 2, 0, 2); E(b, "lt_ck")                       # reverse: step negated, PI - E
        a.label("lt_fw"); E(subs_reg, 2, 2, 0)                                                             # forward: E - PI
        a.label("lt_ck"); E(cmp_imm, 1, 0); E(b_cond, "lt_go", "lt"); E(cmp_reg, 2, 1); E(b_cond, "lt_go", "le")
    else:
        E(movs_imm, 0, 0); E(movw, 1, SD.PLAY); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8); E(cmp_imm, 0, 0); E(b_cond, "lt_go", "eq")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(ldr_imm, 1, 5, O_T0); E(subs_reg, 0, 0, 1); E(movw, 1, TIMEOUT); E(cmp_reg, 0, 1); E(b_cond, "lt_out", "lo")
    E(b, "lt_go")
    a.label("lt_now")
    if not KEEP: E(movs_imm, 0, 0x30); E(orrs_reg, 7, 0)                                                  # stop now (command 3)
    a.label("lt_go"); E(movs_imm, 0, ST_GO); E(b, "lt_fin")
    a.label("lt_gone"); E(movs_imm, 0, ST_NONE); E(cmp_imm, 6, ST_CARRY); E(b_cond, "lt_fin", "eq"); E(movs_imm, 0, ST_GO)   # asked: Play anyway
    a.label("lt_fin"); E(strb_imm, 0, 5, O_ST)
    if KEEP: E(b, "lt_out")                                                                                # the loop and its knobs stay
    E(movs_imm, 0, 0); E(movw, 1, SD.LEN); E(bl, L["c_dw"])                                                # discarded
    a.label("lt_keep")
    E(movs_imm, 0, LOOP | GATE); E(bics_reg, 7, 0); E(movs_imm, 0, DIRTY); E(orrs_reg, 7, 0); E(raw, strb_w(7, 4, S_JF))
    E(ldr_imm, 0, 5, O_NEW); E(raw, str_w(0, 4, KB))                                                       # the new project's knobs
    a.label("lt_out"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_lcled (the LED task calls: ctrl, frame): the chain; Play pressed at the end of the loop; Play blinks while it waits
    a.label("c_lcled")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_lcram"); E(mov_reg, 4, 0); E(ldrb_imm, 0, 4, O_ST)
    E(cmp_imm, 0, ST_GO); E(b_cond, "lv_b", "ne")
    E(movs_imm, 0, ST_NONE); E(strb_imm, 0, 4, O_ST); E(movs_imm, 0, 1); E(strb_imm, 0, 4, O_PASS)
    imm32(0, MGR); E(movs_imm, 1, ID_PLAY); E(bl, BTN_PRESS)
    imm32(0, MGR); E(movs_imm, 1, ID_PLAY); E(bl, BTN_RELEASE)
    E(movs_imm, 0, 0); E(strb_imm, 0, 4, O_PASS); E(b, "lv_x")
    a.label("lv_b"); E(cmp_imm, 0, ST_ASK); E(b_cond, "lv_x", "lo"); E(cmp_imm, 0, ST_NOW); E(b_cond, "lv_x", "hi")
    imm32(0, HAL_TICK); E(ldr_imm, 0, 0, 0); E(lsrs_imm, 0, 0, 8); E(movs_imm, 1, 1); E(ands_reg, 0, 1)
    E(movs_imm, 1, 0); E(cmp_imm, 0, 0); E(b_cond, "lv_w", "eq"); E(movs_imm, 1, COL_PLAY)
    a.label("lv_w"); E(movs_imm, 0, 2 * LED_PLAY); E(raw, h(0x5229))                                       # strh r1, [r5, r0]
    a.label("lv_x"); E(pop_list, [3, 4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """After dspz (dspz.add): c_rs's call of c_clrall, the head of the apply-session end, of the button chain and of the DSP service chain, the
    two LED task calls."""
    import ct_fw
    import hole
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = dict(c_gfst=lab("sc17", "c_gfst"), c_clrall=lab("sc17", "c_clrall"), c_dw=lab("sc17", "c_dw"), c_shift=lab("sc15", "c_shift"))
    prev = dict(load=MP.bw_target(img, P19.LOAD_END, BASE), btn=MP.bw_target(img, MP.BTN_ENTRY, BASE),
                svc=MP.bw_target(img, S14.SVC_HOOK, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    rs, rx = lab("persist19", "c_rs"), lab("persist19", "rs_x")
    sites = [x for x in range(rs, rx, 2) if bytes(img[x - BASE:x - BASE + 4]) == bl_enc(x, L["c_clrall"])]
    assert len(sites) == 1, sites
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    site = sites[0]
    img[site - BASE:site - BASE + 4] = bl_enc(site, labels["c_lcclr"])
    hole.rehash(img, report, site)
    img[P19.LOAD_END - BASE:P19.LOAD_END - BASE + 4] = b_w(P19.LOAD_END, labels["c_lcload"])
    img[MP.BTN_ENTRY - BASE:MP.BTN_ENTRY - BASE + 4] = b_w(MP.BTN_ENTRY, labels["c_lcbtn"])
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_lctick"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_lcled"])
    return labels, code, prev
