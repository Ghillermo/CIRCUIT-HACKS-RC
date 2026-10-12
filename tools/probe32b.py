"""SC32D.1 (DIAGNOSTIC): the ARM side of the raw probe (tools/probe32b_dsp.py): the 14 DSP words go out as MIDI CC (USB and DIN, the stock send 0x0803BEDA).

  * c_dtick32b (head of the DSP service chain, then SC19's c_dtick19): while the synth source view is open (Synth 1 / 2 pressed twice), one word per call
    (index = uptime >> 3 & 15, 0..13) is read from Y:YM + index (stock read 0x08029344) into the idle Master FX LED buffer (SC14 state + 104, 56 bytes; the Master FX view
    is not on screen then); pad 9 is green once the magic is there (the probe ran), red before; pads 10-24 dark.
  * c_dpad (slot 0 of the synth Preset view, in front of srcview's c_xpad): with the source view open, pad 9 sends the dump, in the UI task (as the stock knob
    handlers do, never from the DSP service tick):  CC 20 = 127 (start); per word i = 0..13: CC 21 = i, CC 22 = bits 23..21, CC 23 = bits 20..14,
    CC 24 = bits 13..7, CC 25 = bits 6..0, then 2 ms of sleep; CC 20 = 0 (end).  All on MIDI channel 16.  Word 0 = MAGIC ($C0FFEE), words 1..13 = the results.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, strh_imm, adds_reg, str_imm, strb_imm, add_sp_imm, sub_sp_imm)
import probe32b_dsp as PD  # noqa: E402

DSP_READ, SEND, SLEEP = 0x08029344, 0x0803BEDA, 0x0801BE78
SP_VT = 0x0805AC9C
VIEWS = (0x20042980, 0x20042A34)
HAL_TICK = 0x2000081C
BUF = 104                                        # SC14 state + 104 = the Master FX LED buffer (block + 64), 14 words
NWORDS = 1 + PD.NW
GREEN, RED = 0x19, 0x53                          # (RGB table, stored B, G, R: 0x19 = 0, 121, 0; 0x53 = 255, 0, 0)
STATUS = 0xBF                                    # CC, channel 16
CC0 = 20
INV = {"eq": "ne", "ne": "eq", "lo": "hs", "hs": "lo"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K, xpad):
    a = Asm(base)
    zc = [0]
    S_PAINT, F_SRC = K["S_PAINT"], K["F_SRC"]

    def bc(target, cond):
        zc[0] += 1; n = f"_q{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def src_open(fail):                          # r0 = SC14 state when the source view is open, else -> fail
        a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc(fail, "eq")
        a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc(fail, "eq")

    # ---- c_dtick32b
    a.label("c_dtick32b")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    src_open("dt_out"); a.emit(mov_reg, 4, 0)
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 5, 0, 3); a.emit(movs_imm, 1, 15); a.emit(ands_reg, 5, 1)       # r5 = word index
    a.emit(cmp_imm, 5, NWORDS); bc("dt_led", "hs")
    a.emit(movw, 1, 0x8000 | PD.YM); a.emit(adds_reg, 1, 1, 5); a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)
    a.emit(lsls_imm, 1, 5, 2); a.emit(adds_reg, 1, 1, 4); a.emit(str_imm, 0, 1, BUF)  # buf[i] = word (str imm5*4 reaches 124)
    a.label("dt_led")
    a.emit(ldr_imm, 0, 4, BUF); a.emit(movw, 1, PD.MAGIC & 0xFFFF); a.emit(movt, 1, PD.MAGIC >> 16)
    a.emit(movs_imm, 7, RED); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "dt_c", "ne"); a.emit(movs_imm, 7, GREEN)
    a.label("dt_c")
    for vi, view in enumerate(VIEWS):
        a.emit(movw, 0, view & 0xFFFF); a.emit(movt, 0, view >> 16)
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, SP_VT & 0xFFFF); a.emit(movt, 2, SP_VT >> 16)
        a.emit(cmp_reg, 1, 2); bc(f"dt_v{vi}", "ne")
        a.emit(bl, K["SP_LEDS"])
        a.emit(strh_imm, 7, 0, 16); a.emit(movs_imm, 1, 0)
        for i in range(9, 24): a.emit(strh_imm, 1, 0, 2 * i)
        a.label(f"dt_v{vi}")
    a.label("dt_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_dtick19"])

    # ---- c_snd (r0 = CC number, r1 = value): one CC on channel 16 through the stock send
    a.label("c_snd")
    a.emit(push_list, [4], lr=True)
    a.emit(sub_sp_imm, 8); a.emit(mov_reg, 4, 13)
    a.emit(movs_imm, 2, STATUS); a.emit(strb_imm, 2, 4, 0); a.emit(strb_imm, 0, 4, 1); a.emit(strb_imm, 1, 4, 2)
    a.emit(mov_reg, 1, 4); a.emit(movs_imm, 0, 7); a.emit(bl, SEND)
    a.emit(add_sp_imm, 8); a.emit(pop_list, [4], pc=True)

    # ---- c_dpad (view, pad, vel): slot 0 of the synth Preset view
    a.label("c_dpad")
    a.emit(push_list, [0, 1, 2, 4, 5, 6], lr=True)
    a.emit(cmp_imm, 1, 8); bc("dp_fwd", "ne")
    src_open("dp_fwd"); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 127); a.emit(bl, "c_snd")
    a.emit(movs_imm, 5, 0)
    a.label("dp_l")
    a.emit(lsls_imm, 1, 5, 2); a.emit(adds_reg, 1, 1, 4); a.emit(ldr_imm, 6, 1, BUF)  # r6 = word
    a.emit(movs_imm, 0, CC0 + 1); a.emit(mov_reg, 1, 5); a.emit(bl, "c_snd")
    a.emit(lsrs_imm, 1, 6, 21); a.emit(movs_imm, 0, 7); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + 2); a.emit(bl, "c_snd")
    for k, sh in ((3, 14), (4, 7), (5, 0)):
        if sh: a.emit(lsrs_imm, 1, 6, sh)
        else: a.emit(mov_reg, 1, 6)
        a.emit(movs_imm, 0, 0x7F); a.emit(ands_reg, 1, 0); a.emit(movs_imm, 0, CC0 + k); a.emit(bl, "c_snd")
    a.emit(movs_imm, 0, 2); a.emit(bl, SLEEP)
    a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 5, NWORDS); a.emit(b_cond, "dp_l", "lo")
    a.emit(movs_imm, 0, CC0); a.emit(movs_imm, 1, 0); a.emit(bl, "c_snd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6], lr=True)); a.emit(raw, h(0x4770))          # swallowed
    a.label("dp_fwd")
    a.emit(raw, popw([0, 1, 2, 4, 5, 6], lr=True))
    a.emit(b_w, xpad)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code; c_dtick32b at the head of the DSP service chain; slot 0 of the synth Preset view -> c_dpad (then srcview's c_xpad)."""
    import struct
    import ct_fw
    import build_sc14 as s14
    import build_sc15 as s15
    import srcview
    import drums18
    BASE = ct_fw.APP_BASE
    assert srcview.METER
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    xpad = int(report["srcview"]["labels"]["c_xpad"], 16)
    assert struct.unpack_from("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE)[0] == xpad | 1
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_dtick19=p19["c_dtick19"])
    K = dict(S_PAINT=s15.S_PAINT, F_SRC=srcview.F_SRC, SP_LEDS=s15.SP_LEDS)
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"]
    code, labels = arm_code(base_addr, L, K, xpad)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick32b"])
    struct.pack_into("<I", img, SP_VT + 4 * srcview.SLOT_PAD - BASE, labels["c_dpad"] | 1)
    return labels, code
