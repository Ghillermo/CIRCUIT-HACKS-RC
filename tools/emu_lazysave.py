"""SC42 / Beta 1.10 / RC0.9.3(S) tests: the mod's settings save deferred (lazysave.py), through the controller (MIDI 1's Preset view, pad 27 = the
engine's oscillator toggle, which saved at once before) and the real LED task call; the write itself (0x0803C920) is counted and skipped.

    python tools/emu_lazysave.py NEW.bin NEW_manifest.json [PREVIOUS.bin]
  * playing: the toggle writes nothing, the save pending; seconds later, still playing, nothing;
  * stopped: nothing before 2 s since the request, one write after, then nothing more;
  * the stock's own call (LR in the stock code) saves at once;
  * the previous build (if given): the same toggle writes at once (the cause of the stutter).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_SP
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import lazysave as LZ  # noqa: E402
import packio as PK  # noqa: E402

MGR = 0x20040B10
WRITE = 0x0803C920
SD_OPS = (0x0803CA52, 0x0803CADE, 0x0803CB50, 0x0803CB6A, 0x0803CBF0)   # the content API: its two dispatchers and the exists / size / read ops
STOCK_LR = 0x08010101                    # a return address inside the stock code, where the test stops


class EL(E8):
    def __init__(self, img):
        super().__init__(img)
        self.writes = 0
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def wr(uc, a, s, d): self.writes += 1; skip(uc)
        self.uc.hook_add(UC_HOOK_CODE, wr, begin=WRITE, end=WRITE)
        for f in (0x080292F8, 0x0801BE78): self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: skip(uc), begin=f, end=f)
        def sd_fail(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0xFFFFFFFF); skip(uc)
        for f in SD_OPS: self.uc.hook_add(UC_HOOK_CODE, sd_fail, begin=f, end=f)   # the mod's SD reads (mpatch, pmode) answered: no storage task here
        def zero(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); skip(uc)
        for f in (PK.SEM_TAKE, PK.SEM_GIVE, PK.DSP_READ): self.uc.hook_add(UC_HOOK_CODE, zero, begin=f, end=f)   # the DSP semaphore / reads (xpatch's LED task): no RTOS here
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: uc.emu_stop(), begin=STOCK_LR & ~1, end=STOCK_LR & ~1)
        self.t = 100000
    def at(self, ms): self.t = ms; self.w32(LZ.HAL_TICK, ms)
    def btn(self, i): self.call(0x08033320, MGR, i, maxins=8_000_000); self.call(0x0803381A, MGR, i, maxins=8_000_000)
    def pad(self, q): self.call(PRESS, MGR, q, 100, maxins=8_000_000); self.call(RELEASE, MGR, q, maxins=8_000_000)
    def leds(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
    def transport(self, on):
        for fn in (0x080354FA, 0x0803542C):
            self.call(fn, LZ.TRANSPORT, 0); self.uc.mem_write(self.uc.reg_read(UC_ARM_REG_R0), bytes([on]))
    def stock_save(self):
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, 0x2006F000); uc.reg_write(UC_ARM_REG_R0, LZ.SETOBJ); uc.reg_write(UC_ARM_REG_LR, STOCK_LR)
        uc.emu_start(LZ.SAVE_IN | 1, 0xFFFFFFFF, count=3_000_000)


def toggle(e):
    e.btn(2); e.btn(8); e.pad(26)                          # MIDI 1, Preset, pad 27


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = EL(img)
    rec = e.r32(LZ.SESSION_OBJ + 0x14); tail = rec + LZ.TAIL
    e.at(100000); e.transport(1); e.leds(); e.writes = 0
    toggle(e)
    check(e.writes == 0 and e.r8(tail + LZ.O_PEND) == LZ.PEND, f"playing: pad 27 of MIDI 1 writes nothing, the save pending ({e.writes}, {e.r8(tail + LZ.O_PEND):#x})")
    e.at(105000); e.leds()
    check(e.writes == 0, "5 s later, still playing: nothing written")
    e.transport(0); toggle(e); t0 = e.t
    e.at(t0 + 1000); e.leds(); w1 = e.writes
    e.at(t0 + 2100); e.leds(); w2 = e.writes
    e.at(t0 + 4000); e.leds(); w3 = e.writes
    check(w1 == 0 and w2 == 1 and w3 == 1 and e.r8(tail + LZ.O_PEND) == 0, f"stopped: nothing at 1 s, one write at 2.1 s, then nothing ({w1}, {w2}, {w3})")
    e.writes = 0; e.transport(1); e.stock_save()
    check(e.writes == 1 and e.r8(tail + LZ.O_PEND) == 0, f"the stock's own call: written at once, even playing ({e.writes})")
    del e; gc.collect()
    if prev:
        p = EL(prev); p.at(100000); p.transport(1); p.leds(); p.writes = 0; toggle(p)
        check(p.writes >= 1, f"the previous build: the same toggle wrote at once while playing ({p.writes})")
        del p; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes() if len(a) > 3 else None) else 0)
