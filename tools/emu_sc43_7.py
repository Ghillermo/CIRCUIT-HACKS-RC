"""SC43.7 ARM tests (dpitch.use_lane0, clrtrk.use_autoclr, vcf21.use_osc2pg2), through the controller, the players' real step (0x0804A714) and the
stock's automation apply (the blx at 0x0804A870: lane id, value):
  * K1 = the stock Pitch (P moves, S stays 64); Shift + K6 no longer moves P;
  * the chromatic view's pad sets S, not P; with Record armed and playing it writes 0x80 | S into the six micro steps of the drum's pitch lane
    (lane 0) at its playing step;
  * the players' step: a step of lane 0 = 0x85: not applied as P, the pitch word of S 5 written to X:$A4; a step of 0x50: applied as P 80 (the
    stock), the knob's S again; a step of lane 7 (the pan) = 0x30: applied by the stock as the pan (id 0x59);
  * the gate records id 89 (the pan) again;
  * Clear + K1 right: S back to 64 at once;
  * Clear + Drum 1: its pitch lane deleted (the stock's Clear + knob left), P back to 64, S 64;
  * the OSC 2 page of MIDI 1's engine (SC43.6's): K6 = BITSYNC, Shift + K6 nothing;
  * rollers (use_mute): Drum 1 muted in the Mixer, playing, rollers on micro steps 0 and 2 of an empty step: the players' real tick dispatch
    (0x0804A5C6) plays two hits (none before); their note-off from the LED task 100 ms later; unmuted, the step plays them as before;
  * Synth 1's step-drummer (srcview.use_keepplay, sdkeep): Play / Record keep its view; Drum 1, then Synth 1 = its view again; Synth 1 on it = stays;
    pad 30 closes it; then Synth 1 = its track view.
  * gate retrigger (retrig.py): by default a second held note sends GATE and TRIG; Shift + pad 29 of the Preset view = off (the tail + 159 = 0xA1,
    LED yellow with Shift, green when on): the second note sends NOTE without GATE / TRIG.
  * the arpeggiator (arp.use_viewoff): MIDI 1, stopped, two pads held: the first note's note-off reaches the MIDI transmitter before the
    arpeggio's first note (SC43.6: never); letting go: every note sent on the transmitter is off; Synth 1: the first note stopped through its
    view's interface; the views of the four note tracks at VIEW_IFC0 - 0x110 + VIEW_SZ t;
  * the resolution pads (use_rateflip): Shift + pad 17 = 1/4 (setting 8 << 3), Shift + pad 24 = 1/32T (1 << 3), pad 21 = 1/16, their LEDs
    green; the same on Drum 1;
  * Shift + Play (quant.py): Synth 1's pattern: micro steps 1-2 to 0, 3-5 to the next step (the last's to the first), the same note there
    dropped, an empty step with the old probability; Drum 1's pattern: one hit on micro steps 2 / 4 / 5 to the grid, a roll kept, the drum's
    edit store synced; the transport stays stopped; Play LED with Shift yellow, green after quantizing, as before without Shift.

    python tools/emu_sc43_7.py SC43.7.bin SC43.7_manifest.json
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
DSP_W, STEP, APPLY, REC_LANE, GATE = 0x080292F8, 0x0804A714, 0x0804A870, 0x0803FC20, 0x2003C168


def lab(man, m, k): return int(man["report"][m]["labels"][k], 16)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def setp(store, k, v, n=1):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), v.to_bytes(n, "little"))
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    dsp, ap, recl = [], [], []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: dsp.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), begin=DSP_W, end=DSP_W)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: ap.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), begin=APPLY, end=APPLY)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: recl.append(uc.reg_read(UC_ARM_REG_R1)), begin=REC_LANE, end=REC_LANE)
    conv = lambda v: r0(lab(man, "sc12", "c_conv0"), v)
    S = lambda: r0(lab(man, "dpitch", "c_dpnow"), 0)
    mh = r0(lab(man, "sc18", "c_mh"), 0)
    P = lambda: e.r8(r0(0x0803542C, e.r32(mh + 0xC), 0))
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    def shift(on): e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    clr = lambda on: e.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=8_000_000)
    eng = lambda d=0: e.r32(DP.ENG + 0x30 + 4 * (4 + d))
    def lane(L, d=0):
        base = e.r32(DP.DP0 + DP.DP_SZ * d + 0x48) + DP.PAT_SZ * getp(eng(d), 0) + 0xA8 + 192 * L
        return base, bytes(e.uc.mem_read(base, 192))
    e.btn(4); X.frame(e)
    p0, s0 = P(), S()
    knob(0, 5)
    check(P() == p0 + 5 and S() == 64 == s0, f"K1 +5: the stock Pitch {p0} -> {P()}, S stays {S()}")
    shift(True); knob(5, 3); shift(False)
    check(P() == p0 + 5, f"Shift + K6: P untouched ({P()})")
    shift(True); e.btn(8); shift(False)                                            # the chromatic view
    p1 = P(); e.pad(10); s1 = S()
    check(s1 != 64 and P() == p1, f"chromatic view: a pad sets S ({s1}), not P ({P()})")
    setp(DP.TRANSPORT, 0, 1); setp(DP.TRANSPORT, 1, 1); setp(eng(), 1, 5)
    e.pad(10); base0, l0 = lane(0)
    check(l0[30:36] == bytes([0x80 | min(s1, 126)]) * 6 and set(l0[:30] + l0[36:]) == {0xFF}, f"Record + playing, step 5: lane 0 = 0x80 | S ({l0[24:42].hex()})")
    setp(DP.TRANSPORT, 1, 0)
    # ---- the players' step
    base7, _ = lane(7)
    e.uc.mem_write(base0 + 6 * 9, bytes([0x85]) * 6); e.uc.mem_write(base0 + 6 * 10, bytes([0x50]) * 6); e.uc.mem_write(base7 + 6 * 11, bytes([0x30]) * 6)
    def step(st):
        store = e.r32(DP.DP0 + 8)
        setp(store, 0, getp(eng(), 0)); setp(store, 1, st); setp(store, 2, 0, 4)
        dsp.clear(); ap.clear(); e.call(STEP, DP.DP0, maxins=8_000_000)
        return [v for v, a_ in dsp if a_ == DP.PITCH_X], list(ap)
    pw = lambda s_, p_: r0(lab(man, "dpitch", "c_dpc0"), p_) if False else None
    w9, a9 = step(9)
    pnow = P()
    check(not any(l == 0x28 for l, v in a9) and len(w9) == 1 and e.r8(e.r32(DP.SESSION_OBJ + 0x14) + DP.TAIL + DP.O_ACT) & 1,
          f"step 9 (lane 0 = 0x85): P not applied ({a9}), the pitch word written once ({[hex(x) for x in w9]}), the step's S active")
    w10, a10 = step(10)
    check((0x28, 0x50) in a10 and not e.r8(e.r32(DP.SESSION_OBJ + 0x14) + DP.TAIL + DP.O_ACT) & 1, f"step 10 (lane 0 = 0x50): the stock applies P 80 ({a10}), the knob's S again")
    w11, a11 = step(11)
    check((0x59, 0x30) in a11, f"step 11 (lane 7 = 0x30): the stock applies the pan ({a11})")
    setp(DP.TRANSPORT, 1, 1); recl.clear()
    e.call(0x0802E62C, GATE, 89, 50, maxins=4_000_000)
    check(recl == [7], f"the gate records id 89 (the pan) in lane 7 again ({recl})")
    setp(DP.TRANSPORT, 1, 0); setp(DP.TRANSPORT, 0, 0); X.frame(e)
    del e; gc.collect()

    # ---- Clear + K1, Clear + Drum 1
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    mh = r0(lab(man, "sc18", "c_mh"), 0)
    e.btn(4); X.frame(e)
    shift(True); e.btn(8); shift(False); e.pad(10); e.btn(4); X.frame(e)
    s2 = S(); clr(True); knob(0, 1); s3 = S(); clr(False)
    check(s2 != 64 and s3 == 64, f"Clear + K1 right: S {s2} -> {s3} at once")
    knob(0, 9)
    base0, _ = lane(0); e.uc.mem_write(base0, bytes([0x40, 0x85] * 96))
    clr(True); e.call(0x08033320, MGR, 4, maxins=60_000_000); e.call(0x0803381A, MGR, 4, maxins=8_000_000); clr(False)
    l0 = lane(0)[1]
    check(set(l0) == {0xFF} and P() == 64 and S() == 64, f"Clear + Drum 1: its pitch lane deleted ({set(l0)}), P {P()}, S {S()}")
    del e; gc.collect()
    vcf_tests(img, man, check)
    roll_tests(img, man, check)
    sd_tests(img, man, check)
    arp_tests(img, man, check)
    rate_tests(img, man, check)
    quant_tests(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def sd_tests(img, man, check):
    gc.collect(); e = T.EL(img); e.at(300000); e.transport(0)
    lv = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    scr = lambda: r0(lv["c_sdscr"])
    cur = lambda: e.r8(MGR + 0x152)
    e.btn(0); X.frame(e); e.pad(29); X.frame(e)
    s0 = scr()
    e.btn(17); X.frame(e); s1 = scr(); e.btn(17); X.frame(e)
    e.btn(16); X.frame(e); s2 = scr(); e.btn(16); X.frame(e)
    check(s0 == 2 and s1 == 2 and s2 == 2, f"Synth 1's step-drummer view open ({s0}); Play ({s1}) and Record ({s2}) keep it")
    e.btn(4); X.frame(e); a1 = scr(); e.btn(0); X.frame(e); X.frame(e); s3 = scr()
    e.btn(0); X.frame(e); X.frame(e); s4 = scr()
    check(a1 == 0xFF and s3 == 2 and s4 == 2, f"Drum 1 ({a1}), then Synth 1: the step-drummer again ({s3}); Synth 1 on it: it stays ({s4})")
    e.pad(29); X.frame(e); s5 = scr(); e.btn(4); X.frame(e); e.btn(0); X.frame(e); X.frame(e)
    check(s5 == 0xFF and scr() == 0xFF and cur() == 1, f"pad 30 closes it ({s5}); then Synth 1 = its track view ({cur()})")
    del e; gc.collect()


def roll_tests(img, man, check):
    import rollers as R
    from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC
    gc.collect(); e = T.EL(img); e.at(100000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def setp(store, k, v, n=1):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), v.to_bytes(n, "little"))
    e.btn(4); e.btn(9); X.frame(e)
    e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); e.call(T.PRESS, MGR, 19, 100, maxins=8_000_000)
    DP = R.DP0
    iface = e.r32(DP + 0x4C); ivt = e.r32(iface); on_fn, off_fn = e.r32(ivt) & ~1, e.r32(ivt + 4) & ~1
    log = []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (log.append(("on", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), skip(uc)), begin=on_fn, end=on_fn)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (log.append(("off", uc.reg_read(UC_ARM_REG_R1))), skip(uc)), begin=off_fn, end=off_fn)
    base = e.r32(DP + 0x48); step = 5
    e.uc.mem_write(base + step, bytes([0])); e.uc.mem_write(base + 0x20 + step, bytes([7])); e.uc.mem_write(base + 0x60 + step, bytes([0])); e.uc.mem_write(DP + 0x59, bytes([0]))
    mute = e.r32(DP + 0x28)
    setp(mute, 0, 1)
    setp(e.r32(DP + 0x1C), 0, 1)                                                     # playing
    store, tick_store = e.r32(DP + 8), e.r32(DP + 0x18)
    def run():
        log.clear()
        for tk in range(6):
            setp(store, 0, 0); setp(store, 1, step); setp(store, 2, tk, 4)
            e.call(0x0804A5C6, DP, tick_store, maxins=8_000_000)
        return list(log)
    got = run(); note = e.r8(DP + 0x58)
    check([x for x in got if x[0] == "on"] == [("on", note, 100), ("on", note, 100)], f"Drum 1 muted, playing: its rollers on micro steps 0 / 2 play ({got})")
    e.at(100400); log.clear(); X.frame(e)
    check(("off", note) in log, f"the last roller hit's note-off from the LED task ({log})")
    setp(mute, 0, 0); e.uc.mem_write(DP + 0x59, bytes([0]))
    got2 = run()
    check([x for x in got2 if x[0] == "on"] == [("on", note, 100), ("on", note, 100)], f"unmuted: the step plays them as before ({got2})")
    del e; gc.collect()


def vcf_tests(img, man, check):
    import emu_sc22_4 as T4
    V = T4.V
    gc.collect(); e = T4.E20(img, man)
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    for _ in range(30): e.vtick()
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x05]))
    for _ in range(20): e.vtick()
    gfst = int(man["report"]["sc17"]["labels"]["c_gfst"], 16)
    e.call(gfst); blk = e.uc.reg_read(UC_ARM_REG_R0)
    v2 = lambda k: struct.unpack("b", bytes([e.r8(blk + V.V2_OFF + k)]))[0]
    e.btn(2); e.btn(8); e.call(L["c_vsetpage"], 0, 2)
    b0 = [v2(k) for k in range(8)]
    e.knob_raw(5, 4, shift=True); b1 = [v2(k) for k in range(8)]
    e.knob_raw(5, 4); b2 = [v2(k) for k in range(8)]
    check(b1 == b0 and b2[5] == b0[5] + 4 and b2[:5] + b2[6:] == b0[:5] + b0[6:], f"OSC 2 page: Shift + K6 nothing, K6 = BITSYNC ({b0} -> {b1} -> {b2})")
    # ---- gate retrigger
    import vcf21_dsp as VD
    import retrig as RT
    NON, NOFF = e.r32(V.NOTE_VT[0]) & ~1, e.r32(V.NOTE_VT[1]) & ~1
    note_on = lambda n, vel=90: e.call(NON, 0x20011334, 2, n, vel)
    note_off = lambda n: e.call(NOFF, 0x20011334, 2, n, 0)
    def ticks(n=20):
        out = []
        for _ in range(n):
            for w, ad in e.vtick():
                if ad == VD.VB0: out.append((w >> 16) & 0x7F)
        return out
    tailb = lambda: e.r8(e.r32(RT.SESSION_OBJ + 0x14) + RT.TAIL + RT.O_RT)
    note_on(60); ticks(); note_on(64); m = ticks()
    check(17 in m and 21 in m, f"retrigger on (default): the second note sends GATE and TRIG ({m[:6]})")
    note_off(64); note_off(60); ticks()
    shift = lambda on: e.set_p0(e.r32(T4.MGR + 0xC), 1 if on else 0)
    e.call(L["c_vsetpage"], 0, 0); shift(True); e.padr(RT.PAD_RT); e.rel(RT.PAD_RT); shift(False)
    note_on(60); ticks(); note_on(64); m = ticks()
    check(tailb() == 0xA1 and 18 in m and 17 not in m and 21 not in m, f"Shift + pad 29: off ({tailb():#x}); the second note: NOTE without GATE / TRIG ({m[:6]})")
    note_off(64); note_off(60); ticks()
    shift(True); e.padr(RT.PAD_RT); e.rel(RT.PAD_RT); shift(False)
    check(tailb() == 0xA0, f"again: on ({tailb():#x})")
    del e; gc.collect()
    # the LEDs (the EL harness: the whole LED task)
    e = T.EL(img); e.at(300000); e.transport(0)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05])); X.frame(e)
    e.btn(2); e.btn(8); X.frame(e)
    shift = lambda on: e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    shift(True); l_on = X.frame(e)[RT.PAD_RT]; e.pad(RT.PAD_RT); l_off = X.frame(e)[RT.PAD_RT]; shift(False); l_ns = X.frame(e)[RT.PAD_RT]
    check(l_on == RT.COL_ON and l_off == RT.COL_OFF and l_ns not in (RT.COL_ON, RT.COL_OFF), f"pad 29 with Shift: green on ({l_on:#x}), yellow off ({l_off:#x}); without Shift the chain order's ({l_ns:#x})")
    del e; gc.collect()


def arp_tests(img, man, check):
    import emu_arp as EAm, emu_sc40_8 as T8, arp as A
    from emu_sc08 import CONT
    from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC
    u = lambda a_: struct.unpack_from("<I", img, a_ - 0x08010000)[0]
    TXON, TXOFF = u(0x08059FC4) & ~1, u(0x08059FC8) & ~1

    class EB(T8.E8):
        """emu_arp's harness with the note interfaces running (MIDI: down to the transmitter)"""
        def __init__(self, img, man):
            super().__init__(img, man, {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()})
            self.A = {k: int(v, 16) for k, v in man["report"]["arp"]["labels"].items()}
            self.log, self.views = [], []
            def skip(uc, a, s_, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            def tx(uc, a, s_, d): self.log.append(("txon" if a == TXON else "txoff", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            def ifc(uc, a, s_, d): self.log.append(("on" if a == EAm.IFC_ON else "off", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            def lv(uc, a, s_, d): self.views.append(uc.reg_read(UC_ARM_REG_R0))
            for f in (TXON, TXOFF): self.uc.hook_add(UC_HOOK_CODE, tx, begin=f, end=f)
            for f in (EAm.IFC_ON, EAm.IFC_OFF): self.uc.hook_add(UC_HOOK_CODE, ifc, begin=f, end=f)
            self.uc.hook_add(UC_HOOK_CODE, lv, begin=A.LIVE_ON, end=A.LIVE_ON)
            for f in (A.REC_ON, 0x0801BE78, 0x08029A00): self.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
        setp = EAm.EA.setp; press = EAm.EA.press; release = EAm.EA.release; pad = EAm.EA.pad; unpad = EAm.EA.unpad
        ledtask = EAm.EA.ledtask; transport = EAm.EA.transport
    gc.collect(); e = EB(img, man)
    T_ = 2; p = e.playing(T_); e.call(e.A["c_arset"], T_, p, 0x80 | A.M_UP)
    e.set_p0(e.r32(CONT + 0x188), T_); e.press(T_); e.release(T_); e.press(9); e.release(9)
    e.transport(0); e.w32(A.HAL_TICK, 100000)
    e.pad(20, up=False); e.pad(17, up=False); first = [x for x in e.log if x[0] == "txon"]; e.log.clear()
    e.ledtask(); s0 = [x for x in e.log if x[0].startswith("tx")]; e.log.clear()
    e.w32(A.HAL_TICK, 100125); e.ledtask(); s1 = [x for x in e.log if x[0].startswith("tx")]; e.log.clear()
    e.unpad(17); e.unpad(20); s2 = [x for x in e.log if x[0].startswith("tx")]
    n0 = first[0][2] if len(first) == 1 else None
    check(len(first) == 1 and s0[:1] == [("txoff", T_, n0)] and len(s0) == 2 and s0[1][0] == "txon",
          f"MIDI 1, two pads: the first note ({first}) off at the transmitter before the arpeggio's first ({s0})")
    held = {}
    for k, _, n in first + s0 + s1 + s2:
        held[n] = held.get(n, 0) + (1 if k == "txon" else -1)
    check(all(v <= 0 for v in held.values()), f"letting go: nothing left on at the transmitter ({held}; {s1}, {s2})")
    del e; gc.collect()
    e = EB(img, man)
    vs = {}
    for t in range(4):
        e.set_p0(e.r32(CONT + 0x188), t); e.press(t); e.release(t); e.press(9); e.release(9); e.views.clear()
        e.pad(20, up=False); e.unpad(20); vs[t] = e.views[:1]
    check(all(vs[t] == [A.VIEW_IFC0 - 0x110 + A.VIEW_SZ * t] for t in range(4)), f"the four note tracks' views ({ {t: [hex(x) for x in v] for t, v in vs.items()} })")
    del e; gc.collect()
    # Synth 1, at the interfaces (the synth's sound path waits for the DSP: skipped below them)
    e = EAm.EA(img, man)
    p = e.playing(0); e.call(e.A["c_arset"], 0, p, 0x80 | A.M_UP)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)
    e.transport(0); e.w32(A.HAL_TICK, 100000); e.ifc.clear()
    e.pad(20, up=False); na = e.ifc[0][2]; e.pad(17, up=False); e.ifc.clear(); e.ledtask()
    check(e.ifc[:1] == [("off", A.VIEW_IFC0, na)] and len(e.ifc) == 2 and e.ifc[1][0] == "on", f"Synth 1: the first note off through its view's interface ({e.ifc})")
    e.unpad(17); e.unpad(20)
    del e; gc.collect()


def rate_tests(img, man, check):
    import emu_arp as EAm, arp as A, drumarp as DA
    from emu_sc08 import CONT
    gc.collect(); e = EAm.EA(img, man)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(12); e.release(12)
    p = e.playing(0)
    e.pad(16, shift=True); c17 = e.cfg(0, p); l17 = e.pads(shift=True)
    e.pad(23, shift=True); c24 = e.cfg(0, p); l24 = e.pads(shift=True)
    check((c17 >> 3) & 15 == 8 and (c24 >> 3) & 15 == 1 and l17[16] == A.COL_ON and l24[23] == A.COL_ON and l24[16] != A.COL_ON,
          f"Synth 1, Shift + pad 17 = 1/4 ({c17:#x}), pad 24 = 1/32T ({c24:#x}), the chosen one green ({l17[16]:#x}, {l24[23]:#x})")
    e.pad(20, shift=True); c21 = e.cfg(0, p); l21 = e.pads(shift=True)
    check((c21 >> 3) & 15 == 4 and l21[20] == A.COL_ON, f"pad 21 = 1/16, as the stock's sync rate pad 21 ({c21:#x})")
    e.press(12); e.release(12)
    da = {k: int(v, 16) for k, v in man["report"]["drumarp"]["labels"].items()}
    e.set_p0(e.r32(CONT + 0x188), 4); e.press(4); e.release(4); e.press(12); e.release(12)
    pd = e.playing(4)
    dcfg = lambda: (e.call(da["c_dacfg"], 0, pd), e.uc.reg_read(UC_ARM_REG_R0))[1]
    e.pad(16, shift=True); d17 = dcfg(); m17 = e.pads(shift=True)
    e.pad(23, shift=True); d24 = dcfg(); m24 = e.pads(shift=True)
    check((d17 >> 3) & 15 == 8 and (d24 >> 3) & 15 == 1 and m17[16] == DA.COL_ON and m24[23] == DA.COL_ON,
          f"Drum 1: Shift + pad 17 = 1/4 ({d17:#x}), pad 24 = 1/32T ({d24:#x}), green ({m17[16]:#x}, {m24[23]:#x})")
    del e; gc.collect()


def quant_tests(img, man, check):
    import emu_arp as EAm, arp as A, quant as Q, drumstore as DS
    from emu_sc08 import CONT
    gc.collect(); e = EAm.EA(img, man)
    tp = lambda: (e.call(0x080354FA, A.TRANSPORT, 0), e.r8(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    def shiftplay():
        e.set_p0(e.r32(MGR + 0xC), 1); e.press(17); e.release(17); e.set_p0(e.r32(MGR + 0xC), 0)
    unit = lambda n, m, v=100, ln=6: (n, ln, m, v)
    def steps(spec):
        out = bytearray()
        for s_ in range(8):
            us = spec.get(s_, [])
            out += bytes([sum(1 << i for i in range(len(us))), 5 if us else 7, 0, 0]) + b"".join(bytes(x) for x in us) + bytes([0, 0, 0, 0x60]) * (6 - len(us))
        return bytes(out)
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9)
    p = e.playing(0); base = e.settings(0, p) - 0x380
    e.uc.mem_write(base, steps({0: [unit(60, 2)], 1: [unit(64, 4)], 2: [unit(67, 0)], 3: [unit(69, 5)], 4: [unit(69, 1)], 7: [unit(72, 3)]}))
    e.setpat(0, p, 0, 7); e.transport(0)
    shiftplay()
    def st(s_):
        b_ = bytes(e.uc.mem_read(base + 28 * s_, 28))
        return b_[0], b_[1], [tuple(b_[4 + 4 * i:8 + 4 * i]) for i in range(6) if b_[0] >> i & 1]
    got = {s_: st(s_) for s_ in range(8)}
    check(got[0][2] == [(60, 6, 0, 100), (72, 6, 0, 100)] and got[1][2] == [] and got[2][2] == [(67, 6, 0, 100), (64, 6, 0, 100)],
          f"Shift + Play, Synth 1: micro 2 -> 0, micro 4 -> the next step, the last step's micro 3 -> the first ({got[0]}, {got[1]}, {got[2]})")
    check(got[3][2] == [] and got[4][2] == [(69, 6, 0, 100)] and got[7][2] == [] and tp() == 0,
          f"the same note on the next step: dropped ({got[3]}, {got[4]}); the transport stays stopped ({tp()})")
    e.uc.mem_write(base, steps({1: [unit(62, 3)]})); shiftplay(); g2 = st(2)
    check(g2 == (1, 5, [(62, 6, 0, 100)]), f"into an empty step: its probability with it ({g2})")
    # Drum 1
    e.set_p0(e.r32(CONT + 0x188), 4); e.press(4); e.release(4); e.press(9); e.release(9)
    pd = e.playing(4); dbase = e.settings(4, pd) - 0x80
    vel = [90, 80, 0, 70, 0, 0, 0, 60] + [0] * 24
    prob = [7, 5, 7, 7, 7, 7, 7, 4] + [7] * 24
    flip = [0xFF, 3, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 2] + [0xFF] * 24
    mic = [0b100, 0b10000, 0, 0b101, 0, 0, 0, 0b100000] + [0] * 24
    e.uc.mem_write(dbase, bytes(vel) + bytes(prob) + bytes(flip) + bytes(mic))
    e.setpat(4, pd, 0, 7)
    store = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    follows = e.r32(store + 0x18) == dbase + 0xA8
    shiftplay()
    arr = lambda off: list(e.uc.mem_read(dbase + off, 8))
    v_, pr, fl, mc = arr(0), arr(0x20), arr(0x40), arr(0x60)
    check(mc[:4] == [1, 0, 1, 0b101] and v_[2] == 80 and pr[2] == 5 and fl[2] == 3 and v_[1] == 0 and fl[1] == 0xFF and mc[7] == 0 and v_[7] == 0,
          f"Drum 1: micro 2 -> 0, micro 4 -> the next step with its velocity / probability / flip, the roll kept, the last step's -> the first ({v_}, {pr}, {fl}, {mc})")
    w = (e.call(0x0803542C, store, 16), e.r32(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    check(follows and w == struct.unpack("<I", bytes(mc[:4]))[0], f"the drum's edit store synced (follows the pattern {follows}, word {w:#x})")
    del e; gc.collect()
    # the Play LED (the EL harness: the whole LED task)
    e = T.EL(img); e.at(300000); e.transport(0)
    e.btn(0); X.frame(e)
    sh = lambda on: e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    l0 = X.frame(e)[Q.LED_PLAY]; sh(True); l1 = X.frame(e)[Q.LED_PLAY]
    e.btn(17); l2 = X.frame(e)[Q.LED_PLAY]; sh(False); l3 = X.frame(e)[Q.LED_PLAY]; sh(True); l4 = X.frame(e)[Q.LED_PLAY]; sh(False)
    check(l1 == Q.COL_AV and l2 == Q.COL_DONE and l3 == l0 and l4 == Q.COL_AV,
          f"the Play LED: with Shift yellow ({l1:#x}), green after ({l2:#x}), let go: as before ({l3:#x} / {l0:#x}), Shift again yellow ({l4:#x})")
    del e; gc.collect()


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
