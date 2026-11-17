"""S579D tests (tools/cwatch.py): the LED-task head that freezes the black box when a drum velocity-bar object loses its vtable words.
  * the head is in front of both LED task calls and chains to the previous head;
  * a frame with the four objects intact: the black box's state untouched, the frame identical to the build without the watch (the 5.63 + guards
    scratch is not kept: compared with Beta 5.63's frame instead, which the guards and the watch do not change);
  * the record's corruption ([0x20043610] = 0x0805AD60, Drum 4's listener vtable): the next frame freezes the record (state 0x85 = FROZEN |
    MANUAL | 0x80), notes the drum (RAM + 5 = 4) and fires once (a second frame changes nothing more); the ring (the gestures before) survives;
  * the record already frozen: the watch does nothing.

    python tools/emu_cwatch.py firmware/s579d/circuittracks-4486-S579D.bin firmware/s579d/manifest.json firmware/b5.63/circuittracks-4486-B5.63.bin firmware/b5.63/manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from unicorn.arm_const import UC_ARM_REG_R4  # noqa: E402
import emu_sc48_8 as S  # noqa: E402
import blackbox as BB  # noqa: E402
import cwatch as CW  # noqa: E402
from emu_sc35 import MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import packio as PK  # noqa: E402
import fxdiag as FD  # noqa: E402

C3L = 0x20043610


def frame(e):
    e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR); e.call(0x08033B3E, maxins=40_000_000)
    return bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    R = man["report"]
    check("cwatch" in R and all(bytes(img[c - 0x08010000:c - 0x08010000 + 4]) == __import__("thumb").bl(c, int(R["cwatch"]["labels"]["c_cwled"], 16)) for c in PK.LED_CALLS),
          "both LED task calls go to c_cwled")
    e = S.ET(img, man)
    st = lambda: e.r8(BB.BB + BB.O.ST)
    e.uc.mem_write(CW.CW, bytes(8))
    e.uc.mem_write(BB.BB + BB.O.ST, bytes([0]))
    f0 = frame(e)
    check(st() == 0 and e.r8(CW.CW + 4) == 0, f"intact objects: nothing fires (state {st():#x}, fired {e.r8(CW.CW + 4)})")
    gc.collect(); p = S.ET(prev, pman); fp = frame(p); del p; gc.collect()
    check(f0 == fp, "the LED frame is the one of Beta 5.63 (the watch paints nothing)")
    e.w32(C3L, 0x0805AD60)                                                     # the record's corruption
    f1 = frame(e)
    check(st() == (BB.ST_FROZEN | BB.ST_MANUAL | 0x80) and e.r8(CW.CW + 4) == 1 and e.r8(CW.CW + 5) == 4,
          f"Drum 4's listener vtable changed: the next frame freezes the record (state {st():#x}), fired {e.r8(CW.CW + 4)}, drum {e.r8(CW.CW + 5)}")
    check(f1 == f0, "that frame's LEDs unchanged")
    stv = st(); e.uc.mem_write(BB.BB + BB.O.ST, bytes([stv | BB.ST_RESET]))    # mark: a second freeze would rewrite the state
    frame(e)
    check(st() == (stv | BB.ST_RESET), f"a second frame does not freeze again (state {st():#x})")
    e.w32(C3L, 0x0805ADA8); e.uc.mem_write(CW.CW + 4, bytes([0])); e.uc.mem_write(BB.BB + BB.O.ST, bytes([BB.ST_FROZEN]))
    e.w32(C3L - 0x44 * 0 + 0, 0x0805ADA8)
    e.w32(0x2004353c + 8, 0x11111111)                                          # Drum 1's object, the record already frozen
    frame(e)
    check(st() == BB.ST_FROZEN and e.r8(CW.CW + 4) == 0, f"frozen already: the watch does nothing (state {st():#x}, fired {e.r8(CW.CW + 4)})")
    e.w32(0x2004353c + 8, 0x0805ADA8)
    print(f"{man.get('marker', '?')} CWATCH RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
