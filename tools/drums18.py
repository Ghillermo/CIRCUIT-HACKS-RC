"""SC18 additions: chromatic drum pitch recorded only on its step (ARM) + drum knob controls (ARM + DSP, see drums_dsp.py).

1. Chromatic recording (ARM).  A chromatic pad press sets the drum Pitch through the automation recorder
   (0x0802E62C -> 0x0803FC20): that marks the lane "touched" in [rec+0x2C] and stores the value in [rec+0x28][lane].
   The recorder's step listener (0x0803FE24, loop at 0x0803FEE6) then writes, on EVERY following step while the lane
   stays touched (the mask is only cleared when the record state changes), the pending value or 0xFF (= no automation)
   once it has been consumed -> after one bar every earlier pitch is erased and plays the last pitch.
   Hook 0x0803FF02 (touched lane about to be written) -> c_rstep: if the pending value is 0xFF, the lane is the Pitch lane
   (0) of a drum recorder (vtable 0x0805A578, byte +4 = drum 1..4) and that drum's Preset view is in chromatic mode
   (view+0x51 bit 0), nothing is written.  Knobs and non-chromatic drums: stock.

2. Drum knobs (ARM).  Per drum macro handler (vtable 0x0805AADC, [container + 0x148 + 4 * (4 + d)]); slot 4 (obj, knob, delta)
   was SC12's c_dknob3 -> c_dk18:
     K1 / K3 / K5 / K7 (knob 0 / 2 / 4 / 6, stock: nothing) -> codes 1 / 2 / 3 / 5 (pitch env, hold, LFO amount, env -> cutoff)
     Shift + K5 -> code 4 (LFO speed), Shift + K8 -> code 6 (resonance); other Shift turns: SC12 / stock
     K4 / K6 (decay / distortion): turning left past 0 counts an extended value 0..15 (start point / bitcrush); turning right
       first brings it back to 0, then the stock value.  Everything else -> c_dknob3 (SC11 / SC12 / stock).
   State in 3 padding bytes of the handler object (the constructor does not write them; hook 0x0804FC6A zeroes them):
     +0x31 extended values (bits 3..0 start point, bits 7..4 bitcrush)
     +0x3E bit 7 mailbox tag, bit 6 "extended values changed", bits 3..0 pending code
     +0x3F pending delta (signed, accumulated for the same code)
   The DSP service hook (SVC chain, DSP lock held) sends the pending message to the drum's DSP mailbox
   X:DB(d)+0 = tag << 23 | code << 16 | delta (16 bits) and the extended values to X:DB(d)+2.  A new code replaces an
   unsent one of a different code (one message per drum per service tick).
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, ldrb_w, lsls_imm, lsrs_imm, mov_reg, movs_imm,
                   movt, movw, subs_imm8, adds_imm8, adds_reg, subs_reg, ands_reg, orrs_reg, bics_reg, eors_reg, push_list,
                   pop_list, raw, h)  # noqa: E402

REC_HOOK = 0x0803FF02                 # ldr r2,[r5,#0x28] ; mov r1,r6   (touched lane, about to record [r5+0x28][r6])
REC_GO = 0x0803FF06                   # mov r0,r5 ...
REC_SKIP = 0x0803FF1E                 # pending = 0xFF, next lane
DRUM_REC_VT = 0x0805A578              # drum track recorders (synth / MIDI tracks: 0x0805A5B4); byte +4 = drum 1..4


def ldrb_reg(rt, rn, rm): return h(0x5C00 | rm << 6 | rn << 3 | rt)
def ldrsb_imm(rt, rn, imm): return h(0xF990 | rn) + h(rt << 12 | imm)          # LDRSB.W Rt,[Rn,#imm12]
def ldrb_w_(rt, rn, imm12): return h(0xF890 | rn) + h(rt << 12 | imm12)        # LDRB.W Rt,[Rn,#imm12]
def ldr_w(rt, rn, imm12): return h(0xF8D0 | rn) + h(rt << 12 | imm12)          # LDR.W Rt,[Rn,#imm12]
def lsls_reg_w(rd, rn, rm): return h(0xFA00 | rn) + h(0xF000 | rd << 8 | rm)     # LSL.W Rd,Rn,Rm
def lsrs_reg_w(rd, rn, rm): return h(0xFA20 | rn) + h(0xF000 | rd << 8 | rm)     # LSR.W Rd,Rn,Rm
def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))
def uxth(rd, rm): return h(0xB280 | rm << 3 | rd)
def strb_w(rt, rn, imm): return h(0xF880 | rn) + h(rt << 12 | imm)               # STRB.W Rt,[Rn,#imm12]


CTX_PTR = 0x200069E4
MH_VT = 0x0805AADC                    # drum macro handler vtable; slot 4 = knob turn
MH_SLOT4 = MH_VT + 0x10
MH_CTOR_BL = 0x0804FC6A               # bl 0x0801A7E4 inside the constructor (r7 = this)
MH_CTOR_FN = 0x0801A7E4
PARAM_GET = 0x0803542C
DSP_WRITE = 0x080292F8
O_EXT, O_FLAGS, O_DELTA = 0x31, 0x3E, 0x3F
V2 = False                            # SC18.1: drums2_dsp layout and knob map, chromatic view rows 1-2 dark
TRIM18 = False                        # SC49 (use_trim): c_dk18 / c_dtick / c_dleds18 not emitted (persist19 takes their hooks)


def use_trim():
    """SC49 (flash for the extra drum lane): persist19 puts c_dtick19 at the head of the DSP service chain (chained to svc_next) and SC08's
    c_dleds back on the drum Preset view's slot 7; c_dtick and c_dleds18 are called from nowhere (checked on SC48.9's image): not emitted,
    their hooks left alone.  c_dk18 too: persist19 puts c_dk19 on slot 4 of the drum macro handlers (and c_dk19 goes on to SC12's c_dknob3)."""
    global TRIM18
    TRIM18 = True
DP_VT_SLOT7 = 0x0805ABBC + 0x1C       # drum Preset view getLeds (SC08's c_dleds)
# knob -> mailbox code (knob index 0..7 = K1..K8);  SC18 / SC18.1
MAP1 = dict(plain={0: 1, 2: 2, 4: 3, 6: 5}, shift={4: 4, 7: 6})
MAP2 = dict(plain={0: 7, 2: 2, 4: 3, 6: 5}, shift={0: 1, 2: 8, 4: 4, 6: 9, 7: 6})


def arm_code(base, L):
    """L: c_dview (SC11).  Returns (bytes, labels)."""
    a = Asm(base)
    # ---- c_rstep: b.w from REC_HOOK; r5 = recorder, r6 = lane; r0-r3 and lr are free here
    a.label("c_rstep")
    a.emit(ldr_imm, 2, 5, 0x28); a.emit(raw, ldrb_reg(1, 2, 6))
    a.emit(cmp_imm, 1, 0xFF); a.emit(b_cond, "rs_go", "ne")
    a.emit(cmp_imm, 6, 0); a.emit(b_cond, "rs_go", "ne")
    a.emit(ldr_imm, 0, 5, 0); a.emit(movw, 1, DRUM_REC_VT & 0xFFFF); a.emit(movt, 1, DRUM_REC_VT >> 16)
    a.emit(cmp_reg, 0, 1); a.emit(b_cond, "rs_go", "ne")                      # not a drum recorder
    a.emit(ldrb_imm, 0, 5, 4); a.emit(subs_imm8, 0, 1); a.emit(cmp_imm, 0, 3); a.emit(b_cond, "rs_go", "hi")
    a.emit(bl, L["c_dview"])                                                   # r0 = drum view or 0 (clobbers r1, r2)
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "rs_go", "eq")
    a.emit(ldrb_w, 1, 0, 0x51); a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "rs_go", "eq")
    a.emit(b_w, REC_SKIP)                                                      # chromatic drum, nothing new: keep the step
    a.label("rs_go")
    a.emit(ldr_imm, 2, 5, 0x28); a.emit(mov_reg, 1, 6); a.emit(b_w, REC_GO)
    if "c_dknob3" in L:
        knobs_code(a, L)
    return a.assemble()


