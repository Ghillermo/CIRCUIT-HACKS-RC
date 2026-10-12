"""SC20: VCF / VCA for the audio inputs of the MIDI tracks (ARM side; the DSP side is tools/vcf20_dsp.py).

A toggle pad (pad 26, the one right of the patch flip) in the Preset view of MIDI 1 / MIDI 2 switches the mode of that track: the audio input of the track (line input 1 / 2, or the reverb /
delay return when the Setup sends it to strip 3 / 4) goes through a bipolar VCF, drive + saturation and a VCA with an ADSR envelope and an LFO, in front of the mixer strip.
Patch flip and this mode exclude each other (turning one on turns the other off).
  * the 8 knobs of the track are the VCF / VCA controls (Shift = second layer, see KNOBS); the track's notes (sequenced, recorded or played) are still sent as MIDI as always and also
    open the gate of the envelope (the note wrappers of the note vtable 0x08059FC4 / C8 count the held notes);
  * state: the 75 reserved bytes at the end of the global settings record (settings object 0x2003974C + 0x3D ...): the toggles, 2 x 16 values, and the volatile bookkeeping (held notes, dirty
    bits, tags); saved by the stock save 0x0802D2AC (throttled, called from the knob / pad handlers: the UI thread, like the stock listener); the values belong to the unit, not to the project;
  * the DSP is told through a mailbox at X:$3B80 + 48 t (tag << 23 | code << 16 | value): one message per voice per tick of the DSP service chain (head of the chain, in front of SC19's tick).
Tail layout (offset from SETOBJ + 0x3D): +0 flags (bit 0 MIDI 1 on, bit 1 MIDI 2 on, bit 7 initialised), +1..16 values of track 0, +17..32 of track 1 (code 1..16, signed bytes), +33 / +41 volatile blocks
of 8 bytes [held notes, note, velocity, aux (bit 0 ACT, 1 NOTE, 2 VEL, 3 GATE, 4 TRIG dirty), dirty mask lo, hi, tag, -], +49 time of the last save (units of 32 ms).
Boot / project load: the Master FX block byte 179 bit 3 (zero when the block is created = at power-up) marks "initialised this session": the volatile blocks are cleared and everything is sent.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrh_imm, ldrb_w, strb_w, strb_imm, strh_imm, lsls_imm, lsrs_imm, mov_reg,  # noqa: E402
                   movs_imm, movt, movw, pop_list, push_list, raw, h, adds_imm8, subs_imm8, adds_reg, subs_reg, ands_reg, orrs_reg, bics_reg,
                   eors_reg, muls, tst_reg, lsls_reg, lsrs_reg, str_imm, ldr_sp)

SETOBJ = 0x2003974C
TAIL = SETOBJ + 0x3D
SAVE_FN = 0x0802D2AC
CTX_PTR = 0x200069E4
STOCK_KNOB = 0x0804C062
STOCK_LEDS = 0x08047592
TMPL_VT_LEDS = 0x0805AE5C + 0x1C
AC64_VT = 0x0805AC64
NOTE_VT = (0x08059FC4, 0x08059FC8)
T_PAD_SITE, T_PAD_RET, T_DRAW = 0x0804D59E, 0x0804D5C0, 0x0804D5CA
PARAM_GET, PARAM_PTR, COMMIT = 0x0803542C, 0x080354FA, 0x080353C0
DSP_WRITE = 0x080292F8
HAL_TICK = 0x2000081C
VB0, VBS = 0x3B80, 48
FLAGS_BYTE, B_BOOT = 179, 8                      # persist19.FLAGS in the Master FX block; bit 3 = "initialised this session"
PAD_VCF = 25                                      # pad 26 (index 25); the patch flip is index 24
COL_ON, COL_OFF = 0x13, 0x14                      # yellow bright / dim (the RGB table of 0x0803423C: 19 = 255, 221, 68)
COL_TRACK = (0x09, 0x3B)                          # MIDI 1 orange, MIDI 2 purple (the colours of the stock dynamic codes 0xD1 / 0xD9)
DEFAULTS = (0, 0, 0, 0, 0, 40, 100, 40, 0, 127, 40, 0, 0, 0, 0, 0)   # FILT RES ENVF LFOF ATK DEC SUS REL DRIVE LEVEL LRATE LFOV LSHAPE KEY VELE VMODE
BIPOLAR_MASK = (1 << 0) | (1 << 2) | (1 << 3) | (1 << 13)          # codes 1 (FILT), 3 (ENVF), 4 (LFOF), 14 (KEY) -> bit code - 1
O_FLAGS, O_PAR, O_RT = 0, 1, 33
RT_CNT, RT_NOTE, RT_VEL, RT_AUX, RT_DLO, RT_DHI, RT_TAG = range(7)
SIGNED = False                                    # SC20.1: byte +50 of the tail = SIG_VAL once the state was initialised by us
O_SIG, SIG_VAL = 50, 0xA5
O_SAVED = 49                                      # 8-bit time of the last save (units of 32 ms)
SAVE_MS = 700
INV = {"eq": "ne", "ne": "eq", "cc": "cs", "cs": "cc", "lo": "hs", "hs": "lo", "hi": "ls", "ls": "hi",
       "ge": "lt", "lt": "ge", "gt": "le", "le": "gt", "mi": "pl", "pl": "mi"}


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def pushw(regs, lr=False): return h(0xE92D) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def ldrsb_w(rt, rn, imm12): return h(0xF990 | rn) + h(rt << 12 | imm12)          # LDRSB.W Rt,[Rn,#imm12]
def sxtb(rd, rm): return h(0xB240 | rm << 3 | rd)


def arm_code(base, L):
    """L: c_shift, c_gfst, c_dtick19 (the chain), c_tpad, c_tleds, c_settings (SC06), c_non, c_noff (SC06)."""
    a = Asm(base)
    zc = [0]

    def bc(target, cond):
        zc[0] += 1; n = f"_v{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    def tail(rd):
        a.emit(movw, rd, TAIL & 0xFFFF); a.emit(movt, rd, TAIL >> 16)

    # ---- c_vtrack(r0 = macro handler) -> r0 = 0 / 1 (MIDI 1 / MIDI 2) or 0xFF; clobbers r1, r2
    a.label("c_vtrack")
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x2C); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "vt_no", "eq")
    a.emit(raw, h(0xF8D1) + h(2 << 12 | (0x148 + 8)))                            # ldr.w r2,[r1,#0x150]  (track 2 = MIDI 1)
    a.emit(cmp_reg, 2, 0); a.emit(b_cond, "vt_0", "eq")
    a.emit(raw, h(0xF8D1) + h(2 << 12 | (0x148 + 12)))                           # ldr.w r2,[r1,#0x154]  (track 3 = MIDI 2)
    a.emit(cmp_reg, 2, 0); a.emit(b_cond, "vt_1", "eq")
    a.label("vt_no"); a.emit(movs_imm, 0, 0xFF); a.emit(raw, h(0x4770))
    a.label("vt_0"); a.emit(movs_imm, 0, 0); a.emit(raw, h(0x4770))
    a.label("vt_1"); a.emit(movs_imm, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_von(r0 = track) -> r0 = 0 / 1; clobbers r1
    a.label("c_von")
    tail(1)
    a.emit(ldrb_w, 1, 1, O_FLAGS); a.emit(lsrs_reg, 1, 0); a.emit(movs_imm, 0, 1); a.emit(ands_reg, 0, 1); a.emit(raw, h(0x4770))

    # ---- c_vlvl(r0 = track, r1 = code 1..16) -> r0 = brightness 0..127; clobbers r1-r3
    a.label("c_vlvl")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    tail(2); a.emit(lsls_imm, 3, 0, 4); a.emit(adds_reg, 3, 3, 2); a.emit(adds_reg, 3, 3, 1)             # r3 = TAIL + 16 t + code  (= +1 + 16 t + code - 1)
    a.emit(raw, ldrsb_w(0, 3, 0))
    a.emit(cmp_imm, 4, 13); a.emit(b_cond, "vl_sh", "eq")
    a.emit(cmp_imm, 4, 16); a.emit(b_cond, "vl_md", "eq")
    a.emit(movs_imm, 2, 0); a.emit(movw, 2, BIPOLAR_MASK); a.emit(subs_imm8, 4, 1); a.emit(lsrs_reg, 2, 4); a.emit(movs_imm, 3, 1); a.emit(ands_reg, 2, 3)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "vl_uni", "eq")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vl_bp", "ge"); a.emit(raw, h(0x43C0))                          # mvns r0, r0 : -v - 1
    a.label("vl_bp"); a.emit(lsls_imm, 0, 0, 1); a.emit(cmp_imm, 0, 126); a.emit(b_cond, "vl_x", "ls"); a.emit(movs_imm, 0, 126); a.emit(b, "vl_x")
    a.label("vl_uni")
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vl_x", "ge"); a.emit(movs_imm, 0, 0); a.emit(b, "vl_x")
    a.label("vl_sh")
    a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(movs_imm, 1, 42); a.emit(muls, 0, 1); a.emit(b, "vl_x")
    a.label("vl_md")
    a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(b_cond, "vl_x", "eq"); a.emit(movs_imm, 0, 127)
    a.label("vl_x")
    a.emit(pop_list, [4], pc=True)

    # ---- c_vsave: the stock settings save, at most every SAVE_MS (8-bit time in units of 32 ms); clobbers r0-r3
    a.label("c_vsave")
    a.emit(push_list, [4], lr=True)
    a.emit(movw, 0, HAL_TICK & 0xFFFF); a.emit(movt, 0, HAL_TICK >> 16); a.emit(ldr_imm, 0, 0, 0)
    a.emit(lsrs_imm, 0, 0, 5); a.emit(movs_imm, 1, 0xFF); a.emit(ands_reg, 0, 1); a.emit(mov_reg, 4, 0)             # r4 = now (8 bit)
    tail(1); a.emit(ldrb_w, 2, 1, O_SAVED); a.emit(subs_reg, 2, 0, 2); a.emit(movs_imm, 3, 0xFF); a.emit(ands_reg, 2, 3)   # r2 = (now - last) & 0xFF
    a.emit(cmp_imm, 2, SAVE_MS // 32); a.emit(b_cond, "vs_x", "lo")
    a.emit(strb_w, 4, 1, O_SAVED)
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.label("vs_x"); a.emit(pop_list, [4], pc=True)

    # ---- c_vmark(r0 = track, r1 = code 1..16): dirty bit
    a.label("c_vmark")
    tail(2); a.emit(lsls_imm, 3, 0, 3); a.emit(adds_reg, 2, 2, 3); a.emit(adds_imm8, 2, O_RT)                  # r2 = volatile block
    a.emit(movs_imm, 3, 1); a.emit(subs_imm8, 1, 1); a.emit(lsls_reg, 3, 1)                                  # r3 = 1 << (code - 1)
    a.emit(ldrb_imm, 0, 2, RT_DLO); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_DLO)
    a.emit(lsrs_imm, 3, 3, 8); a.emit(ldrb_imm, 0, 2, RT_DHI); a.emit(orrs_reg, 0, 3); a.emit(strb_imm, 0, 2, RT_DHI)
    a.emit(raw, h(0x4770))

    # ---- c_vknob(obj, knob, delta): slot 4 of the macro handlers of the tracks 0..3: the VCF / VCA controls of a MIDI track whose mode is on, stock otherwise
    a.label("c_vknob")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
    a.emit(bl, "c_vtrack"); a.emit(cmp_imm, 0, 0xFF); a.emit(b_cond, "vk_stock", "eq")
    a.emit(mov_reg, 7, 0); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_stock", "eq")
    a.emit(bl, L["c_shift"]); a.emit(adds_imm8, 5, 1); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_ns", "eq"); a.emit(adds_imm8, 5, 8)
    a.label("vk_ns")                                                              # r5 = code 1..16, r7 = track, r6 = delta
    tail(2); a.emit(lsls_imm, 3, 7, 4); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5)                  # r2 = address of the value
    a.emit(raw, ldrsb_w(4, 2, 0))                                                 # r4 = old value
    a.emit(cmp_imm, 5, 13); a.emit(b_cond, "vk_shape", "eq")
    a.emit(cmp_imm, 5, 16); a.emit(b_cond, "vk_mode", "eq")
    a.emit(adds_reg, 0, 4, 6)                                                     # new = old + delta
    a.emit(movw, 3, BIPOLAR_MASK); a.emit(subs_imm8, 5, 1); a.emit(lsrs_reg, 3, 5); a.emit(adds_imm8, 5, 1); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 3, 1)
    a.emit(cmp_imm, 3, 0); a.emit(b_cond, "vk_uni", "eq")
    a.emit(cmp_imm, 0, 63); a.emit(b_cond, "vk_b1", "le"); a.emit(movs_imm, 0, 63)
    a.label("vk_b1"); a.emit(movs_imm, 1, 0); a.emit(subs_imm8, 1, 64); a.emit(cmp_reg, 0, 1); a.emit(b_cond, "vk_set", "ge"); a.emit(mov_reg, 0, 1); a.emit(b, "vk_set")
    a.label("vk_uni")
    a.emit(cmp_imm, 0, 127); a.emit(b_cond, "vk_u1", "le"); a.emit(movs_imm, 0, 127)
    a.label("vk_u1"); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk_set", "ge"); a.emit(movs_imm, 0, 0); a.emit(b, "vk_set")
    a.label("vk_shape")                                                           # shape: one step per turn, 0..3 wrapping (r0 = new, r4 = old stays)
    a.emit(mov_reg, 0, 4); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_sd", "le"); a.emit(adds_imm8, 0, 1); a.emit(b, "vk_sw")
    a.label("vk_sd"); a.emit(subs_imm8, 0, 1)
    a.label("vk_sw"); a.emit(movs_imm, 1, 3); a.emit(ands_reg, 0, 1); a.emit(b, "vk_set")
    a.label("vk_mode")                                                            # VCA mode: right = gate (1), left = open (0)
    a.emit(movs_imm, 0, 0); a.emit(cmp_imm, 6, 0); a.emit(b_cond, "vk_set", "le"); a.emit(movs_imm, 0, 1)
    a.label("vk_set")
    a.emit(cmp_reg, 0, 4); a.emit(b_cond, "vk_done", "eq")
    tail(2); a.emit(lsls_imm, 3, 7, 4); a.emit(adds_reg, 2, 2, 3); a.emit(adds_reg, 2, 2, 5); a.emit(strb_imm, 0, 2, 0)
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 5); a.emit(bl, "c_vmark")
    a.emit(bl, "c_vsave")
    a.label("vk_done")
    a.emit(pop_list, [4, 5, 6, 7], pc=True)
    a.label("vk_stock")
    a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, STOCK_KNOB)

    # ---- c_vkleds(obj): slot 7 of the macro handlers: the stock buffer, then (MIDI track with the mode on) the track colour with the brightness of each value
    a.label("c_vkleds")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, STOCK_LEDS); a.emit(mov_reg, 5, 0)
    a.emit(mov_reg, 0, 4); a.emit(bl, "c_vtrack"); a.emit(cmp_imm, 0, 0xFF); bc("vk2_x", "eq")
    a.emit(mov_reg, 7, 0); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc("vk2_x", "eq")
    a.emit(movs_imm, 6, COL_TRACK[0]); a.emit(cmp_imm, 7, 0); a.emit(b_cond, "vk2_c", "eq"); a.emit(movs_imm, 6, COL_TRACK[1])
    a.label("vk2_c")
    a.emit(bl, L["c_shift"]); a.emit(movs_imm, 4, 0); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vk2_l", "eq"); a.emit(movs_imm, 4, 8)
    a.label("vk2_l")                                                              # r4 = code - 1 (0..7, or 8..15 with Shift)
    a.emit(mov_reg, 0, 7); a.emit(mov_reg, 1, 4); a.emit(adds_imm8, 1, 1); a.emit(bl, "c_vlvl")
    a.emit(adds_imm8, 0, 2); a.emit(lsls_imm, 0, 0, 8); a.emit(orrs_reg, 0, 6)
    a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 4); a.emit(lsls_imm, 1, 1, 1); a.emit(adds_reg, 1, 1, 5); a.emit(strh_imm, 0, 1, 0)
    a.emit(adds_imm8, 4, 1); a.emit(movs_imm, 1, 7); a.emit(ands_reg, 1, 4); bc("vk2_l", "ne")
    a.label("vk2_x")
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_vset(r0 = track, r1 = on): the toggle bit; ACT is sent again; switching on sends every value
    a.label("c_vset")
    a.emit(push_list, [4], lr=True)
    a.emit(mov_reg, 4, 1)
    tail(2); a.emit(movs_imm, 1, 1); a.emit(lsls_reg, 1, 0); a.emit(ldrb_w, 3, 2, O_FLAGS); a.emit(bics_reg, 3, 1)
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "vs2_w", "eq"); a.emit(orrs_reg, 3, 1)
    a.label("vs2_w"); a.emit(strb_w, 3, 2, O_FLAGS)
    a.emit(lsls_imm, 1, 0, 3); a.emit(adds_reg, 1, 1, 2); a.emit(adds_imm8, 1, O_RT)
    a.emit(ldrb_imm, 3, 1, RT_AUX); a.emit(movs_imm, 2, 1); a.emit(orrs_reg, 3, 2); a.emit(strb_imm, 3, 1, RT_AUX)
    a.emit(cmp_imm, 4, 0); a.emit(b_cond, "vs2_x", "eq")
    a.emit(movs_imm, 3, 0xFF); a.emit(strb_imm, 3, 1, RT_DLO); a.emit(strb_imm, 3, 1, RT_DHI)
    a.label("vs2_x"); a.emit(pop_list, [4], pc=True)

    # ---- c_vpad: b.w from the pad hook of the template (Preset) view of the MIDI tracks (r0 = view, r5 = pad); r4 is free
    a.label("c_vpad")
    a.emit(cmp_imm, 5, PAD_VCF); a.emit(b_cond, "vp_tog", "eq")
    a.emit(cmp_imm, 5, 24); a.emit(b_cond, "vp_flip", "eq")
    a.label("vp_fwd")
    a.emit(b_w, L["c_tpad"])
    a.label("vp_flip")                                                            # the patch flip is pressed: if it is off now it turns on, so this mode goes off
    a.emit(raw, pushw([6, 7], lr=True))
    a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc("vpf_x", "eq")
    a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("vpf_x", "eq")
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_GET); a.emit(ldr_imm, 0, 0, 0); a.emit(lsrs_imm, 0, 0, 26); a.emit(lsrs_reg, 0, 6); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1)
    a.emit(cmp_imm, 0, 0); bc("vpf_x", "ne")                                      # the flip is on now: it turns off
    a.emit(mov_reg, 0, 6); a.emit(movs_imm, 1, 0); a.emit(bl, "c_vset")
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.label("vpf_x")
    a.emit(mov_reg, 0, 4)                                                         # c_tpad wants the view in r0
    a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, L["c_tpad"])
    a.label("vp_tog")
    a.emit(raw, pushw([6, 7], lr=True))
    a.emit(mov_reg, 4, 0); a.emit(ldrb_imm, 6, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 6, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_von"); a.emit(movs_imm, 1, 1); a.emit(eors_reg, 1, 0); a.emit(mov_reg, 7, 1)
    a.emit(mov_reg, 0, 6); a.emit(bl, "c_vset")
    a.emit(cmp_imm, 7, 0); bc("vpt_s", "eq")
    a.emit(bl, L["c_settings"]); a.emit(cmp_imm, 0, 0); bc("vpt_s", "eq")          # on: the patch flip of this track goes off
    a.emit(movs_imm, 1, 2); a.emit(bl, PARAM_PTR); a.emit(ldr_imm, 1, 0, 0)
    a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 26); a.emit(lsls_reg, 3, 6); a.emit(bics_reg, 1, 3); a.emit(str_imm, 1, 0, 0)
    a.emit(bl, L["c_settings"]); a.emit(bl, COMMIT)
    a.label("vpt_s")
    a.emit(movw, 0, SETOBJ & 0xFFFF); a.emit(movt, 0, SETOBJ >> 16); a.emit(bl, SAVE_FN)
    a.emit(raw, popw([6, 7], lr=True)); a.emit(b_w, T_PAD_RET)

    # ---- c_vleds: slot 7 of the template view: SC06's buffer (the patch flip pad), then pad 26 = this mode
    a.label("c_vleds")
    a.emit(push_list, [4, 5], lr=True)
    a.emit(mov_reg, 4, 0); a.emit(bl, L["c_tleds"]); a.emit(mov_reg, 5, 0)
    a.emit(ldrb_imm, 0, 4, 0x10); a.emit(movs_imm, 1, 1); a.emit(ands_reg, 0, 1); a.emit(bl, "c_von")
    a.emit(movs_imm, 1, COL_OFF); a.emit(cmp_imm, 0, 0); a.emit(b_cond, "vle_s", "eq"); a.emit(movs_imm, 1, COL_ON)
    a.label("vle_s"); a.emit(strh_imm, 1, 5, 2 * PAD_VCF)
    a.emit(mov_reg, 0, 5)
    a.emit(pop_list, [4, 5], pc=True)

    # ---- note wrappers (vtable 0x08059FC4 / C8): count the held notes of an active MIDI track, then SC06's wrappers
    for name, orig in (("c_vnon", "c_non"), ("c_vnoff", "c_noff")):
        on = name == "c_vnon"
        a.label(name)
        a.emit(raw, pushw([0, 1, 2, 3, 4, 5, 6], lr=True))
        a.emit(mov_reg, 4, 1); a.emit(subs_imm8, 4, 2); a.emit(cmp_imm, 4, 1); bc(name + "_f", "hi")
        a.emit(mov_reg, 0, 4); a.emit(bl, "c_von"); a.emit(cmp_imm, 0, 0); bc(name + "_f", "eq")
        tail(5); a.emit(lsls_imm, 6, 4, 3); a.emit(adds_reg, 5, 5, 6); a.emit(adds_imm8, 5, O_RT)
        a.emit(ldrb_imm, 0, 5, RT_CNT)
        if on:
            a.emit(cmp_imm, 0, 15); a.emit(b_cond, name + "_c", "hs"); a.emit(adds_imm8, 0, 1)
            a.label(name + "_c"); a.emit(strb_imm, 0, 5, RT_CNT)
            a.emit(raw, ldr_sp(2, 8)); a.emit(raw, ldr_sp(3, 12)); a.emit(strb_imm, 2, 5, RT_NOTE); a.emit(strb_imm, 3, 5, RT_VEL)
            a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 0x1E); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX)
        else:
            a.emit(cmp_imm, 0, 0); bc(name + "_f", "eq")
            a.emit(subs_imm8, 0, 1); a.emit(strb_imm, 0, 5, RT_CNT); bc(name + "_f", "ne")
            a.emit(ldrb_imm, 0, 5, RT_AUX); a.emit(movs_imm, 1, 8); a.emit(orrs_reg, 0, 1); a.emit(strb_imm, 0, 5, RT_AUX)
        a.label(name + "_f")
        a.emit(pop_list, [0, 1, 2, 3]); a.emit(raw, popw([4, 5, 6], lr=True)); a.emit(b_w, L[orig])

    # ---- c_vsend(r5 = tail, r6 = track): one mailbox message of the voice, if anything is pending; clobbers r0-r4, r7
    a.label("c_vsend")
    a.emit(push_list, [4], lr=True)
    a.emit(lsls_imm, 7, 6, 3); a.emit(adds_reg, 7, 7, 5); a.emit(adds_imm8, 7, O_RT)
    a.emit(ldrb_imm, 0, 7, RT_AUX)
    a.emit(movs_imm, 1, 1); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_1", "eq")                                  # ACT = the toggle bit of the track
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX)
    a.emit(ldrb_w, 1, 5, O_FLAGS); a.emit(lsrs_reg, 1, 6); a.emit(movs_imm, 2, 1); a.emit(ands_reg, 1, 2); a.emit(movs_imm, 0, 19); a.emit(b, "sd_send")
    a.label("sd_1")
    a.emit(movs_imm, 1, 2); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_2", "eq")                                  # NOTE
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_NOTE); a.emit(movs_imm, 0, 18); a.emit(b, "sd_send")
    a.label("sd_2")
    a.emit(movs_imm, 1, 4); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_3", "eq")                                  # VEL
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_VEL); a.emit(movs_imm, 0, 20); a.emit(b, "sd_send")
    a.label("sd_3")
    a.emit(movs_imm, 1, 8); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_4", "eq")                                  # GATE = held notes > 0
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(ldrb_imm, 1, 7, RT_CNT); a.emit(movs_imm, 2, 0)
    a.emit(cmp_imm, 1, 0); a.emit(b_cond, "sd_g", "eq"); a.emit(movs_imm, 2, 1)
    a.label("sd_g"); a.emit(mov_reg, 1, 2); a.emit(movs_imm, 0, 17); a.emit(b, "sd_send")
    a.label("sd_4")
    a.emit(movs_imm, 1, 0x10); a.emit(tst_reg, 0, 1); a.emit(b_cond, "sd_5", "eq")                               # TRIG
    a.emit(bics_reg, 0, 1); a.emit(strb_imm, 0, 7, RT_AUX); a.emit(movs_imm, 1, 1); a.emit(movs_imm, 0, 21); a.emit(b, "sd_send")
    a.label("sd_5")
    a.emit(ldrb_imm, 0, 7, RT_DLO); a.emit(ldrb_imm, 1, 7, RT_DHI); a.emit(lsls_imm, 1, 1, 8); a.emit(orrs_reg, 0, 1)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "sd_x", "eq")
    a.emit(movs_imm, 2, 0)
    a.label("sd_f")
    a.emit(movs_imm, 3, 1); a.emit(tst_reg, 0, 3); a.emit(b_cond, "sd_found", "ne"); a.emit(lsrs_imm, 0, 0, 1); a.emit(adds_imm8, 2, 1); a.emit(b, "sd_f")
    a.label("sd_found")                                                                                          # r2 = j: value of code j + 1
    a.emit(movs_imm, 4, 1); a.emit(lsls_reg, 4, 2)
    a.emit(lsls_imm, 1, 6, 4); a.emit(adds_reg, 1, 1, 5); a.emit(adds_reg, 1, 1, 2); a.emit(raw, ldrsb_w(1, 1, 1))
    a.emit(movs_imm, 0, 0xFF); a.emit(ands_reg, 0, 4); a.emit(ldrb_imm, 3, 7, RT_DLO); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_DLO)
    a.emit(lsrs_imm, 0, 4, 8); a.emit(ldrb_imm, 3, 7, RT_DHI); a.emit(bics_reg, 3, 0); a.emit(strb_imm, 3, 7, RT_DHI)
    a.emit(mov_reg, 0, 2); a.emit(adds_imm8, 0, 1)
    a.label("sd_send")                                                                                           # r0 = code, r1 = value
    a.emit(ldrb_imm, 2, 7, RT_TAG); a.emit(lsls_imm, 1, 1, 16); a.emit(lsrs_imm, 1, 1, 16); a.emit(lsls_imm, 0, 0, 16); a.emit(orrs_reg, 1, 0)
    a.emit(cmp_imm, 2, 0); a.emit(b_cond, "sd_t", "eq"); a.emit(movs_imm, 3, 1); a.emit(lsls_imm, 3, 3, 23); a.emit(orrs_reg, 1, 3)
    a.label("sd_t")
    a.emit(movs_imm, 3, 1); a.emit(eors_reg, 2, 3); a.emit(strb_imm, 2, 7, RT_TAG)
    a.emit(lsls_imm, 1, 1, 8)
    a.emit(mov_reg, 2, 6); a.emit(movs_imm, 3, VBS); a.emit(muls, 2, 3); a.emit(movw, 3, VB0); a.emit(adds_reg, 2, 2, 3)
    a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
    a.label("sd_x"); a.emit(pop_list, [4], pc=True)

    # ---- c_vtick: head of the DSP service chain
    a.label("c_vtick")
    a.emit(push_list, [4, 5, 6, 7], lr=True)
    a.emit(bl, L["c_gfst"]); a.emit(cmp_imm, 0, 0); bc("vt_chain", "eq")
    a.emit(mov_reg, 4, 0)
    a.emit(ldrb_w, 1, 4, FLAGS_BYTE); a.emit(movs_imm, 2, B_BOOT); a.emit(tst_reg, 1, 2); bc("vt_run", "ne")
    a.emit(orrs_reg, 1, 2); a.emit(strb_w, 1, 4, FLAGS_BYTE)
    tail(5)
    a.emit(ldrb_w, 0, 5, O_FLAGS); a.emit(movs_imm, 1, 0x80); a.emit(tst_reg, 0, 1)
    if SIGNED:                                                                    # the state counts only with our signature (a tail of garbage / 0xFF would switch both voices on)
        bc("vt_inv", "eq"); a.emit(ldrb_w, 0, 5, O_SIG); a.emit(cmp_imm, 0, SIG_VAL); bc("vt_vol", "eq")
        a.label("vt_inv"); a.emit(movs_imm, 1, 0x80)
    else:
        bc("vt_vol", "ne")
    a.emit(strb_w, 1, 5, O_FLAGS)                                                 # first use: flags = initialised, both off; the default values
    for i, v in enumerate(DEFAULTS):
        a.emit(movs_imm, 1, v); a.emit(strb_w, 1, 5, O_PAR + i); a.emit(strb_w, 1, 5, O_PAR + 16 + i)
    if SIGNED: a.emit(movs_imm, 0, SIG_VAL); a.emit(strb_w, 0, 5, O_SIG)
    a.label("vt_vol")
    a.emit(movs_imm, 1, 0)
    for t in (0, 1):
        for j in range(8): a.emit(strb_w, 1, 5, O_RT + 8 * t + j)
    a.emit(strb_w, 1, 5, O_SAVED)
    a.emit(movs_imm, 0, 1); a.emit(movs_imm, 1, 0xFF)
    for t in (0, 1):
        a.emit(strb_w, 0, 5, O_RT + 8 * t + RT_AUX); a.emit(strb_w, 1, 5, O_RT + 8 * t + RT_DLO); a.emit(strb_w, 1, 5, O_RT + 8 * t + RT_DHI)
    a.label("vt_run")
    tail(5); a.emit(movs_imm, 6, 0)
    a.label("vt_l")
    a.emit(bl, "c_vsend"); a.emit(adds_imm8, 6, 1); a.emit(cmp_imm, 6, 2); bc("vt_l", "lo")
    a.label("vt_chain")
    a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_dtick19"])
    return a.assemble()


def install(img, report, base_addr, text):
    """Append the code at base_addr and hook: the macro handlers (slots 4 / 7), the note vtable, the template view (pad hook, slot 7) and the head of the DSP service chain."""
    import ct_fw
    import build_sc14 as s14
    import drums18
    BASE = ct_fw.APP_BASE
    w = lambda addr: struct.unpack_from("<I", img, addr - BASE)[0]
    s6 = {k: int(v, 16) for k, v in report["sc06"]["labels"].items()}
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    assert w(AC64_VT + 0x10) == STOCK_KNOB | 1 and w(AC64_VT + 0x1C) == STOCK_LEDS | 1, (hex(w(AC64_VT + 0x10)), hex(w(AC64_VT + 0x1C)))
    assert w(NOTE_VT[0]) == s6["c_non"] | 1 and w(NOTE_VT[1]) == s6["c_noff"] | 1
    assert w(TMPL_VT_LEDS) == s6["c_tleds"] | 1
    assert drums18.decode_bw(img, T_PAD_SITE) == s6["c_tpad"], hex(drums18.decode_bw(img, T_PAD_SITE))
    assert drums18.decode_bw(img, s14.SVC_HOOK) == p19["c_dtick19"]
    L = dict(c_shift=int(report["sc15"]["labels"]["c_shift"], 16), c_gfst=int(report["sc17"]["labels"]["c_gfst"], 16), c_dtick19=p19["c_dtick19"],
             c_tpad=s6["c_tpad"], c_tleds=s6["c_tleds"], c_settings=s6["c_settings"], c_non=s6["c_non"], c_noff=s6["c_noff"])
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, AC64_VT + 0x10 - BASE, labels["c_vknob"] | 1)
    struct.pack_into("<I", img, AC64_VT + 0x1C - BASE, labels["c_vkleds"] | 1)
    struct.pack_into("<I", img, NOTE_VT[0] - BASE, labels["c_vnon"] | 1)
    struct.pack_into("<I", img, NOTE_VT[1] - BASE, labels["c_vnoff"] | 1)
    struct.pack_into("<I", img, TMPL_VT_LEDS - BASE, labels["c_vleds"] | 1)
    img[T_PAD_SITE - BASE:T_PAD_SITE - BASE + 4] = b_w(T_PAD_SITE, labels["c_vpad"])
    img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_vtick"])
    return labels, code
