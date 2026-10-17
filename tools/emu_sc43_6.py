"""SC43.6 ARM tests (dpitch.use_rec: the chromatic steps in lane 7 of the drum pattern), through the controller and the players' real step
(0x0804A714):
  * Record armed + playing, Drum 1's chromatic view: a pad writes its S into the six micro steps of lane 7 at the drum's playing step (the others
    stay 0xFF); with Record not armed it does not;
  * the players' step of Drum 1 at a step whose lane 7 holds 70: the pitch word of S 70 written to X:$A4 at micro step 0, lane 7's halfwords
    0xFFFF (no pan from it); a later step without a value: the knob's S again; Drum 2's player does not touch Drum 1;
  * the gate: id 89 (Drum 1's pan) not recorded, id 40 (its pitch) recorded;
  * stopped, the LED task: the step's S gives way (the drum's group marked dirty);
  * Clear + K1 to the left: lane 7 of the playing pattern back to 0xFF;
  * cue mode (cue.py) in the Mixer's pan page, the DSP words through the real group handlers (Synth 1 0x08028C9C, Drum 1 0x080287DE, the reverb
    sends 0x08028B80): off = the stock's; Shift + K1 right = on (the setting's byte 0xC5, its save asked, Octave down pink); no cue = hard left at
    the level; K1 +40 = c 40: level L, pan 64 x 40 / L, its LED pink at 40; its pad toggle while cued = the main mute (the sequencer unmuted, the
    pad in the muted code; level 40, pan 127; its reverb send 0); Clear + K1 = c 0, the mute back; a save: the main mute during the
    serialisation, then the cue's again; Shift + K1 left = off (the stock's words, Octave down white); a load: the cues dropped;
  * the own engine of MIDI 1 (vcf21, the oscillator source): one oscillator: 60 then 64 = OSC1 64 (n2 keeps 60), releasing 64 = back to 60;
    two oscillators: the paraphonic assignment as before; after a note the mailbox gets code 14 before the gate and the trigger; the OSC 2 page:
    K3 = MIX, K4 = FM, Shift + K1 nothing.

    python tools/emu_sc43_6.py SC43.6.bin SC43.6_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import dpitch as DP  # noqa: E402

MGR = T.MGR
DSP_W, STEP, REC_LANE, GATE = 0x080292F8, 0x0804A714, 0x0803FC20, 0x2003C168


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def setp(store, k, v):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), bytes([v]))
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    dsp, dirty, recl = [], [], []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dsp.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), begin=DSP_W, end=DSP_W)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dirty.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), begin=DP.MARK_DIRTY, end=DP.MARK_DIRTY)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: recl.append(uc.reg_read(UC_ARM_REG_R1)), begin=REC_LANE, end=REC_LANE)
    conv = lambda v: r0(lab(man, "sc12", "c_conv0"), v)
    S = lambda d=0: r0(lab(man, "dpitch", "c_dpnow"), d)
    tail = e.r32(DP.SESSION_OBJ + 0x14) + DP.TAIL
    eng = lambda d: e.r32(DP.ENG + 0x30 + 4 * (4 + d))
    def lane(d=0):
        base = e.r32(DP.DP0 + DP.DP_SZ * d + 0x48) + DP.PAT_SZ * getp(eng(d), 0) + 0xA8 + 192 * DP.LANE
        return base, bytes(e.uc.mem_read(base, 192))
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    e.btn(4); X.frame(e)
    shift(True); e.btn(8); shift(False)                                            # Shift + Preset: Drum 1's chromatic view
    view = r0(lab(man, "sc11", "c_dview"), 0)
    check(e.r8(view + 0x51) & 1 == 1, "Drum 1's chromatic view open")
    base, l0 = lane()
    check(set(l0) == {0xFF}, f"lane 7 of the playing pattern empty at first ({base:#x})")
    # ---- recording
    setp(DP.TRANSPORT, 0, 1); setp(DP.TRANSPORT, 1, 0); setp(eng(0), 1, 5)
    e.pad(8); l1 = lane()[1]
    check(set(l1) == {0xFF}, "Record not armed: the pad writes nothing")
    setp(DP.TRANSPORT, 1, 1)
    e.pad(10); s1 = S(); l2 = lane()[1]
    check(l2[30:36] == bytes([s1]) * 6 and set(l2[:30] + l2[36:]) == {0xFF} and s1 != 64,
          f"Record armed, playing, step 5: the pad's S {s1} in the six micro steps of step 5 ({l2[24:42].hex()})")
    setp(DP.TRANSPORT, 1, 0)
    # ---- playback through the players' step
    e.uc.mem_write(base + 6 * 9, bytes([70]) * 6)
    def step(st, d=0):
        p = DP.DP0 + DP.DP_SZ * d; store = e.r32(p + 8)
        setp(store, 0, getp(eng(d), 0)); setp(store, 1, st)
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, 2), struct.pack("<I", 0))
        dsp.clear(); e.call(STEP, p, maxins=8_000_000)
        return [(v, a_) for v, a_ in dsp if a_ == DP.PITCH_X + 10 * d]
    w = step(9); hw = [struct.unpack_from("<H", e.uc.mem_read(e.r32(DP.DP0 + o) + 14, 2))[0] for o in (0x40, 0x44)]
    check(w == [(conv(70), DP.PITCH_X)] and hw == [0xFFFF, 0xFFFF] and e.r8(tail + DP.O_ACT) & 1,
          f"step 9 (lane 70): pitch word {[hex(v) for v, _ in w]} = SC12's of 70 {conv(70):#x} at X:$A4; lane 7 halfwords {[hex(x) for x in hw]}")
    w2 = step(9)
    check(w2 == [], f"the same step again: nothing written ({w2})")
    w3 = step(11)
    check(w3 == [(conv(s1), DP.PITCH_X)] and not e.r8(tail + DP.O_ACT) & 1, f"step 11 (no value): the knob's S {s1} again ({[hex(v) for v, _ in w3]})")
    w4 = step(9, 1)
    check(w4 == [] and not e.r8(tail + DP.O_ACT) & 1, f"Drum 2's player at step 9: nothing for Drum 1 ({w4})")
    # ---- the gate
    setp(DP.TRANSPORT, 1, 1); recl.clear()
    e.call(0x0802E62C, GATE, 89, 50, maxins=4_000_000); a89 = list(recl)
    e.call(0x0802E62C, GATE, 40, 50, maxins=4_000_000); a40 = recl[len(a89):]
    check(a89 == [] and a40 == [0], f"the gate: id 89 (Drum 1's pan) not recorded ({a89}), id 40 recorded in lane {a40}")
    setp(DP.TRANSPORT, 1, 0)
    # ---- stopped
    step(9); setp(DP.TRANSPORT, 0, 0); dirty.clear(); X.frame(e)
    check(not e.r8(tail + DP.O_ACT) & 1 and (0x10, 2) in dirty, f"stopped: the step's S gives way, Drum 1's group dirty ({dirty[:4]})")
    del e; gc.collect()

    # ---- Clear + K1 left
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    e.btn(4); X.frame(e)
    st = e.r32(DP.ENG + 0x30 + 16)
    base = e.r32(DP.DP0 + 0x48) + DP.PAT_SZ * getp(st, 0) + 0xA8 + 192 * DP.LANE
    e.uc.mem_write(base, bytes([66]) * 192)
    e.call(0x08033320, MGR, 23, maxins=8_000_000); e.call(0x08033848, MGR, 0, 0xFFFFFFFF, maxins=8_000_000); e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    l = bytes(e.uc.mem_read(base, 192))
    check(set(l) == {0xFF} and S() == 64, f"Clear + K1 left: lane 7 deleted ({set(l)}), S stays {S()}")
    del e; gc.collect()
    cue_tests(img, man, check)
    vcf_tests(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def vcf_tests(img, man, check):
    import emu_sc22_4 as T4
    import vcf21_dsp as VD
    V = T4.V
    gc.collect(); e = T4.E20(img, man)
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    sgn = lambda v: v - 0x10000 if v & 0x8000 else v
    def ticks(n=30):
        out = []
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0: out.append(((w >> 16) & 0x7F, sgn(w & 0xFFFF)))
        return out
    for _ in range(30): e.vtick()
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x05]))          # MIDI 1: the mode on, the oscillator source
    ticks(30)
    rtb = V.TAIL + V.O_RT
    def dual(on): v = e.rt(0, V.RT_VEL); e.uc.mem_write(rtb + V.RT_VEL, bytes([(v & 0x7F) | (0x80 if on else 0)]))
    n2 = lambda: e.tailb(V.O_PAR + V.STRIDE * 0 + 13)
    n1 = lambda: e.rt(0, V.RT_NOTE) & 0x7F
    cnt = lambda: e.rt(0, V.RT_CNT) & 15
    NON, NOFF = e.r32(V.NOTE_VT[0]) & ~1, e.r32(V.NOTE_VT[1]) & ~1
    note_on = lambda n, vel=90: e.call(NON, 0x20011334, 2, n, vel)
    note_off = lambda n: e.call(NOFF, 0x20011334, 2, n, 0)
    dual(False)
    note_on(60); ms = ticks(20)
    order = [c for c, v in ms]
    fi = lambda c: order.index(c) if c in order else 99
    check(cnt() == 1 and n1() == 60 and n2() == 60 and fi(18) < fi(14) < fi(17) and fi(14) < fi(21),
          f"one note: 60 / 60; the mailbox order NOTE {fi(18)}, code 14 {fi(14)}, GATE {fi(17)}, TRIG {fi(21)}")
    note_on(64); ms = ticks(20)
    check(cnt() == 2 and n1() == 64 and n2() == 60 and (18, 64) in ms, f"one oscillator, 64 while 60 is held: OSC1 {n1()} (sent {[v for c, v in ms if c == 18]}), n2 {n2()}")
    note_off(64); ms = ticks(20)
    check(cnt() == 1 and n1() == 60 and (18, 60) in ms and 17 not in [c for c, v in ms], f"64 released: back to {n1()} (sent {[v for c, v in ms if c == 18]}), no new gate")
    note_off(60); ticks(20)
    dual(True); note_on(60); note_on(64)
    check(n1() == 60 and n2() == 64, f"two oscillators: the paraphonic assignment ({n1()} / {n2()})")
    note_off(64); note_off(60); ticks(20); dual(False)
    # the OSC 2 page
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
    v2 = lambda k: struct.unpack("b", bytes([e.r8(blk + V.V2_OFF + k)]))[0]
    e.btn(2); e.btn(8); e.call(L["c_vsetpage"], 0, 2)
    before = [v2(k) for k in range(8)]
    e.knob_raw(2, 5); e.knob_raw(3, 7); e.knob_raw(0, 3, shift=True)
    after = [v2(k) for k in range(8)]
    check(after[4] == before[4] + 5 and after[6] == before[6] + 7 and after[1] == before[1], f"OSC 2 page: K3 = MIX, K4 = FM, Shift + K1 nothing ({before} -> {after})")
    del e; gc.collect()


def cue_tests(img, man, check):
    import cue as CQ
    from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    getv = lambda ty, ix: r0(0x08036192, ty, ix)
    dsp, saves = [], []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dsp.append((uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R1))), begin=DSP_W, end=DSP_W)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: saves.append(1), begin=CQ.SAVE_SET, end=CQ.SAVE_SET)
    def group(fn, *addrs):
        dsp.clear(); e.call(fn, maxins=4_000_000); return [v for a_, v in dsp if a_ in addrs]
    pw = lambda p: (p << 24) if p <= 64 else (((p << 16) + (p - 64) * 1040 + 15) << 8)
    flag = lambda: e.r8(r0(0x0803542C, e.r32(e.r32(e.r32(CQ.CTX)) + 0x54), 3) + 3)
    mute = lambda t: e.r8(r0(0x0803542C, e.r32(e.r32(CQ.MIX_VIEW + 0x68) + e.r32(CQ.MIX_VIEW + 0x60) * t), 0))
    tail = e.r32(CQ.SESSION_OBJ + 0x14) + CQ.TAIL
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    S1, D1, REV = 0x08028C9C, 0x080287DE, 0x08028B80
    e.btn(14); X.frame(e); e.btn(19); f = X.frame(e)
    m, p0 = getv(0x20, 46), getv(0x20, 50); md, pd = getv(0x10, 1), getv(0x10, 6)
    g = group(S1, 0x52, 0x53); gd = group(D1, 0x80FD, 0x8101)
    check(e.r8(CQ.MIX_VIEW + CQ.PAN_PAGE) == 1 and g == [m << 23, pw(p0)] and gd == [md << 23, pw(pd)] and f[CQ.LED_OCT] == CQ.WHITE,
          f"cue off, the pan page: Synth 1 level {m} / pan {p0} as the stock ({[hex(x) for x in g]}), Drum 1 too; Octave down white ({f[CQ.LED_OCT]:#x})")
    shift(True); knob(0, 1); shift(False); f = X.frame(e)
    g = group(S1, 0x52, 0x53); gd = group(D1, 0x80FD, 0x8101)
    import lazysave as LZ
    saves.append(e.r8(tail + LZ.O_PEND) == LZ.PEND) if not saves else None
    check(flag() == CQ.CUE_ON and any(saves) and f[CQ.LED_OCT] == CQ.PINK and g == [m << 23, 0] and gd == [md << 23, 0] and getv(0x20, 50) == p0,
          f"Shift + K1 right: on (byte {flag():#x}, save asked {len(saves)}), Octave down {f[CQ.LED_OCT]:#x}; no cue = hard left ({[hex(x) for x in g]}); the stock pan kept")
    knob(0, 40); f = X.frame(e); g = group(S1, 0x52, 0x53)
    want = (64 * 40 + m // 2) // m
    check(g == [m << 23, pw(want)] and getv(0x20, 50) == p0 and f[60] == (40 << 8 | CQ.PINK) and e.r8(tail + CQ.O_C0) == 40,
          f"K1 +40: cue 40, level {m}, pan {want} ({[hex(x) for x in g]}); the stock pan kept; K1 LED {f[60]:#x}")
    e.pad(0); f = X.frame(e); g = group(S1, 0x52, 0x53); rv = group(REV, 0xE3)
    check(mute(0) == 0 and e.r8(tail + CQ.O_MM) & 1 and f[0] == CQ.MUTED[0] and g == [40 << 23, pw(127)] and rv == [0],
          f"pad 1 while cued: the sequencer unmuted ({mute(0)}), main mute set, pad {f[0]:#x}; level 40 / pan 127 ({[hex(x) for x in g]}); reverb send {rv}")
    e.call(0x08033320, MGR, 23, maxins=8_000_000); knob(0, 1); e.call(0x0803381A, MGR, 23, maxins=8_000_000)
    check(e.r8(tail + CQ.O_C0) == 0 and mute(0) == 1, f"Clear + K1: cue 0 ({e.r8(tail + CQ.O_C0)}), the main mute back in the sequencer ({mute(0)})")
    e.pad(1); knob(1, 20)
    st = []
    m1 = mute(1)
    store1 = e.r32(e.r32(CQ.MIX_VIEW + 0x68) + e.r32(CQ.MIX_VIEW + 0x60))
    p_r = r0(0x0803542C, store1, 0)
    def ser3(uc, a, s_, d):
        st.append(uc.mem_read(p_r, 1)[0]); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, ser3, begin=0x0802F63C, end=0x0802F63C)
    e.call(int(man["report"]["cue"]["labels"]["c_cqsave"], 16), CQ.SESSION_OBJ, maxins=20_000_000)
    check(m1 == 0 and e.r8(tail + CQ.O_MM) & 2 and st == [1] and mute(1) == 0,
          f"Synth 2 muted then cued: sequencer {m1}; a save serialises its main mute ({st}), then back to {mute(1)}")
    shift(True); knob(3, -1 & 0xFFFFFFFF); shift(False); f = X.frame(e); g = group(S1, 0x52, 0x53)
    check(flag() == 0 and mute(1) == 1 and g == [m << 23, pw(p0)] and f[CQ.LED_OCT] == CQ.WHITE,
          f"Shift + K4 left: off (byte {flag():#x}), Synth 2's mute back ({mute(1)}), Synth 1 the stock's again ({[hex(x) for x in g]})")
    shift(True); knob(0, 1); shift(False); knob(4, 30)
    e.uc.mem_write(0x2006F000, bytes(36) + struct.pack("<I", T.STOP | 1))                      # the frame of the pop.w at the end
    e.call(int(man["report"]["cue"]["labels"]["c_cqload"], 16), maxins=8_000_000)
    cs = [e.r8(tail + CQ.O_C0 + t) for t in range(5)] + [e.r8(tail + CQ.O_C1 + t) for t in range(5, 8)]
    check(cs == [0] * 8 and e.r8(tail + CQ.O_MM) == 0, f"a load: the cues dropped ({cs})")
    del e; gc.collect()
    return 0


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