def knobs_code(a, L):
    import drums_dsp as DD1, drums2_dsp as DD2
    DD = DD2 if V2 else DD1
    DB, STRIDE = DD.DB, DD.STRIDE
    SH = STRIDE.bit_length() - 1
    MAP = MAP2 if V2 else MAP1
    zc = [0]
    def bc(target, cond):                            # conditional branch with long reach
        INV = {"eq": "ne", "ne": "eq", "lt": "ge", "ge": "lt", "gt": "le", "le": "gt", "hi": "ls", "ls": "hi", "lo": "hs", "hs": "lo", "pl": "mi", "mi": "pl"}
        zc[0] += 1; n = f"_k{zc[0]}"
        a.emit(b_cond, n, INV[cond]); a.emit(b, target); a.label(n)

    # ---- c_mhinit: constructor hook (bl from MH_CTOR_BL, r7 = this): stock call, then zero the 3 padding bytes
    a.label("c_mhinit")
    a.emit(push_list, [3], lr=True)
    a.emit(bl, MH_CTOR_FN)
    a.emit(movs_imm, 0, 0)
    a.emit(raw, strb_w(0, 7, O_EXT)); a.emit(raw, strb_w(0, 7, O_FLAGS)); a.emit(raw, strb_w(0, 7, O_DELTA))
    a.emit(pop_list, [3], pc=True)

    # ---- c_mh(r0 = drum 0..3) -> r0 = macro handler object or 0 (clobbers r1, r2)
    a.label("c_mh")
    a.emit(movw, 1, CTX_PTR & 0xFFFF); a.emit(movt, 1, CTX_PTR >> 16)
    a.emit(ldr_imm, 1, 1, 0); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "mh_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x40); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "mh_no", "eq")
    a.emit(ldr_imm, 1, 1, 0x2C); a.emit(cmp_imm, 1, 0); a.emit(b_cond, "mh_no", "eq")
    a.emit(lsls_imm, 0, 0, 2); a.emit(adds_reg, 1, 1, 0); a.emit(raw, ldr_w(0, 1, 0x148 + 16))
    a.emit(cmp_imm, 0, 0); a.emit(b_cond, "mh_no", "eq")
    a.emit(ldr_imm, 1, 0, 0); a.emit(movw, 2, MH_VT & 0xFFFF); a.emit(movt, 2, MH_VT >> 16)
    a.emit(cmp_reg, 1, 2); a.emit(b_cond, "mh_ok", "eq")
    a.label("mh_no"); a.emit(movs_imm, 0, 0)
    a.label("mh_ok"); a.emit(raw, h(0x4770))

    if not TRIM18:
        # ---- c_dk18 (obj, knob, delta): slot 4 of the drum macro handlers
        a.label("c_dk18")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(mov_reg, 4, 0); a.emit(mov_reg, 5, 1); a.emit(mov_reg, 6, 2)
        a.emit(bl, L["c_shift"])
        a.emit(cmp_imm, 0, 0); bc("dk_ns", "eq")
        for knob, code in sorted(MAP["shift"].items()):                             # Shift + knob
            a.emit(movs_imm, 1, code); a.emit(cmp_imm, 5, knob); bc("dk_pend", "eq")
        a.emit(b, "dk_old")
        a.label("dk_ns")
        for knob, code in sorted(MAP["plain"].items()):
            a.emit(movs_imm, 1, code); a.emit(cmp_imm, 5, knob); bc("dk_pend", "eq")
        a.emit(movs_imm, 7, 0); a.emit(cmp_imm, 5, 3); bc("dk_ext", "eq")           # K4: start point (bits 3..0)
        a.emit(movs_imm, 7, 4); a.emit(cmp_imm, 5, 5); bc("dk_ext", "eq")           # K6: bitcrush (bits 7..4)
        a.label("dk_old")
        a.emit(mov_reg, 0, 4); a.emit(mov_reg, 1, 5); a.emit(mov_reg, 2, 6)
        a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["c_dknob3"])
        # pending message: r1 = code, r6 = delta
        a.label("dk_pend")
        a.emit(raw, ldrb_w_(0, 4, O_FLAGS)); a.emit(movs_imm, 2, 0x0F); a.emit(ands_reg, 2, 0)
        a.emit(raw, ldrsb_imm(3, 4, O_DELTA))
        a.emit(cmp_reg, 2, 1); a.emit(b_cond, "dp_same", "eq")
        a.emit(movs_imm, 2, 0xF0); a.emit(ands_reg, 0, 2); a.emit(orrs_reg, 0, 1); a.emit(movs_imm, 3, 0)
        a.label("dp_same")
        a.emit(adds_reg, 3, 3, 6)
        a.emit(cmp_imm, 3, 100); a.emit(b_cond, "dp_c1", "le"); a.emit(movs_imm, 3, 100)
        a.label("dp_c1")
        a.emit(raw, h(0xF113)); a.emit(raw, h(0x0F64))                              # cmn.w r3,#100
        a.emit(b_cond, "dp_c2", "ge"); a.emit(movs_imm, 3, 0); a.emit(subs_imm8, 3, 100)
        a.label("dp_c2")
        a.emit(raw, strb_w(3, 4, O_DELTA)); a.emit(raw, strb_w(0, 4, O_FLAGS))
        a.emit(pop_list, [4, 5, 6, 7], pc=True)
        # extended range: r7 = nibble shift (0 start point / 4 bitcrush), macro = (knob - 1) / 2 (1 decay, 2 distortion)
        a.label("dk_ext")
        a.emit(cmp_imm, 6, 0); bc("dk_done", "eq")
        a.emit(ldr_imm, 0, 4, 0xC); a.emit(lsrs_imm, 1, 5, 1); a.emit(bl, PARAM_GET); a.emit(ldrb_imm, 3, 0, 0)   # r3 = stock value
        a.emit(raw, ldrb_w_(0, 4, O_EXT)); a.emit(raw, lsrs_reg_w(1, 0, 7)); a.emit(movs_imm, 2, 0x0F); a.emit(ands_reg, 1, 2)   # r1 = ext
        a.emit(cmp_imm, 6, 0); bc("de_right", "gt")
        # left: counts when ext > 0 or the stock value is already 0
        a.emit(cmp_imm, 1, 0); a.emit(b_cond, "de_l", "ne")
        a.emit(cmp_imm, 3, 0); bc("dk_old", "ne")
        a.label("de_l")
        a.emit(subs_reg, 1, 1, 6)                                                   # ext - delta (delta < 0)
        a.emit(cmp_imm, 1, 15); a.emit(b_cond, "de_set", "le"); a.emit(movs_imm, 1, 15)
        a.emit(b, "de_set")
        a.label("de_right")
        a.emit(cmp_imm, 1, 0); bc("dk_old", "eq")
        a.emit(subs_reg, 1, 1, 6); a.emit(b_cond, "de_set", "ge"); a.emit(movs_imm, 1, 0)
        a.label("de_set")                                                           # ext field = r1
        a.emit(movs_imm, 2, 0x0F); a.emit(raw, lsls_reg_w(2, 2, 7)); a.emit(bics_reg, 0, 2)
        a.emit(raw, lsls_reg_w(1, 1, 7)); a.emit(orrs_reg, 0, 1)
        a.emit(raw, strb_w(0, 4, O_EXT))
        a.emit(raw, ldrb_w_(0, 4, O_FLAGS)); a.emit(movs_imm, 1, 0x40); a.emit(orrs_reg, 0, 1); a.emit(raw, strb_w(0, 4, O_FLAGS))
        a.label("dk_done")
        a.emit(pop_list, [4, 5, 6, 7], pc=True)

    if not TRIM18:
        # ---- c_dtick: DSP service hook (b.w from the SVC chain, DSP lock held), then the previous target
        a.label("c_dtick")
        a.emit(push_list, [4, 5, 6, 7], lr=True)
        a.emit(movs_imm, 7, 0)
        a.label("dt_loop")
        a.emit(mov_reg, 0, 7); a.emit(bl, "c_mh"); a.emit(cmp_imm, 0, 0); bc("dt_next", "eq")
        a.emit(mov_reg, 4, 0)
        a.emit(raw, ldrb_w_(5, 4, O_FLAGS))
        a.emit(lsls_imm, 0, 5, 28); bc("dt_ext", "eq")                              # no pending code
        a.emit(movs_imm, 0, 0x80); a.emit(eors_reg, 5, 0)                           # toggle the tag
        a.emit(lsrs_imm, 0, 5, 7); a.emit(lsls_imm, 0, 0, 23)                       # tag << 23
        a.emit(movs_imm, 1, 0x0F); a.emit(ands_reg, 1, 5); a.emit(lsls_imm, 1, 1, 16); a.emit(orrs_reg, 0, 1)
        a.emit(raw, ldrsb_imm(1, 4, O_DELTA)); a.emit(raw, uxth(1, 1)); a.emit(orrs_reg, 0, 1)
        a.emit(lsls_imm, 1, 0, 8)
        a.emit(lsls_imm, 2, 7, SH); a.emit(movw, 0, DB & 0xFFFF); a.emit(adds_reg, 2, 2, 0)       # X:DB(d) + MB
        a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
        a.emit(movs_imm, 0, 0xF0); a.emit(ands_reg, 5, 0)
        a.emit(movs_imm, 0, 0); a.emit(raw, strb_w(0, 4, O_DELTA))
        a.label("dt_ext")
        a.emit(lsls_imm, 0, 5, 25); bc("dt_store", "pl")                            # bit 6: extended values changed
        a.emit(movs_imm, 0, 0x40); a.emit(bics_reg, 5, 0)
        a.emit(raw, ldrb_w_(1, 4, O_EXT)); a.emit(lsls_imm, 1, 1, 8)
        a.emit(lsls_imm, 2, 7, SH); a.emit(movw, 0, (DB + DD.EXT) & 0xFFFF); a.emit(adds_reg, 2, 2, 0)
        a.emit(movs_imm, 0, 0); a.emit(bl, DSP_WRITE)
        a.label("dt_store")
        a.emit(raw, strb_w(5, 4, O_FLAGS))
        a.label("dt_next")
        a.emit(adds_imm8, 7, 1); a.emit(cmp_imm, 7, 4); bc("dt_loop", "lo")
        a.emit(raw, popw([4, 5, 6, 7], lr=True)); a.emit(b_w, L["svc_next"])

    if not TRIM18:
        if V2:
            # ---- c_dleds18 (drum Preset view, slot 7): SC08's LEDs, then rows 1-2 dark in chromatic / scale mode
            a.label("c_dleds18")
            a.emit(push_list, [4], lr=True)
            a.emit(mov_reg, 4, 0)
            a.emit(bl, L["c_dleds"])                                                # r0 = LED buffer
            a.emit(ldrb_w, 1, 4, 0x51); a.emit(lsls_imm, 1, 1, 31); a.emit(b_cond, "dl8_x", "eq")
            a.emit(movs_imm, 1, 0); a.emit(movs_imm, 2, 0)
            a.label("dl8_l"); a.emit(raw, h(0x5281))                                # strh r1,[r0,r2]
            a.emit(adds_imm8, 2, 2); a.emit(cmp_imm, 2, 32); a.emit(b_cond, "dl8_l", "lo")
            a.label("dl8_x"); a.emit(pop_list, [4], pc=True)


