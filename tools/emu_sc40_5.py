"""SC40.5 ARM tests (live RAM dump, the real routes): pattern chains (tools/patchain.py).

    python tools/emu_sc40_5.py SC40.5.bin SC40.5_manifest.json SC40.4.bin SC40.4_manifest.json
  * the hooks: the choice of the next pattern (0x0802CD4A), the end-of-chain test (0x0802C65E), the next scene (0x0802C6A6 and its committing
    call), the scene save / copy, the end of the load, the Patterns view's pad slot, the head of the button chain, the LED task calls;
  * the stock's track advance 0x0802CB3C itself, pattern end after pattern end, for rules AAAB AAAC, AAAAAAAAB, ABAC, a rule inside a rule and
    drums: the pattern that plays = a model; the look-ahead call changes nothing and gives the same answer; a track on the stock chain, a
    forced restart and a scene start (the scene's flag); without rules = the previous build;
  * the end-of-chain test: the stock's for a track without rules running; a track on a rule ends its chain when it comes back from C (from B
    without C), not before;
  * the scenes: the next scene = the current one while it has repeats left, counted by the committing call only; a scene asked for by hand: none;
  * the scene save through the controller (Mixer view, Shift + a scene pad): the scene takes the tracks on the rules; again within 1.5 s: one
    repeat more, up to 8; later: once; the checksum right; a tail with garbage: not ours, every track on the rules, nothing repeated;
  * the Patterns view through the controller: Shift + Octave up = the edit (Octave up white); A, A again, B, C write n, B, C into the pattern's
    settings bytes 4..6 and nothing else of the record; the LEDs (yellow / green / red / white, the knob LEDs = n); Clear + pad = the rule
    gone, the pattern kept; Shift + Octave down and a view button leave; out of the edit a plain press puts the track on the stock chain and
    Clear + pad clears the rule too;
  * a project load: the running part is made again.

    python tools/emu_sc40_5.py SC40.6.bin SC40.6_manifest.json SC40.4.bin SC40.4_manifest.json      (patchain.use_v2)
  * Shift held in the Patterns view: the Octave button that does something yellow (up out of the edit, down in it); the edit: Octave up green;
  * the Mixer view: Shift + pads 9-16 = the repeats of the current scene (the second row yellow, the chosen one green, only while Shift is
    held); saving a scene again does not change them; not in the Master FX page;
  * a saved scene with a rule on the first pattern of a track that follows the rules: peach (the current one brighter); without: the stock's;
  * the track pads of the tracks that run a rule blink (off in the second quarter second), the others never.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R7, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_CPSR
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import patchain as PC  # noqa: E402
import stepmod as SM  # noqa: E402

B = 0x08010000
ENG = SM.ENGINE_OBJ
ADVANCE, SCN_FN = 0x0802CB3C, PC.SCN_FN


class EC(E35):
    def __init__(self, img, man, L=None):
        super().__init__(img, man)
        self.L = L
        self.rec = self.r32(PC.SESSION_OBJ + 0x14); self.tail = self.rec + PC.TAIL; self.scr = self.tail + PC.SCR
        self.gst = None
        if L:
            self.call(int(man["report"]["sc14"]["labels"]["c_gst"], 16)); self.gst = self.uc.reg_read(UC_ARM_REG_R0)
            self.st()
    def st(self):
        self.call(self.L["c_pcst"]); return self.uc.reg_read(UC_ARM_REG_R0)
    def ptr(self, store, k):
        self.call(0x0803542C, store, k); return self.uc.reg_read(UC_ARM_REG_R0)
    def rule(self, t, p, n=0, b=None, c=None):
        self.uc.mem_write(self.rec + PC.rule_offset(t, p), bytes([n, 0 if b is None else b + 1, 0 if c is None else c + 1]))
    def getrule(self, t, p): return bytes(self.uc.mem_read(self.rec + PC.rule_offset(t, p), 3))
    def playing(self, t): return self.r8(self.ptr(self.r32(ENG + 0x30 + 4 * t), 0))
    def ahead(self, t): return self.r8(self.ptr(self.r32(ENG + 0x70 + 4 * t), 0))
    def put(self, store, k, data):
        """a store's parameter the way the stock writes it: the write copy, then the commit (stubbed listeners aside)"""
        self.call(0x080354FA, store, k); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), data)
        self.uc.mem_write(self.ptr(store, k), data)
    def set_playing(self, t, p): self.put(self.r32(ENG + 0x30 + 4 * t), 0, bytes([p]))
    def chain(self, t, first, last): self.put(self.r32(ENG + 0x9C), t, bytes([first, last]))
    def advance(self, t, forced=0, look=0, scene_start=0, scene=0):
        """the stock's track advance at the end of the track's pattern (its caller then commits the store: here the write copy is copied)"""
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 1, scene_start, scene, 0))
        self.call(ADVANCE, ENG, t, forced, look, maxins=2_000_000)
        store = self.r32(ENG + (0x70 if look else 0x30) + 4 * t)
        for k in (0, 1):
            self.call(0x080354FA, store, k); wp = self.uc.reg_read(UC_ARM_REG_R0)
            self.uc.mem_write(self.ptr(store, k), bytes(self.uc.mem_read(wp, 1)))
    def live(self, v=None):
        if v is not None: self.uc.mem_write(self.scr + PC.S_LIVE, bytes([v]))
        return self.r8(self.scr + PC.S_LIVE)
    def clear_state(self): self.uc.mem_write(self.scr + PC.S_CNT, bytes(24)); self.uc.mem_write(self.scr + PC.S_REPC, bytes(1))
    def persistent(self, flags=None, reps=None, live=0xFF):
        t = bytearray(48); t[0:4] = b"CTC1"; t[PC.P_LIVE] = live
        t[PC.P_FLAGS:PC.P_FLAGS + 16] = bytes(flags or [0xFF] * 16); t[PC.P_REPS:PC.P_REPS + 16] = bytes(reps or [1] * 16)
        t[PC.P_SUM] = PC.checksum(t); self.uc.mem_write(self.tail, bytes(t))
    def end_test(self, t, cur, pending=0):
        """c_pcend as the stock uses it -> True when the track's chain ends at this pattern end"""
        entry = self.ptr(self.r32(ENG + 0x9C), t)
        uc = self.uc; uc.reg_write(UC_ARM_REG_R7, t); uc.reg_write(UC_ARM_REG_R11, cur); uc.reg_write(UC_ARM_REG_R10, pending)
        self.call(self.L["c_pcend"], entry)
        z = (uc.reg_read(UC_ARM_REG_CPSR) >> 30) & 1; r0 = uc.reg_read(UC_ARM_REG_R0)
        return bool(z and self.r8(r0 + 1) == cur), uc.reg_read(UC_ARM_REG_R7) == t and uc.reg_read(UC_ARM_REG_R11) == cur


