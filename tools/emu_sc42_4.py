"""SC42.4 ARM tests: the micro-step rollers of the drums' Note view (rollers.py) and Clear + knob on the own synth of MIDI 1 / 2 (vcf21.use_clrauto).

    python tools/emu_sc42_4.py SC42.4.bin SC42.4_manifest.json
  * Drum 1, Note: rows 1-3 dim in the colour of their column's drum (mirrored: columns 1-4 = drums 4-1, 5-8 = drums 1-4); a held roller bright;
    pads 4 / 12 / 20 = drum 1's micro steps 1-3, 5 / 13 / 21 = 4-6; let go = cleared; another view = every roller cleared;
  * the drum player's slot 2 (the real vtable entry): an empty step with drum 1's rollers 1 and 3 held = hits on micro steps 0 and 2 (velocity 100),
    nothing on the others; a step the pattern hits on micro step 0 (velocity 90) with rollers 1 and 3 = the stock's hit, then ours on micro step 2
    (velocity 90); drum 2's player is not touched by drum 1's rollers;
  * MIDI 1 with its engine, Clear held, through the controller: a knob whose code has a lane, turned left = the stock's lane clear (0x0803D3B8) on
    MIDI 1's pattern editor with that lane, the value kept, the knob red; turned right = its default, lavender (0x07); a knob without a lane, left =
    no lane clear; Clear let go = the knobs' own colours.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4, UC_ARM_REG_PC, UC_ARM_REG_LR
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import rollers as R  # noqa: E402
import vcf21 as V  # noqa: E402

MGR = T.MGR


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
    e.call(0x08033B3E, maxins=40_000_000)
    return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1

    # ---- the rollers: the view
    e = T.EL(img); e.at(100000); e.transport(0)
    e.btn(4); e.btn(9)
    sub = e.r8(MGR + 0x152)
    f = frame(e)
    dim = [R.DRUM_COL[d] + 1 for d in (3, 2, 1, 0, 0, 1, 2, 3)]
    check(sub == 42 and f[0:24] == dim * 3, f"Drum 1, Note: rows 1-3 dim in their column's drum colour ({[hex(x) for x in f[0:8]]})")
    m_addr = e.r32(T.LZ.SESSION_OBJ + 0x14) + R.TAIL + R.O_MASK
    e.call(T.PRESS, MGR, 3, 100, maxins=8_000_000); e.call(T.PRESS, MGR, 12, 100, maxins=8_000_000)
    f2 = frame(e); m1 = e.r8(m_addr)
    check(m1 == 0b010001 and f2[3] == R.DRUM_COL[0] and f2[12] == R.DRUM_COL[0] and f2[4] == R.DRUM_COL[0] + 1,
          f"pad 4 + pad 13 held: drum 1's micro steps 1 and 5, both bright ({m1:#08b}, {f2[3]:#x}, {f2[12]:#x})")
    e.call(T.RELEASE, MGR, 12, maxins=8_000_000)
    check(e.r8(m_addr) == 0b000001, "pad 13 let go: its bit cleared")
    e.call(T.PRESS, MGR, 19, 100, maxins=8_000_000)
    check(e.r8(m_addr) == 0b000101, "pad 20 = drum 1's micro step 3")

    # ---- the drum player's slot 2
    DP = R.DP0
    iface = e.r32(DP + 0x4C); ivt = e.r32(iface); on_fn, off_fn = e.r32(ivt) & ~1, e.r32(ivt + 4) & ~1
    log = []
    def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (log.append(("on", uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))), skip(uc)), begin=on_fn, end=on_fn)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: (log.append(("off", uc.reg_read(UC_ARM_REG_R1))), skip(uc)), begin=off_fn, end=off_fn)
    slot2 = e.r32(R.DP_VT + 8) & ~1
    check(slot2 == int(man["report"]["rollers"]["labels"]["c_rlplay"], 16), "the drum players' slot 2 = c_rlplay")
    pat = 0; base = e.r32(DP + 0x48) + R.PAT_SZ * pat; step = 5
    def play(m_list, dp=DP):
        log.clear()
        for m in m_list: e.call(slot2, dp, pat, step, m, maxins=3_000_000)
        return list(log)
    e.uc.mem_write(base + step, bytes([0])); e.uc.mem_write(base + 0x20 + step, bytes([7])); e.uc.mem_write(base + 0x60 + step, bytes([0]))
    e.uc.mem_write(DP + 0x59, bytes([0]))
    note = e.r8(DP + 0x58)
    got = play(range(6))
    ons = [x for x in got if x[0] == "on"]
    check(ons == [("on", note, 100), ("on", note, 100)] and len(got) == 3, f"an empty step, rollers 1 and 3: two hits of velocity 100, the first stopped before the second ({got})")
    e.uc.mem_write(base + step, bytes([90])); e.uc.mem_write(base + 0x60 + step, bytes([1])); e.uc.mem_write(DP + 0x59, bytes([0]))
    got2 = play(range(6))
    check([x for x in got2 if x[0] == "on"] == [("on", note, 90), ("on", note, 90)], f"the pattern hits micro step 0: the stock's hit, then ours on micro step 2, its velocity ({got2})")
    got3 = play(range(6), DP + R.DP_SZ)
    check(not any(x[0] == "on" and x[1] == note for x in got3) and len([x for x in got3 if x[0] == "on"]) <= 1, f"drum 2's player: drum 1's rollers do not play there ({got3})")
    e.btn(0); frame(e)
    check(e.r32(m_addr) == 0, "another view: every roller cleared")
    del e; gc.collect()

    # ---- Clear + knob on MIDI 1's own synth
    import emu_sc36_1 as T361
    e = T361.E20(img, man)
    for _ in range(30): e.vtick()
    vl = {k: int(v, 16) for k, v in man["report"]["vcf21"]["labels"].items()} if "vcf21" in man["report"] else e.vl
    clears = []
    def lane_clear(uc, a, s, d): clears.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))); skip(uc)
    e.uc.hook_add(UC_HOOK_CODE, lane_clear, begin=V.LANE_CLEAR, end=V.LANE_CLEAR)
    e.call(e.vl["c_vset"], 0, 1); e.vtick(); e.btn(2)
    def val(code): e.call(e.vl["c_vvaddr"], 0, code); return struct.unpack("b", bytes([e.r8(e.uc.reg_read(UC_ARM_REG_R0))]))[0]
    e.call(e.vl["c_vpage"], 0); page = e.uc.reg_read(UC_ARM_REG_R0)
    rows = [V.KNOB_CODES, V.KNOB_CODES_B, V.KNOB_CODES_C, V.KNOB_CODES_D, V.KNOB_CODES_E]
    codes = rows[page]
    k_lane = next(k for k in range(8) if codes[k] in V.LANE_TAB)
    k_none = next(k for k in range(8) if codes[k] and codes[k] not in V.LANE_TAB and codes[k + 8] not in V.LANE_TAB)
    c_lane = codes[k_lane]
    knob = lambda k, d: e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=6_000_000)
    knob(k_lane, 20); v_before = val(c_lane)
    e.call(0x08033320, MGR, 23, maxins=900000)
    clears.clear(); knob(k_lane, -1); fr = frame(e)
    ed1 = V.EDITOR0 + 2 * V.EDITOR_SZ
    lanes = {V.LANE_TAB.index(c) for c in (codes[k_lane], codes[k_lane + 8]) if c in V.LANE_TAB}
    check(clears and all(ed == ed1 for ed, _ in clears) and {ln for _, ln in clears} == lanes and val(c_lane) == v_before,
          f"Clear + K{k_lane + 1} left: the lane clear on MIDI 1's editor, lanes {sorted(lanes)}, the value kept ({[(hex(a_), b_) for a_, b_ in clears]}, {val(c_lane)})")
    check(fr[60 + k_lane] & 0xFF == V.CLR_RED, f"the knob red ({fr[60 + k_lane]:#x})")
    clears.clear(); knob(k_lane, 1); fr = frame(e)
    d_ = struct.unpack("b", bytes([V.DEFAULTS[c_lane - 1] & 0xFF]))[0] if c_lane <= 26 else None
    check(not clears and fr[60 + k_lane] & 0xFF == V.CLR_LAV, f"Clear + K{k_lane + 1} right: no lane clear, lavender ({fr[60 + k_lane]:#x})")
    check(d_ is None or val(c_lane) == d_, f"… and the value back to its default ({val(c_lane)} / {d_})")
    clears.clear(); knob(k_none, -1)
    check(not clears, f"Clear + K{k_none + 1} (no lane) left: nothing cleared")
    e.call(0x0803381A, MGR, 23, maxins=900000); fr = frame(e)
    check(fr[60 + k_lane] & 0xFF not in (V.CLR_RED, V.CLR_LAV), "Clear let go: the knob's own colour")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(bytearray(Path(a[1]).read_bytes()), json.loads(Path(a[2]).read_text())) else 0)
