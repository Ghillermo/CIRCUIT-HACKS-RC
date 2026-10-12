"""SC28 ARM tests (NRPN out / in for the drum parameters of our patches and for Master FX, tools/nrpn28.py) through the real routes (knobs 0x08033848, buttons, the stock MIDI-in function 0x08051720):

    python tools/emu_sc28.py SC28.bin SC28_manifest.json
  * installation: slot 4 of the drum macro handlers and of the Mixer view, the MIDI-in cave -> ours, the old ones behind;
  * drums out: every knob of ours sends NRPN 5 + drum : code on the drums channel with the value on the wire (bipolar + 64), the extended values (start point, bitcrush), the filter mode, the
    distortion type; the stock knobs send what they sent (no NRPN); Clear sends the default;
  * drums in: the same numbers set the stored bytes (the other bits of the byte kept) and mark the code dirty; out of range / other MSB / Rx off / the internal copy: nothing;
  * Master FX out / in: NRPN 9 : 4 x set + knob on channel 16, the dirty flag of the block;
  * the stock NRPN handler does not react to those numbers (no parameter write).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc27 as T27  # noqa: E402,F401  (applies the options of SC25..SC27)
import emu_sc22_4 as T4  # noqa: E402
import persist19 as P  # noqa: E402
import build_sc17 as B17  # noqa: E402
import nrpn28 as N  # noqa: E402
import drums18  # noqa: E402
V = T4.V
E20, MGR = T4.E20, T4.MGR
SEND, MIDI_IN, CTX_PTR, SCR = 0x0803BEDA, 0x08051720, 0x200069E4, 0x20065000
PARAM_SET = 0x08034D92
BIP = [c for c in range(1, 9) if c not in P.UNIPOLAR]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    L = {k: int(v, 16) for k, v in rep["nrpn28"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - 0x08010000)[0]
    check(w(P.MH_SLOT4) == L["c_ndknob"] | 1 and w(B17.MIX_VT + 16) == L["c_ngknob"] | 1 and drums18.decode_bw(img, V.STK_MIDIIN) == L["c_nmin"],
          "slot 4 of the drum macro handlers / of the Mixer view and the MIDI-in cave -> c_ndknob / c_ngknob / c_nmin")
    check(0x20044E58 - int(rep["sc17"]["sc14_state"], 16) == 236, "RAM reservation unchanged (236)")
    gfst = int(rep["sc17"]["labels"]["c_gfst"], 16)

    gc.collect(); e = E20(img, man)
    sends, psets = [], []
    def hk(uc, a, s, d):
        r = lambda x: uc.reg_read(x)
        if a == SEND:
            sends.append(tuple(uc.mem_read(r(UC_ARM_REG_R1), 3))); uc.reg_write(UC_ARM_REG_PC, r(UC_ARM_REG_LR) | 1)
        else:
            psets.append((r(UC_ARM_REG_R1), r(UC_ARM_REG_R2), r(UC_ARM_REG_R3)))
    for fa in (SEND, PARAM_SET): e.uc.hook_add(UC_HOOK_CODE, hk, begin=fa, end=fa)
    for _ in range(30): e.vtick()
    dch = e.r8(e.r32(V.TXOBJ + 0x0C) + 4)
    check(dch == 9, f"the drums channel (index 4 of the Tx table): {dch + 1}")
    ctx = e.r32(CTX_PTR)
    e.uc.mem_write(ctx + 0x14, bytes([0x0F]))
    def midi(status, d1, d2):
        e.uc.mem_write(SCR, bytes([status, d1, d2])); e.call(MIDI_IN, ctx, SCR, maxins=3_000_000)
    def nrpn(ch, msb, lsb, val):
        midi(0xB0 | ch, 99, msb); midi(0xB0 | ch, 98, lsb); midi(0xB0 | ch, 6, val)
    def trip(ch, msb, lsb, val): return [(0xB0 | ch, 99, msb), (0xB0 | ch, 98, lsb), (0xB0 | ch, 6, val)]
    byte = lambda d, c: e.xm(P.XM_DRUMS + 9 * d + c - 1)
    def xt(d):
        e.call(int(rep["persist19"]["labels"]["c_xt_get"], 16), d); return e.uc.reg_read(UC_ARM_REG_R0)
    wire = lambda c, v: (v + 64) & 0x7F if c in BIP else v

    # ================================================================ drums out
    for d in (0, 2):
        e.sel(d); e.track(4 + d)
        for (k, shift), code in sorted([((k, False), c) for k, c in P.REMAP_PLAIN.items()] + [((k, True), c) for k, c in P.REMAP_SHIFT.items()]):
            if code == 9: continue
            sends.clear(); b0 = e.dval(d, code); dl = 5 if b0 < 50 else -5
            e.knob_raw(k, dl, shift)
            v = e.dval(d, code)
            check(v == b0 + dl and sends == trip(dch, 5 + d, code, wire(code, v)),
                  f"drum {d + 1} {'Shift + ' if shift else ''}K{k + 1} (code {code}) {b0} -> {v}: NRPN {5 + d}:{code} = {wire(code, v)} on channel {dch + 1} ({sends})")
        sends.clear(); e.knob_raw(4, 1, True)
        check(sends == trip(dch, 5 + d, 9, byte(d, 9) & 7) and byte(d, 9) & 7 == 1, f"   Shift + K5: the filter mode: NRPN {5 + d}:9 = {byte(d, 9) & 7}")
        sends.clear(); e.knob_raw(7, 1, True)
        check(sends == trip(dch, 5 + d, N.L_DTYPE, 1) and xt(d) & 3 == 1, f"   Shift + K8: the distortion type: NRPN {5 + d}:12 = 1 ({sends})")
        e.knob_raw(7, -127); e.knob_raw(7, -127); sends.clear(); e.knob_raw(7, 10)                       # K8: twice to the left = the bitcrush nibble at 15, then 10 to the right
        nb = (e.dext(d) >> 4) & 15
        check(nb == 5 and sends == trip(dch, 5 + d, N.L_CRUSH, 5), f"   K8 in its left half: the bitcrush {nb}: NRPN {5 + d}:11 ({sends})")
        e.knob_raw(2, -127); e.knob_raw(2, -127); sends.clear(); e.knob_raw(2, 11)                       # K3: the start point nibble
        nb = e.dext(d) & 15
        check(nb == 4 and sends == trip(dch, 5 + d, N.L_START, 4), f"   K3 in its left half: the start point {nb}: NRPN {5 + d}:10 ({sends})")
        sends.clear(); e.knob_raw(0, 3)
        check(not [s for s in sends if s[1] in (99, 98, 6)], f"   K1 (the stock pitch): no NRPN ({sends})")
    # Clear + knob
    e.sel(0); e.track(4)
    e.call(0x08033320, MGR, 23, maxins=900000); sends.clear(); e.knob_raw(1, 1); e.call(0x0803381A, MGR, 23, maxins=900000)
    got = {(s[2]) for s in sends if s[1] == 98}
    check(e.dval(0, 2) == 0 and e.dval(0, 8) == 0 and got == {2, 8} and (0xB0 | dch, 6, 0) in sends, f"Clear + K2: both layers back to the default and sent (LSBs {sorted(got)})")

    # ================================================================ drums in
    for d in (1, 3):
        marks = lambda: e.dirty(d)
        for code in range(1, 9):
            old = byte(d, code); e.uc.mem_write(e.xa(P.XM_DRUMS + 9 * d + code - 1), bytes([old | 0x80]))          # an extended-value bit: it must survive
            nrpn(dch, 5 + d, code, 100)
            want = 36 if code in BIP else 100
            check(e.dval(d, code) == want and byte(d, code) & 0x80 and (marks() >> (code - 1)) & 1, f"drum {d + 1}: NRPN {5 + d}:{code} = 100 in: {e.dval(d, code)} (bit 7 kept, dirty {marks():#x})")
            e.uc.mem_write(e.xa(P.XM_DRUMS + 9 * d + code - 1), bytes([byte(d, code) & 0x7F]))
        nrpn(dch, 5 + d, 3, 0)
        check(e.dval(d, 3) == -64, f"   a bipolar value at 0: {e.dval(d, 3)}")
        up = byte(d, 9) & 0xF8
        nrpn(dch, 5 + d, 9, 3)
        check(byte(d, 9) == (up | 3), f"   the filter mode 3 (the upper bits of the byte kept: {byte(d, 9):#x})")
        nrpn(dch, 5 + d, 9, 90)
        check(byte(d, 9) & 7 == 4, "   clamped at 4")
        nrpn(dch, 5 + d, N.L_START, 9); nrpn(dch, 5 + d, N.L_CRUSH, 100)
        check(e.dext(d) == (15 << 4 | 9), f"   start point 9, bitcrush clamped at 15 ({e.dext(d):#x})")
        check(e.dval(d, 3) == -64 and e.dval(d, 1) == 36, "   and the values under those bits are intact")
        nrpn(dch, 5 + d, N.L_DTYPE, 2)
        check(xt(d) & 3 == 2 and byte(d, 9) & 7 == 4, f"   the distortion type 2 ({xt(d)})")
        snap = e.xmall()
        nrpn(dch, 5 + d, 0, 50); nrpn(dch, 5 + d, 13, 50); nrpn(dch, 4, 3, 50); nrpn(dch, 9, 3, 50); nrpn(dch, 5 + d + (4 if d == 3 else 5), 3, 50) if d == 3 else None
        check(e.xmall() == snap, "   LSB 0 / 13, MSB 4 / 9 on the drums channel: nothing")
    snap = e.xmall()
    nrpn(dch ^ 1, 6, 3, 50)
    check(e.xmall() == snap, "the same NRPN on another channel: nothing")
    e.uc.mem_write(ctx + 0x14, bytes([0x0D])); nrpn(dch, 6, 3, 50)
    check(e.xmall() == snap, "Setup CC Rx off: nothing")
    e.uc.mem_write(ctx + 0x14, bytes([0x0F]))
    fl = e.r32(V.MIDI_IN_FLAG); e.w32(V.MIDI_IN_FLAG, fl | 4); nrpn(dch, 6, 3, 50); e.w32(V.MIDI_IN_FLAG, fl)
    check(e.xmall() == snap, "MIDI input disabled (the internal copy): nothing")
    psets.clear(); nrpn(dch, 6, 3, 50)
    check(e.dval(1, 3) == -14 and psets == [], f"enabled again: set ({e.dval(1, 3)}); the stock handler writes no parameter for it ({psets})")
    # the stock CCs of the drums still arrive
    psets.clear(); midi(0xB0 | dch, 14, 77)
    check(len(psets) >= 1, f"a stock drum CC (14) still reaches the stock handler ({psets[:2]})")

    # ================================================================ Master FX
    e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
    kn = lambda: list(e.uc.mem_read(blk + B17.S_KNOB, 20))
    e.btn(14)
    if e.r32(MGR + 0x6C) != 0x200447D4: e.btn(14)
    e.btn(14)                                                                     # Mixer -> Mixer = Master FX
    for padi, st in ((0, 0), (3, 2), (5, 4)):
        e.padr(padi); e.rel(padi)
        for k in range(4):
            b0 = kn(); sends.clear(); dl = 6 if b0[4 * st + k] < 60 else -6
            e.knob_raw(k, dl)
            b1 = kn()
            check(b1[4 * st + k] == b0[4 * st + k] + dl and sends == trip(N.GFX_CH, N.GFX_MSB, 4 * st + k, b1[4 * st + k]),
                  f"Master FX pad {padi + 1} (set {st}) K{k + 1}: {b0[4 * st + k]} -> {b1[4 * st + k]}: NRPN 9:{4 * st + k} on channel 16 ({sends})")
    b0 = kn(); sends.clear(); e.knob_raw(0, 0)
    check(sends == [] and kn() == b0, "a turn that changes nothing: nothing sent")
    for lsb in (0, 7, 19):
        e.uc.mem_write(blk + B17.S_DIRTY, b"\x00")
        nrpn(N.GFX_CH, N.GFX_MSB, lsb, 11 + lsb)
        check(kn()[lsb] == 11 + lsb and e.r8(blk + B17.S_DIRTY) == 1, f"NRPN 9:{lsb} = {11 + lsb} in on channel 16: set, the block marked dirty")
    b0 = kn(); t0 = bytes(e.uc.mem_read(blk, 196))
    nrpn(N.GFX_CH, N.GFX_MSB, 20, 50); nrpn(N.GFX_CH, 8, 3, 50); nrpn(N.GFX_CH, 10, 3, 50); nrpn(3, N.GFX_MSB, 3, 50)
    check(bytes(e.uc.mem_read(blk, 196)) == t0, "LSB 20, MSB 8 / 10, another channel: nothing")
    psets.clear(); nrpn(N.GFX_CH, N.GFX_MSB, 2, 99)
    check(kn()[2] == 99 and psets == [], f"the stock handler writes no parameter for NRPN 9:x ({psets})")
    hit = None
    for msb in (1, 2):
        for lsb in range(64):
            psets.clear(); nrpn(N.GFX_CH, msb, lsb, 64)
            if psets: hit = (msb, lsb, psets[0]); break
        if hit: break
    check(hit is not None, f"a stock NRPN of channel 16 still reaches the stock handler (the first one found: {hit})")
    # the mode of the MIDI tracks (SC25) still gets its CCs behind our stage
    e.btn(2); e.track(2); e.btn(8)
    e.padr(V.PAD_OSC); e.rel(V.PAD_OSC)
    for _ in range(40): e.vtick()
    ch2 = e.r8(e.r32(V.TXOBJ + 0x0C) + 2)
    midi(0xB0 | ch2, 71, 90)
    check(e.val(0, 2) == 90, f"CC 71 on the channel of MIDI 1 still sets RES ({e.val(0, 2)})")
    print("SC28 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
