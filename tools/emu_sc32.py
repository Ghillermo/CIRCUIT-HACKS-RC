"""SC32 ARM tests: the Master FX song pointer without pad 7 (build_sc17.use_sp2).  Real routes (controller pads 0x08033282 / release 0x0803381A,
the hooked sequencer tick c_sptick, the LED slot of the Mixer view) on the live RAM dump.

    python tools/emu_sc32.py SC32.bin SC32_manifest.json
  * pad 7: dark, press / release change nothing;
  * one step held = retrigger at every step boundary while held; a tap = one jump; two held = a phrase between them (no retrigger), releasing either ends it;
  * Shift + step = latched start (loop start..16), Shift + a second step = the end (the lower is the start), Shift + the start again = off,
    Shift + a step with a latched phrase = a new start; a latched phrase lights pad 9 white and pad 9 removes it; held steps work inside a latched phrase.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
import build_sc17 as B  # noqa: E402
B.use_jump(hold=True, white=True); B.CLR_ON, B.CLR_DIM = 0x01, 0x03; B.JMP_ON, B.JMP_OFF = 0x2D, 0x2E
B.use_spcache(); B.CLR_COPY = True; B.use_sp_norm(); B.use_sp2()

JT, JF = B.GFX_OFF + B.S_JT, B.GFX_OFF + B.S_JF


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["sc17"].get("sp2") == hex(B.SP2_WHITE), "manifest: sp2")
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); x.uc.mem_write(x.s14 + JT, bytes([0])); return x
    x = fresh(); P = x.step_pad
    # ---- pad 7
    before = (x.sp(), x.s14b(JT), x.s14b(JF))
    x.pad(6); mid = (x.sp(), x.s14b(JT), x.s14b(JF)); x.rel(6)
    x.pad(6, shift=True); x.rel(6)
    check(mid == before and (x.sp(), x.s14b(JT), x.s14b(JF)) == before, "pad 7 (with and without Shift): no state change")
    check(x.gleds()[6] == 0, f"pad 7 dark ({x.gleds()[6]:#x})")
    # ---- one held step: retrigger
    x.pad(P(5))
    check(x.sp()[2:] == (5, 0) and x.s14b(JT) == 5 | 0x40 and x.eff() == (0, 16), f"step 5 held: retrigger armed, no phrase {x.sp()} {x.s14b(JT):#x} {x.eff()}")
    x.set_ticks(20); x.sets.clear(); x.tick(12)
    check(x.sets == [23, 23], f"held: it jumps to step 5 at each of the next two boundaries {x.sets}")
    x.rel(P(5))
    check(x.s14b(JT) == 0 and x.sp()[2:] == (0, 0), "released: target and held step cleared")
    x.sets.clear(); x.tick(12)
    check(x.sets == [], f"then nothing {x.sets}")
    x.pad(P(9)); x.rel(P(9))
    check(x.s14b(JT) == 9, f"a tap before the boundary: one jump pending ({x.s14b(JT):#x})")
    x.set_ticks(20); x.sets.clear(); x.tick(14)
    check(x.sets == [47], f"one jump to step 9 only {x.sets}")
    # ---- two held steps: phrase
    x = fresh()
    x.pad(P(9)); x.pad(P(3))
    check(x.sp()[2:] == (9, 3) and x.s14b(JT) == 0 and x.eff() == (3, 9), f"steps 9 + 3 held: phrase 3..9, no retrigger {x.sp()} {x.eff()}")
    x.set_ticks(52); x.sets.clear(); x.tick(4)
    check(x.sets == [11], f"the phrase loops: step 10 -> step 3 {x.sets}")
    x.rel(P(3))
    check(x.eff() == (0, 16) and x.sp()[2:] == (9, 0) and x.s14b(JT) == 0, f"one released: the phrase ends, the other step does not retrigger {x.sp()}")
    x.sets.clear(); x.set_ticks(20); x.tick(14)
    check(x.sets == [], f"and nothing happens {x.sets}")
    x.rel(P(9))
    check(x.sp() == (0, 0, 0, 0), "both released: clean")
    x.pad(P(4)); x.pad(P(12)); x.rel(P(4))
    check(x.sp()[2:] == (12, 0) and x.eff() == (0, 16), f"the first one released first: the other stays as the held step {x.sp()}")
    x.rel(P(12))
    # ---- Shift: latched phrase
    x = fresh(); pal = [(int(a, 16), int(b, 16)) for a, b in man["report"]["sc17"]["pal_codes"]]
    check(x.gleds()[8] != B.SP2_WHITE, "no phrase: pad 9 not white")
    x.pad(P(5), shift=True); x.rel(P(5))
    check(x.sp()[:2] == (5, 0) and x.eff() == (5, 16), f"Shift + 5: the start, loop 5..16 meanwhile {x.sp()}")
    check(x.gleds()[8] == B.SP2_WHITE, f"pad 9 white ({x.gleds()[8]:#x})")
    x.pad(P(12), shift=True); x.rel(P(12))
    check(x.sp()[:2] == (5, 12) and x.eff() == (5, 12), f"Shift + 12: phrase 5..12 latched {x.sp()}")
    x.set_ticks(6 * 12 - 1); x.sets.clear(); x.tick(3)
    check(x.sets == [6 * 4 - 1], f"latched: step 13 -> step 5 {x.sets}")
    x.pad(P(7));
    check(x.s14b(JT) == 7 | 0x40 and x.sp()[:2] == (5, 12), "a held step inside the latched phrase: retrigger, the phrase stays")
    x.pad(P(10))
    check(x.eff() == (7, 10), f"two held inside it: the held phrase wins ({x.eff()})")
    x.rel(P(10)); x.rel(P(7))
    check(x.eff() == (5, 12) and x.s14b(JT) == 0, f"released: back to the latched phrase ({x.eff()})")
    x.pad(P(3), shift=True); x.rel(P(3))
    check(x.sp()[:2] == (3, 0), f"Shift + 3 with a latched phrase: a new start {x.sp()}")
    x.pad(P(3), shift=True); x.rel(P(3))
    check(x.sp()[:2] == (0, 0) and x.gleds()[8] != B.SP2_WHITE, f"Shift + the start again: off, pad 9 not white {x.sp()}")
    x.pad(P(10), shift=True); x.rel(P(10)); x.pad(P(4), shift=True); x.rel(P(4))
    check(x.sp()[:2] == (4, 10), f"Shift + 10 then Shift + 4: phrase 4..10 (the lower is the start) {x.sp()}")
    x.pad(P(6)); x.pad(P(2), shift=True)
    check(x.sp() == (2, 0, 0, 0) and x.s14b(JT) == 0, f"Shift + a step while a step is held: a new start, held step and retrigger forgotten {x.sp()}")
    x.rel(P(2)); x.rel(P(6))
    x.pad(P(9), shift=True); x.rel(P(9))
    x.pad(P(1)); x.rel(P(1))
    check(x.sp() == (0, 0, 0, 0) and x.s14b(JT) == 0, f"pad 9 (step 1) without Shift: the latched phrase removed, no retrigger {x.sp()}")
    x.pad(P(1)); x.rel(P(1))
    check(x.s14b(JT) == 1, "pad 9 without a phrase: a normal retrigger tap")
    x.uc.mem_write(x.s14 + JT, bytes([0]))
    x.pad(P(6), shift=True); x.rel(P(6)); x.pad(7); x.rel(7)
    check(x.sp() == (0, 0, 0, 0), "pad 8 clears the latched phrase")
    print("SC32 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
