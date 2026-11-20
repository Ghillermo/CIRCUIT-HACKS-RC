"""Alpha 7.12 test (tools/packsave.py): Save, then an empty pack pad in the packs view = the loaded pack copied there, the loaded project saved into
the copy, the new pack loaded, the project number kept.  Through the controller (Save = button 25, the pad by 0x08033282) and the real LED task;
the stock's far ends are stood in for (no storage task in emulation): the duplicate request and the project-load request (0x0803C68C on those two
sinks), the save (0x0802FDF8: the pack it would post = p0 of 0x200111CC at the call), the pack load's commit, the blink timer.
  * Save armed: the empty pads yellow on the frame (pad 21 = pack 20), a pack's pad not;
  * Save + pad 21: the duplicate request (pack 20), Save disarmed, the black box's heartbeat 0, Save white while it runs, every pad swallowed;
  * until the new pack's colour is set nothing more; then the save of the loaded project with p0 = 20 for the call, p0 back to 31 after;
  * then the pack load (the packs view's load store = 20); once loaded with another project, that project loaded again (3);
  * Save + a pack's pad / the loaded pack / the internal pack = nothing, Save red; Save not armed = the stock's pad; Clear = the heartbeat 0.

    python tools/emu_packsave.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, set_loaded, MGR, TICK, PVIEW_OBJ  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc17_7 import VIEW7_PRESS  # noqa: E402
import packsave as PS  # noqa: E402
import blackbox as BX  # noqa: E402
import unicorn  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_LR, UC_ARM_REG_PC  # noqa: E402

GET, WPTR, COMMIT = PS.GET, PS.WPTR, PS.COMMIT
STATE, BUSY = 0x200111CC, 0x2000FE70


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E35(img, man)
    r0 = lambda fn, *a: (e.call(fn, *a, maxins=900000), e.uc.reg_read(UC_ARM_REG_R0))[1]
    byte = lambda st, k: e.r8(r0(GET, st, k))
    def raw(st, k, v):                               # both copies, no commit (the loaded pack's store: its listeners would reload in emulation)
        for o in (0xC, 0x10): e.uc.mem_write(e.r32(st + o) + 4 * k, bytes([v]))
    def put(st, k, v):                               # both copies (in emulation no task copies one into the other)
        p = r0(WPTR, st, k); e.uc.mem_write(p, bytes([v])); e.call(COMMIT, st, maxins=900000); e.uc.mem_write(r0(GET, st, k), bytes([v]))
    set_loaded(e, man, 31)
    e.btn(26, shift=True)
    check(e.r32(MGR + 0x6C) == PVIEW_OBJ, "Shift + Projects: the packs view")
    e.set_p0(e.r32(PVIEW_OBJ + 0xC), byte(e.r32(PVIEW_OBJ + 0xC), 0) | 1)
    cols = e.r32(PVIEW_OBJ + 0x14)
    put(cols, 20, 0xFF); put(cols, 29, 3)
    put(STATE, 8, 3)                                 # the loaded project: 3
    dup_sink, proj_sink, load_st = e.r32(PVIEW_OBJ + 0x20), e.r32(PS.PJ + 0xC), e.r32(PVIEW_OBJ + 0x18)
    log = []
    def ret(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    def h_sink(uc, a, s, d):
        r = [uc.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        if r[0] in (dup_sink, proj_sink): log.append(("dup" if r[0] == dup_sink else "proj", r[1])); uc.reg_write(UC_ARM_REG_R0, 0); ret(uc)
    def h_save(uc, a, s, d):
        p = r0_raw(uc)
        log.append(("save", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), p)); ret(uc)
    def r0_raw(uc):                                  # p0 of 0x200111CC's read copy, without running code
        w4 = struct.unpack("<I", bytes(uc.mem_read(STATE + 4, 4)))[0]; sel = w4 & 1
        base = struct.unpack("<I", bytes(uc.mem_read(STATE + 0xC + 4 * sel, 4)))[0]
        return uc.mem_read(base, 1)[0]
    def h_commit(uc, a, s, d):
        if uc.reg_read(UC_ARM_REG_R0) == load_st:
            w4 = struct.unpack("<I", bytes(uc.mem_read(load_st + 4, 4)))[0]; w8 = struct.unpack("<I", bytes(uc.mem_read(load_st + 8, 4)))[0]
            sel = (w4 ^ w8) & 1; base = struct.unpack("<I", bytes(uc.mem_read(load_st + 0xC + 4 * sel, 4)))[0]
            log.append(("load", uc.mem_read(base, 1)[0])); ret(uc)
    def h_timer(uc, a, s, d): log.append(("timer", uc.reg_read(UC_ARM_REG_R2))); ret(uc)
    e.uc.hook_add(unicorn.UC_HOOK_CODE, h_sink, begin=PS.SINK, end=PS.SINK)
    e.uc.hook_add(unicorn.UC_HOOK_CODE, h_save, begin=PS.SAVE_FN, end=PS.SAVE_FN)
    e.uc.hook_add(unicorn.UC_HOOK_CODE, h_commit, begin=COMMIT, end=COMMIT)
    e.uc.hook_add(unicorn.UC_HOOK_CODE, h_timer, begin=PS.TIMER, end=PS.TIMER)
    def frame():
        from emu_sc05 import STOP
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=5_000_000)
        return struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138)))
    pad = lambda p_: (e.call(PRESS, MGR, p_, 100, maxins=3_000_000), e.call(RELEASE, MGR, p_, maxins=900000))
    btn = lambda b_: (e.call(0x08033320, MGR, b_, maxins=900000), e.call(0x0803381A, MGR, b_, maxins=900000))
    armed = lambda: byte(e.r32(PS.PJ + 0x2C), 0)
    st = lambda: e.r8(PS.RAM + PS.O_ST)
    bbnow = BX.BB + BX.O.NOW
    e.w32(TICK, 100000)

    e.seen.clear(); pad(29)
    check(any(s[0] == VIEW7_PRESS for s in e.seen) and not log, "Save not armed: a pad is the stock's")
    btn(25)
    check(armed() == 1, "Save (button 25): armed")
    f = frame()
    check(f[20] == PS.YELLOW and f[29] != PS.YELLOW, f"Save armed in the packs view: empty pad 21 yellow, pack 29 not ({f[20]:#x}, {f[29]:#x})")
    e.w32(bbnow, 99999); e.seen.clear(); log.clear()
    pad(20)
    check(log[:2] == [("dup", 20), ("timer", 500)], f"Save + pad 21: the duplicate request for pack 20 and the blink ({log})")
    check(armed() == 0 and st() == 1 and e.r32(bbnow) == 0 and not any(s[0] == VIEW7_PRESS for s in e.seen),
          f"Save disarmed, step 1, the black box's heartbeat 0, the stock's pad not reached (st {st()}, now {e.r32(bbnow)})")
    log.clear(); f = frame()
    check(not log and f[PS.LED_SAVE] == PS.WHITE and st() == 1, f"the new pack not rescanned yet: nothing; Save white ({f[PS.LED_SAVE]:#x})")
    e.seen.clear(); pad(29)
    check(not any(s[0] == VIEW7_PRESS for s in e.seen) and not log, "while it runs a pad is swallowed")
    put(cols, 20, 5); log.clear(); frame()
    sv = [x for x in log if x[0] == "save"]
    check(len(sv) == 1 and sv[0][1] == PS.G and sv[0][2] == 3 and sv[0][4] == 20, f"rescanned: the save of project 3 into pack 20 ({sv})")
    check(byte(STATE, 0) == 31 and st() == 2, f"after the call the loaded pack is 31 again; step 2 ({byte(STATE, 0)}, {st()})")
    put(BUSY, 1, 2); log.clear(); frame()
    check(not log and st() == 2, "the save in flight: wait")
    put(BUSY, 1, 0); log.clear(); frame()
    check(("load", 20) in log and st() == 3, f"the save done: pack 20 loaded ({log})")
    log.clear(); frame()
    check(not log and st() == 3, "not loaded yet: wait")
    raw(STATE, 0, 20); raw(STATE, 8, 0); log.clear(); f = frame()
    lp = [x for x in log if x[0] == "proj"]
    check(len(lp) == 1 and lp[0][1] & 0x3F == 3 and st() == 0, f"loaded with project 1: project 3 loaded again; done ({lp})")
    check(f[PS.LED_SAVE] != PS.WHITE, "done: Save no longer white")
    # refusals
    set_loaded(e, man, 31)
    for p_, why in ((29, "a pack's pad"), (31, "the loaded pack"), (0, "the internal pack")):
        btn(25); log.clear(); e.w32(TICK, 200000 + 10000 * p_); pad(p_); f = frame()
        check(not log and st() == 0 and armed() == 0 and f[PS.LED_SAVE] == PS.RED, f"Save + {why}: nothing, Save red ({log}, {f[PS.LED_SAVE]:#x})")
    e.w32(TICK, 900000); f = frame()
    check(f[PS.LED_SAVE] != PS.RED, f"1.5 s later: Save not red ({f[PS.LED_SAVE]:#x}, TF {e.r32(PS.RAM + PS.O_TF)})")
    e.w32(bbnow, 12345); e.call(0x08033320, MGR, 23, maxins=900000); e.call(0x0803381A, MGR, 23, maxins=900000)
    check(e.r32(bbnow) == 0, "Clear (a delete may follow): the black box's heartbeat 0")
    print(f"{man.get('marker', '?')} PACKSAVE RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
