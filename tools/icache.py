"""The Cortex-M7's instruction cache on at power-up (S702D2, 2026-11-17; the user: «tempo drag» with 6 voices of the 8-operator FM).  S702D read
the device: SYSCLK 120 MHz, SCB CCR 0x00040200 = I-cache off, D-cache off (branch prediction on), FLASH ACR 3 wait states with ART / prefetch on;
on the F7 those serve only the flash's ITCM bus (0x0020_0000) and the app runs from 0x0801_0000 over AXI, so every fetch waits for the flash.

The stock enables the FPU at reset in 0x0805B790 (CPACR, dsb, isb, FPSCR, bx lr: a leaf, before main and the RTOS).  Its `isb sy` at 0x0805B7A4
becomes `b.w c_icon` (NOT bl: the stock routine is a leaf that returns with bx lr; a bl there overwrote LR and the routine returned into
itself forever: S702D2's first build did not boot, 2026-11-17): isb, then CMSIS's SCB_EnableICache: dsb, isb, ICIALLU = 0 (invalidate all), dsb,
isb, CCR |= IC (bit 17), dsb, isb, and b.w back to 0x0805B7A8.  r0 / r1 only (the stock then sets r0).  The D-cache stays off (the SD card's and the audio's DMA would need cache maintenance).  Nothing of ours
runs code from cached RAM (the ITCM is not cached).  In dspz's first gap (dspz.add)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, b_cond, b_w, h, ldr_imm, lsls_imm, movs_imm, movt, movw, raw, str_imm  # noqa: E402

SITE = 0x0805B7A4
BACK = SITE + 4
ISB = bytes.fromhex("bff36f8f")                  # isb sy
DSB = bytes.fromhex("bff34f8f")                  # dsb sy
ICIALLU, CCR = 0xE000EF50, 0xE000ED14
DWT = False                                      # (S703D, use_dwt)
DEMCR, DWT_LAR, DWT_CTRL = 0xE000EDFC, 0xE0001FB0, 0xE0001000
SAMP, SAMP_LEN = 0x2004F600, 0x200               # blackbox.use_samp's tables (free: S514D, 0x2004F4B0-0x2004F7FF; fmmap's ends at 0x2004F598)
BKP = False                                      # (S725D, use_bkp)
BKPSRAM, BKP_MAGIC = 0x40024000, 0x31504B42      # "BKP1"
BKP_SEED, BKP_K, BKP_HDR = 0xB4C0FFEE, 0x9E3779B9, 64
RCC_AHB1ENR, RCC_APB1ENR, RCC_CSR, PWR_CR1 = 0x40023830, 0x40023840, 0x40023874, 0x40007000


def use_bkp():
    """S725D (diagnostic, the user, 2026-11-21: «test whether we can use that RAM»): at reset, the backup SRAM (4 KB at 0x40024000, the stock's USB
    drive buffer, unused since msdcut) probed.  Kept first: RCC_AHB1ENR, RCC_APB1ENR, PWR_CR1 as the reset left them and RCC_CSR (the reset
    cause); then the PWR clock, PWR_CR1.DBP and BKPSRAMEN on.  Header (bytes): + 0 "BKP1", + 4 boots, + 8 / + 12 / + 16 / + 20 the four words
    above, + 24 words of the pattern (+ 64 .. + 4095, word i = SEED + i x K) that differ from the last boot's (0xFFFFFFFF: no "BKP1" = lost),
    + 28 the same right after writing it again (0 = the RAM works).  tools/bbread.py --mem 0x40024000 4096 reads it while the device runs: a
    differing pattern word = someone else writes there."""
    global BKP
    BKP = True


def use_dwt():
    """S703D (diagnostic, the user, 2026-11-18: «make a diag build for all those»): also at power-up the cycle counter on (DEMCR TRCENA, the M7's
    DWT lock access key, CYCCNTENA) and blackbox.use_samp's tables zeroed (0x2004F600..0x2004F7FF)."""
    global DWT
    DWT = True


