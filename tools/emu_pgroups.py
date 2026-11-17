"""Chains of pattern groups (patchain.use_groups + scrules, SC57.4 / Beta 5.59), on the RAM dump:
  * the engine (the stock's track advance with c_pcnext / c_pcstep, the end test c_pcend): A x i -> B x j -> C x k -> A ...; no C = A, B; no B
    = A only; the chain ends (for the scenes) at the end of the last group's last pass; a restart begins at A's start; a track off the rules or
    without a chain: the stock's;
  * the Patterns view in the chain mode (through the controller): Shift + start + end = A, then B, then C (a start after its end is turned
    round); a fourth = nothing; the start pads yellow / green / red, a start waiting for its end white; a start pad = K1 sets its repeats
    (1-16, 4 clicks a step; knob LEDs: 1-8 white, 9-16 the first n - 8 blue); Clear + B = B gone, Clear + A = the chain gone; Duplicate +
    a start pad, then a pad of another track = the chain copied (the copy stays when the original goes);
  * scenes (scrules): Shift + scene pad = the eight chains into the scene; picked stopped / starting while playing = back; the card section,
    saved as on the device (r5 = the slot, [manager + 0x60] p0 = the pack: fails up to Beta 5.62, scrules.use_svfix()), none in pack 0.

    python tools/emu_pgroups.py firmware/sc57.4
"""
from __future__ import annotations
import gc, json, random, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_6
emu_sc17_6.MIX_PRESS = -1                                       # the Mixer's pad handler for real
from emu_sc40_5 import EC, ENG  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import packio as PK  # noqa: E402
import patchain as PC  # noqa: E402
import scrules as SR  # noqa: E402
import xlanes as XL  # noqa: E402

PRESS, RELEASE, KNOB = 0x08033282, 0x080332FE, 0x08033848
SES = XL.SESSION_OBJ


