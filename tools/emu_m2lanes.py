"""Alpha 7.42 test (m2lanes + novasec.use_v9) through the controller, on Synth 1's alt page with Macros 2 on the knobs (extra knob 1 = VCF
frequency, row 34; extra knob 2 = OSC 1 semitones, row 12):
  * recording while playing (pattern 3, step 6): K1 = its value into the first half of that step, later in the step into the second half; the
    bitmap's bit;
  * a step held (pads 4 / 5 on the 17-32 page, edited pattern 4): K2 = steps 20 / 21, both halves; nothing else in the lane;
  * Clear + K2 left = knob 2's lane of the edited pattern cleared; Clear + K1 right = row 34 back to the patch's value in the record, no lane
    touched;
  * the players' slot 2: Synth 1 at micro step 0 / 3 = the half step's value set, micro 1 nothing, 0xFF nothing, the lanes not in place
    nothing, the knob just turned by hand nothing (and 300 ms later it plays); Synth 2 with no extra knob: nothing;
  * the stock paste Synth 1 -> Synth 1 copies the block, from MIDI 1 = none; the pattern clear = none; the Nudge rotates the 8 lanes over first ..
    last (back / forward);
  * the power-up head: the 8 KB 0xFF and the ITCM ours; the reset head: the state zeroed; the stock's calls pointed at them.
    python tools/emu_m2lanes.py firmware/a7.42
"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR
import emu_sc48_8 as S
import emu_sc42_6 as X
import emu_arp as EAm
import fxdiag as FD
import arp as A
import novasec as N
import m2lanes as M

MGR, GETTER = S.MGR, 0x08036192
PRESS, RELEASE, KNOB, BTN, BTN_UP = 0x08033282, 0x080332FE, 0x08033848, 0x08033320, 0x0803381A
ID_CLEAR = 23
ROW_K1, ROW_K2 = 34, 12


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    R = man["report"]
    L = {k: int(v, 16) for k, v in R["m2lanes"]["labels"].items()}
    prv = {k: int(v, 16) for k, v in R["m2lanes"]["prev"].items()}
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    N.use_v2(); N.use_fix(); N.use_v3(); N.use_v4(); N.use_v8()
    e = S.ET(img, man)
    setp = lambda st, k, data: EAm.EA.setp(e, st, k, data)
    w8 = lambda ad, v: e.uc.mem_write(ad, bytes([v]))
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def frame(): at(20); X.frame(e); return X.frame(e)
    def quiet(ms=1000): at(ms); return frame()
    def knob(k, dl, n=1, held=None):
        if held is not None: e.call(BTN, MGR, held, maxins=8_000_000)
        for _ in range(n): e.call(KNOB, MGR, k, dl & 0xFFFFFFFF, maxins=8_000_000)
        if held is not None: e.call(BTN_UP, MGR, held, maxins=8_000_000)
    def get(s, p): e.call(GETTER, s, p, maxins=400_000); return e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    gst = int(R["sc14"]["labels"]["c_gst"], 16)
    def alt():
        e.call(gst, maxins=100_000); g = e.uc.reg_read(UC_ARM_REG_R0)
        return g and e.r8(g + N.S_PAINT) & N.F_SRC and e.r8(MGR + 0x152) == 0
    rd = lambda ad, n: bytes(e.uc.mem_read(ad, n))
    blk = lambda b: rd(M.IT0 + M.BLK * b, M.BLK)
    lane = lambda b, k: rd(M.IT0 + M.BLK * b + 64 * k, 64)
    st8 = lambda o: e.r8(M.M2 + o)
    mapw = lambda: struct.unpack("<H", rd(M.M2 + M.O_MAP, 2))[0]
    rec = e.r32(N.SESSION + 0x14)
    def xset(s, rows):                                                          # the synth's extra-knob block in the record (novasec.use_fix)
        bs = [N.XSIG, 0] + list(rows); bs[1] = (sum(bs[2:]) & 0xFF) ^ 0xA5
        for j, v in enumerate(bs): w8(rec + N.SYN_AREA + N.PSIZE * (8 * s + (j >> 1)) + N.PSET + N.XB + (j & 1), v)

    # ---- the static part: the stock's calls pointed at the heads
    B = 0x08010000
    check(FD.bl_target(img, M.RST_AT, B) == L["c_m2rst"] and FD.bl_target(img, M.BOOT_AT, B) == L["c_m2boot"]
          and FD.bl_target(img, int(R["novasec"]["labels"]["kn_m2"], 16), B) == L["c_m2rec"]
          and FD.bl_target(img, int(R["novasec"]["labels"]["kn_m2c"], 16), B) == L["c_m2clr"], "the reset / power-up calls and novasec's two calls pointed here")

    at(0)
    for _ in range(5):
        if alt(): break
        e.btn(0); quiet()
    check(alt(), "Synth 1's alt page reached")
    xset(0, [ROW_K1, ROW_K2] + [0xFF] * 6); xset(1, [0xFF] * 8)
    w8(N.NS + 4, (e.r8(N.NS + 4) & 0xF0) | 8)
    e.uc.mem_write(M.M2, bytes(M.ST_LEN)); e.uc.mem_write(M.IT0, b"\xFF" * M.DATA)
    e.uc.mem_write(M.M2 + M.O_SIG, struct.pack('<I', M.SSIG)); w8(M.M2 + M.O_VAL, 1)
    quiet()

    # ---- recording while playing: pattern 3, step 6, first then second half
    eng = e.r32(M.ENG + 0x30)
    setp(eng, 0, bytes([2])); setp(eng, 1, bytes([5])); setp(eng, 2, struct.pack("<I", 0))
    e.transport(1); setp(A.TRANSPORT, 1, bytes([1]))
    v0 = get(0, ROW_K1); knob(0, 2); v1 = get(0, ROW_K1)
    check(v1 != v0 and lane(2, 0)[10] == v1 and lane(2, 0)[11] == 0xFF and mapw() & 4, f"recording: K1 {v0} -> {v1} into pattern 3, step 6, first half ({lane(2, 0)[8:14].hex()})")
    setp(eng, 2, struct.pack("<I", 100)); knob(0, 2); v2 = get(0, ROW_K1)
    check(lane(2, 0)[11] == v2 and lane(2, 0)[10] == v1, f"later in the step: {v2} into the second half ({lane(2, 0)[8:14].hex()})")
    check(st8(M.O_RK) == 0x80, f"the knob turned by hand noted ({st8(M.O_RK):#x})")
    setp(A.TRANSPORT, 1, bytes([0])); e.transport(0)
    before = blk(2)
    knob(0, 1)
    check(blk(2) == before, "stopped, nothing held: a turn writes nothing")

    # ---- a step held: pads 4 / 5 on the 17-32 page, the edited pattern 4
    h = e.r32(e.r32(e.r32(e.r32(N.CTX) + 0x40) + 0x2C) + 0x148)
    setp(e.r32(h + M.HELD_STORE), 0, bytes([1])); setp(e.r32(M.STEP_OBJ0 + M.STEP_PAGE), 0, bytes([1]))
    setp(e.r32(M.PAT_OBJ + 0x24), 0, bytes([3])); e.w32(MGR + 0x84, 1 << 3 | 1 << 4)
    knob(1, 1); w = get(0, ROW_K2)
    ln = lane(3, 1)
    check(ln[38:42] == bytes([w] * 4) and ln[:38] + ln[42:] == b"\xFF" * 60 and mapw() & 8, f"steps 20 / 21 held + K2: {w} into both halves of both ({ln[36:44].hex()})")
    setp(e.r32(h + M.HELD_STORE), 0, bytes([0])); setp(e.r32(M.STEP_OBJ0 + M.STEP_PAGE), 0, bytes([0])); e.w32(MGR + 0x84, 0)

    # ---- Clear + K2 left, Clear + K1 right
    k1before = lane(3, 0)
    knob(1, -1, held=ID_CLEAR)
    check(lane(3, 1) == b"\xFF" * 64, "Clear + K2 left: knob 2's lane of the edited pattern cleared")
    knob(0, 3); moved = get(0, ROW_K1)
    ent = M.ROWTAB + 8 * ROW_K1
    off, kind = struct.unpack("<H", img[ent - B:ent - B + 2])[0], img[ent - B + 2]
    want = e.r8(rec + M.REC_SYN + off)
    knob(0, 1, held=ID_CLEAR)
    check(kind in (1, 2) and get(0, ROW_K1) == want and lane(3, 0) == k1before, f"Clear + K1 right: row 34 back to the patch's value ({moved} -> {get(0, ROW_K1)}, the record {want}), no lane touched")

    # ---- the players' slot 2
    slot2 = e.r32(M.PLAYER_VT + 8) & ~1
    check(slot2 == L["c_m2pl"], "the players' slot 2 = c_m2pl")
    base = M.IT0 + M.BLK * 2 + 2 * 4
    e.uc.mem_write(base, bytes([40, 90])); w8(M.M2 + M.O_RK, 0)
    play = lambda s, p, step, mi: e.call(slot2, M.PLAYER0 + M.PLAYER_SZ * s, p, step, mi, maxins=20_000_000)
    knob(0, 5); play(0, 2, 4, 0); check(get(0, ROW_K1) == 40, f"micro step 0: the first half's value (40: {get(0, ROW_K1)})")
    play(0, 2, 4, 3); check(get(0, ROW_K1) == 90, f"micro step 3: the second half's (90: {get(0, ROW_K1)})")
    e.uc.mem_write(base, bytes([40])); play(0, 2, 4, 1); check(get(0, ROW_K1) == 90, "micro step 1: nothing")
    play(0, 2, 7, 0); check(get(0, ROW_K1) == 90, "a step without a value: nothing")
    w8(M.M2 + M.O_VAL, 0); play(0, 2, 4, 0); check(get(0, ROW_K1) == 90, "the lanes not in place: nothing"); w8(M.M2 + M.O_VAL, 1)
    w8(M.M2 + M.O_RK, 0x80); e.w32(M.M2 + M.O_RT, t[0]); play(0, 2, 4, 0)
    check(get(0, ROW_K1) == 90, "the knob just turned by hand: not played over")
    at(300); play(0, 2, 4, 0); check(get(0, ROW_K1) == 40, "300 ms later: played")
    s2 = get(1, ROW_K1); e.uc.mem_write(M.IT0 + M.BLK * 10 + 2 * 4, bytes([7]))
    play(1, 2, 4, 0); check(get(1, ROW_K1) == s2, "Synth 2 with no extra knob: nothing")

    # ---- paste / clear / Nudge
    patp = lambda tr, p: e.r32(M.PAT_OBJ + M.PAT_SZ * tr + 4) + M.PAT_N * p
    src = blk(2)
    e.call(L["c_m2cp"], M.PAT_OBJ, patp(0, 2), 5, maxins=60_000_000)
    check(blk(5) == src and mapw() & 0x20, "paste Synth 1 pattern 3 -> pattern 6: the block copied, its bit")
    e.call(L["c_m2cp"], M.PAT_OBJ, patp(2, 0), 5, maxins=60_000_000)
    check(blk(5) == b"\xFF" * M.BLK, "paste from MIDI 1: none")
    e.call(L["c_m2cl"], M.PAT_OBJ, 2, maxins=60_000_000)
    check(blk(2) == b"\xFF" * M.BLK, "the pattern clear: none")
    e.uc.hook_add(UC_HOOK_CODE, lambda u, a_, s_, dd: u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1), begin=prv["nudge"], end=prv["nudge"])
    e.call(int(R["patchain"]["labels"]["c_pcrule"], 16), 0, 4, maxins=400_000); sa = e.uc.reg_read(UC_ARM_REG_R0) - 4
    w8(sa, 3); w8(sa + 1, 0)
    for k in (0, 7): e.uc.mem_write(M.IT0 + M.BLK * 4 + 64 * k, bytes([10 + k, 11, 20, 21, 30, 31, 40, 41]))
    e.call(L["c_m2nu"], 0, 0, 4, 0, maxins=2_000_000)
    check(all(lane(4, k)[:8] == bytes([20, 21, 30, 31, 40, 41, 10 + k, 11]) for k in (0, 7)), f"Nudge back: steps 1-4 one to the left ({lane(4, 0)[:8].hex()})")
    e.call(L["c_m2nu"], 0, 0, 4, 1, maxins=2_000_000)
    check(all(lane(4, k)[:8] == bytes([10 + k, 11, 20, 21, 30, 31, 40, 41]) for k in (0, 7)), f"Nudge forward: back again ({lane(4, 0)[:8].hex()})")

    # ---- the power-up and reset heads (the stock's calls below not run)
    for k in ("boot", "rst"):
        e.uc.hook_add(UC_HOOK_CODE, lambda u, a_, s_, dd: u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR) | 1), begin=prv[k], end=prv[k])
    e.uc.mem_write(M.M2, bytes(M.ST_LEN)); e.uc.mem_write(M.IT0, bytes(M.DATA))
    e.call(L["c_m2boot"], 0, maxins=2_000_000)
    check(rd(M.IT0, M.DATA) == b"\xFF" * M.DATA and struct.unpack('<I', rd(M.M2 + M.O_SIG, 4))[0] == M.SSIG, "the power-up head: the 8 KB 0xFF, the ITCM ours")
    e.uc.mem_write(M.M2, b"\x5A" * M.ST_LEN)
    e.call(L["c_m2rst"], maxins=200_000)
    check(rd(M.M2, M.ST_LEN) == bytes(M.ST_LEN), "the reset head: the state zeroed")
    print("M2LANES RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
