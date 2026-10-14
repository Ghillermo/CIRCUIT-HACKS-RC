"""SC403D (diagnostic, 2026-10-13): are bytes 4..39 of the settings of every pattern free?

Every pattern of the project record has a 40-byte settings block (note tracks: pattern + 0x380; drums: pattern + 0x80) of which the stock reads
four bytes: 0 / 1 = the first / last step, 2 = the sync rate, 3 = the direction (the getters 0x0803C6D6 / 0x0803C744 / 0x0803C790).  The other
36 are zero in the RAM dump: the place for the pattern chains (repeats, next B, next C) if they travel with the pattern.
The probe: at the FIRST save of a project (the "TAIL" mark of tools/taildiag.py not there yet; this hook runs in front of it) every one of the 64
patterns gets, in bytes 4..39 of its settings, 0xC0 | its number (0..15 Synth 1 / 2, 16..31 MIDI 1 / 2, 32..63 Drum 1..4; 8 each), 0x5A and the
bytes 6..39 = their own index.  Later saves do not write them again, so what the stock does with them on load / duplicate / clear / save shows:
the Octave-down LED = green when the 64 patterns carry their own marks, red when only some do, as the stock when none does.
tools/patchtool.py patdiag PACK reads them from the card on the PC, pattern by pattern.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, h, adds_imm8, adds_reg, b, b_cond, b_w, bl, bx_lr, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, muls,  # noqa: E402
                   pop_list, push_list, raw, strb_imm, strb_reg, strh_reg, subs_imm8, ldrb_reg)
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402
import taildiag as TD  # noqa: E402

SAVE_CALL, SESSION_OBJ = TD.SAVE_CALL, TD.SESSION_OBJ
SET_LEN, FIRST = 40, 4
ID, TAG = 0xC0, 0x5A
LED_OCT, COL_OK, COL_BAD = 51, 0x17, 0x53
# (first pattern number, offset of the settings of the first pattern in the record, pattern size)
AREAS = ((0, 0x2E4 + 0x380, 0xCA8), (16, 0x1A27C + 0x380, 0xCA8), (32, 0xCD74 + 0x80, 0x6A8))
N_PAT = 64


def settings_offset(i):
    """Offset in the record of the 40 settings bytes of pattern i (0..63)."""
    n0, off, size = [a for a in AREAS if a[0] <= i][-1]
    return off + (i - n0) * size


def arm_code(base, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)

    # ---- c_pdaddr (r0 = pattern 0..63, r4 = the record) -> r0 = its settings; clobbers r1, r2
    a.label("c_pdaddr")
    E(cmp_imm, 0, 32); E(b_cond, "pa_n", "lo")
    E(subs_imm8, 0, 32); imm32(1, AREAS[2][2]); imm32(2, AREAS[2][1]); E(b, "pa_x")
    a.label("pa_n")
    imm32(1, AREAS[0][2]); imm32(2, AREAS[0][1]); E(cmp_imm, 0, 16); E(b_cond, "pa_x", "lo")
    E(subs_imm8, 0, 16); imm32(2, AREAS[1][1])
    a.label("pa_x"); E(muls, 0, 1); E(adds_reg, 0, 0, 2); E(adds_reg, 0, 0, 4); E(bx_lr)

    # ---- c_pdsave (in the place of the bl to the save): the first save of a project marks its 64 patterns; then the chain
    a.label("c_pdsave")
    E(push_list, [0, 1, 2, 3, 4, 5, 6, 7], lr=True)
    imm32(4, SESSION_OBJ); E(ldr_imm, 4, 4, 0x14)
    imm32(0, TD.TAIL); E(adds_reg, 0, 0, 4); E(ldr_imm, 0, 0, 0); imm32(1, TD.M1); E(cmp_reg, 0, 1); E(b_cond, "ps_x", "eq")
    E(movs_imm, 5, 0)
    a.label("ps_l")
    E(mov_reg, 0, 5); E(bl, "c_pdaddr")
    E(movs_imm, 1, ID); E(adds_reg, 1, 1, 5); E(strb_imm, 1, 0, FIRST); E(movs_imm, 1, TAG); E(strb_imm, 1, 0, FIRST + 1)
    E(movs_imm, 1, FIRST + 2)
    a.label("ps_b"); E(strb_reg, 1, 0, 1); E(adds_imm8, 1, 1); E(cmp_imm, 1, SET_LEN); E(b_cond, "ps_b", "lo")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, N_PAT); E(b_cond, "ps_l", "lo")
    a.label("ps_x")
    E(pop_list, [0, 1, 2, 3, 4, 5, 6, 7]); E(raw, h(0xF85D) + h(0xEB04)); E(b_w, prev["save"])          # ldr lr, [sp], #4

    # ---- c_pdledtask (the LED task calls: ctrl, frame): the chain; the Octave-down LED = how many patterns carry their own marks
    a.label("c_pdledtask")
    E(push_list, [3, 4, 5, 6, 7], lr=True)
    E(mov_reg, 7, 1); E(bl, prev["ledtask"])
    imm32(4, SESSION_OBJ); E(ldr_imm, 4, 4, 0x14)
    E(movs_imm, 5, 0); E(movs_imm, 6, 0)
    a.label("pl_l")
    E(mov_reg, 0, 5); E(bl, "c_pdaddr")
    E(ldrb_imm, 1, 0, FIRST); E(movs_imm, 2, ID); E(adds_reg, 2, 2, 5); E(cmp_reg, 1, 2); E(b_cond, "pl_n", "ne")
    E(ldrb_imm, 1, 0, FIRST + 1); E(cmp_imm, 1, TAG); E(b_cond, "pl_n", "ne")
    E(movs_imm, 2, SET_LEN - 1); E(ldrb_reg, 1, 0, 2); E(cmp_imm, 1, SET_LEN - 1); E(b_cond, "pl_n", "ne")
    E(adds_imm8, 6, 1)
    a.label("pl_n"); E(adds_imm8, 5, 1); E(cmp_imm, 5, N_PAT); E(b_cond, "pl_l", "lo")
    E(cmp_imm, 6, 0); E(b_cond, "pl_x", "eq")
    E(movs_imm, 2, COL_OK); E(cmp_imm, 6, N_PAT); E(b_cond, "pl_c", "eq"); E(movs_imm, 2, COL_BAD)
    a.label("pl_c"); E(movs_imm, 0, 2 * LED_OCT); E(strh_reg, 2, 7, 0)
    a.label("pl_x"); E(pop_list, [3, 4, 5, 6, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the bl to the save and the two LED task calls (in front of those of taildiag)."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    prev = dict(save=FD.bl_target(img, SAVE_CALL, BASE), ledtask=int(report["taildiag"]["labels"]["c_tdledtask"], 16))
    assert prev["save"] == int(report["taildiag"]["labels"]["c_tdsave"], 16)
    code, labels = arm_code(base_addr, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_pdsave"])
    for c in PK.LED_CALLS:
        assert bytes(img[c - BASE:c - BASE + 4]) == bl(c, prev["ledtask"]), hex(c)
        img[c - BASE:c - BASE + 4] = bl(c, labels["c_pdledtask"])
    return labels, code, prev
