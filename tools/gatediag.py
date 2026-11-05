"""S494D (DIAGNOSTIC): do DSP host writes land inside a PCM upload's bulk interval on the Tracks?  Counted, nothing dropped (RYTHM's dspgate drops them).

Arrhythmia (llcoolkm, MIT) found on the Circuit Rhythm, and RYTHM's tools/dspgate.py describes: a PCM upload puts core 0's host port in bulk mode
and leaves it every 4 096 words, sending 2 KB pieces and reading the next one from the card through the storage task's queue (the uploader waits, the
other tasks run), without the DSP service's lock and with core 0's chip select low: a host write in that window goes into the sample stream.  The Tracks
twins (map/xmap.json of RYTHM): bulk enter 0x080295E4(core) / leave 0x08029626(core), called by the sample loader (0x08049AD6 / 0x08049AC4 / 0x08049BA0,
piece 0x080296B0, card reads 0x08049ABE / 0x08049B36 = 0x0803CBD6), the SysEx upload (0x08048DD2) and 0x08035ECE; the host writers 0x080292F8 (16-bit
form, the one everything calls) and 0x08029314.

Heads of the four: enter / leave set and clear a byte and count the intervals; a write while the byte is set is counted as ours (LR in the hole
0x080101F0..0x0801855A or past the stock image, 0x0805CDDC..0x0807FFFF) or the stock's, with our last LR kept.  Block at RAM 0x2004EF00 (above the heap, below
0x2004F000; nobody else uses it in SC49.4): + 0 'DGT1' (set, with the rest zeroed, by the first enter), + 4 in an interval, + 8 intervals,
+ 12 our writes inside, + 16 the stock's writes inside, + 20 our last LR.  Read with tools/ctremote.py mem 0x2004EF00 24.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list,  # noqa: E402
                   push_list, raw, str_imm, strb_imm)
import hole  # noqa: E402

ENTER, LEAVE = 0x080295E4, 0x08029626
W16, W24 = 0x080292F8, 0x08029314
HEADS = {ENTER: "38b50446", LEAVE: "38b50446", W16: "f8b50d46", W24: "f8b50446"}
MOD_START = 0x0805CDDC
FLASH_END = 0x08080000
BLOCK = 0x2004EF00
SIG = 0x31544744                                 # 'DGT1'
R_SIG, R_IN, R_N, R_OURS, R_STOCK, R_LR = 0, 4, 8, 12, 16, 20


def arm_code(base):
    a = Asm(base)
    E = a.emit

    def imm32(rd, v):
        E(movw, rd, v & 0xFFFF)
        E(movt, rd, (v >> 16) & 0xFFFF)

    def tail(addr):                              # the hooked function's own first 4 bytes, then the rest of it
        E(raw, bytes.fromhex(HEADS[addr]))
        E(b_w, addr + 4)

    # ---- enter (r0 = the core; r1, r2 free): the block on first use, the byte, the count
    a.label("c_dgon")
    imm32(1, BLOCK)
    E(ldr_imm, 2, 1, R_SIG)
    imm32(3, SIG)
    E(cmp_reg, 2, 3)
    E(b_cond, "dg_s", "eq")
    E(str_imm, 3, 1, R_SIG)
    E(movs_imm, 2, 0)
    for o in (R_IN, R_N, R_OURS, R_STOCK, R_LR):
        E(str_imm, 2, 1, o)
    a.label("dg_s")
    E(movs_imm, 2, 1)
    E(strb_imm, 2, 1, R_IN)
    E(ldr_imm, 2, 1, R_N)
    E(adds_imm8, 2, 1)
    E(str_imm, 2, 1, R_N)
    tail(ENTER)
    a.label("c_dgoff")
    imm32(1, BLOCK)
    E(movs_imm, 2, 0)
    E(strb_imm, 2, 1, R_IN)
    tail(LEAVE)

    # ---- the writers (r0 core, r1 value, r2 address): counted inside an interval, by LR
    a.label("c_dgcount")                         # r3 = the caller's LR; r0-r2 free here
    imm32(0, BLOCK)
    E(ldr_imm, 1, 0, R_SIG)
    imm32(2, SIG)
    E(cmp_reg, 1, 2)
    E(b_cond, "dc_x", "ne")
    E(ldrb_imm, 1, 0, R_IN)
    E(cmp_imm, 1, 0)
    E(b_cond, "dc_x", "eq")
    imm32(2, FLASH_END)
    E(cmp_reg, 3, 2)
    E(b_cond, "dc_stock", "hs")
    imm32(2, MOD_START)
    E(cmp_reg, 3, 2)
    E(b_cond, "dc_ours", "hs")
    imm32(2, hole.LO)
    E(cmp_reg, 3, 2)
    E(b_cond, "dc_stock", "lo")
    imm32(2, hole.HI)
    E(cmp_reg, 3, 2)
    E(b_cond, "dc_ours", "lo")
    a.label("dc_stock")
    E(ldr_imm, 1, 0, R_STOCK)
    E(adds_imm8, 1, 1)
    E(str_imm, 1, 0, R_STOCK)
    E(b, "dc_x")
    a.label("dc_ours")
    E(ldr_imm, 1, 0, R_OURS)
    E(adds_imm8, 1, 1)
    E(str_imm, 1, 0, R_OURS)
    E(str_imm, 3, 0, R_LR)
    a.label("dc_x")
    E(raw, bytes.fromhex("7047"))                # bx lr

    for name, addr in (("c_dgw16", W16), ("c_dgw24", W24)):
        a.label(name)
        E(push_list, [0, 1, 2, 3], lr=True)
        E(mov_reg, 3, 14)
        E(bl, "c_dgcount")
        E(pop_list, [0, 1, 2, 3])
        E(raw, bytes.fromhex("5df804eb"))        # ldr.w lr, [sp], #4
        tail(addr)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    for addr, head in HEADS.items():
        assert bytes(img[addr - BASE:addr - BASE + 4]).hex() == head, (hex(addr), bytes(img[addr - BASE:addr - BASE + 4]).hex())
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    for addr, lab in ((ENTER, "c_dgon"), (LEAVE, "c_dgoff"), (W16, "c_dgw16"), (W24, "c_dgw24")):
        img[addr - BASE:addr - BASE + 4] = b_w(addr, labels[lab])
    return labels, code