def decode_bw(img, addr):
    """target of a B.W / BL T4/T1 at addr"""
    import struct, ct_fw
    h1, h2 = struct.unpack_from("<HH", img, addr - ct_fw.APP_BASE)
    s = (h1 >> 10) & 1; imm10 = h1 & 0x3FF; j1 = (h2 >> 13) & 1; j2 = (h2 >> 11) & 1; imm11 = h2 & 0x7FF
    i1 = (~(j1 ^ s)) & 1; i2 = (~(j2 ^ s)) & 1
    off = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s: off -= 1 << 25
    return addr + 4 + off


def install_arm(img, report, base_addr, text, knobs=True):
    """Append the ARM code at base_addr (aligned end of image) and patch the hooks.  text(addr, n) = stock disassembly."""
    import struct
    import ct_fw
    import build_sc14 as s14
    from thumb import bl as bl_enc
    BASE = ct_fw.APP_BASE
    assert text(REC_HOOK, 4) == "ldr r2, [r5, #0x28]|mov r1, r6", text(REC_HOOK, 4)
    assert text(REC_SKIP, 6) == "ldr r0, [r5, #0x28]|strb.w r8, [r0, r6]", text(REC_SKIP, 6)
    L = {"c_dview": int(report["sc11"]["labels"]["c_dview"], 16)}
    if knobs:
        assert text(MH_CTOR_BL, 4) == "bl #0x801a7e4", text(MH_CTOR_BL, 4)
        L["c_shift"] = int(report["sc15"]["labels"]["c_shift"], 16)
        L["c_dknob3"] = int(report["sc12"]["labels"]["c_dknob3"], 16)
        assert struct.unpack_from("<I", img, MH_SLOT4 - BASE)[0] == L["c_dknob3"] | 1
        L["svc_next"] = decode_bw(img, s14.SVC_HOOK)                       # current head of the DSP service chain
        if V2:
            L["c_dleds"] = int(report["sc08"]["labels"]["c_dleds"], 16)
            assert struct.unpack_from("<I", img, DP_VT_SLOT7 - BASE)[0] == L["c_dleds"] | 1
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    img[REC_HOOK - BASE:REC_HOOK - BASE + 4] = b_w(REC_HOOK, labels["c_rstep"])
    if knobs:
        img[MH_CTOR_BL - BASE:MH_CTOR_BL - BASE + 4] = bl_enc(MH_CTOR_BL, labels["c_mhinit"])
        if not TRIM18: struct.pack_into("<I", img, MH_SLOT4 - BASE, labels["c_dk18"] | 1)
        if not TRIM18: img[s14.SVC_HOOK - BASE:s14.SVC_HOOK - BASE + 4] = b_w(s14.SVC_HOOK, labels["c_dtick"])
        labels["svc_next"] = L["svc_next"]
        if V2:
            if not TRIM18: struct.pack_into("<I", img, DP_VT_SLOT7 - BASE, labels["c_dleds18"] | 1)
    return labels, code


