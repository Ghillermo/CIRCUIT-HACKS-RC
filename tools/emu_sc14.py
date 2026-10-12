"""SC14 tests: Master FX (Gater / Auto-Filter) in the FX view, main-loop LFO writes to the DSP."""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR, CONT  # noqa: E402
import build_sc14 as B  # noqa: E402

V = 0x200443B4                         # FX view


class E14(E8):
    def __init__(self, image):
        super().__init__(image)
        self.dw = []
        def h(uc, a, s, d):
            if a == 0x080292F8:
                self.dw.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            elif a == B.SVC_NEXT:        # stock DSP service tail: not under test
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, h)

    def btn(self, b, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033320, MGR, b, maxins=600000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)

    def press(self, p, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033282, MGR, p, 100, maxins=600000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)

    def release(self, p):
        self.call(0x080332CE, MGR, p, maxins=600000)

    def ms(self, t): self.w32(B.TICK, t)

    def tick(self):
        self.dw.clear()
        self.call(self.labels["c_gtick"], maxins=200000)
        return list(self.dw)

    def st(self):
        b = bytes(self.uc.mem_read(B.ST, 24))
        return dict(magic=struct.unpack_from("<I", b)[0], held=b[4], latch=b[5], gat=b[6], af=b[7],
                    lgain=b[16], lpos=b[17])

    def leds(self):
        self.call(self.r32(self.r32(V) + 0x1C), V); p = self.uc.reg_read(UC_ARM_REG_R0)
        return list(struct.unpack("<32H", bytes(self.uc.mem_read(p, 64))))


