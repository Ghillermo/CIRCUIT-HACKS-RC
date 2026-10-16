"""SC419D tests: the stutter bench (stutdiag.py), through the real DSP service loop (0x08021392), the stock sequencer tick (0x0802C418) and the real
LED task call; the DSP's block counter (Y:$3B0F) is answered by the hooked DSP read.

    python tools/emu_stutdiag.py NEW.bin NEW_manifest.json
  * steady blocks (96 every 64 ms): nothing lights; a window with 85 % of the rate: Save red for 400 ms, one late event;
  * two service ticks 15 ms apart: Duplicate yellow, the worst gap 15 ms;
  * the sequencer's tick while playing at 120 BPM: 21 ms apart nothing, 40 ms apart Play orange; stopped: nothing;
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import stutdiag as SD  # noqa: E402

MGR = 0x20040B10


class ES(E8):
    def __init__(self, img):
        super().__init__(img)
        self.cnt = 0
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def rd(uc, a, s, d):
            if uc.reg_read(UC_ARM_REG_R1) == 0x8000 | SD.CNT_Y:
                uc.reg_write(UC_ARM_REG_R0, (self.cnt & 0xFFFFFF) << 8); skip(uc)
        self.uc.hook_add(UC_HOOK_CODE, rd, begin=SD.DSP_READ, end=SD.DSP_READ)
        for f in (0x080292F8, 0x0801BE78): self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=f, end=f)
        rec = self.r32(SD.SESSION_OBJ + 0x14); self.st = rec + SD.TAIL + SD.O_ST
    def at(self, ms): self.w32(SD.HAL_TICK, ms)
    def svc(self): self.call(0x08021392, maxins=3_000_000)
    def word(self, off): return self.r32(self.st + off)
    def leds(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        f = struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138)))
        return f[SD.LED_PLAY], f[SD.LED_DUP], f[SD.LED_SAVE]
    def setp(self, store, k, v):
        for fn in (0x080354FA, 0x0803542C):
            self.call(fn, store, k); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([v]))


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = ES(img)
    t = 100000
    for k in range(12):                                   # 2 ms service ticks, 3 blocks every 2 ms
        for i in range(32): e.at(t); e.svc(); t += 2; e.cnt += 3
    l0 = e.leds()
    check(e.word(SD.M) == SD.MAGIC and e.word(SD.N_LATE) == 0 and e.word(SD.N_GAP) == 0 and e.word(SD.RMAX) in range(1530, 1540),
          f"steady: the state made, no events, the baseline {e.word(SD.RMAX)} blocks / 1024 ms")
    check(l0 == (l0[0], l0[1], l0[2]) and SD.COL_LATE not in l0 and SD.COL_GAP != l0[1], f"steady: the indicators off ({[hex(x) for x in l0]})")
    for i in range(32):                                   # a window at 85 %
        e.at(t); e.svc(); t += 2; e.cnt += 3 if i % 7 else 0
    for i in range(3): e.at(t); e.svc(); t += 2; e.cnt += 3
    l1 = e.leds()
    check(e.word(SD.N_LATE) == 1 and l1[2] == SD.COL_LATE and e.word(SD.RMIN) < 95, f"a slow window: Save red, one late event (lowest {e.word(SD.RMIN)} %)")
    t += 500; e.at(t); l2 = e.leds()
    check(l2[2] != SD.COL_LATE, "400 ms later: Save off")
    e.at(t); e.svc(); t += 15; e.at(t); e.svc(); l3 = e.leds()
    check(e.word(SD.N_GAP) >= 1 and e.word(SD.GAPMAX) >= 15 and l3[1] == SD.COL_GAP, f"a 15 ms gap of the main loop: Duplicate yellow (worst {e.word(SD.GAPMAX)} ms)")
    # the sequencer's tick
    eng = 0x20038EC0
    e.setp(SD.TRANSPORT, 0, 1)
    t += 1000; n0 = e.word(SD.N_SEQ)
    for dt in (0, 21, 21, 20, 21):
        t += dt; e.at(t); e.call(SD.SEQ_TICK, eng, maxins=5_000_000)
    n1 = e.word(SD.N_SEQ)
    t += 40; e.at(t); e.call(SD.SEQ_TICK, eng, maxins=5_000_000); n2 = e.word(SD.N_SEQ); l4 = e.leds()
    check(n1 == n0 and n2 == n0 + 1 and l4[0] == SD.COL_SEQ, f"playing at 120 BPM: ticks 21 ms apart nothing, 40 ms apart Play orange ({n0}, {n1}, {n2})")
    e.setp(SD.TRANSPORT, 0, 0)
    t += 100; e.at(t); e.call(SD.SEQ_TICK, eng, maxins=5_000_000); t += 100; e.at(t); e.call(SD.SEQ_TICK, eng, maxins=5_000_000)
    check(e.word(SD.N_SEQ) == n2, "stopped: no sequencer events")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
