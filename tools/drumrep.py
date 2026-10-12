"""SC34: a drum sample replaced by the captured sample (the user, 2026-10-08): in the drum Preset view (the pads = the samples, page in [view + 0x20]),
Shift + a pad = "replace this sample?" (the pad blinks white), Shift + the same pad again = confirmed: the sample N = pad + 32 x page plays the capture from then on
(volatile: until the stock loads the sample table again, at power-up / a pack change).  Any pad without Shift, or Shift + another pad, cancels / moves the question.

  * pending question: bits 1-7 of byte +0x51 of the drum Preset view (= N + 1; bit 0 is SC08's chromatic flag, the other bits were never used);
  * confirmed: N + 1 goes into bits 23-29 of the sampler's S_SMT word (build_sc17.use_sampler2); the Master FX tick (c_smtick) sends REPN = N, CMD 4 to the DSP
    (sampler_dsp.V34: the capture is copied into one of 8 slots and the table entry X:$1D8D + 4 N points at it);
  * c_drp = slot 0 of the drum Preset view (in front of the present handler), c_drl = slot 7 (the LEDs: the asked pad blinks white on its page).
The chromatic keyboard (bit 0) is left alone: its pads are notes, not samples.

CLEARREP (SC37.6; the user, 2026-10-10: «Shift+sample … ya tenía asignación (selección silenciosa) ponemos otro atajo»): the modifier is Clear held instead of
Shift, so Shift + pad is the stock's silent selection again.  The Preset views accept Clear as a held button (bit 0 of [[MGR + 0x20] + 0xC]) and the stock does
nothing more with Clear + pad there (in emulation the RAM changes exactly as without Clear).
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw, adds_imm8, subs_imm8,  # noqa: E402
                   pop_list, push_list, raw, h, tst_reg, ands_reg, orrs_reg, bics_reg, adds_reg, str_imm, strh_reg, ldrb_w, strb_w)

DP_VT = 0x0805ABBC                 # drum Preset view vtable: slot 0 pad press, slot 7 LEDs
PARAM_GET = 0x0803542C
FLAG = 0x51
BLINK_ON, BLINK_OFF = 0x01, 0x00   # white / dark
CLEARREP = False                   # SC37.6: Clear + pad instead of Shift + pad (see above)
MGR = 0x20040B10                   # the controller; [MGR + 0x20] = the held-buttons object, +0xC its store (p0 bit 0 = Clear)


def use_clearrep():
    global CLEARREP
    CLEARREP = True


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L, K, prev_pad, prev_leds):
    a = Asm(base)
    S_SMT = K["S_SMT"]

    def sample_of(rd, pad):                       # rd = pad + 32 x the page of the view (r4); clobbers r0-r3
        a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
        a.emit(lsls_imm, 0, 0, 5); a.emit(adds_reg, rd, 0, pad)

    # ---- c_drp (view, pad, vel)
    a.label("c_drp")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(ldrb_w, 0, 4, FLAG); a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); a.emit(b_cond, "dr_fwd", "ne")     # chromatic: stock
    if CLEARREP:                                                                           # Clear held
        a.emit(movw, 0, MGR & 0xFFFF); a.emit(movt, 0, MGR >> 16); a.emit(ldr_imm, 0, 0, 0x20); a.emit(ldr_imm, 0, 0, 0xC); a.emit(movs_imm, 1, 0)
        a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    else:
        a.emit(bl, L["c_shift"])
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dr_ns", "eq")
    sample_of(7, 5)                                                                        # r7 = N
    a.emit(ldrb_w, 0, 4, FLAG); a.emit(lsrs_imm, 1, 0, 1); a.emit(mov_reg, 2, 7); a.emit(adds_imm8, 2, 1)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "dr_ok", "eq")
    a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(lsls_imm, 2, 2, 1); a.emit(orrs_reg, 0, 2); a.emit(strb_w, 0, 4, FLAG)   # asked
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dr_ok")                                                                       # confirmed: the request for the tick
    a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(strb_w, 0, 4, FLAG)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dr_x", "eq")
    a.emit(ldr_imm, 1, 0, S_SMT); a.emit(movw, 2, 0); a.emit(movt, 2, 0x3F80); a.emit(bics_reg, 1, 2)
    a.emit(mov_reg, 3, 7); a.emit(adds_imm8, 3, 1); a.emit(lsls_imm, 3, 3, 23); a.emit(orrs_reg, 1, 3); a.emit(str_imm, 1, 0, S_SMT)
    a.label("dr_x"); a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("dr_ns")                                                                       # a pad without Shift: no question pending
    a.emit(ldrb_w, 0, 4, FLAG); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(strb_w, 0, 4, FLAG)
    a.label("dr_fwd")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, prev_pad)

    # ---- c_drl (view) -> LED buffer: the asked pad blinks on its page
    a.label("c_drl")
    a.emit(push_list, [4, 5, 6], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, prev_leds); a.emit(mov_reg, 5, 0)
    a.emit(ldrb_w, 0, 4, FLAG); a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); a.emit(b_cond, "dl_x", "ne")
    a.emit(lsrs_imm, 6, 0, 1); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "dl_x", "eq"); a.emit(subs_imm8, 6, 1)   # r6 = N
    a.emit(ldr_imm, 0, 4, 0x20); a.emit(movs_imm, 1, 0); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 0, 0, 0)
    a.emit(lsrs_imm, 1, 6, 5); a.emit(cmp_reg, 1, 0); a.emit(b_cond, "dl_x", "ne")                         # not on this page
    a.emit(bl, L["c_now"]); a.emit(lsrs_imm, 0, 0, 8); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(movs_imm, 2, BLINK_OFF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "dl_b", "eq"); a.emit(movs_imm, 2, BLINK_ON)
    a.label("dl_b")
    a.emit(movs_imm, 1, 31); a.emit(ands_reg, 6, 1); a.emit(lsls_imm, 6, 6, 1); a.emit(raw, h(0x5200 | 6 << 6 | 5 << 3 | 2))   # strh r2,[r5,r6]
    a.label("dl_x"); a.emit(mov_reg, 0, 5); a.emit(pop_list, [4, 5, 6], pc=True)
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    import build_sc17 as B
    BASE = ct_fw.APP_BASE
    assert B.SMP2
    L = dict(c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16), c_shift=int(report["sc15"]["labels"]["c_shift"], 16),
             c_now=int(report["sc14"]["labels"]["c_now"], 16))
    prev_pad = struct.unpack_from("<I", img, DP_VT - BASE)[0] & ~1
    prev_leds = struct.unpack_from("<I", img, DP_VT + 0x1C - BASE)[0] & ~1
    code, labels = arm_code(base_addr, L, dict(S_SMT=B.S_SMT), prev_pad, prev_leds)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, DP_VT - BASE, labels["c_drp"] | 1)
    struct.pack_into("<I", img, DP_VT + 0x1C - BASE, labels["c_drl"] | 1)
    return labels, code, dict(prev_pad=hex(prev_pad), prev_leds=hex(prev_leds))
