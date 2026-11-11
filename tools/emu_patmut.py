"""SC55.8 / Beta 5.43 tests (tools/patmut.py, the pattern mutate): the real routes (the controller, the stock's track advance 0x0802CB3C).

    python tools/emu_patmut.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

  * c_pmgen = patmut.model for 300 (track, chain, seed, settings);
  * the Patterns view: Shift + a Duplicate tap = a seed and every selected track a list (the project block: mark, check); the advance plays the
    list from slot 1 and loops, the look-ahead gives the same pattern and moves nothing; a track without a list: patchain / the stock's chain;
  * Shift + Duplicate held: the page (peach: the chosen values bright); its pads change the settings, the list follows at once, a value set back
    gives the list back; a track button deselects (its list ends), again selects (it joins); Duplicate closes the page;
  * the Patterns view closed: the pads of the patterns outside the list dark, the playing one the stock's; Shift: Duplicate yellow;
  * a pattern pad of a track ends its list; Clear + Duplicate ends them all; Shift + Duplicate in a track view: nothing of ours;
  * a chain changed: the list made again from the same seed over it;
  * scenes: the save writes the tracks / seed / settings into the scene's bytes 34..39; a scene starting (the advance) or picked while stopped
    (the Mixer) puts them back; a scene without them: no lists;
  * the previous build: Shift + Duplicate changes nothing of the record's tail + 367..375;
  * SC55.9 / Beta 5.44 (patmut.use_v2, found by the label c_pmend): eight Amount steps on columns 4 / 5 of the page, Repeats on 6, Keep slot 1
    on 7 (LEDs and values); the end of a mutating track's chain = its list's last slot (the bl at 0x0802C65E, as the stock uses it), not the
    chain's last pattern in the middle of the list; a track without a list: the stock's test.
"""
from __future__ import annotations
import gc, json, random, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_5 as T  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R4  # noqa: E402
import patchain as PC  # noqa: E402
import patmut as P  # noqa: E402

MGR = T.MGR
ENG = T.ENG


