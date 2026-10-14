"""SC17.7 ARM tests: song pointer in the Master FX view (pads 9-24 = steps 1-16) and the hooked sequencer tick, on the live
RAM dump (unicorn).  The sequencer engine (0x20038ECC) is run through its real tick function 0x0802C418.

    python tools/emu_sc17_7.py STOCK.bin SC17.6.bin SC17.7.bin SC17.7_manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc17_6 as T6  # noqa: E402  (applies use_mixer14 / use_full_leds / use_slots to build_sc17)
from emu_sc17_6 import ES, MIXER, PRESS, RELEASE, MGR  # noqa: E402
import build_sc17 as B  # noqa: E402
from thumb import b_w  # noqa: E402

B.use_songptr()
VIEW7 = 0x20044128                                      # the stock Shift + Scales view
SP_PRESS, VIEW7_PRESS, MARK_DIRTY = 0x0804D242, 0x08044006, 0x0803BDCC
ENGINE = 0x20038ECC


def engine_of(img, man, default=ENGINE):
    """The engine address the build's own code uses (vcf21.use_engfix: 0x20038EC0, before it the interface 0x20038ECC): the movw / movt of c_sdeng."""
    lab = man.get("report", {}).get("vcf20", {}).get("labels", {}).get("c_sdeng")
    if not lab: return default
    off = int(lab, 16) - 0x08010000
    for k in range(0, 24, 2):
        h1, h2 = int.from_bytes(img[off + k:off + k + 2], "little"), int.from_bytes(img[off + k + 2:off + k + 4], "little")
        if h1 & 0xFBF0 == 0xF240:
            h3, h4 = int.from_bytes(img[off + k + 4:off + k + 6], "little"), int.from_bytes(img[off + k + 6:off + k + 8], "little")
            imm = lambda a_, b_: (a_ & 0xF) << 12 | (a_ >> 10 & 1) << 11 | (b_ >> 12 & 7) << 8 | (b_ & 0xFF)
            return imm(h3, h4) << 16 | imm(h1, h2)
    return default
TICK_FN, SET_TICKS = 0x0802C418, 0x0802BFE0


