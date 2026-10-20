"""SC45.2 / Beta 3.9 ARM tests (live RAM dump, the real routes): patchain.use_iterled, the repeat now playing in the Mixer view's Shift row.

    python tools/emu_iterled.py NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json      (OLD = the build before, SC45.1 / Beta 3.8)
  * Mixer view, Shift + pad 12 = 4 repeats of the current scene; stopped, Shift held: the second row yellow, the 4th green (as OLD);
  * running, Shift held: the repeat now playing (the running part's counter S_REPC = 0..2) white, the 4th green; the 4th (the last) blinks
    white / green (256 ms); a counter beyond the repeats, Shift not held, a scene that plays once: as OLD;
  * every other LED of those frames as OLD's.
"""
from __future__ import annotations
import gc, json, struct, sys
from unicorn.arm_const import UC_ARM_REG_R4
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc40_5 import EC, MGR, PK, STOP, CONT, PRESS, RELEASE  # noqa: E402
import patchain as PC  # noqa: E402

Y, G, W = PC.COL_SHIFT, PC.COL_SEL, PC.COL_ITER


class Mix:
    def __init__(self, img, man, reps_pad=11):
        L = {k: int(v, 16) for k, v in man["report"]["patchain"]["labels"].items()}
        self.e = e = EC(img, man, L)
        e.set_p0(e.r32(CONT + 0x188), 0)
        self.press(0); self.release(0); self.press(14); self.release(14)              # the Mixer view
        self.shift(1); self.pad(reps_pad); self.shift(0)

    def press(self, i): self.e.call(0x08033320, MGR, i, maxins=8_000_000)
    def release(self, i): self.e.call(0x0803381A, MGR, i, maxins=8_000_000)
    def pad(self, q): self.e.call(PRESS, MGR, q, 100, maxins=8_000_000); self.e.call(RELEASE, MGR, q, maxins=8_000_000)
    def shift(self, v): self.e.set_p0(self.e.r32(MGR + 0xC), v)

    def reps(self):
        e = self.e
        scn = e.r8(e.ptr(e.r32(PC.ENG + 0x2C), 0))
        return e.r8(e.tail + PC.P_REPS + scn)

    def frame(self, shift, running, n=None, phase=0):
        e = self.e
        e.set_p0(PC.PLAY_STORE, running)
        if n is not None:
            e.uc.mem_write(e.scr + PC.S_REPC, bytes([n]))
        e.w32(PK.HAL_TICK, 0x40000 + (0x100 if phase else 0))
        if shift:
            self.shift(1)
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1))
        e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=30_000_000)
        f = list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))
        if shift:
            self.shift(0)
        return f


def main(img, man, prev, prev_man):
    fails = 0

    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m)
        fails += 0 if c else 1

    a, b = Mix(img, man), Mix(prev, prev_man)
    check(a.reps() == 4, "Shift + pad 12: 4 repeats of the current scene")
    fa, fb = a.frame(True, 0, 0), b.frame(True, 0, 0)
    check(fa == fb and fa[8:16] == [Y] * 3 + [G] + [Y] * 4, f"stopped, Shift held: row 2 yellow, the 4th green, as the build before ({[hex(x) for x in fa[8:16]]})")
    for n in range(3):
        fa, fb = a.frame(True, 1, n), b.frame(True, 1, n)
        want = [Y] * 8
        want[3] = G
        want[n] = W
        check(fa[8:16] == want and fa[:8] + fa[16:] == fb[:8] + fb[16:] and fb[8:16] == [Y] * 3 + [G] + [Y] * 4,
              f"running, repeat {n + 1}: pad {9 + n} white, the 4th green; every other LED as before ({[hex(x) for x in fa[8:16]]})")
    on, off = a.frame(True, 1, 3, phase=1), a.frame(True, 1, 3, phase=0)
    check(on[11] == W and off[11] == G and on[8:11] == off[8:11] == [Y] * 3, f"the last repeat: pad 12 blinks white / green ({on[11]:#x} / {off[11]:#x})")
    check(a.frame(True, 1, 5) == b.frame(True, 1, 5), "a counter beyond the repeats: as before")
    check(a.frame(False, 1, 1) == b.frame(False, 1, 1), "Shift not held: every LED as before")
    del a, b
    gc.collect()
    a, b = Mix(img, man, reps_pad=8), Mix(prev, prev_man, reps_pad=8)
    fa, fb = a.frame(True, 1, 0), b.frame(True, 1, 0)
    check(fa == fb and fa[8] == G, f"a scene that plays once (Shift + pad 9): as before, pad 9 green ({fa[8]:#x})")
    print("ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
