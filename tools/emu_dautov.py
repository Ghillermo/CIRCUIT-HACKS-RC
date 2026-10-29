"""SC49.7 test (dautov): the drums' automation view (Shift in a drum's Velocity view, or latched).

    python tools/emu_dautov.py BUILD.bin manifest.json
Through the controller and the LED task (emu_lazysave's harness), Drum 1, the pattern it shows:
  * lanex's c_xlcode stops at 125 (code 126 = the mark);
  * with Shift: steps with a byte in lanes 0-3 or an extra-lane code yellow, a marked step red, the others the stock's;
  * Shift + a yellow step (decay 30): the decay knob at 30, its LED (K3) yellow; Shift + another (distortion 90, micro step 2): both moved, K8
    yellow too; the pads' releases swallowed; Shift let go: decay and distortion as before, the LEDs back;
  * Shift + a step with a chromatic code (S 70): dpitch's S 70, back to 64 after; with lane 0's 0x80 | S: the same;
  * Shift + a step without automation = marked (code 126), again = unmarked; without Shift (not latched): the stock's (no mark);
  * latched (Velocity twice), Clear held + a step: lanes 0-3 and the extra lane of that step erased, its hit kept;
  * a marked step played (the drum player's step, micro step 0): decay back to the project's (the record) and the extra lane's code parameter
    (resonance) back to persist19's byte in the record;
  * state locks: Shift + a step with a state = the 14 values of the state; Shift let go = the 14 values exactly as before; hold a step and tap
    another = slock's ramp, the preview put back first.
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
import dautov as DV  # noqa: E402

MGR = T.MGR
STEP = 0x0804A714


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
    shift = lambda on: e.set_p0(e.r32(MGR + 0xC), 1 if on else 0)
    btn = lambda i, down: e.call(0x08033320 if down else 0x0803381A, MGR, i, maxins=8_000_000)
    press = lambda p: e.call(PRESS, MGR, p, 100, maxins=8_000_000)
    release = lambda p: e.call(RELEASE, MGR, p, maxins=8_000_000)
    wr = lambda st, c, b: e.call(lab("lanex", "c_xlwr"), 0, st, c, b, maxins=4_000_000)
    rd = lambda st, b: r0(lab("lanex", "c_xlrd"), b, st)
    lane = lambda b, k, st: bytes(e.uc.mem_read(b + 0xA8 + 192 * k + 6 * st, 6))
    def setlane(b, k, st, m, v):
        e.uc.mem_write(b + 0xA8 + 192 * k + 6 * st, bytes([0xFF]) * 6); e.uc.mem_write(b + 0xA8 + 192 * k + 6 * st + m, bytes([v]))
    mh = r0(lab("sc18", "c_mh"), 0); kst = e.r32(mh + 0xC)
    knobs = lambda: [getp(kst, k) for k in range(4)]
    kled = lambda: struct.unpack("<8H", bytes(e.uc.mem_read(r0(e.r32(LX.MH_SLOT7) & ~1, mh), 16)))
    snow = lambda: r0(lab("dpitch", "c_dpnow"), 0)

    xc = lab("lanex", "c_xlcode")
    cl = [r0(xc, v) for v in (123, 124, 125, 126, 127)]
    check(cl == [124, 125, 125, 125, 125], f"c_xlcode stops at 125 ({cl})")

    e.btn(4); X.frame(e)
    sb = r0(S("c_slsel"), 0)
    for st in range(32): wr(st, 0, sb)
    e.uc.mem_write(sb + 0xA8, bytes([0xFF]) * 0x600)
    vel = bytearray(32); vel[10] = 100; mic = bytearray(32); mic[10] = 2
    e.uc.mem_write(sb, bytes(vel)); e.uc.mem_write(sb + 0x60, bytes(mic))
    for st in range(32): wr(st, 0, sb)                                  # (the edit store synced)
    setlane(sb, 1, 2, 0, 30); setlane(sb, 2, 3, 2, 90); wr(5, 71, sb); setlane(sb, 0, 6, 0, 0x80 | 60); wr(8, DV.MARK, sb); setlane(sb, 3, 10, 0, 20)
    e.btn(10); X.frame(e)
    k0, s0, l0 = knobs(), snow(), kled()
    shift(True); fr = X.frame(e)
    want = {2: DV.YELLOW, 3: DV.YELLOW, 5: DV.YELLOW, 6: DV.YELLOW, 8: DV.RED, 10: DV.YELLOW}
    got = {st: fr[st] & 0xFF for st in want}
    plain = [fr[st] & 0xFF for st in (0, 1, 4, 7, 9)]
    check(got == want and not any(x in (DV.YELLOW, DV.RED) for x in plain),
          f"Shift: automation yellow, the mark red ({ {k: hex(v) for k, v in got.items()} }), the others the stock's ({[hex(x) for x in plain]})")
    press(2); k1, l1 = knobs(), kled(); release(2)
    press(3); k2, l2 = knobs(), kled(); release(3)
    sw = e.r8(DV.RAM + DV.O_SW)
    check(k1[1] == 30 and k1[2] == k0[2] and l1[2] & 0xFF == DV.YELLOW and k2[1] == 30 and k2[2] == 90 and l2[7] & 0xFF == DV.YELLOW and sw == 0,
          f"Shift + step 3 (decay 30): {k1}, K3 {l1[2]:#x}; + step 4 (distortion 90): {k2}, K8 {l2[7]:#x}; releases swallowed ({sw})")
    shift(False); X.frame(e); k3, l3 = knobs(), kled()
    check(k3 == k0 and l3 == l0 and e.r8(DV.RAM + DV.O_ACT) == 0, f"Shift let go: the knobs as before ({k3} / {k0}), their LEDs too")
    shift(True); press(5); s1 = snow(); release(5); shift(False); X.frame(e); s2 = snow()
    shift(True); press(6); s3 = snow(); release(6); shift(False); X.frame(e); s4 = snow()
    check(s1 == 70 and s2 == s0 and s3 == 60 and s4 == s0, f"the chromatic code (S {s1}) and lane 0's 0x80 | S ({s3}) previewed, back to {s0} ({s2}, {s4})")
    shift(True); press(9); m1 = rd(9, sb); release(9); press(9); m2 = rd(9, sb); release(9); press(8); m3 = rd(8, sb); release(8); shift(False); X.frame(e)
    press(9); m4 = rd(9, sb); release(9)
    check(m1 == DV.MARK and m2 == 0 and m3 == 0 and m4 == 0, f"Shift + step 10: marked ({m1}), again: not ({m2}); the red step 9: unmarked ({m3}); without Shift: nothing ({m4})")
    # latched: Clear + step
    e.btn(10); X.frame(e)
    lat = e.r8(SL.RAM + SL.O_LATCH)
    wr(10, 33, sb)
    btn(23, True); press(10); release(10); btn(23, False)
    v10 = e.r8(sb + 10)
    check(lat == 1 and lane(sb, 3, 10) == b"\xff" * 6 and rd(10, sb) == 0 and v10 == 100 and e.r8(sb + 0x60 + 10) & 0x3F == 2,
          f"latched ({lat}), Clear + step 11: lanes and code erased ({lane(sb, 3, 10).hex()}, {rd(10, sb)}), the hit kept ({v10})")
    e.btn(10); X.frame(e)
    # a marked step played
    rec = e.r32(LX.SESSION_OBJ + 0x14)
    rdec = e.r8(rec + DV.REC_DRUMS + 1)
    e.call(lab("lanex", "c_xlset"), 0, 6, maxins=4_000_000)
    off = DV.rec_offsets()[5]
    rb = e.r8(rec + DV.REC_XM + off)
    e.uc.mem_write(rec + DV.REC_XM + off, bytes([(rb & 0x80) | 23]))
    bip = e.r8(lab("lanex", "t_xltab") + 25 + 6)
    want_res = 23 ^ bip
    e.call(lab("lanex", "c_xlput"), 0, 6, 100, maxins=4_000_000)
    eng = e.r32(DP.ENG + 0x30 + 4 * 4)
    b = e.r32(DP.DP0 + 0x48) + DP.PAT_SZ * getp(eng, 0)
    wr(12, DV.MARK, b)
    setp(kst, 1, 50)
    store = e.r32(DP.DP0 + 8)
    setp(store, 0, getp(eng, 0)); setp(store, 1, 12); setp(store, 2, 0, 4)
    r_before = r0(lab("lanex", "c_xlget"), 0, 6)
    e.call(STEP, DP.DP0, maxins=40_000_000)
    r_after = r0(lab("lanex", "c_xlget"), 0, 6)
    check(knobs()[1] == rdec and r_after == want_res,
          f"a marked step played: decay back to the project's ({knobs()[1]} / {rdec}), the resonance (the lane's code) too ({r_before} -> {r_after} / {want_res})")
    e.call(lab("lanex", "c_xlset"), 0, 0, maxins=4_000_000)
    # state locks
    btn(16, True); btn(21, True); btn(21, False); btn(16, False)
    sb = r0(S("c_slsel"), 0)
    for i, v in ((5, 96), (8, 2), (9, 5), (10, 1), (11, 40)): e.call(S("c_slsetp"), 0, i, v, maxins=8_000_000)
    ks = r0(S("c_slkey"), 0, 4, sb)
    for i, v in ((5, 13), (8, 0), (9, 3), (10, 0), (11, 7)): e.call(S("c_slsetp"), 0, i, v, maxins=8_000_000)
    exact = lambda: [r0(int(rep["dautov"]["labels"]["c_dvget"], 16), 0, i) for i in range(SL.NV)]
    nib = lambda: [r0(S("c_slgetp"), 0, i) for i in range(SL.NV)]
    before = exact()
    stq = list(e.uc.mem_read(r0(S("c_slb"), ks, 0), 8))
    e.btn(10); X.frame(e)
    shift(True); press(4); during = nib(); release(4)
    want_n = [(stq[i >> 1] >> (4 * (i & 1))) & 15 for i in range(SL.NV)]
    shift(False); X.frame(e); after = exact()
    check(1 <= ks <= SL.NST and during == want_n and after == before, f"state locks: Shift + the state's step = its values ({during == want_n}); "
          f"Shift let go: the 14 values exactly as before ({after == before}: {after} / {before})")
    shift(True); press(4); act1 = e.r8(DV.RAM + DV.O_ACT); press(9); act2 = e.r8(DV.RAM + DV.O_ACT); release(9); release(4); shift(False); X.frame(e)
    drawn = [rd(st, sb) for st in range(4, 10)]
    check(act1 == 1 and act2 == 0 and drawn[0] == ks and drawn[1:5] == [SL.RAMP] * 4 and 1 <= drawn[5] <= SL.NST and exact() == before,
          f"hold the state's step (previewing: {act1}), tap step 10: the preview put back ({act2}), slock's ramp ({drawn})")
    del e; gc.collect()
    print(f"DAUTOV RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(a[1], json.loads(Path(a[2]).read_text())) else 0)
