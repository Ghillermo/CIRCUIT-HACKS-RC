"""SC183D probe v2 (diagnostic build = SC18.3 + this): where do the reserved bytes of the session blobs live and what touches them?

Same 15 reserved bytes as probe19 (drums, Synth 1 / 2 patches, project block; see probe19 and docs/NOTAS.md) but every write puts a
GENERATION number (1..255, +1 per write) instead of a fixed marker, and the display can show either the live stores or the session
RECORD buffer (the RAM image that stock saves to / loads from, [0x2003D71C + 0x14]).  So after any action the pads and the knob LEDs say
which generation each place holds: the current one, an older one (= restored from somewhere else) or 0.

Master FX view (rows 2-3 = pads 9-24 are the probe, instead of the song pointer; the FX slot row (pads 25-32) shows the event counters):
  Shift + pad 8   : write the next generation into the 15 live bytes (generation +1)
  Shift + pad 7   : write 0 into the 15 live bytes (clear)
  Shift + pad 9-23: select that probe (its pad turns SELECT colour) -> the 8 knob LEDs show its value in binary (knob 1 = bit 0)
  Shift + pad 24  : switch the source of the display: live stores (pad 24 dim) / session record buffer (pad 24 bright)
  Pads 9-23 (not selected): ON = the byte holds the current generation, OTHER = another non-zero value, DIM = 0, off = not found.
  Pads 25-32 (events since power-up, binary, pad 25 = bit 0): pads 25-26 = "new project" count (0-3), pads 27-29 = project loads (0-7),
  pads 30-32 = project saves (0-7).  Hooks: 0x0802F5FA (new project tail), 0x0802F5B8 (end of the load), 0x0802FE5E (the bl to the save).
The current generation, the selected probe, the display source and the counters are kept in 4 extra bytes of the Master FX block (180..183).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, ldrb_w, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, h, strb_imm, strb_w, strh_imm, strh_w_imm, adds_reg, adds_imm8, adds_imm3, subs_imm8,
                   tst_reg, ands_reg, lsrs_imm, lsls_imm, eors_reg)
import probe19 as P1  # noqa: E402

CTXP, STORE_VT = P1.CTXP, P1.STORE_VT
PROBES = P1.PROBES
OBJ, OBJ_VT = 0x2003D71C, 0x08059CD0                 # session manager (stock save / load object) and its vtable
REC = {P1.CTX_SYNTH1: 0x26D14, P1.CTX_SYNTH2: 0x26E68, P1.CTX_DRUMS: 0x26FBC, P1.CTX_PROJECT: 0x26FE8}   # blob offsets in the record
B_GEN, B_SEL, B_MODE, B_CNT = 180, 181, 182, 183     # extra bytes of the Master FX block
EXTRA = 4
LED_FIRST, LED_MODE, LED_SLOTS, LED_KNOB = 8, 23, 24, 34
ON, DIM, OTHER, SEL, KNOB_ON = 0x20, 0x26, 0x19, 0x45, 0x45
MIX_VT = P1.MIX_VT
LOAD_END, LOAD_END_TXT, NEW_TAIL, NEW_TAIL_TXT, NEW_TARGET = P1.LOAD_END, P1.LOAD_END_TXT, P1.NEW_TAIL, P1.NEW_TAIL_TXT, P1.NEW_TARGET
SAVE_CALL, SAVE_CALL_TXT, SAVE_FN = 0x0802FE5E, "bl #0x802f63c", 0x0802F63C
popw = P1.popw
INV = P1.INV


def table():
    return b"".join(struct.pack("<HHI", co, bo, REC[co] + bo) for co, bo, _ in PROBES)


def arm_code(base, tab, c_gact, c_gfst, c_shift, orig_press, orig_leds, load_end_instr):
    a = Asm(base)
    zc = [0]

    def bc(target, cond):                              # conditional branch, +-2KB
        zc[0] += 1; n = f"_c{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    # ---- c_pr_ptr(r0 = ctx offset, r1 = byte offset) -> r0 = address of the byte in the live store or 0   (clobbers r1-r3)
    a.label("c_pr_ptr")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    a.emit(movw, 2, CTXP & 0xFFFF); a.emit(movt, 2, CTXP >> 16); a.emit(ldr_imm, 2, 2, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pp_none", "eq")
    a.emit(adds_reg, 2, 2, 0); a.emit(ldr_imm, 2, 2, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "pp_none", "eq")
    a.emit(ldr_imm, 3, 2, 0); a.emit(movw, 0, STORE_VT & 0xFFFF); a.emit(movt, 0, STORE_VT >> 16)
    a.emit(cmp_reg, 3, 0); a.emit(b_cond, "pp_none", "ne")
    a.emit(ldr_imm, 1, 2, 0x10); a.emit(cmp_reg, 4, 1); a.emit(b_cond, "pp_none", "hs")
    a.emit(ldr_imm, 0, 2, 0xC); a.emit(ldr_imm, 0, 0, 0); a.emit(adds_reg, 0, 0, 4)
    a.emit(pop_list, [4], pc=True)
    a.label("pp_none")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4], pc=True)

    # ---- c_pr_addr(r0 = probe, r1 = 0 live store / 1 session record) -> r0 = address or 0
    a.label("c_pr_addr")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1)
    a.emit(lsls_imm, 0, 0, 3)
    a.emit(movw, 2, tab & 0xFFFF); a.emit(movt, 2, tab >> 16); a.emit(adds_reg, 2, 2, 0)
    a.emit(cmp_imm, 5, 0); a.emit(b_cond, "pa_rec", "ne")
    a.emit(ldrh_imm, 0, 2, 0); a.emit(ldrh_imm, 1, 2, 2); a.emit(bl, "c_pr_ptr")
    a.emit(pop_list, [4, 5], pc=True)
    a.label("pa_rec")
    a.emit(movw, 3, OBJ & 0xFFFF); a.emit(movt, 3, OBJ >> 16); a.emit(ldr_imm, 0, 3, 0)
    a.emit(movw, 1, OBJ_VT & 0xFFFF); a.emit(movt, 1, OBJ_VT >> 16); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "pa_none", "ne")
    a.emit(ldr_imm, 0, 3, 0x14); a.emit(ldr_imm, 1, 2, 4); a.emit(adds_reg, 0, 0, 1)
    a.emit(lsrs_imm, 1, 0, 16)
    a.emit(movw, 3, 0x2000); a.emit(cmp_reg, 1, 3); a.emit(b_cond, "pa_none", "lo")
    a.emit(movw, 3, 0x2005); a.emit(cmp_reg, 1, 3); a.emit(b_cond, "pa_none", "hs")
    a.emit(pop_list, [4, 5], pc=True)
    a.label("pa_none")
    a.emit(movs_imm, 0, 0); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_pr_val(r0 = probe, r1 = source) -> r0 = byte, or 0xFFFFFFFF when not valid
    a.label("c_pr_val")
    a.emit(push_list, [], lr=True)
    a.emit(bl, "c_pr_addr"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pv_inv", "eq")
    a.emit(ldrb_imm, 0, 0, 0); a.emit(pop_list, [], pc=True)
    a.label("pv_inv")
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x43C0)); a.emit(pop_list, [], pc=True)       # mvns r0,r0

    # ---- c_pr_setall(r0 = value): the value into the 15 live bytes
    a.label("c_pr_setall")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 5, 0); a.emit(movs_imm, 4, 0)
    a.label("sa_l")
    a.emit(mov_reg, 0, 4); a.emit(movs_imm, 1, 0); a.emit(bl, "c_pr_addr")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sa_n", "eq"); a.emit(strb_imm, 5, 0, 0)
    a.label("sa_n")
    a.emit(adds_imm8, 4, 1); a.emit(cmp_imm, 4, len(PROBES)); a.emit(b_cond, "sa_l", "lo")
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_pr_press(view, pad, vel): Mixer view slot 0
    a.label("c_pr_press")
    a.emit(cmp_imm, 1, 6); a.emit(b_cond, "pr_orig", "lo"); a.emit(cmp_imm, 1, 23); a.emit(b_cond, "pr_orig", "hi")
    a.emit(push_list, [0, 1, 2, 4, 5], lr=True)
    a.emit(mov_reg, 4, 1)
    a.emit(bl, c_gact); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pr_back", "eq")
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pr_back", "eq")
    a.emit(bl, c_gfst); a.emit(mov_reg, 5, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pr_back", "eq")
    a.emit(cmp_imm, 4, 7); a.emit(b_cond, "pr_n7", "ne")
    a.emit(ldrb_w, 1, 5, B_GEN); a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 255); a.emit(b_cond, "pr_g", "ls"); a.emit(movs_imm, 1, 1)
    a.label("pr_g")
    a.emit(strb_w, 1, 5, B_GEN); a.emit(mov_reg, 0, 1); a.emit(bl, "c_pr_setall"); a.emit(b, "pr_done")
    a.label("pr_n7")
    a.emit(cmp_imm, 4, 6); a.emit(b_cond, "pr_n6", "ne")
    a.emit(movs_imm, 0, 0); a.emit(bl, "c_pr_setall"); a.emit(b, "pr_done")
    a.label("pr_n6")
    a.emit(cmp_imm, 4, 23); a.emit(b_cond, "pr_n23", "ne")
    a.emit(ldrb_w, 1, 5, B_MODE); a.emit(movs_imm, 2, 1); a.emit(eors_reg, 1, 2); a.emit(strb_w, 1, 5, B_MODE); a.emit(b, "pr_done")
    a.label("pr_n23")
    a.emit(cmp_imm, 4, 8); a.emit(b_cond, "pr_back", "lo")                                  # pad 7 is handled above: 8..22 select
    a.emit(mov_reg, 1, 4); a.emit(subs_imm8, 1, 8); a.emit(strb_w, 1, 5, B_SEL)
    a.label("pr_done")
    a.emit(pop_list, [0, 1, 2, 4, 5], pc=True)
    a.label("pr_back")
    a.emit(raw, popw([0, 1, 2, 4, 5], lr=True))
    a.label("pr_orig")
    a.emit(b_w, orig_press)

    # ---- c_pr_leds(view): Mixer view slot 7
    a.label("c_pr_leds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, orig_leds); a.emit(mov_reg, 4, 0)
    a.emit(bl, c_gact); a.emit(cmp_imm, 0, 0); bc("pl_out", "eq")
    a.emit(bl, c_gfst); a.emit(mov_reg, 5, 0); a.emit(cmp_imm, 0, 0); bc("pl_out", "eq")
    a.emit(ldrb_w, 6, 5, B_GEN); a.emit(ldrb_w, 7, 5, B_MODE)
    for i in range(len(PROBES)):
        a.emit(movs_imm, 0, i); a.emit(mov_reg, 1, 7); a.emit(bl, "c_pr_val")
        a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, f"pl_i{i}", "eq")                    # 0xFFFFFFFF + 1 = 0: not valid
        a.emit(ldrb_w, 2, 5, B_SEL); a.emit(cmp_imm, 2, i); a.emit(b_cond, f"pl_n{i}", "ne")
        a.emit(movs_imm, 1, SEL); a.emit(b, f"pl_s{i}")
        a.label(f"pl_n{i}")
        a.emit(movs_imm, 1, DIM); a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"pl_s{i}", "eq")
        a.emit(movs_imm, 1, ON); a.emit(cmp_reg, 0, 6); a.emit(b_cond, f"pl_s{i}", "eq")
        a.emit(movs_imm, 1, OTHER); a.emit(b, f"pl_s{i}")
        a.label(f"pl_i{i}"); a.emit(movs_imm, 1, 0)
        a.label(f"pl_s{i}"); a.emit(strh_imm, 1, 4, 2 * (LED_FIRST + i))
    a.emit(movs_imm, 1, DIM); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "pl_m", "eq"); a.emit(movs_imm, 1, ON)
    a.label("pl_m"); a.emit(strh_imm, 1, 4, 2 * LED_MODE)
    a.emit(ldrb_w, 2, 5, B_CNT)                                                         # event counters on the slot row
    for k in range(8):
        a.emit(movs_imm, 3, 1 << k); a.emit(movs_imm, 1, 0); a.emit(tst_reg, 2, 3); a.emit(b_cond, f"pl_c{k}", "eq")
        a.emit(movs_imm, 1, KNOB_ON)
        a.label(f"pl_c{k}"); a.emit(strh_imm, 1, 4, 2 * (LED_SLOTS + k))
    a.emit(ldrb_w, 0, 5, B_SEL); a.emit(mov_reg, 1, 7); a.emit(bl, "c_pr_val")           # knob LEDs: value of the selected probe
    a.emit(mov_reg, 2, 0); a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, "pl_kv", "ne"); a.emit(movs_imm, 2, 0)
    a.label("pl_kv")
    for k in range(8):
        a.emit(movs_imm, 3, 1 << k); a.emit(movs_imm, 1, 0); a.emit(tst_reg, 2, 3); a.emit(b_cond, f"pl_k{k}", "eq")
        a.emit(movs_imm, 1, KNOB_ON)
        a.label(f"pl_k{k}"); a.emit(raw, strh_w_imm(1, 4, 2 * (LED_KNOB + k)))
    a.label("pl_out")
    a.emit(mov_reg, 0, 4); a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- event counters in B_CNT: bits 0-1 new project, 2-4 loads, 5-7 saves (saturating)
    def count(prefix, bits, step, mask_shift):
        a.emit(bl, c_gfst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"{prefix}_d", "eq")
        a.emit(ldrb_w, 1, 0, B_CNT)
        if mask_shift == 0:
            a.emit(movs_imm, 2, (1 << bits) - 1); a.emit(ands_reg, 2, 1)
        else:
            a.emit(lsrs_imm, 2, 1, mask_shift); a.emit(movs_imm, 3, (1 << bits) - 1); a.emit(ands_reg, 2, 3)
        a.emit(cmp_imm, 2, (1 << bits) - 1); a.emit(b_cond, f"{prefix}_d", "eq")
        a.emit(adds_imm8, 1, step); a.emit(strb_w, 1, 0, B_CNT)
        a.label(f"{prefix}_d")

    # ---- c_pr_loadA: tail of "new project" (r0 = ctx, r1 = 0x10000, r2 = 1 for 0x08029A00)
    a.label("c_pr_loadA")
    a.emit(push_list, [0, 1, 2, 3, 4], lr=True)
    count("la", 2, 1, 0)
    a.emit(raw, popw([0, 1, 2, 3, 4], lr=True)); a.emit(b_w, NEW_TARGET)
    # ---- c_pr_loadB: end of the load function (its own pop.w follows)
    a.label("c_pr_loadB")
    count("lb", 3, 4, 2)
    a.emit(raw, load_end_instr)
    # ---- c_pr_save: replaces the bl to the stock save (r0 = session manager)
    a.label("c_pr_save")
    a.emit(push_list, [4], lr=True)
    a.emit(bl, SAVE_FN)
    count("sv", 3, 0x20, 5)
    a.emit(pop_list, [4], pc=True)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the table + code at base_addr and patch the Mixer vtable slots 0 / 7 and the three event hooks."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    assert text(LOAD_END, 4) == LOAD_END_TXT, text(LOAD_END, 4)
    assert text(NEW_TAIL, 4) == NEW_TAIL_TXT, text(NEW_TAIL, 4)
    assert text(SAVE_CALL, 4) == SAVE_CALL_TXT, text(SAVE_CALL, 4)
    sl = report["sc17"]["labels"]
    c_gact, c_gfst = int(sl["c_gact"], 16), int(sl["c_gfst"], 16)
    c_shift = int(report["sc15"]["labels"]["c_shift"], 16)
    orig_press = struct.unpack_from("<I", img, MIX_VT - BASE)[0] & ~1
    orig_leds = struct.unpack_from("<I", img, MIX_VT + 28 - BASE)[0] & ~1
    load_end = bytes(img[LOAD_END - BASE:LOAD_END - BASE + 4])
    tab = table()
    code_at = base_addr + len(tab)
    code, labels = arm_code(code_at, base_addr, c_gact, c_gfst, c_shift, orig_press, orig_leds, load_end)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + tab + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MIX_VT - BASE, labels["c_pr_press"] | 1)
    struct.pack_into("<I", img, MIX_VT + 28 - BASE, labels["c_pr_leds"] | 1)
    img[LOAD_END - BASE:LOAD_END - BASE + 4] = b_w(LOAD_END, labels["c_pr_loadB"])
    img[NEW_TAIL - BASE:NEW_TAIL - BASE + 4] = b_w(NEW_TAIL, labels["c_pr_loadA"])
    img[SAVE_CALL - BASE:SAVE_CALL - BASE + 4] = bl(SAVE_CALL, labels["c_pr_save"])
    return labels, code, dict(orig_press=orig_press, orig_leds=orig_leds, table=base_addr)
