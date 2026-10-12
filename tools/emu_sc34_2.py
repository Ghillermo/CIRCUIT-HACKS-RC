"""SC34.2 tests: SC34.1's tests (emu_sc34_1) + the phrase mode of the song pointer (build_sc17.use_sp3), through the real routes (controller pads
0x08033282 / release, the hooked sequencer tick c_sptick, the Master FX LEDs) on the live RAM dump.

    python tools/emu_sc34_2.py SC34.2.bin SC34.2_manifest.json
  * Shift + step 5 = phrase mode, start 5, end 16 (pad 9 white); a tap = the end (no retrigger, no held steps), held taps too; a tap before the start swaps;
    Shift + another step = a new start (an end before it goes back to 16); the phrase loops in the tick; Shift + the start = off; pad 9 = off; pad 8 clears;
  * without phrase mode: SC32 (one held step = retrigger, two held = a momentary phrase).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc34_1  # noqa: E402  (configures build_sc17 as SC34.1: sampler, sampler2, loophold)
from emu_sc17_7 import E7  # noqa: E402
import build_sc17 as B  # noqa: E402
B.use_sp3()

JT = B.GFX_OFF + B.S_JT


def main(img, man):
    fails = emu_sc34_1.main(img, man)
    gc.collect()
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("sp3") is True, "manifest: sp3")
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.s14 + JT, bytes([0])); return x
    x = fresh(); P = x.step_pad
    check(x.gleds()[8] != B.SP2_WHITE, "no phrase: pad 9 not white")
    x.pad(P(5), shift=True); x.rel(P(5))
    check(x.sp() == (5, 0, 0, 0) and x.eff() == (5, 16) and x.gleds()[8] == B.SP2_WHITE, f"Shift + 5: phrase mode, start 5, end 16, pad 9 white {x.sp()} {x.eff()}")
    x.pad(P(12))
    check(x.sp() == (5, 12, 0, 0) and x.s14b(JT) == 0 and x.eff() == (5, 12), f"tap 12 (held): the end, no retrigger, no held step {x.sp()} {x.s14b(JT):#x}")
    x.rel(P(12))
    check(x.sp() == (5, 12, 0, 0) and x.eff() == (5, 12), "released: the phrase stays")
    x.set_ticks(6 * 12 - 1); x.sets.clear(); x.tick(3)
    check(x.sets == [6 * 4 - 1], f"the phrase loops: step 13 -> step 5 {x.sets}")
    x.pad(P(7)); x.pad(P(10))
    check(x.sp() == (5, 10, 0, 0) and x.s14b(JT) == 0 and x.eff() == (5, 10), f"two pads held in phrase mode: each one is the new end, no momentary phrase {x.sp()}")
    x.rel(P(10)); x.rel(P(7))
    check(x.sp() == (5, 10, 0, 0), "released: unchanged")
    x.pad(P(3)); x.rel(P(3))
    check(x.sp() == (3, 5, 0, 0) and x.eff() == (3, 5), f"tap 3 (before the start): phrase 3..5 {x.sp()}")
    x.pad(P(8), shift=True); x.rel(P(8))
    check(x.sp() == (8, 0, 0, 0) and x.eff() == (8, 16), f"Shift + 8: a new start; the end (5) was before it: back to 16 {x.sp()}")
    x.pad(P(14)); x.rel(P(14)); x.pad(P(10), shift=True); x.rel(P(10))
    check(x.sp() == (10, 14, 0, 0), f"tap 14 then Shift + 10: start 10, end kept {x.sp()}")
    x.pad(P(10), shift=True); x.rel(P(10))
    check(x.sp() == (0, 0, 0, 0) and x.gleds()[8] != B.SP2_WHITE, f"Shift + the start: off, pad 9 not white {x.sp()}")
    x.pad(P(6), shift=True); x.rel(P(6)); x.pad(P(1)); x.rel(P(1))
    check(x.sp() == (0, 0, 0, 0) and x.s14b(JT) == 0, f"pad 9 (white) in phrase mode: off, no retrigger {x.sp()}")
    x.pad(P(6), shift=True); x.rel(P(6)); x.pad(7); x.rel(7)
    check(x.sp() == (0, 0, 0, 0), "pad 8 clears the phrase")
    # ---- outside phrase mode: SC32
    x = fresh()
    x.pad(P(5))
    check(x.sp()[2:] == (5, 0) and x.s14b(JT) == 5 | 0x40 and x.eff() == (0, 16), f"no phrase mode: step 5 held = retrigger {x.sp()} {x.s14b(JT):#x}")
    x.pad(P(9))
    check(x.eff() == (5, 9) and x.s14b(JT) == 0, f"two held: the momentary phrase {x.eff()}")
    x.rel(P(9)); x.rel(P(5))
    check(x.sp() == (0, 0, 0, 0), "released: clean")
    x.pad(P(1)); x.rel(P(1))
    check(x.s14b(JT) == 1, "pad 9 without phrase mode: a normal retrigger tap")
    print("SC34.2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
