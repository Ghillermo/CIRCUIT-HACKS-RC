"""SC50.3 / Beta 5.6 (flash for jumpoct): SC09's table of the drums' semitones (128 words, one reader: the conversion 0x0802878C) from one octave: 12 halfwords, a shift by
the octave; one unit from the old table at most below the centre (its own rounding: 1 cent at the very bottom), under 0.1 cents from Pitch 40 up.  What it frees takes a module: centab.add(img, report, name, mod, "semitab")."""
from __future__ import annotations
import math
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, ands_reg, b_cond, b_w, h, ldrh_reg, lsls_imm, lsrs_imm, movs_imm, movt, movw, raw, subs_imm8  # noqa: E402
from build_sc14 import mls, udiv  # noqa: E402
import build_sc09 as S9  # noqa: E402

BASE = 0x08010000
OCT = [round(32768 * 2 ** (b / 12)) for b in range(12)]


def word(v):
    a, b = (v + 8) // 12, (v + 8) % 12
    return OCT[b] << (a - 5) if a >= 5 else (OCT[b] + (1 << (4 - a))) >> (5 - a)


def shrink(img, report):
    tab = int(report["sc09"]["table"], 16)
    old = S9.table()
    assert list(struct.unpack_from("<128I", img, tab - BASE)) == old and all(abs(word(v) - old[v]) <= 1 for v in range(64))
    assert max(abs(1200 * math.log2(word(v) / old[v])) for v in range(40, 128)) < 0.1
    a = Asm(tab)
    E = a.emit
    E(raw, struct.pack("<12H", *OCT))
    # ---- c_stw(r0 = 0..127) -> r0 = 0x10000 x 2 ^ ((r0 - 64) / 12); clobbers r1, r2
    a.label("c_stw")
    E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(adds_imm8, 0, 8); E(movs_imm, 1, 12); E(raw, udiv(2, 0, 1)); E(raw, mls(0, 2, 1, 0)); E(lsls_imm, 0, 0, 1)
    E(movw, 1, tab & 0xFFFF); E(movt, 1, tab >> 16); E(ldrh_reg, 0, 1, 0); E(subs_imm8, 2, 5); E(b_cond, "st_l", "pl")
    E(raw, h(0x4252)); E(movs_imm, 1, 1); E(raw, h(0x4091)); E(lsrs_imm, 1, 1, 1); E(raw, h(0x1840)); E(raw, h(0x40D0)); E(raw, h(0x4770))   # rsbs r2, r2, #0; r1 = half of 1 << r2; adds r0, r0, r1; lsrs r0, r2; bx lr
    a.label("st_l"); E(raw, h(0x4090)); E(raw, h(0x4770))                    # lsls r0, r2; bx lr
    code, labels = a.assemble()
    img[tab - BASE:tab - BASE + len(code)] = code
    low = (tab + len(code) + 3) & ~3
    img[low - BASE:tab + 512 - BASE] = bytes([0xFF]) * (tab + 512 - low)
    img[S9.CONV - BASE:S9.CONV - BASE + 4] = b_w(S9.CONV, labels["c_stw"])
    report["semitab"] = dict(c_stw=hex(labels["c_stw"]), next=hex(low), end=hex(tab + 512))
