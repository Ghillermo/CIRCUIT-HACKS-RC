"""S555D (diagnostic; the user, 2026-11-09: «Clock seems unstable, specially when loading new FM patches or using morph with FM/custom patches»):
three live indicators on the panel, so the moment the clock wobbles shows what was late.  Built from S484D's meter (dspload) and S419D2's culprit
(stutdiag), merged, with the LED task's wrapper keeping nothing on the stack while the chain below runs (SC54's first build reset the device with
76 B more there).

  * Save (LED 57) = core 0 of the DSP's time (dspload's margin m = (Y:$FFD - Y:$FFE) & $3FF, sampled every 4 ms from the DSP service's head, the
    lowest of each 500 ms window shown): green = every block within 1/2 a period, yellow 1/2 - 3/4, amber 3/4 - 1, red = a block took longer than
    a period; white for 2 s after the output ring ran dry (the audio repeated).
  * Duplicate (LED 56) = the ARM main loop late: two DSP service ticks GAP_MS or more apart; for 1 s, the colour of what ran meanwhile, by
    priority: white = a card access called from the mod, blue = a card access of the stock, peach = the DSP service itself >= 5 ms, orange = the
    LED task >= 5 ms, red = a knob event >= 5 ms, green = a pad event >= 5 ms, yellow = none of them.
  * Play (LED 49) violet for 400 ms = the sequencer's tick (0x0802C418, while playing) came more than 1.5 x its interval (2500 / BPM ms, BPM = p0 of
    0x20011404; stutdiag read p1, not the tempo) after the previous one.

RAM modmx.MXR + 0x1F00 (signed "CKD1"; was dspload's, only in diagnostics): + 4 last sample, + 8 window start, + 12 window min margin, + 16 last
window's min, + 20 last dry ring, + 24 dry rings, + 28 worst margin since power-on, + 32 last service tick, + 36 time of the last gap, + 40 gaps,
+ 44 worst gap (ms), + 48 mask of this gap, + 52 colour of the last gap, + 56 every culprit seen, + 60 last sequencer tick, + 64 time of the last
late tick, + 68 late ticks, + 72 the LED wrapper's LR, + 76 its start time, + 80 the main service call's LR, + 84 its start, + 88 the frame (72..91 never cleared).
At the end of the image (no card writes, no settings save).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, pop_list, push_list, raw, str_imm, subs_reg, subs_imm8)
import modmx as MX  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
from build_sc14 import udiv  # noqa: E402

RAM = MX.MXR + 0x1F00
SIG = 0x31444B43                                              # "CKD1"
DSP_READ, HAL_TICK = 0x08029344, 0x2000081C
Y_ISR, Y_BLK = 0x8000 | 0xFFE, 0x8000 | 0xFFD
SAMPLE_MS, WIN_MS, DRY_MS, DRY = 4, 500, 2000, 640
CPU_STEPS = ((224, 0x17), (208, 0x2D), (192, 0x2B))           # min margin >= : green, yellow, amber; below: red
COL_LATE, COL_DRY = 0x53, 0x01
GAP_MS, LONG_MS, CUL_FLASH, SEQ_FLASH = 6, 5, 1000, 400
LED_PLAY, LED_DUP, LED_SAVE = 49, 56, 57
COL_SEQ = 0x49                                                # violet
B_SDMOD, B_SD, B_SVC, B_LED, B_KNOB, B_PAD = 1, 2, 4, 8, 16, 32
CUL_COLS = ((B_SDMOD, 0x01), (B_SD, 0x09), (B_SVC, 0x6B), (B_LED, 0x45), (B_KNOB, 0x53), (B_PAD, 0x17))   # white, blue, peach, orange, red, green
COL_UNKNOWN = 0x2D                                                                                       # yellow
O_LAST, O_W0, O_MIN, O_SMIN, O_DRY, O_NDRY, O_WMIN, O_SVC, O_TGAP, O_NGAP, O_GMAX, O_MASK, O_CCOL, O_SEEN, O_SEQ, O_TSEQ, O_NSEQ, \
    O_LLR, O_LT0, O_SLR, O_ST0, O_FR, RSZ = range(4, 96, 4)
O_SMASK, O_SCOL = 92, 96                                      # (use_seqcul) what ran long since the last sequencer tick; the late tick's colour
SEQCUL = False                                                # S555D2 (use_seqcul)


def use_seqcul():
    """S555D2 (the user, with S555D: «play violet sometimes when loading new patches, difficult to replicate», Duplicate quiet): Play lights in the
    colour of what ran long between the late sequencer tick and the one before (Duplicate's colours), violet = none of them."""
    global SEQCUL
    SEQCUL = True
SEQ_TICK = 0x0802C418
TRANSPORT, TEMPO, PARAM_GET = 0x20011034, 0x20011404, 0x0803542C
SD_ANY, SD_TAIL = 0x0803CA52, 0x0803CA56
SD_ANY2, SD_TAIL2 = 0x0803CADE, 0x0803CAE2
SD_HEADS = (0x0803CB50, 0x0803CB6A, 0x0803CBF0)
SD_CHAINS = (0x0803CC16, 0x0803CC34)
MOD_START = 0x0805CDDC
MAIN_SVC_CALL, SVC = 0x0801D5D8, 0x08021392
PAD_IN, KNOB_IN = 0x08033282, 0x08033848


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldr_w(rt, rn, imm): return h(0xF8D0 | rn) + h(rt << 12 | imm)
def str_w(rt, rn, imm): return h(0xF8C0 | rn) + h(rt << 12 | imm)
def orr_imm(rd, rn, imm8): return h(0xF040 | rn) + h(rd << 8 | imm8)      # orr.w rd, rn, #imm8 (imm8 < 256, no rotation)


def arm_code(base, prev, end_mod):
    a = Asm(base)
    E = a.emit
    RET = h(0x4770)
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def rd_dsp(addr): E(movs_imm, 0, 0); imm32(1, addr); E(bl, DSP_READ)

    # ---- c_ckst() -> r0 = our RAM (signed; minima at 1023 the first time; the wrappers' LR / time / frame words never cleared); clobbers r1-r3
    a.label("c_ckst")
    imm32(0, RAM); E(ldr_imm, 1, 0, 0); imm32(2, SIG); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, 0); E(movs_imm, 3, 4)
    a.label("st_z"); E(raw, h(0x50C1)); E(adds_imm8, 3, 4); E(cmp_imm, 3, O_LLR); E(b_cond, "st_z", "lo")   # str r1, [r0, r3]
    E(str_imm, 2, 0, 0); imm32(1, 1023); E(str_imm, 1, 0, O_MIN); E(str_imm, 1, 0, O_SMIN); E(str_imm, 1, 0, O_WMIN)
    a.label("st_x"); E(raw, RET)

    # ---- c_cktick (the head of the DSP service chain): the main loop's gaps and their culprit; the margin every SAMPLE_MS ms
    a.label("c_cktick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_ckst"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)
    E(ldr_imm, 1, 4, O_SVC); E(str_imm, 5, 4, O_SVC); E(cmp_imm, 1, 0); E(b_cond, "tk_w", "eq")
    E(subs_reg, 1, 5, 1); E(ldr_imm, 2, 4, O_GMAX); E(cmp_reg, 1, 2); E(b_cond, "tk_g", "ls"); E(str_imm, 1, 4, O_GMAX)
    a.label("tk_g"); E(cmp_imm, 1, GAP_MS); E(b_cond, "tk_w", "lo")
    E(str_imm, 5, 4, O_TGAP); E(ldr_imm, 1, 4, O_NGAP); E(adds_imm8, 1, 1); E(str_imm, 1, 4, O_NGAP)
    E(ldr_imm, 2, 4, O_MASK); E(ldr_imm, 1, 4, O_SEEN); E(raw, h(0x4311)); E(str_imm, 1, 4, O_SEEN)          # orrs r1, r2
    for bit, col in CUL_COLS:
        E(movs_imm, 3, col); E(movs_imm, 0, bit); E(raw, h(0x4210)); E(b_cond, "tk_c", "ne")                 # tst r0, r2
    E(movs_imm, 3, COL_UNKNOWN)
    a.label("tk_c"); E(str_imm, 3, 4, O_CCOL)
    a.label("tk_w"); E(movs_imm, 0, 0); E(str_imm, 0, 4, O_MASK)
    # the margin (dspload)
    E(ldr_imm, 0, 4, O_LAST); E(subs_reg, 0, 5, 0); E(cmp_imm, 0, SAMPLE_MS); E(b_cond, "tk_x", "lo"); E(str_imm, 5, 4, O_LAST)
    rd_dsp(Y_ISR); E(lsrs_imm, 6, 0, 8)
    rd_dsp(Y_BLK); E(lsrs_imm, 7, 0, 8)
    E(subs_reg, 0, 7, 6); E(lsls_imm, 0, 0, 22); E(lsrs_imm, 0, 0, 22)
    E(movw, 1, DRY); E(cmp_reg, 0, 1); E(b_cond, "tk_m", "ls")
    E(str_imm, 5, 4, O_DRY); E(ldr_imm, 0, 4, O_NDRY); E(adds_imm8, 0, 1); E(str_imm, 0, 4, O_NDRY); E(b, "tk_win")
    a.label("tk_m")
    E(ldr_imm, 1, 4, O_MIN); E(cmp_reg, 0, 1); E(b_cond, "tk_m2", "hs"); E(str_imm, 0, 4, O_MIN)
    a.label("tk_m2"); E(ldr_imm, 1, 4, O_WMIN); E(cmp_reg, 0, 1); E(b_cond, "tk_win", "hs"); E(str_imm, 0, 4, O_WMIN)
    a.label("tk_win")
    E(ldr_imm, 0, 4, O_W0); E(subs_reg, 0, 5, 0); E(movw, 1, WIN_MS); E(cmp_reg, 0, 1); E(b_cond, "tk_x", "lo")
    E(str_imm, 5, 4, O_W0); E(ldr_imm, 0, 4, O_MIN); E(str_imm, 0, 4, O_SMIN); imm32(0, 1023); E(str_imm, 0, 4, O_MIN)
    a.label("tk_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_ckseq (in front of the sequencer's tick): its interval, while playing
    a.label("c_ckseq")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_ckst"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(raw, h(0x7800))           # ldrb r0, [r0]
    E(ldr_imm, 6, 4, O_SEQ); E(str_imm, 5, 4, O_SEQ)
    E(cmp_imm, 0, 0); E(b_cond, "sq_0", "eq"); E(cmp_imm, 6, 0); E(b_cond, "sq_x", "eq")
    E(subs_reg, 6, 5, 6)
    imm32(0, TEMPO); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(raw, h(0x7801)); E(cmp_imm, 1, 30); E(b_cond, "sq_b", "hs"); E(movs_imm, 1, 120)   # ldrb r1, [r0]: p0 = BPM
    a.label("sq_b"); imm32(0, 3750); E(raw, udiv(0, 0, 1)); E(adds_imm8, 0, 2)
    E(cmp_reg, 6, 0); E(b_cond, "sq_x", "ls"); E(str_imm, 5, 4, O_TSEQ); E(ldr_imm, 0, 4, O_NSEQ); E(adds_imm8, 0, 1); E(str_imm, 0, 4, O_NSEQ)
    if SEQCUL:
        E(ldr_imm, 2, 4, O_SMASK)
        for bit, col in CUL_COLS:
            E(movs_imm, 3, col); E(movs_imm, 0, bit); E(raw, h(0x4210)); E(b_cond, "sq_c", "ne")                 # tst r0, r2
        E(movs_imm, 3, COL_SEQ)
        a.label("sq_c"); E(str_imm, 3, 4, O_SCOL)
    E(b, "sq_x")
    a.label("sq_0"); E(movs_imm, 0, 0); E(str_imm, 0, 4, O_SEQ)
    a.label("sq_x")
    if SEQCUL: E(movs_imm, 0, 0); E(str_imm, 0, 4, O_SMASK)
    E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["seq"])

    # ---- c_ckled (the LED task calls: ctrl, frame): nothing on the stack while the chain runs (its LR and start time in RAM, never nested), then
    #      timed (>= LONG_MS = B_LED) and the three LEDs drawn into the frame
    a.label("c_ckled")
    imm32(12, RAM); E(raw, str_w(14, 12, O_LLR)); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(raw, str_w(2, 12, O_LT0))
    E(raw, str_w(1, 12, O_FR))                                                    # the frame
    E(bl, prev["ledtask"])
    E(push_list, [0, 4, 5, 6, 7])
    E(bl, "c_ckst"); E(mov_reg, 4, 0); E(ldr_imm, 5, 4, O_FR)
    imm32(0, HAL_TICK); E(ldr_imm, 6, 0, 0)
    E(ldr_imm, 0, 4, O_LT0); E(subs_reg, 0, 6, 0); E(cmp_imm, 0, LONG_MS); E(b_cond, "ld_t", "lo")
    E(ldr_imm, 0, 4, O_MASK); E(movs_imm, 1, B_LED); E(raw, h(0x4308)); E(str_imm, 0, 4, O_MASK)         # orrs r0, r1
    if SEQCUL: E(ldr_imm, 0, 4, O_SMASK); E(raw, h(0x4308)); E(str_imm, 0, 4, O_SMASK)
    a.label("ld_t")
    # Save: the margin
    E(ldr_imm, 0, 4, O_DRY); E(cmp_imm, 0, 0); E(b_cond, "ld_c", "eq")
    E(subs_reg, 1, 6, 0); imm32(0, DRY_MS); E(cmp_reg, 1, 0); E(b_cond, "ld_c", "hs")
    E(movs_imm, 1, COL_DRY); E(b, "ld_cw")
    a.label("ld_c")
    E(ldr_imm, 0, 4, O_SMIN); E(movs_imm, 1, COL_LATE)
    for i, (m, col) in enumerate(CPU_STEPS):
        E(cmp_imm, 0, m); E(b_cond, f"ld_c{i}", "lo"); E(movs_imm, 1, col); E(b, "ld_cw"); a.label(f"ld_c{i}")
    E(movs_imm, 1, COL_LATE)
    a.label("ld_cw"); E(movs_imm, 0, 2 * LED_SAVE); E(raw, h(0x5229))                # strh r1, [r5, r0]
    # Duplicate: the last gap's culprit for 1 s; Play: a late sequencer tick for 400 ms
    for off, led, fl in ((O_TGAP, LED_DUP, CUL_FLASH), (O_TSEQ, LED_PLAY, SEQ_FLASH)):
        lab = f"ld_{led}"
        E(ldr_imm, 0, 4, off); E(cmp_imm, 0, 0); E(b_cond, lab, "eq"); E(subs_reg, 0, 6, 0); E(movw, 1, fl); E(cmp_reg, 0, 1); E(b_cond, lab, "hs")
        if led == LED_DUP: E(ldr_imm, 1, 4, O_CCOL)
        elif SEQCUL: E(ldr_imm, 1, 4, O_SCOL)
        else: E(movs_imm, 1, COL_SEQ)
        E(movs_imm, 0, 2 * led); E(raw, h(0x5229))
        a.label(lab)
    E(pop_list, [0, 4, 5, 6, 7])
    imm32(12, RAM); E(raw, ldr_w(14, 12, O_LLR)); E(raw, RET)

    # ---- the main loop's call of the DSP service (bl), timed: >= LONG_MS = B_SVC (LR / start in RAM: the main task only, never nested)
    a.label("c_cksvc")
    imm32(12, RAM); E(raw, str_w(14, 12, O_SLR)); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(raw, str_w(2, 12, O_ST0))
    E(bl, SVC)
    imm32(12, RAM); imm32(2, HAL_TICK); E(ldr_imm, 2, 2, 0); E(raw, ldr_w(3, 12, O_ST0)); E(subs_reg, 2, 2, 3); E(cmp_imm, 2, LONG_MS); E(b_cond, "sv_x", "lo")
    E(raw, ldr_w(2, 12, O_MASK)); E(raw, orr_imm(2, 2, B_SVC)); E(raw, str_w(2, 12, O_MASK))
    if SEQCUL: E(raw, ldr_w(2, 12, O_SMASK)); E(raw, orr_imm(2, 2, B_SVC)); E(raw, str_w(2, 12, O_SMASK))
    a.label("sv_x"); E(raw, ldr_w(14, 12, O_SLR)); E(raw, RET)

    # ---- pad / knob events, timed (they may nest: r4 / LR on the stack, 12 B)
    def timed(label, moved, back, bit):
        a.label(label + "_t"); E(raw, moved); E(b_w, back)
        a.label(label)
        E(push_list, [4], lr=True)
        imm32(3, HAL_TICK); E(ldr_imm, 4, 3, 0)
        E(bl, label + "_t")
        E(push_list, [0]); imm32(3, HAL_TICK); E(ldr_imm, 3, 3, 0); E(subs_reg, 3, 3, 4); E(cmp_imm, 3, LONG_MS); E(b_cond, label + "_x", "lo")
        imm32(3, RAM + O_MASK); E(ldr_imm, 1, 3, 0); E(movs_imm, 2, bit); E(raw, h(0x4311)); E(str_imm, 1, 3, 0)   # orrs r1, r2
        if SEQCUL: E(ldr_imm, 1, 3, O_SMASK - O_MASK); E(raw, h(0x4311)); E(str_imm, 1, 3, O_SMASK - O_MASK)
        a.label(label + "_x"); E(pop_list, [0]); E(pop_list, [4], pc=True)
    timed("c_ckpad", prev["pad_old"], PAD_IN + 4, B_PAD)
    timed("c_ckknob", prev["knob_old"], KNOB_IN + 4, B_KNOB)

    # ---- the storage API: any access (its two dispatchers), and the ones called from the mod (LR in the mod's code); 8 B of stack
    def mark(bit, label):
        E(push_list, [0, 1]); imm32(0, RAM + O_MASK); E(ldr_imm, 1, 0, 0)
        E(raw, orr_imm(1, 1, bit)); E(str_imm, 1, 0, 0)
        if SEQCUL: E(ldr_imm, 1, 0, O_SMASK - O_MASK); E(raw, orr_imm(1, 1, bit)); E(str_imm, 1, 0, O_SMASK - O_MASK)
        E(pop_list, [0, 1])
    a.label("c_cksd"); mark(B_SD, "a"); E(raw, prev["sd_old"]); E(b_w, SD_TAIL)
    a.label("c_cksd2"); mark(B_SD, "b"); E(raw, prev["sd2_old"]); E(b_w, SD_TAIL2)
    def modcheck(label, moved, back):
        a.label(label)
        E(push_list, [0, 1])
        E(mov_reg, 0, 14); imm32(1, MOD_START); E(cmp_reg, 0, 1); E(b_cond, label + "_x", "lo")
        imm32(1, end_mod); E(cmp_reg, 0, 1); E(b_cond, label + "_x", "hs")
        imm32(0, RAM + O_MASK); E(ldr_imm, 1, 0, 0); E(raw, orr_imm(1, 1, B_SDMOD)); E(str_imm, 1, 0, 0)
        if SEQCUL: E(ldr_imm, 1, 0, O_SMASK - O_MASK); E(raw, orr_imm(1, 1, B_SDMOD)); E(str_imm, 1, 0, O_SMASK - O_MASK)
        a.label(label + "_x"); E(pop_list, [0, 1])
        if moved is not None: E(raw, moved)
        E(b_w, back)
    for i, hd in enumerate(SD_HEADS): modcheck(f"c_ckh{i}", prev[f"h{i}_old"], hd + 4)
    for i, hd in enumerate(SD_CHAINS): modcheck(f"c_ckc{i}", None, prev[f"c{i}"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code at the end of the image; the hooks: the DSP service chain's head, the sequencer's tick, the LED task calls, the main loop's
    service call, the controller's pad / knob entries, the storage API's dispatchers and heads."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    old = lambda a_: bytes(img[a_ - BASE:a_ - BASE + 4])
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), seq=MP.bw_target(img, SEQ_TICK, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE),
                pad_old=old(PAD_IN), knob_old=old(KNOB_IN), sd_old=old(SD_ANY), sd2_old=old(SD_ANY2),
                **{f"h{i}_old": old(hd) for i, hd in enumerate(SD_HEADS)}, **{f"c{i}": MP.bw_target(img, hd, BASE) for i, hd in enumerate(SD_CHAINS)})
    assert prev["pad_old"] == bytes.fromhex("70b50646") and prev["knob_old"] == bytes.fromhex("70b50446"), (prev["pad_old"].hex(), prev["knob_old"].hex())
    assert prev["sd_old"] == bytes.fromhex("2de9f04f") and prev["sd2_old"] == bytes.fromhex("38b596b0") and old(MAIN_SVC_CALL) == bl(MAIN_SVC_CALL, SVC)
    assert old(SD_HEADS[0]) == old(SD_HEADS[1]) == bytes.fromhex("01460020") and old(SD_HEADS[2]) == bytes.fromhex("5cb585b0")
    end_mod = BASE + 0x70000                                       # the mod's code ends with the flash (RAM never holds code here)
    code, labels = arm_code(base_addr, prev, end_mod)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000, hex(len(img))
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_cktick"])
    img[SEQ_TICK - BASE:SEQ_TICK - BASE + 4] = b_w(SEQ_TICK, labels["c_ckseq"])
    for c in PK.LED_CALLS:
        assert FD.bl_target(img, c, BASE) == prev["ledtask"], hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_ckled"])
    img[MAIN_SVC_CALL - BASE:MAIN_SVC_CALL - BASE + 4] = bl(MAIN_SVC_CALL, labels["c_cksvc"])
    img[PAD_IN - BASE:PAD_IN - BASE + 4] = b_w(PAD_IN, labels["c_ckpad"])
    img[KNOB_IN - BASE:KNOB_IN - BASE + 4] = b_w(KNOB_IN, labels["c_ckknob"])
    img[SD_ANY - BASE:SD_ANY - BASE + 4] = b_w(SD_ANY, labels["c_cksd"])
    img[SD_ANY2 - BASE:SD_ANY2 - BASE + 4] = b_w(SD_ANY2, labels["c_cksd2"])
    for i, hd in enumerate(SD_HEADS): img[hd - BASE:hd - BASE + 4] = b_w(hd, labels[f"c_ckh{i}"])
    for i, hd in enumerate(SD_CHAINS): img[hd - BASE:hd - BASE + 4] = b_w(hd, labels[f"c_ckc{i}"])
    assert RAM + O_SCOL + 4 <= MX.MXR + 0x2000
    return labels, code, {k: v for k, v in prev.items() if isinstance(v, int)}
