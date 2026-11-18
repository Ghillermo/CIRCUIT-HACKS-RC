"""Alpha 7.02: pattern data that follows the pattern that plays (chains, pattern mutate), against the previous build (Alpha 7.01):
  * drums (drumpat.use_patpass): Drum 1 plays patterns A, B, A, B, ... (as a chain or a mutate list makes it), each with a hit on its first step at
    «1 in 2»: each pattern's own passes count, so A sounds on its 2nd and 4th visit and B the same (the previous build: the count went back to 0 at
    every change: never); the transport stopped (the LED task) = every count 0: the first visit silent again;
  * lanex (use_patmask): the extra lane's base with the engine's pattern at 9 = pattern 1 (the previous build: 9 patterns on, the next drum's);
  * xlanes (use_late): MIDI 1's pattern changes to one whose block is not cached: micro step 0 plays nothing; after the LED task's fill the next
    micro step plays the first half (the previous build: nothing until micro step 3), then nothing more; a fill ending after micro step 3 plays
    the second half on micro step 4.

    python tools/emu_patfollow.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import drumarp as D  # noqa: E402
import drumpat as Q  # noqa: E402
import drumstore as DS  # noqa: E402


def drums(img, man):
    e = T.EL(img); e.at(300000); e.transport(0)
    dp = D.DP0; ifc = e.r32(dp + 0x4C)
    hits, cur = [], [None]
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def on(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == ifc: hits.append((cur[0], uc.reg_read(UC_ARM_REG_R2)))
        skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, on, begin=e.r32(e.r32(ifc)) & ~1, end=e.r32(e.r32(ifc)) & ~1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: skip(uc), begin=e.r32(e.r32(ifc) + 4) & ~1, end=e.r32(e.r32(ifc) + 4) & ~1)
    b0 = e.r32(dp + 0x48)
    for p, vel in ((0, 100), (1, 50)):                                                   # A = pattern 0 (velocity 100), B = pattern 1 (50)
        arr = bytearray(bytes(32) + bytes([7]) * 32 + bytes([0xFF]) * 32 + bytes(32)); arr[0] = vel; arr[0x60] = 1
        base = b0 + 0x6A8 * p
        e.uc.mem_write(base, bytes(arr)); e.uc.mem_write(base + 0x80, bytes([3, 0]))     # 4 steps
        e.uc.mem_write(base + Q.DQ_OFF, bytes([1 << 3]) + bytes(31))                     # step 1: «1 in 2»
    st = e.r32(e.r32(DS.PROB_VIEW0 + 0xC))
    arr = e.uc.mem_read(b0, 0x80)
    for k0, off in DS.ARRAYS:                                                            # the edit store = pattern 0
        for w in range(8):
            for fn in (DS.PARAM_GET, DS.PARAM_WPTR): e.call(fn, st, k0 + w); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes(arr[off + 4 * w:off + 4 * w + 4]))
    e.uc.mem_write(e.r32(T.LZ.SESSION_OBJ + 0x14) + 0x27024 + Q.O_FLAG, b"DQ")
    slot2 = e.r32(D.DP_VT + 8) & ~1
    def visits(seq):
        hits.clear()
        for i, p in enumerate(seq):
            for stp in range(4):
                for m in range(6):
                    cur[0] = (i, p); e.call(slot2, dp, p, stp, m, maxins=3_000_000)
        return [(c[0], c[1], v) for c, v in hits]
    X.frame(e); e.transport(1)                                                          # stopped first (as at power-up): every count 0
    out = {"run": visits([0, 1, 0, 1, 0, 1, 0, 1])}
    e.transport(0); X.frame(e); e.transport(1)
    out["after_stop"] = visits([0, 0])
    return out


def lanex_mask(img, man):
    import lanex as LX
    e = T.EL(img); e.at(300000)
    st = e.r32(LX.ENG + 0x30 + 4 * 4)
    for fn in (0x080354FA, 0x0803542C):
        e.call(fn, st, 0); e.uc.mem_write(e.uc.reg_read(UC_ARM_REG_R0), bytes([9]))
    e.call(int(man["report"]["lanex"]["labels"]["c_xlbase"], 16), 0, maxins=1_000_000)
    return e.uc.reg_read(UC_ARM_REG_R0) - e.r32(D.DP0 + 0x48)


def xlanes_late(img, man):
    from emu_sc35 import E35
    import emu_arp as EAm
    import vcf21 as V
    import xlanes as XL
    e = E35(img, man); R = man["report"]
    e.cur = e.scur = 1
    xl = {k: int(v, 16) for k, v in R["xlanes"]["labels"].items()}
    pv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    for k in ("load", "new", "play"):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=pv[k], end=pv[k])
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))          # the own engine on
    applied = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: applied.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))),
                  begin=xl["c_xlap"], end=xl["c_xlap"])
    e.call(xl["c_xlst"], maxins=10000)
    e.uc.mem_write(XL.XLR + XL.O_MAP, struct.pack("<H", 1 << 2))                          # block 2 (MIDI 1, pattern 2) holds data
    blk = bytearray([0xFF] * XL.BLK); blk[0] = 19; blk[1:XL.NSLOT] = bytes(XL.NSLOT - 1)
    blk[XL.VOFF + 10] = 40; blk[XL.VOFF + 11] = 90                                        # code 19, step 6 (5): 40 then 90
    for i in range(XL.BLKW):
        e.ext[XL.XB + 2 * XL.BLKW + i] = (blk[2 * i] | blk[2 * i + 1] << 8) << 8
    P1 = XL.PLAYER0 + 2 * XL.PLAYER_SZ
    EAm.EA.setp(e, XL.REC_ON, 0, bytes([1]))
    pl = lambda pat, step, micro: (applied.clear(), e.call(xl["c_xlpl"], P1, pat, step, micro, maxins=2_000_000), list(applied))[2]
    work = lambda: e.call(xl["c_xlwork"], maxins=200_000_000)
    pl(4, 0, 0); work()                                                                  # pattern 4 cached (no data)
    out = {"m0": pl(2, 5, 0)}                                                            # the change: block 2 not cached yet
    work()                                                                               # the fill
    out["m1"] = pl(2, 5, 1); out["m2"] = pl(2, 5, 2); out["m3"] = pl(2, 5, 3)
    pl(4, 0, 0); work()                                                                  # back to pattern 4
    out["m3b"] = pl(2, 5, 3); work(); out["m4"] = pl(2, 5, 4); out["m5"] = pl(2, 5, 5)
    return out


def main(a):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    new_i, new_m = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    old_i, old_m = Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())
    n = drums(new_i, new_m); gc.collect(); o = drums(old_i, old_m); gc.collect()
    want = [(2, 0, 100), (3, 1, 50), (6, 0, 100), (7, 1, 50)]
    check(n["run"] == want, f"drums, A B A B A B A B at «1 in 2»: A on its visits 2 and 4, B the same ({n['run']})")
    check(o["run"] != want, f"(the previous build: {o['run']})")
    check(n["after_stop"] == [(1, 0, 100)], f"the transport stopped: every pattern's count back to 0, A silent on its first visit again ({n['after_stop']})")
    nb = lanex_mask(new_i, new_m); gc.collect(); ob = lanex_mask(old_i, old_m); gc.collect()
    check(nb == 0x6A8, f"lanex: the engine's pattern 9 = pattern 1's base (+{nb:#x}; the previous build +{ob:#x})")
    import vcf21 as V
    nx = xlanes_late(new_i, new_m); gc.collect(); ox = xlanes_late(old_i, old_m); gc.collect()
    vt = lambda v: v                                                                        # (c_xlap gets the stored lane value)
    check(nx["m0"] == [] and nx["m1"] == [(19, 40)] and nx["m2"] == [] and nx["m3"] == [(19, 90)],
          f"xlanes: the change on micro 0 (block not cached) nothing; after the fill micro 1 = the first half, micro 2 nothing, micro 3 the second "
          f"({nx['m0']}, {nx['m1']}, {nx['m2']}, {nx['m3']})")
    check(ox["m1"] == [] and ox["m3"] == [(19, 90)], f"(the previous build: micro 1 {ox['m1']}, micro 3 {ox['m3']})")
    check(nx["m3b"] == [] and nx["m4"] == [(19, 90)] and nx["m5"] == [],
          f"xlanes: a fill ending after micro 3: micro 4 = the second half, then nothing ({nx['m3b']}, {nx['m4']}, {nx['m5']}; previous {ox['m4']})")
    print("A7.02 PATTERN-FOLLOW RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
