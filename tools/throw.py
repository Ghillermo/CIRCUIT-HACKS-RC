"""SC39.8 (the user, 2026-10-12: «en Digitise, añade un control adicional: envía, mientras esté pulsado, un send de valor 100 de todas las pistas (o de
master) al delay (el delay vuelve a su estado anterior al soltar)» … «en los efectos de menos de 4 knobs, añade un control adicional si hay sitio»):
Digitise had two knobs (K1 sample-rate reduction, K2 bit depth); K3 is now the delay throw.

While pad 4 of the Master FX view (Digitise) is held, the delay send of the eight tracks is K3 (0 = no throw; the default is 100); when the pad is
let go the eight sends go back to what they were.  Only the pad held by hand does it: not Shift + pad (the latch), not a bottom slot, not the FX
sequencer (those switch effects from the DSP service tick, where the project's parameters must not be written).
The sends are the project parameters of type 0x20, indices 11..18, read with 0x08036192 and written with the listener of the MIDI input
(0x08034D92: the store, the DSP, the Mixer / FX views, MIDI out), from the pad handlers (the interface task).  What they were is kept in three
free words of the DSP (the Vinyl parameters, unused since SC39.7: 7 bits x 3 per word) with a mark in a fourth, read and written under the
semaphore of the DSP service as packio's clip is: the Master FX block has no free byte.  If the view is left with the pad held (no release comes),
the next button press puts the sends back: the head of the button chain looks at the mark while the Master FX view is on the screen.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, adds_imm8, ands_reg, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm, mov_reg, movs_imm,  # noqa: E402
                   movt, movw, orrs_reg, pop_list, push_list, raw, h, sub_sp_imm, add_sp_imm, tst_reg)
import build_sc17 as S17  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import mpatch as MP  # noqa: E402

PAD_DIG, SET_DIG = 3, 2               # pad 4 = Digitise, its knob set
K_THROW = S17.S_KNOB + 4 * SET_DIG + 2
SEND_TYPE, DELAY0, NTRK = 0x20, 11, 8
GETTER, PARAM_SET, CTX = 0x08036192, 0x08034D92, 0x200069E4
FLAG, WORDS = G.VN_CR, (G.VN_HISS, G.VN_LPK, G.VN_HPK)
MAGIC = 0x5E2D01
BTN_ENTRY = MP.BTN_ENTRY


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, prev):
    a = Asm(base)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    def take(): E(mov_reg, 0, 13); E(bl, L["c_take"])
    def give(): E(mov_reg, 0, 13); E(bl, L["c_give"])

    # ---- c_thw(r0 = track 0..7, r1 = value): its delay send
    a.label("c_thw")
    E(push_list, [3, 4, 5], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1)
    imm32(0, CTX); E(ldr_imm, 0, 0, 0); E(ldr_imm, 0, 0, 0x10); E(ldr_imm, 0, 0, 0)
    E(adds_imm8, 0, 4); E(movs_imm, 1, SEND_TYPE); E(mov_reg, 2, 4); E(adds_imm8, 2, DELAY0); E(mov_reg, 3, 5); E(bl, PARAM_SET)
    E(pop_list, [3, 4, 5], pc=True)

    # ---- c_thon(r0 = the level): the sends kept in the DSP words, then all eight at the level (nothing when a throw is already on)
    a.label("c_thon")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    E(mov_reg, 7, 0)
    take(); imm32(0, FLAG); E(bl, L["c_xr"]); E(mov_reg, 4, 0); give()
    imm32(1, MAGIC); E(cmp_reg, 4, 1); E(b_cond, "on_go", "ne"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)
    a.label("on_go")
    for w, addr in enumerate(WORDS):
        E(movs_imm, 6, 0)
        for j in (2, 1, 0):
            i = 3 * w + j
            if i >= NTRK: continue
            E(movs_imm, 0, SEND_TYPE); E(movs_imm, 1, DELAY0 + i); E(bl, GETTER); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1)
            E(lsls_imm, 6, 6, 7); E(orrs_reg, 6, 0)
        take(); imm32(0, addr); E(mov_reg, 1, 6); E(bl, L["c_xw"]); give()
    take(); imm32(0, FLAG); imm32(1, MAGIC); E(bl, L["c_xw"]); give()
    for i in range(NTRK): E(movs_imm, 0, i); E(mov_reg, 1, 7); E(bl, "c_thw")
    a.label("on_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_thoff(): a throw is on (the mark) = the eight sends back, the mark gone
    a.label("c_thoff")
    E(push_list, [4, 5, 6, 7], lr=True); E(sub_sp_imm, 8)
    take(); imm32(0, FLAG); E(bl, L["c_xr"]); imm32(1, MAGIC); E(cmp_reg, 0, 1); E(b_cond, "of_go", "eq")
    give(); E(b, "of_x")
    a.label("of_go")
    for reg, addr in zip((4, 5, 6), WORDS): imm32(0, addr); E(bl, L["c_xr"]); E(mov_reg, reg, 0)
    imm32(0, FLAG); E(movs_imm, 1, 0); E(bl, L["c_xw"]); give()
    for i in range(NTRK):
        reg = (4, 5, 6)[i // 3]
        if i % 3: E(lsrs_imm, 1, reg, 7 * (i % 3))
        else: E(mov_reg, 1, reg)
        E(movs_imm, 0, 0x7F); E(ands_reg, 1, 0); E(movs_imm, 0, i); E(bl, "c_thw")
    a.label("of_x"); E(add_sp_imm, 8); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_thpress (the Mixer view's slot 0: view, pad, velocity): Digitise held by hand = the throw
    a.label("c_thpress")
    E(cmp_imm, 1, PAD_DIG); E(b_cond, "tp_f", "ne")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(bl, L["c_gact"]); E(mov_reg, 4, 0); E(cmp_imm, 4, 0); E(b_cond, "tp_fp", "eq")
    E(bl, L["c_shift"]); E(cmp_imm, 0, 0); E(b_cond, "tp_fp", "ne")
    E(ldrb_imm, 0, 4, S17.S_LATCH); E(movs_imm, 1, 1 << PAD_DIG); E(tst_reg, 0, 1); E(b_cond, "tp_fp", "ne")     # (a tap on the latched effect switches it off)
    E(ldrb_w, 0, 4, K_THROW); E(movs_imm, 1, 0x7F); E(ands_reg, 0, 1); E(cmp_imm, 0, 0); E(b_cond, "tp_fp", "eq")
    E(bl, "c_thon")
    a.label("tp_fp"); E(raw, popw([0, 1, 2, 4, 5], lr=True))
    a.label("tp_f"); E(b_w, prev["press"])

    # ---- c_threl (slot 1: view, pad): Digitise let go
    a.label("c_threl")
    E(cmp_imm, 1, PAD_DIG); E(b_cond, "tr_f", "ne")
    E(push_list, [0, 1, 2, 4, 5], lr=True); E(bl, "c_thoff"); E(raw, popw([0, 1, 2, 4, 5], lr=True))
    a.label("tr_f"); E(b_w, prev["rel"])

    # ---- c_thbtn (the controller's button press: ctrl, id): the Master FX view on the screen = a throw left on goes back first
    a.label("c_thbtn")
    E(push_list, [0, 1, 2, 4, 5], lr=True)
    E(bl, L["c_gact"]); E(cmp_imm, 0, 0); E(b_cond, "tb_f", "eq")
    E(bl, "c_thoff")
    a.label("tb_f"); E(raw, popw([0, 1, 2, 4, 5], lr=True)); E(b_w, prev["btn"])
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; the Mixer view's slots 0 / 1 and the head of the button chain."""
    import ct_fw
    BASE = ct_fw.APP_BASE
    u = lambda a: struct.unpack_from("<I", img, a - BASE)[0]
    lab = lambda sec, n: int(report[sec]["labels"][n], 16)
    VT = S17.MIX_VT
    L = dict(c_gact=lab("sc17", "c_gact"), c_shift=lab("sc15", "c_shift"), **{n: lab("packio", n) for n in ("c_take", "c_give", "c_xr", "c_xw")})
    prev = dict(press=u(VT) & ~1, rel=u(VT + 4) & ~1, btn=MP.bw_target(img, BTN_ENTRY, BASE))
    assert prev["btn"] == lab("psave", "c_psbtn"), hex(prev["btn"])
    code, labels = arm_code(base_addr, L, prev)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, VT - BASE, labels["c_thpress"] | 1)
    struct.pack_into("<I", img, VT + 4 - BASE, labels["c_threl"] | 1)
    img[BTN_ENTRY - BASE:BTN_ENTRY - BASE + 4] = b_w(BTN_ENTRY, labels["c_thbtn"])
    return labels, code, prev
