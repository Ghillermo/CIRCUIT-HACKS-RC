"""SC57.8 / Beta 5.63 tests: the step flip's fixes of the 2026-11-14 bug hunt (jumpseq.use_stopclr / use_audrel + its companion, jumprnd.use_v2,
jsaflip.use_sel), through the stock's tick and the players' own slots as emu_jumpseq.py / emu_jumprnd.py (whose harness this is):
  * JR-4: a jump left pending at Stop (the target at half the rate) does not run after the next Play's SET_TICKS(0) with nothing pointing;
  * XC-3: one note on MIDI 1's first step: Synth 1 jumps on every Play (SET_TICKS(0), then the first step), not only the first time;
  * JR-7 (b): notes on micro steps 0 and 2 of a step, the target starting its step on micro step 0: one jump, never a second one on its next step;
  * JR-7 (a): MIDI 2 also pointing (at Synth 2, another rate, its notes between MIDI 1's two): MIDI 1's two notes still land near half each;
  * JR-5: a pad pressed stopped and let go after Play: the target's note-off (the pre-listen's release) is sent; pressed and let go running: nothing;
  * JR-6: a drum target, a pad on a flipped step held, then a pad on a step without a flip: the selected sample is set before the second hit.

    python tools/emu_jumpfix.py BUILD.bin manifest.json [--only A,B,...] [--loops N]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc48_8 as S  # noqa: E402
import emu_arp as EAm  # noqa: E402
import emu_jumpseq as EJ  # noqa: E402
import arp as A  # noqa: E402
import jumpseq as J  # noqa: E402
import mpatch  # noqa: E402

ENG, SEQ_TICK, PLAYERS = EJ.ENG, EJ.SEQ_TICK, EJ.PLAYERS
SET_TICKS = 0x0802BFE0
TX = 0x20011334
DP0 = 0x20040810
note_of = lambda s_: 59 + (s_ & 16) + 2 * (s_ & 7) + (s_ >> 3 & 1)                    # the pattern's note for a step, the root at C


class H:
    """one emulator: MIDI 1 / 2's patterns, the stores' rates, a clock as on the unit"""
    def __init__(self, img, man):
        self.img, self.man = img, man
        e = self.e = S.ET(img, man)
        e.marks.pop(0x0802E5BC, None); e.marks.pop(0x0802E61C, None)
        self.R = man["report"]
        self.t = [500000]; self.at(0)
        self.rec = e.r32(J.SESSION_OBJ + 0x14) + J.TAIL + J.O_JS
        kb_scale = e.r32(J.MU.KB_CTX + 0xC); kb_root = e.r32(J.MU.KB_CTX + 0x10)
        e.uc.mem_write(kb_root, bytes([0])); e.w32(kb_scale + 4, EJ.mask_of(EJ.MINOR))
        self.pats = {}
        for m in (0, 1):
            e.call(int(self.R["vcf20"]["labels"]["c_sdpat"], 16), m, maxins=1_000_000); self.pats[m] = e.uc.reg_read(UC_ARM_REG_R0)
            e.uc.mem_write(self.pats[m], bytes(S.chord([], 32)))
        self.seen = []
        self.rates = [3] * 8
        # the harness answers SET_TICKS itself (emu_sc17_7: the stock's resync needs pattern data the dump lacks): the heads in front of it run
        # here (from the b.w at its entry), the stock's body is cut at SET_TICKS + 4 and the ticks are written as the harness does
        self.st_head = mpatch.bw_target(img, SET_TICKS, 0x08010000)
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: uc.emu_stop(), begin=SET_TICKS + 4, end=SET_TICKS + 4)

    def at(self, ms): self.t[0] += ms; self.e.w32(A.HAL_TICK, self.t[0])

    def step(self, m, s_, units): self.e.uc.mem_write(self.pats[m] + 28 * s_, bytes(S.chord(units, 1)))

    def point(self, m1, m2): self.e.uc.mem_write(self.rec, bytes([m1, m2, J.SIG]))

    def setup(self, rates):
        e = self.e; self.rates = rates
        for q, k in ((0, 2), (1, 3), (2, 0), (3, 1)):                                     # the patterns' own rate (a pattern's start reloads it; the dump's chains
            e.call(int(self.R["vcf20"]["labels"]["c_sdrec"], 16), q, maxins=1_000_000)   # move a track on to its next pattern at the wrap: all eight patterns)
            base = e.r32(e.uc.reg_read(UC_ARM_REG_R0) + 0x48)
            for i in range(8): e.uc.mem_write(base + 0xCA8 * i + 0x380 + 2, bytes([rates[k]]))
        for k in range(8):
            st = e.r32(ENG + 0x50 + 4 * k)
            EAm.EA.setp(e, st, 0, bytes([15, 0])); EAm.EA.setp(e, st, 1, bytes([rates[k]])); EAm.EA.setp(e, st, 2, bytes([0]))

    def rewind(self, set_ticks=True):
        """Play from the start: the real SET_TICKS(engine, 0) (the Play handler's), then every track one tick before its first step"""
        e = self.e
        e.transport(0)
        if set_ticks:
            e.call(self.st_head, ENG, 0, maxins=3_000_000)
            g = e.r32(ENG + 0x90)
            for b in (e.r32(g + 0xC), e.r32(g + 0x10)): e.w32(b, 0)
        tps = (2, 3, 4, 6, 8, 12, 16, 24)
        for k in range(8):
            st = e.r32(ENG + 0x30 + 4 * k)
            EAm.EA.setp(e, st, 1, bytes([0])); EAm.EA.setp(e, st, 2, struct.pack("<I", tps[self.rates[k]] - 1))   # the next clock: step 2
            EAm.EA.setp(e, e.r32(ENG + 0x70 + 4 * k), 1, bytes([0]))
        e.transport(1)

    def clock(self):
        e = self.e
        self.at(21); e.call(SEQ_TICK, ENG, maxins=5_000_000)
        st = e.r32(ENG + 0x30)
        if e.r32(e.ptr(st, 2)) == 0: self.seen.append((e.r8(e.ptr(e.r32(ENG + 0x38), 1)), e.r8(e.ptr(st, 1))))   # (MIDI 1's step, Synth 1's) on each start
        for o in (0x14, 0x18):
            for p in PLAYERS: e.call(e.r32(e.r32(p)) & ~1, p, e.r32(p + o), maxins=3_000_000)


def done(h):
    del h.e; gc.collect()


def t_stale(img, man):
    """JR-4: MIDI 1's step 5 -> Synth 1 (half the rate: a step of it starts with MIDI 1's 4 / 6) to step 13, Stop with it pending, nothing
    pointing, Play: Synth 1 goes on from its step 2 (the harness's first clock)"""
    h = H(img, man); e = h.e
    h.step(0, 4, [(note_of(12), 3, 0, 100)]); h.point(1, 0); h.setup([5] + [3] * 7)
    e.uc.mem_write(J.RAM + 4, bytes(8)); h.rewind(set_ticks=False)
    pend = 0
    for _ in range(40):
        h.clock(); pend = e.r8(J.RAM + 4)
        if pend: break
    e.transport(0)
    h.step(0, 4, []); h.point(0, 0)
    h.seen.clear(); h.rewind()
    for _ in range(36): h.clock()
    syn = [s for _, s in h.seen]
    done(h)
    return pend == 13, syn


def t_replay(img, man, runs):
    """XC-3: one note on MIDI 1's first step played (step 2 in the harness) -> Synth 1 to step 10; Play, a few clocks, Stop, again: a jump each time"""
    h = H(img, man)
    h.step(0, 1, [(note_of(9), 3, 0, 100)]); h.point(1, 0); h.setup([3] * 8)
    first = []
    for _ in range(runs):
        h.seen.clear(); h.rewind()
        for _ in range(3): h.clock()
        first.append(h.seen[0][1] if h.seen else None)
    done(h)
    return first


def t_micro(img, man, loops):
    """JR-7 (b): MIDI 1's step 5 holds a note for step 10 on micro step 0 and one for step 14 on micro step 2; Synth 1 at the same rate"""
    h = H(img, man)
    h.step(0, 4, [(note_of(9), 1, 0, 100), (note_of(13), 1, 2, 100)]); h.point(1, 0); h.setup([3] * 8)
    h.e.uc.mem_write(J.RAM + 4, bytes(8)); h.rewind()
    for _ in range(6 * 16 * loops): h.clock()
    land = [s for m, s in h.seen if m == 4]                                            # the jump: Synth 1 on MIDI 1's step 5
    nxt = [s for m, s in h.seen if m == 5]                                             # its next step: the landing + 1, no second jump
    done(h)
    return land, nxt


def t_two(img, man, loops):
    """JR-7 (a): MIDI 1's step 5 holds notes for steps 10 / 14 on micro steps 0 / 3, Synth 1 at half the rate (it lands on MIDI 1's step 6);
    MIDI 2 points at Synth 2 at 2 ticks a step, a note on every step: its notes come between MIDI 1's two"""
    h = H(img, man)
    h.step(0, 4, [(note_of(9), 1, 0, 100), (note_of(13), 1, 3, 100)])
    for s_ in range(16): h.step(1, s_, [(note_of(3), 1, 0, 100)])
    h.point(1, 2); h.setup([5, 3, 3, 0, 3, 3, 3, 3])
    h.e.uc.mem_write(J.RAM + 4, bytes(8)); h.rewind()
    for _ in range(6 * 16 * loops): h.clock()
    land = [s for m, s in h.seen if m == 5]
    done(h)
    return {9: land.count(9), 13: land.count(13)}, len(land)


def t_audrel(img, man):
    """JR-5: MIDI 1 points at MIDI 2 (its step 11: note 60); the target's interface slots (0 on, 1 off) logged"""
    h = H(img, man); e = h.e
    h.point(4, 0)
    st = h.pats[1] + 28 * 10
    e.uc.mem_write(st, bytes([1, 7, 0, 0, 60, 6, 0, 100]))
    ON, OFF = e.r32(J.TX_VT) & ~1, e.r32(J.TX_VT + 4) & ~1
    P3 = J.PLAYER0 + 3 * J.PLAYER_SZ
    ifc = e.r32(P3 + 0x4C); vt = e.r32(ifc)
    log = []
    for k in (0, 1):
        f = e.r32(vt + 4 * k) & ~1
        def hk(uc, a, s_, d, k=k):
            if uc.reg_read(UC_ARM_REG_R0) == ifc: log.append((k, uc.reg_read(UC_ARM_REG_R1)))
        e.uc.hook_add(UC_HOOK_CODE, hk, begin=f, end=f)
    n = note_of(10) - 12
    on = lambda: e.call(ON, TX, 2, n, 100, maxins=5_000_000)
    off = lambda: e.call(OFF, TX, 2, n, maxins=5_000_000)
    out = {}
    e.transport(0); log.clear(); on(); off(); out["stopped"] = list(log)
    log.clear(); on(); out["press"] = list(log); log.clear(); e.transport(1); off(); out["after_play"] = list(log)
    log.clear(); on(); off(); out["running"] = list(log)
    log.clear(); on(); e.transport(0); off(); out["run_stop"] = list(log)
    done(h)
    return out


def t_sel(img, man):
    """JR-6: MIDI 1 points at Drum 1; its step 11 has a sample flip, step 12 none: A held, then B"""
    from emu_sc48_8 import ET  # noqa: F401
    h = H(img, man); e = h.e; R = h.R
    ON, OFF = e.r32(J.TX_VT) & ~1, e.r32(J.TX_VT + 4) & ~1
    dh = []
    ifd = e.r32(DP0 + 0x4C); don = e.r32(e.r32(ifd)) & ~1
    def d_on(uc, a, s_, d):
        if uc.reg_read(UC_ARM_REG_R0) == ifd: dh.append(("on", uc.reg_read(UC_ARM_REG_R1)))
    e.uc.hook_add(UC_HOOK_CODE, d_on, begin=don, end=don)
    dsm = int(R["drumarp"]["labels"]["c_dasmp"], 16)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s_, d: dh.append(("c_dasmp", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1))), begin=dsm, end=dsm)
    h.point(5, 0)
    e.call(int(R["drumarp"]["labels"]["c_dapat"], 16), 0, maxins=1_000_000); pn = e.uc.reg_read(UC_ARM_REG_R0)
    vb = e.r32(DP0 + 0x48) + pn * 0x6A8
    sel = e.r8(e.ptr(e.r32(DP0 + 0x5C), 0)); fl = 5 if sel != 5 else 6
    e.uc.mem_write(vb, bytes(32)); e.uc.mem_write(vb + 0x40, bytes([0xFF]) * 32)
    e.uc.mem_write(vb + 10, bytes([77])); e.uc.mem_write(vb + 0x40 + 10, bytes([fl])); e.uc.mem_write(vb + 11, bytes([66]))
    tx = lambda s_: note_of(s_) - 12
    e.transport(0)
    dh.clear(); e.call(ON, TX, 2, tx(10), 100, maxins=5_000_000); a_on = list(dh)
    dh.clear(); e.call(ON, TX, 2, tx(11), 100, maxins=5_000_000); b_on = list(dh)
    e.call(OFF, TX, 2, tx(10), maxins=5_000_000); e.call(OFF, TX, 2, tx(11), maxins=5_000_000)
    done(h)
    return sel, fl, a_on, b_on