def arm_code(base):
    a = Asm(base)
    E = a.emit
    a.label("c_icon")
    E(raw, ISB); E(raw, DSB); E(raw, ISB)
    E(movw, 1, ICIALLU & 0xFFFF); E(movt, 1, ICIALLU >> 16); E(movs_imm, 0, 0); E(str_imm, 0, 1, 0)
    E(raw, DSB); E(raw, ISB)
    E(movw, 1, CCR & 0xFFFF); E(movt, 1, CCR >> 16); E(ldr_imm, 0, 1, 0)
    E(raw, bytes.fromhex("40f40030"))            # orr r0, r0, #0x20000 (IC)
    E(str_imm, 0, 1, 0)
    E(raw, DSB); E(raw, ISB)
    if DWT:
        from thumb import orrs_reg, subs_imm8
        E(movw, 1, DEMCR & 0xFFFF); E(movt, 1, DEMCR >> 16); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 24)
        E(orrs_reg, 0, 2); E(str_imm, 0, 1, 0)                                          # TRCENA
        E(movw, 1, DWT_LAR & 0xFFFF); E(movt, 1, DWT_LAR >> 16); E(movw, 0, 0xCE55); E(movt, 0, 0xC5AC); E(str_imm, 0, 1, 0)
        E(movw, 1, DWT_CTRL & 0xFFFF); E(movt, 1, DWT_CTRL >> 16); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 1)
        E(orrs_reg, 0, 2); E(str_imm, 0, 1, 0)                                          # CYCCNTENA
        E(movw, 1, SAMP & 0xFFFF); E(movt, 1, SAMP >> 16); E(movs_imm, 0, 0); E(movs_imm, 2, SAMP_LEN // 4)
        a.label("ic_z"); E(str_imm, 0, 1, 0); E(adds_imm8, 1, 4); E(subs_imm8, 2, 1); E(b_cond, "ic_z", "ne")
        E(raw, DSB); E(raw, ISB)
    if BKP:
        from thumb import orrs_reg, push_list, pop_list, adds_reg, cmp_reg, mov_reg, bl, b
        def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
        E(push_list, [4, 5, 6, 7], lr=True)
        imm32(1, RCC_AHB1ENR); E(ldr_imm, 4, 1, 0)
        imm32(1, RCC_APB1ENR); E(ldr_imm, 5, 1, 0)
        imm32(1, PWR_CR1); E(ldr_imm, 6, 1, 0)
        imm32(1, RCC_APB1ENR); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 28); E(orrs_reg, 0, 2); E(str_imm, 0, 1, 0); E(raw, DSB)
        imm32(1, PWR_CR1); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 8); E(orrs_reg, 0, 2); E(str_imm, 0, 1, 0)
        imm32(1, RCC_AHB1ENR); E(ldr_imm, 0, 1, 0); E(movs_imm, 2, 1); E(lsls_imm, 2, 2, 18); E(orrs_reg, 0, 2); E(str_imm, 0, 1, 0)
        E(raw, DSB); E(raw, ISB)
        imm32(7, BKPSRAM)
        E(str_imm, 4, 7, 8); E(str_imm, 5, 7, 12); E(str_imm, 6, 7, 16)
        imm32(1, RCC_CSR); E(ldr_imm, 0, 1, 0); E(str_imm, 0, 7, 20)
        E(ldr_imm, 0, 7, 0); imm32(1, BKP_MAGIC); E(cmp_reg, 0, 1); E(b_cond, "bk_new", "ne")
        E(ldr_imm, 0, 7, 4); E(adds_imm8, 0, 1); E(str_imm, 0, 7, 4)
        E(bl, "bk_chk"); E(b, "bk_wr")
        a.label("bk_new"); E(movs_imm, 0, 1); E(str_imm, 0, 7, 4); E(movs_imm, 6, 0); E(raw, bytes.fromhex("f643"))   # mvns r6, r6 = 0xFFFFFFFF
        a.label("bk_wr"); E(str_imm, 6, 7, 24)
        imm32(1, BKP_SEED); imm32(4, BKP_K); E(mov_reg, 2, 7); E(adds_imm8, 2, BKP_HDR); imm32(5, BKPSRAM + 4096)
        a.label("bk_wl"); E(str_imm, 1, 2, 0); E(adds_reg, 1, 1, 4); E(adds_imm8, 2, 4); E(cmp_reg, 2, 5); E(b_cond, "bk_wl", "ne")
        E(raw, DSB)
        E(bl, "bk_chk"); E(str_imm, 6, 7, 28)
        imm32(1, BKP_MAGIC); E(str_imm, 1, 7, 0); E(raw, DSB)
        E(raw, bytes.fromhex("bde8f040"))                                          # pop.w {r4-r7, lr}
        E(b_w, BACK)
        a.label("bk_chk")                                                          # r7 = BKPSRAM -> r6 = pattern words that differ (r0-r5 clobbered)
        imm32(1, BKP_SEED); imm32(4, BKP_K); E(mov_reg, 2, 7); E(adds_imm8, 2, BKP_HDR); imm32(5, BKPSRAM + 4096); E(movs_imm, 6, 0)
        a.label("bk_cl"); E(ldr_imm, 0, 2, 0); E(cmp_reg, 0, 1); E(b_cond, "bk_ok", "eq"); E(adds_imm8, 6, 1)
        a.label("bk_ok"); E(adds_reg, 1, 1, 4); E(adds_imm8, 2, 4); E(cmp_reg, 2, 5); E(b_cond, "bk_cl", "ne")
        E(raw, h(0x4770))
        return a.assemble()
    E(b_w, BACK)                                 # back to the stock routine (its own bx lr returns to its caller)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import b_w as bw_enc
    BASE = ct_fw.APP_BASE
    assert bytes(img[SITE - BASE:SITE - BASE + 4]) == ISB, "0x0805B7A4 is not the stock's isb"
    code, labels = arm_code(base_addr)
    img += code
    img[SITE - BASE:SITE - BASE + 4] = bw_enc(SITE, labels["c_icon"])
    return labels, code, {}
