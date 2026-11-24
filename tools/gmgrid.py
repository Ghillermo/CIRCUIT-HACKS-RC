"""Alpha 7.48 (the user, 2026-11-24: «A»): the global macro view's page-2 grid (gmview.use_page2col, GM + 56..59: a byte per row, bit = knob)
saved with the project.  Rows 1-3 in bytes 4..6 of the settings of MIDI 1's pattern 8, row 4 in byte 6 of MIDI 2's pattern 8 (the old
per-pattern chain rules' bytes, unused since the group chains: 0 in all 210 sessions scanned (173 of the card copy, 37 others); Clear keeps
them (patchain.use_keep46); gmview's block uses MIDI 2's bytes 4 / 5 and 8..39, the play order byte 7 is left alone).  No signature (no room):
a project from an old beta with chain rules on those patterns opens with some grid pads lit; a pattern duplicated onto MIDI 1's pattern 8 brings
its bytes 4..6 (zeros).
  * c_ggsave: a head of the save call (before gmview's): the grid into the record when gmview's state is signed.
  * c_ggload: a head of the load's re-send (before gmview's): gmview's state set up (c_gmst), the grid from the record (a load, a new project:
    its bytes, 0 there = empty).
Code in dspz's fourth gap (factcut's), after m2lanes."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movt, movw, orrs_reg, raw, str_imm, strb_imm  # noqa: E402
import fxdiag as FD  # noqa: E402
import gmview as G  # noqa: E402
import persist19 as P19  # noqa: E402
import projsyn as PS  # noqa: E402

OFF1 = PS.AREA + PS.PSIZE * 7 + PS.SET + 4            # MIDI 1's pattern 8, settings + 4..6: rows 1-3
OFF2 = PS.AREA + PS.PSIZE * (8 + 7) + PS.SET + 6      # MIDI 2's pattern 8, settings + 6: row 4
SIG4 = int.from_bytes(b"GMV4", "little")


def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(r, v): E(movw, r, v & 0xFFFF); E(movt, r, (v >> 16) & 0xFFFF)

    def rec_rows():                                    # r0 = the session record, flags: 0 = none
        imm32(0, PS.SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0)

    # ---- c_ggsave (the save call's head)
    a.label("c_ggsave")
    E(raw, pushw([0, 1, 2, 3, 4], lr=True))
    rec_rows(); E(b_cond, "sv_x", "eq")
    imm32(4, G.GM); E(ldr_imm, 1, 4, 0); imm32(2, SIG4); E(cmp_reg, 1, 2); E(b_cond, "sv_x", "ne")
    E(ldr_imm, 1, 4, G.O_MX)                                                           # r1 = the grid (rows 1-4 = bytes 0-3)
    imm32(2, OFF1); E(raw, h(0x1882))                                                  # adds r2, r0, r2
    E(strb_imm, 1, 2, 0); E(lsrs_imm, 3, 1, 8); E(strb_imm, 3, 2, 1); E(lsrs_imm, 3, 1, 16); E(strb_imm, 3, 2, 2)
    imm32(2, OFF2); E(raw, h(0x1882)); E(lsrs_imm, 3, 1, 24); E(strb_imm, 3, 2, 0)
    a.label("sv_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["save"])

    # ---- c_ggload (the load's re-send head)
    a.label("c_ggload")
    E(raw, pushw([0, 1, 2, 3, 4], lr=True))
    E(bl, L["c_gmst"]); E(mov_reg, 4, 0)
    E(raw, h(0x2100)); E(str_imm, 1, 4, G.O_MX)                                         # movs r1, #0: the grid empty
    rec_rows(); E(b_cond, "ld_x", "eq")
    imm32(2, OFF1); E(raw, h(0x1882))
    E(ldrb_imm, 1, 2, 0); E(ldrb_imm, 3, 2, 1); E(lsls_imm, 3, 3, 8); E(orrs_reg, 1, 3); E(ldrb_imm, 3, 2, 2); E(lsls_imm, 3, 3, 16); E(orrs_reg, 1, 3)
    imm32(2, OFF2); E(raw, h(0x1882)); E(ldrb_imm, 3, 2, 0); E(lsls_imm, 3, 3, 24); E(orrs_reg, 1, 3)
    E(str_imm, 1, 4, G.O_MX)
    a.label("ld_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(b_w, prev["resend"])
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into the gap): the outermost heads of the save call and of the load's re-send."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    gl = {k: int(v, 16) for k, v in report["gmview"]["labels"].items()}
    assert "kg_l" in gl, "gmview's page-2 grid (use_page2col) first"
    L = dict(c_gmst=gl["c_gmst"])
    prev = dict(save=FD.bl_target(img, P19.SAVE_CALL, BASE), resend=FD.bl_target(img, G.RESEND_CALL, BASE))
    code, labels = arm_code(base_addr, L, prev)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    img[P19.SAVE_CALL - BASE:P19.SAVE_CALL - BASE + 4] = bl(P19.SAVE_CALL, labels["c_ggsave"])
    img[G.RESEND_CALL - BASE:G.RESEND_CALL - BASE + 4] = bl(G.RESEND_CALL, labels["c_ggload"])
    return labels, code, prev
