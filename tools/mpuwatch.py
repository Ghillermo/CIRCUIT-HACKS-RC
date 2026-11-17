"""S564D2 (diagnostic, 2026-11-15): the MPU instead of the DWT to catch the writer of the word 0x20042988 (the 5.64 crashes: 0x0805ACC8 ->
0x000F0009).  S564D's DWT write watchpoint on that word did not fire before the next crash (the record: a plain BusFault, vector 5): either the
write is a DMA transfer (the DWT and the MPU only see the CPU) or the debug event was lost (a top-priority handler).  The 32 bytes 0x20042980..
0x2004299F (Synth 1's Preset view's head: its vtable, LED buffer, listener vtable and store pointers, written only by its constructor at boot; no
gesture of the emulation writes them) become read-only with MPU region 0 (no other region: the stock never uses the MPU; PRIVDEFENA keeps the
default map everywhere else; normal write-back memory as the default map has; XN): any CPU write there raises a MemManage fault at once (the stock
sets MEMFAULTENA; set again here), which the black box captures as a fault of vector 4 with the writer's PC / LR, the CFSR and MMFAR (the address);
the device then restarts.  If the word changes with no fault, the writer is DMA.
A head of the LED task arms it once (RAM 0x2004FAF0: + 0 the LR, + 4 armed).  Code in dspz's first gap (dspz.add)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, bl, cmp_imm, h, ldr_imm, ldrb_imm, movs_imm, movt, movw, orrs_reg, raw, str_imm, strb_imm  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

MW = 0x2004FAF0
REGION = 0x20042980                                    # 32-byte aligned, 32 bytes
MPU_CTRL, MPU_RNR, MPU_RBAR, MPU_RASR, SHCSR = 0xE000ED94, 0xE000ED98, 0xE000ED9C, 0xE000EDA0, 0xE000ED24
RASR = (1 << 28) | (6 << 24) | (1 << 19) | (1 << 17) | (1 << 16) | (4 << 1) | 1   # XN, AP read-only, TEX 1 C B (normal WB-WA), 32 B, enabled
assert REGION % 32 == 0 and MW + 8 <= 0x2004FC00


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, v >> 16)
    a.label("c_mwled")
    imm32(2, MW); E(raw, h(0xF8C2) + h(0xE000))                                  # str.w lr, [r2]
    E(bl, prev["ledtask"])
    imm32(2, MW); E(ldrb_imm, 0, 2, 4); E(cmp_imm, 0, 0); E(b_cond, "mw_x", "ne")
    E(movs_imm, 0, 1); E(strb_imm, 0, 2, 4)
    imm32(0, SHCSR); E(ldr_imm, 1, 0, 0); imm32(2, 0x10000); E(orrs_reg, 1, 2); E(str_imm, 1, 0, 0)   # MEMFAULTENA
    imm32(0, MPU_RNR); E(movs_imm, 1, 0); E(str_imm, 1, 0, 0)
    imm32(1, REGION); E(str_imm, 1, 0, 4)                                         # RBAR
    imm32(1, RASR); E(str_imm, 1, 0, 8)                                           # RASR
    imm32(0, MPU_CTRL); E(movs_imm, 1, 5); E(str_imm, 1, 0, 0)                   # ENABLE | PRIVDEFENA
    E(raw, h(0xF3BF) + h(0x8F4F)); E(raw, h(0xF3BF) + h(0x8F6F))                 # dsb sy; isb sy
    a.label("mw_x")
    imm32(2, MW); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))                       # bx r2: the LR from RAM
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_mwled"])
    report["mpuwatch"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()},
                              region=hex(REGION), rasr=hex(RASR))
    return labels, code, prev
