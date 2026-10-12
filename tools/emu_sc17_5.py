"""SC17.5 ARM tests: FX view keys (Octave UP / DOWN = delay / reverb sends, button 16 = reset) and the pad 30 / 31
synth source modes, on the live RAM dump (unicorn).  The DSP side is tools/emu_sc17_5_dsp.py.

    python tools/emu_sc17_5.py STOCK.bin SC17.4.bin SC17.5.bin SC17.5_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc08 import E8, MGR  # noqa: E402
from shi_capture import attach  # noqa: E402
import emu_sc15 as T15  # noqa: E402
import fxkeys as K  # noqa: E402
from thumb import b_w  # noqa: E402

FX = 0x200443B4                       # FX view object (controller + 0x44)
MIXER = 0x200447D4
GETTER = 0x08036192
FLUSH = 0x080213B0                    # DSP flush task: one dirty group per call


class EA(E8):
    def __init__(self, image):
        gc.collect()                  # every instance maps ~0.5 GB: free the old ones (Windows runs out otherwise)
        super().__init__(image)
        def delay(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, delay, begin=0x0801BE78, end=0x0801BE78)        # sleep(ms): the clock never advances
        self.shi = attach(self)
        self.stubs[0x0801B394] = 'delay'
        self.call(0x08029492, maxins=50_000_000)                                       # post-upload init (tables)
        self.knob_calls = []
        self.clear_calls = []                                                           # stock Clear / Duplicate handler (button id)
        def ch(uc, a, s, d): self.clear_calls.append(uc.reg_read(UC_ARM_REG_R1))
        self.uc.hook_add(UC_HOOK_CODE, ch, begin=0x08041530, end=0x08041530)
        def kh(uc, a, s, d): self.knob_calls.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        self.uc.hook_add(UC_HOOK_CODE, kh, begin=0x08050830, end=0x08050830)           # FX send page: knob handler
        def fl(uc, a, s, d):
            uc.reg_write(UC_ARM_REG_R0, 1); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        self.uc.hook_add(UC_HOOK_CODE, fl, begin=0x080297A4, end=0x080297A4)           # DSP ready flag for the flush task

    def btn(self, b, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(0x08033320, MGR, b, maxins=900000); self.call(0x0803381A, MGR, b, maxins=900000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)

    def view(self): return self.r32(MGR + 0x6C)
    def page(self): return self.store_p0(self.r32(FX + 0x20))
    def get(self, t, i):
        self.call(GETTER, t, i, maxins=900000); return self.uc.reg_read(UC_ARM_REG_R0)
    def pset(self, t, i, v):
        ctx = self.r32(self.r32(self.r32(0x200069E4) + 0x10)) + 4
        self.call(K.PARAM_SET, ctx, t, i, v, maxins=900000)
    def knob(self, k, delta):
        self.knob_calls.clear(); self.call(0x08033848, MGR, k, delta, maxins=900000); return list(self.knob_calls)
    def flush(self):
        self.shi.writes.clear()
        for _ in range(8): self.call(FLUSH, maxins=50_000_000)
        return {a: v for c, sp, a, v in self.shi.writes if c == 0 and sp == 'x'}
    def sub_vals(self, sub):
        st = self.r32(sub + 0x14)
        return [self.store_p0_idx(st, k) for k in range(8)]
    def store_p0_idx(self, st, k):
        self.call(0x0803542C, st, k); return self.r8(self.uc.reg_read(UC_ARM_REG_R0))

    def regions(self):
        return [bytes(self.uc.mem_read(a, n)) for a, n in ((0x20010000, 0x2000), (0x20038000, 0x20044C00 - 0x20038000))]


def main(stock, ref, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]
    L = {k: int(v, 16) for k, v in rep["fxkeys"]["labels"].items()}
    c_gst = int(rep["sc14"]["labels"]["c_gst"], 16); c_gfst = int(rep["sc17"]["labels"]["c_gfst"], 16)
    CLEAR = bool(rep["fxkeys"].get("clear_reset"))          # SC17.6: Duplicate = reset, button 16 = resonance step
    K.CLEAR_RESET = CLEAR
    K.PAGE_BTN = bool(rep["fxkeys"].get("page_btn"))      # SC19: the resonance step is on the real 1-16 / 17-32 button (id 21), 16 / 17 = Record / Play
    PB = 21 if K.PAGE_BTN else 16
    RB = 24 if CLEAR else 16
    # ---- hooks installed, stock bytes elsewhere
    for hook, lab, _ in K.hooks():
        o = hook - 0x08010000
        check(img[o:o + 4] == b_w(hook, L[lab]), f"{hex(hook)} -> b.w {lab}")
    # ---- Octave keys in the FX view
    e = EA(img)
    e.btn(15)
    check(e.view() == FX, "FX button: FX view active")
    e.btn(20); check(e.page() == 1, "Octave UP: delay page (p0 = 1)")
    k = e.knob(2, 3); check(k == [(e.r32(FX + 0xC), 2, 3)], f"knob 3 goes to the delay send page {[(hex(a), b, c) for a, b, c in k]}")
    e.btn(19); check(e.page() == 0, "Octave DOWN: reverb page (p0 = 0)")
    k = e.knob(5, -2); check(k == [(e.r32(FX + 0x10), 5, -2 & 0xFFFFFFFF)], f"knob 6 goes to the reverb send page {[(hex(a), b, c) for a, b, c in k]}")
    e.btn(19); check(e.page() == 0, "Octave DOWN again: still reverb")
    e.btn(20); e.btn(20); check(e.page() == 1, "Octave UP twice: delay")
    # ---- everywhere else the buttons are as before (SC17.4 = stock behaviour for these buttons)
    def seq(image, prelude, presses):
        x = EA(image)
        for p in prelude: x.btn(p)
        for p in presses: x.btn(*p) if isinstance(p, tuple) else x.btn(p)
        return x.regions()
    others = [19, 20, 16, 17] + ([23, 24] if CLEAR else [])
    for name, prelude in (("track view", []), ("Mixer", [14]), ("Master FX (Mixer twice)", [14, 14]), ("Preset (button 8)", [8]), ("Patterns (13)", [13])):
        a, b = seq(ref, prelude, others), seq(img, prelude, others)
        check(a == b, f"{name}: buttons {' / '.join(map(str, others))} leave the stores and views exactly as SC17.4")
    a, b = seq(ref, [15], [17]), seq(img, [15], [17])
    check(a == b, "FX view: button 17 (the other of the pair) as SC17.4")
    if CLEAR:
        a, b = seq(ref, [15], [23, (23, True), (24, True)]), seq(img, [15], [23, (23, True), (24, True)])
        check(a == b, "FX view: Clear (23), Shift + Clear and Shift + Duplicate as SC17.4 (no reset with Shift; Clear untouched)")
    a, b = seq(ref, [15], []), seq(img, [15], [])
    check(a == b, "FX view entered: as SC17.4")
    # ---- reset
    e = EA(img)
    e.btn(15)
    for i in range(8): e.pset(0x20, i, 40 + i); e.pset(0x20, 11 + i, 60 + i)
    e.pset(0x21, 0, 20); e.pset(0x21, 1, 50)
    other = [e.get(0x20, i) for i in (8, 9, 10, 19, 20, 21, 22, 23, 24)] + [e.get(0x21, i) for i in range(2, 10)]
    e.call(c_gst); st = e.uc.reg_read(UC_ARM_REG_R0)
    e.uc.mem_write(st + 4, bytes([5, 3, 2, 1]))
    e.call(c_gfst); gb = e.uc.reg_read(UC_ARM_REG_R0)
    e.uc.mem_write(gb + 5, bytes([0x0B, 0x13]))
    check([e.get(0x20, i) for i in range(8)] == [40 + i for i in range(8)] and e.get(0x21, 0) == 20, "test setup: sends and filter set")
    e.flush(); e.clear_calls.clear(); e.btn(RB)
    if CLEAR: check(e.clear_calls[:1] == [24], f"reset on Duplicate: the stock Duplicate handler still runs {e.clear_calls}")
    check([e.get(0x20, i) for i in range(8)] == [0] * 8, "reset: the 8 reverb sends = 0")
    check([e.get(0x20, 11 + i) for i in range(8)] == [0] * 8, "reset: the 8 delay sends = 0")
    check(e.get(0x21, 0) == 64 and e.get(0x21, 1) == 50, "reset: master filter centred (64), resonance untouched (50)")
    after = [e.get(0x20, i) for i in (8, 9, 10, 19, 20, 21, 22, 23, 24)] + [e.get(0x21, i) for i in range(2, 10)]
    check(after == other, "reset: reverb / delay parameters and the other master parameters (compressor, gain) untouched")
    check(list(e.uc.mem_read(st + 4, 4)) == [0, 0, 0, 0] and list(e.uc.mem_read(gb + 5, 2)) == [0, 0],
          "reset: SC14 Gater / Auto-Filter and Master FX held / latched pads cleared")
    check(e.sub_vals(e.r32(FX + 0xC)) == [0] * 8 and e.sub_vals(e.r32(FX + 0x10)) == [0] * 8, "reset: the knob values of both send pages follow (no jump on the next turn)")
    w = e.flush()
    sends = (0xE3, 0xE4, 0xAB, 0xB5, 0xBF, 0xC9, 0xE5, 0xE6, 0xE7, 0xE8, 0xAC, 0xB6, 0xC0, 0xCA, 0xE9, 0xEA)
    check(all(w.get(a) == 0 for a in sends) and w.get(0xCF) == 0x400000 and w.get(0xD0, 50 << 16) == 50 << 16,
          f"reset: DSP gets the 16 send gains = 0 and X:$CF = $400000; X:$D0 (resonance) keeps its value ({len(w)} writes)")
    e.btn(RB)
    check(e.flush() == {}, "reset again: nothing left to change")
    # knob after the reset starts from 0 (no jump)
    e.btn(20); e.knob(0, 5)
    check(e.get(0x20, 11) == 5, "after the reset a delay-send knob turn starts from 0")
    if CLEAR:
        # ---- button 1-16 / 17-32: master filter resonance += 32 (after the maximum: 0)
        e = EA(img)
        e.btn(15)
        e.pset(0x21, 1, 50); e.pset(0x21, 0, 20)
        sends = [e.get(0x20, i) for i in range(25)]
        e.flush()
        seq_ = []
        for _ in range(9):
            e.btn(PB); seq_.append(e.get(0x21, 1))
        check(seq_ == [82, 114, 127, 0, 32, 64, 96, 127, 0], f"button {PB} in the FX view: resonance 50 +32 each press, clamped to 127, then 0 {seq_}")
        e.btn(PB); w = e.flush()
        check(e.get(0x21, 1) == 32 and w.get(0xD0) == 32 << 16, f"DSP gets X:$D0 = {hex(w.get(0xD0, -1))}")
        check(e.get(0x21, 0) == 20 and [e.get(0x20, i) for i in range(25)] == sends, "filter position and every send / FX parameter untouched")
        check(e.page() in (0, 1), f"button {PB} no longer touches the FX view")
        if K.PAGE_BTN:
            e = EA(img); e.btn(15); e.pset(0x21, 1, 50); e.flush()
            for b_ in (16, 17):
                e.btn(b_)
            check(e.get(0x21, 1) == 50 and e.flush() == {}, "Record / Play (ids 16 / 17) in the FX view: stock, the resonance is untouched")
            for view_btn in (14, 13):
                e = EA(img); e.btn(view_btn); e.pset(0x21, 1, 50); e.flush(); e.btn(21)
                check(e.get(0x21, 1) == 50 and e.flush() == {}, f"button 21 outside the FX view (button {view_btn}): stock, the resonance is untouched")
    # ---- pads 30 / 31: modes 5 / 6
    NM = rep.get("linein3", {}).get("modes", 7)
    T15.N_MODES = NM; T15.B.N_MODES = NM
    T15.ST = int(rep["sc17"]["sc14_state"], 16)
    _init = T15.E15.__init__
    def init(self, image): gc.collect(); _init(self, image)
    T15.E15.__init__ = init
    def c15(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    if rep.get("srcview"):
        print("     (SC19.1+: the synth source modes have their own view, opened by a second Synth press: tested by emu_sc19_1.py)")
    elif rep.get("modeview"):
        print("     (mode pads moved to the Shift + Scales view: tested by emu_sc17_7.py)")
    else:
        T15.arm_tests(stock, img, c15)
    _sinit = T15.Session.__init__
    def sinit(self, image): gc.collect(); _sinit(self, image)          # each Session keeps ~0.3 GB of SHI words: free the old ones
    T15.Session.__init__ = sinit
    # modes 0-4 of the DSP: same as linein2 (the new code is a superset): noise = stock, In 1/2 x2, inverted x(-2)
    T15.N_MODES = 5; T15.GAIN = 2
    T15.dsp_tests(stock, img, c15)
    print("SC17.5 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    st, rf, im = (Path(sys.argv[i]).read_bytes() for i in (1, 2, 3))
    sys.exit(1 if main(st, rf, im, json.loads(Path(sys.argv[4]).read_text())) else 0)
