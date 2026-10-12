"""SC20D: the capture meter (ARM side).  Diagnostic for the delay / reverb return modes (5 / 6) of the synth source.

The DSP (tools/linein3.py, METER) captures L + R of the delay and reverb outputs every block and leaves the mean |L + R| of each
capture in Y:$3B00 (delay) / Y:$3B01 (reverb), plus a constant 0x5A3C69 in Y:$3B02.  While the SC19.1 source view is open (flag = bit 2 of the SC14
byte +20) the DSP service tick (head of the chain, as the drum tick of SC19) reads the three words with the stock DSP read 0x08029344(core 0, 0x8000 | Y address)
(returns the 24-bit word in bits 31..8) and paints the bars in the Preset view of the synths, pad rows 2 (delay) and 3 (reverb):
  * lit pads = number of thresholds 2^(6 + 2 k) (k = 0..7, 12 dB apart, about -102 .. -18 dB of full scale) reached by the mean |L + R| / 32 x 32 frames;
    the number of lit pads is the level, delay colour 0x6B (peach), reverb 0x2A (cream), the colours of the FX view Octave LEDs;
  * if the constant does not read back, both rows are painted with 0x05 (red): the DSP read path itself is not working, the bars mean nothing.
Nothing is read or written while the source view is closed.  The tick then continues into SC19's c_dtick19.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, mov_reg, movs_imm, movt, movw, adds_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, strh_imm, adds_reg, tst_reg)

DSP_READ = 0x08029344
SP_VT = 0x0805AC9C
VIEWS = (0x20042980, 0x20042A34)               # synth Preset views (Synth 1 / Synth 2)
COL_DELAY, COL_REVERB, COL_BAD = 0x6B, 0x2A, 0x05
N_BARS = 8
THR0, THR_STEP = 14, 2                         # threshold k = 1 << (14 + 2k) on the word (24-bit value << 8) = 2^(6 + 2k) on the value
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K, meter_y, check_y, magic):
    a = Asm(base)
    zc = [0]
    S_PAINT, F_SRC = K["S_PAINT"], K["F_SRC"]

    def bc(target, cond):
        zc[0] += 1; n = f"_m{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    a.label("c_dtick20")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("mt_out", "eq")
    a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc("mt_out", "eq")
    # three reads: delay level, reverb level, check constant
    a.emit(movs_imm, 0, 0); a.emit(movw, 1, 0x8000 | meter_y[0]); a.emit(bl, DSP_READ); a.emit(mov_reg, 4, 0)
    a.emit(movs_imm, 0, 0); a.emit(movw, 1, 0x8000 | meter_y[1]); a.emit(bl, DSP_READ); a.emit(mov_reg, 5, 0)
    a.emit(movs_imm, 0, 0); a.emit(movw, 1, 0x8000 | check_y); a.emit(bl, DSP_READ)
    a.emit(movw, 1, (magic << 8) & 0xFFFF); a.emit(movt, 1, (magic << 8) >> 16)
    a.emit(cmp_reg, 0, 1); bc("mt_ok", "eq")
    a.emit(movs_imm, 6, N_BARS); a.emit(movs_imm, 7, N_BARS)                   # check failed: both rows entirely red
    a.emit(movs_imm, 4, COL_BAD); a.emit(movs_imm, 5, COL_BAD)
    a.emit(b, "mt_paint")
    a.label("mt_ok")
    a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 0)                             # r6 / r7 = lit pads of delay / reverb
    for k in range(N_BARS):
        a.emit(movs_imm, 2, 1); a.emit(lsls_imm, 2, 2, THR0 + THR_STEP * k)
        a.emit(cmp_reg, 4, 2); bc(f"mt_d{k}", "lo"); a.emit(adds_imm8, 6, 1); a.label(f"mt_d{k}")
        a.emit(cmp_reg, 5, 2); bc(f"mt_r{k}", "lo"); a.emit(adds_imm8, 7, 1); a.label(f"mt_r{k}")
    a.emit(movs_imm, 4, COL_DELAY); a.emit(movs_imm, 5, COL_REVERB)             # r4 / r5 = the colours of the two rows from here on
    a.label("mt_paint")
    for vi, view in enumerate(VIEWS):
        a.emit(movw, 0, view & 0xFFFF); a.emit(movt, 0, view >> 16)
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, SP_VT & 0xFFFF); a.emit(movt, 2, SP_VT >> 16)
        a.emit(cmp_reg, 1, 2); bc(f"mt_v{vi}", "ne")                           # not a synth Preset view: leave it alone
        a.emit(bl, K["SP_LEDS"])                                               # r0 = LED buffer
        a.emit(movs_imm, 1, 0)
        a.label(f"mt_l{vi}")
        a.emit(lsls_imm, 3, 1, 1); a.emit(adds_reg, 3, 3, 0)
        a.emit(movs_imm, 2, 0); a.emit(cmp_reg, 1, 6); bc(f"mt_a{vi}", "hs"); a.emit(mov_reg, 2, 4); a.label(f"mt_a{vi}")
        a.emit(strh_imm, 2, 3, 16)                                             # entries 8..15 = row 2
        a.emit(movs_imm, 2, 0); a.emit(cmp_reg, 1, 7); bc(f"mt_b{vi}", "hs"); a.emit(mov_reg, 2, 5); a.label(f"mt_b{vi}")
        a.emit(strh_imm, 2, 3, 32)                                             # entries 16..23 = row 3
        a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, N_BARS); bc(f"mt_l{vi}", "lo")
        a.label(f"mt_v{vi}")
    a.label("mt_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_dtick19"])
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and put c_dtick20 at the head of the DSP service chain (in front of SC19's c_dtick19)."""
    import ct_fw
    import build_sc14 as s14
    import build_sc15 as s15
    import linein3
    import srcview
    BASE = ct_fw.APP_BASE
    assert linein3.METER and srcview.METER
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_dtick19=p19["c_dtick19"])
    K = dict(S_PAINT=s15.S_PAINT, F_SRC=srcview.F_SRC, SP_LEDS=s15.SP_LEDS)
    import drums18
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"], hex(drums18.decode_bw(img, s14.SVC_HOOK))
    code, labels = arm_code(base_addr, L, K, linein3.METER_Y, linein3.METER_CHECK, linein3.METER_MAGIC)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick20"])
    return labels, code
