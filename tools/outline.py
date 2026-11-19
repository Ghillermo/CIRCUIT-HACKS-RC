"""Alpha 7.07 (the user, 2026-11-18: «Make more flash room»): call idioms of our code shared by one helper each (thumb.OUTLINE, with COMPACT).

Measured on Alpha 7.06's listings: about 280 parameter reads `movs r1, #k; bl 0x0803542C (PARAM_GET); [ldrb r0, [r0]]` (6-8 B) and about 280
calls of our small getters followed by `cmp r0, #0` (6 B).  Each becomes a 4-byte `bl` to a helper:
  * PARAM_GET with a prefix only: `movs r1, #k; b.w PARAM_GET` (a tail call: it returns to the caller; no stack);
  * with a suffix: `push {lr}; [movs r1, #k]; bl T; [ldrb r0, [r0]]; [cmp r0, #0]; pop {pc}` (4 B more stack while T runs; pop {pc} keeps the
    flags; LR after the call is the caller's return address, as with the bl T it replaces);
  * the getters (GETTERS: shallow reads of state, no stock chain below them): only the `cmp r0, #0` suffix.
While the build runs, the folded calls go to placeholders in the bootloader's range (thumb.OUT_BASE + 4 i: never a real target); install()
(the last module of the build: dspz.add puts it in a gap or at the end) writes the helpers and points every bl at a placeholder to its helper."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thumb  # noqa: E402
from thumb import Asm, b_w, bl, cmp_imm, ldrb_imm, movs_imm, pop_list, push_list  # noqa: E402

PARAM_GET = 0x0803542C
PG_KEYS = {(0, True, False), (0, True, True), (0, False, False), (0, False, True), (1, True, False), (1, False, False), (2, False, False),
           (2, True, False), (3, False, False), (8, True, False), (None, True, False), (None, True, True)}
GETTERS = ("c_shift", "c_von", "c_gst", "c_gfst", "c_edact", "c_gact", "c_vdbit", "c_mh")
KEEP = {"c_dppad": 0x100}                             # chromfix finds `movs r1, #1; bl PARAM_GET; ldrb r0, [r0]; pop {r1}` there
ADDR = {}                                              # getter name -> its latest assembled address (thumb.OUT_NAMES feeds it)


def accept(key):
    T, k, ld, cz = key
    if T == PARAM_GET:
        return (k, ld, cz) in PG_KEYS
    return k is None and cz and not ld and T in ADDR.values()


def use():
    """Before anything is assembled (the builder's first lines)."""
    thumb.OUTLINE = accept
    thumb.OUT_NAMES = ADDR
    thumb.OUT_KEEP = KEEP
    for n in GETTERS: ADDR.setdefault(n, None)


def helper(a, key):
    T, k, ld, cz = key
    E = a.emit
    if not ld and not cz:
        E(movs_imm, 1, k); E(b_w, T); return
    E(push_list, [], lr=True)
    if k is not None: E(movs_imm, 1, k)
    E(bl, T)
    if ld: E(ldrb_imm, 0, 0, 0)
    if cz: E(cmp_imm, 0, 0)
    E(pop_list, [], pc=True)


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    keys = sorted(thumb.OUT_REG, key=lambda k_: thumb.OUT_REG[k_])
    saved, thumb.OUTLINE = thumb.OUTLINE, None                 # the helpers themselves: plain
    try:
        a = Asm(base_addr)
        for i, key in enumerate(keys):
            a.label(f"o_{i}"); helper(a, key)
        code, labels = a.assemble()
    finally:
        thumb.OUTLINE = saved
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    ph = {thumb.OUT_BASE + 4 * thumb.OUT_REG[k_]: labels[f"o_{i}"] for i, k_ in enumerate(keys)}
    n = {}
    for o in range(0, len(img) - 4, 2):
        h1, h2 = struct.unpack_from("<HH", img, o)
        if h1 & 0xF800 != 0xF000 or h2 & 0xD000 != 0xD000: continue
        off = ((h1 & 0x7FF) << 12 | (h2 & 0x7FF) << 1)
        s = (h1 >> 10) & 1; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1
        i1, i2 = 1 - (j1 ^ s), 1 - (j2 ^ s)
        off |= s << 24 | i1 << 23 | i2 << 22
        if s: off -= 1 << 25
        t = BASE + o + 4 + off
        if t in ph:
            img[o:o + 4] = bl(BASE + o, ph[t]); n[t] = n.get(t, 0) + 1
    prev = {f"sites_{i}": n.get(thumb.OUT_BASE + 4 * thumb.OUT_REG[k_], 0) for i, k_ in enumerate(keys)}
    prev["helpers"] = len(keys); prev["sites"] = sum(n.values())
    return labels, code, prev
