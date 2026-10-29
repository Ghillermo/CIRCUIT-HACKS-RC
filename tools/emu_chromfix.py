"""SC49.7 test (chromfix): a chromatic pad recorded = a hit with its pitch; quantize moves the pitch with its hit.

    python tools/emu_chromfix.py BUILD.bin manifest.json
  * recording (the real sequencer tick and recorder, Drum 1's chromatic view, Record + Play): a hit already on step 9 (micro step 3, velocity 80);
    four pads pressed at steps 1, 5, 9, 13: each step gets the hit (the micro step of the engine's tick, 6 ticks a step here; the pad's velocity
    100 and probability 7 on an empty step; step 9 keeps its velocity and gets one more micro step) and the pad's pitch (the extra lane's code
    S + 1, or lane 0's 0x80 | S without lanex); the drum's edit store synced;
  * quantize (Shift + Play on Drum 1): a hit at micro step 4 of step 3 with its pitch, step 4 empty: hit and pitch (the extra lane's code and lane 0's
    0x80 | S) on step 4, none left on step 3; a hit at micro step 1 of step 6: stays with its pitch; a hit at micro step 5 of step 10 when step 11
    has a hit with its own pitch: step 11's pitch kept, step 10's left (the hit merged as before).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import dpitch as DP  # noqa: E402
import arp as A  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc35 import MGR  # noqa: E402

ENG, SEQ_TICK = 0x20038EC0, 0x0802C418


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = T8.E8(img, man, {k: int(v, 16) for k, v in R["patchain"]["labels"].items()})
    e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
    def skip(uc, a, s, dd): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (0x0801BE78, 0x08029A00): e.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=40_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    pget = lambda store, k: e.r8(r0(0x0803542C, store, k))
    dstore = lambda: e.r32(ENG + 0x30 + 4 * 4)
    for b_ in (4, 8, 8): e.call(0x08033320, MGR, b_, maxins=8_000_000); e.call(0x0803381A, MGR, b_, maxins=8_000_000); X.frame(e)
    base = e.r32(DP.DP0 + 0x48) + DP.PAT_SZ * pget(dstore(), 0)
    vel = bytearray(32); mic = bytearray(32); vel[9] = 80; mic[9] = 1 << 3
    e.uc.mem_write(base, bytes(vel)); e.uc.mem_write(base + 0x20, bytes([7] * 32)); e.uc.mem_write(base + 0x40, bytes([0xFF] * 32))
    e.uc.mem_write(base + 0x60, bytes(mic)); e.uc.mem_write(base + 0xA8, bytes([0xFF]) * 192)
    lanex = "lanex" in R
    def pitch_at(st):
        if lanex: return r0(lab("lanex", "c_xlrd"), base, st) - 1
        b0 = e.r8(base + 0xA8 + 6 * st); return b0 - 0x80 if 0x80 <= b0 < 0xFF else -1
    for b_ in (16, 17): e.call(0x08033320, MGR, b_, maxins=8_000_000); e.call(0x0803381A, MGR, b_, maxins=8_000_000)
    plan = {(1, 5): 10, (5, 2): 13, (9, 1): 20, (13, 4): 11}
    t, got = 500000, []
    for i in range(6 * 16):
        t += 21; e.w32(A.HAL_TICK, t); e.call(SEQ_TICK, ENG, maxins=5_000_000)
        s_, tk = pget(dstore(), 1), pget(dstore(), 2)
        if (s_, i % 6) in plan:
            e.call(PRESS, MGR, plan[(s_, i % 6)], 100, maxins=8_000_000)
            S = r0(lab("dpitch", "c_dpnow"), 0)
            e.call(RELEASE, MGR, plan[(s_, i % 6)], maxins=8_000_000)
            got.append((s_, tk, S))
    for b_ in (17,): e.call(0x08033320, MGR, b_, maxins=8_000_000); e.call(0x0803381A, MGR, b_, maxins=8_000_000)
    v2, p2, m2 = bytes(e.uc.mem_read(base, 32)), bytes(e.uc.mem_read(base + 0x20, 32)), bytes(e.uc.mem_read(base + 0x60, 32))
    for s_, tk, S in got:
        mb = 1 << min(5, tk)
        want_v = 80 if s_ == 9 else 100
        want_m = (mb | (1 << 3)) if s_ == 9 else mb
        check(v2[s_] == want_v and p2[s_] & 7 == 7 and m2[s_] & 0x3F == want_m and pitch_at(s_) == S,
              f"a pad at step {s_}, tick {tk}: the hit there (velocity {v2[s_]} / {want_v}, micro steps {m2[s_] & 0x3F:#04x} / {want_m:#04x}), its pitch "
              f"{pitch_at(s_)} / {S}")
    others = [st for st in range(32) if v2[st] and st not in [g[0] for g in got]]
    check(len(got) == 4 and not others, f"four presses ({[g[:2] for g in got]}), no other step gets a hit ({others})")
    from drumstore import PROB_VIEW0
    store = e.r32(e.r32(PROB_VIEW0 + 0xC))
    words = [(e.call(0x0803542C, store, k), e.r32(e.uc.reg_read(UC_ARM_REG_R0)))[1] for k in (0, 2, 4)]
    follows = e.r32(store + 0x18) == base + 0xA8
    check(not follows or words == [struct.unpack_from("<I", v2, 0)[0], struct.unpack_from("<I", v2, 8)[0], struct.unpack_from("<I", v2, 16)[0]],
          f"the drum's edit store synced when it holds this pattern (it does: {follows}; velocities {[hex(w) for w in words]})")
    del e; gc.collect()
    fails += quant_tests(img, man, check)
    print(f"CHROMFIX RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


def quant_tests(img, man, check):
    import emu_arp as EAm
    import struct
    from emu_sc08 import CONT
    R = man["report"]
    lab = lambda m, k: int(R[m]["labels"][k], 16)
    e = EAm.EA(img, man)
    r0 = lambda fn, *a: (e.call(fn, *a), e.uc.reg_read(UC_ARM_REG_R0))[1]
    e.set_p0(e.r32(CONT + 0x188), 4); e.press(4); e.release(4); e.press(9); e.release(9)
    pd = e.playing(4); base = e.settings(4, pd) - 0x80
    vel = [0] * 32; mic = [0] * 32
    for st, m in ((3, 4), (6, 1), (10, 5), (11, 0)): vel[st] = 100; mic[st] = 1 << m
    e.uc.mem_write(base, bytes(vel) + bytes([7] * 32) + bytes([0xFF] * 32) + bytes(mic))
    e.uc.mem_write(base + 0xA8, bytes([0xFF]) * 192)
    e.setpat(4, pd, 0, 15)
    lanex = "lanex" in R
    if lanex:
        for st, c in ((3, 5), (6, 9), (10, 12), (11, 20)): e.call(lab("lanex", "c_xlwr"), 0, st, c, base)
    for st, sv in ((3, 7), (10, 12), (11, 20)): e.uc.mem_write(base + 0xA8 + 6 * st, bytes([0x80 | sv] * 6))
    e.set_p0(e.r32(MGR + 0xC), 1); e.press(17); e.release(17); e.set_p0(e.r32(MGR + 0xC), 0)
    rd = (lambda st: r0(lab("lanex", "c_xlrd"), base, st)) if lanex else (lambda st: None)
    v, m = list(e.uc.mem_read(base, 16)), list(e.uc.mem_read(base + 0x60, 16))
    l0 = lambda st: bytes(e.uc.mem_read(base + 0xA8 + 6 * st, 6)).hex()
    check(v[3] == 0 and v[4] == 100 and m[4] & 0x3F == 1 and (not lanex or (rd(4) == 5 and rd(3) == 0)),
          f"quantize: the hit at micro step 4 of step 3 on step 4 with its pitch (velocity {v[3]} / {v[4]}, codes {rd(3)} / {rd(4)})")
    check(l0(4) == "87" * 6 and l0(3) == "ff" * 6, f"lane 0's 0x80 | S with it ({l0(3)} / {l0(4)})")
    check(v[6] == 100 and m[6] & 0x3F == 1 and (not lanex or rd(6) == 9), f"micro step 1 of step 6: stays, its pitch too ({v[6]}, code {rd(6)})")
    check((not lanex or (rd(11) == 20 and rd(10) == 12)) and l0(11) == "94" * 6 and l0(10) == "8c" * 6 and m[11] & 0x3F == 1,
          f"step 11 with its own hit and pitch: its pitch kept, step 10's left (codes {rd(10)} / {rd(11)}, lane 0 {l0(10)} / {l0(11)})")
    from drumstore import PROB_VIEW0
    store = e.r32(e.r32(PROB_VIEW0 + 0xC))
    w = (e.call(0x0803542C, store, 16), e.r32(e.uc.reg_read(UC_ARM_REG_R0)))[1]
    mm = bytes(e.uc.mem_read(base + 0x60, 4))
    check(w == struct.unpack("<I", mm)[0], f"the drum's edit store synced ({w:#x} / {mm.hex()})")
    fails = 0
    del e; gc.collect()
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
