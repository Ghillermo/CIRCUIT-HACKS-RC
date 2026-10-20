"""SC45.3 / RC2.04 ARM tests: recfix (a note held past 16 steps), smhold (the picker: a sample held, then a step) and, where the build has them,
arp.use_pressord() / use_mutarp().

    python tools/emu_sc45_3.py BUILD.bin BUILD_manifest.json [OLD.bin OLD_manifest.json]
  * recfix: the stock's note writer of Synth 1's recorder (0x0803F7BE: called when a note is let go, the note's entry word set by hand: step,
    pattern, velocity, start tick, micro step), the pattern at 6 ticks a step: 10 steps = one unit (gate 60); 20 steps + 3 ticks = 96 tied +
    the same note 16 steps later (gate 27, its micro step / velocity); 40 steps in 32 = 96 tied at 3, 96 at 19, nothing past the start; a pattern
    of 16 = only the stock's 96; 24 steps from step 11 = the rest at step 3 (wrapped); a unit of the same note there is reused; no free unit =
    no tie.  (The build before: 96 and nothing else.)
  * smhold: MIDI 1 in the sample mode, its picker (Note twice): sample pad held + step 4 = step 4's flip; the step held + a sample still works;
    Clear held: the step loses its flip, the held sample does not flip it; the sample let go: a step is only held.
  * pressord: the input's list (c_arins / c_ardel on the live state): pressed 64, 60, 67 = that order; 60 let go and 72 pressed = 72 in its
    place; a fifth note at the end; the sequence: a chord's units in their order (up = 64, 60, 67; down reversed).
  * mutarp: a chord step with random-mutate level 7: its arpeggio plays other notes too (level 0: only the chord's).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R1, UC_ARM_REG_R3
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc40_8 as T8  # noqa: E402
import arp as A  # noqa: E402

REC, WRITER = 0x2003C168, 0x0803F7BE
NOTE = 60


def recfix_part(img, man):
    e = T8.E8(img, man, {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()})
    rec = e.r32(REC + 0xC); pb = e.r32(rec + 0x48)
    def setup(last, first=0, extra=None):
        for s in range(32): e.uc.mem_write(pb + 28 * s, bytes([0, 7, 0, 0]) + bytes([0, 0, 0, 0x60]) * 6)
        e.uc.mem_write(pb + 0x380, bytes([last, first, 3]))
        if extra: extra()
    def write(step, steps, ticks=0, micro=1, vel=100, start=100):
        e.w32(rec + 0x9C + 4 * NOTE, 0 | step << 3 | 0 << 8 | vel << 11 | start << 18 | micro << 29)
        e.call(WRITER, rec, NOTE, start + 6 * steps + ticks, maxins=4_000_000)
        out = {}
        for s in range(32):
            st = bytes(e.uc.mem_read(pb + 28 * s, 28))
            us = [tuple(st[4 + 4 * u:8 + 4 * u]) for u in range(6) if st[0] >> u & 1]
            if us: out[s] = us
        return out
    r = {}
    setup(31); r["10"] = write(2, 10)
    setup(31); r["20"] = write(2, 20, 3)
    setup(31); r["40"] = write(2, 40)
    setup(15); r["p16"] = write(2, 20)
    setup(23); r["p24"] = write(10, 24)
    def same(): e.uc.mem_write(pb + 28 * 18, bytes([1 << 2, 7, 0, 0]) + bytes([0, 0, 0, 0x60]) * 2 + bytes([NOTE, 12, 4, 50]) + bytes([0, 0, 0, 0x60]) * 3)
    setup(31, extra=same); r["reuse"] = write(2, 20, 3)
    def full(): e.uc.mem_write(pb + 28 * 18, bytes([0x3F, 7, 0, 0]) + b"".join(bytes([40 + u, 6, 0, 90]) for u in range(6)))
    setup(31, extra=full); r["full"] = write(2, 20, 3)
    del e; gc.collect()
    return r


def main(img, man, old=None, man_old=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    T = 0x80
    # ---- recfix
    r = recfix_part(img, man)
    check(r["10"] == {2: [(NOTE, 60, 1, 100)]}, f"10 steps: one unit, gate 60 ({r['10']})")
    check(r["20"] == {2: [(NOTE, 96 | T, 1, 100)], 18: [(NOTE, 27, 1, 100)]}, f"20 steps + 3 ticks: 96 tied at step 3, the rest (27) at step 19 ({r['20']})")
    check(r["40"] == {2: [(NOTE, 96 | T, 1, 100)], 18: [(NOTE, 96, 1, 100)]}, f"40 steps in a pattern of 32: 96 tied, 96, nothing past the start ({r['40']})")
    check(r["p16"] == {2: [(NOTE, 96, 1, 100)]}, f"a pattern of 16: only the stock's 96 ({r['p16']})")
    check(r["p24"] == {10: [(NOTE, 96 | T, 1, 100)], 2: [(NOTE, 48, 1, 100)]}, f"24 steps from step 11 in a pattern of 24: the rest at step 3 ({r['p24']})")
    check(r["reuse"].get(18) == [(NOTE, 27, 1, 100)] and r["reuse"].get(2) == [(NOTE, 96 | T, 1, 100)], f"the note already at step 19: that unit reused ({r['reuse']})")
    check(r["full"].get(2) == [(NOTE, 96, 1, 100)] and len(r["full"].get(18, [])) == 6 and all(u[0] != NOTE for u in r["full"][18]),
          f"step 19 full: no tie, nothing written there ({r['full'].get(2)})")
    if old is not None:
        o = recfix_part(old, man_old)
        check(o["20"] == {2: [(NOTE, 96, 1, 100)]}, f"the build before: 20 steps = 96 and nothing else ({o['20']})")
    # ---- smhold
    import emu_sc42_6 as X
    import emu_sc22_4 as T4  # noqa: F401
    import smpick as SP
    from emu_sc17_6 import PRESS, RELEASE
    V = T4.V
    e = X.EP(img, man)
    sl = {k: int(v, 16) for k, v in R["smpick"]["labels"].items()}
    def skip(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    for f in (SP.REC_ON, SP.REC_OFF): e.uc.hook_add(UC_HOOK_CODE, skip, begin=f, end=f)
    lane = lambda step: bytes(e.uc.mem_read(e.r0(sl["c_splb"], 0, step), 6))
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    for _ in range(10): e.at(e.t + 40); e.call(e.vl["c_vtick"], maxins=3_000_000)
    e.btn(2); e.btn(8)
    if "modesel" in R: e.pad(26); e.pad(16 + 5); e.pad(26)
    else:
        for _ in range(3): e.pad(26)
    for _ in range(3):
        if e.r8(X.MGR + SP.S_CUR) == SP.PICK[0]: break
        e.btn(9)
    check(e.r0(sl["c_spk"]) == 0, f"MIDI 1 in the sample mode, its picker on the screen (c_spk {e.r0(sl['c_spk'])})")
    for s in (3, 5, 6, 7): e.uc.mem_write(e.r0(sl["c_splb"], 0, s), b"\xff" * 6)
    e.call(PRESS, X.MGR, 16 + 7, 90, maxins=8_000_000); e.call(PRESS, X.MGR, 3, 100, maxins=8_000_000)
    e.call(RELEASE, X.MGR, 3, maxins=8_000_000); e.call(PRESS, X.MGR, 5, 100, maxins=8_000_000); e.call(RELEASE, X.MGR, 5, maxins=8_000_000)
    e.call(RELEASE, X.MGR, 16 + 7, maxins=8_000_000)
    check(lane(3) == bytes([0x80 | 7]) * 6 and lane(5) == bytes([0x80 | 7]) * 6 and e.val(0, 25) == 7,
          f"sample 8 held + steps 4 and 6: their flips ({lane(3).hex()}, {lane(5).hex()}); the track's sample = 7 ({e.val(0, 25)})")
    e.pad(6)
    check(lane(6) == b"\xff" * 6, f"the sample let go: a step tap flips nothing ({lane(6).hex()})")
    e.call(PRESS, X.MGR, 7, 100, maxins=8_000_000); e.pad(16 + 2); e.call(RELEASE, X.MGR, 7, maxins=8_000_000)
    check(lane(7) == bytes([0x80 | 2]) * 6, f"step 8 held + sample 3: its flip as before ({lane(7).hex()})")
    clr = e.r32(e.r32(X.MGR + SP.HELD) + 0xC)
    e.call(PRESS, X.MGR, 16 + 9, 90, maxins=8_000_000); e.set_p0(clr, 1); e.pad(3); e.set_p0(clr, 0); e.call(RELEASE, X.MGR, 16 + 9, maxins=8_000_000)
    check(lane(3) == b"\xff" * 6, f"a sample held + Clear + step 4: the flip cleared, not set ({lane(3).hex()})")
    st = e.r8(e.r0(sl["c_spst"]))
    check(st >> 3 == 0, f"nothing left held ({st:#x})")
    del e; gc.collect()
    # ---- the arpeggiator
    if "c_armut" in R["arp"]["labels"] or "c_arins_old" in R["arp"]["labels"]:
        import emu_arp as EA_
        e = EA_.EA(img, man)
        e.call(e.A["c_arst"], 0, 1); st = e.uc.reg_read(UC_ARM_REG_R0)
        lst = lambda: [e.r8(st + A.S_NOTES + i) for i in range(e.r8(st + A.S_N))]
        pos = lambda: [e.r8(st + A.D_POS + i) for i in range(e.r8(st + A.S_N))]
        for n in (64, 60, 67): e.call(e.A["c_arins"], st, n, 100, 6)
        a1 = lst()
        e.call(e.A["c_ardel"], st, 60); a2, p2 = lst(), pos()
        e.call(e.A["c_arins"], st, 72, 100, 6); a3, p3 = lst(), pos()
        e.call(e.A["c_arins"], st, 50, 100, 6); a4 = lst()
        e.call(e.A["c_ardel"], st, 64); e.call(e.A["c_ardel"], st, 72); e.call(e.A["c_arins"], st, 40, 100, 6); e.call(e.A["c_arins"], st, 41, 100, 6)
        a5, p5 = lst(), pos()
        check(a1 == [64, 60, 67] and a2 == [64, 67] and p2 == [0, 2] and a3 == [64, 72, 67] and p3 == [0, 1, 2] and a4 == [64, 72, 67, 50],
              f"pressed 64 60 67 = {a1}; 60 let go = {a2} (places {p2}); 72 takes its place = {a3}; 50 at the end = {a4}")
        check(a5 == [40, 41, 67, 50] and p5 == [0, 1, 2, 3], f"64 and 72 let go, 40 and 41 pressed: the two empty places first ({a5}, {p5})")
        del e; gc.collect()
        chord = [(64, 18, 0, 100), (60, 18, 0, 90), (67, 12, 0, 80)]
        def seq(setting, units=chord, steps=5, level=0):
            e = EA_.EA(img, man)
            p = e.playing(0); base = e.settings(0, p) - 0x380
            raw = bytearray(EA_.chord_steps(units)); raw[2] = level
            e.uc.mem_write(base, bytes(raw)); e.setpat(0, p, 0, 7)
            e.setp(e.r32(EA_.PLAYER + 0x10), 1, bytes([3]))
            e.call(e.A["c_arset"], 0, p, setting)
            e.transport(1); e.ons.clear(); e.run(p, steps)
            out = [n for t, n, v, d in e.ons]; del e; gc.collect(); return out
        up, dn = seq(0x80 | A.M_UP), seq(0x80 | A.M_DOWN)
        check(up == [64, 60, 67] and dn == [67, 60, 64], f"a step's chord in its units' order: up {up}, down {dn}")
        if "c_armut" in R["arp"]["labels"]:
            long_ = [(64, 96, 0, 100), (60, 96, 0, 90), (67, 96, 0, 80)]
            m0, m7 = seq(0x80 | A.M_UP, long_, 16, 0), seq(0x80 | A.M_UP, long_, 16, 7)
            check(len(m0) == 16 and set(m0) == {60, 64, 67} and len(m7) == 16 and set(m7) - {60, 64, 67},
                  f"random-mutate on the chord's step: level 0 = the chord's notes ({m0}); level 7 = others too ({m7})")
    if "c_armutL" in R["arp"]["labels"]:
        import emu_arp as EA_
        def live(level, playing):
            e = EA_.EA(img, man)
            p = e.playing(0); base = e.settings(0, p) - 0x380
            e.uc.mem_write(base, EA_.chord_steps([]))
            e.uc.mem_write(base + 28 * 5 + 2, bytes([level]))
            e.setp(e.r32(A.ENG + 0x30), 1, bytes([5]))                                  # the track on step 6
            e.call(e.A["c_arset"], 0, p, 0x80 | A.M_UP)
            e.call(e.A["c_arst"], 0, 1); st = e.uc.reg_read(UC_ARM_REG_R0)
            for n in (64, 60, 67): e.call(e.A["c_arins"], st, n, 100, 6)
            e.uc.mem_write(st + A.S_FL, bytes([1])); e.uc.mem_write(st + A.S_PEND, bytes([0xFF]))
            e.transport(1 if playing else 0); e.ons.clear(); e.ifc.clear()
            for _ in range(16): e.call(e.A["c_arlstep"], 0, 1 if playing else 0, maxins=4_000_000)
            out = [n for _, n, _, _ in e.ons] if playing else [n for k, _, n in e.ifc if k == "on"]
            del e; gc.collect(); return out
        l0, l7, s7 = live(0, True), live(7, True), live(7, False)
        check(len(l0) == 16 and set(l0) == {60, 64, 67}, f"live arpeggio, the track's step at level 0: the held notes ({l0})")
        check(len(l7) == 16 and set(l7) - {60, 64, 67}, f"live, the track's step at level 7: other notes too ({l7})")
        check(len(s7) == 16 and set(s7) - {60, 64, 67}, f"live, stopped, the step it stands on at level 7: other notes too ({s7})")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    old = Path(a[3]).read_bytes() if len(a) > 4 else None
    mo = json.loads(Path(a[4]).read_text()) if len(a) > 4 else None
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), old, mo) else 0)
