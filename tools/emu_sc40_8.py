"""SC40.8 ARM tests (live RAM dump, the real routes): Nudge and the fractal / deconstructed play orders (tools/playmode.py).

    python tools/emu_sc40_8.py SC40.8.bin SC40.8_manifest.json SC40.7.bin SC40.7_manifest.json
  * the hooks: the three places where the engine reads the direction, the Pattern Settings view's slots 0 / 7, the LED task calls;
  * the stock's own end test (0x0802C4E4) and track advance (0x0802CB3C), step after step, for several first / last steps and tracks: the step
    that plays and the step the pattern ends at = a model of the fractal order (1 · 1 2 · 1 2 3 ...) and of the deconstructed one (the
    diagonals; steps outside the pattern skipped; 17-32 the same in the second half); the pattern's end restarts both; the look-ahead call
    changes nothing; the stock's directions (forward, reverse) = the previous build;
  * stopped: the fractal's group back to one step;
  * the Pattern Settings view through the controller (Synth 1): pads 26-28 lit (orange, the direction pads' colours); pad 27 / 28 = the order
    in byte 7 of the pattern's settings, the stock's direction forward, no direction pad lit; a direction pad = ours off; pad 26 (Nudge): the
    steps and the twelve automation lanes rotated so that the first step is step 1, over 16 or over 32 steps, the last step moved with it,
    nothing else of the pattern changed; a drum track: the three pads off and without effect.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import emu_sc40_5 as T5  # noqa: E402
import mutate39 as MU  # noqa: E402
import patchain as PC  # noqa: E402
import playmode as PM  # noqa: E402

B = 0x08010000
ENG = PC.ENG
END_TEST, ADVANCE = 0x0802C4E4, 0x0802CB3C


class E8(T5.EC):
    def settings(self, t, p): return self.rec + PC.rule_offset(t, p) - 4
    def setpat(self, t, p, first, last, mode=0, direction=0):
        """the pattern's settings in memory and in the engine's store, as a selection leaves them"""
        self.uc.mem_write(self.settings(t, p), bytes([last, first]))
        self.uc.mem_write(self.settings(t, p) + 3, bytes([direction])); self.uc.mem_write(self.settings(t, p) + 7, bytes([mode]))
        s = self.r32(ENG + 0x50 + 4 * t); self.put(s, 0, bytes([last, first])); self.put(s, 2, bytes([direction]))
    def step(self, t, v=None):
        s = self.r32(ENG + 0x30 + 4 * t)
        if v is not None: self.put(s, 1, bytes([v]))
        return self.r8(self.ptr(s, 1))
    def ends(self, t):
        self.call(END_TEST, ENG, t, 1, maxins=2_000_000); return self.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    def adv(self, t, end, look=0):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", end, 0, 0, 0))
        self.call(ADVANCE, ENG, t, 0, look, maxins=2_000_000)
        store = self.r32(ENG + (0x70 if look else 0x30) + 4 * t)
        for k in (0, 1):
            self.call(0x080354FA, store, k); wp = self.uc.reg_read(UC_ARM_REG_R0); self.uc.mem_write(self.ptr(store, k), bytes(self.uc.mem_read(wp, 1)))
    def k(self, t, v=None):
        if v is not None: self.uc.mem_write(self.tail + PM.S_K + t, bytes([v]))
        return self.r8(self.tail + PM.S_K + t)


def model(mode, first, last, n):
    """the steps that play and where the pattern ends: (steps, ends) for n step ends from the pattern's start"""
    if mode == PM.M_FRAC:
        run = [first + j for k in range(last - first + 1) for j in range(k + 1)]
    else:
        run = [s for s in PM.ORDER if first <= s <= last]
    steps, ends = [], []
    i = 0
    for _ in range(n):
        steps.append(run[i]); e = i == len(run) - 1; ends.append(e); i = 0 if e else i + 1
    return steps, ends


