"""SC40.3 ARM tests (live RAM dump, the real routes): the two modes of the probability view (tools/stepmod.py).

    python tools/emu_sc40_3.py SC40.3.bin SC40.3_manifest.json SC40.2.bin SC40.2_manifest.json
    python tools/emu_sc40_3.py SC40.4.bin SC40.4_manifest.json SC40.2.bin SC40.2_manifest.json      (the frequency by the plays of each pattern:
        the 32 counters of 10 bits, the mask builder by them, the track advance 0x0802CB3C counts a pass that ends, cleared while stopped)
  * the hooks: the mask builder's tests (0x08040D8A) -> c_rfmask, the player's loads -> c_rfnote, the probability view's slots 0 / 7 / 8 and
    thunk, the Pattern Settings view's slots 0 / 7, the LED task calls;
  * the views through the controller (Synth 1): Pattern Settings: pad 25 peach; Pattern Settings twice, a step held: mode 1: row 3 the stock's,
    row 4 the frequency (the step's byte [3] bits 0-2, a yellow bar), bytes [1] / [2] untouched; a third press: Pattern Settings (the stock's);
    pad 25 there: the probability view in mode 2: row 3 = the dynamics (byte [3] bits 4-6, the chosen pad green), row 4 = the mutate level
    (byte [2], peach); a step without notes: nothing written; Pattern Settings twice again: mode 1; a drum track: pad 25 off and without effect;
  * the mask builder 0x08040D4C itself (Synth 1's player): byte [3] = 0: the stock's mask for every probability / random word / micro step (= the
    previous build); the frequency = the model over several passes, lengths and sync rates (the last pass of each n; the tick store at 0 = Play);
    the position: the unit starts in exactly one micro step of its step, the model's; recording with mode 2 on the screen: the new micro step
    written into the unit and no second start; otherwise the step untouched;
  * the player 0x08040E5A: the velocity and the length given to the note-on = those of a step that holds the model's values; a tied unit keeps
    its length; recording with mode 2 on the screen: note, velocity and length written; recording without it: nothing written (the mutated note
    neither).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT, MASKS  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import emu_sc39 as T39  # noqa: E402
import mutate39 as MU  # noqa: E402
import stepmod as SM  # noqa: E402

B = 0x08010000
PLAYER, STEP0, STEP1 = T39.PLAYER, T39.STEP0, T39.STEP1
BUILD, PLAY, NOTE_ON = 0x08040D4C, 0x08040E5A, 0x08040FA2


def view_run(img, man, new):
    e = E35(img, man)
    def frame():
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))[16:]
    def ledtask():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=20_000_000)
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda p: (e.call(PRESS, MGR, p, 100, maxins=8_000_000), e.call(RELEASE, MGR, p, maxins=8_000_000))
    step = lambda a: bytes(e.uc.mem_read(a, 4))
    sub = lambda: e.r8(MGR + 0x152)
    out = {}
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)                        # Synth 1
    press(12); release(12); out["sub1"] = sub(); out["ps"] = frame()
    press(12); release(12); out["sub2"] = sub(); out["open"] = frame()
    e.call(PRESS, MGR, 0, 100, maxins=8_000_000)                                  # step 1 held
    out["freq"] = []
    for k in (3, 7, 0, 5):
        pad(24 + k); out["freq"].append((k, step(STEP0), frame()))
    pad(16 + 2); out["prob"] = (step(STEP0), frame())
    e.call(RELEASE, MGR, 0, maxins=8_000_000)
    press(12); release(12); out["sub3"] = sub()                                     # a third press: Pattern Settings
    if new:
        for _ in range(4): ledtask()
    pad(24); out["sub3b"] = sub(); out["mode2"] = frame()                           # pad 25 there
    if new:
        e.call(PRESS, MGR, 0, 100, maxins=8_000_000)
        out["dyn"] = []
        for k in (4, 7, 1, 0, 6):
            pad(16 + k); out["dyn"].append((k, step(STEP0), frame()))
        out["mut"] = []
        for k in (3, 0, 6):
            pad(24 + k); out["mut"].append((k, step(STEP0), frame()))
        e.call(RELEASE, MGR, 0, maxins=8_000_000)
        e.call(PRESS, MGR, 1, 100, maxins=8_000_000)                              # step 2 (no notes)
        pad(16 + 4); pad(24 + 4); out["empty"] = (step(STEP1), frame())
        e.call(RELEASE, MGR, 1, maxins=8_000_000)
        press(12); release(12); out["sub4"] = sub()                                 # Pattern Settings
        for _ in range(4): ledtask()
        press(12); release(12); out["sub5"] = sub()
        e.call(PRESS, MGR, 0, 100, maxins=8_000_000); out["again"] = frame(); pad(24 + 2); out["again_step"] = step(STEP0); e.call(RELEASE, MGR, 0, maxins=8_000_000)
        press(12); release(12)
        e.set_p0(e.r32(CONT + 0x188), 4); press(4); release(4)                      # Drum 1
        press(12); release(12); out["dsub"] = sub(); out["dps"] = frame(); pad(24); out["dsub2"] = sub()
    del e; gc.collect()
    return out


class EM(T39.EP):
    """Synth 1's player: the mask builder and the player, the note-on watched with its length"""
    def __init__(self, img, man, L=None):
        super().__init__(img, man)
        self.args = []
        def on(uc, a, s, d): self.args.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)))
        self.uc.hook_add(UC_HOOK_CODE, on, begin=NOTE_ON, end=NOTE_ON)
        self.L = L
        self.st = None
        if L:
            self.call(L["c_rfst"]); self.st = self.uc.reg_read(UC_ARM_REG_R0)
        self.snap = bytes(self.uc.mem_read(PLAYER, 0x200))

    def ptr(self, store, k):
        self.call(0x0803542C, store, k); return self.uc.reg_read(UC_ARM_REG_R0)

    def setup(self, first=0, last=15, rate=None, tick=0, T=0):
        s = self.r32(PLAYER + 0x10); self.uc.mem_write(self.ptr(s, 0), bytes([first, last]))
        if rate is not None: self.uc.mem_write(self.ptr(s, 1), bytes([rate]))
        self.w32(self.ptr(self.r32(PLAYER + 8), 2), tick)
        self.w32(self.ptr(self.r32(SM.ENGINE + 0x90), 0), T)
        return self.r8(self.ptr(s, 1))

    def screen(self, mode2):
        if self.st: self.uc.mem_write(self.st + 1, bytes([0x31 if mode2 else 0]))

    def build(self, micro, word, keep=False):
        """the mask builder for one micro step of step 1 -> the mask"""
        self.uc.mem_write(PLAYER, self.snap); self.w32(PLAYER + 4, word)
        self.uc.mem_write(0x2006F000, bytes(4))                                    # (the fifth argument: 0)
        self.call(BUILD, PLAYER, 0, 0, micro, maxins=400_000)
        w = self.r32(PLAYER + 4)
        if keep: self.kept = w
        return self.r8(PLAYER + 0x13C + micro)

    def note(self, rnd):
        self.uc.mem_write(PLAYER, self.snap); self.uc.mem_write(PLAYER + 0x13C, bytes([1]))
        self.rnd = rnd; self.ons.clear(); self.args.clear(); self.rcalls = 0
        self.call(PLAY, PLAYER, 0, 0, 0, maxins=400_000)
        return list(self.args)