def main(stock, img, labels):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in labels.items()}
    e = E14(img); e.labels = L
    es = E14(stock)
    bpm = e.store_p0(0x20011404); beat = 60000 // bpm
    check(e.r32(B.HEAP_LIMIT_PTR) == B.HEAP_LIMIT and e.r32(B.HEAP_CUR_PTR) <= B.ST, f"heap: limit {e.r32(B.HEAP_LIMIT_PTR):#x}, current {e.r32(B.HEAP_CUR_PTR):#x}, tempo {bpm}")
    e.ms(1000); dw = e.tick()
    s = e.st()
    check(dw == [] and s["magic"] == B.MAGIC and e.r32(B.HEAP_LIMIT_PTR) == B.ST and s["gat"] == s["af"] == 0 and s["lgain"] == s["lpos"] == 0xFF,
          f"first tick: heap limit lowered to {B.ST:#x}, state initialised, nothing written")
    # stock FX view untouched
    e.btn(15); es.btn(15)
    Ls, Lp = es.leds(), e.leds()
    check(Ls[:25] == Lp[:25], "FX view: rows 1-3 and row 4 pad 1 LEDs as stock")
    check(Lp[25:29] == [B.GAT_DIM] * 4 and Lp[29:32] == [B.AF_DIM] * 3, f"row 4 pads 2-8: Gater / Auto-Filter colours {Lp[25:]}")
    for p in (0, 5, 17, 24):
        e.dw.clear(); es.dw.clear()
        e.press(p); es.press(p); e.release(p); es.release(p)
        check(e.dw == es.dw and e.leds()[:25] == es.leds()[:25], f"pad {p}: stock behaviour")
    # Gater 1/16 held
    e.ms(5000); e.press(27)
    s = e.st(); check(s["gat"] == 3 and s["held"] == 0b100, "press pad 4 (Gater 1/16): active while held")
    per = beat // 4
    seq = []
    for t in (0, 1, per // 2 - 1, per // 2, per // 2 + 3, per - 1, per, per + per // 2):
        e.ms(5000 + t); seq.append((t, e.tick()))
    exp_on, exp_off = (127 << 24, 0xDE), (0, 0xDE)
    check(seq[0][1] == [exp_on] and seq[1][1] == [] and seq[2][1] == [] and seq[3][1] == [exp_off] and seq[4][1] == []
          and seq[5][1] == [] and seq[6][1] == [exp_on] and seq[7][1] == [exp_off],
          f"Gater 1/16 at {bpm} BPM: open {per//2} ms / closed, writes X:$DE only on change {[(t, [(hex(a), hex(b)) for a, b in w]) for t, w in seq]}")
    L1 = e.leds(); check(L1[27] == B.GAT_ON and L1[25] == B.GAT_DIM, "LED: active Gater pad bright")
    e.release(27); e.ms(5000 + 2 * per + 1); dw = e.tick()
    check(e.st()["gat"] == 0 and dw == [exp_on] and e.st()["lgain"] == 0xFF, f"release: Gater off, stock gain restored {dw}")
    e.ms(5000 + 3 * per); check(e.tick() == [], "idle: no writes")
    # last pressed wins, release falls back to the other held pad
    e.ms(9000); e.press(25); e.press(28)
    check(e.st()["gat"] == 4, "pads 2 then 5 held: Gater 1/32 active")
    e.release(28); check(e.st()["gat"] == 1 and e.st()["held"] == 1, "release pad 5: back to Gater 1/4 (still held)")
    e.release(25); e.tick(); check(e.st()["gat"] == 0, "release all: off")
    # latch
    e.ms(20000); e.press(26, shift=True); e.release(26)
    s = e.st(); check(s["gat"] == 2 and s["latch"] == 0b10, "Shift + pad 3: Gater 1/8 latched, stays after release")
    e.press(26, shift=True); e.release(26); e.tick()
    s = e.st(); check(s["gat"] == 0 and s["latch"] == 0, "Shift + pad 3 again: unlatched, off")
    # Auto-Filter LP 1 bar: triangle 64 -> 8 -> 64 over 4 beats
    e.dw.clear(); e.ms(30000); e.press(29)
    pos = []
    bar = beat * 4
    for t in (0, bar // 4, bar // 2, 3 * bar // 4, bar - 1):
        e.ms(30000 + t); w = e.tick(); pos.append((t, [(a >> 24, hex(b)) for a, b in w]))
    vals = {t: w[0][0] for t, w in pos if w}
    check(vals.get(0) == 64 and abs(vals.get(bar // 4, 0) - 36) <= 1 and vals.get(bar // 2) == 8 and abs(vals.get(3 * bar // 4, 0) - 36) <= 1
          and all(x[1] == '0xcf' for _, w in pos for x in w), f"Auto-Filter LP 1 bar: 64 -> 36 -> 8 -> 36 on X:$CF {pos}")
    e.release(29); e.ms(40000); dw = e.tick()
    check(len(dw) == 1 and dw[0][1] == 0xCF and e.st()["lpos"] == 0xFF, f"release: master filter restored to the stock value {[(a >> 24, hex(b)) for a, b in dw]}")
    e.press(30); e.ms(40000 + bar // 2); w = e.tick()
    check(w and w[-1] == (120 << 24, 0xCF), f"Auto-Filter HP 1 bar: peak 120 at half bar {[(a >> 24, hex(b)) for a, b in w]}")
    e.press(31); e.ms(40000 + bar // 2 + beat // 4); w = e.tick()
    check(e.st()["af"] == 3 and w and w[-1] == (8 << 24, 0xCF), f"pad 8 (LP 1/8) takes over; restarts, bottom at 1/16 {[(a >> 24, hex(b)) for a, b in w]}")
    # Gater and Auto-Filter together
    e.press(25); e.ms(40000 + bar); w = e.tick()
    check({x[1] for x in w} == {0xDE, 0xCF}, "Gater + Auto-Filter at the same time")
    for p in (25, 30, 31): e.release(p)
    e.ms(50000); w = e.tick(); s = e.st()
    check(s["gat"] == s["af"] == 0 and {x[1] for x in w} == {0xDE, 0xCF} and s["lgain"] == s["lpos"] == 0xFF, "all released: both restored")
    # heap already used up -> disabled, nothing touched
    e2 = E14(img); e2.labels = L
    e2.w32(B.HEAP_CUR_PTR, B.ST + 4)
    e2.ms(1); w = e2.tick()
    e2.btn(15); e2.press(27); e2.ms(100); w2 = e2.tick()
    check(e2.r32(B.HEAP_LIMIT_PTR) == B.HEAP_LIMIT and w == w2 == [], "heap already past the reserve: Master FX disabled, heap untouched")
    print("SC14 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    man = json.loads(Path(sys.argv[3]).read_text())
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), man["report"]["sc14"]["labels"]) else 0)