def play(e, t, p, n, look=True):
    """n step ends through the stock's code from where the track is -> (the steps that played, where it said the pattern ended, anything odd)"""
    steps, ends, bad = [], [], []
    for i in range(n):
        s = e.step(t); steps.append(s); en = bool(e.ends(t)); ends.append(en)
        if look:
            k0 = e.k(t); e.adv(t, int(en), look=1)
            if e.k(t) != k0 or e.step(t) != s: bad.append(("look", i))
        e.adv(t, int(en))
    return steps, ends, bad


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["playmode"]["labels"].items()}
    LP = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
    from thumb import bl as tbl
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    at = lambda a, n: bytes(img[a - B:a - B + n])
    check(at(PM.END_HOOK, 4) == tbl(PM.END_HOOK, L["c_pmend"]) and at(PM.STEP_HOOK, 4) == tbl(PM.STEP_HOOK, L["c_pmstep"]) and at(PM.START_HOOK, 4) == tbl(PM.START_HOOK, L["c_pmstart"])
          and bytes(prev[PM.END_HOOK - B:PM.END_HOOK - B + 4]) == PM.DIR_OLD and bytes(prev[PM.STEP_HOOK - B:PM.STEP_HOOK - B + 4]) == PM.DIR_OLD,
          "the engine's three reads of the direction -> c_pmend, c_pmstep, c_pmstart (the previous build: the stock's)")
    check(w(PM.PS_VT) == L["c_pmpspad"] | 1 and w(PM.PS_VT + 28) == L["c_pmpsbuf"] | 1 and all(at(c, 4) == tbl(c, int(man["report"]["rodisk"]["labels"]["c_roledtask"], 16) if "rodisk" in man["report"] else int(man["report"]["fxsess"]["labels"]["c_fsledtask"], 16) if "fxsess" in man["report"] else L["c_pmledtask"]) for c in PK.LED_CALLS)
          and PM.ORDER[:16] == [0, 5, 10, 15, 1, 6, 11, 12, 2, 7, 8, 13, 3, 4, 9, 14] and sorted(PM.ORDER) == list(range(32)),
          "the Pattern Settings view's slots 0 / 7, the LED task calls; the deconstructed order = 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15, then the same + 16")
    e = E8(img, man, LP); p = E8(prev, prev_man, {k: int(v, 16) for k, v in prev_man["report"]["patchain"]["labels"].items()})
    for x in (e, p):
        x.live(0x00)                                                              # (no chain rules here)
        for t in range(8): x.chain(t, x.playing(t), x.playing(t))
    cases = [(0, 0, 15), (1, 0, 7), (2, 2, 9), (3, 0, 31), (5, 4, 4), (6, 0, 20), (0, 3, 3 + 5), (4, 16, 31)]
    for mode, name in ((PM.M_FRAC, "fractal"), (PM.M_DEC, "deconstructed")):
        bad = []; total = 0
        for t, first, last in cases:
            pat = e.playing(t)
            n = 2 * (len(model(mode, first, last, 1)[0]) and (sum(range(1, last - first + 2)) if mode == PM.M_FRAC else last - first + 1)) + 3
            n = min(n, 140)
            e.setpat(t, pat, first, last, mode); e.k(t, 0); e.step(t, model(mode, first, last, 1)[0][0])
            got = play(e, t, pat, n); want = model(mode, first, last, n); total += n
            if got[0] != want[0] or got[1] != want[1] or got[2]: bad.append((t, first, last, got[0][:24], want[0][:24], got[2][:2]))
        ex = model(mode, 0, 7, 12)[0]
        check(not bad, f"the {name} order through the stock's end test and track advance: {total} step ends in {len(cases)} patterns = the model (steps 1-8: {[s + 1 for s in ex]}...); "
              f"the pattern's end restarts it; the look-ahead call changes nothing {bad[:2]}")
    # a pattern that starts by its end flag from a step outside our order: the start hook puts the first step of the order
    e.setpat(2, e.playing(2), 3, 12, PM.M_DEC); e.step(2, 3); e.adv(2, 1); s_dec = e.step(2)
    e.setpat(2, e.playing(2), 3, 12, PM.M_FRAC); e.k(2, 5); e.step(2, 9); e.adv(2, 1); s_fr = (e.step(2), e.k(2))
    check(s_dec == 5 and s_fr == (3, 0), f"a pattern that starts: the first step of the order within the pattern (deconstructed, steps 4-13: step {s_dec + 1}); the fractal: its first step, one step long")
    # the stock's directions as before
    seqs = []
    for x in (e, p):
        x.setpat(0, x.playing(0), 0, 7, 0, 0); x.step(0, 0); f_ = play(x, 0, x.playing(0), 18, look=False)
        x.setpat(0, x.playing(0), 0, 7, 0, 1); x.step(0, 7); r_ = play(x, 0, x.playing(0), 18, look=False)
        x.setpat(0, x.playing(0), 0, 7, 0, 0); seqs.append((f_[:2], r_[:2]))
    check(seqs[0] == seqs[1] and seqs[0][0][0][:10] == [0, 1, 2, 3, 4, 5, 6, 7, 0, 1] and seqs[0][1][0][:4] == [7, 6, 5, 4], f"the stock's forward and reverse = the previous build ({seqs[0][0][0][:10]}, {seqs[0][1][0][:6]})")
    p.setpat(0, p.playing(0), 0, 7, PM.M_FRAC); p.step(0, 0); pf = play(p, 0, p.playing(0), 10, look=False)
    check(pf[0] == [0, 1, 2, 3, 4, 5, 6, 7, 0, 1], "the previous build ignores byte 7: forward")
    del p; gc.collect()
    def ledtask():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=30_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    def transport(on): e.uc.mem_write(e.ptr(MU.PLAY_STORE, 0), bytes([on]))
    for t in range(8): e.k(t, 3 + t)
    transport(1); ledtask(); a_ = [e.k(t) for t in range(8)]; transport(0); ledtask(); b_ = [e.k(t) for t in range(8)]
    check(a_ == [3 + t for t in range(8)] and b_ == [0] * 8, "playing: the fractal's groups stay; stopped: back to one step")

    # ---- the Pattern Settings view
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    def frame():
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    T = 0
    e.set_p0(e.r32(CONT + 0x188), T); press(T); release(T); press(12); release(12)
    pat = e.playing(T); S = e.settings(T, pat); base = S - PM.SET_OFF
    e.setpat(T, pat, 0, 15, 0, 0)
    f0 = frame()
    U, C = PM.COL_UNSEL, PM.COL_SEL
    check(e.r8(MGR + 0x152) == 4 and f0[24:] == [f0[24], PM.COL_NUDGE, U, U, C, U, U, U],
          f"Pattern Settings (Synth 1): pad 26 orange, pads 27 / 28 as the direction pads not chosen, forward chosen ({[hex(x) for x in f0[24:]]})")
    pad(PM.PAD_FRAC); m1 = (e.r8(S + 7), e.r8(S + 3), frame()[24:])
    pad(PM.PAD_DEC); m2 = (e.r8(S + 7), e.r8(S + 3), frame()[24:])
    pad(PM.PAD_DIR + 1); m3 = (e.r8(S + 7), e.r8(S + 3), frame()[24:])
    pad(PM.PAD_FRAC); m4 = (e.r8(S + 7), e.r8(S + 3))
    pad(PM.PAD_DIR); m5 = (e.r8(S + 7), e.r8(S + 3), frame()[24:])
    check(m1 == (PM.M_FRAC, 0, [f0[24], PM.COL_NUDGE, C, U, U, U, U, U]) and m2 == (PM.M_DEC, 0, [f0[24], PM.COL_NUDGE, U, C, U, U, U, U]),
          f"pad 27 / pad 28: the order in byte 7 of the settings, the stock's direction forward, the pad lit and no direction pad lit ({m1[:2]}, {m2[:2]})")
    check(m3 == (0, 1, [f0[24], PM.COL_NUDGE, U, U, U, C, U, U]) and m4 == (PM.M_FRAC, 0) and m5 == (0, 0, [f0[24], PM.COL_NUDGE, U, U, C, U, U, U]),
          f"a direction pad: ours off, the stock's direction; from reverse, pad 27 puts it forward again ({m3[:2]}, {m4}, {m5[:2]})")
    # Nudge
    def fill():
        steps = b"".join(bytes([0x10 + s, s]) + bytes((7 * s + i) & 0xFF for i in range(26)) for s in range(32))
        lanes = b"".join(bytes((l * 37 + s * 5 + i) & 0xFF for s in range(32) for i in range(6)) for l in range(12))
        e.uc.mem_write(base, steps); e.uc.mem_write(base + PM.AUTO_OFF, lanes); return steps, lanes
    def rot(data, size, n, k): return b"".join(data[size * ((i + k) % n):size * ((i + k) % n) + size] for i in range(n)) + data[size * n:]
    res = []
    for first, last, n in ((5, 12, 16), (3, 2, 16), (20, 27, 32), (4, 30, 32), (0, 9, 16)):
        e.setpat(T, pat, first, last, 0, 0); steps, lanes = fill()
        whole0 = bytes(e.uc.mem_read(base, 0xCA8))
        pad(PM.PAD_NUDGE)
        whole = bytes(e.uc.mem_read(base, 0xCA8))
        want_s = rot(steps, 28, n, first) if first else steps
        want_l = b"".join(rot(lanes[192 * l:192 * l + 192], 6, n, first) for l in range(12)) if first else lanes
        nl = (last - first) % n if first else last
        ok = whole[:len(steps)] == want_s and whole[PM.AUTO_OFF:PM.AUTO_OFF + len(lanes)] == want_l and (e.r8(S), e.r8(S + 1)) == (nl, 0)
        rest = whole[len(steps):PM.SET_OFF] == whole0[len(steps):PM.SET_OFF] and whole[PM.SET_OFF + 2:PM.AUTO_OFF] == whole0[PM.SET_OFF + 2:PM.AUTO_OFF] and whole[PM.AUTO_OFF + len(lanes):] == whole0[PM.AUTO_OFF + len(lanes):]
        res.append((first, last, n, ok, rest, e.r8(S), e.r8(S + 1)))
    check(all(r[3] and r[4] for r in res), f"pad 26 (Nudge): steps and the 12 automation lanes rotated to the first step, over 16 or 32, first = 1, the last step moved; the rest of the pattern as it was "
          f"({[(r[0] + 1, r[1] + 1, r[2], '->', r[6] + 1, r[5] + 1) for r in res]})")
    # a drum track
    press(12); release(12); press(12); release(12)
    e.set_p0(e.r32(CONT + 0x188), 4); press(4); release(4); press(12); release(12)
    dp = e.playing(4); DS = e.settings(4, dp); e.setpat(4, dp, 2, 9, 0, 0); d0 = bytes(e.uc.mem_read(DS - 0x80, 0x6A8)); fd = frame()
    pad(PM.PAD_NUDGE); pad(PM.PAD_FRAC); pad(PM.PAD_DEC)
    if "fxsess" in man["report"]:                                                 # (SC40.9: the drum tracks too, see emu_sc40_9.py)
        check(fd[25:28] == [PM.COL_NUDGE, PM.COL_UNSEL, PM.COL_UNSEL], f"a drum track: pads 26-28 lit ({[hex(x) for x in fd[24:]]})")
    else:
        check(fd[25:28] == [0, 0, 0] and bytes(e.uc.mem_read(DS - 0x80, 0x6A8)) == d0, f"a drum track: pads 26-28 off and without effect ({[hex(x) for x in fd[24:]]})")
    print("SC40.8 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