def main(a):
    img, man = Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else set("ABCDEF")
    loops = int(a[a.index("--loops") + 1]) if "--loops" in a else 24
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if "A" in only:
        ok, syn = t_stale(img, man)
        check(ok and 12 not in syn and syn[:1] == [1], f"JR-4: a jump pending at Stop does not run after Play with nothing pointing (Synth 1 {syn})")
    if "B" in only:
        first = t_replay(img, man, 8)
        check(first == [9] * 8, f"XC-3: one note on the first step: Synth 1 jumps on every Play ({first})")
    if "C" in only:
        land, nxt = t_micro(img, man, loops // 2)
        check(len(land) >= loops // 2 - 1 and set(land) <= {9, 13}, f"JR-7 (b): the step jumps ({ {s: land.count(s) for s in set(land)} })")
        check(len(nxt) >= loops // 2 - 1 and all(s in (10, 14) for s in nxt), f"JR-7 (b): no second jump from the same step (the next step: { {s: nxt.count(s) for s in set(nxt)} })")
    if "D" in only:
        got, n = t_two(img, man, loops)
        check(n >= loops - 1 and all(v >= n * 0.2 for v in got.values()), f"JR-7 (a): MIDI 2 pointing too: MIDI 1's two notes near half each over {n} ({ {k + 1: v for k, v in got.items()} })")
    if "E" in only:
        o = t_audrel(img, man)
        check(o["stopped"] and o["stopped"][0][0] == 0 and o["stopped"][-1][0] == 1, f"JR-5: stopped press / release: on and off as before ({o['stopped']})")
        check(any(k == 1 for k, _ in o["after_play"]), f"JR-5: pressed stopped, let go after Play: the off ({o['press']} / {o['after_play']})")
        check(o["running"] == [], f"JR-5: pressed and let go running: nothing ({o['running']})")
    if "F" in only:
        sel, fl, a_on, b_on = t_sel(img, man)
        k_dsm = [i for i, x in enumerate(b_on) if x[0] == "c_dasmp" and x[2] == sel]
        k_on = [i for i, x in enumerate(b_on) if x[0] == "on"]
        check(any(x[0] == "c_dasmp" and x[2] == fl for x in a_on), f"JR-6: A's press sets its flip ({a_on})")
        check(k_dsm and k_on and k_dsm[0] < k_on[0], f"JR-6: B (no flip) with A held: the selected sample ({sel}) before B's hit ({b_on})")
    print(f"{Path(a[0]).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
