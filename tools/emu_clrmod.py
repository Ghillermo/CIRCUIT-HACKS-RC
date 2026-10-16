"""SC41.7 ARM tests: Clear + pad 25 of the Pattern Settings view (playmode.use_clrmod), through the controller.

    python tools/emu_clrmod.py NEW.bin NEW_manifest.json
  * Synth 1, Pattern Settings: Clear held + pad 25 = every step of the pattern it plays: byte 2 (random-mutate) 0, byte 3 bits 4-6 (dynamics) 0, bits 0-2
    (frequency) and every other byte kept; the probability view does not open;
  * pad 25 without Clear: the stepmod mode 2 (the probability view, controller sub-mode 5), the steps untouched.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import MGR  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import emu_sc40_8 as T8  # noqa: E402
import playmode as PM  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = lambda sec: {k: int(v, 16) for k, v in man["report"][sec]["labels"].items()}
    e = T8.E8(img, man, lab("patchain"))
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda q: (e.call(PRESS, MGR, q, 100, maxins=8_000_000), e.call(RELEASE, MGR, q, maxins=8_000_000))
    T = 0
    e.set_p0(e.r32(CONT + 0x188), T); press(T); release(T); press(12); release(12)
    pat = e.playing(T); base = e.settings(T, pat) - PM.SET_OFF
    steps = b"".join(bytes([0x10 + s, s, 0x40 | s & 7, 0x5A | (s & 7)]) + bytes((7 * s + i) & 0xFF for i in range(24)) for s in range(32))
    e.uc.mem_write(base, steps)
    sub0 = e.r8(MGR + 0x152)
    press(23); pad(PM.PAD_MODE2); release(23)
    got = bytes(e.uc.mem_read(base, 32 * 28))
    want = b"".join(steps[28 * s:28 * s + 2] + bytes([0, steps[28 * s + 3] & 0x8F]) + steps[28 * s + 4:28 * s + 28] for s in range(32))
    check(sub0 == 4 and got == want and e.r8(MGR + 0x152) == 4, f"Clear + pad 25: random-mutate and dynamics of the 32 steps to 0, frequency and the rest kept, the view stays ({e.r8(MGR + 0x152)})")
    e.uc.mem_write(base, steps)
    pad(PM.PAD_MODE2)
    check(bytes(e.uc.mem_read(base, 32 * 28)) == steps and e.r8(MGR + 0x152) == 5, f"pad 25 alone: mode 2 opens (sub-mode {e.r8(MGR + 0x152)}), the steps untouched")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