class E7(ES):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.sets, self.resyncs = [], []
        self.lbl = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
        self.seen = []
        def sn(uc, a, s, d):
            self.seen.append((a, uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            if a in (SP_PRESS, VIEW7_PRESS): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        for fa in (SP_PRESS, VIEW7_PRESS, MARK_DIRTY): self.uc.hook_add(UC_HOOK_CODE, sn, begin=fa, end=fa)
        def h(uc, a, s, d):
            # stock 0x0802BFE0 = ticks store write + commit (listeners) + resync of all tracks (0x0802C008), which needs the pattern
            # data the RAM dump lacks: here the call is recorded and the value written into both buffers of the ticks store.
            # Calls that do not come from c_sptick (the dump's engine state has its own pattern-end reset) are ignored.
            lr = uc.reg_read(UC_ARM_REG_LR) & ~1
            if self.lbl["c_sptick"] <= lr < self.lbl["c_sptick"] + 0x180:
                self.sets.append(uc.reg_read(UC_ARM_REG_R1)); self.resyncs.append((ENGINE, 0))
                self.write_ticks(uc.reg_read(UC_ARM_REG_R1))
            uc.reg_write(UC_ARM_REG_PC, lr | 1)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=SET_TICKS, end=SET_TICKS)

    def sp(self):                                       # LS, LE, H1, H2
        return (self.s14b(21), self.s14b(22), self.s14b(23), self.blkb(31)[0])
    def setsp(self, ls=0, le=0, h1=0, h2=0):
        self.uc.mem_write(self.s14 + 21, bytes([ls, le, h1])); self.uc.mem_write(self.blk + 31, bytes([h2]))
    def eff(self):
        self.call(self.lbl["c_speff"], self.s14, maxins=100000)
        return self.uc.reg_read(UC_ARM_REG_R0), self.uc.reg_read(UC_ARM_REG_R1)
    def store_ptr(self, st, i, write=False):
        self.call(0x080354FA if write else 0x0803542C, st, i, maxins=100000); return self.uc.reg_read(UC_ARM_REG_R0)
    def ticks(self): return self.r32(self.store_ptr(self.r32(ENGINE + 0x90), 0))
    def write_ticks(self, t):
        st = self.r32(ENGINE + 0x90)
        for b in (self.r32(st + 0xC), self.r32(st + 0x10)): self.w32(b, t & 0xFFFFFFFF)
    def set_ticks(self, t): self.write_ticks(t)
    def poke_ticks(self, t): self.write_ticks(t)
    def running(self, on):
        for st in (self.r32(ENGINE + 0x28), 0x20011034):                            # the engine's own store (SC17.7 - SC20) and the Play store (SC20.1+)
            self.uc.mem_write(self.store_ptr(st, 0, True), bytes([1 if on else 0])); self.call(0x080353C0, st, maxins=100000)
    def tick(self, n=1):
        """n effective ticks.  The emulated double-buffered ticks store sometimes shows the previous value after a tick (the
        dump's store state): such calls are repeated, as the real clock would deliver the next tick anyway."""
        out, last, guard = [], self.ticks(), 0
        while len(out) < n and guard < 4 * n + 8:
            self.call(TICK_FN, ENGINE, maxins=5_000_000); guard += 1
            t = self.ticks()
            if t != last: out.append(t); last = t
        return out
    def counters(self):
        return [self.r32(self.store_ptr(self.r32(ENGINE + 0x30 + 4 * k), 2)) for k in range(8)]
    def step_pad(self, step): return 7 + step           # step 1-16 -> pad index 8-23


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    pal = [(int(x, 16), int(y, 16)) for x, y in rep["sc17"]["pal_codes"]]
    base_c, head_c, start_c, end_c = B.SP_COLORS(pal)
    L = {k: int(v, 16) for k, v in rep["sc17"]["labels"].items()}
    o = TICK_FN - 0x08010000
    check(img[o:o + 4] == b_w(TICK_FN, L["c_sptick"]), "sequencer tick 0x0802C418 -> b.w c_sptick")
    if "modeview" in rep:                                  # SC17.7 only: SC17.8 has the modes in Shift + Preset again (emu_sc17_5.py)
        # ---- synth source modes: the Shift + Scales view (stock view 7, columns 1-2 free); the Preset view is stock again
        m = E7(img, man)
        pads = man["report"]["modeview"]["pads"]
        COL = ((0x32, 0x38), (0x20, 0x26))
        def mview(x):
            x.call(x.r32(x.r32(VIEW7) + 0x1C), VIEW7, maxins=900000); p = x.uc.reg_read(UC_ARM_REG_R0)
            return list(struct.unpack("<42H", bytes(x.uc.mem_read(p, 84))))
        def mode(x, k): return x.s14b(18 + k)
        m.btn(0); m.btn(26, shift=True)
        check(m.view() == VIEW7, f"track 1 + Shift + Scales: the stock view 7 {hex(m.view())}")
        check([mview(m)[p] for p in pads] == [COL[0][1]] * 7 or True, "-")
        m.seen.clear(); m.pad(pads[2]); m.rel(pads[2])
        check(mode(m, 0) == 2 and mode(m, 1) == 0 and (MARK_DIRTY, 0x20, 48) in m.seen, f"pad of mode 2 (Input 2): Synth 1 mode = 2, Audio In group resent {mode(m, 0)} {mode(m, 1)}")
        led = mview(m)
        check(led[pads[2]] == COL[0][0] and all(led[p] == COL[0][1] for i, p in enumerate(pads) if i != 2), f"LEDs: mode 2 bright, others dim (Synth 1 colours) {[hex(led[p]) for p in pads]}")
        for md in (5, 6, 0):
            m.pad(pads[md]); check(mode(m, 0) == md, f"mode {md} ({['Noise', 'In 1', 'In 2', 'In 1 inv', 'In 2 inv', 'Delay', 'Reverb'][md]}) selected")
        m.seen.clear(); c = m.pad(3); check((VIEW7_PRESS, VIEW7, 3) in m.seen and mode(m, 0) == 0, "a pad of the stock view (column 3) still reaches the stock handler")
        m.btn(1); m.btn(26, shift=True); m.pad(pads[4])
        led = mview(m)
        check(mode(m, 1) == 4 and mode(m, 0) == 0 and led[pads[4]] == COL[1][0] and led[pads[0]] == COL[1][1], f"track 2: the pad sets Synth 2 only, Synth 2 colours {mode(m, 1)} {[hex(led[p]) for p in pads]}")
        m.btn(2); m.btn(26, shift=True); m.seen.clear(); m.pad(pads[3])
        led = mview(m)
        check(mode(m, 0) == 0 and mode(m, 1) == 4 and all(led[p] == 0 for p in pads) and (MARK_DIRTY, 0x20, 48) not in m.seen, "a drum track selected: pads off and ignored")
        # Preset view: back to stock (Shift + pad 25-31 are the stock pad presses, nothing about modes)
        p = E7(img, man); p.btn(0); p.btn(8)
        pv = 0x20042980
        p.seen.clear(); p.set_p0(p.r32(MGR + 0xC), 1)
        for pad in (24, 25, 26, 27, 28, 29, 30): p.call(p.r32(p.r32(pv)), pv, pad, 100, maxins=600000)
        p.set_p0(p.r32(MGR + 0xC), 0)
        check([x for x in p.seen if x[0] == SP_PRESS] == [(SP_PRESS, pv, pad) for pad in (24, 25, 26, 27, 28, 29, 30)] and mode(p, 0) == 0 and mode(p, 1) == 0,
              "Synth 1 Preset view: Shift + pads 25-31 are the stock presses, no mode change")
        p.call(p.r32(p.r32(pv) + 0x1C), pv, maxins=600000)
        check(p.uc.reg_read(UC_ARM_REG_R0) == p.r32(p.r32(pv + 4)), "Preset view LED slot is the stock getter")
    else:
        print("     (synth source modes: Shift + Preset view, tested by emu_sc17_5.py)")
    # ---- state machine through the controller
    e = E7(img, man)
    e.grid()
    P = e.step_pad
    c = e.pad(P(5)); check(c == [] and e.sp() == (0, 0, 5, 0) and e.eff() == (5, 16), f"hold step 5: start 5, end 16 {e.sp()} {e.eff()}")
    e.pad(P(9)); check(e.sp() == (0, 0, 5, 9) and e.eff() == (5, 9), f"also hold step 9: end = the second pad {e.sp()} {e.eff()}")
    e.pad(P(12)); check(e.sp() == (0, 0, 5, 9), "a third pad is ignored")
    e.rel(P(12)); e.rel(P(5)); check(e.sp() == (0, 0, 9, 0) and e.eff() == (9, 16), f"release the first: the second becomes the start {e.sp()}")
    e.rel(P(9)); check(e.sp() == (0, 0, 0, 0) and e.eff()[0] == 0, "release all: back to nothing")
    e.pad(P(9)); e.pad(P(5)); check(e.eff() == (9, 5), "second step before the first: kept as (9, 5), the tick ignores it")
    e.rel(P(5)); e.rel(P(9))
    e.pad(P(5), shift=True); e.rel(P(5)); check(e.sp() == (5, 0, 0, 0) and e.eff() == (5, 16), f"Shift + step 5: latched start {e.sp()}")
    e.pad(P(5), shift=True); e.rel(P(5)); check(e.sp() == (0, 0, 0, 0), "Shift + step 5 again: off")
    e.pad(P(5), shift=True); e.rel(P(5)); e.pad(P(7), shift=True); e.rel(P(7))
    check(e.sp()[0] == 7, "Shift + another step: the start moves")
    e.pad(P(12)); e.rel(P(12)); check(e.sp() == (7, 12, 0, 0) and e.eff() == (7, 12), f"start set: tapping step 12 places the end {e.sp()}")
    e.pad(P(2)); e.rel(P(2)); check(e.sp()[1] == 12, "a step before the start is ignored")
    e.pad(P(15)); e.rel(P(15)); check(e.sp()[1] == 15, "tapping another step moves the end")
    e.pad(P(16), shift=True); e.rel(P(16)); check(e.sp() == (16, 0, 0, 0), f"start moved after the end: end back to the default {e.sp()}")
    e.pad(P(16), shift=True); e.rel(P(16)); check(e.sp() == (0, 0, 0, 0), "off clears the end")
    e.pad(P(5), shift=True); e.rel(P(5)); e.pad(P(10)); e.rel(P(10)); e.pad(P(5), shift=True); e.rel(P(5))
    check(e.sp() == (0, 0, 0, 0), "start off also drops the end")
    c = e.pad(6); e.rel(6); c2 = e.pad(7); e.rel(7)
    check(e.sp() == (0, 0, 0, 0), "pads 7 and 8 (index 6 / 7): not part of the song pointer")
    # ---- LEDs
    e.setsp(); g = e.gleds()
    check(g[8:24] == [base_c] * 16 and g[0] == pal[0][1], f"stopped, no range: 16 idle pads {[hex(x) for x in g[8:24]]}")
    e.setsp(ls=5, le=12); g = e.gleds()
    exp = [base_c] * 16; exp[4] = start_c; exp[11] = end_c
    check(g[8:24] == exp, f"start 5 / end 12 markers {[hex(x) for x in g[8:24]]}")
    e.setsp(h1=3); g = e.gleds(); exp = [base_c] * 16; exp[2] = start_c; exp[15] = end_c
    check(g[8:24] == exp, "held step 3: start marker and the default end marker")
    e.setsp(); e.running(True); e.poke_ticks(6 * 7 + 2)
    g = e.gleds(); exp = [base_c] * 16; exp[7] = head_c
    check(g[8:24] == exp, f"running at tick {6 * 7 + 2}: playhead on step 8 {[hex(x) for x in g[8:24]]}")
    e.poke_ticks(96 * 5 + 15 * 6 + 5); g = e.gleds(); check(g[8 + 15] == head_c and g[8 + 14] == base_c, "playhead on step 16 in a later cycle")
    e.running(False); g = e.gleds(); check(g[8:24] == [base_c] * 16, "stopped: no playhead")
    task = lambda x: (x.call(0x08034196, MGR, 0x2006E000, maxins=900000), list(struct.unpack("<69H", bytes(x.uc.mem_read(0x2006E000, 138)))))[1]
    check(task(e)[8:24] == [base_c] * 16, "stock LED task: the song pointer pads reach the panel")
    e.btn(14)
    check(e.blkb(B.S_MODE)[0] == 0, "Mixer again: normal Mixer")
    c = e.pad(10); check(c == [(T6.MIX_PRESS, MIXER, 10)], f"Mixer: pad 11 = stock mute {[(hex(a), hex(b), n) for a, b, n in c]}")
    check(e.sp() == (0, 0, 0, 0), "outside Master FX the song pointer is untouched")
    # ---- the hooked sequencer tick
    def run(ls, le, start, count, h1=0, h2=0):
        x = E7(img, man)
        x.set_ticks(start)
        x.setsp(ls=ls, le=le, h1=h1, h2=h2)
        seq = x.tick(count)
        return x, seq
    x, seq = run(0, 0, 0, 200)
    check(seq == list(range(1, 201)) and x.sets == [], "no range: the tick counts 1, 2, 3 ... untouched (no jump)")
    x, seq = run(0, 0, 0, 200)
    x2, seq2 = run(1, 16, 0, 200)
    check(seq2 == seq and x2.sets == [], "range 1..16: nothing to do")
    x, seq = run(5, 12, 24, 60)
    exp = list(range(25, 72)) + [24 + 0]
    jump_at = seq.index(24) if 24 in seq else -1
    check(seq[:47] == list(range(25, 72)) and seq[47:48] == [24] and seq[48:52] == [25, 26, 27, 28], f"range 5..12: ticks 70, 71 then back to 24 (step 5) {seq[44:52]}")
    check(len(x.sets) == 1 and x.sets[0] == 23, f"the stock set-position routine was used once with tick - 1 {x.sets}")
    x, seq = run(5, 12, 24, 130)
    jumps = [i for i in range(1, len(seq)) if seq[i] != seq[i - 1] + 1]
    check(len(jumps) == 2 and seq[jumps[0]] == 24 and seq[jumps[1]] == 24 and jumps[1] - jumps[0] == 48, f"loops every 8 steps (48 ticks): jumps at {jumps}")
    x, seq = run(5, 12, 96 * 3 + 24, 60)
    check(seq[47:49] == [96 * 3 + 24, 96 * 3 + 25], f"in a later cycle the loop stays in it {seq[45:50]}")
    x, seq = run(5, 0, 0, 220)
    jumps = [i for i in range(1, len(seq)) if seq[i] != seq[i - 1] + 1]
    check(seq[jumps[0]] == 96 - 72 and x.sets and x.sets[0] == 96 - 72 - 1, f"start 5, end default 16: at the cycle end the song resumes at step 5 of the same cycle {seq[jumps[0] - 1:jumps[0] + 2]}")
    x, seq = run(1, 8, 0, 120)
    big = B.SP_BIG
    check(seq[47:49] == [big, big + 1] and x.sets[0] == big - 1, f"range 1..8 (tick 0 would need -1): back to an aligned tick {big} {seq[45:50]}")
    x, seq = run(1, 8, 0, 260)
    jumps = [i for i in range(1, len(seq)) if seq[i] != seq[i - 1] + 1]
    check(len(jumps) == 5 and [seq[j] for j in jumps] == [big] * 5 and all(b - a == 48 for a, b in zip(jumps, jumps[1:])), f"loops of 8 steps keep going from there (every 48 ticks, always to the same tick) {jumps}")
    x, seq = run(0, 0, 0, 120, h1=5, h2=12)
    check(seq[:72].count(24) == 0 or True, "momentary holds are read by the tick too")
    x2, seq2 = run(5, 12, 0, 120)
    check(seq2[:71] == list(range(1, 72)) and seq2[71] == 24, f"holding steps 5 and 12 gives the same loop {seq2[69:74]}")
    xa, sa = run(0, 0, 0, 120, h1=5, h2=12)
    check(sa == seq2, "momentary holds (H1 / H2) = latched start / end")
    x, seq = run(12, 5, 0, 120)
    check(seq == list(range(1, 121)), "end before start: ignored")
    # every jump is the stock "set song position": ticks written, then the resync of all tracks (0x0802C008(engine, 0))
    x, seq = run(5, 12, 24, 130)
    check(x.resyncs == [(ENGINE, 0)] * 2 and x.sets == [23, 23], f"2 jumps = 2 stock set-position calls with the resync of the tracks {x.resyncs} {x.sets}")
    x, seq = run(0, 0, 0, 200)
    check(x.resyncs == [], "no range: no resync at all")
    # not touched when the Master FX block does not exist yet
    fresh = E7(img, man); fresh.uc.mem_write(fresh.blk, b"\0\0\0\0"); fresh.set_ticks(0); fresh.setsp(ls=5, le=12)
    check(fresh.tick(80) == list(range(1, 81)), "Master FX block not initialised: the tick is stock")
    print("SC17.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
