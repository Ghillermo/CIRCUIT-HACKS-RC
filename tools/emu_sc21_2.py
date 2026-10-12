"""SC21.2 ARM tests: Shift + knob in the FX view = the reverb / delay parameters (tools/fxparams.py), through the real controller routes on the live RAM dump.

    python tools/emu_sc21_2.py SC21.1.bin SC21.2.bin SC21.1_manifest.json SC21.2_manifest.json
  * the sub-view class (vtable 0x0805AF3C): slots 4 / 7 -> ours; nothing else of the image changes;
  * FX button (15) then Octave down / up = the reverb / delay page; with Shift held the knobs set the project parameters 0x20 / 8..10 (reverb type, decay, damping) and 19..24 (delay time, sync,
    feedback, width, L-R ratio, slew), through the listener the MIDI uses (0x08034D92), stepped parameters one step per click, clamped to their ranges; the other knobs do nothing; the sends are NOT touched;
  * without Shift the knobs are the stock ones: the same listener calls as SC21.1;
  * outside the FX view Shift + knob is as before;
  * the LEDs: with Shift held the knob LEDs of the page shown are the parameters' values as brightness (peach delay / cream reverb, the unused knobs dark); on release the stock LEDs are back,
    for both sub-views (the buffer is persistent).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_6 import E196, MGR, CONT  # noqa: E402
import fxparams as F  # noqa: E402

PARAM_SET, GETTER = 0x08034D92, 0x08036192
BASE = 0x08010000


class E212(E196):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.sets = []
        def h(uc, a, s, d): self.sets.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3)))
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PARAM_SET, end=PARAM_SET)
    def param(self, typ, idx):
        self.call(GETTER, typ, idx); return self.uc.reg_read(UC_ARM_REG_R0) & 0xFF
    def fx(self): return self.r32(MGR + 0x44)
    def sub(self, which): return self.r32(self.fx() + (0x0C if which == "delay" else 0x10))
    def go_fx(self, page):
        if self.r32(MGR + 0x6C) != self.fx():                                          # the FX button twice leaves the view
            self.call(0x08033320, MGR, 15, maxins=600000)
            self.call(0x0803381A, MGR, 15, maxins=600000)
        for b in (20 if page == "delay" else 19,):                                    # Octave up = delay, down = reverb (SC17.5)
            self.call(0x08033320, MGR, b, maxins=600000); self.call(0x0803381A, MGR, b, maxins=600000)
    def turn(self, k, delta, shift):
        self.sets.clear()
        self._knob19(k, delta, shift)
        return list(self.sets)
    def knobs(self): return self.frame()[60:68]


def main(prev, img, man1, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    w = lambda image, a: struct.unpack_from("<I", image, a - BASE)[0]
    L = {k: int(v, 16) for k, v in man["report"]["fxparams"]["labels"].items()}
    check(w(img, F.SLOT4) == L["c_fxknob"] | 1 and w(img, F.SLOT7) == L["c_fxleds"] | 1, "sub-view class: slots 4 / 7 -> c_fxknob / c_fxleds")
    check(w(prev, F.SLOT4) == F.STOCK_KNOB | 1 and w(prev, F.SLOT7) == F.STOCK_LEDS | 1, "SC21.1 has the stock slots there")
    gc.collect(); n = E212(img, man); gc.collect(); o = E212(prev, man1)
    # ---- the reverb page
    n.go_fx("reverb"); o.go_fx("reverb")
    check(n.r32(MGR + 0x6C) == n.fx() and n.sub("reverb") != n.sub("delay"), "FX view active, two sub-views")
    base_r = [n.param(0x20, i) for i in (8, 9, 10)]
    base_sends = [n.param(0x20, i) for i in range(0, 8)] + [n.param(0x20, i) for i in range(11, 19)]
    print("     reverb params at start", base_r)
    for k, (idx, mx, mul) in enumerate(F.REVERB):
        s = n.turn(k, 3, True)
        cur = n.param(0x20, idx)
        want_step = 1 if mx < 127 else 3
        want = min(mx, base_r[k] + want_step)
        check(s == ([(0x20, idx, want)] if want != base_r[k] else []) and cur == want, f"reverb K{k + 1} + Shift +3: index {idx} {base_r[k]} -> {cur} (max {mx}){' one step' if mx < 127 else ''}: {s}")
    for k in range(3, 8):
        s = n.turn(k, 3, True)
        check(s == [], f"reverb K{k + 1} + Shift: nothing ({s})")
    check([n.param(0x20, i) for i in range(0, 8)] + [n.param(0x20, i) for i in range(11, 19)] == base_sends, "the sends are untouched by the Shift knobs")
    for _ in range(10): n.turn(0, 1, True)
    check(n.param(0x20, 8) == 5, "reverb type clamps at 5 (Great Hall)")
    for _ in range(10): n.turn(0, -1, True)
    check(n.param(0x20, 8) == 0, "reverb type clamps at 0 (Chamber), a click left = one step")
    for _ in range(40): n.turn(1, 5, True)
    check(n.param(0x20, 9) == 127, "decay clamps at 127")
    for _ in range(40): n.turn(1, -5, True)
    check(n.param(0x20, 9) == 0, "decay clamps at 0")
    # without Shift: as SC21.1
    sends = lambda e: [e.param(0x20, i) for i in list(range(0, 8)) + list(range(11, 19))]
    for k in (0, 3, 7):
        n.turn(k, 4, False); o.turn(k, 4, False)
        check(sends(n) == sends(o) and sends(n) != base_sends, f"reverb K{k + 1} without Shift: the send changes exactly as in SC21.1 ({sends(n)[:8]})")
    # ---- the delay page
    n.go_fx("delay"); o.go_fx("delay")
    base_d = [n.param(0x20, 19 + i) for i in range(6)]
    print("     delay params at start", base_d)
    for k, (idx, mx, mul) in enumerate(F.DELAY):
        s = n.turn(k, 3, True)
        cur = n.param(0x20, idx)
        want_step = 1 if mx < 127 else 3
        want = min(mx, base_d[k] + want_step)
        check(s == ([(0x20, idx, want)] if want != base_d[k] else []) and cur == want, f"delay K{k + 1} + Shift +3: index {idx} {base_d[k]} -> {cur} (max {mx}){' one step' if mx < 127 else ''}: {s}")
    for k in (6, 7):
        s = n.turn(k, 3, True)
        check(s == [], f"delay K{k + 1} + Shift: nothing ({s})")
    for _ in range(50): n.turn(1, 1, True)
    check(n.param(0x20, 20) == 35, "time sync clamps at 35")
    for _ in range(50): n.turn(4, 1, True)
    check(n.param(0x20, 23) == 12, "L-R ratio clamps at 12")
    for _ in range(50): n.turn(5, -2, True)
    check(n.param(0x20, 24) == 0, "slew clamps at 0")
    for k in (0, 4, 7):
        n.turn(k, 4, False); o.turn(k, 4, False)
        check(sends(n) == sends(o), f"delay K{k + 1} without Shift: the sends are exactly SC21.1's ({sends(n)[8:16]})")
    # ---- other views: Shift + knob as before
    n.call(0x08033320, MGR, 4, maxins=600000); o.call(0x08033320, MGR, 4, maxins=600000)       # Drum 1
    a_ = n.turn(1, 3, True); b_ = o.turn(1, 3, True)
    check(a_ == b_, f"Drum 1 view: Shift + knob as in SC21.1 ({a_})")

    # ---- LEDs
    gc.collect(); n = E212(img, man); gc.collect(); o = E212(prev, man1)
    for page, colour, table in (("delay", F.COL_DELAY, F.DELAY), ("reverb", F.COL_REVERB, F.REVERB)):
        n.go_fx(page); o.go_fx(page)
        stock_frame = n.frame()
        check(stock_frame[60:68] == o.frame()[60:68], f"{page} page, no Shift: the knob LEDs are SC21.1's (the sends)")
        n.set_p0(n.r32(MGR + 0xC), 1)
        fr = n.frame(); fr2 = n.frame()
        exp = []
        for k in range(8):
            if k < len(table):
                idx, mx, mul = table[k]
                val = n.param(0x20, idx)
                exp.append(colour | (min(127, val * mul) + 2) << 8)
            else:
                exp.append(0)
        check(fr[60:68] == exp and fr == fr2, f"{page} page, Shift held: the knob LEDs = the parameters' values as brightness, colour {colour:#x}, unused knobs dark {[hex(x) for x in fr[60:68]]}")
        n.set_p0(n.r32(MGR + 0xC), 0)
        back = n.frame()
        check(back[60:68] == stock_frame[60:68], f"{page} page, Shift released: the stock knob LEDs are back")
    # both sub-views get the stock LEDs back, also the one not shown while Shift was held on the other page
    n.go_fx("delay"); st_d = n.frame()[60:68]
    n.set_p0(n.r32(MGR + 0xC), 1); n.frame()
    n.go_fx("reverb"); n.frame()                                                      # page switched with Shift held: the reverb sub-view is painted too
    n.set_p0(n.r32(MGR + 0xC), 0); n.frame()
    n.go_fx("delay"); back_d = n.frame()[60:68]
    check(back_d == st_d, "paged to the other sub-view with Shift held, then released: both are stock again")
    print("SC21.2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
