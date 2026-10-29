"""SC49.4 (persist19.use_nocomb): Shift + K5 of a drum (its filter mode, persist19's code 9) skips 3, the comb.

    python tools/emu_nocomb.py BUILD.bin manifest.json
Through the controller (Drum 1's track view, Shift held, K5 turned one step at a time): up from 0 = 1, 2, 4, 0; down from 0 = 4, 2, 1, 0.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_lazysave as T  # noqa: E402
import emu_sc42_6 as X  # noqa: E402

MGR = T.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = T.EL(Path(img).read_bytes()); e.at(300000); e.transport(0)
    dget = int(man["report"]["persist19"]["labels"]["c_dget"], 16)
    mode = lambda: (e.call(dget, 0, 9, maxins=2_000_000), e.uc.reg_read(UC_ARM_REG_R0) & 7)[1]
    knob = lambda d: e.call(0x08033848, MGR, 4, d & 0xFFFFFFFF, maxins=8_000_000)
    e.btn(4); X.frame(e)
    e.set_p0(e.r32(MGR + 0xC), 1)
    m0 = mode()
    while mode() != 0: knob(1)
    up = []
    for _ in range(4): knob(1); up.append(mode())
    down = []
    for _ in range(4): knob(-1); down.append(mode())
    e.set_p0(e.r32(MGR + 0xC), 0)
    check(up == [1, 2, 4, 0] and down == [4, 2, 1, 0], f"Shift + K5 up from 0: {up}, down: {down} (3, the comb, skipped; started at {m0})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} NOCOMB RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
