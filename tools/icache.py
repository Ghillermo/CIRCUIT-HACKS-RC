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
