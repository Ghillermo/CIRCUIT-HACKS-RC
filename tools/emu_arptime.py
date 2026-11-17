"""RC4.12 tests (arp.use_timed): an arpeggio note that falls between two micro steps, played at its time by the main loop.

    python tools/emu_arptime.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

Synth 1's player through the stock's per-tick calls (emu_arp), the ms clock moved tick by tick at 120 BPM (a tick = 20.83 ms) and the main loop's
call of the DSP service (c_armain, the service itself skipped) run every ms between ticks; the note-ons logged with the ms they happen at.
  * a 1/8 track with the arpeggio at 1/32 (x4: a note every 1.5 micro steps = 62.5 ms): the previous build plays them 2 and 1 micro steps apart
    (83 / 42 ms), the new one every 62.5 ms (within 2 ms), the same notes in the same order;
  * an arpeggio on the micro steps (1/16 on a 1/16 track, 1/32 on a 1/16 track) plays as before, from the sequencer, at the same ms;
  * a note armed when the transport stops is dropped, nothing armed stays.

    python tools/emu_arptime.py --ext IMG MANIFEST            (RC4.14 / Beta 5.63, arp.use_tmext)

Slaved to an external clock (bit 1 of [0x20011364 + 0x54], its measured increment at + 0x90) at 150 BPM with the project at 120, the ticks at
150 BPM: the x4 arpeggio every 50 ms within 2 ms (before use_tmext the due time used the project's 120: the notes came on the micro steps, 2 and
1 apart); with the slave bit off and the same increment: every 62.5 ms at 120 BPM ticks (the project's tempo, as before).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_arp import EA, chord_steps, PLAYER, TICK_BUILD, TICK_PLAY, TICK_HOLD  # noqa: E402
import arp as A  # noqa: E402

TICK_MS = 2500 / 120                                         # 120 BPM, 24 PPQN
CLOCK = 0x20011364                                           # (--ext) the clock object: + 0x54 bit 1 = slave, + 0x90 the measured increment


def play(img, man, sync, setting, steps, tps, stop_ms=None, ext=None):
    """-> [(ms, note)] of the note-ons, and the armed flags left.  ext = (slave, BPM): the clock's slave bit and measured tempo, the ticks at
    that BPM when slaved"""
    e = EA(img, man)
    tick_ms = TICK_MS
    if ext is not None:
        slave, bpm = ext
        e.uc.mem_write(CLOCK + 0x54, bytes([2 if slave else 0])); e.w32(CLOCK + 0x90, -(-(bpm << 32) // 0x9C4))
        if slave: tick_ms = 2500 / bpm
    A_ = e.A
    timed = "c_armain" in A_
    e.ons.clear()
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=A.SVC, end=A.SVC)
    p = e.playing(0); base = e.settings(0, p) - 0x380
    e.uc.mem_write(base, chord_steps([(64, 6 * steps, 0, 100), (60, 6 * steps, 0, 90), (67, 6 * steps, 0, 80)]))
    e.setpat(0, p, 0, 7)
    e.setp(e.r32(PLAYER + 0x10), 1, bytes([sync]))
    e.setp(A.TEMPO, 0, bytes([120]))
    e.call(A_["c_arset"], 0, p, setting)
    e.transport(1)
    st = e.r32(A.ENG + 0x30); e.setp(st, 0, bytes([p]))
    t0 = 100000
    for s in range(steps):
        e.setp(st, 1, bytes([s]))
        for t in range(tps):
            n = s * tps + t
            now = t0 + int(n * tick_ms)
            e.w32(A.HAL_TICK, now); e.w32(TICK_HOLD, now)
            e.setp(st, 2, struct.pack("<I", t))
            stopped = stop_ms is not None and now - t0 >= stop_ms
            if not stopped:                                   # stopped: the sequencer no longer ticks, the main loop goes on
                e.call(TICK_BUILD, PLAYER, maxins=3_000_000); e.call(TICK_PLAY, PLAYER, maxins=3_000_000)
            if timed:
                for ms in range(now, t0 + int((n + 1) * tick_ms)):
                    if stop_ms is not None and ms - t0 == stop_ms: e.transport(0)
                    e.w32(A.HAL_TICK, ms); e.w32(TICK_HOLD, ms); e.call(A_["c_armain"], maxins=3_000_000)
    left = []
    if timed:
        for k in (0, 1):
            e.call(A_["c_arst"], 0, k); a = e.uc.reg_read(UC_ARM_REG_R0)
            if a: left.append(e.r8(a + A.D_EXT + A.TM_FL))
    ons = [(m - t0, n) for m, n, _v, _d in e.ons]
    del e; gc.collect()
    return ons, left


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    x4 = 0x80 | 2 << 3 | A.M_UP                                # the arpeggio at 1/32 (TICKS_TAB 1: 3 ticks), up
    new, left = play(img, man, 5, x4, 4, 12)                   # a 1/8 track: 12 ticks a step, a micro step = 2 ticks
    old, _ = play(prev, pman, 5, x4, 4, 12)
    gaps = lambda L: [b[0] - a[0] for a, b in zip(L, L[1:])]
    print("      new ", [(m, n) for m, n in new][:10], gaps(new)[:10])
    print("      prev", [(m, n) for m, n in old][:10], gaps(old)[:10])
    ideal = [round(i * 3 * TICK_MS, 1) for i in range(len(new))]
    check(len(new) >= 12 and all(abs(m - i) <= 2 for (m, _), i in zip(new, ideal)),
          f"x4 (1/32 on a 1/8 track): every 62.5 ms within 2 ms ({gaps(new)[:8]})")
    check(sorted(set(gaps(old)[:8])) != sorted(set(gaps(new)[:8])) and max(gaps(old)[:8]) - min(gaps(old)[:8]) > 30,
          f"the previous build: 2 and 1 micro steps apart ({gaps(old)[:8]})")
    check([n for _, n in new] == [n for _, n in old][:len(new)] or [n for _, n in new][:len(old)] == [n for _, n in old],
          f"the same notes in the same order ({[n for _, n in new][:8]})")
    for sync, setting, tps, what in ((3, 0x80 | 4 << 3 | A.M_UP, 6, "1/16 on a 1/16 track"), (3, 0x80 | 2 << 3 | A.M_UP, 6, "1/32 on a 1/16 track")):
        a, _ = play(img, man, sync, setting, 4, tps); b, _ = play(prev, pman, sync, setting, 4, tps)
        check(a == b and len(a) >= 4, f"{what}: on the micro steps, as before ({gaps(a)[:6]})")
    st, left2 = play(img, man, 5, x4, 4, 12, stop_ms=175)          # the note due at 187.5 ms is armed at tick 8 (166.7 ms), stopped at 175
    check(all(not (f & 3) for f in left2) and [m for m, _ in st] == [m for m, _ in new][:3],
          f"the transport stopped with a note armed: dropped, nothing left ({[m for m, _ in st]}, {left2})")
    check(all(not (f & 3) for f in left), f"nothing left armed at the end ({left})")
    print(f"{man.get('marker', '?')} ARPTIME RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def main_ext(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    x4 = 0x80 | 2 << 3 | A.M_UP
    gaps = lambda L: [b[0] - a[0] for a, b in zip(L, L[1:])]
    for slave, bpm, every in ((True, 150, 3 * 2500 / 150), (True, 96, 3 * 2500 / 96), (False, 150, 3 * TICK_MS)):
        ons, left = play(img, man, 5, x4, 4, 12, ext=(slave, bpm))
        ideal = [i * every for i in range(len(ons))]
        print("      ", "slave" if slave else "not slaved", bpm, [m for m, _ in ons][:10], gaps(ons)[:10])
        check(len(ons) >= 12 and all(abs(m - i) <= 2 for (m, _), i in zip(ons, ideal)) and all(not (f & 3) for f in left),
              f"{'slaved to' if slave else 'not slaved, a clock measured at'} {bpm} BPM (project 120): x4 every {every:.1f} ms within 2 ms ({gaps(ons)[:8]})")
    print(f"{man.get('marker', '?')} ARPTIME EXT RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    if sys.argv[1] == "--ext":
        a_ = [Path(x) for x in sys.argv[2:4]]
        sys.exit(1 if main_ext(a_[0].read_bytes(), json.loads(a_[1].read_text())) else 0)
    a_ = [Path(x) for x in sys.argv[1:5]]
    sys.exit(1 if main(a_[0].read_bytes(), json.loads(a_[1].read_text()), a_[2].read_bytes(), json.loads(a_[3].read_text())) else 0)
