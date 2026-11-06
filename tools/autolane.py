"""SC52.4 (the user, 2026-11-06: «si la lista de automatizables no está llena y se mueve un knob mientras se graba, añade ese knob a la lista y
grábalo»; chosen: a free lane = one without automation in the pattern that plays): MIDI 1 / 2's own engine, Record armed and playing, a knob whose parameter is
not one of page 4's 8 lanes: the first lane with nothing in the playing pattern (its 192 bytes 0xFF; lane 0 not with the step-drummer on) takes it
(the track's row, vcf21.use_p4dest: saved with the patch) and vcf21's recording goes on into it.  No free lane: nothing recorded, as before.
The parameter must be one of the matrix's destinations (modmx's dcode).  A head of vcf21's c_vcc_rec (its first 4 bytes: push {r4-r7, lr};
mov r4, r0)."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, h, ldrb_imm, ldrb_reg, mov_reg, movs_imm, movt, movw, muls,  # noqa: E402
                   pop_list, push_list, raw, strb_reg)
import recinst as RI  # noqa: E402
import packio as PK  # noqa: E402


def arm_code(base, L, prev, nd):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    # ---- c_alrec (r0 = track, r1 = code, r2 = value): a lane for the code first when it has none and the unit records; then c_vcc_rec
    a.label("c_alrec")
    E(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    for prm in (1, 0):                                                              # Record armed, playing (the gate writes: the lane is not empty after)
        imm32(0, RI.TRANSPORT); E(movs_imm, 1, prm); E(bl, PK.PARAM_GET); E(ldrb_imm, 0, 0, 0); E(cmp_imm, 0, 0); E(b_cond, "al_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_vlane"]); E(cmp_imm, 0, 0xFF); E(b_cond, "al_x", "ne")    # it has a lane
    imm32(0, L["t_dcode"]); E(movs_imm, 1, 0)                                       # one of the destinations?
    a.label("al_d"); E(ldrb_reg, 2, 0, 1); E(cmp_reg, 2, 5); E(b_cond, "al_ok", "eq"); E(adds_imm8, 1, 1); E(cmp_imm, 1, nd); E(b_cond, "al_d", "lo")
    E(b, "al_x")
    a.label("al_ok")
    E(mov_reg, 0, 4); E(bl, L["c_sdpat"]); E(movw, 1, RI.LANES); E(adds_reg, 6, 0, 1)     # r6 = lane 0's bytes
    E(movs_imm, 7, 0)                                                               # r7 = the lane
    a.label("al_l")
    E(cmp_imm, 7, 0); E(b_cond, "al_s", "ne"); E(mov_reg, 0, 4); E(bl, L["c_sden"]); E(cmp_imm, 0, 0); E(b_cond, "al_n", "ne")   # lane 0: not with the step-drummer
    a.label("al_s"); E(movs_imm, 1, 0)
    a.label("al_b"); E(ldrb_reg, 0, 6, 1); E(cmp_imm, 0, 0xFF); E(b_cond, "al_n", "ne"); E(adds_imm8, 1, 1); E(cmp_imm, 1, RI.LANE_BYTES); E(b_cond, "al_b", "lo")
    E(mov_reg, 0, 4); E(bl, L["c_vrow"]); E(strb_reg, 5, 0, 7); E(b, "al_x")     # a free lane: the code's
    a.label("al_n"); E(movs_imm, 0, RI.LANE_BYTES); E(adds_reg, 6, 6, 0); E(adds_imm8, 7, 1); E(cmp_imm, 7, 8); E(b_cond, "al_l", "lo")
    a.label("al_x")
    E(pop_list, [0, 1, 2, 4, 5, 6, 7])
    E(raw, h(0xBC08) + h(0x469E))                                                  # pop {r3}; mov lr, r3 (the caller's)
    if prev["head"]: E(b_w, prev["head"])                                           # the head that was there (c_vcc_rec starts with a b.w)
    else: E(push_list, [4, 5, 6, 7], lr=True); E(mov_reg, 4, 0); E(b_w, prev["rec"] + 4)   # c_vcc_rec's first 4 bytes
    return a.assemble()


def install(img, report, base_addr):
    """The code at base_addr; the first 4 bytes of vcf21's c_vcc_rec -> b.w c_alrec."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vlane", "c_vrow", "c_sdpat", "c_sden", "c_vcc_rec")}
    L["t_dcode"] = lab("modmx", "t_dcode")
    nd = int(report["modmx"]["prev"]["pmax"], 16) // __import__("modmx").ZONE
    rec = L["c_vcc_rec"]
    import mpatch as MP
    first = bytes(img[rec - BASE:rec - BASE + 4])
    head = 0 if first == push_list([4, 5, 6, 7], lr=True) + mov_reg(4, 0) else MP.bw_target(img, rec, BASE)
    prev = dict(rec=rec, head=head)
    code, labels = arm_code(base_addr, L, prev, nd)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[rec - BASE:rec - BASE + 4] = b_w(rec, labels["c_alrec"])
    return labels, code, prev
