"""SC46.1 / RC2.07 ARM tests (stepgate.use_v4): the fixed length of step entry, through the controller (Synth 1's Note view and its Micro Step
view) and the real LED task.

    python tools/emu_sc46_1.py NEW.bin NEW_manifest.json [OLD.bin OLD_manifest.json]       (OLD = SC46 / RC2.06: the failures it had)
  * the selector: pad 31 opens it (the length over pads 17-32), pad 20 = 4 steps: pads 17-30 back to the stock's Micro Step LEDs (the build
    before: still the selector's); the view left with the selector open: the LED task closes it and the view's buffer is the stock's again;
  * the fixed length (4 steps = 24 micro steps) on a note entered with the note pad let go first, the step pad let go first, the note held
    first, on step 1 (where the stock gives a new note the step's longest gate), on a step cleared (Clear + step) and on both notes of a chord
    (the build before: the stock's gate with the step pad let go first, and for the first note of the chord);
  * the gate by holding (pad 32): a note held 375 ms at 120 BPM = 18 micro steps, with the note pad or the step pad let go first (the build
    before: not with the step pad first).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_arp import EA, CONT  # noqa: E402
import arp as A  # noqa: E402
import stepgate as SG  # noqa: E402

MGR, TV = 0x20040B10, 0x200412E0


def run(img, man):
    e = EA(img, man)
    lab = {k: int(v, 16) for k, v in man["report"]["stepgate"]["labels"].items()}
    e.set_p0(e.r32(CONT + 0x188), 0); e.press(0); e.release(0); e.press(9); e.release(9); e.transport(0)
    r = {}
    def pg(st, k): e.call(0x0803542C, st, k); return e.uc.reg_read(UC_ARM_REG_R0)
    def store_units():
        st = e.r32(TV + 0x24); mask = e.r8(pg(st, 0)); out = []
        for k in range(6):
            if mask >> k & 1: q = pg(st, k + 1); out.append((e.r8(q), e.r8(q + 1) & 0x7F))
        return out
    def look(s): e.pad(s, up=False); u = store_units(); e.unpad(s); return u
    t = [200000]
    def at(ms): t[0] += ms; e.w32(A.HAL_TICK, t[0])
    def enter(s, notes, order="sn", rel="n", ms=100):
        at(10)
        if order == "sn": e.pad(s, up=False); [e.pad(n, up=False) for n in notes]
        else: [e.pad(n, up=False) for n in notes]; e.pad(s, up=False)
        at(ms)
        if rel == "n": [e.unpad(n) for n in reversed(notes)]; e.unpad(s)
        else: e.unpad(s); [e.unpad(n) for n in reversed(notes)]
        return look(s)
    # ---- the selector's LEDs
    e.press(11); e.release(11); e.press(11); e.release(11)
    r["sub"] = e.r8(MGR + 0x152)
    f0 = e.pads()
    e.pad(30); f1 = e.pads()
    e.pad(19); f2 = e.pads()
    e.call(lab["c_sgfget"], 0); r["fixed"] = e.uc.reg_read(UC_ARM_REG_R0)
    r["leds"] = (f0[16:30], f1[16:30], f2[16:30], f2[30])
    # ---- the fixed length (4 steps), every way of entering
    e.press(9); e.release(9)
    r["note_first_rel"] = enter(4, [16])
    r["step_first_rel"] = enter(5, [17], rel="s")
    r["note_held_first"] = enter(6, [18], order="ns")
    r["step1"] = enter(0, [19])
    clr = e.r32(e.r32(MGR + 0x20) + 0xC)
    e.set_p0(clr, 1); e.pad(7); e.set_p0(clr, 0)
    r["cleared"] = enter(7, [16])
    r["chord"] = enter(8, [16, 18])
    # ---- the selector open when the view is left: pad 31 (the fixed length off), pad 31 (the selector), Note
    e.press(11); e.release(11); e.press(11); e.release(11)
    ms = SG.MS_OBJ0
    buf = lambda: list(bytes(e.uc.mem_read(e.r32(e.r32(ms + 4)), 32)))
    b0 = buf()
    e.pad(30); e.pad(30); at(10); e.pads()
    tail = e.r32(SG.SESSION_OBJ + 0x14) + SG.TAIL
    r["open"] = e.r8(tail + SG.O_FL + 6)
    e.press(9); e.release(9); at(400); e.ledtask()
    r["closed"] = (e.r8(tail + SG.O_FL + 6), buf() == b0)
    # ---- the gate by holding
    e.press(11); e.release(11); e.press(11); e.release(11); e.pad(31); e.press(9); e.release(9)
    e.call(lab["c_sgon"], 0); r["hold_on"] = e.uc.reg_read(UC_ARM_REG_R0)
    r["hold_n"] = enter(10, [17], ms=375)
    r["hold_s"] = enter(11, [19], rel="s", ms=375)
    del e; gc.collect()
    return r


def main(img, man, old=None, oman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    r = run(img, man)
    f0, f1, f2, p31 = r["leds"]
    check(r["sub"] == 8 and f1 == [SG.COL_OFF] * 14 and f1 != f0, f"the Micro Step view (subview {r['sub']}), pad 31 = the selector, no length yet ({[hex(x) for x in f1]})")
    check(r["fixed"] == 0x84 and f2 == f0 and p31 == SG.COL_FIX, f"pad 20 = 4 steps ({r['fixed']:#x}): pads 17-30 back to the stock's ({[hex(x) for x in f2]} / {[hex(x) for x in f0]}), pad 31 orange")
    check(r["open"] and r["closed"] == (0, True), f"the view left with the selector open: closed by the LED task, the view's buffer the stock's again ({r['open']}, {r['closed']})")
    g = lambda u: sorted(x[1] for x in u)
    for k, want in (("note_first_rel", [24]), ("step_first_rel", [24]), ("note_held_first", [24]), ("cleared", [24]), ("chord", [24, 24])):
        check(g(r[k]) == want, f"fixed length 4 steps, {k.replace('_', ' ')}: gates {r[k]}")
    check(24 in g(r["step1"]), f"fixed length, step 1: {r['step1']}")
    check(r["hold_on"] == 1 and g(r["hold_n"]) == [18] and g(r["hold_s"]) == [18], f"the gate by holding, 375 ms: the note let go first {r['hold_n']}, the step first {r['hold_s']}")
    if old is not None:
        o = run(old, oman)
        check(o["leds"][2] != o["leds"][0] and g(o["step_first_rel"]) == [6] and g(o["chord"]) == [6, 24] and g(o["hold_s"]) != [18],
              f"the build before: the selector's LEDs left ({[hex(x) for x in o['leds'][2][:6]]}), the step let go first {o['step_first_rel']}, the chord {o['chord']}, "
              f"held 375 ms with the step let go first {o['hold_s']}")
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    old = Path(a[3]).read_bytes() if len(a) > 4 else None
    om = json.loads(Path(a[4]).read_text()) if len(a) > 4 else None
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), old, om) else 0)
