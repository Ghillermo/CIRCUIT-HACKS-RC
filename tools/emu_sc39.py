"""SC39 ARM tests (live RAM dump, the real routes): random-mutate (tools/mutate39.py) and the steady glide colours (packio.use_pmode2).

    python tools/emu_sc39.py SC39.bin SC39_manifest.json SC38.9.bin SC38.9_manifest.json
  * the hooks: the player's two loads (0x08040EFC) -> c_mutnote, the probability view's slots 0 / 7 / 8 and its listener thunk;
  * the view through the controller (Synth 1, Shift + button 12 = the probability view, a step held, the pads by 0x08033282 and the LED task 0x08034196):
    row 4 writes the level (0..7) into the step's byte [2] of the pattern, row 3 still writes the stock probability (byte [1]) and leaves the level;
    the LEDs: row 3 as the stock, row 4 a peach bar (dim above the level), drawn when the view opens; a step without notes: nothing written, row 4 off;
  * the player 0x08040E5A itself (the sequencer's player object of Synth 1, the note-on 0x08040FA2 watched, the stock generator 0x08049908 replaced
    by chosen values): the note played = the model, for every level, several notes, scales and roots; level 0 = the step's note, no generator call;
    a tied unit, a unit that continues a tie and a new note that already sounds: the step's note;
  * recording (the transport's parameters 0 / 1 set, 2 clear): the mutated note is written into the step; playing only, or the count-in: the step stays;
  * the stock generator: over many plays the octave / scale rates of levels 1, 4 and 7 are near 6 / 12 / 25 + 50 %;
  * the glide patches: steady codes (not one of the board's animated ones), emu_sc38_8's checks with the new colours;
  * the previous build: row 4 does nothing, the player plays the step's note whatever the byte [2].
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
from emu_sc08 import CONT, SCALE_OBJ, ROOT_PTR, MASKS  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import mutate39 as MU  # noqa: E402
import packio as PK  # noqa: E402

PLAYER = 0x20040200                  # Synth 1's player object (vtable 0x0805B750): + 0x48 its patterns, + 0x4C its note interface
PLAY, NOTE_ON = 0x08040E5A, 0x08040FA2
STEP0, STEP1 = 0x20011B20, 0x20011B20 + 28       # Synth 1, pattern 1, steps 1 / 2 (step 1 has one note in the dump, step 2 none)
ANIMATED = {0x03, 0x04, 0x05, 0x06, 0x10, 0x11, 0x15, 0x16, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x27, 0x28, 0x2F, 0x30, 0x39, 0x3A, 0x42, 0x43, 0x47, 0x48, 0x4B,
            0x4C, 0x4F, 0x50, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5B, 0x61, 0x62}     # read on the unit (2026-10-12): entries of the RGB table that change


def scale_model(n, rnd, mask, root):
    pc = (120 + n - root) % 12
    others = [j for j in range(12) if j != pc and (mask >> (2 * j)) & 3 == 0]
    if not others: return n
    m = n - pc + others[rnd % len(others)]
    if m < 0: m += 12
    if m > 127: m -= 12
    return m


def model(n, level, rnd, mask, root):
    """the note c_mutnote plays for the generator's value rnd"""
    r = (rnd & 0xFFFFFFFF) >> 6
    ch = MU.CHANCE[level]; sc, oc = ch >> 4, ch & 15
    t = r & 15; r >>= 4
    if t < sc: n = scale_model(n, r, mask, root); r >>= 8
    t = r & 15; r >>= 4
    if t < oc:
        if r & 1:
            n -= 12
            if n < 0: n += 24
        else:
            n += 12
            if n > 127: n -= 24
    return n


class EP(E35):
    """the player of Synth 1 with the note-on watched and the generator under control"""
    def __init__(self, img, man):
        super().__init__(img, man)
        self.ons, self.rnd, self.rcalls, self.real = [], 0, 0, False
        def on(uc, a, s, d):                              # the note-on itself is not run (the synth's note interface waits for the DSP in emulation)
            self.ons.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2))); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        def rh(uc, a, s, d):
            self.rcalls += 1
            if not self.real:
                uc.reg_write(UC_ARM_REG_R0, self.rnd & 0xFFFFFFFF); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        self.uc.hook_add(UC_HOOK_CODE, on, begin=NOTE_ON, end=NOTE_ON)
        self.uc.hook_add(UC_HOOK_CODE, rh, begin=MU.RANDOM, end=MU.RANDOM)
        self.snap = bytes(self.uc.mem_read(PLAYER, 0x200))
        self.step = bytes(self.uc.mem_read(STEP0, 28))

    def play(self, level, rnd=0, note=None, tie=False, held=None, sounding=None, keep=False):
        """one play of step 1 (its unit 0) -> the notes given to the note-on"""
        self.uc.mem_write(PLAYER, self.snap)
        if not keep: self.uc.mem_write(STEP0, self.step)
        self.uc.mem_write(STEP0 + 2, bytes([level]))
        if note is not None: self.uc.mem_write(STEP0 + 4, bytes([note]))
        if tie: self.uc.mem_write(STEP0 + 5, bytes([self.step[5] | 0x80]))
        if held is not None:
            a = PLAYER + MU.O_HELD + 4 * (held >> 5); self.w32(a, self.r32(a) | 1 << (held & 31))
        if sounding is not None: self.uc.mem_write(PLAYER + MU.O_SOUND + sounding, bytes([0]))
        self.uc.mem_write(PLAYER + 0x13C, bytes([1]))                              # unit 0 starts at micro step 0
        self.rnd = rnd; self.ons.clear(); self.rcalls = 0
        self.call(PLAY, PLAYER, 0, 0, 0, maxins=200_000)
        return [n for n, v in self.ons]

    def transport(self, play, rec, count):
        for k, v in enumerate((play, rec, count)):
            self.call(0x0803542C, MU.PLAY_STORE, k); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([v]))

    def set_scale(self, mask, root):
        self.w32(SCALE_OBJ + 4, mask); self.uc.mem_write(ROOT_PTR, bytes([root]))


