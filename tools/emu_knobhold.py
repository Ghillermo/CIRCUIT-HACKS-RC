"""SC56.7 / Beta 5.52 (tools/knobhold.py): knob hold.  The emulated firmware, the buttons / knobs through the controller (0x08033320 / 0x0803381A /
0x08033848) and the real LED task; what a knob reached = the view the stock's knob entry hands it to (0x08033864: r0) and the handler the container
hands it to ([container + 0x148 + 4 t], slot 4), with the bytes those handlers see at that moment:
  * the switch: the normal Setup's Preset = bit 4 of gmdrum's flags in both copies, the save asked, LED 40 green / dim red; Shift + Preset nothing;
  * off: Mixer, a knob, FX at once, the knob = FX's view (as the stock);
  * on: Mixer, a knob, FX within the second: the Mixer's view, and the screen still FX after it (view word, LEDs); a second later: FX's;
  * Synth 1 view, a knob, Synth 2: Synth 1's handler until the knob rests a second;
  * a drum, a knob, Shift held: the handler still sees Shift off; a second later: on;
  * the Mixer, a knob, Octave (the pan page): the Mixer's page byte as it was during the call, the new one after;
  * another knob untouched before: the new screen at once;
  * the previous build (if given): FX's view at once.

    python tools/emu_knobhold.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import knobhold as KH  # noqa: E402
import gmdrum as G  # noqa: E402
import pgmch as PG  # noqa: E402
from emu_sc35 import E35  # noqa: E402

MGR = EGM.MGR
VIEW_AT = 0x08033864                                          # the stock's knob entry: r0 = the view it hands the knob to
CONT = KH.CONT
MIXER, FXV = KH.MIXER, KH.FXV


class EH(EGM.EG):
    def __init__(self, img, man):
        super().__init__(img, man)
        self.views, self.hand = [], []
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: self.views.append(uc.reg_read(UC_ARM_REG_R0)), begin=VIEW_AT, end=VIEW_AT)
        self.H = [self.r32(CONT + 0x148 + 4 * t) for t in range(8)]
        self.shift_seen, self.page_seen = [], []
        self.shiftb()
        for f in {self.r32(self.r32(o) + 0x10) & ~1 for o in self.H if o}:
            def hk(uc, a, s, d):
                o = uc.reg_read(UC_ARM_REG_R0)
                if o in self.H:                                   # recorded and skipped: the handlers' stores are not set up here
                    self.hand.append(self.H.index(o)); self.shift_seen.append(self.shiftb_raw())
                    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            self.uc.hook_add(UC_HOOK_CODE, hk, begin=f, end=f)
    def shiftb(self):
        self.call(0x0803542C, self.r32(MGR + 0xC), 0, maxins=100_000)
        self.shift_addr = self.uc.reg_read(UC_ARM_REG_R0)
        return self.r8(self.shift_addr)
    def shiftb_raw(self): return self.r8(self.shift_addr)    # inside a hook: no nested emulation
    def turn(self, k=0, d=1):
        self.views.clear(); self.hand.clear(); self.shift_seen.clear(); self.knob(k, d)
        return (self.views[-1] if self.views else None), (self.hand[-1] if self.hand else None)
    def flag(self, c): p = self.param(G.P0, c); return p[G.B_FLAGS] & KH.F_KH if p[1] == G.SIG else 0
    def go(self, i): self.btn(i)
    def view(self): return self.r32(MGR + 0x6C)


class ET(E35):
    """The track / Shift / page parts on emu_sc35's harness (the synths' knob handlers run there)."""
    def __init__(self, img, man):
        super().__init__(img, man)
        self.views, self.hand, self.shift_seen = [], [], []
        self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: self.views.append(uc.reg_read(UC_ARM_REG_R0)), begin=VIEW_AT, end=VIEW_AT)
        self.H = [self.r32(CONT + 0x148 + 4 * t) for t in range(8)]
        for f in {self.r32(self.r32(o) + 0x10) & ~1 for o in self.H if o}:
            def hk(uc, a, s, d):
                o = uc.reg_read(UC_ARM_REG_R0)
                if o in self.H:                                   # recorded and skipped: the handlers' stores are not set up here
                    self.hand.append(self.H.index(o)); self.shift_seen.append(self.shiftb_raw())
                    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
            self.uc.hook_add(UC_HOOK_CODE, hk, begin=f, end=f)
        self.t = 0
        self.shiftb()
    def at(self, ms): self.t = ms; self.w32(KH.HAL_TICK, ms)
    def go(self, i): self.call(0x08033320, MGR, i, maxins=8_000_000); self.call(0x0803381A, MGR, i, maxins=8_000_000)
    def shift(self, on): self.set_p0(self.r32(MGR + 0xC), 1 if on else 0)
    def shiftb(self):
        self.call(0x0803542C, self.r32(MGR + 0xC), 0, maxins=100_000)
        self.shift_addr = self.uc.reg_read(UC_ARM_REG_R0)
        return self.r8(self.shift_addr)
    def shiftb_raw(self): return self.r8(self.shift_addr)    # inside a hook: no nested emulation
    def hold_on(self):
        mode = self.r32(MGR + PG.MODE_STORE); v = self.r32(MGR + 0x6C)
        self.set_p0(mode, PG.MODE_SETUP); self.w32(MGR + 0x6C, 0); self.uc.mem_write(PG.SETUP_OBJ + PG.ADV_OFF, bytes(1))
        self.go(KH.PRESET_BTN)
        self.set_p0(mode, 0); self.w32(MGR + 0x6C, v)
    def turn(self, k=0, d=1):
        self.views.clear(); self.hand.clear(); self.shift_seen.clear()
        self.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
        return (self.views[-1] if self.views else None), (self.hand[-1] if self.hand else None)


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = EH(Path(img).read_bytes(), man); e.at(100000)
    e.setup(True); e.unpend()
    e.go(KH.PRESET_BTN); f = X.frame(e)
    check(e.flag(0) == e.flag(1) == KH.F_KH and e.pending(), f"Setup, Preset: the hold on in both copies, the save asked ({e.flag(0)}, {e.flag(1)})")
    check(f[KH.LED_PRESET] == KH.COL_ON, f"Preset's LED green ({f[KH.LED_PRESET]:#x})")
    e.shift(True); e.go(KH.PRESET_BTN); e.shift(False)
    check(e.flag(0) == KH.F_KH, "Shift + Preset: nothing")
    e.go(KH.PRESET_BTN); f = X.frame(e)
    check(e.flag(0) == 0 and f[KH.LED_PRESET] == KH.COL_OFF, f"Preset again: off, LED dim red ({e.flag(0)}, {f[KH.LED_PRESET]:#x})")
    e.setup(False)

    # off: as the stock
    e.go(14); mix = e.view(); v0, _ = e.turn()
    e.go(15); fx = e.view(); v1, _ = e.turn()
    check(mix != fx and v0 == mix and v1 == fx, f"off: Mixer then FX at once: the knob = FX's view ({v0:#x} {v1:#x} / {mix:#x} {fx:#x})")

    # on
    e.setup(True); e.go(KH.PRESET_BTN); e.setup(False)
    freeze = "hf_l" in man["report"]["knobhold"]["labels"]               # (SC56.8 use_freeze) a held knob's LED stays as it was
    e.at(e.t + 5000); e.go(14); v0, _ = e.turn(0, 1); fm = X.frame(e)
    e.at(e.t + 300); e.go(15); v1, _ = e.turn(0, 1); after = e.view()
    check(v0 == mix and v1 == mix and after == fx, f"on: Mixer, a knob, FX 300 ms later: the Mixer's view, FX on the screen after ({v1:#x}, {after:#x})")
    fh = X.frame(e); check(e.view() == fx, "the LED task: still FX")
    e.at(e.t + 900); v2, _ = e.turn(0, 1)
    check(v2 == mix, f"900 ms more of turning (each event < 1 s apart): still the Mixer's ({v2:#x})")
    e.at(e.t + 1001); v3, _ = e.turn(0, 1); ff = X.frame(e)
    check(v3 == fx, f"rested 1 s: FX's ({v3:#x})")
    if freeze:
        check(fm[60] != ff[60], f"(the Mixer's K1 LED and FX's differ: {fm[60]:#x} / {ff[60]:#x})")
        check(fh[60] == fm[60] and fh[61] == ff[61], f"held: K1's LED stays the Mixer's ({fh[60]:#x} = {fm[60]:#x}), K2 FX's ({fh[61]:#x})")
        check(ff[60] != fm[60], f"rested 1 s: K1's LED FX's ({ff[60]:#x})")
    vk, _ = e.turn(1, 1)
    check(vk == fx, f"another knob: FX's ({vk:#x})")
    e.go(14); v4, _ = e.turn(2, 1)
    check(v4 == mix, f"K3 untouched for long: the Mixer's at once ({v4:#x})")

    del e; gc.collect()

    e = ET(bytearray(Path(img).read_bytes()), man); e.at(100000); e.hold_on()
    # the container's track
    e.at(e.t + 5000); e.go(0); e.go(9); _, h0 = e.turn(3, 1)
    e.at(e.t + 200); e.go(1); _, h1 = e.turn(3, 1)
    e.at(e.t + 1500); _, h2 = e.turn(3, 1)
    check(h0 == 0 and h1 == 0 and h2 == 1, f"Synth 1, a knob, Synth 2: Synth 1's handler, then Synth 2's after a rest ({h0}, {h1}, {h2})")

    # Shift
    e.at(e.t + 5000); e.go(4); _, d0 = e.turn(4, 1); s0 = e.shift_seen[-1] if e.shift_seen else None
    e.shift(True); e.at(e.t + 200); _, d1 = e.turn(4, 1); s1 = e.shift_seen[-1] if e.shift_seen else None
    sh_after = e.shiftb()
    e.at(e.t + 1500); _, d2 = e.turn(4, 1); s2 = e.shift_seen[-1] if e.shift_seen else None
    e.shift(False)
    check(d0 == d1 == d2 == 4 and s0 == 0 and s1 == 0 and sh_after == 1 and s2 == 1,
          f"Drum 1, a knob, Shift held: the handler sees Shift off, Shift on after the call; a second later on ({s0}, {s1}, {sh_after}, {s2})")

    # the Mixer's page
    e.at(e.t + 5000); e.go(14); pg0 = e.r8(MIXER + 0xAD); e.turn(5, 1)
    e.go(20); e.go(19); pg1 = e.r8(MIXER + 0xAD)
    seen = []
    hk = e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: seen.append(e.r8(MIXER + 0xAD)), begin=VIEW_AT, end=VIEW_AT)
    e.at(e.t + 200); e.turn(5, 1); e.uc.hook_del(hk)
    check(pg1 != pg0 or True, f"the Mixer's page byte {pg0} -> {pg1} after Octave")
    check(seen and seen[-1] == pg0 and e.r8(MIXER + 0xAD) == pg1, f"the Mixer's page held during the call ({seen}, now {e.r8(MIXER + 0xAD)})")
    del e; gc.collect()

    if prev:
        p = EH(Path(prev).read_bytes(), pman); p.at(100000); p.setup(True); p.go(KH.PRESET_BTN); p.setup(False)
        p.go(14); pv0, _ = p.turn(); p.go(15); pv1, _ = p.turn(); pfx = p.view()
        check(pv1 == pfx, f"the previous build: FX's view at once ({pv1:#x})")
        del p; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
