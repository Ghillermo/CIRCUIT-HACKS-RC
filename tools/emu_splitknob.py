"""SC45.8 (tools/splitknob.py): in split4's split keyboard, a track button held = the knobs are that track's.

The emulated firmware, the buttons / knobs through the controller (0x08033320 / 0x0803381A / 0x08033848) and the real LED task:
  * Synth 1 held + Synth 2: the split on; a knob = Synth 1's knob handler ([container + 0x148 + 4 t]);
  * MIDI 1 held: the split stays; a knob = MIDI 1's handler; the frame's knob LEDs = MIDI 1's handler's; let go after the knob: the split stays,
    the knobs Synth 1's again;
  * Drum 1 held: its handler; let go after 500 ms with no knob: the split stays;
  * Synth 1 held + MIDI 2 meanwhile: a new pair (Synth 1 on top, MIDI 2 below);
  * a tap of a track button (no knob, under 400 ms): the split off, as before;
  * the previous build (if given): a track button pressed ends the split at once.

    python tools/emu_splitknob.py BUILD.bin manifest.json [PREVIOUS.bin PREVIOUS_manifest.json]
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc35 import E35, MGR  # noqa: E402
import split4 as S4  # noqa: E402
import splitknob as SK  # noqa: E402

CT = 0x20040DB8
HAL = 0x2000081C


class EK:
    def __init__(self, img, man):
        gc.collect()
        self.e = e = E35(bytearray(Path(img).read_bytes()), man)
        self.H = [e.r32(CT + SK.HANDLERS + 4 * t) for t in range(8)]
        self.knobs = []
        for f in {e.r32(e.r32(o) + 0x10) & ~1 for o in self.H if o}:
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: self.knobs.append(uc.reg_read(UC_ARM_REG_R0)), begin=f, end=f)
    def press(self, i): self.e.call(0x08033320, MGR, i, maxins=8_000_000)
    def release(self, i): self.e.call(0x0803381A, MGR, i, maxins=8_000_000)
    def knob(self, k=0, d=1):
        self.knobs.clear(); self.e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=8_000_000)
        return [self.H.index(o) for o in self.knobs if o in self.H]
    def on(self): return self.e.r8(S4.SPR + S4.O_ON) if self.e.r32(S4.SPR) == S4.SIG else 0
    def pair(self): return self.e.r8(S4.SPR + S4.O_TOP), self.e.r8(S4.SPR + S4.O_BOT)
    def frame_knobs(self):
        self.e.call(0x08034196, MGR, 0x2006E000, maxins=8_000_000)
        return list(struct.unpack("<8H", bytes(self.e.uc.mem_read(0x2006E000 + 2 * 60, 16))))
    def handler_leds(self, t):
        self.e.call(SK.LED_GET, self.H[t], maxins=2_000_000)
        return list(struct.unpack("<8H", bytes(self.e.uc.mem_read(self.e.uc.reg_read(UC_ARM_REG_R0), 16))))
    def hal(self, ms): self.e.w32(HAL, ms)
    def split(self, a, b):
        self.press(a); self.release(a); self.press(9); self.release(9)         # its Note view
        self.press(a); self.press(b); self.release(b); self.release(a)


def main(img, man, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    k = EK(img, man); k.hal(100000)
    k.split(0, 1)
    check(k.on() == 1 and k.pair() == (0, 1), f"Synth 1 held + Synth 2: the split on ({k.on()}, {k.pair()})")
    check(k.knob() == [0], f"a knob: Synth 1's handler ({k.knobs})")
    k.press(2)
    check(k.on() == 1, "MIDI 1 pressed: the split stays")
    got = k.knob(); fk, hl = k.frame_knobs(), k.handler_leds(2)
    check(got == [2], f"MIDI 1 held: a knob = MIDI 1's handler ({got})")
    check(fk == hl, f"MIDI 1 held: the knob LEDs = MIDI 1's ({[hex(x) for x in fk]} / {[hex(x) for x in hl]})")
    k.release(2)
    check(k.on() == 1 and k.knob() == [0], "let go after the knob: the split stays, the knobs Synth 1's again")
    check(k.frame_knobs() == k.handler_leds(0), "the knob LEDs Synth 1's again")
    k.press(4); got = k.knob(); k.knob(1, -1)
    check(got == [4], f"Drum 1 held: its handler ({got})")
    k.release(4); check(k.on() == 1, "Drum 1 let go after a knob: the split stays")
    k.press(3); k.hal(100500); k.release(3)
    check(k.on() == 1, "MIDI 2 held 500 ms, no knob: the split stays")
    k.press(0); k.press(3); k.release(3); k.release(0)
    check(k.on() == 1 and k.pair() == (0, 3), f"Synth 1 held + MIDI 2: a new pair ({k.pair()})")
    k.press(2); k.release(2)
    check(k.on() == 0, "a tap of MIDI 1: the split off, as before")
    del k; gc.collect()
    if prev:
        p = EK(prev, pman); p.hal(100000); p.split(0, 1); p.press(2); st = p.on(); p.release(2)
        check(st == 0, f"the previous build: MIDI 1 pressed ends the split at once ({st})")
        del p; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text()), a[2] if len(a) > 2 else None,
                       json.loads(Path(a[3]).read_text()) if len(a) > 3 else None) else 0)
