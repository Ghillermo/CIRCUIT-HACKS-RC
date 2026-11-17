"""RC4.13 / SC57.7 test (arp.use_tmfix): an armed arpeggio note is played by the main loop OUTSIDE the DSP service's lock.

    python tools/emu_armain_lock.py NEW.bin NEW_manifest.json [PREV.bin PREV_manifest.json]

Beta 5.61 / RC4.12 (arp.use_timed) hung the unit a moment after Play (the user, 2026-11-14): c_armain sat in place of the main loop's call of the
DSP service (0x0801D5D8), after the main loop takes the service's lock (0x08021064 at 0x0801D5D4), and the note's sound path (the note interface
0x0801D38E -> 0x0803BD58 / 0x0803BD94) takes that lock again: on the device it waits for ever.  The old test (emu_arptime) skipped the note-on and
the interface, so it never saw it.

Here the note-on (0x08040FA2) and the note interface run for real; Synth 1's player is ticked as in emu_arptime (1/32 arpeggio on a 1/8 track: notes
armed between micro steps) and, every ms, the main loop's own code runs from 0x0801D5CA to 0x0801D602 (the lock taken, the service (skipped), the lock
given back, the instruction pair at 0x0801D5FE).  A take of the lock while the main loop holds it = the hang.
  * NEW: armed notes played (note-ons from the main loop), no take while held, the main loop's stretch always reaches 0x0801D602 (a pass that
    plays a note stops in the DSP read's wait, 0x08029344: in emulation the DSP never answers);
  * PREV (optional, e.g. Beta 5.61): the takes while held are reported (expected: the hang).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R1, UC_ARM_REG_R7, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arp as A  # noqa: E402

REAL_NOTE_ON = A.NOTE_ON
LOOP_FROM, LOOP_TO = 0x0801D5CA, 0x0801D602                   # the main loop: the lock, the service, the lock back, mov r0, r7; ldr r0, [r0]
TAKE, MAIN_TAKE_LR, RELEASE_AT, IFC_ON = 0x08021064, 0x0801D5D9, 0x0801D5DC, 0x0801D38E
DSPR_LO, DSPR_HI = 0x08029344, 0x080293A0                    # the stock's DSP read (0x08029344): its wait for the DSP's answer
FLAGS = 0x2006E800                                            # r7: the main loop's flags word (0: the service runs)


def run(img, man):
    import emu_arp as EAM
    A.NOTE_ON, EAM.IFC_ON, EAM.IFC_OFF = 0x0807FFF0, 0x0807FFE0, 0x0807FFE8   # the harness's skips go nowhere: the real note path runs
    try:
        e = EAM.EA(img, man)
    finally:
        A.NOTE_ON, EAM.IFC_ON, EAM.IFC_OFF = REAL_NOTE_ON, 0x0801D38E, 0x0801D942
    A_ = e.A
    st_ = dict(held=False, ctx="tick", nested=[], ons=[], loops=0, short=0, dspwait=0)
    def take(uc, a, s, d):
        lr = uc.reg_read(UC_ARM_REG_LR)
        if lr == MAIN_TAKE_LR: st_["held"] = True
        elif st_["held"]:
            st_["nested"].append(hex(lr)); uc.reg_write(UC_ARM_REG_PC, lr | 1)   # (on the device: for ever)
    e.uc.hook_add(UC_HOOK_CODE, take, begin=TAKE, end=TAKE)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: st_.update(held=False), begin=RELEASE_AT, end=RELEASE_AT)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1), begin=A.SVC, end=A.SVC)
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: st_["ons"].append((st_["ctx"], uc.reg_read(UC_ARM_REG_R1))), begin=REAL_NOTE_ON, end=REAL_NOTE_ON)
    e.w32(FLAGS, 0)
    p = e.playing(0); base = e.settings(0, p) - 0x380
    e.uc.mem_write(base, EAM.chord_steps([(64, 6 * 4, 0, 100), (60, 6 * 4, 0, 90), (67, 6 * 4, 0, 80)]))
    e.setpat(0, p, 0, 7); e.setp(e.r32(EAM.PLAYER + 0x10), 1, bytes([5])); e.setp(A.TEMPO, 0, bytes([120]))
    e.call(A_["c_arset"], 0, p, 0x80 | 2 << 3 | A.M_UP); e.transport(1)
    st = e.r32(A.ENG + 0x30); e.setp(st, 0, bytes([p]))
    t0, tick_ms = 100000, 2500 / 120
    for s in range(3):
        e.setp(st, 1, bytes([s]))
        for t in range(12):
            n = s * 12 + t; now = t0 + int(n * tick_ms)
            e.w32(A.HAL_TICK, now); e.w32(EAM.TICK_HOLD, now); e.setp(st, 2, struct.pack("<I", t))
            st_["ctx"] = "tick"
            e.call(EAM.TICK_BUILD, EAM.PLAYER, maxins=3_000_000); e.call(EAM.TICK_PLAY, EAM.PLAYER, maxins=3_000_000)
            st_["ctx"] = "main loop"
            for ms in range(now, t0 + int((n + 1) * tick_ms)):
                e.w32(A.HAL_TICK, ms); e.w32(EAM.TICK_HOLD, ms)
                sp = e.uc.reg_read(UC_ARM_REG_SP)
                e.uc.reg_write(UC_ARM_REG_R7, FLAGS)
                e.uc.emu_start(LOOP_FROM | 1, LOOP_TO, count=3_000_000)
                pc_ = e.uc.reg_read(UC_ARM_REG_PC); st_["loops"] += 1
                if pc_ != LOOP_TO:
                    if DSPR_LO <= pc_ < DSPR_HI: st_["dspwait"] += 1       # the DSP read's wait: in emulation the DSP never answers
                    else: st_["short"] += 1; st_.setdefault("where", []).append(hex(pc_))
                e.uc.reg_write(UC_ARM_REG_SP, sp)
    del e; gc.collect()
    return st_


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    main_ons = [n for c, n in r["ons"] if c == "main loop"]
    check(len(main_ons) >= 3, f"armed notes played by the main loop ({len(main_ons)} note-ons there, {len(r['ons'])} in all)")
    check(not r["nested"], f"no take of the DSP service's lock while the main loop holds it ({r['nested'][:6]})")
    check(r["loops"] > 0 and r["short"] == 0, f"the main loop's stretch ran to its end every ms, but for the DSP read's wait that never ends in "
          f"emulation ({r['loops']} passes, {r['dspwait']} in that wait, other stops {r.get('where', [])[:4]})")
    if prev is not None:
        q = run(prev, pman)
        print(f"      previous build: {len(q['nested'])} takes while held ({sorted(set(q['nested']))[:4]}) = the hang on the device")
        check(len(q["nested"]) > 0, "the test catches the previous build's hang")
    print(f"{man.get('marker', '?')} ARMAIN LOCK RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a_ = [Path(x) for x in sys.argv[1:5]]
    args = [a_[0].read_bytes(), json.loads(a_[1].read_text())]
    if len(a_) == 4: args += [a_[2].read_bytes(), json.loads(a_[3].read_text())]
    sys.exit(1 if main(*args) else 0)
