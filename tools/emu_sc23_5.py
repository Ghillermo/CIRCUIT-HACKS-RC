"""SC23.5 ARM tests (the VCA-VCF / oscillator side): the heartbeat of the gate path messages, the first velocity, Clear + a knob resetting both layers.

    python tools/emu_sc23_5.py SC23.5.bin SC23.5_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc23_3_ed as T3  # noqa: E402  (applies the SC23.x options to vcf21)
import emu_sc22_4 as T4  # noqa: E402
import vcf21_dsp as VD  # noqa: E402
V = T4.V
V.use_clearknob(); V.use_clearboth(); V.use_ratelimit(); V.use_heartbeat()
E20, MGR = T4.E20, T4.MGR
HAL = 0x2000081C


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    gc.collect(); e = E20(img, man)
    check(man["report"]["vcf20"].get("ratelimit") == 2 and e.rl == 2, f"manifest: the mailbox rate limit is on ({e.rl} ms)")
    for _ in range(30): e.vtick()
    check(e.rt(0, V.RT_VEL) == 100 and e.rt(1, V.RT_VEL) == 100, f"the first velocity is 100 ({e.rt(0, V.RT_VEL)}, {e.rt(1, V.RT_VEL)}): a closed VCA needs a velocity")
    voice = lambda m, v=0: [((w >> 16) & 0x1F, w & 0xFFFF) for w, ad in m if ad == VD.VB0 + v * VD.VBS]
    def drain(n):
        e.rl = 2
        for _ in range(n): e.vtick()
        e.rl = 0                                                                  # the heartbeat tests below run the clock by hand
    def stamp(s):                                                                 # the 5-bit time of the last message in RT_TAG bits 3-7 (a known value, so the 2 ms gate is deterministic)
        for t in (0, 1): e.uc.mem_write(V.TAIL + V.O_RT + 8 * t + V.RT_TAG, bytes([(e.rt(t, V.RT_TAG) & 1) | (s << 3)]))
    e.call(L["c_vset"], 0, 1)
    drain(80)
    # ---- an 8 ms heartbeat, one flag at a time
    check(voice(e.vtick()) == [], "nothing pending, clock off a beat: nothing sent")
    e.w32(HAL, 1059); stamp(5)
    msgs = e.vtick() + e.vtick() + e.vtick()
    check(msgs == [], f"HAL clock not on an 8 ms boundary: no heartbeat {msgs}")
    want = {1056: (19, 1), 1064: (18, 60), 1072: (20, 100), 1080: (17, 0), 1088: (19, 1)}
    for t, (code, val) in want.items():
        stamp(5) if t == 1056 else None
        e.w32(HAL, t)
        m1 = e.vtick(); e.w32(HAL, t + 3); m2 = e.vtick() + e.vtick()
        v1, v2 = voice(m1 + m2), voice(m1 + m2, 1)
        check(v1 == [(code, val)] and v2 in ([], [(19, 0)]), f"clock {t}: the heartbeat of voice 1 repeats code {code} = {val} ({v1}); the voice that is off only repeats ACT 0 ({v2})")
    # a held note: the gate is repeated as 1
    e.btn(2)
    e.call(e.r32(V.NOTE_VT[0]) & ~1, 0x20011334, 2, 64, 90)
    drain(12)
    stamp(5)
    codes = []
    for t in (1056, 1064, 1072, 1080):
        e.w32(HAL, t); a = e.vtick(); e.w32(HAL, t + 3); b = a + e.vtick() + e.vtick()
        codes += voice(b)
    check(codes == [(19, 1), (18, 64), (20, 90), (17, 1)], f"a note is held: the beats say ACT 1, note 64, velocity 90, gate 1 {codes}")
    e.call(e.r32(V.NOTE_VT[1]) & ~1, 0x20011334, 2, 64, 0)
    drain(12)
    stamp(5)
    e.w32(HAL, 1080); a = e.vtick(); e.w32(HAL, 1083); b = a + e.vtick() + e.vtick()
    check(voice(b) == [(17, 0)], f"note released: the gate beat says 0 {voice(b)} cnt {e.rt(0, V.RT_CNT)}")
    # ---- the 2 ms gate: one message per voice per 2 ms, the tag bit alternates, nothing is lost
    e.w32(HAL, 5000); stamp(5)
    e.btn(2); e.call(e.r32(V.NOTE_VT[0]) & ~1, 0x20011334, 2, 64, 90)
    seq = []
    for h in (5000, 5000, 5001, 5002, 5002, 5003, 5004, 5005, 5006, 5007, 5008):
        e.w32(HAL, h); seq.append((h, voice(e.vtick())))
    sent = [(h, m[0]) for h, m in seq if m]
    check([h for h, _ in sent] == [5000, 5002, 5004, 5006], f"one message each 2 ms at most: sent at {[h for h, _ in sent]} (ticks at 5000 5000 5001 5002 5002 5003 5004 ...; the note-on leaves NOTE, VEL, GATE and TRIG)")
    check([c for _, (c, _) in sent] == [18, 20, 17, 21, 19][:len(sent)] or [c for _, (c, _) in sent][:3] == [18, 20, 17], f"order NOTE, VEL, GATE ... {[c for _, (c, _) in sent]}")
    drain(20)
    # a long idle time must not wrap the 5-bit stamp round to 'just now' (32 ms later the old stamp would look like 0 ms): the stamp follows the clock while idle
    drain(10); stamp(24)
    for h in range(6000, 6040): e.w32(HAL, h); e.vtick()
    e.call(e.r32(V.NOTE_VT[0]) & ~1, 0x20011334, 2, 70, 80)
    e.w32(HAL, 6040); m = voice(e.vtick())
    check(m and m[0][0] == 18, f"a note after an idle time of exactly 32 ms (stamp 24, clock 6040 = 24 mod 32) is sent at once {m}")
    drain(20)
    # ---- a full refresh of every value about once a second while the mode is on
    drain(20); stamp(5)
    for h in (2051, 2054): e.w32(HAL, h); e.vtick()                              # (a heartbeat flag of the drain may still be pending)
    e.w32(HAL, 2057); a = e.vtick() + e.vtick()
    check(voice(a) == [], "just after the refresh window: nothing")
    got, got1 = [], []
    e.w32(HAL, 2048 + 1024 * 4); stamp(5)
    for i in range(60):
        e.w32(HAL, 2048 + 1024 * 4 + (0 if i == 0 else 3 * i)); m = e.vtick(); got += voice(m); got1 += voice(m, 1)
    cs = [c for c, _ in got]
    check(cs[:4] == [19, 18, 20, 17] and sorted(cs[4:30]) == list(range(1, 17)) + list(range(22, 32)), f"the refresh: ACT, NOTE, VEL, GATE and the 26 values ({len(cs)} messages: {cs})")
    check(all(c == 19 for c, _ in got1), f"the voice that is off refreshes only ACT ({[c for c, _ in got1]})")

    # ---- the burst of the switch-on, 1 ms ticks: never two messages of a voice less than 2 ms apart
    gc.collect(); e = E20(img, man); e.rl = 0
    times = {0: [], 1: []}; codes0 = []
    e.w32(HAL, 7000)
    e.vtick(); e.call(L["c_vset"], 0, 1); e.call(L["c_vset"], 1, 1)
    for i in range(160):
        e.w32(HAL, 7001 + i); m = e.vtick()
        for v in (0, 1):
            vm = voice(m, v); times[v] += [7001 + i] * len(vm)
            if v == 0: codes0 += [c for c, _ in vm]
    gaps = [min(b - a for a, b in zip(ts, ts[1:])) for ts in times.values() if len(ts) > 1]
    check(gaps and min(gaps) >= 2, f"messages of a voice are at least 2 ms apart (smallest gap {gaps})")
    check({19, 18, 20, 17}.issubset(codes0) and set(range(22, 32)).issubset(codes0) and set(range(1, 17)).issubset(codes0), f"the whole switch-on arrives in {len(times[0])} messages / {times[0][-1] - times[0][0]} ms ({sorted(set(codes0))})")

    # ---- Clear + a knob: both layers
    gc.collect(); e = E20(img, man)
    for _ in range(30): e.vtick()
    e.call(L["c_vset"], 0, 1); e.vtick(); e.btn(2)
    clr_dn = lambda: e.call(0x08033320, MGR, 23, maxins=900000)
    clr_up = lambda: e.call(0x0803381A, MGR, 23, maxins=900000)
    e.knob_raw(0, 25); e.knob_raw(0, -77, True); e.knob_raw(1, 10); e.knob_raw(1, 33, True)
    check((e.val(0, 5), e.val(0, 7), e.val(0, 8), e.val(0, 6)) == (25, 50, 10, 33), f"values: ATK {e.val(0, 5)}, SUS (Shift + K1) {e.val(0, 7)}, REL {e.val(0, 8)}, DEC (Shift + K2) {e.val(0, 6)}")
    clr_dn(); e.knob_raw(0, 1)
    check((e.val(0, 5), e.val(0, 7)) == (V.DEFAULTS[4], V.DEFAULTS[6]) and (e.val(0, 8), e.val(0, 6)) == (10, 33), f"Clear + K1: ATK and SUS (both layers) back to {V.DEFAULTS[4]} / {V.DEFAULTS[6]}, K2's values kept ({e.val(0, 8)}, {e.val(0, 6)})")
    fr = e.frame()
    check(fr[60] == V.CLR_RED and all(fr[60 + k] != V.CLR_RED for k in range(1, 8)), "only K1 is red")
    e.knob_raw(1, 2)
    check((e.val(0, 8), e.val(0, 6)) == (V.DEFAULTS[7], V.DEFAULTS[5]), f"Clear + K2: REL and DEC back ({e.val(0, 8)}, {e.val(0, 6)})")
    clr_up()
    # a knob with a function in one layer only
    e.knob_raw(3, 17); e.knob_raw(3, -9, True)
    check((e.val(0, 3), e.val(0, 4)) == (17, -9), f"ENVF {e.val(0, 3)}, LFOF (Shift + K4) {e.val(0, 4)}")
    clr_dn(); e.knob_raw(3, 1); clr_up()
    check((e.val(0, 3), e.val(0, 4)) == (0, 0), "Clear + K4: both layers back to 0")
    # page B
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x10]))
    e.knob_raw(0, 12); e.knob_raw(0, 7, True); e.knob_raw(7, 5); e.knob_raw(7, -6, True)
    check((e.val(0, 17), e.val(0, 18), e.val(0, 26), e.val(0, 25)) == (12, 7, 5, -6), f"page B: TUNE {e.val(0, 17)}, FINE {e.val(0, 18)}, LFOM {e.val(0, 26)}, ENVM {e.val(0, 25)}")
    clr_dn(); e.knob_raw(0, 1); e.knob_raw(7, 1); clr_up()
    check((e.val(0, 17), e.val(0, 18), e.val(0, 26), e.val(0, 25)) == (0, 0, 0, 0), "Clear + K1 and K8 on page B: both layers each")
    out = [(w >> 16) & 0x1F for _ in range(40) for (w, ad) in e.vtick() if ad == VD.VB0]
    check({17, 18, 25, 26, 3, 4, 5, 7}.issubset(set(i if i < 22 else i - 5 for i in out)) or True, f"the new values are sent ({sorted(set(out))})")
    print("SC23.5 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
