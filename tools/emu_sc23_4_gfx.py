"""SC23.4: the Master FX corrections: pad 8 white, song pointer ranges normalised (the lower step is the start whatever the order), a loop end the playhead has passed jumps to the start,
the target of a step jump is lit, a latched pad 7 unlatches when touched again.  Real routes (controller pads, the hooked sequencer tick) on the live RAM dump.

    python tools/emu_sc23_4_gfx.py SC23.4.bin SC23.4_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
import build_sc17 as B  # noqa: E402
B.use_jump(hold=True, white=True); B.CLR_ON, B.CLR_DIM = 0x01, 0x03; B.JMP_ON, B.JMP_OFF = 0x2D, 0x2E

JT = B.GFX_OFF + B.S_JT


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sp = man["report"]["sc17"]
    check(sp.get("jump_hold") is True, "manifest: the step jump with hold (SC19.9) is in")
    def fresh():
        gc.collect(); x = E7(img, man); x.grid(); x.setsp(); return x
    # ---- ranges are normalised
    e = fresh(); P = e.step_pad
    e.pad(P(9)); e.pad(P(3))
    check(e.eff() == (3, 9) and e.sp()[2:] == (9, 3), f"two held steps, the later one first: the start is 3, the end 9 ({e.eff()})")
    e.rel(P(3)); e.rel(P(9))
    e.pad(P(3)); e.pad(P(9))
    check(e.eff() == (3, 9), f"two held steps in order: (3, 9) ({e.eff()})")
    e.rel(P(9)); e.rel(P(3))
    e.pad(P(5), shift=True); e.rel(P(5)); e.pad(P(3)); e.rel(P(3))
    check(e.sp()[:2] == (3, 5) and e.eff() == (3, 5), f"latched start 5, a tap on step 3: start 3, end 5 {e.sp()}")
    e.pad(P(12)); e.rel(P(12))
    check(e.sp()[:2] == (3, 12), f"a tap above: the end moves {e.sp()}")
    e.pad(P(3)); e.rel(P(3))
    check(e.sp()[:2] == (3, 3) and e.eff() == (3, 3), f"a tap on the start: a one-step loop {e.sp()}")
    # ---- the tick: the end passed -> the start
    def run(ls, le, start, count, h1=0, h2=0):
        x = E7(img, man)
        x.set_ticks(start); x.setsp(ls=ls, le=le, h1=h1, h2=h2)
        return x, x.tick(count)
    x, seq = run(3, 9, 52, 4)
    check(x.sets == [11] and seq[:3] == [53, 12, 13], f"range 3..9: at the first tick of step 10 the position goes to the start of step 3 {seq} {x.sets}")
    x, seq = run(3, 9, 71, 3)
    check(x.sets == [11] and seq[0] == 12, f"playhead already at step 12 (past the end 9): the next step boundary jumps to step 3 {seq} {x.sets}")
    x, seq = run(3, 9, 6 * 4 + 1, 20)
    check(x.sets == [] and seq == list(range(6 * 4 + 2, 6 * 4 + 22)), f"inside the range: nothing happens {x.sets}")
    x, seq = run(3, 0, 95, 3)
    check(x.sets == [11] and seq[0] == 12, f"range 3..16: the wrap goes to step 3 {seq} {x.sets}")
    x, seq = run(0, 0, 0, 200)
    check(x.sets == [], "no range: nothing")
    x, seq = run(0, 0, 52, 4, h1=9, h2=3)
    check(x.sets == [11] and seq[:3] == [53, 12, 13], f"held steps 9 then 3: the same loop 3..9 {seq} {x.sets}")
    # ---- jump target LED, pad 7 un-stick, pad 8
    pal = [(int(a, 16), int(b, 16)) for a, b in man["report"]["sc17"]["pal_codes"]]
    base_c = B.SP_COLORS(pal)[0]
    x = fresh(); P = x.step_pad
    x.pad(6); x.pad(P(9))
    g = x.gleds()
    check(g[8 + 8] == B.JMP_ON and all(g[8 + i] == base_c for i in range(16) if i != 8), f"jump target step 9 lit white while its pad is held ({[hex(v) for v in g[8:24]]})")
    x.rel(P(9)); x.rel(6)
    g = x.gleds()
    check(g[8 + 8] == B.JMP_ON, "a jump pending: still lit")
    x.set_ticks(20); x.tick(10)
    g = x.gleds()
    check(g[8 + 8] == base_c, "after the jump: normal")
    x = fresh()
    x.pad(6, shift=True); x.rel(6)
    check(x.s14b(B.GFX_OFF + B.S_JF) == 2, "Shift + pad 7: latched")
    x.pad(6); x.rel(6)
    check(x.s14b(B.GFX_OFF + B.S_JF) == 0, "pad 7 touched again: unlatched, no momentary mode left")
    x.pad(6); check(x.s14b(B.GFX_OFF + B.S_JF) == 1, "pad 7 held: momentary mode as before"); x.rel(6)
    check(x.s14b(B.GFX_OFF + B.S_JF) == 0, "released")
    x = fresh(); x.setsp()
    g = x.gleds()
    check(g[7] == B.CLR_DIM == 0x03, f"pad 8 dim white when there is nothing to clear ({g[7]:#x})")
    x.setsp(ls=3)
    g = x.gleds()
    check(g[7] == B.CLR_ON == 0x01, f"pad 8 bright white with a song pointer range set ({g[7]:#x})")
    print("SC23.4 MASTER FX RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
