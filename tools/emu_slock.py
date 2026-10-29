"""SC49.5 (slock): the drums' extra lane, phase 2: state locks, ramps, the drums' automation view.

    python tools/emu_slock.py BUILD.bin manifest.json

Through the controller, the drum player's step and the LED task (emu_lazysave's harness), Drum 1:
  * the pool: states 1-20 at the tail + 376, 21-48 at + 680, 49-80 in the scenes' spare bytes 2-3 (2 a scene); 0 / 81 = none;
  * the 4-bit scale: 0 / 64 / 127 exact, every value within 5 of its level;
  * Record held + 1-16/17-32 = state-lock mode, the lane erased in the 8 patterns, Record's state back;
  * a state (c_slkey) holds the 14 values; the step played (micro step 0) = them back after they changed;
  * a ramp (state, 127 x 3, state): micro step 0 of its middle step = halfway, the drum players' slot 2 at micro step 3 = 15 / 24 of the way;
  * recording (playing, Record): 16 / 32 / 48 at steps 2 / 4 / 6 = states at 2 and 6, ramp steps 3-5; then 16 at step 8 = a turn: a state, 7
    untouched; K6 turned at step 10 = a state there;
  * Clear + K6 to the left = the playing pattern's lane erased;
  * the automation view: Velocity in the drum's Velocity view = latched (the view stays); steps with a state yellow, ramp steps dim yellow;
    holding a step and tapping another = a ramp; Velocity again = off; latched, then the Note view = off; Shift + Velocity = the stock's;
  * Record held: the 8 knob LEDs white; Record held + a step in the Note view = a state at that step;
  * Record held + 1-16/17-32 again = the lane (chromatic), the lane erased; the automation view on a drum with the lane: its steps yellow,
    Velocity twice latches it (fixed velocity untouched), no ramps.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import dpitch as DP  # noqa: E402
import lanex as LX  # noqa: E402
import slock as SL  # noqa: E402

MGR = T.MGR
STEP = 0x0804A714
RES = 6                                                  # persist19's code 6 (K6, the resonance): value 4 of the state


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    def lab(m, k): return int(rep[m]["labels"][k], 16)
    def S(k): return int((rep["slock"]["labels"].get(k) or rep["slockb"]["labels"][k]), 16)
    e = T.EL(Path(img).read_bytes()); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=40_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    def setp(store, k, v, n=1):
        for fn in (0x080354FA, 0x0803542C): e.uc.mem_write(r0(fn, store, k), v.to_bytes(n, "little"))
    getp = lambda store, k: e.r8(r0(0x0803542C, store, k))
    eng = lambda d=0: e.r32(DP.ENG + 0x30 + 4 * (4 + d))
    base = lambda d=0: e.r32(DP.DP0 + DP.DP_SZ * d + 0x48) + DP.PAT_SZ * getp(eng(d), 0)
    code_at = lambda st, b=None: r0(lab("lanex", "c_xlrd"), b if b is not None else base(), st)
    asg = lambda: r0(lab("lanex", "c_xlasg"), 0)
    btn = lambda i, down: e.call(0x08033320 if down else 0x0803381A, MGR, i, maxins=8_000_000)
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
    shift = lambda on: e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    setv = lambda i, v: e.call(S("c_slsetp"), 0, i, v, maxins=8_000_000)
    getq = lambda i: r0(S("c_slgetp"), 0, i)
    res = lambda: r0(lab("lanex", "c_xlget"), 0, RES)
    nibs = lambda: [getq(i) for i in range(SL.NV)]
    rec = e.r32(LX.SESSION_OBJ + 0x14)

    # ---- the pool
    want = {(1, 0): rec + LX.TAIL + 376, (20, 7): rec + LX.TAIL + 376 + 159, (21, 0): rec + LX.TAIL + 680, (48, 7): rec + LX.TAIL + 680 + 223,
            (49, 0): rec + 0x42, (49, 1): rec + 0x43, (49, 2): rec + 0x46, (49, 7): rec + 0x42 + 12 + 1, (50, 0): rec + 0x42 + 16,
            (51, 0): rec + 0x42 + 40, (80, 7): rec + 0x40 + 40 * 15 + 2 + 16 + 12 + 1, (81, 0): 0, (0, 0): 0}
    got = {k: r0(S("c_slb"), k[0], k[1]) for k in want}
    check(got == want, f"the pool's addresses: {sorted((k, hex(v)) for k, v in got.items() if v != want[k]) or 'all as designed'}")
    enc = [r0(S("c_slenc"), u) for u in range(128)]
    dec = [r0(S("c_sldec"), q) for q in range(16)]
    err = max(abs(dec[enc[u]] - u) for u in range(128))
    check(enc[0] == 0 and enc[64] == 8 and enc[127] == 15 and dec[0] == 0 and dec[8] == 64 and dec[15] == 127 and err <= 5,
          f"the 4-bit scale: 0 / 64 / 127 exact, the largest error {err} ({dec})")

    # ---- the mode switch (Drum 1's view)
    e.btn(4); X.frame(e)
    view = e.r8(MGR + 0x152)
    b0, b5 = r0(S("c_slpat"), 0, 0), r0(S("c_slpat"), 0, 5)
    e.call(lab("lanex", "c_xlwr"), 0, 3, 40, b0, maxins=4_000_000); e.call(lab("lanex", "c_xlwr"), 0, 7, 50, b5, maxins=4_000_000)
    p1 = getp(DP.TRANSPORT, 1)
    btn(16, True); btn(21, True); btn(21, False); btn(16, False)
    check(asg() == SL.STATE and code_at(3, b0) == 0 and code_at(7, b5) == 0 and getp(DP.TRANSPORT, 1) == p1,
          f"view {view}, Record held + 1-16/17-32: state locks ({asg():#x}), the lane erased in patterns 0 / 5 ({code_at(3, b0)}, {code_at(7, b5)}), Record as it was")

    # ---- a state, played back
    b = base()
    for i, v in ((RES - 1, 96), (8, 2), (9, 5), (10, 1), (11, 40), (12, 16), (13, 8)): setv(i, v)
    q_state = nibs()
    k = r0(S("c_slkey"), 0, 9, b)
    for i, v in ((RES - 1, 10), (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0)): setv(i, v)
    q_changed = nibs()
    def step(st, micro=0):
        store = e.r32(DP.DP0 + 8)
        setp(store, 0, getp(eng(), 0)); setp(store, 1, st); setp(store, 2, micro, 4)
        e.call(STEP, DP.DP0, maxins=40_000_000)
    step(9)
    check(1 <= k <= SL.NST and code_at(9) == k and q_changed != q_state and nibs() == q_state,
          f"a state ({k}) at step 9: the 14 values back when it plays ({q_state} / changed {q_changed} / now {nibs()})")

    # ---- a ramp
    setv(RES - 1, 0); ka = r0(S("c_slkey"), 0, 4, b); setv(RES - 1, 127); kb = r0(S("c_slkey"), 0, 8, b)
    for st in (5, 6, 7): e.call(lab("lanex", "c_xlwr"), 0, st, SL.RAMP, b, maxins=4_000_000)
    setv(RES - 1, 30)
    step(6)
    mid = res()
    ctx = bytes(e.uc.mem_read(SL.RAM + SL.O_CTX, 5))
    slot2 = e.r32(SL.DP_VT + 8) & ~1
    e.call(slot2, DP.DP0, getp(eng(), 0), 6, 3, maxins=40_000_000)
    m3 = res()
    check(ka != kb and mid == 127 * 12 // 24 and tuple(ctx) == (6, 4, 8, ka, kb) and m3 == 127 * 15 // 24,
          f"a ramp 4 -> 8 (states {ka}, {kb}): step 6 at micro step 0 = {mid} (63), its context {tuple(ctx)}, micro step 3 = {m3} (79)")

    # ---- recording: a sweep, then a turn
    for st in range(32): e.call(lab("lanex", "c_xlwr"), 0, st, 0, b, maxins=4_000_000)
    for kk in range(4): e.uc.mem_write(SL.RAM + SL.O_KP + kk, b"\xff"); e.uc.mem_write(SL.RAM + SL.O_KQ + kk, b"\xff")
    setp(DP.TRANSPORT, 0, 1); setp(DP.TRANSPORT, 1, 1)
    for st, v in ((2, 16), (4, 32), (6, 48)):
        setp(eng(), 1, st); setv(RES - 1, v); e.call(S("c_slrec"), 0, maxins=40_000_000)
    sweep = [code_at(st) for st in range(2, 9)]
    setp(eng(), 1, 8); setv(RES - 1, 16); e.call(S("c_slrec"), 0, maxins=40_000_000)
    turn = [code_at(st) for st in range(2, 9)]
    setp(eng(), 1, 10); knob(5, 5)
    k10 = code_at(10)
    setp(DP.TRANSPORT, 1, 0); setp(DP.TRANSPORT, 0, 0)
    isst = lambda c: 1 <= c <= SL.NST
    check(isst(sweep[0]) and sweep[1:4] == [SL.RAMP] * 3 and isst(sweep[4]) and sweep[5:] == [0, 0],
          f"recording 16 / 32 / 48 at steps 2 / 4 / 6: states at 2 and 6, ramp steps 3-5 ({sweep})")
    check(turn[:5] == sweep[:5] and turn[5] == 0 and isst(turn[6]), f"then 16 at step 8 (a turn): 7 untouched, a state at 8 ({turn})")
    check(isst(k10), f"recording, K6 turned at step 10: a state there ({k10})")

    # ---- Clear + K6 left
    n0 = sum(1 for st in range(32) if code_at(st))
    btn(23, True); knob(5, -1); btn(23, False)
    check(n0 > 0 and not any(code_at(st) for st in range(32)), f"Clear + K6 left: the lane erased ({n0} steps -> none)")

    # ---- the automation view
    ks = r0(S("c_slkey"), 0, 2, b)
    for st in (3, 4): e.call(lab("lanex", "c_xlwr"), 0, st, SL.RAMP, b, maxins=4_000_000)
    ke = r0(S("c_slkey"), 0, 5, b)
    fixed = lambda: getp(e.r32(MGR + 0x78), 2) & 2
    e.btn(10); X.frame(e)
    vel, fx0 = e.r8(MGR + 0x152), fixed()
    e.btn(10); fr = X.frame(e)
    latched = (e.r8(SL.RAM + SL.O_LATCH), e.r8(MGR + 0x152))
    check(vel == 38 and latched == (1, 38) and fixed() == fx0, f"the Velocity view ({vel}), Velocity again: latched, the view stays ({latched}), fixed velocity untouched ({fx0} / {fixed()})")
    check(fr[2] == SL.YELLOW and fr[3] == SL.YELLOW_DIM and fr[4] == SL.YELLOW_DIM and fr[5] == SL.YELLOW,
          f"the step pads: states yellow, ramp steps dim yellow ({[hex(x) for x in fr[:8]]})")
    e.call(PRESS, MGR, 9, 100, maxins=8_000_000); e.call(PRESS, MGR, 13, 100, maxins=8_000_000)
    e.call(RELEASE, MGR, 13, maxins=8_000_000); e.call(RELEASE, MGR, 9, maxins=8_000_000)
    drawn = [code_at(st) for st in range(9, 14)]
    check(isst(drawn[0]) and drawn[1:4] == [SL.RAMP] * 3 and isst(drawn[4]) and e.r8(SL.RAM + SL.O_HELD) == 0xFF,
          f"hold step 10, tap step 14: a ramp ({drawn}), the held step let go")
    e.btn(10); X.frame(e)
    check(e.r8(SL.RAM + SL.O_LATCH) == 0 and e.r8(MGR + 0x152) == 38, f"Velocity again: off ({e.r8(SL.RAM + SL.O_LATCH)})")
    e.btn(10); X.frame(e); e.btn(9); X.frame(e)
    check(e.r8(SL.RAM + SL.O_LATCH) == 0 and e.r8(MGR + 0x152) != 38, f"latched, then the Note view ({e.r8(MGR + 0x152)}): off")
    e.btn(10); X.frame(e)
    f0 = fixed(); shift(True); e.btn(10); shift(False); X.frame(e)
    check(fixed() != f0 and e.r8(SL.RAM + SL.O_LATCH) == 0, f"Shift + Velocity: the stock's fixed velocity ({f0} -> {fixed()}), no latch")
    if fixed() != f0:
        shift(True); e.btn(10); shift(False)

    # ---- Record held: the knob LEDs; Record held + a step in the Note view
    e.btn(9); X.frame(e)
    mh = r0(lab("sc18", "c_mh"), 0)
    btn(16, True)
    buf = r0(e.r32(LX.MH_SLOT7) & ~1, mh)
    kl = struct.unpack("<8H", bytes(e.uc.mem_read(buf, 16)))
    btn(16, False)
    check(all(x == LX.KNOB_WHITE for x in kl), f"Record held, state-lock mode: the 8 knob LEDs white ({[hex(x) for x in kl]})")
    sb = r0(S("c_slsel"), 0)
    for st in range(32): e.call(lab("lanex", "c_xlwr"), 0, st, 0, sb, maxins=4_000_000)
    btn(16, True); e.pad(6); btn(16, False)
    check(isst(code_at(6, sb)), f"Record held + step 7 in the Note view ({e.r8(MGR + 0x152)}): a state ({code_at(6, sb)})")

    # ---- back to the lane
    e.call(lab("lanex", "c_xlwr"), 0, 11, 9, b5, maxins=4_000_000)
    btn(16, True); btn(21, True); btn(21, False); btn(16, False)
    check(asg() == 0 and code_at(6, sb) == 0 and code_at(11, b5) == 0, f"Record held + 1-16/17-32 again: the chromatic lane ({asg()}), the lane erased")

    # ---- the automation view on a drum with the lane: its lane's steps yellow, Velocity twice = the view (not fixed velocity), no ramps
    e.btn(10); X.frame(e)
    lb = base()
    e.call(lab("lanex", "c_xlwr"), 0, 3, 50, lb, maxins=4_000_000)
    fx1 = fixed()
    e.btn(10); fr = X.frame(e)
    lat = e.r8(SL.RAM + SL.O_LATCH)
    e.call(PRESS, MGR, 1, 100, maxins=8_000_000); e.call(PRESS, MGR, 5, 100, maxins=8_000_000)
    e.call(RELEASE, MGR, 5, maxins=8_000_000); e.call(RELEASE, MGR, 1, maxins=8_000_000)
    codes = [code_at(st, lb) for st in range(1, 6)]
    check(lat == 1 and fixed() == fx1 and fr[3] == SL.YELLOW and codes == [0, 0, 50, 0, 0] and e.r8(SL.RAM + SL.O_HELD) == 0xFF,
          f"a drum with the lane: Velocity twice = the automation view ({lat}), fixed velocity untouched ({fx1} / {fixed()}), step 4 yellow "
          f"({fr[3]:#x}), hold step 2 + tap step 6 = no ramp ({codes})")
    e.btn(10); X.frame(e)
    check(e.r8(SL.RAM + SL.O_LATCH) == 0, f"Velocity again: off ({e.r8(SL.RAM + SL.O_LATCH)})")
    del e; gc.collect()
    print(f"{Path(img).stem} SLOCK RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
