"""SC21D (DIAGNOSTIC): the DSP probe display and the NRPN monitor (ARM side; the DSP side is tools/probe21_dsp.py).

While the synth source view is open (Synth 1 / 2 pressed twice: the SC19.1 view, flag bit 2 of the SC14 byte +20) the pad rows 2 and 3 (16 pads, entries 8..23 of the LED
buffer of the synth Preset view: the rows the SC20D meter used) cycle through four pages, 4 s each (page = uptime >> 12 & 3), a colour per page:
  page 0 yellow  FACTS of the DSP probe, one pad each, lit = true (pad 9 = the probe ran; pads 10..17 = P-RAM write / read-back OK at P:$3800, $3C00, $3FFF, $4000, $5000,
                 $6000, $7000, $7FFF; pad 18 = P:$3800 was 0; pad 19 = P:$3800 was $FFFFFF; pad 20 = the shared memory word X:$030000 is 0; pad 21 = ICPR1 != 0; pad 22 = ICCR1 != 0)
  page 1 blue    OMR bits 15..0 (pad 9 = bit 15)
  page 2 green   the last NRPN: MSB (row 2, 8 bits) and LSB (row 3), as received on the MIDI input
  page 3 magenta the last CC number (row 2) and its value (row 3); the count of CC messages is the 8-bit sum on pad ... (see the PRUEBA.md)
If the DSP magic ($C0FFEE) does not read back, the pages 0 and 1 are all red (the probe did not run or the DSP read path failed).
NRPN monitor: a hook at the first four bytes of 0x08052854 (the stock incoming CC dispatcher: r2 = CC number, r3 = value) stores [CC, value, NRPN MSB (CC 99), NRPN LSB (CC 98),
data entry (CC 6), count] in the first bytes of the settings tail (SETOBJ + 0x3D) and runs the displaced instructions.  Nothing else of the MIDI path changes.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, strh_imm, strb_imm, adds_reg, tst_reg, ands_reg, lsrs_reg, ldrb_w)

DSP_READ = 0x08029344
SP_VT = 0x0805AC9C
VIEWS = (0x20042980, 0x20042A34)               # synth Preset views (Synth 1 / Synth 2)
HAL_TICK = 0x2000081C
TAIL = 0x20039789                              # settings object 0x2003974C + 0x3D
CC_FN, CC_NEXT = 0x08052854, 0x08052858        # the stock incoming CC dispatcher; its first 4 bytes are push {r4, r5, r6, lr} ; mov r4, r0
CC_BYTES = bytes.fromhex("70b50446")
YR = 0x3B10
FACTS, OMR = YR + 8, YR + 1
MAGIC = 0xC0FFEE
COL = (0x2D, 0x13, 0x19, 0x32)                 # yellow, blue, green, magenta (the RGB table of 0x0803423C)
COL_BAD = 0x05
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K):
    a = Asm(base)
    zc = [0]
    S_PAINT, F_SRC = K["S_PAINT"], K["F_SRC"]

    def bc(target, cond):
        zc[0] += 1; n = f"_p{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def read_y(addr):                           # r0 = the 24-bit word of Y:addr (right-aligned)
        a.emit(movs_imm, 0, 0); a.emit(movw, 1, 0x8000 | addr); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)

    # ---- c_nrpnlog: b.w from the first bytes of the CC dispatcher; r0..r3 are its arguments (r2 = CC, r3 = value) and are kept
    a.label("c_nrpnlog")
    a.emit(push_list, [0, 1, 2, 3, 4])
    a.emit(movw, 4, TAIL & 0xFFFF); a.emit(movt, 4, TAIL >> 16)
    a.emit(strb_imm, 2, 4, 0); a.emit(strb_imm, 3, 4, 1)
    a.emit(cmp_imm, 2, 99); a.emit(b_cond, "nl_1", "ne"); a.emit(strb_imm, 3, 4, 2)
    a.label("nl_1"); a.emit(cmp_imm, 2, 98); a.emit(b_cond, "nl_2", "ne"); a.emit(strb_imm, 3, 4, 3)
    a.label("nl_2"); a.emit(cmp_imm, 2, 6); a.emit(b_cond, "nl_3", "ne"); a.emit(strb_imm, 3, 4, 4)
    a.label("nl_3"); a.emit(ldrb_imm, 0, 4, 5); a.emit(adds_imm8, 0, 1); a.emit(strb_imm, 0, 4, 5)
    a.emit(pop_list, [0, 1, 2, 3, 4])
    a.emit(raw, h(0xB570)); a.emit(raw, h(0x4604))                              # the displaced push {r4, r5, r6, lr} ; mov r4, r0
    a.emit(b_w, CC_NEXT)

    # ---- c_dtick21: head of the DSP service chain (in front of SC19's c_dtick19)
    a.label("c_dtick21")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("pt_out", "eq")
    a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc("pt_out", "eq")
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 5, 0, 12); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 5, 1)       # r5 = page 0..3
    a.emit(movs_imm, 7, COL[0]); a.emit(cmp_imm, 5, 1); a.emit(b_cond, "pt_c1", "ne"); a.emit(movs_imm, 7, COL[1])
    a.label("pt_c1"); a.emit(cmp_imm, 5, 2); a.emit(b_cond, "pt_c2", "ne"); a.emit(movs_imm, 7, COL[2])
    a.label("pt_c2"); a.emit(cmp_imm, 5, 3); a.emit(b_cond, "pt_c3", "ne"); a.emit(movs_imm, 7, COL[3])
    a.label("pt_c3")
    a.emit(movs_imm, 4, 0)                                                       # r4 = 1: pad 9 + i = bit i (facts); 0: pad 9 = bit 15 (the others)
    a.emit(cmp_imm, 5, 2); bc("pt_arm", "hs")
    read_y(YR); a.emit(movw, 1, MAGIC & 0xFFFF); a.emit(movt, 1, MAGIC >> 16); a.emit(cmp_reg, 0, 1); bc("pt_ok", "eq")
    a.emit(movw, 6, 0xFFFF); a.emit(movs_imm, 7, COL_BAD); a.emit(b, "pt_paint")   # the probe did not run (or the read path is broken): all red
    a.label("pt_ok")
    a.emit(cmp_imm, 5, 0); bc("pt_om", "ne")
    read_y(FACTS); a.emit(mov_reg, 6, 0); a.emit(movs_imm, 4, 1); a.emit(b, "pt_paint")
    a.label("pt_om")
    read_y(OMR); a.emit(mov_reg, 6, 0); a.emit(b, "pt_paint")
    a.label("pt_arm")                                                            # pages 2 / 3: bytes of the NRPN monitor
    a.emit(movw, 0, TAIL & 0xFFFF); a.emit(movt, 0, TAIL >> 16)
    a.emit(cmp_imm, 5, 2); a.emit(b_cond, "pt_p3", "ne")
    a.emit(ldrb_imm, 6, 0, 2); a.emit(lsls_imm, 6, 6, 8); a.emit(ldrb_imm, 1, 0, 3); a.emit(raw, h(0x430E | 0))   # orrs r6, r1 (below)
    a.emit(b, "pt_paint")
    a.label("pt_p3")
    a.emit(ldrb_imm, 6, 0, 0); a.emit(lsls_imm, 6, 6, 8); a.emit(ldrb_imm, 1, 0, 1); a.emit(raw, h(0x430E | 0))
    a.label("pt_paint")                                                          # r6 = 16-bit pattern, r7 = colour, r4 = bit order
    a.emit(movw, 0, 0xFFFF); a.emit(raw, h(0x4006))                              # ands r6, r0
    for vi, view in enumerate(VIEWS):
        a.emit(movw, 0, view & 0xFFFF); a.emit(movt, 0, view >> 16)
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, SP_VT & 0xFFFF); a.emit(movt, 2, SP_VT >> 16)
        a.emit(cmp_reg, 1, 2); bc(f"pt_v{vi}", "ne")                             # not a synth Preset view: leave it alone
        a.emit(bl, K["SP_LEDS"])                                                 # r0 = LED buffer
        a.emit(movs_imm, 1, 0)
        a.label(f"pt_l{vi}")
        a.emit(mov_reg, 2, 1); a.emit(cmp_imm, 4, 0); a.emit(b_cond, f"pt_b{vi}", "ne")
        a.emit(movs_imm, 2, 15); a.emit(raw, h(0x1A52 | 0))                      # subs r2, r2, r1 (15 - i)
        a.label(f"pt_b{vi}")
        a.emit(mov_reg, 3, 6); a.emit(lsrs_reg, 3, 2); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 3, 2)
        a.emit(movs_imm, 2, 0); a.emit(cmp_imm, 3, 0); a.emit(b_cond, f"pt_s{vi}", "eq"); a.emit(mov_reg, 2, 7)
        a.label(f"pt_s{vi}")
        a.emit(lsls_imm, 3, 1, 1); a.emit(adds_reg, 3, 3, 0); a.emit(strh_imm, 2, 3, 16)   # entries 8..23 = rows 2 and 3
        a.emit(adds_imm8, 1, 1); a.emit(cmp_imm, 1, 16); bc(f"pt_l{vi}", "lo")
        a.label(f"pt_v{vi}")
    a.label("pt_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_dtick19"])
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr; put c_dtick21 at the head of the DSP service chain; hook the incoming CC dispatcher."""
    import ct_fw
    import build_sc14 as s14
    import build_sc15 as s15
    import srcview
    import drums18
    BASE = ct_fw.APP_BASE
    assert srcview.METER
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    L = dict(c_gst=int(report["sc14"]["labels"]["c_gst"], 16), c_dtick19=p19["c_dtick19"])
    K = dict(S_PAINT=s15.S_PAINT, F_SRC=srcview.F_SRC, SP_LEDS=s15.SP_LEDS)
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"], hex(drums18.decode_bw(img, s14.SVC_HOOK))
    assert bytes(img[CC_FN - BASE:CC_FN - BASE + 4]) == CC_BYTES, bytes(img[CC_FN - BASE:CC_FN - BASE + 4]).hex()
    code, labels = arm_code(base_addr, L, K)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick21"])
    img[CC_FN - BASE:CC_FN - BASE + 4] = b_w(CC_FN, labels["c_nrpnlog"])
    return labels, code
