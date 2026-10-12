"""SC32D2 (DIAGNOSTIC): the zone survey of SC32D (tools/probe32_dsp.py with V2, tools/probe32.py) plus a MIDI dump of its flags.

  * c_dtick32c (head of the DSP service chain, then SC32D's c_dtick32 = the LED pages, then c_dtick19): while the synth source view is open, one entry per call
    (index = uptime >> 3 & 63): 0..37 = the flags of area k (Y:STF + k) into byte k of the idle Master FX LED buffer (SC14 state + 104), 38 = the sweep count
    (Y:SWEEP, two bytes at 38 / 39).
  * c_dpad (slot 0 of the synth Preset view, in front of srcview's c_xpad): with the source view open, pad 9 sends areas 0..18 and pad 10 areas 19..37, in the UI
    task, on MIDI channel 16: CC 20 = 127; per area k: CC 21 = k, CC 22 = its flags (bit 0 visited, 1 non-zero, 2 changing, 3 write OK, 4 alias), 1 ms of sleep after
    each pair; CC 23 = sweeps & 127, CC 24 = (sweeps >> 7) & 127; CC 20 = 0.  Through the stock send 0x0803BEDA (as SC32D.1).  42 messages per press: the dumps of
    SC32D.1 on the device stopped after exactly 64 messages (the stock send queue is not drained while the UI task runs; 0x0801BE78 only yields to tasks of its
    own priority or higher).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, adds_reg, strb_imm, add_sp_imm, sub_sp_imm)
import probe32_dsp as PD  # noqa: E402

DSP_READ, SEND, SLEEP = 0x08029344, 0x0803BEDA, 0x0801BE78
SP_VT = 0x0805AC9C
HAL_TICK = 0x2000081C
BUF = 104
STATUS, CC0 = 0xBF, 20
HALF = 19                                        # pad 9: areas 0..18, pad 10: 19..37 (42 messages each, under the 64 that got through in SC32D.1)
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K, xpad, next_tick):
    a = Asm(base)
    zc = [0]
    S_PAINT, F_SRC = K["S_PAINT"], K["F_SRC"]

    def bc(target, cond):
        zc[0] += 1; n = f"_r{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def src_open(fail):
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc(fail, "eq")
        a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc(fail, "eq")

    def read_y_r1():
        a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)

    # ---- c_dtick32c
    a.label("c_dtick32c")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    src_open("dc_out"); a.emit(mov_reg, 4, 0); a.emit(adds_imm8, 4, BUF)              # r4 = the byte buffer
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 5, 0, 3); a.emit(movs_imm, 1, 63); a.emit(ands_reg, 5, 1)       # r5 = index
    a.emit(cmp_imm, 5, PD.NA); bc("dc_sw", "hs")
    a.emit(movw, 1, 0x8000 | PD.STF); a.emit(adds_reg, 1, 1, 5); read_y_r1()
    a.emit(adds_reg, 1, 4, 5); a.emit(strb_imm, 0, 1, 0); a.emit(b, "dc_out")
    a.label("dc_sw")
    a.emit(cmp_imm, 5, PD.NA); bc("dc_out", "ne")
    a.emit(movw, 1, 0x8000 | PD.SWEEP); read_y_r1()
    a.emit(mov_reg, 1, 4); a.emit(adds_imm8, 1, PD.NA)                                # (strb reaches #31 only)
    a.emit(strb_imm, 0, 1, 0); a.emit(lsrs_imm, 0, 0, 8); a.emit(strb_imm, 0, 1, 1)
    a.label("dc_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, next_tick)

    # ---- c_snd (r0 = CC, r1 = value), channel 16
    a.label("c_snd")
    a.emit(push_list, [4], lr=True)
    a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 13)
    a.emit(movs_imm, 2, STATUS); a.emit(strb_imm, 2, 4, 0); a.emit(strb_imm, 0, 4, 1); a.emit(strb_imm, 1, 4, 2)
    a.emit(mov_reg, 1, 4); a.emit(movs_imm, 0, 7); a.emit(bl, SEND)
    a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)

    # ---- c_dpad (view, pad, vel)
    a.label("c_dpad")
    a.emit(push_list, [0, 1, 2, 4, 5, 6, 7], lr=True)
    a.emit(movs_imm, 5, 0); a.emit(movs_imm, 7, HALF)                                 # pad 9: areas 0..HALF-1
    a.emit(cmp_imm, 1, 8); a.emit(b_cond, "dq_p", "eq")
    a.emit(movs_imm, 5, HALF); a.emit(movs_imm, 7, PD.NA)                             # pad 10: the rest
    a.emit(cmp_imm, 1, 9); bc("dq_fwd", "ne")
    a.label("dq_p")
    src_open("dq_fwd"); a.emit(mov_reg, 4, 0); a.emit(adds_imm8, 4, BUF)
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 127); a.emit(bl, "c_snd")
    a.label("dq_l")
    a.emit(movs_imm, 0, CC0 + 1); a.emit(mov_reg, 1, 5); a.emit(bl, "c_snd")
    a.emit(adds_reg, 1, 4, 5); a.emit(ldrb_imm, 1, 1, 0); a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 1, 0)
    a.emit(movs_imm, 0, CC0 + 2); a.emit(bl, "c_snd")
    a.emit(movs_imm, 0, 1); a.emit(bl, SLEEP)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_reg, 5, 7); a.emit(b_cond, "dq_l", "lo")
    a.emit(mov_reg, 2, 4); a.emit(adds_imm8, 2, PD.NA)
    a.emit(ldrb_imm, 6, 2, 0); a.emit(ldrb_imm, 1, 2, 1); a.emit(lsls_imm, 1, 1, 8); a.emit(adds_reg, 6, 6, 1)   # r6 = sweeps
    a.emit(movs_imm, 0, 0x7F); a.emit(mov_reg, 1, 6); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + 3); a.emit(bl, "c_snd")
    a.emit(lsrs_imm, 1, 6, 7); a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + 4); a.emit(bl, "c_snd")
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 0); a.emit(bl, "c_snd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True)); a.emit(raw, h(0x4770))
    a.label("dq_fwd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6, 7], lr=True))
    a.emit(b_w, xpad)
    return a.assemble()


def install(img, report, base_addr, next_tick):
    """After probe32.install: c_dtick32c becomes the head of the DSP service chain (then next_tick = c_dtick32); slot 0 of the synth Preset view -> c_dpad."""
    import struct
    import ct_fw
    import build_sc14 as s14
    import build_sc15 as s15
    import srcview
    import drums18
    BASE = ct_fw.APP_BASE
    xpad = int(report["srcview"]["labels"]["c_xpad"], 16)
    assert struct.unpack_from("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE)[0] == xpad | 1
    assert drums18.decode_bw(img, s14.SVC_HOOK) == next_tick
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16))
    K = dict(S_PAINT=s15.S_PAINT, F_SRC=srcview.F_SRC)
    code, labels = arm_code(base_addr, L, K, xpad, next_tick)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick32c"])
    struct.pack_into("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE, labels["c_dpad"] | 1)
    return labels, code
