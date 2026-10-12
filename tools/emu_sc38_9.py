"""SC38.9 ARM tests (live RAM dump, the real routes: the controller's button press / release 0x08033320 / 0x0803381A, pads 0x08033282 / 0x080332FE, the
LED task 0x08034196): Synth 1 + Synth 2 pressed together = a split keyboard (srcview.use_split).

    python tools/emu_sc38_9.py SC38.9.bin SC38.9_manifest.json SC38.8.bin SC38.8_manifest.json
  * Synth 1's Note view, Synth 1 held (a second press: the source view) + Synth 2 pressed: the split keyboard on, Synth 1's Note view underneath;
  * pads 1-16: notes of Synth 1 (its note interface), the same notes its own Note view gives for pads 17-32; pads 17-32: notes of Synth 2; each release
    a note-off on the synth that played it;
  * the LEDs: pads 1-16 = Synth 1's keyboard window, 17-32 = Synth 2's;
  * a pad held when Note (a view button) is pressed: released, the split off, its physical release does nothing more; the Note view as the stock;
  * the buttons released: no split from Synth 2 alone; a single Synth button during the split ends it and is not taken for the source view's second press;
  * Play / Octave leave the split on;
  * the previous build: Synth 1 held + Synth 2 = Synth 2's view (the stock).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
import srcview as SV  # noqa: E402

CT = 0x20040DB8
NOTE_ON, NOTE_OFF = 0x0801D38E, 0x0801D942          # the note interface (vtable 0x0805BF54) slots 0 / 1
NI = {0x200413F0: 1, 0x200416E4: 2}                 # [Note view + 0x18] of Synth 1 / Synth 2


def run(img, man):
    e = E35(img, man)
    gst = int(man["report"]["sc14"]["labels"]["c_gst"], 16)
    notes = []
    def hk(uc, a, s, d):
        o = uc.reg_read(UC_ARM_REG_R0)
        if o in NI: notes.append(("on" if a == NOTE_ON else "off", NI[o], uc.reg_read(UC_ARM_REG_R1)))
    e.uc.hook_add(UC_HOOK_CODE, hk, begin=NOTE_ON, end=NOTE_ON); e.uc.hook_add(UC_HOOK_CODE, hk, begin=NOTE_OFF, end=NOTE_OFF)
    press = lambda i: e.call(0x08033320, MGR, i, maxins=8_000_000)
    release = lambda i: e.call(0x0803381A, MGR, i, maxins=8_000_000)
    pad = lambda p: e.call(PRESS, MGR, p, 100, maxins=8_000_000)
    rel = lambda p: e.call(RELEASE, MGR, p, maxins=8_000_000)
    def state():
        e.call(gst); g = e.uc.reg_read(UC_ARM_REG_R0); return e.r8(g + 20) if g else None
    def frame():
        e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000); return list(struct.unpack("<32H", bytes(e.uc.mem_read(0x2006E000, 64))))
    def window(t):
        e.call(0x08043A84, CT, t, 1); v = e.uc.reg_read(UC_ARM_REG_R0)
        e.call(e.r32(e.r32(v) + 28) & ~1, v, maxins=900000); return list(struct.unpack("<16H", bytes(e.uc.mem_read(e.uc.reg_read(UC_ARM_REG_R0), 32))))
    def direct(t, p):                                                         # the note a Note view plays for its pad p (on, then off)
        e.call(0x08043A84, CT, t, 1); v = e.uc.reg_read(UC_ARM_REG_R0); notes.clear()
        e.call(e.r32(e.r32(v)) & ~1, v, p, 100, maxins=5_000_000); e.call(e.r32(e.r32(v) + 4) & ~1, v, p, maxins=5_000_000)
        n = [x[2] for x in notes if x[0] == "on" and x[1] == t + 1]; notes.clear(); return n[0] if n else None
    out = {}
    e.set_p0(e.r32(CONT + 0x188), 0); press(0); release(0)                      # Synth 1's view
    if e.r8(MGR + 0x152) != 1: press(9); release(9)                             # its Note view
    out["view0"] = e.r8(MGR + 0x152)
    out["want"] = (direct(0, 18), direct(1, 20))                                # pad 3 -> Synth 1's pad 19; pad 21 -> Synth 2's pad 21
    press(0); press(1)                                                          # Synth 1 held + Synth 2
    out["st1"] = state(); out["view1"] = e.r8(MGR + 0x152)
    notes.clear(); pad(2); pad(20); out["on"] = list(notes); notes.clear(); rel(2); rel(20); out["off"] = list(notes)
    out["leds"] = frame(); out["w"] = (window(0), window(1))
    press(17); release(17); press(20); release(20); out["st_play"] = state()     # Play, Octave: still on
    pad(4); notes.clear(); press(9); out["exit"] = (state(), list(notes)); notes.clear(); rel(4); out["after_rel"] = list(notes); release(9)
    out["view_exit"] = e.r8(MGR + 0x152)
    release(1); release(0); out["st_rel"] = state()
    press(1); release(1); out["st_alone"] = state(); out["view_alone"] = e.r8(MGR + 0x152)
    press(0); release(0); press(9); release(9)
    press(1); press(0); out["st2"] = state()                                    # the other order: Synth 2 held + Synth 1
    release(0); release(1)
    press(0); release(0); out["st_single"] = state(); out["view_single"] = e.r8(MGR + 0x152)   # a single Synth button ends it (no source view)
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man)
    SPL, SRC = SV.F_SPLIT, SV.F_SRC
    on = lambda st: st is not None and bool(st & SPL)
    check(o["view0"] == 1 and on(o["st1"]) and o["view1"] == 1 and not o["st1"] & SRC, f"Synth 1 held + Synth 2: the split keyboard on (state {o['st1']:#x}), Synth 1's Note view underneath ({o['view0']} -> {o['view1']}), the source view closed")
    w1, w2 = o["want"]
    check(o["on"] == [("on", 1, w1), ("on", 2, w2)], f"pad 3 = Synth 1's note {w1}, pad 21 = Synth 2's note {w2} ({o['on']})")
    check(o["off"] == [("off", 1, w1), ("off", 2, w2)], f"the releases: note-offs on the synth that played ({o['off']})")
    check(o["leds"][:16] == o["w"][0] and o["leds"][16:] == o["w"][1], f"the LEDs: pads 1-16 = Synth 1's keys, 17-32 = Synth 2's\n    got  {[hex(x) for x in o['leds']]}")
    check(on(o["st_play"]), "Play and Octave leave the split keyboard on")
    st, n = o["exit"]
    check(not on(st) and len(n) == 1 and n[0][0] == "off" and o["after_rel"] == [], f"Note pressed with a pad held: the split off, its note released ({n}), the physical release does nothing more ({o['after_rel']})")
    check(o["st_rel"] is not None and not o["st_rel"] & (SV.F_HELD * 3), f"Synth 1 / 2 released: their held bits clear ({o['st_rel']:#x})")
    check(not on(o["st_alone"]) and o["view_alone"] == 10, f"Synth 2 alone: no split, Synth 2's view as the stock ({o['view_alone']})")
    check(on(o["st2"]), "the other order (Synth 2 held + Synth 1): the split keyboard on")
    check(not on(o["st_single"]) and not o["st_single"] & SRC, f"a single Synth button ends the split, not taken for the source view ({o['st_single']:#x}, view {o['view_single']})")
    q = run(prev, prev_man)
    check(not on(q["st1"]) and q["view1"] == 10, f"SC38.8: Synth 1 held + Synth 2 = Synth 2's view ({q['view1']}), no split")
    print("SC38.9 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
