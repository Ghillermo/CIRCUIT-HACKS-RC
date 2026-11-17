"""Beta 5.65 / RC4.16 (2026-11-15): the stock pad painters that overran their 16-pad LED buffers (the 5.63 / 5.64 crashes), guarded.

Caught on the device (S564D5 + tools/livewatch.py, 21:14:59): the 32 bytes after MIDI 2's probability-view LED buffer (16 pads, 0x20042960) became
0x20 0x26 0x28 0x27 0x09 0x0F 0x10 0x11 0x3B 0x41 0x42 0x43 0x45 0x46 0x47 0x48 = exactly what the stock probability painter (0x0804D116, the view's
listener) writes as pads 17-32 when the selected step's probability byte is >= 32 (it lights pad k while k < the byte; valid probabilities are 0..7):
the next object (Synth 1's Preset view: its vtable, LED buffer and listener vtable) was trampled, and the next store commit that called it crashed
(Play / Record).  The 5.63 crash is the same with Drum 3's velocity bar (0x0804EF0E: it lights 16 pads from the step's velocity; a velocity >= 129
runs past them into Drum 4's object).  How a selected step gets such a byte is still open (a chain / scene leading a track to a pattern past its
eight is the lead: NOTAS «Beta 5.65»); these guards make both painters skip a value they cannot draw:
  * c_pgl: stepmod's two calls of the probability listener (c_rfled, c_rfbuf) -> here: the selected step's probability byte > 15 = return
    (nothing painted), else the stock's;
  * c_vgp / c_vg: the velocity bar's listener tail (0x0804EFCC: pop.w {r4, lr}; b painter -> b.w c_vgp; nop) and its constructor's call
    (0x0804EE56: bl painter -> bl c_vg): the painter's r1 is the step; its velocity (byte r1 & 3 of the word PARAM_GET([bar + 0xC], r1 >> 2), as
    the painter reads it) > 127 = return, else the stock painter.
In dspz's first gap (dspz.add); ~60 B."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import Asm, b_cond, b_w, bl, cmp_imm, h, ldr_imm, ldrb_imm, mov_reg, movs_imm, movt, movw, pop_list, push_list, raw  # noqa: E402

PROB_LISTEN = 0x0804D116
PARAM_GET = 0x0803542C
PAINTER = 0x0804EF0E
VB_TAIL = 0x0804EFCC                                    # pop.w {r4, lr}; b PAINTER  (6 B)
VB_CTOR = 0x0804EE56                                    # bl PAINTER
TAIL_BYTES = bytes.fromhex("bde810409de7")


def pushw(regs, lr=False):
    m = sum(1 << r for r in regs) | (0x4000 if lr else 0); return h(0xE92D) + h(m)


def popw(regs, lr=False, pc=False):
    m = sum(1 << r for r in regs) | (0x4000 if lr else 0) | (0x8000 if pc else 0); return h(0xE8BD) + h(m)


FREEZE = None                                           # (beta) the black box's c_bbfrz: a skip freezes the record once (state 0x85, the tag at STK1)


def arm_code(base):
    a = Asm(base)
    E = a.emit
    def frz(tag):                                                                # the record frozen once, with the tag (1 probability, 2 velocity)
        if FREEZE is None: return
        import blackbox as BB
        E(movw, 0, BB.BB & 0xFFFF); E(movt, 0, BB.BB >> 16); E(ldrb_imm, 1, 0, BB.O.ST); E(raw, h(0x07C9)); E(b_cond, f"fz_{tag}", "mi")   # lsls r1, r1, #31
        E(movs_imm, 0, 0x85); E(bl, FREEZE)
        E(movw, 0, (BB.BB + BB.O.STK1) & 0xFFFF); E(movt, 0, (BB.BB + BB.O.STK1) >> 16); E(movs_imm, 1, tag); E(raw, h(0x6001))          # str r1, [r0]
        E(raw, h(0x6044))                                                        # str r4, [r0, #4]: the value it skipped
        a.label(f"fz_{tag}")
    # ---- c_pgl(r0 = the view, r1 = the store): the selected step's probability byte > 15 -> nothing, else the stock listener
    a.label("c_pgl")
    E(raw, pushw([0, 1, 4], lr=True))
    E(ldr_imm, 0, 0, 0xC); E(ldr_imm, 0, 0, 8); E(movs_imm, 1, 0); E(bl, PARAM_GET)
    E(ldrb_imm, 4, 0, 1)
    E(cmp_imm, 4, 15); E(b_cond, "pg_x", "hi")
    E(raw, popw([0, 1, 4], lr=True)); E(b_w, PROB_LISTEN)
    a.label("pg_x"); frz(1); E(raw, popw([0, 1, 4], pc=True))
    # ---- c_vgp: the velocity bar listener's tail (pop.w {r4, lr} first); c_vg(r0 = the bar, r1 = the velocity): > 127 -> nothing
    a.label("c_vgp"); E(raw, popw([4], lr=True))
    a.label("c_vg")                                                              # (r0 = the bar, r1 = the step): its velocity as the painter reads it
    E(raw, pushw([0, 1, 4], lr=True)); E(raw, h(0x000C))                         # movs r4, r1
    E(ldr_imm, 0, 0, 0xC); E(raw, h(0x08A1)); E(bl, PARAM_GET)                   # lsrs r1, r4, #2: the word of four steps
    E(ldr_imm, 0, 0, 0); E(movs_imm, 2, 3); E(raw, h(0x4022)); E(raw, h(0x00D2))   # ands r2, r4; lsls r2, r2, #3
    E(raw, h(0x40D0)); E(raw, h(0xB2C0))                                         # lsrs r0, r2; uxtb r0
    E(cmp_imm, 0, 127); E(b_cond, "vg_x", "hi")
    E(raw, popw([0, 1, 4], lr=True)); E(b_w, PAINTER)
    a.label("vg_x"); E(mov_reg, 4, 0); frz(2); E(raw, popw([0, 1, 4], pc=True))
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    sites = [x for x in (int(report["stepmod"]["labels"]["c_rfled"], 16), int(report["stepmod"]["labels"]["c_rfbuf"], 16))]
    calls = [BASE + o for o in range(0, len(img) - 3, 2) if bytes(img[o:o + 4]) == bl_enc(BASE + o, PROB_LISTEN) and BASE + o >= min(sites)]
    assert len(calls) == 2, [hex(c) for c in calls]
    assert bytes(img[VB_TAIL - BASE:VB_TAIL - BASE + 6]) == TAIL_BYTES, bytes(img[VB_TAIL - BASE:VB_TAIL - BASE + 6]).hex()
    assert bytes(img[VB_CTOR - BASE:VB_CTOR - BASE + 4]) == bl_enc(VB_CTOR, PAINTER)
    global FREEZE
    if FREEZE == "auto": FREEZE = int(report["blackbox"]["labels"]["c_bbfrz"], 16)
    code, labels = arm_code(base_addr)
    img += code
    while len(img) % 4:
        img += bytes([0xFF])
    for c in calls: img[c - BASE:c - BASE + 4] = bl_enc(c, labels["c_pgl"])
    import rdiag as RD
    img[VB_TAIL - BASE:VB_TAIL - BASE + 4] = RD.b_w(VB_TAIL, labels["c_vgp"]); img[VB_TAIL - BASE + 4:VB_TAIL - BASE + 6] = bytes.fromhex("00bf")
    img[VB_CTOR - BASE:VB_CTOR - BASE + 4] = bl_enc(VB_CTOR, labels["c_vg"])
    report["paintguard"] = dict(arm_start=hex(base_addr), labels={k: hex(v) for k, v in labels.items()}, calls=[hex(c) for c in calls])
    return labels, code, {}
