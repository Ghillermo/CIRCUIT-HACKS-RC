"""SC43 ARM tests: the drum hits our modules record survive the stock's next commit (drumstore.py), through the controller and the real views:
  * Drum 1's arpeggio recorded (1/8, playing with Record) on steps 1 and 3, then a probability edit of step 6 in the stock's probability view:
    the recorded hits are still in the pattern (SC42.9: gone), and the edit is there;
  * a roller recorded on step 10 (micro step 1), then the same edit: still there;
  * the drums' probability view (drumpat.py): Pattern Settings pad 25 = mode 2 (row 3 the dynamics, pads 25-28 the mutate; the project marked,
    the other drum patterns' bytes cleared), Pattern Settings twice = mode 1 (row 4 the frequency, row 3 the stock's again); played micro step by
    micro step: the frequency (passes 4 and 8 of 8), the dynamics (velocities within ±32; later micro steps, never earlier), the mutate (± 8 / ± 1
    from the step's flip, at about its chance), a project not marked = as the stock.

    python tools/emu_sc43.py SC43.bin SC43_manifest.json [SC42.9.bin SC42.9_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import drumarp as D  # noqa: E402
import drumstore as DS  # noqa: E402
import rollers as R  # noqa: E402
import drumnote as DN  # noqa: E402
DN.MIRROR = True

MGR = T.MGR


def run(img, man):
    lab = {k: int(v, 16) for k, v in man["report"]["drumarp"]["labels"].items()}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    dp = D.DP0; ifc = e.r32(dp + 0x4C)
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (e.r32(e.r32(ifc)) & ~1, e.r32(e.r32(ifc) + 4) & ~1): e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=f, end=f)
    def setp(k, v):
        for fn in (0x080354FA, 0x0803542C):
            e.call(fn, D.TRANSPORT, k); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([v]))
    pat = r0(lab["c_dapat"], 0)
    base = e.r32(dp + 0x48) + 0x6A8 * pat
    st = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    empty = bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32)                # an empty pattern, raw and in the store
    e.uc.mem_write(base, empty)
    for k0, off in DS.ARRAYS:
        for w in range(8):
            word = empty[off + 4 * w:off + 4 * w + 4]
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, st, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), word)
    slot2 = e.r32(D.DP_VT + 8) & ~1
    def play(steps):
        for stp in steps:
            for m in range(6): e.call(slot2, dp, pat, stp, m, maxins=3_000_000)
    pv = lambda s: (e.r8(base + s), e.r8(base + 0x40 + s), e.r8(base + 0x60 + s))
    # the arpeggio recorded
    e.btn(4); e.btn(8); X.frame(e)
    e.call(lab["c_daset"], 0, pat, 0x80 | 6 << 3)
    e.call(T.PRESS, MGR, 0, 90, maxins=8_000_000); e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000)
    setp(0, 1); setp(1, 1); setp(2, 0)
    play(range(4))
    e.call(T.RELEASE, MGR, 3, maxins=8_000_000); e.call(T.RELEASE, MGR, 0, maxins=8_000_000)
    rec = (pv(0), pv(2))
    # a roller recorded on step 10, micro step 1
    e.btn(4)
    for _ in range(3):
        if e.r8(MGR + 0x152) == 42: break
        e.btn(9)
    X.frame(e)
    rp = [q for q in range(24) if R.tables()[0][q] == 0 and R.tables()[1][q] == 0][0]
    e.call(T.PRESS, MGR, rp, 100, maxins=8_000_000); play([9]); e.call(T.RELEASE, MGR, rp, maxins=8_000_000)
    rol = pv(9)
    setp(0, 0); setp(1, 0)
    # the stock's probability view: step 6, probability pad 20
    e.btn(4); e.btn(12); e.btn(12); X.frame(e)
    e.pad(5); X.frame(e); e.pad(16 + 3); X.frame(e)
    out = (rec, rol, pv(0), pv(2), pv(9), e.r8(base + 0x20 + 5), e.r8(MGR + 0x152))
    del e; gc.collect()
    return out


def dq_part(img, man, check):
    import drumpat as Q
    lab = {k: int(v, 16) for k, v in man["report"]["drumpat"]["labels"].items()}
    e = T.EL(img); e.at(300000); e.transport(0)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=4_000_000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    dp = D.DP0; ifc = e.r32(dp + 0x4C); setter = e.r32(dp + 0x50)
    hits, sets, cur = [], [], [0]
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    from unicorn.arm_const import UC_ARM_REG_R2
    def on(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == ifc: hits.append((cur[0], uc.reg_read(UC_ARM_REG_R2)))
        skip(uc)
    def st_(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == setter: sets.append((cur[0], uc.reg_read(UC_ARM_REG_R2)))
    e.uc.hook_add(UC_HOOK_CODE, on, begin=e.r32(e.r32(ifc)) & ~1, end=e.r32(e.r32(ifc)) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: skip(uc), begin=e.r32(e.r32(ifc) + 4) & ~1, end=e.r32(e.r32(ifc) + 4) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, st_, begin=e.r32(e.r32(setter)) & ~1, end=e.r32(e.r32(setter)) & ~1)
    pat = r0(int(man["report"]["drumarp"]["labels"]["c_dapat"], 16), 0)
    base = e.r32(dp + 0x48) + 0x6A8 * pat
    other = e.r32(dp + 0x90 + 0x48) + 0x6A8 * 3                                        # Drum 2, pattern 4: garbage there
    e.uc.mem_write(other + Q.DQ_OFF, bytes([0x5A]) * 32)
    st = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    arr = bytearray(bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32))
    arr[0] = 100; arr[0x40] = 10; arr[0x60] = 1                                         # step 1: a hit, sample flip 10, on its first micro step
    e.uc.mem_write(base, bytes(arr)); e.uc.mem_write(base + 0x80, bytes([3, 0]))         # a 4-step pattern
    for k0, off in DS.ARRAYS:
        for w in range(8):
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, st, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(arr[off + 4 * w:off + 4 * w + 4]))
    byte = lambda: e.r8(base + Q.DQ_OFF)
    prob = lambda: e.r32(e.r32(DS.PROB_VIEW0 + 4))
    leds = lambda: [e.r16(prob() + 2 * i) for i in range(16)] if hasattr(e, "r16") else list(struct.unpack("<16H", bytes(e.uc.mem_read(prob(), 32))))
    # mode 2 from Pattern Settings pad 25
    e.btn(4); e.btn(12); X.frame(e); e.pad(24); X.frame(e)
    sub = e.r8(MGR + 0x152)
    e.pad(16 + 2); e.pad(16 + 8 + 2); e.pad(16 + 12); X.frame(e); L2 = leds()
    flag = bytes(e.uc.mem_read(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, 2))
    check(sub == 41 and byte() == (2 | 2 << 6) and flag == b"DQ" and bytes(e.uc.mem_read(other + Q.DQ_OFF, 32)) == bytes(32),
          f"Pattern Settings pad 25 = the probability view in mode 2: dynamics 2, mutate 2 (byte {byte():#x}), the project marked, the garbage cleared")
    check(L2[2] == Q.COL_DYN and L2[0] == Q.COL_DIM and L2[8:11] == [Q.COL_MUT] * 3 and L2[11] == Q.COL_DIM and L2[12:16] == [0] * 4,
          f"its LEDs: dynamics 3 green, mutate bar of 3, pads 29-32 dark ({[hex(x) for x in L2]})")
    # mode 1: Pattern Settings twice
    e.btn(4); X.frame(e); X.frame(e); X.frame(e); X.frame(e); e.btn(12); e.btn(12); X.frame(e)
    e.pad(16 + 8 + 3); X.frame(e); L1 = leds()
    check(e.r8(MGR + 0x152) == 41 and (byte() >> 3) & 7 == 3 and L1[8:12] == [Q.COL_FREQ] * 4 and L1[12] == Q.COL_DIM and L1[2] != Q.COL_DYN,
          f"Pattern Settings twice = mode 1: pad 28 = every 4 passes ({byte():#x}), row 4 a bar of 4, row 3 the stock's ({[hex(x) for x in L1]})")
    # playing
    e.transport(1)
    slot2 = e.r32(D.DP_VT + 8) & ~1
    def play(passes):
        hits.clear(); sets.clear()
        for ps in range(passes):
            for stp in range(4):
                for m in range(6):
                    cur[0] = (ps, stp, m); e.call(slot2, dp, pat, stp, m, maxins=3_000_000)
        return list(hits), list(sets)
    e.uc.mem_write(base + Q.DQ_OFF, bytes([3 << 3]))                                     # every 4 passes, nothing else
    h_, _ = play(8)
    check([c[0] for c, _ in h_] == [3, 7] and all(c[1:] == (0, 0) for c, _ in h_), f"every 4 passes: passes 4 and 8 ({[c for c, _ in h_]})")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([6]))                                           # balanced velocity -32..+32
    h_, _ = play(40); vs = [v for _, v in h_]
    check(len(vs) == 40 and min(vs) >= 68 and max(vs) <= 127 and len(set(vs)) > 10, f"dynamics 7: velocities 68..127 ({min(vs)}..{max(vs)}, {len(set(vs))} kinds)")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([5]))                                           # dragging: -1..+3 micro steps
    h_, _ = play(40); ms_ = [c[2] for c, _ in h_]
    check(len(ms_) == 40 and min(ms_) == 0 and max(ms_) > 0 and max(ms_) <= 3, f"dynamics 6 (-1..+3): the hit on micro step 1 moves to 1..4, never earlier ({sorted(set(ms_))})")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([2 << 6]))                                      # mutate 2 (pad 27): ± 8, 25 %
    h_, s_ = play(64); smp = [v for c, v in s_]
    jumps = sum(1 for v in smp if v in (2, 18)); same = sum(1 for v in smp if v == 10)
    check(len(h_) == 64 and set(smp) <= {2, 10, 18} and 6 <= jumps <= 30, f"mutate 2: ± 8 from the flip 10, 25 % ({jumps} of 64 moved, {same} the flip)")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([1 << 6]))                                      # mutate 1 (pad 26): ± 1, 25 %
    h_, s_ = play(64); smp = [v for c, v in s_]
    moved = sum(1 for v in smp if v in (9, 11))
    check(set(smp) <= {9, 10, 11} and 6 <= moved <= 30, f"mutate 1: ± 1 inside the row, 25 % ({moved} of 64 moved)")
    e.uc.mem_write(base + Q.DQ_OFF, bytes([3 << 6]))                                      # mutate 3 (pad 28): both at 12 %
    h_, s_ = play(96); smp = [v for c, v in s_]
    row = sum(1 for v in smp if v // 8 != 1); col = sum(1 for v in smp if v % 8 != 2)
    check(set(smp) <= {1, 2, 3, 9, 10, 11, 17, 18, 19} and 2 <= row <= 26 and 2 <= col <= 26, f"mutate 3: ± 1 and ± 8 at 12 % each ({row} rows, {col} inside of 96)")
    e.uc.mem_write(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, bytes(2)); e.uc.mem_write(base + Q.DQ_OFF, bytes([3 << 3 | 6]))
    h_, _ = play(4)
    check(len(h_) == 4 and all(v == 100 for _, v in h_), f"a project not marked: the stock's hits ({h_})")
    # Nudge (Pattern Settings pad 26): the arrays and our bytes rotated, kept after the stock's next commit
    e.transport(0)
    e.uc.mem_write(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, b"DQ")
    arr = bytearray(bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32)); arr[2] = 77; arr[0x60 + 2] = 4; arr[0x40 + 2] = 12
    e.uc.mem_write(base, bytes(arr)); e.uc.mem_write(base + 0x80, bytes([7, 2])); e.uc.mem_write(base + Q.DQ_OFF, bytes(32)); e.uc.mem_write(base + Q.DQ_OFF + 2, bytes([0x85]))
    for k0, off in DS.ARRAYS:
        for w in range(8):
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, st, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(arr[off + 4 * w:off + 4 * w + 4]))
    e.btn(4); e.btn(12); X.frame(e); e.pad(25); X.frame(e)
    nud = (e.r8(base), e.r8(base + 0x60), e.r8(base + 0x40), e.r8(base + Q.DQ_OFF), e.r8(base + 0x81))
    e.btn(12); X.frame(e); e.pad(9); X.frame(e); e.pad(16 + 2); X.frame(e)                 # a probability edit of step 10
    kept = (e.r8(base), e.r8(base + 0x60), e.r8(base + 0x40), e.r8(base + Q.DQ_OFF))
    check(nud == (77, 4, 12, 0x85, 0) and kept == nud[:4], f"Nudge from step 3: step 3's hit, flip and our byte on step 1 ({nud}), still after a probability edit ({kept})")
    del e; gc.collect()


def main(img, man, prev=None, prev_man=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rec, rol, a0, a2, r9, prob5, sub = run(img, man)
    check({rec[0][:2], rec[1][:2]} == {(90, 0), (100, 3)} and rol == (100, 0xFF, 1), f"recorded: the arpeggio on steps 1 / 3 {rec}, the roller on step 10 {rol}")
    check(sub == 41 and (a0, a2, r9) == (rec[0], rec[1], rol) and prob5 != 7, f"after a probability edit of step 6 (probability {prob5}): still there ({a0}, {a2}, {r9})")
    if "drumpat" in man["report"]: dq_part(img, man, check)
    if prev:
        p = run(prev, prev_man)
        check(p[2][0] == 0 and p[3][0] == 0 and p[4][0] == 0, f"SC42.9: the same edit took them away ({p[2]}, {p[3]}, {p[4]})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    pv = (Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) if len(a) > 4 else (None, None)
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), *pv) else 0)
