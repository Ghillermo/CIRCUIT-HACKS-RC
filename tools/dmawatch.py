"""S564D3 (diagnostic, 2026-11-15): who writes 0x20042988 (0x0805ACC8 -> 0x000F0009, the 5.64 crashes) when neither S564D's DWT watchpoint nor
S564D2's MPU read-only region caught a CPU store: most likely a DMA transfer.  Every LED frame this head compares the two corrupted words (5.64:
0x20042988 = 0x0805ACC8; 5.63: 0x20043610 = 0x0805ADA8) with their boot values; at the first difference it freezes the black box (state MANUAL |
0x80: the ring holds the gestures before) and overwrites its first stack copy (BB + O.STK1, 384 B) with:
  + 0   the frame count since boot (1 = already wrong at the first frame: the boot / project load), + 4 the word now;
  + 8   DMA1 streams 0-7 then DMA2 streams 0-7: NDTR, M0AR, CR, PAR (16 B each, 256 B): what each stream writes to and how much is left.
  (Only the 5.64 word; the 5.63 one is not watched: flash.)
Read it with python tools/bbread.py (the raw hex).  RAM 0x2004FAF0: + 0 the LR, + 4 fired, + 8 the frame count (u32).  In dspz's first gap."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, adds_reg, b, b_cond, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, movs_imm, movt, movw, pop_list, push_list, raw, str_imm, strb_imm  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import blackbox as BB  # noqa: E402

DM = 0x2004FAF0
WATCH = ((0x20042988, 0x0805ACC8), (0x20043610, 0x0805ADA8))
STATE = BB.ST_FROZEN | BB.ST_MANUAL | 0x80
DMA1, DMA2, SDMMC1 = 0x40026000, 0x40026400, 0x40012C00
OUT = BB.BB + BB.O.STK1
assert DM + 12 <= 0x2004FC00                          # (a build with mpuwatch too moves DM: dmawatch.DM = 0x2004FB00 before install)


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, v >> 16)
    w, v = WATCH[0]
    a.label("c_dmled")
    imm32(2, DM); E(raw, h(0xF8C2) + h(0xE000))                                  # str.w lr, [r2]
    E(bl, prev["ledtask"])
    E(push_list, [4, 5, 6, 7])
    imm32(4, DM); E(ldrb_imm, 0, 4, 4); E(cmp_imm, 0, 0); E(b_cond, "dm_x", "ne")
    E(ldr_imm, 0, 4, 8); E(adds_imm8, 0, 1); E(str_imm, 0, 4, 8)                 # frames + 1
    imm32(5, w); E(ldr_imm, 0, 5, 0); imm32(1, v); E(cmp_reg, 0, 1); E(b_cond, "dm_x", "eq")
    E(movs_imm, 0, 1); E(strb_imm, 0, 4, 4)
    E(movs_imm, 0, STATE); E(bl, L["c_bbfrz"])
    imm32(6, OUT)
    E(ldr_imm, 0, 4, 8); E(str_imm, 0, 6, 0); E(ldr_imm, 0, 5, 0); E(str_imm, 0, 6, 4)   # + 0 the frames, + 4 the word now
    imm32(1, DMA1 + 0x10); E(movs_imm, 2, 0)                                      # + 8: 16 x (NDTR, M0AR, CR, PAR)
    a.label("dm_s")
    for k in (4, 0xC, 0, 8):
        E(ldr_imm, 0, 1, k); E(str_imm, 0, 6, 8); E(adds_imm8, 6, 4)
    E(adds_imm8, 1, 0x18); E(adds_imm8, 2, 1); E(cmp_imm, 2, 8); E(b_cond, "dm_n", "ne")
    imm32(1, DMA2 + 0x10)
    a.label("dm_n"); E(cmp_imm, 2, 16); E(b_cond, "dm_s", "lo")
    a.label("dm_x")
    E(pop_list, [4, 5, 6, 7]); imm32(2, DM); E(ldr_imm, 2, 2, 0); E(raw, h(0x4710))      # bx r2
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    L = dict(c_bbfrz=int(report["blackbox"]["labels"]["c_bbfrz"], 16))
    prev = dict(ledtask=FD.bl_target(img, PK.LED_CALLS[0], BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl_enc(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_dmled"])
    report["dmawatch"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, prev={k: hex(v) for k, v in prev.items()}, ram=hex(DM))
    return labels, code, prev
