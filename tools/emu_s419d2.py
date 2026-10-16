"""S419D2 tests: the culprit of a main-loop gap (stutdiag.use_culprit), through the real service loop, the controller's knob / pad routes and the storage
API's own entries (their work answered by the harness), and the real LED task call.

    python tools/emu_s419d2.py NEW.bin NEW_manifest.json
  * a 15 ms gap with nothing of ours: Duplicate yellow; with an SD read called from the mod's code: white; from the stock's code: blue;
    with a knob event that took 6 ms: red; a pad event of 6 ms: green; a knob event of 1 ms: yellow;
  * the SC419D indicators still work (a slow block window: Save red).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_stutdiag as T  # noqa: E402
import stutdiag as SD  # noqa: E402
from thumb import bl  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402

MGR = 0x20040B10
CAVE = None                                           # code of the test in the mod's area (just after the image): bl to the storage op


class E2(T.ES):
    def __init__(self, img):
        super().__init__(img)
        global CAVE
        CAVE = (0x08010000 + len(img) + 0x1F) & ~0xF
        self.extra_ms = {}
        def sd_body(uc, a, s, d):                     # the dispatcher's work: its 9 pushed registers off, back to the caller
            sp = uc.reg_read(UC_ARM_REG_SP); lr = struct.unpack("<I", bytes(uc.mem_read(sp + 32, 4)))[0]
            uc.reg_write(UC_ARM_REG_SP, sp + 36); uc.reg_write(UC_ARM_REG_PC, lr | 1)
        self.uc.hook_add(UC_HOOK_CODE, sd_body, begin=SD.SD_TAIL, end=SD.SD_TAIL)
        def sd_body2(uc, a, s, d):                    # the other one: push {r3, r4, r5, lr}; sub sp, #0x58 undone, back to the caller
            sp = uc.reg_read(UC_ARM_REG_SP); lr = struct.unpack("<I", bytes(uc.mem_read(sp + 0x58 + 12, 4)))[0]
            uc.reg_write(UC_ARM_REG_SP, sp + 0x58 + 16); uc.reg_write(UC_ARM_REG_PC, lr | 1)
        self.uc.hook_add(UC_HOOK_CODE, sd_body2, begin=SD.SD_TAIL2, end=SD.SD_TAIL2)
        def slow(uc, a, s, d):
            ms = self.extra_ms.get(a, 0)
            if ms: self.at(self.r32(SD.HAL_TICK) + ms)
        for a in (SD.PAD_IN + 4, SD.KNOB_IN + 4): self.uc.hook_add(UC_HOOK_CODE, slow, begin=a, end=a)
        self.uc.mem_write(CAVE, bytes.fromhex("00b5") + bl(CAVE + 2, SD.SD_HEADS[1]) + bytes.fromhex("00bd"))     # push {lr}; bl size-op; pop {pc}
    def mod_sd(self): self.call(CAVE, 0, maxins=2_000_000)
    def stock_sd(self): self.call(SD.SD_HEADS[1], 0, maxins=2_000_000)
    def dup(self): return self.leds()[1]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = E2(img)
    t = [100000]
    def svc(dt=2):
        t[0] += dt; e.at(t[0]); e.svc()
    for i in range(70): svc(); e.cnt += 3
    def gap(action):
        svc(); e.cnt += 3
        if action: action()
        t[0] = max(t[0], e.r32(SD.HAL_TICK)); svc(15); e.cnt += 22
        return e.dup()
    knob = lambda ms: (e.extra_ms.__setitem__(SD.KNOB_IN + 4, ms), e.call(0x08033848, MGR, 0, 1, maxins=6_000_000))
    pad = lambda ms: (e.extra_ms.__setitem__(SD.PAD_IN + 4, ms), e.call(PRESS, MGR, 20, 100, maxins=8_000_000), e.extra_ms.__setitem__(SD.PAD_IN + 4, 0),
                      e.call(RELEASE, MGR, 20, maxins=8_000_000))
    res = dict(none=gap(None), mod=gap(e.mod_sd), stock=gap(e.stock_sd), knob=gap(lambda: knob(6)), pad=gap(lambda: pad(6)), quick=gap(lambda: knob(1)))
    want = dict(none=SD.COL_UNKNOWN, mod=0x01, stock=0x07, knob=0x53, pad=0x17, quick=SD.COL_UNKNOWN)
    for k in want:
        check(res[k] == want[k], f"gap with {k}: Duplicate {res[k]:#x} (want {want[k]:#x})")
    check(e.word(SD.SEEN) & (SD.B_SDMOD | SD.B_SD | SD.B_KNOB | SD.B_PAD) == SD.B_SDMOD | SD.B_SD | SD.B_KNOB | SD.B_PAD, f"every culprit kept in the seen word ({e.word(SD.SEEN):#x})")
    for i in range(32): svc(); e.cnt += 3 if i % 7 else 0
    for i in range(3): svc(); e.cnt += 3
    check(e.leds()[2] == SD.COL_LATE, "a slow block window: Save red, as SC419D")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
