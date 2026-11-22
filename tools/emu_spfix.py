"""Alpha 7.27 test (build_sc17.use_spfix): the song pointer on the real clock path (the stock clock handler 0x0802B886, which ticks or, after a
reposition, replays the position; the stock's SET_TICKS for real: emu_sc17_7.E7's stub dropped), each track's build / play calls after it:
  * phrase 5..8: every loop exactly 24 clocks, no clock that replays instead of ticking, the reposition flag (engine + 0xA4) never left set,
    the playhead cache = the step that plays on the loop clock;
  * a held step (retrigger): repeated every 6 clocks, no replays.
    python tools/emu_spfix.py firmware/a7.27      (Alpha 7.26 fails: one clock lost per jump)
"""
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import unicorn
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
import emu_sc48_8 as S
import emu_arp as EAm
import jumpseq as J
import arp as A
import build_sc17 as B17

ENG, SET_TICKS, CLOCK = J.ENG, 0x0802BFE0, 0x0802B886
PLAYERS = [J.PLAYER0 + J.PLAYER_SZ * t for t in range(4)] + [0x20040810 + 0x90 * d for d in range(4)]


def make(d):
    d = Path(d); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    ha = unicorn.Uc.hook_add
    def hk(self, htype, cb, user_data=None, begin=1, end=0, *a, **k):        # E7's SET_TICKS stub out: the real routine runs
        if begin == SET_TICKS and end == SET_TICKS and getattr(cb, "__qualname__", "").startswith("E7."): return 0
        return ha(self, htype, cb, user_data, begin, end, *a, **k)
    unicorn.Uc.hook_add = hk
    try: e = S.ET(img, man)
    finally: unicorn.Uc.hook_add = ha
    return e, man["report"]


def run(d, ls, le, n, held=0):
    e, R = make(d)
    t = [500000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    at(0)
    e.call(int(R["sc17"]["labels"]["c_gfst"], 16), maxins=400000); blk = e.uc.reg_read(UC_ARM_REG_R0)
    sets = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, dd: sets.append(uc.reg_read(UC_ARM_REG_R1)), begin=SET_TICKS, end=SET_TICKS)
    for k in range(8):
        st = e.r32(ENG + 0x50 + 4 * k)
        EAm.EA.setp(e, st, 0, bytes([15, 0])); EAm.EA.setp(e, st, 1, bytes([3])); EAm.EA.setp(e, st, 2, bytes([0]))
    ticks = lambda: e.r32(e.ptr(e.r32(ENG + 0x90), 0))
    e.uc.mem_write(blk - B17.GFX_OFF + 21, bytes([ls, le, 0])); e.uc.mem_write(blk + 31, bytes([0]))
    e.transport(0)
    for k in range(8):
        st = e.r32(ENG + 0x30 + 4 * k)
        EAm.EA.setp(e, st, 1, bytes([0])); EAm.EA.setp(e, st, 2, struct.pack("<I", 5))
        EAm.EA.setp(e, e.r32(ENG + 0x70 + 4 * k), 1, bytes([0]))
    e.transport(1)
    log = []
    for i in range(n):
        if held and i == 30: e.uc.mem_write(blk + B17.S_JT, bytes([held | 0x40]))
        at(21); n0 = len(sets)
        e.call(CLOCK, ENG, e.r32(ENG + 0x14) + 0xC, 0, maxins=8_000_000)
        for o in (0x14, 0x18):
            for p in PLAYERS: e.call(e.r32(e.r32(p)) & ~1, p, e.r32(p + o), maxins=3_000_000)
        log.append((i, ticks(), bool(sets[n0:]), e.r8(ENG + 0xA4), e.r32(blk + B17.S_SPS) & 0xFF))
    del e; gc.collect()
    return log


def main(a):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    d = a[0]
    for name, args, period in (("phrase 5..8", (5, 8, 130), 24), ("held step 10", (0, 0, 70, 10), 6)):
        log = run(d, *args)
        jumps = [x for x in log if x[2]]
        gaps = [jumps[k][0] - jumps[k - 1][0] for k in range(1, len(jumps))]
        replays = [log[k][0] for k in range(1, len(log)) if log[k][1] != log[k - 1][1] + 1 and not log[k][2]]
        check(len(jumps) >= 3 and all(g == period for g in gaps), f"{name}: a jump every {period} clocks ({[x[0] for x in jumps]})")
        check(not replays, f"{name}: no clock replays the position instead of ticking ({replays})")
        check(not [x for x in log if x[3]], f"{name}: the reposition flag is never left set")
        check(all(x[4] == (x[1] // 6) & 15 for x in jumps), f"{name}: the playhead cache = the step that plays ({[(x[4], (x[1] // 6) & 15) for x in jumps]})")
    print("SPFIX RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
