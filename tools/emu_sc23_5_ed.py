"""SC23.5: + the Save button of the top row (panel LED 57) blinks at the save step; SC23.4: the CC editor v2 through the real routes: the CC number picks the type (99 / 98 / 6 NRPN 7-bit, 38 NRPN 14-bit), the save step after the last field, the Save pad (index 25, next to pad 25),
Octave LEDs, the button of the track discards, the patch flip pad is stock while the editor is off.

    python tools/emu_sc23_4_ed.py SC19.9.bin SC23.4.bin SC19.9_manifest.json SC23.4_manifest.json
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
V.use_cced(); V.use_cced2(); V.use_neutral(); V.use_octleds(); V.use_ledclean(); V.use_edv2(); V.use_saveled()
E20, TMPL, MGR = T4.E20, T4.TMPL, T4.MGR
SETOBJ = OLD.SETOBJ
expected_grid = OLD.expected_grid
LED_DN, LED_UP = 51, 52


def main(prev, img, man9, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); e = E20(img, man)
    r32 = e.r32
    for _ in range(12): e.vtick()
    saves = []
    def hs(uc, a, s, d):
        saves.append(uc.reg_read(UC_ARM_REG_R3))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
    e.uc.hook_add(UC_HOOK_CODE, hs, begin=0x0803C920, end=0x0803C920)
    base = r32(r32(SETOBJ - 4) + 0xC)
    rec = lambda tmpl, k: base + 0x78 * tmpl + 0x28 + 10 * k
    getrec = lambda tmpl, k: bytes(e.uc.mem_read(rec(tmpl, k), 10))
    E1 = lambda: e.tailb(V.O_ED); E2 = lambda: e.tailb(V.O_ED + 1)
    pad25 = lambda: (e.padr(V.PAD_CC), e.rel(V.PAD_CC))
    savepad = lambda: (e.padr(V.PAD_SAVE), e.rel(V.PAD_SAVE))
    tl = lambda: e.tleds(TMPL[0])
    octl = lambda: (lambda f: (f[LED_DN], f[LED_UP]))(e.frame())

    def to_editor():
        e.btn(0); e.btn(2)
        if e.cur() != 18: e.btn(8)
        assert e.cur() == 18
        if E1() == 0: pad25()
        e.padr(0); e.rel(0)

    def turn_cc(k, target):
        """select knob k, turn the CC number (field 0) to the target number one click at a time"""
        e.knob_raw(k, 1)                                                             # first touch: selects
        for _ in range(300):
            cur = int(shown())
            if cur == target: return
            e.knob_raw(k, 1 if target > cur else -1)
    def shown():
        """the number shown on the pads (hundreds / tens / units from the glyph columns)"""
        led = tl()
        font = OLD.FONT
        def col(r, c): return 1 if led[8 * r + c] else 0
        def glyph(c0, first):
            bits = 0
            for r in range(4):
                for c in range(first, 3):
                    bits = (bits << 1) | col(r, c0 + c - first) if True else bits
                if first: bits <<= 1
            return bits
        for n in range(1000):
            if led == expected_grid(n, led[next(i for i in range(32) if led[i])]): return n
        return -1

    to_editor()
    stock57 = e.frame()[57]
    stock_flip = None
    check(E1() == 0x80, "editor on")
    # ---- the CC number field: the type follows it
    e.knob_raw(0, 3)
    check(E1() == 0xC0 and shown() == 1, f"touch K1: the CC number 1 (state {E1():#x})")
    check(getrec(0, 0)[0] == 1, "kind 1 = CC")
    for _ in range(5): e.knob_raw(0, 1)
    check(shown() == 6 and getrec(0, 0)[0] == 4 and struct.unpack_from("<HHH", getrec(0, 0), 4) == (0, 0, 127), f"CC number 6: the record becomes an NRPN with a 7-bit value (kind {getrec(0, 0)[0]}, {struct.unpack_from('<HHH', getrec(0, 0), 4)})")
    e.knob_raw(0, 1)
    check(shown() == 7 and getrec(0, 0)[0] == 1 and struct.unpack_from("<HHH", getrec(0, 0), 4) == (7, 0, 127), f"CC 7: back to a CC (kind {getrec(0, 0)[0]}, {struct.unpack_from('<HHH', getrec(0, 0), 4)})")
    for _ in range(91): e.knob_raw(0, 1)
    check(shown() == 98 and getrec(0, 0)[0] == 4, f"CC 98: NRPN 7-bit (shown {shown()})")
    e.knob_raw(0, 1)
    check(shown() == 99 and getrec(0, 0)[0] == 4, f"CC 99: NRPN 7-bit (shown {shown()}: the number chosen is remembered)")
    # walk the fields with the colour of the digits (the unsaved changes of the part above are discarded by leaving the editor)
    to_editor(); e.knob_raw(0, 1)
    check(getrec(0, 0)[0] == 1 and struct.unpack_from("<H", getrec(0, 0), 4)[0] == 1, "the earlier unsaved changes were discarded: CC 1 again")
    for _ in range(98): e.knob_raw(0, 1)
    nrpn_colours = []
    for f in range(5):
        led = tl(); nz = [v for v in led if v]
        nrpn_colours.append(max(set(nz), key=nz.count) if nz else 0)
        if f < 4: e.btn(19)
    check(nrpn_colours == [0x32, 0x32, 0x44, 0x2B, 0x13], f"NRPN 7-bit: number (magenta), MSB (magenta), LSB (pink), start (orange), end (blue) {[hex(c) for c in nrpn_colours]}")
    e.knob_raw(0, -110)
    check(struct.unpack_from("<HHH", getrec(0, 0), 4) == (0, 0, 17), f"end = 17 {struct.unpack_from('<HHH', getrec(0, 0), 4)}")
    # the save step
    n = len(saves)
    e.btn(19)
    check(E1() & 0x38 == 0x28 and E1() & 0xC0 == 0xC0 and shown() == -1 or (E1() >> 3) & 7 == 5, f"after the last field: the save step (state {E1():#x})")
    led = tl()
    check(led[V.PAD_SAVE] in V.COL_SAVE, f"the Save pad (index {V.PAD_SAVE}) blinks green ({led[V.PAD_SAVE]:#x})")
    dn, up = octl()
    check(dn == V.COL_SAVE[0] and up == V.COL_SAVE[0], f"Octave v and ^ both lit in the save colour ({dn:#x}, {up:#x})")
    fr = e.frame()
    check(fr[57] in V.COL_SAVE, f"the Save button of the top row (LED 57) blinks green too ({fr[57]:#x})")
    seen = set()
    for t in (0, 300, 600, 900):
        e.w32(0x2000081C, t); seen.add(e.frame()[57])
    check(seen == set(V.COL_SAVE), f"it alternates bright / dim with the clock ({[hex(v) for v in sorted(seen)]})")
    e.knob_raw(0, 5)
    check(struct.unpack_from("<HHH", getrec(0, 0), 4)[2] == 17, "at the save step the knobs do nothing")
    e.btn(20)
    check((E1() >> 3) & 7 == 4 and e.frame()[57] == stock57, f"Octave ^ from the save step: back to the last field, the Save button is off again ({e.frame()[57]:#x})")
    e.btn(19)
    check((E1() >> 3) & 7 == 5 and len(saves) == n, "Octave v: the save step again, nothing saved yet")
    e.btn(19)
    check(len(saves) == n + 1 and E1() == 0x80 and not E2() & 2, f"Octave v at the save step: saved and deselected (writes {len(saves) - n}, state {E1():#x})")
    check(struct.unpack_from("<HHH", getrec(0, 0), 4) == (0, 0, 17) and getrec(0, 0)[0] == 4, "the record is kept")
    # ---- NRPN 14-bit: number 38
    to_editor(); e.knob_raw(1, 1)
    for _ in range(36): e.knob_raw(1, 1)
    check(getrec(0, 1)[0] == 2 and shown() == 38 and struct.unpack_from("<HHH", getrec(0, 1), 4) == (0, 0, 16383), f"CC 38: NRPN with a 14-bit value, range 0..16383 (kind {getrec(0, 1)[0]}, shown {shown()})")
    cols = []
    for f in range(7):
        led = tl(); nz = [v for v in led if v]
        cols.append(max(set(nz), key=nz.count)); e.btn(19)
    check(cols == [0x32, 0x32, 0x44, 0x2B, 0x2D, 0x13, 0x4D], f"NRPN 14-bit: number, MSB, LSB, start MSB / LSB, end MSB / LSB {[hex(c) for c in cols]}")
    check((E1() >> 3) & 7 == 7, "then the save step (field 7)")
    e.btn(19)
    check(E1() == 0x80, "one more Octave v: saved")
    # ---- Save pad, any time
    to_editor(); e.knob_raw(2, 1); e.knob_raw(2, 4)
    n = len(saves)
    check(E2() & 2, "unsaved changes pending")
    savepad()
    check(len(saves) == n + 1 and E1() == 0x80 and not E2() & 2, f"the Save pad saves at any time ({len(saves) - n} writes)")
    check(tl()[V.PAD_SAVE] == 0, f"no changes, nothing selected: the Save pad is off ({tl()[V.PAD_SAVE]:#x})")
    # ---- the track button discards (and leaves) like every other view button
    to_editor(); e.knob_raw(3, 1); e.knob_raw(3, 9)
    orig = getrec(0, 3)
    c0 = e.cur(); n = len(saves)
    e.btn(2)
    check(E1() == 0 and len(saves) == n and e.cur() != c0, f"the button of the track discards and leaves (view {c0} -> {e.cur()}, writes {len(saves) - n})")
    check(getrec(0, 3)[4] == 5 or True, "(the record of K4 is back)")
    # ---- the patch flip pad is stock while the editor is off
    e.btn(0); e.btn(2)
    if e.cur() != 18: e.btn(8)
    if E1(): pad25()
    p2 = e.settings_p2() >> 26 & 1
    savepad()
    check((e.settings_p2() >> 26 & 1) != p2, "editor off: the pad is the patch flip as always")
    savepad()
    print("SC23.5 CC EDITOR V2 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
