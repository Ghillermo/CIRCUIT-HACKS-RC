"""SC28: MIDI (NRPN with a 7-bit value) out and in for the parameters our patches added to the drums and for the parameters of Master FX (ARM side).

The stock unit has no MIDI for them (they are ours); the stock NRPN handler ignores every NRPN on the drums channel and, on the other channels, every MSB above 2, so the numbers below are free:

    drums (the drums channel)        NRPN MSB 5 + d (d = 0..3 = Drum 1..4), LSB = the code:
        1 pitch envelope, 2 ring mod frequency, 3 LFO amount, 4 LFO speed, 5 env -> cutoff, 6 resonance, 7 envelope shape, 8 ring mod amount   (0..127; the bipolar ones 64 = centre)
        9 filter mode (0..4), 10 start point (0..15), 11 bitcrush (0..15), 12 distortion type (0..3)
        SC41.7 (use_k3split): 10 start point (0..120 of 128), 13 cut (0..120), 14 amp attack (0..127)
    Master FX (channel 16)             NRPN MSB 9, LSB = 4 x set + knob (set 0..4: gate, filter (both filter pads), digitise, phaser, vinyl; knob 0..3), value 0..127

Out: two wrappers in front of the knob handlers (slot 4 of the drum macro handlers, slot 4 of the Mixer / Master FX view) compare the values before and after the stock + SC19 code and send what changed
(so Clear, the extended values and every later change of those handlers are covered) through the template CC helper of SC05 (the Setup CC Tx filter applies).
In: a second stage in front of vcf21's cave at the CC section of the stock MIDI-in function (Setup CC Rx on, not an internal copy).  The NRPN select CCs are kept in the stock records (index 2 = drums,
3 = the other channels); the stock code runs afterwards for every message.  No RAM."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from thumb import (Asm, b, b_cond, b_w, bl, cmp_imm, cmp_reg, ldr_imm, ldrb_imm, strb_imm, lsls_imm, lsrs_imm, mov_reg, movs_imm, movt, movw,  # noqa: E402
                   pop_list, push_list, raw, h, adds_imm8, subs_imm8, adds_reg, ands_reg, orrs_reg, eors_reg, ldrb_reg, strb_reg)
import vcf21 as V  # noqa: E402
import persist19 as P  # noqa: E402
import build_sc17 as B17  # noqa: E402
import drums18  # noqa: E402

DRUM_MSB0 = 5                         # NRPN MSB of Drum 1 (.. + 3 = Drum 4)
GFX_MSB = 9
GFX_CH = 15                           # channel 16
N_GFX = 20                            # 5 sets x 4 knobs
L_START, L_CRUSH, L_DTYPE = 10, 11, 12
K3SPLIT = False                       # SC41.7 (use_k3split): LSB 10 = the start (0..120 of 128), 13 = the cut, 14 = the amp attack (persist19.use_k3split)
L_CUT, L_ATK = 13, 14
K3_LSB = ((0, L_ATK), (1, L_START), (2, L_CUT))      # (which of persist19's c_k3get / c_k3put, LSB)


def use_k3split():
    global K3SPLIT
    K3SPLIT = True
REC_IDX = 0x080528EC                  # stock (this, channel) -> the index of the NRPN record: 0 / 1 the synths, 2 the drums, 3 the rest
INV = P.INV


def popw(regs, lr=False): return h(0xE8BD) + h(sum(1 << r for r in regs) | (1 << 14 if lr else 0))


def arm_code(base, L):
    """L: c_dget, c_dput, c_dext_get, c_dnib_set, c_xt_get, c_xt_set, c_mark (persist19), c_mh (drums18), c_gfst (Master FX), prev_dk / prev_gk (the knob handlers behind ours), c_vmin (vcf21's MIDI-in cave)."""
    a = Asm(base)
    E = a.emit
    zc = [0]

    def bc(target, cond):
        zc[0] += 1; n = f"_n{zc[0]}"
        E(b_cond, n, INV[cond]); E(b, target); a.label(n)

    # ---- c_nq(r0 = channel, r1 = MSB, r2 = LSB, r3 = value): CC 99, 98, 6
    a.label("c_nq")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2); E(mov_reg, 7, 3)
    for cc, r in ((99, 5), (98, 6), (6, 7)):
        E(mov_reg, 0, 4); E(movs_imm, 1, 0xB0); E(movs_imm, 2, cc); E(mov_reg, 3, r); E(bl, V.CC_HELPER)
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ndq(r0 = drum, r1 = LSB, r2 = value): the NRPN of a drum value on the drums channel (index 4 of the stock table of the Tx channels)
    a.label("c_ndq")
    E(push_list, [4], lr=True)
    E(mov_reg, 3, 2); E(mov_reg, 2, 1); E(mov_reg, 1, 0); E(adds_imm8, 1, DRUM_MSB0)
    E(movw, 0, V.TXOBJ & 0xFFFF); E(movt, 0, V.TXOBJ >> 16); E(ldr_imm, 0, 0, 0x0C); E(ldrb_imm, 0, 0, 4)
    E(bl, "c_nq")
    E(pop_list, [4], pc=True)

    # ---- c_ndknob(obj, knob, delta): slot 4 of the drum macro handlers.  Stack: [0..8] the bytes of the codes 1..9, [9] the distortion type bits, [10] the extended values
    a.label("c_ndknob")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(raw, h(0xB084))                                                             # sub sp, #16
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(movs_imm, 7, 0)
    a.label("nd_f")
    E(mov_reg, 0, 7); E(bl, L["c_mh"]); E(cmp_reg, 0, 4); E(b_cond, "nd_have", "eq")
    E(adds_imm8, 7, 1); E(cmp_imm, 7, 4); E(b_cond, "nd_f", "lo")
    E(raw, h(0xB004))                                                             # not a drum handler we know: the handler behind
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(raw, popw([4, 5, 6, 7], lr=True)); E(b_w, L["prev_dk"])
    a.label("nd_have")
    E(raw, h(0xB420))                                                             # push {r5}  (the knob; r5 = the loop counter below)
    E(movs_imm, 5, 1)
    a.label("nd_s")
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(mov_reg, 1, 13); E(adds_reg, 1, 1, 5); E(strb_imm, 0, 1, 3)        # [sp + 4 + code - 1]
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 9); E(b_cond, "nd_s", "ls")
    E(mov_reg, 0, 7); E(bl, L["c_xt_get"]); E(mov_reg, 1, 13); E(strb_imm, 0, 1, 4 + 9)
    E(mov_reg, 0, 7); E(bl, L["c_dext_get"]); E(mov_reg, 1, 13); E(strb_imm, 0, 1, 4 + 10)
    if K3SPLIT:                                                                   # [11..13] attack, start, cut
        for which, _ in K3_LSB:
            E(mov_reg, 0, 7); E(movs_imm, 1, which); E(bl, L["c_k3get"]); E(mov_reg, 1, 13); E(strb_imm, 0, 1, 4 + 11 + which)
    E(raw, h(0xBC20))                                                             # pop {r5}
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["prev_dk"])
    E(movs_imm, 5, 1)
    a.label("nd_c")                                                               # the codes 1..9
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(mov_reg, 6, 0)
    E(mov_reg, 1, 13); E(adds_reg, 1, 1, 5); E(subs_imm8, 1, 1); E(ldrb_imm, 1, 1, 0)
    E(movs_imm, 2, 0x7F); E(cmp_imm, 5, 9); E(b_cond, "nd_m", "ne"); E(movs_imm, 2, 7)
    a.label("nd_m")
    E(eors_reg, 1, 6); E(ands_reg, 1, 2); E(cmp_imm, 1, 0); E(b_cond, "nd_n", "eq")
    E(ands_reg, 2, 6)                                                             # r2 = the new value
    E(cmp_imm, 5, 9); E(b_cond, "nd_e", "eq")
    for c in P.UNIPOLAR:
        E(cmp_imm, 5, c); E(b_cond, "nd_e", "eq")
    E(movs_imm, 1, 0x40); E(eors_reg, 2, 1)                                       # bipolar (7-bit two's complement): + 64
    a.label("nd_e")
    E(mov_reg, 0, 7); E(mov_reg, 1, 5); E(bl, "c_ndq")
    a.label("nd_n")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, 9); E(b_cond, "nd_c", "ls")
    E(mov_reg, 0, 7); E(bl, L["c_dext_get"]); E(mov_reg, 6, 0)                    # the extended values: the two nibbles
    E(mov_reg, 1, 13); E(ldrb_imm, 5, 1, 10); E(eors_reg, 5, 6)
    if not K3SPLIT:                                                               # (with K3SPLIT the start is not the nibble any more)
        E(lsls_imm, 0, 5, 28); E(b_cond, "nd_x1", "eq")
        E(mov_reg, 0, 7); E(movs_imm, 1, L_START); E(movs_imm, 2, 15); E(ands_reg, 2, 6); E(bl, "c_ndq")
        a.label("nd_x1")
    E(lsrs_imm, 0, 5, 4); E(b_cond, "nd_x2", "eq")
    E(mov_reg, 0, 7); E(movs_imm, 1, L_CRUSH); E(lsrs_imm, 2, 6, 4); E(bl, "c_ndq")
    a.label("nd_x2")
    E(mov_reg, 0, 7); E(bl, L["c_xt_get"]); E(movs_imm, 1, 3); E(ands_reg, 0, 1); E(mov_reg, 6, 0)
    E(mov_reg, 2, 13); E(ldrb_imm, 2, 2, 9); E(ands_reg, 2, 1); E(cmp_reg, 2, 6); E(b_cond, "nd_x3", "eq")
    E(mov_reg, 0, 7); E(movs_imm, 1, L_DTYPE); E(mov_reg, 2, 6); E(bl, "c_ndq")
    a.label("nd_x3")
    if K3SPLIT:
        for which, lsb in K3_LSB:
            E(mov_reg, 0, 7); E(movs_imm, 1, which); E(bl, L["c_k3get"]); E(mov_reg, 6, 0)
            E(mov_reg, 1, 13); E(ldrb_imm, 1, 1, 11 + which); E(cmp_reg, 1, 6); E(b_cond, f"nd_k{which}", "eq")
            E(mov_reg, 0, 7); E(movs_imm, 1, lsb); E(mov_reg, 2, 6); E(bl, "c_ndq")
            a.label(f"nd_k{which}")
    E(raw, h(0xB004))                                                             # add sp, #16
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_ngknob(view, knob, delta): slot 4 of the Mixer / Master FX view.  Stack: the 20 parameter bytes before the turn
    a.label("c_ngknob")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(raw, h(0xB086))                                                             # sub sp, #24
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(bl, L["c_gfst"]); E(mov_reg, 7, 0); E(cmp_imm, 7, 0); E(b_cond, "ng_have", "ne")
    E(raw, h(0xB006))
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(raw, popw([4, 5, 6, 7], lr=True)); E(b_w, L["prev_gk"])
    a.label("ng_have")
    E(adds_imm8, 7, B17.S_KNOB)
    E(movs_imm, 3, 0); E(mov_reg, 1, 13)
    a.label("ng_s"); E(ldrb_reg, 0, 7, 3); E(strb_reg, 0, 1, 3); E(adds_imm8, 3, 1); E(cmp_imm, 3, N_GFX); E(b_cond, "ng_s", "lo")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(mov_reg, 2, 6); E(bl, L["prev_gk"])
    E(movs_imm, 5, 0)
    a.label("ng_c")
    E(ldrb_reg, 3, 7, 5); E(mov_reg, 1, 13); E(ldrb_reg, 1, 1, 5); E(cmp_reg, 1, 3); E(b_cond, "ng_n", "eq")
    E(movs_imm, 0, GFX_CH); E(movs_imm, 1, GFX_MSB); E(mov_reg, 2, 5); E(bl, "c_nq")
    a.label("ng_n")
    E(adds_imm8, 5, 1); E(cmp_imm, 5, N_GFX); E(b_cond, "ng_c", "lo")
    E(raw, h(0xB006))                                                             # add sp, #24
    E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_nset(r0 = drum, r1 = LSB 1..12, r2 = value 0..127): an incoming drum value
    a.label("c_nset")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 4, 0); E(mov_reg, 5, 1); E(mov_reg, 6, 2)
    E(cmp_imm, 5, 0); bc("ns_x", "eq")
    if K3SPLIT:                                                                   # 10 start, 13 cut (0..120), 14 attack (0..127)
        for which, lsb in K3_LSB:
            E(movs_imm, 1, which); E(cmp_imm, 5, lsb); E(b_cond, "ns_k3", "eq")
    E(cmp_imm, 5, L_DTYPE); bc("ns_x", "hi")
    E(cmp_imm, 5, 9); bc("ns_ext", "hi")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dget"]); E(mov_reg, 7, 0); E(adds_imm8, 0, 1); bc("ns_x", "eq")     # (the store is not there)
    E(cmp_imm, 5, 9); E(b_cond, "ns_mode", "eq")
    E(mov_reg, 2, 6)
    for c in P.UNIPOLAR:
        E(cmp_imm, 5, c); E(b_cond, "ns_u", "eq")
    E(movs_imm, 1, 0x40); E(eors_reg, 2, 1)
    a.label("ns_u")
    E(movs_imm, 1, 0x7F); E(ands_reg, 2, 1); E(movs_imm, 1, 0x80); E(ands_reg, 1, 7); E(orrs_reg, 2, 1)                # bit 7 (an extended-value bit) kept
    E(b, "ns_put")
    a.label("ns_mode")
    E(cmp_imm, 6, 4); E(b_cond, "ns_m4", "ls"); E(movs_imm, 6, 4)
    a.label("ns_m4"); E(movs_imm, 2, 0xF8); E(ands_reg, 2, 7); E(orrs_reg, 2, 6)                                        # the upper bits (signature / distortion type) kept
    a.label("ns_put")
    E(cmp_reg, 2, 7); bc("ns_x", "eq")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, L["c_dput"])
    E(b, "ns_mark")
    a.label("ns_ext")
    E(cmp_imm, 5, L_DTYPE); E(b_cond, "ns_type", "eq")
    E(cmp_imm, 6, 15); E(b_cond, "ns_e15", "ls"); E(movs_imm, 6, 15)
    a.label("ns_e15")
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(subs_imm8, 1, L_START); E(lsls_imm, 1, 1, 2); E(mov_reg, 2, 6); E(bl, L["c_dnib_set"])
    E(movs_imm, 5, 10); E(b, "ns_mark")
    a.label("ns_type")
    E(cmp_imm, 6, 3); E(b_cond, "ns_t3", "ls"); E(movs_imm, 6, 3)
    a.label("ns_t3")
    E(mov_reg, 0, 4); E(bl, L["c_xt_get"]); E(movs_imm, 1, 4); E(ands_reg, 1, 0); E(orrs_reg, 1, 6); E(mov_reg, 0, 4); E(bl, L["c_xt_set"])
    E(movs_imm, 5, 10)
    if K3SPLIT:
        a.label("ns_k3")                                                          # r1 = which; r6 = the value
        E(cmp_imm, 1, 0); E(b_cond, "ns_kv", "eq"); E(cmp_imm, 6, 120); E(b_cond, "ns_kv", "ls"); E(movs_imm, 6, 120)
        a.label("ns_kv")
        E(mov_reg, 0, 4); E(mov_reg, 2, 6); E(bl, L["c_k3put"]); E(b, "ns_x")
    a.label("ns_mark")                                                            # r5 = the code to send to the DSP again
    E(mov_reg, 0, 4); E(bl, L["c_mh"]); E(cmp_imm, 0, 0); E(b_cond, "ns_x", "eq")
    E(mov_reg, 1, 5); E(bl, L["c_mark"])
    a.label("ns_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_nin(receiver, message): a CC on the drums channel / on channel 16: the NRPN select CCs go to the stock record, the data entry (CC 6) of our numbers sets the value
    a.label("c_nin")
    E(push_list, [4, 5, 6, 7], lr=True)
    E(mov_reg, 6, 0); E(mov_reg, 5, 1)
    E(ldrb_imm, 2, 5, 0); E(lsrs_imm, 3, 2, 4); E(cmp_imm, 3, 0xB); bc("ni_x", "ne")
    E(ldrb_imm, 3, 6, 0x14); E(movs_imm, 4, 0x22); E(ands_reg, 3, 4); E(cmp_imm, 3, 2); bc("ni_x", "ne")                # the Setup CC Rx
    E(movw, 3, V.MIDI_IN_FLAG & 0xFFFF); E(movt, 3, V.MIDI_IN_FLAG >> 16); E(ldr_imm, 3, 3, 0); E(lsls_imm, 3, 3, 29); bc("ni_x", "mi")
    E(movs_imm, 3, 0x0F); E(ands_reg, 2, 3); E(mov_reg, 7, 2)                     # r7 = the channel
    E(ldr_imm, 0, 6, 0x10); E(cmp_imm, 0, 0); bc("ni_x", "eq")
    E(mov_reg, 1, 7); E(bl, REC_IDX); E(mov_reg, 4, 0)                            # r4 = the record index
    E(cmp_imm, 4, 2); bc("ni_x", "lo")
    E(b_cond, "ni_ok", "eq")
    E(cmp_imm, 7, GFX_CH); bc("ni_x", "ne")
    a.label("ni_ok")
    E(ldr_imm, 3, 6, 0x10); E(lsls_imm, 0, 4, 2); E(adds_reg, 0, 0, 4); E(adds_reg, 3, 3, 0)                            # r3 = this + 5 x index: +0xA LSB, +0xB MSB, +0xC set
    E(ldrb_imm, 1, 5, 1); E(ldrb_imm, 2, 5, 2)
    E(cmp_imm, 1, 99); E(b_cond, "ni_a", "ne"); E(strb_imm, 2, 3, 0x0B); E(b, "ni_f")
    a.label("ni_a"); E(cmp_imm, 1, 98); E(b_cond, "ni_b", "ne"); E(strb_imm, 2, 3, 0x0A)
    a.label("ni_f"); E(movs_imm, 0, 1); E(strb_imm, 0, 3, 0x0C); E(b, "ni_x")
    a.label("ni_b"); E(cmp_imm, 1, 6); bc("ni_x", "ne")
    E(ldrb_imm, 0, 3, 0x0C); E(cmp_imm, 0, 0); bc("ni_x", "eq")
    E(ldrb_imm, 0, 3, 0x0B); E(ldrb_imm, 1, 3, 0x0A)                              # r0 = MSB, r1 = LSB, r2 = value
    E(cmp_imm, 4, 2); E(b_cond, "ni_g", "ne")
    E(subs_imm8, 0, DRUM_MSB0); E(cmp_imm, 0, 3); bc("ni_x", "hi")
    E(bl, "c_nset"); E(b, "ni_x")
    a.label("ni_g")
    E(cmp_imm, 0, GFX_MSB); bc("ni_x", "ne"); E(cmp_imm, 1, N_GFX); bc("ni_x", "hs")
    E(mov_reg, 4, 1); E(mov_reg, 5, 2)
    E(bl, L["c_gfst"]); E(cmp_imm, 0, 0); bc("ni_x", "eq")
    E(adds_imm8, 4, B17.S_KNOB); E(strb_reg, 5, 0, 4); E(movs_imm, 1, 1); E(strb_imm, 1, 0, B17.S_DIRTY)
    a.label("ni_x"); E(pop_list, [4, 5, 6, 7], pc=True)

    # ---- c_nmin: the head of the CC section of the stock MIDI-in function (r4 = the receiver, r5 = the message): our stage, then vcf21's cave
    a.label("c_nmin")
    E(push_list, [0, 1, 2, 3], lr=True)
    E(mov_reg, 0, 4); E(mov_reg, 1, 5); E(bl, "c_nin")
    E(raw, popw([0, 1, 2, 3], lr=True)); E(b_w, L["c_vmin"])
    return a.assemble()


def install(img, report, base_addr):
    import ct_fw
    BASE = ct_fw.APP_BASE
    w = lambda ad: struct.unpack_from("<I", img, ad - BASE)[0]
    p19 = {k: int(v, 16) for k, v in report["persist19"]["labels"].items()}
    v20 = {k: int(v, 16) for k, v in report["vcf20"]["labels"].items()}
    L = {k: p19[k] for k in ("c_dget", "c_dput", "c_dext_get", "c_dnib_set", "c_xt_get", "c_xt_set", "c_mark")}
    if K3SPLIT:
        L.update(c_k3get=p19["c_k3get"], c_k3put=p19["c_k3put"])
    L["c_mh"] = int(report["sc18"]["labels"]["c_mh"], 16); L["c_gfst"] = int(report["sc17"]["labels"]["c_gfst"], 16)
    L["prev_dk"] = w(P.MH_SLOT4) & ~1; L["prev_gk"] = w(B17.MIX_VT + 16) & ~1; L["c_vmin"] = v20["c_vmin"]
    assert L["prev_dk"] == p19["c_dk19"] and L["prev_gk"] == int(report["sc17"]["labels"]["c_gknob"], 16), (hex(L["prev_dk"]), hex(L["prev_gk"]))
    assert drums18.decode_bw(img, V.STK_MIDIIN) == v20["c_vmin"], hex(drums18.decode_bw(img, V.STK_MIDIIN))
    code, labels = arm_code(base_addr, L)
    img += bytes([0xFF]) * (base_addr - BASE - len(img)) + code
    while len(img) % 4:
        img += bytes([0xFF])
    assert len(img) <= 0x70000
    struct.pack_into("<I", img, P.MH_SLOT4 - BASE, labels["c_ndknob"] | 1)
    struct.pack_into("<I", img, B17.MIX_VT + 16 - BASE, labels["c_ngknob"] | 1)
    img[V.STK_MIDIIN - BASE:V.STK_MIDIIN - BASE + 4] = b_w(V.STK_MIDIIN, labels["c_nmin"])
    return labels, code
