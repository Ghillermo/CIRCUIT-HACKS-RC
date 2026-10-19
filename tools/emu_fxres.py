"""SC44.4 tests: the master filter resonance on Shift + Octave UP / DOWN in the FX view (fxres.py), through the controller and the real LED task.

    python tools/emu_fxres.py NEW.bin NEW_manifest.json PREVIOUS.bin STOCK.bin
  * FX view, Shift + Octave UP: +16 a press, stops at 127; Shift + Octave DOWN: -16, stops at 0 (no wrap); the DSP gets X:$D0; the sends page,
    the filter position and every send stay;
  * without Shift Octave UP / DOWN still pick the delay / reverb page, the resonance stays;
  * the "1-16 / 17-32" button (id 21): its stock bytes; in the FX view the resonance stays;
  * outside the FX view Shift + Octave and id 21 leave the stores and views as PREVIOUS (SC44.3) does;
  * LEDs in the FX view: Octave UP / DOWN yellow with Shift, their page colours without; LED 53 is not the old green.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_5 import EA, FX  # noqa: E402
from emu_sc08 import MGR  # noqa: E402
import fxkeys as K  # noqa: E402
import fxres as R  # noqa: E402
import leds18 as L18  # noqa: E402
import packio as PK  # noqa: E402
from thumb import b_w  # noqa: E402

BASE = 0x08010000
UP, DN, PAIR = 20, 19, 21


class EF(EA):
    def __init__(self, img):
        super().__init__(img)
        def zero(uc, a, s, d): uc.reg_write(UC_ARM_REG_R0, 0); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        for f in (PK.SEM_TAKE, PK.SEM_GIVE, PK.DSP_READ): self.uc.hook_add(UC_HOOK_CODE, zero, begin=f, end=f)
    def frame(self, shift=False):
        from emu_sc05 import STOP
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(0x08033B3E, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
        return struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138)))


def main(img, man, prev, stock):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["fxres"]["labels"].items()}
    o = K.BTN_PAGE - BASE
    check(img[o:o + 4] == stock[o:o + 4], f"id 21: the stock bytes ({img[o:o + 4].hex()})")
    for a_, lab in ((K.BTN_DOWN, "c_rsdn"), (K.BTN_UP, "c_rsup")):
        check(img[a_ - BASE:a_ - BASE + 4] == b_w(a_, L[lab]), f"{a_:#x} -> b.w {lab}")

    # ---- FX view: Shift + Octave
    e = EF(img); e.btn(15)
    check(e.view() == FX, "FX button: FX view active")
    e.btn(UP); e.pset(0x21, 1, 50); e.pset(0x21, 0, 20)
    sends = [e.get(0x20, i) for i in range(25)]
    e.flush()
    ups = []
    for _ in range(7): e.btn(UP, shift=True); ups.append(e.get(0x21, 1))
    check(ups == [66, 82, 98, 114, 127, 127, 127], f"Shift + Octave UP: +16 a press, stops at 127 {ups}")
    w = e.flush(); check(w.get(0xD0) == 127 << 16, f"the DSP gets X:$D0 = {hex(w.get(0xD0, -1))}")
    e.btn(UP, shift=True); check(e.flush() == {}, "at 127 Shift + Octave UP changes nothing")
    check(e.page() == 1, "Shift + Octave UP: the sends page stays (delay)")
    dns = []
    for _ in range(10): e.btn(DN, shift=True); dns.append(e.get(0x21, 1))
    check(dns == [111, 95, 79, 63, 47, 31, 15, 0, 0, 0], f"Shift + Octave DOWN: -16 a press, stops at 0 {dns}")
    w = e.flush(); check(w.get(0xD0, -1) == 0, f"the DSP gets X:$D0 = {hex(w.get(0xD0, -1))}")
    check(e.page() == 1, "Shift + Octave DOWN: the sends page stays (delay)")
    check(e.get(0x21, 0) == 20 and [e.get(0x20, i) for i in range(25)] == sends, "filter position and every send / FX parameter untouched")
    e.pset(0x21, 1, 8); e.btn(DN, shift=True); check(e.get(0x21, 1) == 0, "from 8, Shift + Octave DOWN: 0")
    e.pset(0x21, 1, 120); e.btn(UP, shift=True); check(e.get(0x21, 1) == 127, "from 120, Shift + Octave UP: 127")
    # ---- without Shift: the pages
    e.pset(0x21, 1, 50); e.flush()
    e.btn(DN); check(e.page() == 0 and e.get(0x21, 1) == 50, "Octave DOWN: reverb page, the resonance stays")
    e.btn(UP); check(e.page() == 1 and e.get(0x21, 1) == 50, "Octave UP: delay page, the resonance stays")
    e.flush(); e.btn(PAIR)
    check(e.get(0x21, 1) == 50 and e.flush().get(0xD0) is None, "1-16 / 17-32 in the FX view: the resonance stays")
    # ---- LEDs
    f0, f1 = e.frame(), e.frame(shift=True)
    check((f1[L18.LED_OCT_DN], f1[L18.LED_OCT_UP]) == (R.YELLOW, R.YELLOW), f"with Shift: Octave DOWN / UP yellow ({f1[51]:#x}, {f1[52]:#x})")
    check((f0[L18.LED_OCT_DN], f0[L18.LED_OCT_UP]) == (0x2A, 0x6B), f"without Shift: Octave DOWN / UP cream / peach ({f0[51]:#x}, {f0[52]:#x})")
    check(f0[53] != L18.LIGHT_GREEN and f1[53] != L18.LIGHT_GREEN, f"LED 53 is not the old green ({f0[53]:#x}, {f1[53]:#x})")
    del e; gc.collect()
    # ---- outside the FX view: as SC44.3
    def seq(image, prelude, presses):
        x = EF(image)
        for p in prelude: x.btn(p)
        x.pset(0x21, 1, 50)
        for b_, s in presses: x.btn(b_, shift=s)
        r = x.regions() + [bytes([x.get(0x21, 1)])]
        f = x.frame(shift=True)
        del x; gc.collect()
        return r, f
    for name, prelude in (("track view", []), ("Mixer", [14]), ("Patterns (13)", [13]), ("Preset (8)", [8])):
        pr = [(UP, True), (DN, True), (PAIR, False), (UP, True)]
        (a, fa), (b, fb) = seq(prev, prelude, pr), seq(img, prelude, pr)
        check(a == b, f"{name}: Shift + Octave and 1-16 / 17-32 leave the stores and views as SC44.3 (resonance {b[-1][0]})")
        check(fa == fb, f"{name}: the LEDs with Shift as SC44.3")
    print("SC44.4 fxres RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes(), Path(a[3]).read_bytes()) else 0)
