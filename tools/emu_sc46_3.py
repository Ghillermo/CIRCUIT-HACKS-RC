"""SC46.3 / Beta 3.20: gmdrum.use_v2(), janko, chords; through the controller (buttons, pads, knobs) and the real LED task.
  * GM: the number view open (K5), K4 to off closes it (the Setup's pads back, the save asked); with the mode off K5 changes nothing, no note,
    the knob LEDs untouched;
  * Jankó: in the custom scale's editor Shift + pad 8 = on (B_ON 2; pad 8 cyan); the LED task rebuilds the keyboard: the Note view's bottom row =
    root + 2 c, the row above + 1; the inverse table and the links on the screen; Octave = + / - 1 semitone (the stock's octave kept), Shift +
    Octave = the stock's; the expanded view's top row = the bottom + 3; the quantiser leaves every note, random-mutate = another of the twelve;
    Shift + pad 8 again = off, the stock's tables back;
  * chords (expanded Note view of Synth 1): Shift + pad 8 = on (no note; its release swallowed); a root = its chord through the track view's
    live note-on (each note, the pad's velocity), its release = each note off; the types (page 1 and Shift page 2), the inversion, the root an
    octave down, open voicing, diatonic (the scale's thirds), latch; the LEDs of rows 1-2 (and with Shift); the normal Note view and the chords
    off: the stock's single note;
  * the previous build (if given): Shift + pad 8 in the editor / in the expanded view: the stock's.

    python tools/emu_sc46_3.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_cscale as ECS  # noqa: E402
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import cscale as CS  # noqa: E402
import janko as J  # noqa: E402
import chords as CH  # noqa: E402
import gmdrum as G  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402

MGR = ECS.MGR
V0 = 0x200412E0


class E(ECS.EC):
    def __init__(self, img, man):
        super().__init__(bytearray(img), {k: int(v, 16) for k, v in man["report"]["cscale"]["labels"].items()})
        self.man = man; self.at(100000); self.transport(0)
        self.ons, self.offs = [], []
        def skip(uc): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        def on(uc, a, s, d): self.ons.append((uc.reg_read(UC_ARM_REG_R1) & 0xFF, uc.reg_read(UC_ARM_REG_R2) & 0xFF, uc.reg_read(UC_ARM_REG_R3) & 0xFF)); skip(uc)
        def off(uc, a, s, d):
            v, p = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1) & 0xFF
            self.offs.append((self.r8(v + 0x40 + p), p)); skip(uc)
        self.uc.hook_add(UC_HOOK_CODE, on, begin=CH.NOTE_ON, end=CH.NOTE_ON)
        self.uc.hook_add(UC_HOOK_CODE, off, begin=CH.NOTE_OFF, end=CH.NOTE_OFF)
    def press(self, q, vel=100, shift=False):
        if shift: self.shift(1)
        self.call(PRESS, MGR, q, vel, maxins=8_000_000)
        if shift: self.shift(0)
    def release(self, q): self.call(RELEASE, MGR, q, maxins=8_000_000)
    def tap(self, q, shift=False): self.press(q, shift=shift); self.release(q)
    def goto(self, sub):
        for _ in range(4):
            if self.r8(MGR + 0x152) == sub: return
            self.btn(9)
    def val(self, pad, view=V0): return self.r8(CS.KB + 0x14 + (self.r0(0x0804B174, view, pad) & 0xFF))
    def idx(self, pad, view=V0): return self.r0(0x0804B174, view, pad) & 0xFF
    def note_chord(self, q, vel=100):
        self.ons.clear(); self.offs.clear(); self.press(q, vel); on = list(self.ons); self.release(q); return on, list(self.offs)


def run_gm(img, man):
    o = {}
    e = EGM.EG(Path(img).read_bytes(), man)
    f0 = X.frame(e)
    e.knob(3, 1); e.knob(4, 2)
    o["open"] = e.edit()
    e.unpend(); e.knob(3, -1); f1 = X.frame(e)
    o["closed"] = (e.edit(), e.pending(), f1[:32] == f0[:32])
    n0 = e.param(4, 0)[3]; e.sent.clear(); e.knob(4, 4)
    o["off_knob"] = (e.param(4, 0)[3] == n0, not e.sent, e.edit())
    f2 = X.frame(e)
    o["off_leds"] = f2[64:68] == f0[64:68]
    del e; gc.collect()
    return o


def run_janko(img, man, check):
    e = E(Path(img).read_bytes(), man)
    e.btn(0); t0 = e.tables(); oct0 = e.r0(int(man["report"]["janko"]["labels"]["c_jkoct"], 16), 0) if "janko" in man["report"] else None
    e.sbtn(CS.ID_SCALES); e.press(J.PAD_JK, shift=True); e.release(J.PAD_JK)
    if "janko" not in man["report"]:
        check(e.on() != J.JK, "the previous build: Shift + pad 8 in the editor is not Jankó"); del e; gc.collect(); return
    e.frame(); led = e.scales_leds()
    check(e.on() == J.JK and led[J.PAD_JK] == J.COL_ON, f"the editor: Shift + pad 8 = Jankó on (B_ON {e.on()}, pad 8 {led[J.PAD_JK]:#x})")
    e.btn(0); e.frame()
    bot = [e.val(24 + c) for c in range(8)]; up = [e.val(16 + c) for c in range(8)]
    check(bot == [60 + 2 * c for c in range(8)] and up == [61 + 2 * c for c in range(8)], f"the Note view: bottom row {bot}, the row above {up}")
    r = e.idx(24)
    inv60, lnk = e.r8(CS.KB + 0xF4 + 60), e.r8(CS.KB + 0x180 + r + 1)
    check(inv60 == r and lnk == r - 16 and e.r8(CS.KB + 0x180 + r - 16) == r + 1, f"the inverse table on the screen ({inv60} / {r}), the links ({lnk} / {r - 16})")
    e.btn(J.ID_UP); e.frame(); a1 = e.val(24)
    e.btn(J.ID_DOWN); e.btn(J.ID_DOWN); e.frame(); a2 = e.val(24)
    oc = e.r0(int(man["report"]["janko"]["labels"]["c_jkoct"], 16), 0)
    check(a1 == 61 and a2 == 59 and oc == oct0, f"Octave up / down = + / - 1 semitone ({a1}, {a2}); the stock's octave kept ({oc} / {oct0})")
    e.sbtn(J.ID_UP); e.frame()
    check(e.val(24) == 59, f"Shift + Octave: the stock's (the window stays: {e.val(24)})")
    e.goto(6); e.frame()
    check(e.r8(MGR + 0x152) == 6 and e.val(24) == 59 and e.val(0) == 62 and e.val(1) == 64, f"the expanded view: bottom-left {e.val(24)}, top row from {e.val(0)}")
    so = e.r32(CS.KB + 0xC)
    q = [e.r0(CS.QUANT, so, v) & 0xFF for v in range(48, 73)]
    check(q == list(range(48, 73)), "the quantiser leaves every note")
    mutscale = int(man["report"]["mutate39"]["labels"]["c_mutscale"], 16)
    mut = [e.r0(mutscale, 60, rr * 7919) & 0xFF for rr in range(60)]
    check(all(60 <= m <= 71 and m != 60 for m in mut) and len(set(mut)) == 11, f"random-mutate: another of the twelve ({sorted(set(mut))})")
    e.sbtn(CS.ID_SCALES); e.press(J.PAD_JK, shift=True); e.release(J.PAD_JK); e.btn(0); e.frame()
    check(e.on() == 0 and e.tables() == t0, f"Shift + pad 8 again: off (B_ON {e.on()}), the stock's tables back")
    del e; gc.collect()


def chord_model(e, root, ints):
    return sorted(root + i for i in ints)


def run_chords(img, man, check):
    e = E(Path(img).read_bytes(), man)
    e.btn(0); e.goto(6)
    on, off = e.note_chord(24)
    check(len(on) == 1, f"chords off: the stock's single note ({on})")
    e.ons.clear(); e.offs.clear(); e.press(CH.PAD_TOG, shift=True); e.release(CH.PAD_TOG)
    if "chords" not in man["report"]:
        check(len(e.ons) == 1, f"the previous build: Shift + pad 8 plays its note ({e.ons})"); del e; gc.collect(); return
    cr = CH.CR
    check(e.r8(cr + CH.O_FL) & 1 and not e.ons and not e.offs, f"Shift + pad 8: the chord screen on, no note ({e.ons}, {e.offs})")
    r = e.val(24)
    def chord(ints, q=24, vel=100):
        on, off = e.note_chord(q, vel)
        return sorted(n for n, v, p in on), [(v, p) for n, v, p in on], sorted(n for n, p in off)
    n, vp, f = chord(None)
    check(n == chord_model(e, r, (0, 4, 7)) and all(x == (100, 24) for x in vp) and f == n, f"major on root {r}: {n}, released {f}")
    n, vp, f = chord(None, vel=77)
    check(all(x[0] == 77 for x in vp), "the pad's velocity")
    e.tap(3); n, _, f = chord(None)
    check(n == chord_model(e, r, (0, 3, 7, 10)) and f == n, f"m7: {n}")
    e.tap(1, shift=True); n, _, _ = chord(None)
    check(n == chord_model(e, r, (0, 4, 7, 9)), f"Shift + pad 2 = 6: {n}")
    e.tap(0); e.tap(9); n, _, _ = chord(None)
    check(n == sorted([r + 4, r + 7, r + 12]), f"pad 10 = 1st inversion: {n}")
    e.tap(9); n, _, _ = chord(None)
    check(n == sorted([r, r + 4, r + 7]), f"pad 10 again = root position: {n}")
    e.tap(13); n, _, _ = chord(None)
    check(n == sorted([r - 12, r, r + 4, r + 7]), f"the root an octave down: {n}")
    e.tap(13); e.tap(12); n, _, _ = chord(None)
    check(n == sorted([r, r + 7, r + 16]), f"open voicing: {n}")
    e.tap(12); e.tap(14)
    so = e.r32(CS.KB + 0xC); ins = lambda v: (e.r0(CS.QUANT, so, v) & 0xFF) == v
    sc = [v for v in range(r + 1, r + 31) if ins(v)]
    n, _, _ = chord(None)
    check(n == sorted([r, sc[1], sc[3]]), f"diatonic (the scale's thirds): {n} (scale {sc[:6]})")
    e.tap(14); e.tap(15)
    e.ons.clear(); e.offs.clear(); e.press(24); e.release(24)
    a_on, a_off = len(e.ons), len(e.offs)
    e.ons.clear(); e.offs.clear(); e.press(25); e.release(25)
    b_on, b_off = len(e.ons), len(e.offs)
    e.offs.clear(); e.tap(15); c_off = len(e.offs)
    check((a_on, a_off, b_on, b_off, c_off) == (3, 0, 3, 3, 3), f"latch: held after the release, the next root replaces it, latch off ends it {(a_on, a_off, b_on, b_off, c_off)}")
    f = e.frame(); fs = e.frame(shift=True)
    lv = e.r32(e.r32(MGR + 0x90))
    row = [x for x in f[:16]]; rows = [x for x in fs[:8]]
    want = [CH.COL_SEL] + [CH.COL_DIM] * 7 + [CH.COL_INV] + [CH.COL_DIM] * 7
    check(row == want, f"rows 1-2: the type white, the root inversion orange, the rest dim ({[hex(x) for x in row]})")
    check(rows == [CH.COL_SHIFT] * 7 + [CH.COL_ON], f"with Shift: page 2 yellow, pad 8 green ({[hex(x) for x in rows]})")
    e.goto(1)
    on, _ = e.note_chord(24)
    check(e.r8(MGR + 0x152) == 1 and len(on) == 1, f"the normal Note view: the stock's single note ({on})")
    e.goto(6); e.tap(CH.PAD_TOG, shift=True)
    on, _ = e.note_chord(24)
    check(not (e.r8(cr + CH.O_FL) & 1) and len(on) == 1, f"Shift + pad 8 again: off, the stock's note ({on})")
    del e; gc.collect()


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run_gm(img, man)
    check(o["open"] == 1, "GM: K5 opens the number view")
    check(o["closed"] == (0, True, True), f"GM: K4 to off closes it, the save asked, the Setup's pads back {o['closed']}")
    check(o["off_knob"] == (True, True, 0), f"GM off: K5 changes nothing, no note, no view {o['off_knob']}")
    check(o["off_leds"], "GM off: K5..K8's LEDs untouched")
    run_janko(img, man, check)
    run_chords(img, man, check)
    if prev:
        run_janko(prev, pman, check); run_chords(prev, pman, check)
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
