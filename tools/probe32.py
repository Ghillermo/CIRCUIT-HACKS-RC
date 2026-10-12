"""SC32D (DIAGNOSTIC): the display of the external Y memory probe (ARM side; the DSP side is tools/probe32_dsp.py).

While the synth source view is open (Synth 1 / 2 pressed twice: the SC19.1 view, flag bit 2 of the SC14 byte +20) the pad rows 2 and 3 (pads 9-24, entries 8..23 of the LED
buffer of the synth Preset view) cycle through four pages of 4 s (page = uptime >> 12 & 3).  The first 0.5 s of a page is its MARK: one white pad, pad 9 + page.  Then:
  page 0  zones 0-15 (pad 9 = zone 0)             page 1  zones 16-29 (pads 9-22), pads 23 / 24 = Y:$5BF000 / $5C0000
  page 2  pads 9-14 = Y:$600000, $680000, $700000, $780000, $880000, $8FF000      page 3  the number of finished sweeps, 16 bits in white (pad 9 = bit 15)
State colours (pages 0-2): dark = not visited yet, red = write failed, blue = alias, magenta = changing (a live buffer), yellow = static content, green = free.
If the DSP magic ($C0FFEE) does not read back, the rows are all red (the probe did not run or the DSP read path failed).
The DSP service chain head becomes c_dtick32 (then SC19's c_dtick19).  At most three DSP reads per call (magic + two words), all with the stock read 0x08029344.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, lsrs_reg, muls, subs_reg, strh_reg, adds_reg)
import probe32_dsp as PD  # noqa: E402

DSP_READ = 0x08029344
SP_VT = 0x0805AC9C
VIEWS = (0x20042980, 0x20042A34)               # synth Preset views (Synth 1 / Synth 2)
HAL_TICK = 0x2000081C
WHITE, RED, BLUE, MAGENTA, YELLOW, GREEN = 0x01, 0x05, 0x13, 0x32, 0x2D, 0x19
STATE_COL = {PD.S_NONE: 0, PD.S_FAIL: RED, PD.S_ALIAS: BLUE, PD.S_CHG: MAGENTA, PD.S_STATIC: YELLOW, PD.S_FREE: GREEN}
ALL_RED = int("1" * 8, 8)                      # eight codes 1 = 0x249249
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

    def read_y_r1():                            # r0 = the 24-bit word of Y:(r1 & 0x7FFF) (r1 = 0x8000 | address)
        a.emit(movs_imm, 0, 0); a.emit(bl, DSP_READ); a.emit(lsrs_imm, 0, 0, 8)

    # ---- c_dtick32: head of the DSP service chain (in front of SC19's c_dtick19)
    a.label("c_dtick32")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, L["c_gst"]); a.emit(cmp_imm, 0, 0); bc("pt_out", "eq")
    a.emit(ldrb_imm, 1, 0, S_PAINT); a.emit(movs_imm, 2, F_SRC); a.emit(tst_reg, 1, 2); bc("pt_out", "eq")
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 5, 0, 12); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 5, 1)       # r5 = page 0..3
    a.emit(lsrs_imm, 0, 0, 9); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 0, 1)        # first 0.5 s of the page: its mark
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "pt_nm", "ne")
    a.emit(movs_imm, 4, 0); a.emit(movs_imm, 6, 0); a.emit(movs_imm, 7, 0)
    a.emit(movs_imm, 0, 0x80); a.emit(lsrs_reg, 0, 5); a.emit(mov_reg, 6, 0)          # row 2: bit 7 - page (pad 9 + page)
    a.emit(b, "pt_paint")
    a.label("pt_nm")
    a.emit(movw, 1, 0x8000 | PD.YR); read_y_r1()
    a.emit(movw, 1, PD.MAGIC & 0xFFFF); a.emit(movt, 1, PD.MAGIC >> 16); a.emit(cmp_reg, 0, 1); bc("pt_ok", "eq")
    a.emit(movs_imm, 4, 3); a.emit(movw, 6, ALL_RED & 0xFFFF); a.emit(movt, 6, ALL_RED >> 16); a.emit(mov_reg, 7, 6); a.emit(b, "pt_paint")
    a.label("pt_ok")
    a.emit(cmp_imm, 5, 3); a.emit(b_cond, "pt_st", "ne")
    a.emit(movw, 1, 0x8000 | PD.SWEEP); read_y_r1()                                  # page 3: the sweep count in white
    a.emit(movs_imm, 4, 0); a.emit(movs_imm, 1, 0xFF); a.emit(mov_reg, 7, 0); a.emit(ands_reg, 7, 1)
    a.emit(lsrs_imm, 6, 0, 8); a.emit(ands_reg, 6, 1); a.emit(b, "pt_paint")
    a.label("pt_st")                                                                  # pages 0-2: PK[2 page] (row 2), PK[2 page + 1] (row 3, none on page 2)
    a.emit(movs_imm, 4, 3)
    a.emit(lsls_imm, 2, 5, 1); a.emit(movw, 1, 0x8000 | PD.PK); a.emit(adds_reg, 1, 1, 2); a.emit(mov_reg, 7, 1)
    read_y_r1(); a.emit(mov_reg, 6, 0)
    a.emit(movs_imm, 0, 0); a.emit(cmp_imm, 5, 2); a.emit(b_cond, "pt_r3", "eq")
    a.emit(mov_reg, 1, 7); a.emit(adds_imm8, 1, 1); read_y_r1()
    a.label("pt_r3"); a.emit(mov_reg, 7, 0)
    a.label("pt_paint")                                                               # r6 / r7 = the words of rows 2 / 3, r4 bit 0 / 1 = state codes (else 8 bits, MSB first)
    for vi, view in enumerate(VIEWS):
        a.emit(movw, 0, view & 0xFFFF); a.emit(movt, 0, view >> 16)
        a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, SP_VT & 0xFFFF); a.emit(movt, 2, SP_VT >> 16)
        a.emit(cmp_reg, 1, 2); bc(f"pt_v{vi}", "ne")                                   # not a synth Preset view: leave it alone
        a.emit(bl, K["SP_LEDS"]); a.emit(mov_reg, 5, 0)                               # r5 = LED buffer
        a.emit(adds_imm8, 0, 16); a.emit(mov_reg, 1, 6); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 2, 4); a.emit(bl, "c_p8")
        a.emit(mov_reg, 0, 5); a.emit(adds_imm8, 0, 32); a.emit(mov_reg, 1, 7); a.emit(movs_imm, 2, 2); a.emit(ands_reg, 2, 4); a.emit(bl, "c_p8")
        a.label(f"pt_v{vi}")
    a.label("pt_out")
    a.emit(raw, popw([4, 5, 6, 7], lr=True))
    a.emit(b_w, L["c_dtick19"])

    # ---- c_p8 (r0 = 8 LED halfwords, r1 = word, r2 != 0: eight 3-bit state codes (pad j = bits 3j..3j+2), else bits 7..0 in white)
    a.label("c_p8")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(movs_imm, 3, 0)
    a.label("p8_l")
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "p8_bits", "eq")
    a.emit(movs_imm, 4, 3); a.emit(muls, 4, 3); a.emit(mov_reg, 5, 1); a.emit(lsrs_reg, 5, 4); a.emit(movs_imm, 4, 7); a.emit(ands_reg, 5, 4)
    for code_, col in STATE_COL.items():                                              # r5 = code -> colour
        if code_ == 0: continue
        a.emit(cmp_imm, 5, code_); a.emit(b_cond, f"p8_c{code_}", "ne"); a.emit(movs_imm, 5, col); a.emit(b, "p8_st")
        a.label(f"p8_c{code_}")
    a.emit(movs_imm, 5, 0); a.emit(b, "p8_st")
    a.label("p8_bits")
    a.emit(movs_imm, 4, 7); a.emit(subs_reg, 4, 4, 3); a.emit(mov_reg, 5, 1); a.emit(lsrs_reg, 5, 4); a.emit(movs_imm, 4, 1); a.emit(ands_reg, 5, 4)
    a.emit(cmp_imm, 5, 0); a.emit(b_cond, "p8_st", "eq"); a.emit(movs_imm, 5, WHITE)
    a.label("p8_st")
    a.emit(lsls_imm, 4, 3, 1); a.emit(strh_reg, 5, 0, 4)
    a.emit(adds_imm8, 3, 1); a.emit(cmp_imm, 3, 8); a.emit(b_cond, "p8_l", "lo")
    a.emit(pop_list, [4, 5], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    """Append the code at base_addr; put c_dtick32 at the head of the DSP service chain."""
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
    code, labels = arm_code(base_addr, L, K)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick32"])
    return labels, code
