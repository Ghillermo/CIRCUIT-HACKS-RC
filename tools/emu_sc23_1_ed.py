"""SC23.1: the CC editor of the MIDI macros (Octave v / ^ cycle the fields, the track button saves, any view button discards), through the real routes on the live RAM dump.

    python tools/emu_sc23_1_ed.py SC19.9.bin SC23.1.bin SC19.9_manifest.json SC23.1_manifest.json
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
V.use_cced(); V.use_cced2()
E20, TMPL, MGR = T4.E20, T4.TMPL, T4.MGR
SETOBJ = OLD.SETOBJ
expected_grid = OLD.expected_grid


def main(prev, img, man9, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = E20(img, man)
    r32 = e.r32
    for _ in range(12): e.vtick()
    saves, emits = [], []
    def hs(uc, a, s, d):
        r = [uc.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        saves.append((r[0], r[1], r[2], r[3], struct.unpack("<I", bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 4)))[0]))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)                       # the store queue is drained by its own task on the unit: here the write returns at once
    def hm(uc, a, s, d): emits.append(bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_R1), 3)).hex())
    e.uc.hook_add(UC_HOOK_CODE, hs, begin=0x0803C920, end=0x0803C920)
    e.uc.hook_add(UC_HOOK_CODE, hm, begin=0x0803BEDA, end=0x0803BEDA)
    T4_ = r32(SETOBJ - 4); base = r32(T4_ + 0xC)
    rec = lambda tmpl, k: base + 0x78 * tmpl + 0x28 + 10 * k
    getrec = lambda tmpl, k: bytes(e.uc.mem_read(rec(tmpl, k), 10))
    getall = lambda tmpl: bytes(e.uc.mem_read(rec(tmpl, 0), 80))
    E1 = lambda: e.tailb(V.O_ED); E2 = lambda: e.tailb(V.O_ED + 1)
    cc = lambda tmpl, k: struct.unpack_from("<H", getrec(tmpl, k), 4)[0]
    grid = lambda: e.tleds(TMPL[0])
    pad25 = lambda: (e.padr(V.PAD_CC), e.rel(V.PAD_CC))
    e.call(int(man["report"]["sc17"]["labels"]["c_gfst"], 16)); scr = e.uc.reg_read(UC_ARM_REG_R0) + V.S_SCR
    check(scr > V.S_SCR, f"scratch of the editor = the idle Master FX LED buffer ({scr:#x})")

    def to_editor():
        """MIDI 1 Preset view with the editor on and nothing selected."""
        e.btn(0); e.btn(2)
        if e.cur() != 18: e.btn(8)
        assert e.cur() == 18, e.cur()
        if E1() == 0: pad25()
        assert E1() == 0x80, hex(E1())
        e.padr(0); e.rel(0)                                                          # template 1 (a template pad drops the selection of a knob)

    to_editor()
    check(E1() == 0x80 and E2() == 0, f"MIDI 1 + Preset + pad 25: editor on (state {E1():#x})")
    orig = getall(0)
    check(getrec(0, 0) == bytes.fromhex("01000100010000007f00"), "record of knob 1: CC 1, range 0..127")
    e.btn(19); e.btn(20)
    check(E1() == 0x80 and not saves, "Octave v / ^ with no knob selected: nothing")
    e.knob_raw(0, 3)
    check(E1() == 0xC0 and getall(0) == orig and E2() == 0, "knob 1 touched: selected, nothing changed")
    e.knob_raw(0, 19)
    check(cc(0, 0) == 20 and E2() & 2 and bytes(e.uc.mem_read(scr, 80)) == orig and e.uc.mem_read(scr + 80, 1)[0] == 0, "CC 20 (live); the original 8 records are in the scratch, template 0")
    e.knob_raw(0, 5); e.knob_raw(0, -5)
    check(cc(0, 0) == 20 and bytes(e.uc.mem_read(scr, 80)) == orig, "more changes: the backup is not overwritten")
    e.btn(19)
    check(E1() == 0xC8 and grid() == expected_grid(0, 0x2B), f"Octave v: start of the range (state {E1():#x}), 0 in orange")
    e.knob_raw(0, 5)
    e.btn(19)
    check(E1() == 0xD0 and grid() == expected_grid(127, 0x13), f"Octave v: end of the range (state {E1():#x}), 127 in light blue")
    e.btn(19)
    check(E1() == 0xC0 and grid() == expected_grid(20, 0x32), "Octave v after the last field: back to the CC (wraps)")
    e.btn(20)
    check(E1() == 0xD0, f"Octave ^ from the first field: wraps to the end ({E1():#x})")
    e.btn(20)
    check(E1() == 0xC8 and grid() == expected_grid(5, 0x2B), "Octave ^: the start of the range again (5)")
    check(not saves, "nothing was persisted by cycling or editing")
    e.btn(2)
    check(len(saves) == 1 and saves[0][0] == r32(T4_ + 0x10) and saves[0][3] == base and saves[0][4] == 0x78, f"MIDI 1 button: the template is persisted (0x78 bytes from {saves[0][3]:#x})" if saves else "MIDI 1 button persists")
    check(E1() == 0x80 and not E2() & 2 and e.cur() == 18, f"saved: knob deselected, editor still on, still in the Preset view (state {E1():#x}, view {e.cur()})")
    saved = getall(0)
    check(struct.unpack_from("<HHH", getrec(0, 0), 4) == (20, 5, 127), "saved record: CC 20, range 5..127")

    # discard: two knobs pending, then a view button
    e.knob_raw(1, 1); e.knob_raw(1, 9)
    e.knob_raw(0, 1); e.knob_raw(0, 3)
    check(cc(0, 1) == 11 and cc(0, 0) == 23 and E2() & 2, "two knobs changed (CC 11 and CC 23), pending")
    n = len(saves)
    e.btn(0)
    check(E1() == 0 and getall(0) == saved and len(saves) == n, f"Synth 1 button: both knobs back to the saved values, nothing persisted (state {E1():#x}, {len(saves) - n} writes)")
    e.btn(2)
    emits.clear(); e.knob_raw(1, 3)
    check(emits[:1] and emits[0][:4] == "b202", f"the sender was rebuilt with the saved CC 2: {emits[:2]}")
    emits.clear(); e.knob_raw(0, 3)
    check(emits[:1] and emits[0][:4] == "b214", f"knob 1 sends the saved CC 20: {emits[:2]}")

    for name, act, stays in (("Mixer", lambda: e.btn(14), False), ("FX", lambda: e.btn(15), False), ("Drum 1", lambda: e.btn(4), False), ("MIDI 2", lambda: e.btn(3), False),
                             ("Preset", lambda: e.btn(8), False), ("pad 25", pad25, False), ("template pad 4", lambda: (e.padr(3), e.rel(3)), True)):
        to_editor()
        e.knob_raw(2, 1); e.knob_raw(2, 7)
        pend = cc(0, 2) != struct.unpack_from("<H", saved, 24)[0]
        n = len(saves)
        act()
        check(pend and getall(0) == saved and len(saves) == n and (E1() & 0x80) == (0x80 if stays else 0), f"{name}: discards (restored {getall(0) == saved}, state {E1():#x}, {len(saves) - n} writes)")
    # Record / Play / Shift keep the editor and the changes
    to_editor()
    e.knob_raw(2, 1); e.knob_raw(2, 7)
    e.btn(16); e.btn(17)
    check(E1() == 0xC2 and cc(0, 2) != struct.unpack_from("<H", saved, 24)[0], f"Record / Play: the editor stays, the change stays (state {E1():#x})")
    e.btn(0)

    # the track button with nothing to save leaves (stock view change); with only a selection it deselects
    to_editor()
    c0 = e.cur(); n = len(saves)
    e.btn(2)
    check(E1() == 0 and len(saves) == n and e.cur() != c0, f"MIDI 1, no selection and nothing changed: leaves the editor, stock view change ({c0} -> {e.cur()})")
    to_editor()
    e.knob_raw(3, 1)
    n = len(saves); c0 = e.cur()
    e.btn(2)
    check(E1() == 0x80 and e.cur() == c0 and len(saves) == n, f"MIDI 1 with only a selection: deselects, stays (state {E1():#x}, {len(saves) - n} writes)")
    pad25()
    e.btn(19); e.btn(20)
    check(E1() == 0 and e.cur() == 18, "editor off: the Octave buttons are stock")

    # NRPN with a 14-bit value
    to_editor()
    e.uc.mem_write(rec(0, 1), bytes.fromhex("0200") + bytes([1, 0]) + struct.pack("<HHH", 300, 0, 16383))
    e.knob_raw(1, 1)
    seq = []
    for _ in range(7):
        seq.append(E1()); e.btn(19)
    check(seq == [0xC1, 0xC9, 0xD1, 0xD9, 0xE1, 0xE9, 0xC1], f"NRPN 14-bit: six fields, then wraps ({[hex(x) for x in seq]})")
    e.btn(20); e.btn(20); e.btn(20)
    check(E1() == 0xE1, f"Octave ^ three times from the second field (wrapping through the first): the MSB of the end ({E1():#x})")
    e.knob_raw(1, -27)
    check(struct.unpack_from("<H", getrec(0, 1), 8)[0] == 100 * 128 + 127, f"end MSB 100 ({struct.unpack_from('<H', getrec(0, 1), 8)[0]})")
    n = len(saves)
    e.btn(2)
    check(len(saves) == n + 1 and E1() == 0x80, "saved by the track button")
    # NRPN with a 7-bit value
    e.uc.mem_write(rec(0, 2), bytes.fromhex("0400") + bytes([1, 0]) + struct.pack("<HHH", 130, 10, 100))
    e.knob_raw(2, 1)
    seq = []
    for _ in range(5):
        seq.append(E1()); e.btn(19)
    check(seq == [0xC2, 0xCA, 0xD2, 0xDA, 0xC2], f"NRPN 7-bit: four fields, then wraps ({[hex(x) for x in seq]})")
    e.uc.mem_write(rec(0, 4), bytes(10))
    e.knob_raw(4, 1); e.knob_raw(4, 5); e.btn(19)
    check(getrec(0, 4) == bytes(10) and E1() & 0x38 == 0, "a record of kind 0 cannot be edited")
    # a CC edited by its LSB-less record: the templates
    to_editor()
    t0 = getall(0)
    e.knob_raw(0, 1); e.knob_raw(0, 2)
    check(getall(0) != t0, "template 1 changed (pending)")
    e.padr(1); e.rel(1)
    check(getall(0) == t0 and E1() & 0xC0 == 0x80, "template pad 2: the unsaved changes of template 1 are discarded")
    e.knob_raw(0, 1); e.knob_raw(0, 4)
    n = len(saves)
    e.btn(2)
    check(len(saves) == n + 1 and saves[-1][3] == base + 0x78, f"template 2 saved: persisted at +{saves[-1][3] - base:#x}")

    # MIDI 2
    e.btn(0); e.btn(3)
    if e.cur() != 27: e.btn(8)
    pad25()
    check(E1() == 0x80 and E2() & 1 == 1, f"MIDI 2: editor on for track 2 (view {e.cur()})")
    e.knob_raw(0, 1); e.knob_raw(0, 2)
    e.btn(19); e.btn(20)
    n = len(saves); e.btn(3)
    check(len(saves) == n + 1 and E1() == 0x80, "MIDI 2 button: saved")
    o = getall(0)
    e.knob_raw(5, 1); e.knob_raw(5, 2)
    check(getall(0) != o, "MIDI 2: knob 6 changed (pending)")
    e.btn(2)
    check(E1() == 0 and getall(0) == o, "the button of the other track discards and leaves")

    gc.collect(); e2 = E20(img, man)
    e2.uc.mem_write(V.TAIL + V.O_ED, bytes([0xC9, 3, 0x12, 0x34]))
    e2.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([0x80])); e2.uc.mem_write(V.TAIL + V.O_SIG, bytes([V.SIG_VAL]))
    for _ in range(4): e2.vtick()
    check(e2.tailb(V.O_ED) == 0 and e2.tailb(V.O_ED + 1) == 0 and e2.tailb(V.O_ED + 2) == 0, "power-up: the editor state is cleared")
    print("SC23.1 CC EDITOR RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
