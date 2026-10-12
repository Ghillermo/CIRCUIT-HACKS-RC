"""SC21.3: the drum Note view gets its four drum squares ALSO at the start of the bottom row (ARM only).

The Note view of the drum tracks (object [container + 0xAC + 4 d], vtable 0x0805AD44, view mode 6): the pads 29-32 (indices 28-31) are the drums 1-4 -- the press / release handlers (slots 0 / 1,
0x0804ED50 / 0x0804ED68) forward `pad - 0x1B` (1..4) to the object [view + 0x10] for the pads >= 28 and ignore the others; the LED painter (0x0804ED84) writes the four colours (bright / dim by the
drum's state) into the entries 28-31 of the persistent LED buffer.  Here:
  * slots 0 / 1 (c_nvp / c_nvr): the pads 25-28 (indices 24-27) are forwarded as the pads 29-32 (index + 4), so they play, record and release the drums 1-4 exactly as those do;
  * slot 7 (c_nvl): the stock LED getter, then the entries 28-31 are copied to 24-27 on every call (the buffer is persistent: the stock paints 28-31 when a drum's state changes, the copy follows).
Nothing else of the view changes.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, ldrh_imm, adds_imm8, movs_imm, subs_reg, pop_list, push_list, strh_imm)  # noqa: E402

VT = 0x0805AD44
SLOT0, SLOT1, SLOT7 = VT, VT + 4, VT + 0x1C
STOCK_PRESS, STOCK_REL, STOCK_LEDS = 0x0804ED50, 0x0804ED68, 0x08047592
MIRROR = False                                                                    # SC23.4: the left squares mirror the right ones (pad 25 = drum 4 ... pad 28 = drum 1)


def arm_code(base):
    a = Asm(base)
    for name, stock in (("c_nvp", STOCK_PRESS), ("c_nvr", STOCK_REL)):
        a.label(name)                                                             # (view, pad, vel / ...)
        a.emit(cmp_imm, 1, 24); a.emit(b_cond, name + "_s", "lt")
        a.emit(cmp_imm, 1, 28); a.emit(b_cond, name + "_s", "ge")
        if MIRROR: a.emit(movs_imm, 2, 55); a.emit(subs_reg, 1, 2, 1)             # the pads 24..27 act as 31..28
        else: a.emit(adds_imm8, 1, 4)                                             # the pads 24..27 act as 28..31
        a.label(name + "_s"); a.emit(b_w, stock)
    a.label("c_nvl")                                                              # (view) -> the LED buffer
    a.emit(push_list, [4], lr=True)
    a.emit(bl, STOCK_LEDS)
    for k in range(4):
        a.emit(ldrh_imm, 1, 0, 2 * ((31 - k) if MIRROR else (28 + k))); a.emit(strh_imm, 1, 0, 2 * (24 + k))
    a.emit(pop_list, [4], pc=True)
    return a.assemble()


def install(img, report, base_addr, text):
    import ct_fw
    BASE = ct_fw.APP_BASE
    w = lambda addr: struct.unpack_from("<I", img, addr - BASE)[0]
    assert w(SLOT0) == STOCK_PRESS | 1 and w(SLOT1) == STOCK_REL | 1 and w(SLOT7) == STOCK_LEDS | 1, [hex(w(x)) for x in (SLOT0, SLOT1, SLOT7)]
    code, labels = arm_code(base_addr)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, SLOT0 - BASE, labels["c_nvp"] | 1)
    struct.pack_into("<I", img, SLOT1 - BASE, labels["c_nvr"] | 1)
    struct.pack_into("<I", img, SLOT7 - BASE, labels["c_nvl"] | 1)
    return labels, code
