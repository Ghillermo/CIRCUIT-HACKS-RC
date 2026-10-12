"""SC182D probe (diagnostic build = SC18.2 + this): do the reserved bytes of the session blobs survive Save -> power off -> Load?

Facts found in the stock code (see docs/NOTAS.md, "cómo guardar nuestros valores en el proyecto"):
  session object ctx = [0x200069B4] (0x20010038); the five blob stores are at ctx + 0x344 (Synth 1, 340 B), 0x348 (Synth 2, 340 B),
  0x34C (drums, 44 B), 0x350 (project, 60 B), 0x354 (master, 21 B; saved with the global settings, not the project); each store object
  has the vtable 0x0805BBAC, its data pointer is [[obj + 0xC]] and its size [obj + 0x10].
  Save = 0x0802F63C(session manager) copies whole blobs into the session buffer, load = 0x0802EEFE(manager, flag) copies them back
  (slot 3 of the store vtable), "new project" = 0x0802F5BC.  No descriptor covers the reserved bytes probed below.

Probe (Master FX view, rows 2-3 = pads 9-24 show the probes instead of the song pointer):
  Shift + pad 8 (the clear pad): writes the 15 markers into the reserved bytes, or clears them if the first one is already there.
  Pad colours: marker present = ON, byte is 0 = DIM, any other value = OTHER (something rewrote it), store not found = off.
    pads  9-12  drums, first reserved byte of each drum (offset 7 / 18 / 29 / 40)       markers 0xA1..0xA4
    pads 13-16  drums, last reserved byte of each drum (offset 10 / 21 / 32 / 43)        markers 0xB1..0xB4
    pads 17-18  Synth 1 offsets 18 and 115 (0xC1, 0xC2)    pads 19-20  Synth 2 offsets 18 and 115 (0xC3, 0xC4)
    pads 21-23  project offsets 11, 15, 30 (0xD1, 0xD2, 0xD3)
    pad 24      lit once any load / new-project hook has fired since power-up
  Knob LEDs 1-4 = binary count of "new project" (0x0802F5BC) events, knob LEDs 5-8 = count of project loads (0x0802EEFE) since power-up
  (count kept in the Master FX block byte 179, low / high nibble).
Hooks: Mixer view vtable slots 0 / 7 (chained to the current handlers), 0x0802F5B8 (pop.w at the end of the load) and 0x0802F5FA
(tail b.w of the new-project function).  Only the 15 reserved bytes are ever written, and only after checking the store vtable and size.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, h, strb_imm, strb_w, strh_imm, strh_w_imm, adds_reg, adds_imm8, adds_imm3, tst_reg,
                   ands_reg, lsrs_imm)

CTXP = 0x200069B4                         # [CTXP] = session object ctx
STORE_VT = 0x0805BBAC
CTX_SYNTH1, CTX_SYNTH2, CTX_DRUMS, CTX_PROJECT = 0x344, 0x348, 0x34C, 0x350
PROBES = ([(CTX_DRUMS, 7 + 11 * d, 0xA1 + d) for d in range(4)] + [(CTX_DRUMS, 10 + 11 * d, 0xB1 + d) for d in range(4)]
          + [(CTX_SYNTH1, 18, 0xC1), (CTX_SYNTH1, 115, 0xC2), (CTX_SYNTH2, 18, 0xC3), (CTX_SYNTH2, 115, 0xC4)]
          + [(CTX_PROJECT, 11, 0xD1), (CTX_PROJECT, 15, 0xD2), (CTX_PROJECT, 30, 0xD3)])
LED_FIRST = 8                             # LED entry of the first probe (pad 9)
LED_HOOK = 23                             # pad 24
LED_KNOB = 34                             # knob LEDs 34..41
ON, DIM, OTHER = 0x20, 0x26, 0x19         # LED codes: marker present / zero / something else
KNOB_ON = 0x45
CNT = 179                                 # Master FX block: load counters (low nibble new project, high nibble load)
MIX_VT = 0x0805A668
LOAD_END, LOAD_END_TXT = 0x0802F5B8, "pop.w {r0, r4, r5, r6, r7, r8, sb, sl, fp, pc}"
NEW_TAIL, NEW_TAIL_TXT = 0x0802F5FA, "b.w #0x8029a00"
NEW_TARGET = 0x08029A00


def popw(regs, lr=False):
    return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def arm_code(base, c_gact, c_gfst, c_shift, orig_press, orig_leds, load_end_instr):
    a = Asm(base)
    zc = [0]

    def bc(target, cond):                              # conditional branch, +-2KB
        zc[0] += 1; n = f"_c{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)
    # ---- c_pr_ptr(r0 = ctx offset, r1 = byte offset) -> r0 = address of the byte or 0   (clobbers r1-r3)
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

    # ---- c_pr_get(r0 = ctx offset, r1 = byte offset) -> r0 = byte, or 0xFFFFFFFF when the store is not valid
    a.label("c_pr_get")
    a.emit(push_list, [], lr=True)
    a.emit(bl, "c_pr_ptr")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pg_inv", "eq")
    a.emit(ldrb_imm, 0, 0, 0); a.emit(pop_list, [], pc=True)
    a.label("pg_inv")
    a.emit(movs_imm, 0, 0); a.emit(raw, h(0x43C0)); a.emit(pop_list, [], pc=True)       # mvns r0,r0

    # ---- c_pr_toggle: write the markers (clear them when the first one is already there)
    a.label("c_pr_toggle")
    a.emit(push_list, [4, 5], lr=True)
    co, bo, mk = PROBES[0]
    a.emit(movw, 0, co); a.emit(movs_imm, 1, bo); a.emit(bl, "c_pr_get")
    a.emit(movs_imm, 5, 1); a.emit(cmp_imm, 0, mk); a.emit(b_cond, "pt_go", "ne"); a.emit(movs_imm, 5, 0)
    a.label("pt_go")
    for i, (co, bo, mk) in enumerate(PROBES):
        a.emit(movw, 0, co); a.emit(movs_imm, 1, bo); a.emit(bl, "c_pr_ptr")
        a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"pt_s{i}", "eq")
        a.emit(movs_imm, 2, mk); a.emit(cmp_imm, 5, 0); a.emit(b_cond, f"pt_w{i}", "ne"); a.emit(movs_imm, 2, 0)
        a.label(f"pt_w{i}"); a.emit(strb_imm, 2, 0, 0)
        a.label(f"pt_s{i}")
    a.emit(pop_list, [4, 5], pc=True)

    # ---- c_pr_press(view, pad, vel): Mixer view slot 0.  Shift + pad 8 in the Master FX view = toggle the markers, else the previous handler
    a.label("c_pr_press")
    a.emit(cmp_imm, 1, 7); a.emit(b_cond, "pr_orig", "ne")
    a.emit(push_list, [0, 1, 2, 4], lr=True)
    a.emit(bl, c_gact); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pr_back", "eq")
    a.emit(bl, c_shift); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pr_back", "eq")
    a.emit(bl, "c_pr_toggle")
    a.emit(pop_list, [0, 1, 2, 4], pc=True)
    a.label("pr_back")
    a.emit(raw, popw([0, 1, 2, 4], lr=True))
    a.label("pr_orig")
    a.emit(b_w, orig_press)

    # ---- c_pr_leds(view): Mixer view slot 7: previous LEDs, then in the Master FX view the probes and the counters
    a.label("c_pr_leds")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(bl, orig_leds); a.emit(mov_reg, 4, 0)
    a.emit(bl, c_gact); a.emit(cmp_imm, 0, 0); bc("pl_out", "eq")
    for i, (co, bo, mk) in enumerate(PROBES):
        a.emit(movw, 0, co); a.emit(movs_imm, 1, bo); a.emit(bl, "c_pr_get")
        a.emit(adds_imm3, 1, 0, 1); a.emit(b_cond, f"pl_i{i}", "eq")                 # 0xFFFFFFFF + 1 = 0: store not valid
        a.emit(movs_imm, 1, ON); a.emit(cmp_imm, 0, mk); a.emit(b_cond, f"pl_s{i}", "eq")
        a.emit(movs_imm, 1, DIM); a.emit(cmp_imm, 0, 0); a.emit(b_cond, f"pl_s{i}", "eq")
        a.emit(movs_imm, 1, OTHER); a.emit(b, f"pl_s{i}")
        a.label(f"pl_i{i}"); a.emit(movs_imm, 1, 0)
        a.label(f"pl_s{i}"); a.emit(strh_imm, 1, 4, 2 * (LED_FIRST + i))
    a.emit(bl, c_gfst); a.emit(cmp_imm, 0, 0); bc("pl_out", "eq")
    a.emit(ldrb_w, 5, 0, CNT)
    a.emit(movs_imm, 1, DIM); a.emit(cmp_imm, 5, 0); a.emit(b_cond, "pl_h", "eq"); a.emit(movs_imm, 1, ON)
    a.label("pl_h"); a.emit(strh_imm, 1, 4, 2 * LED_HOOK)
    for k in range(8):
        a.emit(movs_imm, 2, 1 << k); a.emit(movs_imm, 1, 0); a.emit(tst_reg, 5, 2); a.emit(b_cond, f"pl_k{k}", "eq")
        a.emit(movs_imm, 1, KNOB_ON)
        a.label(f"pl_k{k}"); a.emit(raw, strh_w_imm(1, 4, 2 * (LED_KNOB + k)))
    a.label("pl_out")
    a.emit(mov_reg, 0, 4); a.emit(pop_list, [4, 5], pc=True)

    # ---- c_pr_loadA: tail of the "new project" function (r0 = ctx, r1 = 0x10000, r2 = 1 for 0x08029A00): count in the low nibble
    a.label("c_pr_loadA")
    a.emit(push_list, [0, 1, 2, 3, 4], lr=True)
    a.emit(bl, c_gfst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "la_done", "eq")
    a.emit(ldrb_w, 1, 0, CNT); a.emit(movs_imm, 2, 0xF); a.emit(ands_reg, 2, 1)
    a.emit(cmp_imm, 2, 15); a.emit(b_cond, "la_done", "eq")
    a.emit(adds_imm8, 1, 1); a.emit(strb_w, 1, 0, CNT)
    a.label("la_done")
    a.emit(raw, popw([0, 1, 2, 3, 4], lr=True))
    a.emit(b_w, NEW_TARGET)

    # ---- c_pr_loadB: end of the load function (registers are restored by its own pop.w right after): count in the high nibble
    a.label("c_pr_loadB")
    a.emit(bl, c_gfst); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "lb_done", "eq")
    a.emit(ldrb_w, 1, 0, CNT); a.emit(lsrs_imm, 2, 1, 4); a.emit(cmp_imm, 2, 15); a.emit(b_cond, "lb_done", "eq")
    a.emit(adds_imm8, 1, 0x10); a.emit(strb_w, 1, 0, CNT)
    a.label("lb_done")
    a.emit(raw, load_end_instr)
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and patch the Mixer vtable slots 0 / 7 and the two load hooks."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    assert text(LOAD_END, 4) == LOAD_END_TXT, text(LOAD_END, 4)
    assert text(NEW_TAIL, 4) == NEW_TAIL_TXT, text(NEW_TAIL, 4)
    sl = report["sc17"]["labels"]
    c_gact, c_gfst = int(sl["c_gact"], 16), int(sl["c_gfst"], 16)
    c_shift = int(report["sc15"]["labels"]["c_shift"], 16)
    orig_press = struct.unpack_from("<I", img, MIX_VT - BASE)[0] & ~1
    orig_leds = struct.unpack_from("<I", img, MIX_VT + 28 - BASE)[0] & ~1
    load_end = bytes(img[LOAD_END - BASE:LOAD_END - BASE + 4])
    code, labels = arm_code(base_addr, c_gact, c_gfst, c_shift, orig_press, orig_leds, load_end)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, MIX_VT - BASE, labels["c_pr_press"] | 1)
    struct.pack_into("<I", img, MIX_VT + 28 - BASE, labels["c_pr_leds"] | 1)
    img[LOAD_END - BASE:LOAD_END - BASE + 4] = b_w(LOAD_END, labels["c_pr_loadB"])
    img[NEW_TAIL - BASE:NEW_TAIL - BASE + 4] = b_w(NEW_TAIL, labels["c_pr_loadA"])
    return labels, code, dict(orig_press=orig_press, orig_leds=orig_leds)
