"""SC23.3: the Octave LEDs of the CC editor (Octave v lights while a next field exists, Octave ^ while a previous one exists, in the colour of the field), through the real routes and the real LED task.

    python tools/emu_sc23_3_ed.py SC19.9.bin SC23.3.bin SC19.9_manifest.json SC23.3_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc22_4 as T4  # noqa: E402
import emu_sc23_ed as OLD  # noqa: E402
V = T4.V
V.use_cced(); V.use_cced2(); V.use_neutral(); V.use_octleds(); V.use_ledclean()
E20, TMPL, MGR = T4.E20, T4.TMPL, T4.MGR
SETOBJ = OLD.SETOBJ
LED_DN, LED_UP = 51, 52


def main(prev, img, man9, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = E20(img, man)
    r32 = e.r32
    for _ in range(12): e.vtick()
    def hs(uc, a, s, d): uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hs, begin=0x0803C920, end=0x0803C920)
    base = r32(r32(SETOBJ - 4) + 0xC)
    rec = lambda tmpl, k: base + 0x78 * tmpl + 0x28 + 10 * k
    pad25 = lambda: (e.padr(V.PAD_CC), e.rel(V.PAD_CC))
    oct_ = lambda: (lambda f: (f[LED_DN], f[LED_UP]))(e.frame())

    e.btn(0); e.btn(2)
    if e.cur() != 18: e.btn(8)
    stock = oct_()
    check(e.cur() == 18, f"MIDI 1 Preset view; Octave LEDs as stock {stock[0]:#x} / {stock[1]:#x}")
    off_leds = e.tleds(TMPL[0])
    pad25()
    on_leds = e.tleds(TMPL[0])
    check(oct_() == stock, "editor on, no number yet: the Octave LEDs are untouched")
    e.knob_raw(0, 3)
    dn, up = oct_()
    check(dn == 0x32 and up == stock[1], f"the number appears (CC, field 1 of 3): Octave v lit in the colour of the field ({dn:#x}), Octave ^ not ({up:#x})")
    e.btn(19)
    dn, up = oct_()
    check(dn == 0x2B and up == 0x2B, f"field 2 (start of the range): both lit, orange ({dn:#x}, {up:#x})")
    e.btn(19)
    dn, up = oct_()
    check(dn == stock[0] and up == 0x13, f"last field (end of the range): only Octave ^ lit, light blue ({dn:#x}, {up:#x})")
    e.btn(19)
    dn, up = oct_()
    check(dn == 0x32 and up == stock[1], "Octave v wraps to the first field: only Octave v lit again")
    # NRPN with a 14-bit value: six fields
    e.uc.mem_write(rec(0, 1), bytes.fromhex("0200") + bytes([1, 0]) + struct.pack("<HHH", 300, 0, 16383))
    e.knob_raw(1, 1)
    seq = []
    for _ in range(6):
        dn, up = oct_()
        seq.append((dn != stock[0], up != stock[1])); e.btn(19)
    check(seq == [(True, False), (True, True), (True, True), (True, True), (True, True), (False, True)], f"NRPN 14-bit: Octave v / ^ lit per field {seq}")
    # a record that cannot be edited shows no number: no LEDs
    e.uc.mem_write(rec(0, 4), bytes(10))
    e.knob_raw(4, 1)
    check(oct_() == stock, "a record of kind 0 (no number shown): the Octave LEDs are untouched")
    # selection dropped / editor off / another view
    e.knob_raw(0, 1)
    shown = e.tleds(TMPL[0])
    check(shown != on_leds, "the number is drawn on the pads")
    e.btn(2)
    check(oct_() == stock, "saved (knob deselected): the Octave LEDs go out")
    e.tleds(TMPL[0])
    clean = e.tleds(TMPL[0])
    check(clean == on_leds, f"the number is gone one frame after the save: the pads are the ones of before ({[i for i in range(32) if clean[i] != on_leds[i]]})")
    e.knob_raw(0, 1)
    check(oct_()[0] == 0x32, "number shown again: Octave v lit")
    e.btn(0)
    e.btn(2)
    if e.cur() != 18: e.btn(8)
    back = e.tleds(TMPL[0])
    check(oct_() == stock, "after leaving the editor (a view button discards): the Octave LEDs are untouched")
    check(back == off_leds, f"leaving the editor with a number shown: the Preset view is clean when it comes back ({[i for i in range(32) if back[i] != off_leds[i]]})")
    # template pad / pad 25 off with a number shown
    pad25(); e.knob_raw(1, 1)
    e.padr(3); e.rel(3)
    f1 = e.tleds(TMPL[0]); f2 = e.tleds(TMPL[0])
    check(all(f2[i] == on_leds[i] for i in range(8, 32)), f"a template pad drops the number: pads 9-32 clean ({[i for i in range(8, 32) if f2[i] != on_leds[i]]})")
    e.padr(0); e.rel(0)
    e.knob_raw(1, 1)
    pad25()
    f3 = e.tleds(TMPL[0]); f4 = e.tleds(TMPL[0])
    check(f4 == off_leds, f"pad 25 off with a number shown: the view is as before the editor ({[i for i in range(32) if f4[i] != off_leds[i]]})")
    print("SC23.3 CC EDITOR LEDS RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
