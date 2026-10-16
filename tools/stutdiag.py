"""SC419D (diagnostic, the user 2026-10-15: «sigue habiendo stutter audibles (de ritmo) sobre el delay al cambiar entre modos de sinte o mover sus
perillas. Prepara un banco de pruebas si es necesario»): three live indicators, so the user sees at the moment of the stutter which part was late.

  * Save (LED 57) red: the DSP's audio blocks came slower.  Core 0 copies its block counter (granular_dsp's CNT, bumped at the end of its Master FX
    chain) to Y:$3B0F (granular_dsp.DIAGCNT); the DSP service tick reads it every >= 64 ms (0x08029344, from the tick: allowed) and compares the blocks
    per ms with the best rate seen (the baseline): under 95 % = late blocks (core 0 over its time, or core 1 late serving its external reads).
  * Duplicate (LED 56) yellow: the ARM main loop was late: two DSP service ticks more than 10 ms apart (SD reads, long UI work...).
  * Play (LED 49) orange: the sequencer's tick (0x0802C418, while playing) came more than 1.5 x its interval (2500 / BPM ms) after the previous one.
Each lights for 400 ms.  Counters in the record's tail + 600 (RAM): magic "SDG1", the last service tick, the window, the baseline, the three times,
and how many of each (+ 40 late blocks, + 44 main loop, + 48 sequencer), the worst gap of the main loop (+ 52, ms) and the lowest rate (+ 56, %).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, muls,  # noqa: E402
                   pop_list, push_list, raw, h, str_imm, subs_reg, adds_imm8)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import mpatch as MP  # noqa: E402
import build_sc14 as S14  # noqa: E402
from build_sc14 import udiv  # noqa: E402

SEQ_TICK = 0x0802C418
DSP_READ, CNT_Y = 0x08029344, 0x3B0F
HAL_TICK = 0x2000081C
TRANSPORT, TEMPO = 0x20011034, 0x20011404
PARAM_GET = 0x0803542C
SESSION_OBJ, TAIL, O_ST = 0x2003D71C, 0x27024, 600
MAGIC = 0x31474453                                             # "SDG1"
WIN, GAP_MS, FLASH_MS = 64, 10, 400
LED_PLAY, LED_DUP, LED_SAVE = 49, 56, 57
COL_SEQ, COL_GAP, COL_LATE = 0x09, 0x2D, 0x53
# state words (offsets from the state)
M, LASTSVC, WT0, WC0, RMAX, T_LATE, T_GAP, SEQLAST, T_SEQ, N_LATE, N_GAP, N_SEQ, GAPMAX, RMIN = (0, 4, 8, 12, 16, 20, 24, 28, 32, 40, 44, 48, 52, 56)
CULPRIT = False                                                # S419D2 (see use_culprit)
MASK, CCOL, SEEN = 60, 64, 68                                  # what ran long since the last service tick; the colour of the last gap; every culprit seen
LONG_MS, CUL_FLASH = 5, 1000
B_SDMOD, B_SD, B_SVC, B_LED, B_KNOB, B_PAD = 1, 2, 4, 8, 16, 32
CUL_COLS = ((B_SDMOD, 0x01), (B_SD, 0x07), (B_SVC, 0x6B), (B_LED, 0x09), (B_KNOB, 0x53), (B_PAD, 0x17))   # white, blue, peach, orange, red, green
COL_UNKNOWN = 0x2D
SD_ANY, SD_TAIL = 0x0803CA52, 0x0803CA56                       # the storage API's dispatcher (read / write / delete), after its first 4 bytes
SD_ANY2, SD_TAIL2 = 0x0803CADE, 0x0803CAE2                     # the other one (exists / size)
SD_HEADS = (0x0803CB50, 0x0803CB6A, 0x0803CBF0)                # exists / size / read: their first 4 bytes are moved out
SD_CHAINS = (0x0803CC16, 0x0803CC34)                           # write / delete: already b.w heads (rodisk)
MOD_START = 0x0805CDDC
MAIN_SVC_CALL, SVC = 0x0801D5D8, 0x08021392
PAD_IN, KNOB_IN = 0x08033282, 0x08033848


def use_culprit():
    """S419D2 (the user, 2026-10-15, with SC419D: «duplicate amarillo» = the main loop is late): on each gap of the main loop Duplicate lights 1 s in
    the colour of what ran during it, by priority: white = an SD access called from the mod, blue = an SD access of the stock, peach = the DSP service
    itself >= 5 ms, orange = the LED task >= 5 ms, red = a knob event >= 5 ms, green = a pad event >= 5 ms, yellow = none of them."""
    global CULPRIT
    CULPRIT = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def inc(reg_state, off):
        E(ldr_imm, 1, reg_state, off); E(adds_imm8, 1, 1); E(str_imm, 1, reg_state, off)

    # ---- c_sdst() -> r0 = the state (made on first use), or 0; clobbers r1-r3
    a.label("c_sdst")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "st_x", "eq")
    imm32(1, TAIL + O_ST); E(adds_reg, 0, 0, 1)
    E(ldr_imm, 1, 0, M); imm32(2, MAGIC); E(cmp_reg, 1, 2); E(b_cond, "st_x", "eq")
    E(movs_imm, 1, 0); E(movs_imm, 3, 0)
    a.label("st_z"); E(raw, h(0x50C1)); E(adds_imm8, 3, 4); E(cmp_imm, 3, 96 if CULPRIT else 64); E(b_cond, "st_z", "lo")   # str r1, [r0, r3]
    E(str_imm, 2, 0, M); E(movs_imm, 1, 100); E(str_imm, 1, 0, RMIN)
    a.label("st_x"); E(raw, h(0x4770))

    # ---- c_sdtick (the head of the DSP service chain): the main loop's gaps, the DSP's block rate
    a.label("c_sdtick")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "tk_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)                                          # r5 = now
    E(ldr_imm, 1, 4, LASTSVC); E(str_imm, 5, 4, LASTSVC); E(cmp_imm, 1, 0); E(b_cond, "tk_w", "eq")
    E(subs_reg, 1, 5, 1); E(ldr_imm, 2, 4, GAPMAX); E(cmp_reg, 1, 2); E(b_cond, "tk_g", "ls"); E(str_imm, 1, 4, GAPMAX)
    a.label("tk_g"); E(cmp_imm, 1, GAP_MS); E(b_cond, "tk_w", "lo"); E(str_imm, 5, 4, T_GAP); inc(4, N_GAP)
    if CULPRIT:
        E(ldr_imm, 2, 4, MASK); E(ldr_imm, 1, 4, SEEN); E(raw, h(0x4311)); E(str_imm, 1, 4, SEEN)      # orrs r1, r2
        for bit, col in CUL_COLS:
            E(movs_imm, 3, col); E(movs_imm, 0, bit); E(raw, h(0x4210)); E(b_cond, "tk_c", "ne")      # tst r0, r2
        E(movs_imm, 3, COL_UNKNOWN)
        a.label("tk_c"); E(str_imm, 3, 4, CCOL)
    a.label("tk_w")
    if CULPRIT: E(movs_imm, 0, 0); E(str_imm, 0, 4, MASK)
    E(ldr_imm, 6, 4, WT0); E(subs_reg, 6, 5, 6); E(cmp_imm, 6, WIN); E(b_cond, "tk_x", "lo")   # r6 = the window's ms
    E(movs_imm, 0, 0); imm32(1, 0x8000 | CNT_Y); E(bl, DSP_READ); E(lsrs_imm, 0, 0, 8)      # r0 = the DSP's block counter
    E(ldr_imm, 1, 4, WC0); E(str_imm, 0, 4, WC0); E(ldr_imm, 2, 4, WT0); E(str_imm, 5, 4, WT0)
    E(cmp_imm, 2, 0); E(b_cond, "tk_x", "eq")                                         # the first window
    E(cmp_imm, 6, 255); E(b_cond, "tk_x", "hi")                                       # a window too long (a gap of its own): not a rate
    E(subs_reg, 0, 0, 1); E(lsls_imm, 0, 0, 8); E(lsrs_imm, 0, 0, 8)                   # blocks in the window (24 bits)
    E(lsls_imm, 0, 0, 10); E(raw, udiv(0, 0, 6))                                       # r0 = blocks per 1024 ms
    E(ldr_imm, 1, 4, RMAX); E(cmp_reg, 0, 1); E(b_cond, "tk_r", "ls"); E(str_imm, 0, 4, RMAX); E(b, "tk_x")
    a.label("tk_r")
    E(cmp_imm, 1, 0); E(b_cond, "tk_x", "eq")
    E(movs_imm, 2, 100); E(mov_reg, 3, 0); E(muls, 3, 2); E(raw, udiv(3, 3, 1))           # r3 = the rate in % of the best
    E(ldr_imm, 2, 4, RMIN); E(cmp_reg, 3, 2); E(b_cond, "tk_m", "hs"); E(str_imm, 3, 4, RMIN)
    a.label("tk_m"); E(cmp_imm, 3, 95); E(b_cond, "tk_x", "hs"); E(str_imm, 5, 4, T_LATE); inc(4, N_LATE)
    a.label("tk_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["svc"])

    # ---- c_sdseq (in front of the sequencer's tick): its interval, while playing
    a.label("c_sdseq")
    E(raw, pushw([0, 1, 2, 3, 4, 5, 6, 7], lr=True))
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "sq_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 5, 0, 0)
    imm32(0, TRANSPORT); E(movs_imm, 1, 0); E(bl, PARAM_GET); E(raw, h(0x7800))           # ldrb r0, [r0]
    E(ldr_imm, 6, 4, SEQLAST); E(str_imm, 5, 4, SEQLAST)
    E(cmp_imm, 0, 0); E(b_cond, "sq_0", "eq"); E(cmp_imm, 6, 0); E(b_cond, "sq_x", "eq")
    E(subs_reg, 6, 5, 6)                                                              # r6 = ms since the last tick
    imm32(0, TEMPO); E(movs_imm, 1, 1); E(bl, PARAM_GET); E(raw, h(0x7801)); E(cmp_imm, 1, 30); E(b_cond, "sq_b", "hs"); E(movs_imm, 1, 120)   # ldrb r1, [r0]
    a.label("sq_b"); imm32(0, 3750); E(raw, udiv(0, 0, 1)); E(adds_imm8, 0, 2)          # 1.5 x 2500 / BPM ms (+ 2 for the ms ticks)
    E(cmp_reg, 6, 0); E(b_cond, "sq_x", "ls"); E(str_imm, 5, 4, T_SEQ); inc(4, N_SEQ); E(b, "sq_x")
    a.label("sq_0"); E(movs_imm, 0, 0); E(str_imm, 0, 4, SEQLAST)                       # stopped: no interval
    a.label("sq_x"); E(raw, popw([0, 1, 2, 3, 4, 5, 6, 7], lr=True)); E(b_w, prev["seq"])

    # ---- c_sdled (the LED task calls: ctrl, frame): the chain, then the three LEDs for 400 ms after their event
    a.label("c_sdled")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 5, 1); E(bl, prev["ledtask"])
    E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "ld_x", "eq"); E(mov_reg, 4, 0)
    imm32(0, HAL_TICK); E(ldr_imm, 6, 0, 0)
    for off, led, col in ((T_SEQ, LED_PLAY, COL_SEQ), (T_GAP, LED_DUP, COL_GAP), (T_LATE, LED_SAVE, COL_LATE)):
        lab = f"ld_{led}"
        fl = CUL_FLASH if (CULPRIT and led == LED_DUP) else FLASH_MS
        E(ldr_imm, 0, 4, off); E(cmp_imm, 0, 0); E(b_cond, lab, "eq"); E(subs_reg, 0, 6, 0); imm32(1, fl); E(cmp_reg, 0, 1); E(b_cond, lab, "hs")
        if CULPRIT and led == LED_DUP: E(ldr_imm, 1, 4, CCOL)
        else: E(movs_imm, 1, col)
        E(movs_imm, 0, 2 * led); E(raw, h(0x5229))                                       # strh r1, [r5, r0]
        a.label(lab)
    a.label("ld_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    if CULPRIT:
        # ---- c_pfbit(r0 = a bit): into the mask of this gap; clobbers r0-r3
        a.label("c_pfbit")
        E(push_list, [4], lr=True); E(mov_reg, 4, 0)
        E(bl, "c_sdst"); E(cmp_imm, 0, 0); E(b_cond, "pb_x", "eq")
        E(ldr_imm, 1, 0, MASK); E(raw, h(0x4321)); E(str_imm, 1, 0, MASK)                    # orrs r1, r4
        a.label("pb_x"); E(pop_list, [4], pc=True)

        # ---- timed wrappers: the call timed (r4 = its start), marked when it took >= 5 ms; r0 (the answer) kept
        def timed(label, target, bit):
            a.label(label)
            E(push_list, [4], lr=True)
            imm32(3, HAL_TICK); E(ldr_imm, 4, 3, 0)
            E(bl, target)
            E(push_list, [0]); imm32(3, HAL_TICK); E(ldr_imm, 3, 3, 0); E(subs_reg, 3, 3, 4); E(cmp_imm, 3, LONG_MS); E(b_cond, label + "_x", "lo")
            E(movs_imm, 0, bit); E(bl, "c_pfbit")
            a.label(label + "_x"); E(pop_list, [0]); E(pop_list, [4], pc=True)
        timed("c_pfsvc", SVC, B_SVC)
        timed("c_pfled", "c_sdled", B_LED)
        a.label("c_pfpad_t"); E(raw, prev["pad_old"]); E(b_w, PAD_IN + 4)
        timed("c_pfpad", "c_pfpad_t", B_PAD)
        a.label("c_pfknob_t"); E(raw, prev["knob_old"]); E(b_w, KNOB_IN + 4)
        timed("c_pfknob", "c_pfknob_t", B_KNOB)

        # ---- the storage API: any access (its dispatcher), and the ones called from the mod (LR inside the mod's code)
        a.label("c_pfsd")
        E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 0, B_SD); E(bl, "c_pfbit"); E(raw, popw([0, 1, 2, 3, 12], lr=True))
        E(raw, prev["sd_old"]); E(b_w, SD_TAIL)
        a.label("c_pfsd2")
        E(raw, pushw([0, 1, 2, 3, 12], lr=True)); E(movs_imm, 0, B_SD); E(bl, "c_pfbit"); E(raw, popw([0, 1, 2, 3, 12], lr=True))
        E(raw, prev["sd2_old"]); E(b_w, SD_TAIL2)

        def modcheck(label, moved, back):
            a.label(label)
            E(raw, pushw([0, 1, 2, 3, 12], lr=True))
            E(mov_reg, 0, 14); imm32(1, MOD_START); E(cmp_reg, 0, 1); E(b_cond, label + "_x", "lo")
            imm32(1, base + 0x2000); E(cmp_reg, 0, 1); E(b_cond, label + "_x", "hs")              # the mod's code only (not the RAM)
            E(movs_imm, 0, B_SDMOD); E(bl, "c_pfbit")
            a.label(label + "_x"); E(raw, popw([0, 1, 2, 3, 12], lr=True))
            if moved is not None: E(raw, moved)
            E(b_w, back)
        for i, hd in enumerate(SD_HEADS): modcheck(f"c_pfh{i}", prev[f"h{i}_old"], hd + 4)
        for i, hd in enumerate(SD_CHAINS): modcheck(f"c_pfc{i}", None, prev[f"c{i}"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the head of the DSP service chain, the sequencer's tick, the LED task calls."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(svc=MP.bw_target(img, S14.SVC_HOOK, BASE), seq=MP.bw_target(img, SEQ_TICK, BASE), ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    old = lambda a_: bytes(img[a_ - BASE:a_ - BASE + 4])
    if CULPRIT:
        prev.update(pad_old=old(PAD_IN), knob_old=old(KNOB_IN), sd_old=old(SD_ANY), sd2_old=old(SD_ANY2),
                    **{f"h{i}_old": old(hd) for i, hd in enumerate(SD_HEADS)}, **{f"c{i}": MP.bw_target(img, hd, BASE) for i, hd in enumerate(SD_CHAINS)})
        assert prev["pad_old"] == bytes.fromhex("70b50646") and prev["knob_old"] == bytes.fromhex("70b50446"), (prev["pad_old"].hex(), prev["knob_old"].hex())
        assert prev["sd_old"] == bytes.fromhex("2de9f04f") and prev["sd2_old"] == bytes.fromhex("38b596b0") and old(MAIN_SVC_CALL) == bl(MAIN_SVC_CALL, SVC)
        assert old(SD_HEADS[0]) == old(SD_HEADS[1]) == bytes.fromhex("01460020"), old(SD_HEADS[0]).hex()
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[S14.SVC_HOOK - BASE:S14.SVC_HOOK - BASE + 4] = b_w(S14.SVC_HOOK, labels["c_sdtick"])
    img[SEQ_TICK - BASE:SEQ_TICK - BASE + 4] = b_w(SEQ_TICK, labels["c_sdseq"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_pfled" if CULPRIT else "c_sdled"])
    if CULPRIT:
        img[MAIN_SVC_CALL - BASE:MAIN_SVC_CALL - BASE + 4] = bl(MAIN_SVC_CALL, labels["c_pfsvc"])
        img[PAD_IN - BASE:PAD_IN - BASE + 4] = b_w(PAD_IN, labels["c_pfpad"])
        img[KNOB_IN - BASE:KNOB_IN - BASE + 4] = b_w(KNOB_IN, labels["c_pfknob"])
        img[SD_ANY - BASE:SD_ANY - BASE + 4] = b_w(SD_ANY, labels["c_pfsd"])
        img[SD_ANY2 - BASE:SD_ANY2 - BASE + 4] = b_w(SD_ANY2, labels["c_pfsd2"])
        for i, hd in enumerate(SD_HEADS): img[hd - BASE:hd - BASE + 4] = b_w(hd, labels[f"c_pfh{i}"])
        for i, hd in enumerate(SD_CHAINS): img[hd - BASE:hd - BASE + 4] = b_w(hd, labels[f"c_pfc{i}"])
    return labels, code, {k: v for k, v in prev.items() if isinstance(v, int)}
