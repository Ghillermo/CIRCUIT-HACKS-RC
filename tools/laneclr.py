"""Alpha 7.10 (the bug hunt's JR-1 leftover; the user, 2026-11-19: «Clear knob clears lane» -> «Clear, all patterns. All 8 patterns keep the
knob assignations on the whole track»): freeing a slot of the MIDI 1 / 2 own synth's page 4 (the sequenceable knobs) with Duplicate + knob
(p4dest.use_dup: its code to 0) also clears that slot's automation lane in the track's 8 patterns.  The knob assignments are the track's (one row
for every pattern); before, the freed lane kept its old values, silent (vcf21.use_freeslot), and drove the next destination given to the slot.
The non-sequenceable page (Shift + pad 4) has no lanes: freeing one of its slots only frees it, as before.

  * p4dest's `movs r1, #0; strb r1, [r0, r5]` (the slot freed, r0 = the row, r5 = the knob, r6 = the track 0 / 1) -> bl c_lcfree, which writes
    the 0 and, on page 4, the lane's 192 bytes (32 steps x 6) to 0xFF in the 8 patterns ([c_sdrec(t) + 0x48] + 0xCA8 p + 0x3A8 + 192 k), then
    tells the track's pattern editor store (0x08035456 + commit, as playmode's Nudge does) so the views follow.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, adds_imm8, adds_reg, b_cond, bl, cmp_imm, h, ldr_imm, mov_reg, movs_imm, movt, movw, muls, pop_list, push_list, raw, strb_imm, subs_imm8  # noqa: E402
import vcf21 as V  # noqa: E402

PAT_SZ, LANES, LANE_SZ, NPAT = 0xCA8, 0x3A8, 192, 8
EDITOR0, EDITOR_SZ, STORE_W, COMMIT = 0x20039E50, 0x3A0, 0x08035456, 0x080353C0
SITE = bytes.fromhex("00214155")                   # p4dest: movs r1, #0; strb r1, [r0, r5]


def strb_reg(rt, rn, rm): return h(0x5400 | rm << 6 | rn << 3 | rt)


def arm_code(base, L):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_lcfree")                                                    # r0 = the row, r5 = the knob, r6 = the track; keeps r4-r7
    E(push_list, [4, 7], lr=True)
    E(movs_imm, 1, 0); E(raw, strb_reg(1, 0, 5))                           # the slot freed (as before)
    E(mov_reg, 0, 6); E(bl, L["c_vpage"]); E(cmp_imm, 0, V.NS_PAGE); E(b_cond, "lc_x", "eq")    # the non-sequenceable page: no lane
    E(mov_reg, 0, 6); E(bl, L["c_sdrec"]); E(ldr_imm, 4, 0, 0x48)          # r4 = the track's pattern 0
    E(movw, 1, LANES); E(adds_reg, 4, 4, 1); E(movs_imm, 1, LANE_SZ); E(muls, 1, 5); E(adds_reg, 4, 4, 1)
    E(movs_imm, 7, NPAT); E(movs_imm, 3, 0xFF)
    a.label("lc_p"); E(mov_reg, 0, 4); E(movs_imm, 2, LANE_SZ)
    a.label("lc_b"); E(strb_imm, 3, 0, 0); E(adds_imm8, 0, 1); E(subs_imm8, 2, 1); E(b_cond, "lc_b", "ne")
    E(movw, 1, PAT_SZ); E(adds_reg, 4, 4, 1); E(subs_imm8, 7, 1); E(b_cond, "lc_p", "ne")
    E(movw, 0, EDITOR_SZ); E(mov_reg, 1, 6); E(adds_imm8, 1, 2); E(muls, 0, 1); imm32(1, EDITOR0); E(adds_reg, 0, 0, 1)
    E(ldr_imm, 4, 0, 0x18)                                                 # the editor's pattern store: told
    E(mov_reg, 0, 4); E(bl, STORE_W); E(mov_reg, 0, 4); E(bl, COMMIT)
    a.label("lc_x"); E(pop_list, [4, 7], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    lab = lambda m, k: int(report[m]["labels"][k], 16)
    L = {k: lab("vcf20", k) for k in ("c_vpage", "c_sdrec")}
    p4 = report["p4dest"]; lo = int(p4["arm_start"], 16); kn = lab("p4dest", "kn_n")
    seg = bytes(img[lo - BASE:kn - BASE]); i = seg.rfind(SITE)
    assert i >= 0 and seg.count(SITE) == 1, "p4dest: the slot freed (movs r1, #0; strb r1, [r0, r5])"
    site = lo + i
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    img[site - BASE:site - BASE + 4] = bl(site, labels["c_lcfree"])
    if p4.get("hole"):
        import hole
        hole.rehash(img, report, site)
    return labels, code, dict(site=site)