def counter_tests(e, img, L, put, check):
    """SC40.4: the frequency by the plays of each pattern (stepmod.use_passcount)"""
    f0 = [0]
    def chk(c, m):
        check(c, m); f0[0] += 0
    from thumb import bl as tbl
    check(bytes(img[SM.PASS_HOOK - B:SM.PASS_HOOK - B + 4]) == tbl(SM.PASS_HOOK, L["c_rfpass"]), "the track advance's load at 0x0802CD42 = bl c_rfpass")
    get = lambda i: (e.call(L["c_rfcget"], i), e.uc.reg_read(UC_ARM_REG_R0))[1]
    inc = lambda i: e.call(L["c_rfcinc"], i)
    st = e.st
    area = lambda: bytes(e.uc.mem_read(st - 6, 46))
    e.call(L["c_rfclr"], st)
    # the counters: 10 bits each, apart
    bad = []
    for i in (0, 3, 19, 20, 31):
        for k in range(1, 843):
            inc(i); g = get(i)
            if g != k % SM.CNT_MAX: bad.append((i, k, g)); break
        others = [get(j) for j in range(32) if j != i]
        if any(others): bad.append((i, "others", others))
        e.call(L["c_rfclr"], st)
    a0 = area()
    check(not bad and a0[6] == SM.MAGIC and a0[4:6] == bytes(e.uc.mem_read(st - 2, 2)), f"the 32 counters: 0..839 and around, each one apart (counters 0, 3, 19, 20, 31) {bad[:3]}")
    for i in range(32):
        for _ in range(i + 1): inc(i)
    check([get(i) for i in range(32)] == list(range(1, 33)) and e.r8(st + 1) & SM.ST_COUNTS, "the 32 counters hold 32 different counts; the state's bit 3 set")
    # the frequency: the mask builder, Synth 1 (track 0), its playing pattern
    e.call(L["c_rfclr"], st); e.setup()
    s0 = e.r32(PLAYER + 8); pat = e.r8(e.ptr(s0, 0))
    bad, n = [], 0
    for N in range(1, 9):
        e.call(L["c_rfclr"], st); put(e, 7, N - 1, 0)
        for k in range(0, 3 * N + 2):
            for T in (0, 5000):
                e.setup(T=T); got = e.build(0, 0); n += 1
                if got != (1 if k % N == N - 1 else 0): bad.append((N, k, T, got))
            inc(pat)
    check(not bad, f"the frequency by the plays of the pattern (pattern {pat + 1} of Synth 1): {n} masks, the step starts in play n, 2n, 3n... whatever the time since Play {bad[:4]}")
    e.call(L["c_rfclr"], st); put(e, 7, 1, 0)
    for j in range(32):
        if j != pat: inc(j)
    a_ = e.build(0, 0); inc(pat); b_ = e.build(0, 0)
    check(a_ == 0 and b_ == 1, "the plays of the other patterns and tracks do not count for it")
    # the track advance 0x0802CB3C: a pass that ends = one more play
    def advance(track, end, scene, nxt):
        e.uc.mem_write(0x2006F000, struct.pack("<4I", end, scene, 0, 0))
        e.call(0x0802CB3C, SM.ENGINE_OBJ, track, 0, nxt, maxins=2_000_000)
    e.call(L["c_rfclr"], st)
    pats = [e.r8(e.ptr(e.r32(SM.ENGINE_OBJ + 0x30 + 4 * t), 0)) for t in range(8)]
    res = {}
    advance(0, 1, 0, 0); res["end"] = get(pats[0])
    advance(0, 0, 0, 0); res["mid"] = sum(get(j) for j in range(32))
    advance(0, 1, 0, 1); res["next"] = sum(get(j) for j in range(32))
    advance(4, 1, 0, 0); res["drum"] = sum(get(j) for j in range(32))
    p2 = e.r8(e.ptr(e.r32(SM.ENGINE_OBJ + 0x30 + 8), 0)); advance(2, 0, 1, 0); res["scene"] = get(16 + p2)
    check(res == dict(end=1, mid=1, next=1, drum=1, scene=1) and e.r32(T39.PLAYER + 8) == e.r32(SM.ENGINE_OBJ + 0x30),
          f"the track advance 0x0802CB3C: a pattern of a note track that ends (or a scene change) = one more play; within the pattern, the look-ahead call and a drum track: none ({res})")
    # stopped: back to 0; the tag gone: back to 0
    for j in range(32): inc(j)
    def ledtask():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=20_000_000)
    e.transport(1, 0, 0); ledtask(); playing = sum(get(j) for j in range(32))
    e.transport(0, 0, 0); ledtask(); stopped = sum(get(j) for j in range(32))
    check(playing > 32 and stopped == 0 and not e.r8(st + 1) & SM.ST_COUNTS, f"the LED task: playing, the counts stay ({playing}); stopped, all back to 0")
    for j in range(32): inc(j)
    e.uc.mem_write(st - 6, bytes([0xA5]) * 46)
    check(sum(get(j) for j in range(32)) == 0 and e.r8(st) == SM.MAGIC, "the bytes taken by someone else (the CC editor's backup): the tag again and every count 0")
    e.transport(0, 0, 0); e.call(L["c_rfclr"], st)
    return 0