def install_dsp(s16):
    """Before building: drum DSP code appended to the (wrapped) SC16 DSP code; sc_init clears the new memory."""
    import drums_dsp as DD1, drums2_dsp as DD2
    DD = DD2 if V2 else DD1
    if V2:
        s16.CLR_FROM = DD2.CLR_FROM                                         # X:$3400.. (comb buffers) .. $3B7F
    s16.CLR_N = DD.DB + 4 * DD.STRIDE - s16.CLR_FROM
    prev = s16.dsp_code
    def wrapped(base):
        w, l = prev(base)
        w2, l2 = DD.code(base + len(w))
        return w + w2, {**l, **l2}
    s16.dsp_code = wrapped
    s16.DRUMS_DD = DD


def patch_dsp(img, report):
    import drums_dsp as DD1, drums2_dsp as DD2
    DD = DD2 if V2 else DD1
    import linein2 as L2
    dl = {k: int(v, 16) for k, v in report["sc16"]["dsp_labels"].items()}
    assert DD.SC16_MIX == dl["mixhook"], hex(dl["mixhook"])
    L2.patch_p(img, DD.HOOK_CTL, [0x0BF080, DD.VOICE], [0x0BF080, dl["dctl"]])
    L2.patch_p(img, DD.HOOK_TRIG, [0x020B8E, 0x200013], [0x0BF080, dl["dtrig"]])
    L2.patch_p(img, DD.HOOK_MIX, [0x0BF080, DD.SC16_MIX], [0x0BF080, dl["dstage"]])
    if not V2:
        L2.patch_p(img, DD.HOOK_EQ, [0x02129E], [0x200013])
