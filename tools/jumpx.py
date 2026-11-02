"""SC50.2 / Beta 5.5 (the user, 2026-11-01: «con el transporte parado debería poder oírse lo que se está disparando»): with the transport stopped, a pad of a pointing track
sounds the target's step: c_jsa, through each player's note interface [player + 0x4C] (slot 0 note-on: interface, note, velocity, 0; slot 1 note-off: interface, note, 0), which does
not record.  A note track: the units of the step, until the pad is let go.  A drum: its hit, at the step's velocity, on its selected sample (a sample flip is not heard).
In the bytes centab frees: jumpseq lives at the image's end.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, adds_reg, b, b_cond, bl, cmp_imm, h, ldr_imm, ldrb_imm, ldrb_reg, lsls_imm, lsrs_reg, mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw  # noqa: E402
import drumarp as D  # noqa: E402

PLAYER0, PLAYER_SZ = 0x20040200, 0x184
DRUM_SZ, DPAT_SZ = 0x90, 0x6A8


def ldrbw(rt, rn, off): return h(0xF890 | rn) + h(rt << 12 | off)


def arm_code(base, L):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_jsa(r0 = target 0..7, r1 = step, r2 = 1 on / 0 off)
    a.label("c_jsa")
    E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 5, 1); E(mov_reg, 6, 2); imm32(4, PLAYER0)
    E(cmp_imm, 0, 4); E(b_cond, "ja_d", "hs")
    E(movw, 1, PLAYER_SZ); E(muls, 1, 0); E(adds_reg, 4, 4, 1)
    E(adds_imm8, 0, 2); E(movs_imm, 1, 3); E(raw, h(0x4008)); E(bl, L["c_sdpat"])        # ands r0, r1: the index of c_sdpat
    E(movs_imm, 1, 28); E(muls, 5, 1); E(adds_reg, 5, 5, 0); E(movs_imm, 7, 0)
    a.label("ja_l")
    E(ldrb_imm, 0, 5, 0); E(lsrs_reg, 0, 7); E(lsls_imm, 0, 0, 31); E(b_cond, "ja_n", "pl")
    E(lsls_imm, 3, 7, 2); E(adds_reg, 3, 3, 5); E(ldrb_imm, 1, 3, 4); E(ldrb_imm, 2, 3, 7); E(bl, "ja_c")
    a.label("ja_n"); E(adds_imm8, 7, 1); E(cmp_imm, 7, 6); E(b_cond, "ja_l", "lo")
    a.label("ja_x"); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("ja_d")
    E(raw, h(0x3804)); E(mov_reg, 7, 0); E(bl, L["c_dapat"]); E(movs_imm, 1, DRUM_SZ); E(muls, 1, 7); E(movw, 2, D.DP0 - PLAYER0); E(adds_reg, 4, 4, 2); E(adds_reg, 4, 4, 1)       # subs r0, #4
    E(movw, 1, DPAT_SZ); E(muls, 0, 1); E(ldr_imm, 1, 4, 0x48); E(adds_reg, 0, 0, 1)
    E(ldrb_reg, 2, 0, 5); E(cmp_imm, 2, 0); E(b_cond, "ja_x", "eq"); E(raw, ldrbw(1, 4, 0x58)); E(bl, "ja_c"); E(b, "ja_x")

    # ---- r1 = note, r2 = velocity, r4 = the player, r6 = on
    a.label("ja_c")
    E(ldr_imm, 0, 4, 0x4C); E(ldr_imm, 3, 0, 0); E(cmp_imm, 6, 0); E(b_cond, "jc_1", "ne"); E(adds_imm8, 3, 4); E(movs_imm, 2, 0)
    a.label("jc_1"); E(ldr_imm, 3, 3, 0); E(raw, h(0x469C)); E(movs_imm, 3, 0); E(raw, h(0x4760))      # mov ip, r3; bx ip
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    L = dict(c_sdpat=int(report["vcf20"]["labels"]["c_sdpat"], 16), c_dapat=int(report["drumarp"]["labels"]["c_dapat"], 16))
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    return labels, code, {}
