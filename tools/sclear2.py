"""Alpha 7.04 / RC4.16 (the pending fixes of the 2026-11-14 bug hunt: «the byte of mode of patchain and the bytes of patmut in the scene clear»):
Clear + a scene pad (the stock's scene clear, 0x0802DFC6, its first bl 0x0802B2CC with r1 = r4 = the scene) left our per-scene data behind:
  * patchain: the scene's chain mode (the record's tail + P_FLAGS + s) and its repeats (+ P_REPS + s): a cleared scene still switched the chain
    mode when it started and still played its repeats;
  * patmut (when installed): the scene's bytes 34..39 (rec + 0x40 + 40 s + 34: its mutate lists, kept by their check byte): a cleared scene
    still started its old mutate lists if the stock keeps the scene's "saved" byte.
The outermost head of that bl: the mode = the default (0 with patchain.use_v3, else 0xFF), the repeats = 1, the sum rewritten (only when the
tail is ours: c_pcvalid); patmut's six bytes = 0 (the check fails: nothing restored); then the call as it was (r0-r3 and [sp] untouched)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_reg, b_cond, b_w, bl, cmp_imm, h, ldr_imm, mov_reg, movs_imm, movt, movw, muls, raw, strb_imm, strh_imm  # noqa: E402
import patchain as PC  # noqa: E402

SC_CLEAR = 0x0802DFC6
SESSION_OBJ = 0x2003D71C
PUSH, POP = h(0xE92D) + h(0x403F), h(0xE8BD) + h(0x403F)        # push.w / pop.w {r0-r5, lr}


def arm_code(base, L, prev, patmut):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_sc2")
    E(raw, PUSH); E(mov_reg, 4, 1); E(cmp_imm, 4, 16); E(b_cond, "s2_x", "hs")
    E(bl, L["c_pcst"]); E(cmp_imm, 0, 0); E(b_cond, "s2_pm", "eq"); E(mov_reg, 5, 0)
    E(bl, L["c_pcvalid"]); E(cmp_imm, 0, 0); E(b_cond, "s2_pm", "eq")
    E(adds_reg, 0, 5, 4); E(movs_imm, 1, 0 if PC.V3 else 0xFF); E(strb_imm, 1, 0, PC.P_FLAGS); E(movs_imm, 1, 1); E(strb_imm, 1, 0, PC.P_REPS)
    E(mov_reg, 0, 5); E(bl, L["c_pcsum"])
    a.label("s2_pm")
    if patmut:
        import patmut as PM
        imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "s2_x", "eq")
        E(movs_imm, 1, PM.SC_LEN); E(muls, 1, 4); E(adds_reg, 0, 0, 1); E(movs_imm, 1, PM.SC_BASE + PM.SC_OFF); E(adds_reg, 0, 0, 1)
        E(movs_imm, 1, 0)
        for k in (0, 2, 4): E(strh_imm, 1, 0, k)
    a.label("s2_x"); E(raw, POP); E(b_w, prev)
    return a.assemble()


def install(img, report, base_addr):
    """Appended at the end (dspz.add moves it into a gap; the RC appends it): the outermost head of the scene clear's first bl."""
    import ct_fw
    import fxdiag as FD
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    lab = lambda k: int(report["patchain"]["labels"][k], 16)
    L = dict(c_pcst=lab("c_pcst"), c_pcvalid=lab("c_pcvalid"), c_pcsum=lab("c_pcsum"))
    prev = FD.bl_target(img, SC_CLEAR, BASE)
    patmut = "patmut" in report
    if patmut:
        import patmut as PM
        assert (PM.SC_LEN, PM.SC_BASE + PM.SC_OFF) == (40, 0x40 + 34)
    code, labels = arm_code(base_addr, L, prev, patmut)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[SC_CLEAR - BASE:SC_CLEAR - BASE + 4] = bl_enc(SC_CLEAR, labels["c_sc2"])
    return labels, code, dict(sclear=prev)