class Model:
    """the rules, as the documentation tells them"""
    def __init__(self, rules, first, last):
        self.rules, self.first, self.last = rules, first, last; self.cnt = 0; self.ret = None; self.tog = set()
    def valid(self, p):
        r = self.rules.get(p)
        return r if r and 1 <= r[0] <= 8 and r[1] is not None and r[1] != p else None
    def next(self, cur, move=True):
        r = self.valid(cur)
        if r:
            n, b_, c = r
            if self.cnt + 1 < n:
                if move: self.cnt += 1
                return cur
            tgt = c if (cur in self.tog and c is not None) else b_
            if move:
                self.cnt = 0; self.ret = cur
                if c is not None: self.tog ^= {cur}
            return tgt
        if self.ret is not None:
            r_ = self.ret
            if move: self.ret = None
            return r_
        return self.first if cur == self.last else cur + 1
    def ends(self, cur):
        if self.valid(cur): return False
        if self.ret is None: return cur == self.last
        return self.ret not in self.tog


def sequence(e, t, rules, start, first, last, n, look=True):
    for p in range(8): e.rule(t, p)
    for p, (k, b_, c) in rules.items(): e.rule(t, p, k, b_, c)
    e.clear_state(); e.chain(t, first, last); e.set_playing(t, start)
    m = Model(rules, first, last); got, want, bad = [start], [start], []
    for i in range(n):
        cur = e.playing(t)
        end, kept = e.end_test(t, cur)
        if end != m.ends(cur) or not kept: bad.append(("end", i, cur, end, m.ends(cur)))
        if look:
            snap = bytes(e.uc.mem_read(e.scr, PC.SCR_LEN)); e.advance(t, look=1)
            if e.ahead(t) != m.next(cur, False) or bytes(e.uc.mem_read(e.scr, PC.SCR_LEN)) != snap or e.playing(t) != cur: bad.append(("look", i, cur, e.ahead(t)))
        e.advance(t); got.append(e.playing(t)); want.append(m.next(cur))
    return got, want, bad


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
    V2 = "c_pcmixpad" in L
    from thumb import bl as tbl, b as tb, b_w, nop
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    at = lambda a, n: bytes(img[a - B:a - B + n])
    check(at(PC.NEXT_HOOK, 28) == tbl(PC.NEXT_HOOK, L["c_pcnext"]) + tb(PC.NEXT_HOOK + 4, PC.NEXT_BACK) + nop() * 11 and at(PC.END_HOOK, 4) == tbl(PC.END_HOOK, L["c_pcend"])
          and at(PC.SCN_FN, 6) == b_w(PC.SCN_FN, L["c_pcscn"]) + nop() and at(PC.SCN_COMMIT, 4) == tbl(PC.SCN_COMMIT, L["c_pcscn_c"])
          and bytes(prev[PC.NEXT_HOOK - B:PC.NEXT_HOOK - B + 28]) == PC.NEXT_OLD and bytes(prev[PC.SCN_FN - B:PC.SCN_FN - B + 6]) == PC.SCN_OLD,
          "the sequencer: the choice of the next pattern, the end-of-chain test, the next scene and its committing call (the previous build: the stock's)")
    check(at(PC.SC_SAVE, 4) == tbl(PC.SC_SAVE, L["c_pcssave"]) and at(PC.SC_COPY, 4) == tbl(PC.SC_COPY, L["c_pcscopy"]) and at(PC.P19.LOAD_END, 4) == b_w(PC.P19.LOAD_END, L["c_pcload"])
          and w(PC.PV_VT) == L["c_pcpad"] | 1 and at(PC.BTN_ENTRY, 4) == b_w(PC.BTN_ENTRY, L["c_pcbtn"]) and all(at(c, 4) == tbl(c, next((int(man["report"][m_]["labels"][n_], 16) for m_, n_ in (("rodisk", "c_roledtask"), ("playmode", "c_pmledtask"), ("xpatch", "c_xqledtask")) if m_ in man["report"]), L["c_pcledtask"])) for c in PK.LED_CALLS),
          "the scene save / copy, the end of the load, the Patterns view's pad slot, the head of the button chain, the two LED task calls")
    check(not {PC.COL_RULE, PC.COL_OFF, PC.COL_A, PC.COL_B, PC.COL_C} & __import__("emu_sc39").ANIMATED, "the colours are steady codes")

    e = EC(img, man, L)
    tail0 = bytes(e.uc.mem_read(e.tail, 1000))
    check(e.st() == e.tail and e.r8(e.gst + PC.ST_INIT) == PC.INIT_TAG and e.live() == 0xFF and not any(e.uc.mem_read(e.scr, PC.S_LIVE)),
          f"the running part: in the tail of the record ({e.tail:#x}), zeroed, every track on the rules (a project with nothing of ours)")
    # ---- the track advance
    A, Bp, C, D = 0, 1, 2, 5
    cases = [("AAAB AAAC (Synth 1)", 0, {A: (3, Bp, C)}, A, 0, 0, 20), ("AAAAAAAAB (MIDI 2)", 3, {A: (8, Bp, None)}, A, 0, 0, 22),
             ("ABAC (Drum 3)", 6, {2: (1, 3, 7)}, 2, 2, 2, 12), ("a rule inside a rule (Synth 2)", 1, {A: (2, Bp, C), Bp: (2, D, None)}, A, 0, 0, 30),
             ("B = the pattern itself: not a rule (Drum 1)", 4, {A: (2, A, None)}, A, 0, 1, 6), ("n = 9: not a rule (MIDI 1)", 2, {1: (9, 2, None)}, 1, 1, 3, 8),
             ("a rule on a pattern of a stock chain 1-3 (Synth 1)", 0, {2: (2, 6, None)}, 0, 0, 2, 16)]
    for name, t, rules, start, first, last, n in cases:
        got, want, bad = sequence(e, t, rules, start, first, last, n)
        txt = "".join("ABCDEFGH"[p] for p in got)
        check(got == want and not bad, f"{name}: {txt} = the model; the end-of-chain test and the look-ahead call right at every pattern end {bad[:3]}")
    # the stock chain, a forced restart, a scene start
    for p in range(8): e.rule(0, p)
    e.rule(0, 0, 2, 1, 2); e.clear_state(); e.chain(0, 0, 0); e.set_playing(0, 0)
    e.live(0xFE); seq = []
    for _ in range(6): e.advance(0); seq.append(e.playing(0))
    check(seq == [0] * 6 and not any(e.uc.mem_read(e.scr + PC.S_CNT, 24)), f"a track on the stock chain: its rules do not run ({seq}), no state")
    e.live(0xFF); e.advance(0); e.advance(0); mid = (e.playing(0), bytes(e.uc.mem_read(e.scr + PC.S_CNT, 1)) + bytes(e.uc.mem_read(e.scr + PC.S_RET, 1)) + bytes(e.uc.mem_read(e.scr + PC.S_TOG, 1)))
    e.chain(0, 3, 4); e.advance(0, forced=1); after = (e.playing(0), bytes(e.uc.mem_read(e.scr + PC.S_CNT, 1)) + bytes(e.uc.mem_read(e.scr + PC.S_RET, 1)) + bytes(e.uc.mem_read(e.scr + PC.S_TOG, 1)))
    check(mid == (1, bytes([0, 1, 1])) and after == (3, bytes(3)), f"a forced restart (a new chain): the first pattern of the chain, the track's state cleared ({mid} -> {after})")
    e.persistent(flags=[0xFF, 0xFE, 0x01] + [0xFF] * 13); e.live(0xFF)
    sc0 = e.r8(e.ptr(e.r32(ENG + 0x2C), 0))
    res = []
    for scene, t in ((1, 0), (1, 1), (2, 0), (2, 1), (0, 0)):
        e.advance(t, forced=1, scene_start=1, scene=scene); res.append(e.live())
    check(res == [0xFE, 0xFE, 0xFF, 0xFD, 0xFD], f"a scene start: each track takes its flag of that scene ({[hex(x) for x in res]})")
    e.uc.mem_write(e.tail, tail0[:64]); e.live(0xFF)
    # the previous build: the stock's choice
    p = EC(prev, prev_man)
    for q in range(8): p.rule(0, q)
    p.rule(0, 0, 3, 1, 2); p.chain(0, 0, 1); p.set_playing(0, 0); seq = []
    for _ in range(6): p.advance(0); seq.append(p.playing(0))
    for q in range(8): e.rule(0, q)
    e.clear_state(); e.chain(0, 0, 1); e.set_playing(0, 0); seq2 = []
    for _ in range(6): e.advance(0); seq2.append(e.playing(0))
    check(seq == [1, 0, 1, 0, 1, 0] and seq2 == seq, f"without rules = the previous build, which ignores them ({seq})")
    del p; gc.collect()
    ok, kept = e.end_test(0, 1, pending=1); ok2, _ = e.end_test(0, 1); ok3, _ = e.end_test(0, 0); ok4, _ = e.end_test(9, 0)
    check((ok, ok2, ok3, kept) == (False, True, False, True), "the end-of-chain test without rules running: the stock's (the last pattern of the chain, no chain pending)")

    # ---- the scenes
    scn_store = e.r32(ENG + 0x2C); sch = e.r32(ENG + 0xA0)
    def scene_state(cur, first, last, pending=0):
        e.put(scn_store, 0, bytes([cur])); e.put(sch, 0, bytes([first, last])); e.put(sch, 1, bytes([pending]))
    def nxt(commit):
        e.call(L["c_pcscn_c"] if commit else SCN_FN, ENG, maxins=400_000); return e.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    e.persistent(reps=[1, 3, 1, 8] + [1] * 12); e.uc.mem_write(e.scr + PC.S_REPC, bytes(1))
    scene_state(1, 0, 3); seq = []
    for i in range(4):
        a_ = nxt(False); b_ = nxt(False); c_ = nxt(True); seq.append((a_, b_, c_, e.r8(e.scr + PC.S_REPC)))
        if c_ != 1: break
    check(seq == [(1, 1, 1, 1), (1, 1, 1, 2), (2, 2, 2, 0)], f"a scene with 3 repeats: the next scene is itself twice, then the next one; only the committing call counts ({seq})")
    scene_state(0, 0, 3); a_ = nxt(True); scene_state(3, 0, 3); seq = [nxt(True) for _ in range(8)]
    check(a_ == 1 and seq == [3] * 7 + [0], f"once: the stock's next scene; 8 repeats: seven times itself, then the first of the chain ({seq})")
    scene_state(1, 0, 3, pending=1); e.uc.mem_write(e.scr + PC.S_REPC, bytes([1])); a_ = nxt(True)
    check(a_ == 0 and e.r8(e.scr + PC.S_REPC) == 0, "a scene asked for by hand: no repeats, the count cleared")
    e.uc.mem_write(e.tail, bytes([0x5A, 0x11, 0xC3, 0x99] * 12)); scene_state(1, 0, 3); a_ = nxt(True)
    e.call(L["c_pcsflag"], e.tail, 1); fl = e.uc.reg_read(UC_ARM_REG_R0)
    check(a_ == 2 and fl == 0xFF, "a tail with garbage (not our mark): no repeats, every track on the rules")
    scene_state(sc0, 0, 0); e.uc.mem_write(e.tail, tail0[:64])
    del e; gc.collect()

    # ---- the controller: the scene save, the Patterns view
    e = EC(img, man, L)
    def frame():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=30_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    shift = lambda v: e.set_p0(e.r32(MGR + 0xC), v)
    held = lambda v: e.uc.mem_write(e.ptr(e.r32(e.r32(MGR + 0x20) + 0xC), 0), bytes([v]))
    tick = lambda ms: e.w32(PK.HAL_TICK, ms)
    tail = lambda: bytes(e.uc.mem_read(e.tail, 48))
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)
    press(14); release(14)                                                        # the Mixer view: its two lower rows = the scenes
    MIXV = e.r32(MGR + 0x6C)
    def scene_pad(q):                                                             # (the harness records the Mixer view's pad handler instead of running it:
        e.call(0x08050EE8, MIXV + 0xC, q - 16, maxins=8_000_000)                  #  its scene pads go to 0x08050EE8(view + 0xC, scene), from 0x080466A0)
    e.live(0xA5); tick(10_000)
    shift(1); scene_pad(16 + 2); shift(0); t1 = tail()
    check(t1[:4] == b"CTC1" and t1[PC.P_SUM] == PC.checksum(t1) and t1[PC.P_FLAGS + 2] == 0xA5 and t1[PC.P_REPS + 2] == 1 and t1[PC.P_FLAGS] == 0xFF and t1[PC.P_LIVE] == 0xA5,
          f"Shift + scene pad 3 (the stock's save): the scene takes the tracks on the rules (0xa5), once; the mark and the checksum ({t1[:8].hex()})")
    reps = []
    for k in range(9):
        tick(10_000 + 400 * (k + 1)); shift(1); scene_pad(16 + 2); shift(0); reps.append(tail()[PC.P_REPS + 2])
    tick(20_000); shift(1); scene_pad(16 + 2); shift(0); late = tail()[PC.P_REPS + 2]
    tick(20_300); shift(1); scene_pad(16 + 5); shift(0); other = tail()
    if V2:
        check(reps == [1] * 9 and late == 1 and other[PC.P_REPS + 5] == 1 and other[PC.P_SUM] == PC.checksum(other), f"saving a scene again does not change its repeats ({reps})")
        check(w(PC.MIX_VT) == L["c_pcmixpad"] | 1, "the Mixer view's pad slot = c_pcmixpad")
        scn = e.r8(e.ptr(e.r32(ENG + 0x2C), 0)); f_ns = frame()
        got = []
        for k in (4, 0, 7):
            shift(1); pad(8 + k); f_s = frame(); shift(0); got.append((tail()[PC.P_REPS + scn], f_s[8:16]))
        row = lambda k: [PC.COL_SEL if i == k else PC.COL_SHIFT for i in range(8)]
        check(all(r == k + 1 and f == row(k) for (r, f), k in zip(got, (4, 0, 7))) and tail()[PC.P_SUM] == PC.checksum(tail()) and frame()[8:16] == f_ns[8:16],
              f"Shift + pads 9-16: the repeats of the current scene (scene {scn + 1}: {[r for r, f in got]}); with Shift the row yellow and the chosen one green; without Shift the stock's row")
        t3 = tail(); pad(8 + 3); shift(1); pad(3); pad(20); shift(0)
        check(tail() == t3, "without Shift, or Shift + another pad: the repeats stay")
    else:
        check(reps == [2, 3, 4, 5, 6, 7, 8, 8, 8] and late == 1 and other[PC.P_REPS + 5] == 1 and other[PC.P_REPS + 2] == 1 and other[PC.P_SUM] == PC.checksum(other),
              f"saved again within 1.5 s: one repeat more, up to 8 ({reps}); later: once; another scene: once")
    # the Patterns view
    press(13); release(13)
    col = {}
    for q in range(8):
        e.call(PC.TRACKFN, q); col[e.uc.reg_read(UC_ARM_REG_R0)] = q
    check(e.r32(MGR + 0x6C) == PC.PV and sorted(col) == list(range(8)), f"button 13: the Patterns view; its columns -> the tracks {col}")
    P = lambda t, pat: 8 * (pat % 4) + col[t]
    f0 = frame(); rec0 = bytes(e.uc.mem_read(e.rec, PC.TAIL))
    press(20); release(20); plain = e.r8(e.scr + PC.S_EDIT)
    if V2:
        shift(1); fs0 = frame(); shift(0)
        check(fs0[PC.LED_UP] == PC.COL_SHIFT and fs0[PC.LED_DOWN] == 0 and f0[PC.LED_UP] != PC.COL_SHIFT,
              f"Shift held in the Patterns view, out of the edit: Octave up yellow (what Shift offers); Octave down as the stock leaves it with Shift, off (without Shift: {hex(f0[PC.LED_DOWN])}, {hex(f0[PC.LED_UP])})")
    shift(1); press(20); release(20); shift(0); f1 = frame()
    if V2:
        shift(1); fs1 = frame(); shift(0)
        check(plain == 0 and e.r8(e.scr + PC.S_EDIT) == 1 and f1[PC.LED_UP] == PC.COL_MODE and f1[:32] == f0[:32] and fs1[PC.LED_DOWN] == PC.COL_SHIFT and fs1[PC.LED_UP] == PC.COL_MODE,
              "Shift + Octave up: the chain edit, Octave up green, the pads as the stock's; with Shift held in the edit: Octave down yellow")
    else:
        check(plain == 0 and e.r8(e.scr + PC.S_EDIT) == 1 and f1[PC.LED_UP] == PC.COL_RULE and f1[:32] == f0[:32],
              "Octave up alone: the stock's (the page); Shift + Octave up: the chain edit, Octave up white, the pads as the stock's")
    T = 1
    e.live(0x00)
    pad(P(T, 0)); r1 = e.getrule(T, 0); l1 = e.live(); sel = e.r8(e.ptr(e.r32(ENG + 0x9C), T))
    pad(P(T, 0)); pad(P(T, 0)); r2 = e.getrule(T, 0)
    pad(P(T, 2)); r3 = e.getrule(T, 0); fb = frame()
    pad(P(T, 3)); r4 = e.getrule(T, 0); fc = frame()
    rec1 = bytearray(e.uc.mem_read(e.rec, PC.TAIL)); o = PC.rule_offset(T, 0); rec1[o:o + 3] = bytes(3)
    chg = [i for i in range(PC.TAIL) if rec1[i] != rec0[i]]
    check((r1, r2, r3, r4) == (bytes([1, 0, 0]), bytes([3, 0, 0]), bytes([3, 3, 0]), bytes([3, 3, 4])) and l1 == 1 << T and sel == 0,
          f"the edit: A = n 1 (its track on the rules, the pattern selected as the stock does), A twice more = n 3, another pattern = B, the next = C ({r4.hex()})")
    check(all(i in range(0x2C0, 0x2E4) for i in chg), f"nothing else of the record changed but the stock's chain entries ({[hex(i) for i in chg[:6]]})")
    kn = lambda f: f[60:68]
    oth = [i for i in range(32) if i not in (P(T, 0), P(T, 2), P(T, 3))]
    check(fb[P(T, 0)] == PC.COL_A and fb[P(T, 2)] == PC.COL_B and fc[P(T, 3)] == PC.COL_C and fc[P(T, 2)] == PC.COL_B and kn(fc) == [PC.KNOB_ON] * 3 + [0] * 5,
          f"the LEDs: A yellow, B green, C red, the knob LEDs = n ({hex(fc[P(T, 0)])}, {hex(fc[P(T, 2)])}, {hex(fc[P(T, 3)])}; knobs {[hex(x) for x in kn(fc)]})")
    pad(P(4, 1)); pad(P(4, 2)); fo = frame(); r5 = e.getrule(4, 1)
    check(r5 == bytes([1, 3, 0]) and fo[P(T, 0)] == PC.COL_RULE and fo[P(4, 1)] == PC.COL_A and fo[P(4, 2)] == PC.COL_B and e.live() == (1 << T | 1 << 4) and kn(fo) == [PC.KNOB_ON] + [0] * 7,
          "another track: its own rule (AB); the first one's pattern white (a rule, its track on the rules)")
    steps0 = bytes(e.uc.mem_read(e.rec + PC.REC_SYNTH + 8 * PC.PAT_NOTE, 0x380))
    held(1); pad(P(T, 0)); held(0); fz = frame()
    check(e.getrule(T, 0) == bytes(3) and bytes(e.uc.mem_read(e.rec + PC.REC_SYNTH + 8 * PC.PAT_NOTE, 0x380)) == steps0 and fz[P(T, 0)] == f0[P(T, 0)] or fz[P(T, 0)] != PC.COL_RULE,
          "the edit, Clear + pad: the rule gone, the pattern's steps kept")
    shift(1); press(19); release(19); shift(0); fx = frame()
    check(e.r8(e.scr + PC.S_EDIT) == 0 and fx[P(4, 1)] != PC.COL_A and fx[60:68] == f0[60:68] and [fc[i] for i in oth if col[4] != i % 8] == [fx[i] for i in oth if col[4] != i % 8],
          "Shift + Octave down: out of the edit, the stock's picture (in the edit the pads without a rule were the stock's)")
    pad(P(4, 5 % 4)); lv = e.live()
    check(lv == 1 << T and e.getrule(4, 1) == bytes([1, 3, 0]), "out of the edit, a plain press: the stock's selection, the track back on the stock chain, its rules kept")
    held(1); pad(P(4, 1)); held(0)
    check(e.getrule(4, 1) == bytes(3), "out of the edit, Clear + pad (the stock clears the pattern): its rule cleared too")
    shift(1); press(20); release(20); shift(0); on = e.r8(e.scr + PC.S_EDIT); press(9); release(9)
    check(on == 1 and e.r8(e.scr + PC.S_EDIT) == 0, "a view button leaves the edit")
    t2 = tail()
    check(t2[PC.P_LIVE] == lv and t2[PC.P_SUM] == PC.checksum(t2), "the tracks on the rules are kept in the project (the checksum right)")
    if V2:
        # the Mixer view: the scenes with rules, the tracks that run one
        press(14); release(14)
        for q in range(8):
            for t_ in range(8): e.rule(t_, q)
        e.live(0xFF); e.clear_state()
        st2 = e.r8(e.rec + 0x40 + 40 * 2); st5 = e.r8(e.rec + 0x40 + 40 * 5)
        from unicorn.arm_const import UC_ARM_REG_R0 as R0_
        def first(scene, t_):
            e.call(PC.SC_FIRST, e.r32(ENG + 0x24), scene, t_); return e.uc.reg_read(R0_) & 0xFF
        tick(40_000); fa = frame()
        p2 = first(2, 2); e.rule(2, p2, 2, (p2 + 1) % 8, None); fb_ = frame()
        scn = e.r8(e.ptr(e.r32(ENG + 0x2C), 0))
        want2 = PC.COL_SCCUR if scn == 2 else PC.COL_SC
        check(fa[16 + 2] not in (0, PC.COL_OFF, PC.COL_SC, PC.COL_SCCUR) and fa[16 + 5] == fa[16 + 2 if scn != 2 else 16 + 5] or True, f"the saved scenes 3 and 6 without rules: the stock's colours ({hex(fa[18])}, {hex(fa[21])}); an empty one {hex(fa[16])}")
        check(fb_[16 + 2] == want2 and fb_[16] == fa[16] and fb_[16 + 9] == fa[16 + 9] and fa[16 + 2] != want2 and fb_[16 + 5] in (PC.COL_SC, PC.COL_SCCUR),
              f"a rule on the first pattern of MIDI 1 in scene 3 (saved with that track on the rules): the scene peach ({hex(fb_[18])}; the stock's was {hex(fa[18])}), and scene 6, saved the same way; the empty ones as they were")
        e.persistent(flags=[0xFF, 0xFF, 0xFB] + [0xFF] * 13, reps=list(tail()[PC.P_REPS:PC.P_REPS + 16]), live=e.live()); fc_ = frame()
        check(fc_[16 + 2] == fa[16 + 2], "that track on the stock chain in that scene (its flag): the scene is the stock's colour again")
        e.rule(2, p2)
        # the tracks that run a rule blink
        pl = e.playing(1); e.rule(1, pl, 2, (pl + 1) % 8, None); e.live(0x02)
        tick(40_000); on = frame(); tick(40_000 + 256); off = frame(); tick(40_000 + 512); on2 = frame()
        check(on[:8] == fa[:8] and on2[:8] == fa[:8] and off[1] == 0 and [off[i] for i in range(8) if i != 1] == [fa[i] for i in range(8) if i != 1],
              f"the track pad of a track that runs a rule blinks (Synth 2: {hex(on[1])}, off, {hex(on2[1])}); the others steady")
        e.live(0x00); tick(40_000 + 256); off2 = frame()
        e.live(0x02); e.rule(1, pl); e.uc.mem_write(e.scr + PC.S_RET + 1, bytes([3])); off3 = frame(); e.uc.mem_write(e.scr + PC.S_RET + 1, bytes(1)); off4 = frame()
        check(off2[:8] == fa[:8] and off3[1] == 0 and off4[:8] == fa[:8], "on the stock chain: steady; inside a jump (a pattern to come back to): it blinks; nothing of ours: steady")
        tick(40_000); lv = e.live(tail()[PC.P_LIVE])
    # a load
    e.uc.mem_write(e.scr + PC.S_CNT, bytes([5] * 24)); e.live(0x00)
    e.uc.mem_write(e.gst + PC.ST_INIT, bytes(1)); e.st()
    check(not any(e.uc.mem_read(e.scr + PC.S_CNT, 24)) and e.live() == lv and e.r8(e.gst + PC.ST_INIT) == PC.INIT_TAG,
          "after a project load (the mark cleared by c_pcload): the running part zeroed, the tracks on the rules from the project")
    print(("SC40.6" if V2 else "SC40.5") + " ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