def off_model(level, nib):
    mlo, mhi, vlo, vhi = SM.DYN[level]
    return mlo + nib % (mhi - mlo + 1)


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["stepmod"]["labels"].items()}
    t0 = int(man["report"]["stepmod"]["arm_start"], 16) - B                          # the dynamics table is the first thing of the module: which one is it
    keep = SM.DYN; SM.DYN = SM.DYN2; tab2 = SM.dyn_table(); SM.DYN = keep
    if bytes(img[t0:t0 + 32]) == tab2: SM.DYN = SM.DYN2; print("(the dynamics table of SC40.7)")
    LM = {k: int(v, 16) for k, v in man["report"]["mutate39"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import bl as tbl, nop
    ledhead = next((int(man["report"][m_]["labels"][n_], 16) for m_, n_ in (("rodisk", "c_roledtask"), ("fxsess", "c_fsledtask"), ("playmode", "c_pmledtask"), ("xpatch", "c_xqledtask"), ("patchain", "c_pcledtask")) if m_ in man["report"]), L["c_rfledtask"])      # (a later build: the chain goes on)
    check(bytes(img[SM.MASK_HOOK - B:SM.MASK_BACK - B]) == tbl(SM.MASK_HOOK, L["c_rfmask"]) + nop() * 5 and bytes(prev[SM.MASK_HOOK - B:SM.MASK_BACK - B]) == SM.MASK_OLD
          and bytes(img[MU.NOTE_LOAD - B:MU.NOTE_LOAD - B + 4]) == tbl(MU.NOTE_LOAD, L["c_rfnote"]),
          "the mask builder's tests at 0x08040D8A = bl c_rfmask + nops (the previous build: the stock's); the player's loads = bl c_rfnote")
    PM_ = {k: int(x, 16) for k, x in man["report"].get("playmode", {}).get("labels", {}).items()}       # (a later build: its pads in front)
    check(w(MU.PROB_VT) == L["c_rfpad"] | 1 and w(MU.PROB_VT + 28) == L["c_rfbuf"] | 1 and w(MU.PROB_VT + 32) == L["c_rfled"] | 1 and w(MU.PROB_VT2) == L["c_rfled_t"] | 1
          and w(SM.PS_VT) == PM_.get("c_pmpspad", L["c_rfpspad"]) | 1 and w(SM.PS_VT + 28) == PM_.get("c_pmpsbuf", L["c_rfpsbuf"]) | 1 and all(bytes(img[c - B:c - B + 4]) == tbl(c, ledhead) for c in PK.LED_CALLS),
          "the probability view's slots 0 / 7 / 8 and thunk, the Pattern Settings view's slots 0 / 7, the two LED task calls")
    check(not {SM.COL_FREQ, SM.COL_DYN, SM.COL_DIM} & T39.ANIMATED, "the colours are steady codes")

    # ---- the view
    v = view_run(img, man, True)
    Y, G, D, PL, PD = SM.COL_FREQ, SM.COL_DYN, SM.COL_DIM, MU.COL_LIT, MU.COL_DIM
    stock3 = [0x6C + i for i in range(8)]
    fbar = lambda k: [Y] * (k + 1) + [D] * (7 - k)
    pbar = lambda k: [PL] * (k + 1) + [PD] * (7 - k)
    dsel = lambda k: [G if i == k else D for i in range(8)]
    check(v["sub1"] == 4 and (v["ps"][8:12] == [PL, 0, 0, 0] or (PM_ and v["ps"][8] == PL)) and len(set(v["ps"][12:])) == 2,
          f"Pattern Settings: pad 25 peach, pads 26-28 off, the direction pads as the stock ({[hex(x) for x in v['ps'][8:]]})")
    check(v["sub1"] == 4 and v["sub2"] == 5 and v["open"] == stock3 + fbar(0),
          f"Pattern Settings twice: the probability view (submodes {v['sub1']}, {v['sub2']}); row 3 the stock's, row 4 the frequency bar in yellow (always)\n    {[hex(x) for x in v['open']]}")
    check(all(s[3] == k and s[1] == 7 and s[2] == 0 and f[8:] == fbar(k) and f[:8] == stock3 for k, s, f in v["freq"]),
          f"mode 1, row 4: the frequency - 1 in the step's byte [3], the bar follows, the rest untouched ({[(k, s.hex()) for k, s, f in v['freq']]})")
    s, f = v["prob"]
    check(s[1] == 2 and s[3] == 5 and f == [0x6C, 0x6D, 0x6E, 0, 0, 0, 0, 0] + fbar(5), f"mode 1, row 3: the stock probability ({s.hex()})")
    check(v["sub3"] == 4 and v["sub3b"] == 5 and v["mode2"] == dsel(0) + pbar(0),
          f"a third press: Pattern Settings (the stock's); pad 25 there: the probability view (submode {v['sub3b']}) in mode 2: row 3 = the dynamics (none), row 4 = the mutate bar\n    {[hex(x) for x in v['mode2']]}")
    check(all(s[3] == (k << 4 | 5) and s[1] == 2 and s[2] == 0 and f == dsel(k) + pbar(0) for k, s, f in v["dyn"]),
          f"mode 2, row 3: the dynamics in bits 4-6 of byte [3], the frequency kept ({[(k, s.hex()) for k, s, f in v['dyn']]})")
    check(all(s[2] == k and s[3] == (6 << 4 | 5) and f == dsel(6) + pbar(k) for k, s, f in v["mut"]), f"mode 2, row 4: the mutate level in byte [2] ({[(k, s.hex()) for k, s, f in v['mut']]})")
    s, f = v["empty"]
    check(s[0] == 0 and s[2] == 0 and s[3] == 0 and f == [0] * 16, f"a step without notes: nothing written ({s.hex()}), the rows off")
    check(v["sub4"] == 4 and v["sub5"] == 5 and v["again"][:8] != dsel(6) and v["again"][8:] == fbar(5) and v["again_step"][3] == (6 << 4 | 2),
          f"Pattern Settings twice again: mode 1 (row 3 the stock's again, row 4 = the frequency, a pad of it writes the frequency)\n    {[hex(x) for x in v['again']]}")
    check(v["dsub"] == 9 * 4 + 4 and v["dps"][8] == 0 and v["dsub2"] == v["dsub"], f"a drum track (Drum 1, 9 x 4 + submode 4 = {v['dsub']}): pad 25 of Pattern Settings off and without effect")
    gc.collect(); vp = view_run(prev, prev_man, False)
    check(vp["ps"][8] == 0 and vp["sub3b"] == 4 and all(s[3] == 0 for k, s, f in vp["freq"]), "the previous build: pad 25 of Pattern Settings off and without effect, byte [3] never written")
    del vp; gc.collect()

    # ---- the mask builder
    e = EM(img, man, L); p = EM(prev, prev_man)
    rate0 = e.setup()
    step = e.step; m0 = step[6]
    words = [0, 0x3FFFFFFF, 0x12345678 & 0x3FFFFFFF, 0x0BADF00D, 0x2AAAAAAA, 0x15555555, 0x00F0F0F0, 0x1F3, 0x7C5, 0x93C467 & 0x3FFFFFFF, 0x30303030, 7, 0x38, 0x48]
    def put(ee, b1=None, b3=0, micro=None, st=None):
        s = bytearray(st or step); s[3] = b3
        if b1 is not None: s[1] = b1
        if micro is not None: s[6] = micro
        ee.uc.mem_write(STEP0, bytes(s))
    bad, n = [], 0
    e.setup(); p.setup()
    for b1 in range(8):
        for wd in words:
            for micro in range(6):
                for mm in (0, 3, 5):
                    put(e, b1, 0, mm); put(p, b1, 0, mm); n += 1
                    a, b_ = e.build(micro, wd), p.build(micro, wd); want = 1 if (b1 >= (wd & 7) and mm == micro) else 0
                    if not (a == b_ == want) or e.r32(PLAYER + 4) != wd: bad.append((b1, hex(wd), micro, mm, a, b_, want))
    check(not bad, f"byte [3] = 0: {n} masks = the stock's rule = the previous build's (probability, micro step), the random word untouched {bad[:3]}")
    put(p, 7, 0x77, m0); check(p.build(m0, 0) == 1, "the previous build ignores byte [3]")
    # the frequency
    if "c_rfpass" in L:                                                             # SC40.4: the plays of the pattern are counted
        counter_tests(e, img, L, put, check)
    else:
        bad, n = [], 0
        TICKS = [struct.unpack_from("<I", img, SM.TICKS_TAB - B + 4 * i)[0] for i in range(8)]
        for first, last, rate in ((0, 15, None), (0, 7, None), (4, 6, None), (30, 1, None), (0, 31, 0), (0, 15, 7), (2, 2, 1)):
            r = e.setup(first, last, rate); tps = TICKS[min(r, 7)]
            steps = last - first + 1 + (32 if last < first else 0); Lp = steps * tps
            for N in range(1, 9):
                put(e, 7, N - 1, 0)
                for ps in range(0, 2 * N + 1):
                    for tin, where in ((0, 0), (0, Lp - tps), (tps - 1, Lp - 1), (1, 1)):
                        T = ps * Lp + where
                        e.setup(first, last, rate, tin, T); got = e.build(0, 0); n += 1
                        want = 1 if ps % N == N - 1 else 0
                        if got != want: bad.append((first, last, r, N, ps, where, got, want))
        check(not bad, f"the frequency: {n} masks over passes, lengths and sync rates (ticks per step {sorted(set(TICKS))}): the step starts in the last pass of each n {bad[:4]}")
    # the position
    e.setup(rate=rate0); bad, n, moved = [], 0, 0
    for level in range(1, 8):
        for mm in (0, 1, 3, 5):
            for wd in words:
                put(e, 7, level << 4, mm)
                got = [e.build(mi, wd) for mi in range(6)]; n += 1
                want = min(max(mm + off_model(level, (wd >> 3) & 15), 0), 5); moved += want != mm
                if got != [1 if mi == want else 0 for mi in range(6)] or e.uc.mem_read(STEP0 + 6, 1)[0] != mm: bad.append((level, mm, hex(wd), got, want))
    check(not bad and moved > 20, f"the position: {n} steps (levels 1-7), the unit starts in one micro step, the model's ({moved} moved); the step untouched {bad[:3]}")
    # a second unit: its own four bits
    st2 = bytearray(step); st2[0] |= 4; st2[12:16] = bytes([60, 3, 2, 100])
    bad = []
    for wd in words:
        put(e, 7, 4 << 4, 3, st=bytes(st2)); got = [e.build(mi, wd) for mi in range(6)]
        w0 = min(max(3 + off_model(4, (wd >> 3) & 15), 0), 5); w2 = min(max(2 + off_model(4, (wd >> 11) & 15), 0), 5)
        if got != [(1 if mi == w0 else 0) | (4 if mi == w2 else 0) for mi in range(6)]: bad.append((hex(wd), got, w0, w2))
    check(not bad, f"two units of a step: each one its own offset (bits 3 + 4 x unit of the random word) {bad[:3]}")
    # recording with mode 2 on the screen: written, no second start
    bad, n = [], 0
    for rec, scr in ((1, 1), (1, 0), (0, 1)):
        e.transport(1, rec, 0); e.screen(scr)
        for level in (1, 4, 6):
            for mm in (0, 2, 5):
                for wd in words:
                    put(e, 7, level << 4, mm); want = min(max(mm + off_model(level, (wd >> 3) & 15), 0), 5); cur = wd; got = []
                    for mi in range(6):
                        e.uc.mem_write(PLAYER, e.snap); e.w32(PLAYER + 4, cur); e.uc.mem_write(0x2006F000, bytes(4))
                        e.call(BUILD, PLAYER, 0, 0, mi, maxins=400_000); got.append(e.r8(PLAYER + 0x13C + mi)); cur = e.r32(PLAYER + 4)
                    after = e.uc.mem_read(STEP0 + 6, 1)[0]; n += 1
                    if got != [1 if mi == want else 0 for mi in range(6)] or after != (want if rec and scr else mm) or (cur & 7) != (wd & 7): bad.append((rec, scr, level, mm, hex(wd), got, after, want))
    check(not bad, f"recording with mode 2 on the screen: the new micro step written, one start only; recording alone / the view alone: the step untouched ({n} steps) {bad[:3]}")
    e.transport(0, 0, 0); e.screen(0)

    # ---- the player: the velocity and the length
    e.setup(rate=rate0); p.setup(rate=rate0)
    def ref(vel, gate, note=None):
        s = bytearray(step); s[2] = s[3] = 0; s[5] = gate; s[7] = vel
        if note is not None: s[4] = note
        p.uc.mem_write(STEP0, bytes(s)); return p.note(0)
    def model(level, rnd, vel, gate):
        mlo, mhi, vlo, vhi = SM.DYN[level]
        v2 = min(max(vel + vlo + ((rnd >> 8) & 0xFFFF) % (vhi - vlo + 1), 1), 127)
        g2 = gate if gate & 0x80 else min(max(gate + mlo + ((rnd >> 24) & 0xFF) % (mhi - mlo + 1), 1), SM.MAX_LEN)
        return v2, g2
    rnds = [0, 0xFFFFFFFF, 0x12345678, 0x0BADF00D, 0x00010000, 0x3FFFFFC0, 0x2AAAAAAA, 0x15555555, 0x00F0F0F0, 0x05001F00, 0x02000400, 0x03002100, 0x01000100]
    bad, n, ch = [], 0, 0
    for level in range(0, 8):
        for vel, gate in ((100, 6), (1, 1), (127, 0x60), (20, 2), (110, 0x5F), (64, 0x86)):
            for r in rnds:
                s = bytearray(step); s[2] = 0; s[3] = level << 4; s[5] = gate; s[7] = vel; e.uc.mem_write(STEP0, bytes(s))
                got = e.note(r); v2, g2 = model(level, r, vel, gate) if level else (vel, gate); want = ref(v2, g2); n += 1; ch += (v2, g2) != (vel, gate)
                if got != want or len(got) != 1 or bytes(e.uc.mem_read(STEP0, 28)) != bytes(s) or e.rcalls != (1 if level else 0): bad.append((level, vel, hex(gate), hex(r), got, want))
    check(not bad and ch > 100, f"the player: {n} plays (levels 0-7): the velocity and the length at the note-on = a step with the model's values ({ch} changed); the step untouched; "
          f"level 0: no generator call {bad[:3]}")
    # recording
    e.set_scale(MASKS[0], 0); n0 = step[4]
    mut = [(lv, r) for lv in range(1, 8) for r in rnds if T39.model(n0, lv, r, MASKS[0], 0) != n0 and e.snap[MU.O_SOUND + T39.model(n0, lv, r, MASKS[0], 0)] == 0xFF]
    lv, r = mut[0]; nm = T39.model(n0, lv, r, MASKS[0], 0)
    res = {}
    for name, rec, scr in (("rec+view", 1, 1), ("rec", 1, 0), ("view", 0, 1)):
        e.transport(1, rec, 0); e.screen(scr)
        s = bytearray(step); s[2] = lv; s[3] = 4 << 4; s[5] = 6; s[7] = 90; e.uc.mem_write(STEP0, bytes(s))
        got = e.note(r); res[name] = (got, bytes(e.uc.mem_read(STEP0, 8)))
    v2, g2 = model(4, r, 90, 6)
    a, sa = res["rec+view"]; b_, sb = res["rec"]; c, sc = res["view"]
    check(a == b_ == c and a[0][0] == nm and a[0][1] == v2 and (v2, g2) != (90, 6), f"mutate + dynamics: the same note / velocity / length played in the three cases ({a})")
    check(sa[4] == nm and sa[7] == v2 and sa[5] == g2 and sb[4] == n0 and sb[7] == 90 and sb[5] == 6 and sc[4:8] == sb[4:8],
          f"recording with mode 2 on the screen: note {n0} -> {sa[4]}, velocity 90 -> {sa[7]}, length 6 -> {sa[5]} written; recording alone / the view alone: the step untouched")
    e.transport(0, 0, 0)
    print(("SC40.4" if "c_rfpass" in L else "SC40.3") + " ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
