"""SC19.7 ARM tests: the Master FX song pointer's instant jump mode (pad 7): white pad, and the target step repeats while the mode stays on.

    python tools/emu_sc19_7.py SC19.6.bin SC19.7.bin SC19.6_manifest.json SC19.7_manifest.json
Real routes: pads through the controller (0x08033282 / 0x080332FE, Shift through p0 of [ctrl+0xC]), the LED buffer of the Master FX view, and the sequencer tick
0x0802C418 (hooked by c_sptick) on the live RAM dump; the stock "set ticks" call (0x0802BFE0) is recorded as in emu_sc17_7.py.
Jump state = the Master FX block bytes S_JF (bit 0 held, bit 1 sticky) and S_JT (target 1-16, bit 7 = repeating).
  * pad 7: dim white off (code 3), bright white on (code 1); every other pad LED as in SC19.6;
  * held / sticky + a step pad: the first jump at the next step boundary, then the same step again at every boundary (ticks 48..53, 48..53, ...);
  * released / toggled off (also in the middle of a step): no more jumps, the song goes on from where it is; pad 8 (clear) ends it too;
  * a tap that ends before the boundary still jumps once (as SC19.6); a new step pad while repeating moves the target;
  * without jump mode the tick counts 1, 2, 3 ... as before.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_7 import E7  # noqa: E402
import build_sc17 as B  # noqa: E402

JF, JT = B.GFX_OFF + B.S_JF, B.GFX_OFF + B.S_JT


def main(prev, img, man6, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    check(rep["sc17"].get("jump_repeat") is True and rep["sc17"].get("jump_white") == [hex(B.JMP_OFF), hex(B.JMP_ON)] and "jump_repeat" not in man6["report"]["sc17"],
          f"manifest: jump_repeat, jump_white {rep['sc17'].get('jump_white')} (off in SC19.6)")
    jstate = lambda e: (e.s14b(JF), e.s14b(JT))
    OFF, ON = B.JMP_OFF, B.JMP_ON

    # ---- pad 7: white
    gc.collect(); e = E7(img, man); e.grid()
    gc.collect(); r = E7(prev, man6); r.grid()
    check(jstate(e) == (0, 0) and e.gleds()[6] == OFF, f"power-up: jump mode off, pad 7 dim white ({e.gleds()[6]:#x})")
    check(all(a == b for i, (a, b) in enumerate(zip(e.gleds()[:34], r.gleds()[:34])) if i != 6) and r.gleds()[6] != OFF, "every other pad / button LED as SC19.6 (off; the knob LEDs of SC19.9 carry the value brightness)")
    c = e.pad(6); r.pad(6)
    check(jstate(e) == (1, 0) and c == [] and e.gleds()[6] == ON, f"hold pad 7: jump mode on, pad 7 bright white ({e.gleds()[6]:#x}), no stock press")
    check(all(a == b for i, (a, b) in enumerate(zip(e.gleds()[:34], r.gleds()[:34])) if i != 6), "every other pad LED as SC19.6 (on)")
    e.rel(6); check(jstate(e) == (0, 0) and e.gleds()[6] == OFF, "release pad 7: off, dim white")
    e.pad(6, shift=True); e.rel(6); check(jstate(e) == (2, 0) and e.gleds()[6] == ON, "Shift + pad 7: sticky on, bright white")
    e.pad(6, shift=True); e.rel(6); check(jstate(e) == (0, 0) and e.gleds()[6] == OFF, "Shift + pad 7 again: off")

    # ---- held pad 7 + a step: first jump, then the same step again at every boundary
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.pad(6); x.pad(x.step_pad(9)); x.rel(x.step_pad(9))
    check(jstate(x) == (1, 9), f"pad 7 held + step 9: target 9 {jstate(x)}")
    x.set_ticks(20)
    seq = x.tick(3 + 6 * 3)
    check(seq[:3] == [21, 22, 23] and seq[3:] == [48, 49, 50, 51, 52, 53] * 3 and x.sets == [47] * 3,
          f"held: 21, 22, 23, then step 9 (48..53) again and again {seq[:12]} sets {x.sets}")
    check(jstate(x) == (1, 9 | 0x80), f"the target stays, marked as repeating {jstate(x)}")
    # released in the middle of a repetition: the song goes on from there
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.pad(6); x.pad(x.step_pad(9)); x.rel(x.step_pad(9)); x.set_ticks(20)
    seq = x.tick(3 + 6 + 3)                                                  # 21 22 23, 48..53, 48 49 50
    x.rel(6)
    n_sets = len(x.sets)
    seq2 = x.tick(18)
    check(seq[-3:] == [48, 49, 50] and seq2 == list(range(51, 69)) and len(x.sets) == n_sets and jstate(x) == (0, 0),
          f"pad 7 released after the second pass of step 9: 51, 52, 53, 54 ... no more jumps {seq2[:8]} {jstate(x)} sets {len(x.sets) - n_sets}")

    # ---- sticky (Shift + pad 7): repeats until it is toggled off
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.pad(6, shift=True); x.rel(6)
    x.pad(x.step_pad(3)); x.rel(x.step_pad(3))
    check(jstate(x) == (2, 3), f"sticky + step 3: target 3 {jstate(x)}")
    x.set_ticks(38)
    seq = x.tick(3 + 6 * 3)
    check(seq[:3] == [39, 40, 41] and seq[3:] == [12, 13, 14, 15, 16, 17] * 3 and jstate(x) == (2, 3 | 0x80),
          f"sticky: 39, 40, 41, then step 3 (12..17) every boundary {seq[:10]} {jstate(x)}")
    x.pad(6, shift=True); x.rel(6)
    seq = x.tick(14)
    check(jstate(x) == (0, 0) and seq == list(range(18, 32)),
          f"toggled off (Shift + pad 7): the song goes on {seq[:8]} {jstate(x)}")

    # ---- a new step pad while repeating moves the target
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.pad(6); x.pad(x.step_pad(9)); x.rel(x.step_pad(9)); x.set_ticks(20)
    x.tick(3 + 6 + 2)
    x.pad(x.step_pad(2)); x.rel(x.step_pad(2))
    check(jstate(x) == (1, 2), f"step 2 touched while repeating: target 2, repeating mark cleared {jstate(x)}")
    seq = x.tick(4 + 6)
    check(seq[:4] == [50, 51, 52, 53] and seq[4:] == [6, 7, 8, 9, 10, 11] and jstate(x) == (1, 2 | 0x80), f"the next boundary jumps to step 2 (tick 6..11) {seq}")
    # ---- pad 8 (clear) ends it
    x.pad(7); x.rel(7)
    check(jstate(x) == (0, 0), f"pad 8: jump mode and target cleared {jstate(x)}")
    seq = x.tick(12)
    check(seq == list(range(seq[0], seq[0] + 12)), f"after pad 8 the song goes on {seq[:6]}")

    # ---- a tap that ends before the boundary: one jump (as SC19.6)
    gc.collect(); x = E7(img, man); x.grid(); x.setsp()
    x.pad(6); x.pad(x.step_pad(9)); x.rel(x.step_pad(9)); x.rel(6)
    check(jstate(x) == (0, 9), f"tap pad 7 + step 9, all released before the boundary: target pending {jstate(x)}")
    x.set_ticks(20)
    seq = x.tick(3 + 6 + 2)
    check(seq[:4] == [21, 22, 23, 48] and seq[4:] == [49, 50, 51, 52, 53, 54, 55] and jstate(x) == (0, 0) and x.sets == [47],
          f"one jump, then the song goes on {seq} sets {x.sets}")
    # ---- no jump mode: the tick counts as before
    gc.collect(); x = E7(img, man); x.grid(); x.setsp(); x.set_ticks(20)
    seq = x.tick(30)
    check(seq == list(range(21, 51)) and x.sets == [], "jump mode off: 21, 22, 23 ... untouched")
    # ---- a stale repeating mark with the mode off (transport restarted after a release): cleared, no jump
    x.uc.mem_write(x.s14 + JT, bytes([9 | 0x80]))
    seq = x.tick(8)
    check(jstate(x) == (0, 0) and seq == list(range(51, 59)) and x.sets == [], f"stale repeating mark, mode off: cleared, no jump {seq[:4]} {jstate(x)}")
    print("SC19.7 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
