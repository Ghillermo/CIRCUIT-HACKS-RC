"""SC43.7 (the user, 2026-10-17: «en preset view de midi 1: shift+29: gate retrigger (reinicia el trigger con cada nueva nota, ON por defecto)»):
the own engine of MIDI 1 / 2 retriggers its envelope on every new note (as before) or, with the retrigger off, plays legato: a note played while
others are held changes the pitch (and the velocity) without a new gate / trigger.

The engine (vcf21): the note wrapper c_vnon (the transmitter's note-on, 0x08059FC4: obj, track, note, velocity; tracks 2 / 3) counts the held
notes in RT_CNT bits 0-3 and flags NOTE, VEL, GATE and TRIG (RT_AUX 0x1E); c_vsend sends them to the DSP (GATE / TRIG restart the envelopes; the
granular voice starts its grains on them).

Ours:
  * the note-on entry -> c_rtnon: the chain first; then, with the retrigger off for that track and two or more notes held, GATE and TRIG are no
    longer flagged (the gate is open already);
  * the Preset view of MIDI 1 / 2 (the template view, 0x0805AE5C): Shift + pad 29 (with the engine on) toggles it (slot 0); with Shift its LED
    shows it: green = retrigger on, yellow = off (legato) (slot 7);
  * the state: the record's tail + 159 = 0xA0 | bit t (t = 0 MIDI 1, 1 MIDI 2: retrigger off), saved with the project; any other value = both on.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, adds_reg, b_cond, b_w, bl, cmp_imm, eors_reg, h, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, orrs_reg, pop_list, push_list, raw, strb_imm, strh_imm, subs_imm8, ands_reg, bics_reg)
import vcf21 as V  # noqa: E402

TMPL_VT, NOTE_ON = 0x0805AE5C, 0x08059FC4
PAD_RT = 28                                                       # pad 29 (index 28)
SESSION_OBJ, TAIL, O_RT, TAG = 0x2003D71C, 0x27024, 159, 0xA0
RT0 = V.TAIL + V.O_RT                                             # the RT block of MIDI 1 (MIDI 2 = + 8)
COL_ON, COL_OFF = 0x17, 0x2D                                      # with Shift: green = retrigger on, yellow = off


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    RET = h(0x4770)

    # ---- c_rtb() -> r0 = the state byte's address, or 0; clobbers r1
    a.label("c_rtb")
    imm32(0, SESSION_OBJ); E(ldr_imm, 0, 0, 0x14); E(cmp_imm, 0, 0); E(b_cond, "rb_x", "eq")
    imm32(1, TAIL + O_RT); E(adds_reg, 0, 0, 1)
    a.label("rb_x"); E(raw, RET)

    # ---- c_rtoff(r0 = 0 / 1) -> r0 = 1 when that track's retrigger is off; clobbers r1, r2
    a.label("c_rtoff")
    E(push_list, [4], lr=True); E(mov_reg, 4, 0); E(bl, "c_rtb"); E(cmp_imm, 0, 0); E(b_cond, "ro_x", "eq")
    E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 4); E(cmp_imm, 2, TAG >> 4); E(b_cond, "ro_0", "ne")
    E(raw, h(0x40E1)); E(movs_imm, 0, 1); E(ands_reg, 0, 1); E(pop_list, [4], pc=True)       # lsrs r1, r4
    a.label("ro_0"); E(movs_imm, 0, 0)
    a.label("ro_x"); E(pop_list, [4], pc=True)

    # ---- c_rtnon (the transmitter's note-on: obj, track, note, velocity): the chain, then no GATE / TRIG for a legato note
    a.label("c_rtnon")
    E(raw, pushw([0, 1, 2, 3, 4], lr=True))
    E(bl, prev["non"])
    E(raw, h(0x9000))                                                              # str r0, [sp]: the chain's answer
    E(raw, h(0x9C01))                                                              # ldr r4, [sp, #4]: the track
    E(subs_imm8, 4, 2); E(cmp_imm, 4, 1); E(b_cond, "rn_x", "hi")
    E(mov_reg, 0, 4); E(bl, "c_rtoff"); E(cmp_imm, 0, 0); E(b_cond, "rn_x", "eq")
    imm32(1, RT0); E(lsls_imm, 0, 4, 3); E(adds_reg, 1, 1, 0)
    E(ldrb_imm, 0, 1, V.RT_CNT); E(movs_imm, 2, 15); E(ands_reg, 0, 2); E(cmp_imm, 0, 2); E(b_cond, "rn_x", "lo")
    E(ldrb_imm, 0, 1, V.RT_AUX); E(movs_imm, 2, 0x18); E(bics_reg, 0, 2); E(strb_imm, 0, 1, V.RT_AUX)
    a.label("rn_x"); E(raw, popw([0, 1, 2, 3, 4], lr=True)); E(raw, h(0x4770))

    # ---- c_rtpad (the template view's slot 0: view, pad, velocity): Shift + pad 29 with the engine on = the toggle
    a.label("c_rtpad")
    E(cmp_imm, 1, PAD_RT); E(b_cond, "rp_f", "ne")
    E(push_list, [0, 1, 2, 4], lr=True)
    E(ldrb_imm, 4, 0, 0x10); E(movs_imm, 1, 1); E(ands_reg, 4, 1)                  # r4 = the track 0 / 1
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "rp_p", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "rp_p", "eq")
    E(bl, "c_rtb"); E(cmp_imm, 0, 0); E(b_cond, "rp_e", "eq")
    E(ldrb_imm, 1, 0, 0); E(lsrs_imm, 2, 1, 4); E(cmp_imm, 2, TAG >> 4); E(b_cond, "rp_t", "eq"); E(movs_imm, 1, TAG)   # not ours: both on
    a.label("rp_t"); E(movs_imm, 2, 1); E(raw, h(0x40A2)); E(eors_reg, 1, 2); E(movs_imm, 2, 3); E(ands_reg, 1, 2); E(adds_imm8, 1, TAG)   # lsls r2, r4
    E(strb_imm, 1, 0, 0)
    a.label("rp_e"); E(pop_list, [0, 1, 2, 4], pc=True)
    a.label("rp_p"); E(raw, popw([0, 1, 2, 4], lr=True))
    a.label("rp_f"); E(b_w, prev["pad"])

    # ---- c_rtleds (the template view's slot 7: view -> the LED buffer): with Shift and the engine on, pad 29 = the retrigger
    a.label("c_rtleds")
    E(push_list, [4, 5], lr=True)
    E(ldrb_imm, 4, 0, 0x10); E(movs_imm, 1, 1); E(ands_reg, 4, 1)
    E(bl, prev["leds"]); E(mov_reg, 5, 0)
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    E(mov_reg, 0, 4); E(bl, L["c_von"]); E(cmp_imm, 0, 0); E(b_cond, "rl_x", "eq")
    E(mov_reg, 0, 4); E(bl, "c_rtoff"); E(movs_imm, 1, COL_ON); E(cmp_imm, 0, 0); E(b_cond, "rl_w", "eq"); E(movs_imm, 1, COL_OFF)
    a.label("rl_w"); E(strh_imm, 1, 5, 2 * PAD_RT)
    a.label("rl_x"); E(mov_reg, 0, 5); E(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the transmitter's note-on entry, slots 0 / 7 of the template view."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a_: struct.unpack_from("<I", img, a_ - BASE)[0]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_von=int(report["vcf20"]["labels"]["c_von"], 16))
    prev = dict(non=u(NOTE_ON) & ~1, pad=u(TMPL_VT) & ~1, leds=u(TMPL_VT + 28) & ~1)
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, NOTE_ON - BASE, labels["c_rtnon"] | 1)
    struct.pack_into("<I", img, TMPL_VT - BASE, labels["c_rtpad"] | 1)
    struct.pack_into("<I", img, TMPL_VT + 28 - BASE, labels["c_rtleds"] | 1)
    return labels, code, prev
