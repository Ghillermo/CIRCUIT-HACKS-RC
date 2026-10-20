"""SC44.9 ARM tests (vcf21.use_p4dest + tools/p4dest.py: the destinations of knob page 4 of the own engine of MIDI 1 / 2), through the controller and the
real LED task:
  * the rows start at LANE_TAB (both tracks);
  * page 4 (pad 4), Shift + K1: a slow knob (DIV clicks a destination) through the matrix's list; clamped at the end;
  * Shift: the knob LEDs = the destinations' page colours, full brightness;
  * K1 alone then moves the new destination's value (the old one stays) and records it in lane 0 (the automation gate, id 20); a lane played
    (c_vapply lane 0) sets the new destination; the old code records nowhere; Clear + K1 to the left clears lane 0 (c_vlane);
  * Clear held, then Shift + K1 = back to the default (Shift + Clear is the metronome); MIDI 2's row untouched;
  * the patch: c_p4gath writes "P4", version 1, the 8 codes and the check at padding + 88; c_p4appl restores them, a patch without them = LANE_TAB;
  * psave / xpatch move 100 bytes of padding.

    python tools/emu_p4dest.py SC44.9.bin SC44.9_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R5, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import packio as PK  # noqa: E402
import modmx as MX  # noqa: E402
import p4dest as P4  # noqa: E402

V = T4.V
MGR = X.MGR
CLEAR = 23
LANE_TAB = (17, 8, 15, 3, 1, 2, 11, 9)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    R = man["report"]
    pl = {k: int(v, 16) for k, v in R["p4dest"]["labels"].items()}
    ml = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    nd = int(R["p4dest"]["prev"]["nd"], 16)
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd)); dcol = bytes(e.uc.mem_read(ml["t_dcol"], nd))
    idx = {c: i for i, c in enumerate(dcode)}
    clears = []
    def lc(uc, a, s, d): clears.append(uc.reg_read(UC_ARM_REG_R1)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lc, begin=V.LANE_CLEAR, end=V.LANE_CLEAR)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = lambda t=0: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], t), 8))
    check(row(0) == LANE_TAB and row(1) == LANE_TAB and e.r32(P4.RAM + 16) == V.P4SIG, f"the rows start at LANE_TAB ({row(0)}, {row(1)})")
    e.btn(2); e.btn(8); e.pad(3)
    pg = e.r0(e.vl["c_vpage"], 0)
    check(pg == P4.PAGE, f"pad 4: page {pg}")
    # Shift + K1: slow, through the list
    e.shift(True)
    i0 = idx[17]
    for _ in range(P4.DIV - 1): e.knob(0, 1)
    r1 = row()[0]
    e.knob(0, 1); r2 = row()[0]
    for _ in range(3 * P4.DIV): e.knob(0, 1)
    r3 = row()[0]
    want = dcode[min(nd - 1, i0 + 4)]
    check(r1 == 17 and r2 == dcode[i0 + 1] and r3 == want, f"Shift + K1: {P4.DIV - 1} clicks nothing ({r1}), {P4.DIV} = the next ({r2}), 4 steps = {r3} (want {want})")
    for _ in range(P4.DIV * (nd + 4)): e.knob(1, 1)
    end = row()[1]
    for _ in range(P4.DIV * (nd + 4)): e.knob(1, -1)
    start = row()[1]
    check(end == dcode[-1] and start == dcode[0], f"Shift + K2 clamped at both ends ({end} = {dcode[-1]}, {start} = {dcode[0]})")
    f = X.frame(e)
    exp = [(129 << 8) | dcol[idx[c]] for c in row()]
    check(f[60:68] == exp, f"Shift: the LEDs = the destinations' page colours ({[hex(x) for x in f[60:68]]})")
    e.shift(False)
    # K1 alone: the new destination
    nc = row()[0]
    a0, o0 = e.val(0, nc), e.val(0, 17)
    e.gates.clear(); e.knob(0, 3)
    a1, o1 = e.val(0, nc), e.val(0, 17)
    check(a1 != a0 and o1 == o0, f"K1 moves code {nc} ({a0} -> {a1}), TUNE stays ({o0} -> {o1})")
    check(any(g[0] == 20 for g in e.gates), f"recorded in lane 0 (gate ids {sorted(set(g[0] for g in e.gates))})")
    e.gates.clear(); e.call(e.vl["c_vcc_rec"], 0, 17, 5, maxins=2_000_000)
    check(not e.gates, f"TUNE records nowhere now ({e.gates})")
    e.call(e.vl["c_vapply"], 0, 0, 100, maxins=4_000_000)
    v = e.val(0, nc)
    e.call(e.vl["c_vapply"], 0, 0, 20, maxins=4_000_000)
    check(v != e.val(0, nc), f"lane 0 played: code {nc} follows ({v} -> {e.val(0, nc)})")
    lanes = (e.r0(e.vl["c_vlane"], 0, nc), e.r0(e.vl["c_vlane"], 0, 17), e.r0(e.vl["c_vlane"], 0, row()[2]))
    check(lanes == (0, 0xFF, 2), f"c_vlane: code {nc} = lane 0, TUNE none, code {row()[2]} lane 2 ({lanes})")
    if "c_vclrauto" in e.vl:
        clears.clear()
        e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.knob(0, -1); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
        check(0 in clears, f"Clear + K1 to the left: lane 0 cleared ({clears})")
    # Clear, then Shift + K1: the default
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.knob(0, 1); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    check(row()[0] == 17 and row(1) == LANE_TAB, f"Clear, then Shift + K1: back to TUNE ({row()[0]}); MIDI 2 untouched ({row(1)})")
    # the patch
    e.shift(True)
    for _ in range(P4.DIV * 2): e.knob(4, 1)
    for _ in range(P4.DIV): e.knob(7, -1)
    e.shift(False)
    saved = row()
    e.call(pl["c_p4gath"], 0, maxins=8_000_000)
    buf = bytes(e.uc.mem_read(PK.BUF + P4.POFS, P4.PLEN))
    sm = (0x5A + sum(buf[:11])) & 0xFF
    check(buf[:3] == b"P4\x01" and tuple(buf[3:11]) == saved and buf[11] == sm and bytes(e.uc.mem_read(PK.BUF + 64, 3)) == b"MX\x01",
          f"gather: {buf.hex()} (the matrix before it: {bytes(e.uc.mem_read(PK.BUF + 64, 3))})")
    keep = {24: bytes(24), 12: bytes(buf)}
    def rd(uc, a, s, d):
        n = uc.reg_read(UC_ARM_REG_R3)
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), keep[n]); uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_R1, n)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    hk = e.uc.hook_add(UC_HOOK_CODE, rd, begin=int(R["mpatch"]["labels"]["c_mpr"], 16), end=int(R["mpatch"]["labels"]["c_mpr"], 16))
    e.call(0x08033320, MGR, CLEAR, maxins=8_000_000); e.shift(True); e.knob(4, 1); e.shift(False); e.call(0x0803381A, MGR, CLEAR, maxins=8_000_000)
    mid = row()
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(pl["c_p4appl"], 0, maxins=8_000_000)
    ok1 = row() == saved and mid != saved
    keep[12] = bytes(12)
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(pl["c_p4appl"], 0, maxins=8_000_000)
    ok2 = row() == LANE_TAB
    bad = bytearray(buf); bad[5] = 14; bad[11] = (0x5A + sum(bad[:11])) & 0xFF; keep[12] = bytes(bad)
    e.uc.reg_write(UC_ARM_REG_R5, 11); e.call(pl["c_p4appl"], 0, maxins=8_000_000)
    ok3 = row()[2] == LANE_TAB[2] and row()[0] == saved[0]
    e.uc.hook_del(hk)
    check(ok1 and ok2 and ok3, f"apply: a patch with them restores them ({ok1}); without them LANE_TAB ({ok2}); a code that is not a destination = its default ({ok3})")
    # the mpatch hooks point at ours
    for site, ours in (("c_mpsave", "c_p4gath"), ("c_mpload", "c_p4appl")):
        a0_ = int(R["mpatch"]["labels"][site], 16)
        s = MX.bl_sites(bytearray(img), a0_, a0_ + 0x120, pl[ours], 0x08010000)
        check(len(s) == 1, f"{site} calls {ours} ({[hex(x) for x in s]})")
    ps, xp = R["psave"]["listing"], R["xpatch"]["listing"]
    check(any("#0x64" in l for l in ps) and any("#0x64" in l for l in xp), "psave / xpatch: 100 bytes of padding (movs #0x64 in their listings)")
    del e; gc.collect()
    if "recinst" in R: recinst_part(img, man, check)
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def recinst_part(img, man, check):
    """recinst: Record held + a step pad of MIDI 1's track view = the values that differ from their defaults into the step's lanes"""
    from emu_sc17_6 import PRESS, RELEASE
    import recinst as RI
    e = X.EP(img, man)
    R = man["report"]
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    tdef = int(R["vcf20"]["labels"]["t_def"], 16)
    dflt = lambda c: struct.unpack("b", bytes([e.r8(tdef + c)]))[0]
    setv = lambda c, v: e.uc.mem_write(e.r0(e.vl["c_vvaddr"], 0, c), bytes([v & 0xFF]))
    row = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))
    pat = e.r0(e.vl["c_sdpat"], 0)
    lane = lambda k, st: bytes(e.uc.mem_read(pat + RI.LANES + RI.LANE_BYTES * k + 6 * st, 6))
    ml = {k: int(v, 16) for k, v in R["modmx"]["labels"].items()}
    nd = int(R["recinst"]["prev"]["nd"], 16)
    dcode = bytes(e.uc.mem_read(ml["t_dcode"], nd))
    for c in dcode: setv(c, dflt(c))                                                # everything at its default
    tou = lambda c, v: e.r0(e.vl["c_vtou"], c, v & 0xFFFFFFFF)
    def p1(): e.call(PK.PARAM_GET, RI.TRANSPORT, 1, maxins=100000); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    stp = lambda st: bytes(e.uc.mem_read(pat + 28 * st, 28))
    e.btn(2)                                                                        # MIDI 1's track view
    # nothing changed: nothing written
    before = [lane(k, 3) for k in range(8)]
    e.call(0x08033320, MGR, RI.REC_ID, maxins=8_000_000); armed = p1()
    e.call(PRESS, MGR, 3, 100, maxins=8_000_000); e.call(RELEASE, MGR, 3, maxins=8_000_000)
    e.call(0x0803381A, MGR, RI.REC_ID, maxins=8_000_000)
    check([lane(k, 3) for k in range(8)] == before and p1() == 0 and armed == 1,
          f"all at their defaults: no lane written; Record armed by the press ({armed}), back to {p1()} at the release")
    # FILT (lane 4) and RES (lane 5) changed, plus two codes without a lane (the first two of the list that are not lanes)
    free = [c for c in dcode if c not in LANE_TAB][:2]
    near = lambda c, d: dflt(c) + d if -64 <= dflt(c) + d <= 63 or 0 <= dflt(c) + d <= 127 and dflt(c) >= 0 else dflt(c) - d
    vals = {1: near(1, 20), 2: near(2, 9), free[0]: near(free[0], 3), free[1]: near(free[1], -5)}
    for c, v in vals.items(): setv(c, v)
    for k in range(8): e.uc.mem_write(pat + RI.LANES + RI.LANE_BYTES * k, bytes(range(1, 101)) + bytes(92))     # lanes with old values
    s3 = stp(3)
    e.call(0x08033320, MGR, RI.REC_ID, maxins=8_000_000)
    e.call(PRESS, MGR, 3, 100, maxins=8_000_000); e.call(RELEASE, MGR, 3, maxins=8_000_000)
    e.call(0x0803381A, MGR, RI.REC_ID, maxins=8_000_000)
    r = row()
    want_row = (free[0], free[1]) + LANE_TAB[2:]
    check(r == want_row, f"the row: the two codes without a lane take lanes 0 / 1 (TUNE / REL do not differ): {r} (want {want_row})")
    ok = all(lane(r.index(c), 3) == bytes([tou(c, v)]) * 6 for c, v in vals.items())
    check(ok, f"step 4: each changed value on its lane's 6 micro steps ({[(c, lane(r.index(c), 3).hex()) for c in vals]})")
    cl = lane(0, 5) == bytes([0xFF]) * 6 and lane(1, 0)[:3] == bytes([0xFF]) * 3 and lane(2, 5) == bytes(range(31, 37))
    check(cl, f"lanes 0 / 1 cleared before (another parameter's values), lane 2 untouched ({lane(0, 5).hex()}, {lane(2, 5).hex()})")
    check(stp(3) == s3 and p1() == 0, f"the step's notes untouched (the press swallowed); Record back to {p1()}")
    # page 17-32: the step = pad + 16
    e.btn(21)
    e.call(0x08033320, MGR, RI.REC_ID, maxins=8_000_000)
    e.call(PRESS, MGR, 2, 100, maxins=8_000_000); e.call(RELEASE, MGR, 2, maxins=8_000_000)
    e.call(0x0803381A, MGR, RI.REC_ID, maxins=8_000_000)
    check(lane(r.index(1), 18) == bytes([tou(1, vals[1])]) * 6, f"page 17-32, pad 3 = step 19 ({lane(r.index(1), 18).hex()})")
    # without Record: the stock's step pad
    n0 = stp(4)
    e.call(PRESS, MGR, 4, 100, maxins=8_000_000); e.call(RELEASE, MGR, 4, maxins=8_000_000)
    check(e.r8(RI.RAM) == 0 and e.r8(RI.RAM + 3) == 0, "without Record held the pads go to the stock (no flag left)")
    del e; gc.collect()


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
