"""SC41.8 ARM tests: the metronome's four states and the count-in (countin.py), through the controller and the real LED task call.

    python tools/emu_countin.py NEW.bin NEW_manifest.json
  * Shift + Clear walks none -> metronome -> count-in only -> both -> none: the stock's metronome parameter and our byte in the record's tail;
    with Shift held the Clear LED shows the state (yellow / green / orange / blue);
  * Record armed, Play from stopped with the count-in: nothing starts; the LED task clicks once per beat at 120 BPM (4 clicks, the stock's click
    call), Record blinks red; after the bar the transport plays (and records);
  * Play during the count cancels it; without the count-in Play starts at once; the count-in without Record armed does nothing;
  * the stock apply of a project puts the count's RAM bytes in the tail to 0 (a file with something else there starts nothing).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
import countin as CI  # noqa: E402

MGR = 0x20040B10
TICK = CI.HAL_TICK


class EC(E8):
    def __init__(self, img, man):
        super().__init__(img)
        self.L = {k: int(v, 16) for k, v in man["report"]["countin"]["labels"].items()}
        self.clicks = []
        def click(uc, a, s, d):
            self.clicks.append(self.r32(TICK)); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, click, begin=CI.CLICK, end=CI.CLICK)
        def delay(uc, a, s, d):                      # 0x0801BE78 sleep(ms): the emulated clock never advances
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, delay, begin=0x0801BE78, end=0x0801BE78)
        self.uc.hook_add(UC_HOOK_CODE, delay, begin=0x08029A00, end=0x08029A00)   # the apply's last call (an SPI transfer that waits for the hardware)
        rec = self.r32(CI.SESSION_OBJ + 0x14); assert rec
        self.tail = rec + CI.TAIL
        for i in (0, 1):                                               # 120 BPM in p0 (the tempo: SC44.8 / RC2.03) and in p1 (what SC41.8 .. RC2.02 read)
            for fn in (CI.PARAM_WPTR, 0x0803542C):
                self.call(fn, CI.TEMPO, i, maxins=200000); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([120]))

    def r0(self, fn, *a):
        self.call(fn, *a, maxins=2_000_000); return self.uc.reg_read(UC_ARM_REG_R0)
    def par(self, st, i): return self.r8(self.r0(CI.PARAM_WPTR, st, i))
    def btn(self, b, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033320, MGR, b, maxins=8_000_000); self.call(0x0803381A, MGR, b, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
    def frame(self, shift=False):
        from emu_sc05 import STOP
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138)))
    def state(self): return self.r0(self.L["c_cistate"])
    def playing(self): return self.par(CI.TRANSPORT, 0)
    def armed(self): return self.par(CI.TRANSPORT, 1)
    def set_state(self, k):
        for _ in range(4):
            if self.state() == k: return
            self.btn(CI.ID_CLEAR, shift=True)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1

    e = EC(img, man)
    e.w32(TICK, 100000)
    seq, cols = [], []
    s0 = e.state()
    for _ in range(4):
        e.btn(CI.ID_CLEAR, shift=True)
        st = e.state(); seq.append((st, e.par(CI.METRO_STORE, 3), e.r8(e.tail + CI.O_FLAG)))
        cols.append(e.frame(shift=True)[CI.LED_CLEAR])
    check(s0 == 0 and [x[0] for x in seq] == [1, 2, 3, 0], f"Shift + Clear: none -> metronome -> count-in -> both -> none ({s0}, {seq})")
    check([bool(x[1]) for x in seq] == [True, False, True, False] and [x[2] == CI.CI_ON for x in seq] == [False, True, True, False],
          "the stock's metronome parameter and the count-in byte follow the state")
    check(cols == [CI.COLS[1], CI.COLS[2], CI.COLS[3], CI.COLS[0]], f"Shift held: Clear LED = green / orange / blue / yellow ({[hex(c) for c in cols]})")

    # the count-in only, Record armed
    e.set_state(2); e.btn(16)
    check(e.armed() == 1 and e.playing() == 0, f"Record armed, stopped ({e.armed()}, {e.playing()})")
    e.clicks.clear(); e.w32(TICK, 200000); e.btn(CI.ID_PLAY)
    check(e.playing() == 0, "Play with the count-in: the transport does not start yet")
    recs, ticks = [], []
    for t in (0, 100, 300, 500, 760, 1000, 1250, 1500, 1990):
        e.w32(TICK, 200000 + t); f = e.frame(); recs.append(f[CI.LED_REC]); ticks.append((t, len(e.clicks), e.playing()))
    check([n for _, n, _ in ticks] == [1, 1, 1, 2, 2, 3, 3, 4, 4] and all(p == 0 for *_, p in ticks), f"one click per beat at 120 BPM, 4 in all ({ticks})")
    check(recs[0] == CI.COL_REC and recs[2] != CI.COL_REC and recs[3] == CI.COL_REC, f"Record blinks red ({[hex(r) for r in recs]})")
    e.w32(TICK, 202000); e.frame()
    check(e.playing() == 1 and len(e.clicks) == 4, f"after the bar: playing ({e.playing()}), armed {e.armed()}, clicks {len(e.clicks)}")
    e.w32(TICK, 203000); e.frame()
    check(len(e.clicks) == 4 and e.r32(e.tail + CI.O_T0) == 0, "no more clicks after the start")
    del e; gc.collect()

    # cancel
    e = EC(img, man); e.w32(TICK, 100000)
    e.set_state(3); e.btn(16); e.btn(CI.ID_PLAY)
    e.frame(); e.w32(TICK, 100600); e.frame()
    e.btn(CI.ID_PLAY)
    check(e.playing() == 0 and e.r32(e.tail + CI.O_T0) == 0, "Play during the count: cancelled, stopped")
    n = len(e.clicks)
    for t in (101000, 101500, 102500): e.w32(TICK, t); e.frame()
    check(len(e.clicks) == n == 2 and e.playing() == 0, f"no clicks nor start after the cancel ({n}, {len(e.clicks)})")
    e.btn(CI.ID_PLAY); e.w32(TICK, 104000); e.frame()
    check(e.r32(e.tail + CI.O_T0) != 0 and e.playing() == 0, "Play again: a new count")
    del e; gc.collect()

    # without the count-in / without Record
    e = EC(img, man); e.w32(TICK, 100000)
    e.set_state(1); e.btn(16); e.btn(CI.ID_PLAY)
    check(e.playing() == 1 and not e.clicks, "the metronome only: Play starts at once")
    del e; gc.collect()
    e = EC(img, man); e.w32(TICK, 100000)
    e.set_state(2); e.btn(CI.ID_PLAY)
    check(e.playing() == 1 and not e.clicks, "the count-in without Record armed: Play starts at once")
    del e; gc.collect()

    # a project whose tail holds something else: the stock apply (0x0802EEFE) puts the count's bytes to 0; one byte of the signature is not enough
    e = EC(img, man); e.w32(TICK, 100000)
    e.btn(16)
    e.uc.mem_write(e.tail + CI.O_FLAG, bytes([CI.CI_ON, 0x55, 0x11, 0x22, 0x33, 0x44, 1, 1]))
    check(e.state() == 0, "0xC1 without its second byte: no count-in")
    e.call(0x0802EEFE, CI.SESSION_OBJ, 1, maxins=30_000_000)
    check(e.r32(e.tail + CI.O_T0) == 0 and e.r8(e.tail + CI.O_N) == 0 and e.r8(e.tail + CI.O_PASS) == 0, "the stock apply: the count's bytes to 0")
    e.frame(); e.w32(TICK, 105000); e.frame()
    check(not e.clicks and e.playing() == 0, "nothing clicks nor starts after a load")
    del e; gc.collect()

    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