def labels(man, sec): return {k: int(v, 16) for k, v in man["report"][sec]["labels"].items()}


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = labels(man, "patchain"); M = labels(man, "patmut")
    V2 = "c_pmend" in M
    P.AMT8 = V2
    e = T.EC(img, man, L)
    blk = lambda: bytes(e.uc.mem_read(e.rec + P.TAIL_OFF, 9))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    tick = [100_000]
    def at(ms): tick[0] = ms; e.w32(T.PK.HAL_TICK, ms)
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=30_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    def r0(fn, *a): e.call(fn, *a, maxins=4_000_000); return e.uc.reg_read(UC_ARM_REG_R0)

    # ---- the generator against the model
    rnd = random.Random(7); bad = []
    for _ in range(300):
        t = rnd.randrange(8); f = rnd.randrange(8); l_ = rnd.randrange(8); seed = rnd.randrange(65536)
        s0, s1 = P.settings(rnd.randrange(1, 9), rnd.randrange(3), rnd.randrange(8 if V2 else 4), rnd.random() < 0.5, rnd.random() < 0.5)
        got = r0(M["c_pmgen"], t, f << 4 | l_, seed | s0 << 16 | s1 << 24) & 0x0FFFFFFF
        want = P.pack_word(P.model(t, f, l_, seed, s0, s1))
        if got != want: bad.append((t, f, l_, seed, s0, s1, hex(got), hex(want)))
    check(not bad, f"c_pmgen = the model, 300 cases ({bad[:2]})")

    trk = {}                                                                          # (column, row) -> pad
    for q in range(32): trk[(r0(PC.TRACKFN, q), q >> 3)] = q
    at(100_000)
    e.set_p0(e.r32(T.CONT + 0x188), 0); press(0); release(0)
    press(13); release(13)
    check(e.r32(MGR + 0x6C) == PC.PV, "the Patterns view on the screen")
    e.put(PC.PLAY_STORE, 0, bytes(1))                                               # the transport stopped
    for t in range(8): e.chain(t, 0, 3); e.set_playing(t, 0)
    # ---- Shift + Duplicate tap
    b0 = blk()
    shift(1); press(24); at(100_100); release(24); shift(0)
    b1 = blk(); seed = b1[3] | b1[4] << 8
    s0, s1 = b1[5], b1[6]
    check(b1[0] == P.MARK and b1[1] == 0xFF and b1[7] == (sum(b1[1:7]) ^ 0x5A) & 0xFF, f"Shift + Duplicate tap: every track a list, the block ours ({b0.hex()} -> {b1.hex()})")
    want0 = P.model(0, 0, 3, seed, s0, s1)
    e.advance(0, forced=1); seq = [e.playing(0)]
    for _ in range(2 * len(want0) - 1):
        la = None
        e.advance(0, look=1); la = e.ahead(0)
        e.advance(0); seq.append(e.playing(0))
        if la != seq[-1]: seq.append(("look", la))
    check(seq == (want0 * 2)[:len(seq)] and len(seq) == 2 * len(want0), f"the advance plays the list from slot 1 and loops, the look-ahead the same ({seq} / {want0})")
    # ---- the page
    at(101_000); shift(1); press(24); at(101_100); f_h = frame(); at(101_500); f_p = frame(); release(24); shift(0)
    ram = lambda: bytes(e.uc.mem_read(P.RAM, 64))
    check(ram()[P.R_FL] & P.FL_OPEN and not f_h == f_p, f"Shift + Duplicate held 1/3 s: the page open (flags {ram()[P.R_FL]})")
    f_p = frame()
    want_len = lambda col, row: P.C_ON if 4 * col + row == ((s0 & 7) ^ 3) else P.C_DIM
    ok = all(f_p[trk[(c, r)]] & 0xFF == want_len(c, r) for c in (0, 1) for r in range(4))
    check(ok and all(f_p[32 + t] & 0xFF == P.C_ON for t in range(8)) and f_p[P.LED_DUP] & 0xFF == P.C_ON,
          f"the page: Length in peach (chosen bright), the tracks bright, Duplicate peach ({[hex(f_p[trk[(0, r)]]) for r in range(4)]})")
    pad(trk[(0, 1)]); pad(trk[(2, 1)])                                                # Length 2, exact
    nb = blk(); s0b = nb[5]
    want2 = P.model(0, 0, 3, seed, s0b, nb[6])
    check(nb[3:5] == b1[3:5] and len(want2) == 2 and ((s0b & 7) ^ 3) + 1 == 2 and (s0b >> 3) & 3 == 1, f"Length 2 exact: the seed kept, the settings {s0b:#x}")
    e.advance(0, forced=1); sq = [e.playing(0)]
    for _ in range(3): e.advance(0); sq.append(e.playing(0))
    check(sq == want2 * 2, f"the list follows at once ({sq} / {want2})")
    pad(trk[(0, 3)]); pad(trk[(2, 0)])                                                # back to Length 4 as the chain
    e.advance(0, forced=1); sq = [e.playing(0)]
    for _ in range(len(want0) - 1): e.advance(0); sq.append(e.playing(0))
    check(sq == want0 and blk()[5] == s0, f"the values back: the list back ({sq})")
    press(1); release(1)                                                              # Synth 2's button: deselected, its list ends
    b2 = blk()
    check(b2[2] == 0x02 and b2[1] == 0xFD and bytes(e.uc.mem_read(P.RAM, 64))[P.R_FL] & P.FL_OPEN, f"a track button on the page: deselected, its list ends, the page stays ({b2.hex()})")
    press(1); release(1)
    check(blk()[2] == 0 and blk()[1] == 0xFF, "again: selected, it joins")
    if V2:
        # eight Amount steps: column 4 rows 1-4 = 0..3, column 5 = 4..7; Repeats column 6, Keep slot 1 column 7
        okv = True
        for col in (3, 4):
            for row in range(4):
                pad(trk[(col, row)]); v = blk()[5] >> 5
                fa = frame(); lit = [(c, r) for c in (3, 4) for r in range(4) if fa[trk[(c, r)]] & 0xFF == P.C_ON]
                okv &= v == 4 * (col - 3) + row and lit == [(col, row)]
        check(okv, "eight Amount steps: columns 4 / 5, the chosen one bright")
        s0a = blk()[5]; want7 = P.model(0, 0, 3, seed, s0a, blk()[6])
        e.advance(0, forced=1); sq = [e.playing(0)]
        for _ in range(len(want7) - 1): e.advance(0); sq.append(e.playing(0))
        check(sq == want7, f"Amount 8 of 8 (a little): the list as the model ({sq} / {want7})")
        pad(trk[(5, 1)]); r1 = blk()[6]; pad(trk[(6, 1)]); r2 = blk()[6]; fr = frame()
        check(r1 == 2 and r2 == 3 and fr[trk[(5, 1)]] & 0xFF == P.C_ON and fr[trk[(6, 1)]] & 0xFF == P.C_ON and fr[trk[(7, 0)]] == 0,
              f"Repeats off = S1 bit 1 (column 6), Keep slot 1 = bit 0 (column 7), column 8 dark ({r1}, {r2})")
        pad(trk[(5, 0)]); pad(trk[(6, 0)]); pad(trk[(3, 0)])
        check(blk()[5] == s0 and blk()[6] == s1, f"the values back ({blk()[5]:#x} {blk()[6]:#x})")
    press(24); release(24)
    check(not ram()[P.R_FL] & P.FL_OPEN, "Duplicate closes the page")
    # ---- the overlay
    e.set_playing(0, want0[0])
    f_o = frame(); inlist = set(want0)
    dark = [p for p in range(4) if f_o[trk[(0, p)]] == 0]
    check(set(dark) == set(range(4)) - inlist - {want0[0]}, f"the overlay: the patterns outside the list dark ({sorted(dark)}, list {want0})")
    shift(1); f_s = frame(); shift(0)
    check(f_s[P.LED_DUP] & 0xFF == P.C_SHIFT, "Shift held: Duplicate yellow")
    # ---- a pattern pad ends the track's list
    pad(trk[(3, 2)])
    check(blk()[1] == 0xF7, f"a pattern pad of MIDI 2 ends its list ({blk()[1]:#x})")
    e.chain(3, 0, 3); e.advance(3, forced=1); a_ = e.playing(3); e.advance(3); b_ = e.playing(3)
    check((a_, b_) == (0, 1), f"MIDI 2 back on its chain ({a_}, {b_})")
    # ---- a chain changed: the same seed over the new chain
    e.chain(0, 4, 7); want4 = P.model(0, 4, 7, seed, s0, s1)
    e.advance(0, forced=1); sq = [e.playing(0)]
    for _ in range(len(want4) - 1): e.advance(0); sq.append(e.playing(0))
    check(sq == want4, f"a new chain: the list made again over it ({sq} / {want4})")
    e.chain(0, 0, 3)
    if V2:
        # ---- the end of the chain: the list's last slot (the bl at 0x0802C65E, as the stock uses it)
        import fm8dest as FD
        from unicorn.arm_const import UC_ARM_REG_R7, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_CPSR
        tgt = FD.bl_target(bytearray(img), PC.END_HOOK, 0x08010000)
        check(tgt == M["c_pmend"], f"the bl at 0x0802C65E -> c_pmend ({tgt:#x})")
        def ends(t, cur):
            uc = e.uc; uc.reg_write(UC_ARM_REG_R7, t); uc.reg_write(UC_ARM_REG_R11, cur); uc.reg_write(UC_ARM_REG_R10, 0)
            e.call(tgt, e.ptr(e.r32(ENG + 0x9C), t))
            z = (uc.reg_read(UC_ARM_REG_CPSR) >> 30) & 1; r = uc.reg_read(UC_ARM_REG_R0)
            return bool(z and e.r8(r + 1) == cur), uc.reg_read(UC_ARM_REG_R7) == t and uc.reg_read(UC_ARM_REG_R11) == cur
        b0_ = blk()
        found = None
        for sd in range(1, 4000):                                                   # a Length 6 exact list with pattern 3 before its last slot
            s0x, s1x = P.settings(6, 1, 0, False, False)
            lst = P.model(0, 0, 3, sd, s0x, s1x)
            if 3 in lst[:-1] and lst[-1] != 3: found = (sd, s0x, s1x, lst); break
        sd, s0x, s1x, lst = found
        for off, v in ((P.B_SEED, sd & 0xFF), (P.B_SEED + 1, sd >> 8), (P.B_S0, s0x), (P.B_S1, s1x)): e.call(M["c_pmset"], off, v)
        e.advance(0, forced=1); got = []
        for i in range(len(lst)):
            cur = e.playing(0); en, kept = ends(0, cur); got.append((cur, en)); e.advance(0)
        check([c for c, _ in got] == lst and [en for _, en in got] == [False] * (len(lst) - 1) + [True] and kept,
              f"a mutating track: its chain ends with its list's last slot, not on pattern 3 in the middle ({got})")
        e.call(M["c_pmset"], P.B_ACT, 0xFE)                                         # Synth 1 without a list: the stock's test
        e.chain(0, 0, 3)
        st = [ends(0, p)[0] for p in range(4)]
        check(st == [False, False, False, True], f"a track without a list: the stock's test ({st})")
        for off, v in zip(range(1, 8), b0_[1:8]): e.call(M["c_pmset"], off, v)
    # ---- scenes
    press(14); release(14); MIXV = e.r32(MGR + 0x6C)
    shift(1); e.call(0x08050EE8, MIXV + 0xC, 2, maxins=8_000_000); shift(0)
    scn = lambda s: bytes(e.uc.mem_read(e.rec + P.SC_BASE + P.SC_LEN * s, 40))
    s2 = scn(2)
    check(s2[32] != 0 and s2[34:39] == blk()[1:2] + blk()[3:7] and s2[39] == (sum(s2[34:39]) ^ P.SC_CHK) & 0xFF,
          f"the scene save: the tracks, the seed, the settings into bytes 34..39 ({s2[32:40].hex()})")
    shift(1); e.call(0x08050EE8, MIXV + 0xC, 5, maxins=8_000_000); shift(0)
    check(scn(2)[34:40] == s2[34:40], "another scene saved: scene 3's bytes kept")
    at(102_000); shift(1); press(24); at(102_100); release(24); shift(0)               # Shift + Duplicate in the Mixer: a new seed
    b3 = blk()
    check(b3[3:5] != b1[3:5], f"Shift + Duplicate in the Mixer: a new seed ({b1[3:5].hex()} -> {b3[3:5].hex()})")
    e.advance(0, scene_start=1, scene=2)
    check(blk()[1:2] + blk()[3:7] == s2[34:39], "a scene starting: its lists back")
    held(0); press(23); held(1); press(24); release(24); held(0); release(23)
    check(blk()[1] == 0, f"Clear + Duplicate: every list ends ({blk()[1]:#x})")
    pad(16 + 2)
    check(blk()[1:2] + blk()[3:7] == s2[34:39], f"stopped, scene 3 picked in the Mixer: its lists back ({blk().hex()})")
    pad(16 + 9)
    check(blk()[1] == 0, "a scene without ours: no lists")
    # ---- Shift + Duplicate in a track view: nothing of ours
    press(0); release(0); bt = blk()
    at(103_000); shift(1); press(24); at(103_100); release(24); shift(0)
    check(blk() == bt, "Shift + Duplicate in Synth 1's view: nothing of ours")
    del e; gc.collect()
    # ---- the previous build
    pe = T.EC(prev, pman, labels(pman, "patchain"))
    pb = bytes(pe.uc.mem_read(pe.rec + P.TAIL_OFF, 9))
    pe.set_p0(pe.r32(T.CONT + 0x188), 0); pe.call(0x08033320, MGR, 13, maxins=8_000_000); pe.call(0x0803381A, MGR, 13, maxins=8_000_000)
    pe.set_p0(pe.r32(MGR + 0xC), 1); pe.call(0x08033320, MGR, 24, maxins=8_000_000); pe.call(0x0803381A, MGR, 24, maxins=8_000_000)
    check(bytes(pe.uc.mem_read(pe.rec + P.TAIL_OFF, 9)) == pb, "the previous build: nothing changes")
    del pe; gc.collect()
    print(f"{man.get('marker', '?')} PATMUT RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    A = [Path(x) for x in sys.argv[1:5]]
    sys.exit(1 if main(A[0].read_bytes(), json.loads(A[1].read_text()), A[2].read_bytes(), json.loads(A[3].read_text())) else 0)
