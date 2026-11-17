"""Beta 5.63 test (bug hunt 2026-11-14, JR-1 / JR-2: vcf21.use_freeslot + recinst.use_code0): a slot of page 4 freed with Duplicate + knob
(p4dest.use_dup writes code 0 into the row) while its lane still holds automation, through the controller:
  * MIDI 1's own engine on, the assigned-knob view (pad 1): automation in lane 2 (all 32 steps), then Duplicate + K2 frees slot 2 (code 0);
  * playback through the stock macro sender (0x080313C4 = c_vplay's head, the transport running), lane 2 at 40 / 0 / 127: the tail's flags byte
    (c_vvaddr(0, 0)) and c_von(0) unchanged, no CC sent (before the fix: the flags byte = the lane value, MIDI 1's engine off, CC 0 sent);
    a lane that is not freed (lane 1, TUNE) still sets its value (the control);
  * MIDI 2 (c_vapply(1, lane, v) with code 0 in its row): its byte c_vvaddr(1, 0) (TAIL + 26) unchanged, no CC;
  * Record held + step 4 of MIDI 1's track view (the snapshot) with two codes off their defaults and slot 2 free: c_ridiff(0, code 0) = 0, the
    freed lane is not kept: nothing written into it (since SC57.3 a changed code without a lane goes to the extra lanes, xlanes' c_xlsn, and the
    row stays; without xlanes the SC44.9 policy: the first lanes whose code does not differ, the freed one too), the flags byte unchanged, and
    playing step 4's lanes back leaves MIDI 1's engine on (before the fix: lane 2 kept as «differing», 0 written into it, played into the flags
    byte);
  * no stock memset with an unaligned destination (Unicorn does not trap an unaligned stm).

    python tools/emu_p4free.py BUILD.bin manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import recinst as RI  # noqa: E402

V = T4.V
MGR, DUPB = X.MGR, 24
SENDER = 0x080313C4                                  # the stock macro sender (c_vplay's head): (this, knob, value)
MEMSET = 0x0801A9BC


def setup(img, man):
    e = X.EP(img, man)
    bad = []
    def ms(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) & 3: bad.append(hex(uc.reg_read(UC_ARM_REG_R0)))
    e.uc.hook_add(UC_HOOK_CODE, ms, begin=MEMSET, end=MEMSET)
    ccs = []
    def cc(uc, a, s, d): ccs.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)))
    e.uc.hook_add(UC_HOOK_CODE, cc, begin=V.CC_HELPER, end=V.CC_HELPER)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    return e, bad, ccs


def free_slot2(e):
    dup = lambda v: e.call(0x08033320 if v else 0x0803381A, MGR, DUPB, maxins=8_000_000)
    e.btn(2); e.btn(8); e.pad(0)                                                   # MIDI 1's Preset, the assigned-knob view
    dup(True); e.knob(1, 1); dup(False)


def play_part(img, man, check):
    e, bad, ccs = setup(img, man)
    vl = e.vl
    row = lambda t=0: tuple(e.uc.mem_read(e.r0(vl["c_vrow"], t), 8))
    pat = e.r0(vl["c_sdpat"], 0)
    e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * 1, bytes([40]) * RI.LANE_BYTES)     # lane 2's recorded automation
    free_slot2(e)
    r = row()
    check(r[1] == 0 and r[0] == V.LANE_TAB[0], f"Duplicate + K2 on the assigned-knob view: slot 2 freed ({r})")
    check(bytes(e.uc.mem_read(pat + RI.LANES + RI.LANE_BYTES, 6)) == bytes([40]) * 6, "lane 2 still holds its automation")
    fa = e.r0(vl["c_vvaddr"], 0, 0); f0 = e.r8(fa); on0 = e.r0(vl["c_von"], 0)
    e.transport(1)
    G = e.r32(V.SETOBJ - 8)
    res = []
    for v in (40, 0, 127):
        ccs.clear()
        e.call(SENDER, G + 0x110, 1, v, maxins=4_000_000)
        res.append((v, e.r8(fa), e.r0(vl["c_von"], 0), list(ccs)))
    ok = all(f == f0 and on == on0 for _, f, on, _ in res)
    check(ok, f"lane 2 played at 40 / 0 / 127: the flags byte {fa:#x} stays {f0:#x}, c_von(0) stays {on0} ({[(v, hex(f), on) for v, f, on, _ in res]})")
    check(all(not c for *_, c in res), f"... and no CC sent ({[c for *_, c in res]})")
    # the control: lane 1 (TUNE) still plays
    t0 = e.val(0, V.LANE_TAB[0]); ccs.clear()
    e.call(SENDER, G + 0x110, 0, 100, maxins=4_000_000)
    t1 = e.val(0, V.LANE_TAB[0])
    check(t1 != t0 and e.r8(fa) == f0, f"lane 1 (code {V.LANE_TAB[0]}) still plays ({t0} -> {t1}; CCs {len(ccs)})")
    # MIDI 2: code 0 in its row, c_vapply directly (the sender path for track 1 is the same function)
    r2a = e.r0(vl["c_vrow"], 1)
    e.uc.mem_write(r2a + 1, b"\x00")
    a2 = e.r0(vl["c_vvaddr"], 1, 0); b2 = e.r8(a2); ccs.clear()
    for v in (40, 127): e.call(vl["c_vapply"], 1, 1, v, maxins=4_000_000)
    check(e.r8(a2) == b2 and not ccs, f"MIDI 2, a freed slot played: its byte {a2:#x} stays {b2:#x} ({e.r8(a2):#x}), no CC ({ccs})")
    e.transport(0)
    check(not bad, f"no memset with an unaligned destination ({bad})")
    del e; gc.collect()


def snap_part(img, man, check):
    from emu_sc17_6 import PRESS, RELEASE
    e, bad, ccs = setup(img, man)
    R = man["report"]; vl = e.vl
    tdef = int(R["vcf20"]["labels"]["t_def"], 16)
    dflt = lambda c: struct.unpack("b", bytes([e.r8(tdef + c)]))[0]
    setv = lambda c, v: e.uc.mem_write(e.r0(vl["c_vvaddr"], 0, c), bytes([v & 0xFF]))
    row = lambda: tuple(e.uc.mem_read(e.r0(vl["c_vrow"], 0), 8))
    pat = e.r0(vl["c_sdpat"], 0)
    lane = lambda k, st: bytes(e.uc.mem_read(pat + RI.LANES + RI.LANE_BYTES * k + 6 * st, 6))
    ml = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    nd = int(R["recinst"]["prev"]["nd"], 16)
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd))
    for c in dcode: setv(c, dflt(c))                                                # everything at its default
    tou = lambda c, v: e.r0(vl["c_vtou"], c, v & 0xFFFFFFFF)
    free_slot2(e)
    check(row()[1] == 0, f"slot 2 freed ({row()})")
    rl = {k: int(v, 16) for k, v in R["recinst"]["labels"].items()}
    d0 = e.r0(rl["c_ridiff"], 0, 0)
    check(d0 == 0, f"c_ridiff(0, code 0) = {d0} (a freed slot never differs)")
    row2 = tuple(e.uc.mem_read(e.r0(vl["c_vrow2"], 0), 8)) if "c_vrow2" in vl else ()
    fresh = [c for c in dcode if c and c not in V.LANE_TAB and c not in row2 and e.r0(vl["c_vlane"], 0, c) == 0xFF][:2]   # codes on no dedicated view
    near = lambda c, d: dflt(c) + d if dflt(c) + d <= 63 else dflt(c) - d
    vals = {fresh[0]: near(fresh[0], 7), fresh[1]: near(fresh[1], 11)}
    for c, v in vals.items(): setv(c, v)
    for k in range(8): e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * k, bytes(range(1, 101)) + bytes(92))     # lanes with old values
    fa = e.r0(vl["c_vvaddr"], 0, 0); f0 = e.r8(fa); old1 = lane(1, 3)
    sn = []
    if "xlanes" in R and "c_xlsn" in R["xlanes"]["labels"]:
        a_sn = int(R["xlanes"]["labels"]["c_xlsn"], 16)
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: sn.append(uc.reg_read(UC_ARM_REG_R1)), begin=a_sn, end=a_sn)
    e.btn(2)                                                                        # MIDI 1's track view
    e.call(0x08033320, MGR, RI.REC_ID, maxins=8_000_000)
    e.call(PRESS, MGR, 3, 100, maxins=8_000_000); e.call(RELEASE, MGR, 3, maxins=8_000_000)
    e.call(0x0803381A, MGR, RI.REC_ID, maxins=8_000_000)
    r = row()
    xl = "xlanes" in R and "c_xlsn" in R["xlanes"]["labels"]
    if xl:          # (SC57.3+) a differing code without a lane goes to the extra lanes (xlanes' c_xlsn in recinst's in_f): the 8 lanes keep their codes
        want = (V.LANE_TAB[0], 0) + tuple(V.LANE_TAB[2:])
        check(r == want and sorted(sn) == sorted(vals), f"Record + step 4: the row unchanged, slot 2 still free ({r}); the two changed codes to the extra lanes ({sn})")
    else:           # the SC44.9 policy: the first lanes whose code does not differ (the freed one is one of them now)
        want = (fresh[0], fresh[1]) + tuple(V.LANE_TAB[2:])
        check(r == want, f"Record + step 4: the two changed codes take lanes 1 / 2 (the freed one too): {r} (want {want})")
        got = {c: lane(r.index(c), 3).hex() for c in vals if c in r}
        check(all(c in r and lane(r.index(c), 3) == bytes([tou(c, v)]) * 6 for c, v in vals.items()), f"each value on its lane's step 4 ({got})")
    check(r[1] != 0 or lane(1, 3) == old1, f"the freed lane not written (step 4 {lane(1, 3).hex()}, was {old1.hex()})")
    check(e.r8(fa) == f0, f"the flags byte unchanged by the snapshot ({f0:#x} -> {e.r8(fa):#x})")
    for k in range(8): e.call(vl["c_vapply"], 0, k, lane(k, 3)[0], maxins=4_000_000) if lane(k, 3)[0] != 0xFF and lane(k, 3)[0] < 128 else None
    on = e.r0(vl["c_von"], 0)
    check(on == 1 and e.r8(fa) == f0, f"step 4's lanes played back: c_von(0) = {on}, the flags byte {e.r8(fa):#x} (was {f0:#x})")
    check(not bad, f"no memset with an unaligned destination ({bad})")
    del e; gc.collect()


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    play_part(img, man, check)
    snap_part(img, man, check)
    print(f"{man.get('marker', 'build')} P4FREE RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