def model(groups, start, n):
    """the patterns that play after `start` (state: group 0, no pass) and whether each pattern end is the chain's end"""
    g, c, p = 0, 0, start; out = []
    last = len(groups) - 1
    for _ in range(n):
        s, e, r = groups[g]
        end = p == e and c + 1 >= r and g == last
        if s <= p < e: p += 1
        elif p == e:
            if c + 1 < r: c += 1; p = s
            else: c = 0; g = (g + 1) % len(groups); p = groups[g][0]
        else: c = 0; p = s
        out.append((p, end))
    return out


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    L = {k: int(v, 16) for k, v in R["patchain"]["labels"].items()}
    A = {k: int(v, 16) for k, v in R["scrules"]["labels"].items()}
    B = {k: int(v, 16) for k, v in R["scrules"]["io"]["labels"].items()}
    xl = {k: int(v, 16) for k, v in R["xlanes"]["labels"].items()}
    xpv = {k: int(v, 16) for k, v in R["xlanes"]["prev"].items()}
    e = EC(img, man, L)
    for k in ("load", "new"):
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=xpv[k], end=xpv[k])
    r0 = lambda: e.uc.reg_read(UC_ARM_REG_R0)
    RB = SR.RB
    st = lambda o, n: bytes(e.uc.mem_read(RB + o, n))
    word = lambda t: struct.unpack_from("<I", st(SR.O_CURW + 4 * t, 4))[0]
    mask = lambda: st(SR.O_CURM, 1)[0]
    def setw(t, groups):
        e.uc.mem_write(RB + SR.O_CURW + 4 * t, struct.pack("<I", SR.pack(groups) if groups else 0))
        m = mask(); m = (m | 1 << t) if groups else (m & ~(1 << t)); e.uc.mem_write(RB + SR.O_CURM, bytes([m]))
    e.uc.mem_write(RB, bytes(SR.O_SCW + 16 * 32)); e.uc.mem_write(RB, b"SCR3")
    e.st(); e.persistent(); e.clear_state(); e.live(0xFF)

    # ---- the engine
    def run(t, groups, start, n, stock=(2, 4)):
        e.chain(t, *stock); setw(t, groups); e.clear_state(); e.set_playing(t, start)
        got = []
        for _ in range(n):
            cur = e.playing(t); end, _ok = e.end_test(t, cur)
            e.advance(t); got.append((e.playing(t), end))
        return got
    for name, groups in (("A x 2, B x 1, C x 1", [(0, 1, 2), (3, 3, 1), (5, 6, 1)]), ("no C: A x 3, B x 2", [(1, 2, 3), (6, 7, 2)]),
                         ("no B: A x 4", [(4, 6, 4)]), ("A x 16", [(0, 0, 16)])):
        got = run(1, groups, groups[0][0], 24)
        exp = model(groups, groups[0][0], 24)
        check(got == exp, f"{name}: {[p + 1 for p, _ in got[:14]]}…, the chain's end where the model says ({[i for i, (_, x) in enumerate(got) if x][:3]})")
    got = run(2, [(0, 1, 2), (3, 3, 1)], 6, 3)
    check([p for p, _ in got] == [0, 1, 0], f"a track off its groups (pattern 7): into A's start ({[p + 1 for p, _ in got]})")
    setw(3, [(5, 6, 1)]); e.chain(3, 2, 4); e.clear_state(); e.set_playing(3, 1); e.advance(3, forced=1)
    check(e.playing(3) == 5, f"a restart (forced): A's start, not the stock chain's first ({e.playing(3) + 1})")
    setw(3, [(5, 6, 1)]); e.set_playing(3, 1); e.advance(3, forced=1, look=1)
    check(e.ahead(3) == 5, f"the look-ahead of a restart: A's start ({e.ahead(3) + 1})")
    setw(4, None); e.chain(4, 2, 4); e.clear_state(); e.set_playing(4, 2); e.advance(4)
    check(e.playing(4) == 3, f"a track without a chain: the stock chain ({e.playing(4) + 1})")
    setw(1, [(0, 1, 2)]); e.live(0xFF & ~2); e.chain(1, 2, 4); e.clear_state(); e.set_playing(1, 2); e.advance(1)
    check(e.playing(1) == 3, f"a track off the rules (chain mode off): the stock chain ({e.playing(1) + 1})")
    e.live(0xFF)

    # ---- the Patterns view
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=30_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    knob = lambda k, d: e.call(KNOB, MGR, k, d & 0xFFFFFFFF, maxins=6_000_000)
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)
    press(13); release(13)
    col = {}
    for q in range(8):
        e.call(PC.TRACKFN, q); col[r0()] = q
    P = lambda t, pat: 8 * (pat % 4) + col[t]
    shift(1); press(20); release(20); shift(0)
    check(e.r8(e.scr + PC.S_EDIT) == 1, "Shift + Octave up: the chain mode")
    for t in range(8): setw(t, None)
    T = 1
    sg = lambda a, b: (shift(1), pad(P(T, a)), pad(P(T, b)), shift(0))
    sg(0, 1); w1 = word(T)
    sg(3, 2); w2 = word(T)
    sg(1, 1); w3 = word(T)
    sg(2, 3); w4 = word(T)
    check((w1, w2, w3, w4) == (SR.pack([(0, 1, 1)]), SR.pack([(0, 1, 1), (2, 3, 1)]), SR.pack([(0, 1, 1), (2, 3, 1), (1, 1, 1)]), w3) and mask() == 1 << T,
          f"Shift + start + end: A (1-2), B (4 then 3 = 3-4), C (2-2); a fourth: nothing ({w4:#010x})")
    f = frame()
    check(f[P(T, 0)] == PC.COL_A and f[P(T, 2)] == PC.COL_B and f[P(T, 1)] == PC.COL_C, f"the start pads: A yellow, B green, C red ({hex(f[P(T, 0)])}, {hex(f[P(T, 2)])}, {hex(f[P(T, 1)])})")
    shift(1); pad(P(2, 3)); shift(0); f = frame()
    check(f[P(2, 3)] == PC.COL_PEND and e.r8(e.scr + PC.G_PEND) == 0x80 | 2 << 3 | 3, f"a start waiting for its end: white ({hex(f[P(2, 3)])})")
    shift(1); pad(P(2, 1)); shift(0)
    check(word(2) == SR.pack([(1, 3, 1)]), f"... its end on the same track: A 2-4 ({word(2):#010x})")
    pad(P(T, 0))
    reps = []
    for d in (1, 1, 1, 1, 1, 1, 1, 1):
        knob(0, d); reps.append(((word(T) >> 6) & 15) + 1)
    check(reps == [1, 1, 1, 2, 2, 2, 2, 3], f"A's start pad, then K1: 4 clicks a step ({reps})")
    for _ in range(4 * 7): knob(0, 1)
    f = frame(); kl = f[60:68]
    blue, white = PC.COL_BLUE | 129 << 8, PC.KNOB_ON
    check(((word(T) >> 6) & 15) + 1 == 10 and kl == [blue, blue] + [white] * 6, f"10 repeats: knobs 1-2 blue, 3-8 white ({[hex(x) for x in kl]})")
    for _ in range(4 * 10): knob(0, 1)
    check(((word(T) >> 6) & 15) + 1 == 16 and frame()[60:68] == [blue] * 8, "16 at most: all eight blue")
    for _ in range(4 * 20): knob(0, -1)
    check(((word(T) >> 6) & 15) + 1 == 1 and frame()[60:68] == [white] + [0] * 7, "down to 1 at least: K1 lit")
    pad(P(T, 2)); knob(0, 1); knob(0, 1); knob(0, 1); knob(0, 1)
    check((word(T) >> 16) & 15 == 1 and (word(T) >> 6) & 15 == 0, "B's start pad: K1 = B's repeats")
    held(2); pad(P(T, 0)); pad(P(5, 3)); held(0)
    check(word(5) == word(T) and mask() & (1 << 5), f"Duplicate + A's start, then a pad of Drum 2: the chain copied ({word(5):#010x})")
    held(1); pad(P(T, 2)); held(0)
    check(not word(T) >> 30 & 1 and word(T) & 0x3FF == SR.pack([(0, 1, 1)]) & 0x3FF, f"Clear + B: B gone, A stays ({word(T):#010x})")
    held(1); pad(P(T, 0)); held(0)
    check(not mask() & 1 << T and mask() & 1 << 5, "Clear + A: the chain gone; the copy stays")

    # ---- scenes (scrules) and the card
    press(14); release(14)
    setw(0, [(0, 1, 2)]); setw(1, [(4, 5, 1), (7, 7, 3)]); setw(5, None); setw(2, None)
    S1 = (word(0), word(1), mask())
    shift(1); pad(16); shift(0)
    setw(0, [(2, 3, 1)]); setw(1, None)
    shift(1); pad(17); shift(0)
    pad(16); e.call(B["c_srwork"], maxins=200_000_000)
    check((word(0), word(1), mask()) == S1, f"scene 1 picked (stopped): its chains back ({mask():#04x})")
    pad(17); e.call(B["c_srwork"], maxins=200_000_000)
    check(word(0) == SR.pack([(2, 3, 1)]) and not mask() & 2, "scene 2: its chains (MIDI 2 back on the stock chain)")
    e.clear_state(); e.set_playing(1, 0); e.advance(1, forced=1, scene_start=1, scene=0)
    check(word(1) == S1[1] and mask() & 2 and e.playing(1) == 4, f"playing, scene 1 starts on Synth 2: its chain back, from A's start ({e.playing(1) + 1})")
    # the save as on the device (the stock save 0x0802FDF8: r5 at the bl 0x0802FE5E = the slot, [manager + 0x60] p0 = the pack; the loaded
    # pack's items are keyed 0xFF, the storage task's current pack modelled): up to Beta 5.62 the two were swapped (the 2026-11-14 bug hunt,
    # SCR-1 / XC-1: scrules.use_svfix())
    PACK, SLOT = 5, 3
    e.cur = e.scur = PACK
    item = lambda slot: (XL.KIND_SES, slot, 0xFF)
    plain = bytes(random.Random(5).randrange(256) for _ in range(XL.SZ0))
    e.sd[item(SLOT)] = plain
    pad(17); e.call(B["c_srwork"], maxins=200_000_000)                               # (the stopped scene settled first)
    e.set_p0(e.r32(SES + 0x60), PACK); e.uc.reg_write(UC_ARM_REG_R5, SLOT); e.call(A["c_srsv"], SES, maxins=2_000_000)
    data = st(SR.O_DATA, SR.DATA)
    keys0 = {k: v for k, v in e.sd.items()}
    e.call(B["c_srwork"], maxins=200_000_000)
    f3 = e.sd[item(SLOT)]
    check(len(f3) == SR.OFF + SR.SECT and f3[SR.OFF:SR.OFF + 4] == b"SCN3" and f3[SR.OFF + SR.HDR:] == data, f"the save: the section after the lanes' area ({len(f3)} B)")
    other = sorted(k for k in e.sd if k != item(SLOT) and e.sd[k] != keys0.get(k))
    check(not other and e.scur == PACK, f"... in project {SLOT} of the loaded pack {PACK} only (else {other}), the storage task still on it ({e.scur})")
    e.uc.mem_write(RB + SR.O_DATA, bytes(SR.DATA))
    e.call(PK.PARAM_GET, e.r32(XL.PROJ_OBJ + 0x20), 8, maxins=100000); e.uc.mem_write(r0(), bytes([3]))
    e.call(A["c_srld"], maxins=2_000_000); e.call(B["c_srwork"], maxins=200_000_000)
    check(st(SR.O_DATA, SR.DATA) == data, "the load: the chains and the scenes back")
    e.call(A["c_srnew"], maxins=2_000_000); e.call(B["c_srwork"], maxins=200_000_000)
    check(mask() == 0 and struct.unpack_from("<H", st(SR.H_MAP, 2))[0] == 0, "a new project: no chains")
    setw(0, [(0, 1, 2)]); keys0 = {k: v for k, v in e.sd.items()}
    e.set_p0(e.r32(SES + 0x60), 0); e.uc.reg_write(UC_ARM_REG_R5, SLOT); e.call(A["c_srsv"], SES, maxins=2_000_000)
    e.call(B["c_srwork"], maxins=200_000_000)
    check(e.sd == keys0 and not st(SR.H_FL, 1)[0] & SR.F_SAVE, "a save in pack 0 (internal, read-only for the mod): nothing written")
    gc.collect()
    print("ALL PASS" if not fails else f"{fails} FAILED")
    return fails


if __name__ == "__main__":
    d = Path(sys.argv[1])
    sys.exit(main(next(d.glob("*.bin")).read_bytes(), json.loads((d / "manifest.json").read_text())))