def view_run(img, man):
    e = E35(img, man)
    def frame():
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda p: (e.call(PRESS, MGR, p, 100, maxins=8_000_000), e.call(RELEASE, MGR, p, maxins=8_000_000))
    step = lambda a: bytes(e.uc.mem_read(a, 4))
    out = {}
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)                        # Synth 1
    e.set_p0(e.r32(MGR + 0xC), 1); press(12); release(12); e.set_p0(e.r32(MGR + 0xC), 0)   # Shift + button 12: the probability view
    out["sub"] = e.r8(MGR + 0x152); out["open"] = frame()
    e.call(PRESS, MGR, 0, 100, maxins=8_000_000)                                  # step 1 held
    out["levels"] = []
    for k in (3, 7, 1, 0, 5):
        pad(24 + k); out["levels"].append((k, step(STEP0), frame()[24:]))
    pad(16 + 2); out["prob"] = (step(STEP0), frame()[16:])                          # row 3: the stock probability, the level stays
    e.call(RELEASE, MGR, 0, maxins=8_000_000)
    e.call(PRESS, MGR, 1, 100, maxins=8_000_000)                                  # step 2 (no notes)
    pad(24 + 4); out["empty"] = (step(STEP1), frame()[24:])
    e.call(RELEASE, MGR, 1, maxins=8_000_000)
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    B = 0x08010000
    L = {k: int(v, 16) for k, v in man["report"]["mutate39"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import bl as tbl, nop
    check(bytes(img[MU.NOTE_LOAD - B:MU.NOTE_BACK - B]) == tbl(MU.NOTE_LOAD, L["c_mutnote"]) + nop() and bytes(prev[MU.NOTE_LOAD - B:MU.NOTE_BACK - B]) == MU.NOTE_OLD,
          "the player's two loads at 0x08040EFC = bl c_mutnote; nop (the previous build: the stock's)")
    check(w(MU.PROB_VT) == L["c_mutpad"] | 1 and w(MU.PROB_VT + 28) == L["c_mutbuf"] | 1 and w(MU.PROB_VT + 32) == L["c_mutled"] | 1 and w(MU.PROB_VT2) == L["c_mutled_t"] | 1,
          "the probability view: slot 0 = c_mutpad, 7 = c_mutbuf, 8 = c_mutled, the listener's thunk = c_mutled_t")

    # ---- the view
    v = view_run(img, man)
    LIT, DIM = MU.COL_LIT, MU.COL_DIM
    bar = lambda k: [LIT] * (k + 1) + [DIM] * (7 - k)
    check(v["sub"] == 5 and v["open"][24:] == bar(0) and v["open"][16:24] == [0x6C + i for i in range(8)],
          f"Shift + button 12: the probability view (submode {v['sub']}); row 3 as the stock, row 4 drawn in peach (level 0) at once\n    {[hex(x) for x in v['open'][16:]]}")
    ok = all(s[2] == k and s[1] == 7 and s[3] == 0 and f == bar(k) for k, s, f in v["levels"])
    check(ok, f"row 4 (pads 25-32): the level in the step's byte [2], the bar follows ({[(k, s.hex()) for k, s, f in v['levels']]})")
    s, f = v["prob"]
    check(s[1] == 2 and s[2] == 5 and f == [0x6C, 0x6D, 0x6E, 0, 0, 0, 0, 0] + bar(5), f"row 3 (pad 19): the stock probability 2, the level kept ({s.hex()})")
    s, f = v["empty"]
    check(s[0] == 0 and s[2] == 0 and f == [0] * 8, f"a step without notes: nothing written ({s.hex()}), row 4 off")
    gc.collect(); vp = view_run(prev, prev_man)
    check(all(s[2] == 0 for k, s, f in vp["levels"]) and vp["open"][24:] == [0] * 8, "the previous build: row 4 does nothing and stays off")

    # ---- the player
    gc.collect(); e = EP(img, man)
    n0 = e.step[4]
    check(e.play(0, 0) == [n0] and e.rcalls == 0, f"level 0: the step's note ({n0}), the generator not called")
    bad, n = [], 0
    rnds = [0, 0xFFFFFFFF, 0x12345678, 0x0BADF00D, 0x00000400, 0x00010000, 0x3FFFFFC0, 0x2AAAAAAA, 0x15555555, 0x00F0F0F0, 0x0000FFC0, 0x1F00, 0x40, 0x7C0, 0x1000,
            0x93C467E3, 0x7DB4C0, 0x00FC00, 0x30303030]
    for mask, root in ((MASKS[0], 0), (MASKS[3], 5), (MASKS[15], 0), (MASKS[8], 11), (0x00FFFFFC, 3)):
        e.set_scale(mask, root)
        for note in (n0, 0, 5, 60, 61, 119, 127):
            for level in range(1, 8):
                for r in rnds:
                    got = e.play(level, r, note=note); want = model(note, level, r, mask, root); n += 1
                    if e.snap[MU.O_SOUND + want] != 0xFF: want = note               # (the dump's entry of note 0 is not 0xFF: it "sounds")
                    if got != [want] or bytes(e.uc.mem_read(STEP0 + 4, 1))[0] != note: bad.append((hex(mask), root, note, level, hex(r), got, want))
    check(not bad, f"the player: {n} plays (5 scales / roots, 7 notes, levels 1-7, {len(rnds)} generator values) = the model, the step untouched {bad[:4]}")
    e.set_scale(MASKS[0], 0)
    mut = [(lv, r) for lv in range(1, 8) for r in rnds if model(n0, lv, r, MASKS[0], 0) != n0]
    lv, r = mut[0]; m0 = model(n0, lv, r, MASKS[0], 0)
    check(e.play(lv, r) == [m0] and e.play(lv, r, tie=True) == [n0], f"a tied unit: the step's note ({n0}), not {m0}")
    got = e.play(lv, r, held=n0)
    check(m0 not in got, f"a unit that continues a tie: no mutated note ({got})")
    check(e.play(lv, r, sounding=m0) == [n0], f"the new note ({m0}) already sounds: the step's note")
    e.transport(1, 0, 0); a = e.play(lv, r); sa = e.uc.mem_read(STEP0 + 4, 1)[0]
    e.transport(1, 1, 1); b_ = e.play(lv, r); sb = e.uc.mem_read(STEP0 + 4, 1)[0]
    e.transport(1, 1, 0); c = e.play(lv, r); sc = e.uc.mem_read(STEP0 + 4, 1)[0]
    check(a == b_ == c == [m0] and sa == n0 and sb == n0 and sc == m0, f"recording: the mutated note written into the step ({n0} -> {sc}); playing only / the count-in: not ({sa}, {sb})")
    e.transport(1, 1, 0); c2 = e.play(lv, r, tie=True); sc2 = e.uc.mem_read(STEP0 + 4, 1)[0]
    check(c2 == [n0] and sc2 == n0, "recording, a tied unit: nothing written")
    e.transport(0, 0, 0)
    # ---- the stock generator
    e.real = True
    for level, oc, sc_ in ((1, 1 / 16, 0), (4, 0, 2 / 16), (7, 4 / 16, 8 / 16)):
        N = 1600; no = ns = 0
        for _ in range(N):
            g = e.play(level)[0]
            if (g - n0) % 12: ns += 1                                               # another degree of the scale
            if g // 12 != n0 // 12: no += 1                                         # another octave (root C: the scale change stays in the octave)
        lo = lambda p: p * N * 0.75 - 6; hi = lambda p: p * N * 1.25 + 6
        okk = (oc == 0 and no == 0 or oc and lo(oc) <= no <= hi(oc)) and (sc_ == 0 and ns == 0 or sc_ and lo(sc_) <= ns <= hi(sc_))
        check(okk, f"the stock generator, level {level}, {N} plays: octave {no} (expected ~{oc * N:.0f}), scale {ns} (~{sc_ * N:.0f})")
    del e; gc.collect()
    ep = EP(prev, prev_man)
    check(all(ep.play(lv_, r_) == [n0] for lv_ in (1, 7) for r_ in rnds[:6]), "the previous build: the step's note whatever the byte [2]")
    del ep; gc.collect()

    # ---- the glide patches' colours
    PK.PMODE = True; PK.use_pmode2()
    check(not set(PK.PM_GLIDE + PK.PM_MONO + (LIT, DIM)) & ANIMATED, f"the glide / mono / mutate colour codes are steady ones ({[hex(c) for c in PK.PM_GLIDE]})")
    import emu_sc38_8 as T8
    f7 = Path(__file__).resolve().parent.parent / "firmware" / "sc38.7"
    print("--- emu_sc38_8 on this build, with the new glide colours (the previous build there: SC38.7)")
    fails += T8.main(img, man, (f7 / "circuittracks-4486-SC38.7.bin").read_bytes(), json.loads((f7 / "manifest.json").read_text())) or 0
    print("SC39 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
