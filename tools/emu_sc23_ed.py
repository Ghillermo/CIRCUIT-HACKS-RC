"""SC23: the CC editor of the MIDI macros, through the real routes (pad 25 of the Preset view, the knobs, the button of the track) on the live RAM dump.

    python tools/emu_sc23_ed.py SC19.9.bin SC23.bin SC19.9_manifest.json SC23_manifest.json
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc22_4 as T4  # noqa: E402
V = T4.V
V.use_cced()
E20, TMPL, MGR = T4.E20, T4.TMPL, T4.MGR

SETOBJ = 0x2003974C
GLYPH = {0: (0, 1, 1, 0xF6F), 1: (1, 0x492), 2: (2, 0x653), 3: (3, 0xECF), 4: (4, 0x979), 5: (5, 0x68B), 6: (6, 0x49B), 7: (7, 0x649), 8: (8, 0xFEF), 9: (9, 0x6C9)}
FONT = [0xF6F, 0x492, 0x653, 0xECF, 0x979, 0x68B, 0x49B, 0x649, 0xFEF, 0x6C9]


def expected_grid(value, colour):
    """The 32 pads (4 rows x 8 columns) with the digits of the stock tempo display."""
    g = [0] * 32
    h_, t_, u_ = value // 100, (value // 10) % 10, value % 10
    def draw(d, base, first):
        for r in range(4):
            for c in range(first, 3):
                if (FONT[d] >> (11 - 3 * r - c)) & 1: g[8 * r + base + c - first] = colour
    if h_: draw(h_, 0, 1)
    if h_ or t_: draw(t_, 2, 0)
    draw(u_, 5, 0)
    return g


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
    E1 = lambda: e.tailb(V.O_ED); E2 = lambda: e.tailb(V.O_ED + 1)

    e.btn(2); e.btn(8)
    check(e.cur() == 18, f"MIDI 1 + Preset: view index {e.cur()}")
    led = e.tleds(TMPL[0])
    check(led[V.PAD_CC] == V.COL_CC[1] and E1() == 0, f"editor off: pad 25 dim magenta ({led[V.PAD_CC]:#x}), state {E1():#x}")
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    check(E1() == 0x80 and E2() == 0 and e.tailb(V.O_ED + 2) == TMPL[0] & 0xFF and e.tailb(V.O_ED + 3) == (TMPL[0] >> 8) & 0xFF, f"pad 25: editor on for MIDI 1 (state {E1():#x}, track {E2()}, view {e.tailb(V.O_ED + 3):#x}{e.tailb(V.O_ED + 2):02x})")
    led = e.tleds(TMPL[0])
    check(led[V.PAD_CC] == V.COL_CC[0], "pad 25 bright magenta")
    rec0 = getrec(0, 0)
    check(rec0 == bytes.fromhex("01000100010000007f00"), f"record of knob 1 (template 1): CC 1, range 0..127 {rec0.hex()}")
    # first touch: selects, shows the CC, changes nothing
    e.knob_raw(0, 3)
    check(E1() == 0xC0 and getrec(0, 0) == rec0, f"knob 1 touched: selected (state {E1():#x}), the record is unchanged")
    led = e.tleds(TMPL[0])
    check(led == expected_grid(1, 0x32), f"the pads show 1 in magenta: {led}")
    # turn: the CC changes (live)
    e.knob_raw(0, 3)
    check(struct.unpack_from("<H", getrec(0, 0), 4)[0] == 4 and e.tleds(TMPL[0]) == expected_grid(4, 0x32), "turn +3: CC 4, the pads show 4")
    e.knob_raw(0, 120)
    check(struct.unpack_from("<H", getrec(0, 0), 4)[0] == 124, "turn +120: CC 124")
    e.knob_raw(0, 100); check(struct.unpack_from("<H", getrec(0, 0), 4)[0] == 127 and e.tleds(TMPL[0]) == expected_grid(127, 0x32), "clamped at 127: the pads show 127 (hundreds in 2 columns)")
    e.knob_raw(0, -127); check(struct.unpack_from("<H", getrec(0, 0), 4)[0] == 0 and e.tleds(TMPL[0]) == expected_grid(0, 0x32), "clamped at 0: the pads show 0")
    e.knob_raw(0, 20)                                                                # CC 20
    check(E2() & 2 and not saves, f"changed flag set ({E2():#x}), nothing persisted yet")
    # the button of the track: next field
    e.btn(2)
    check(E1() == 0xC8 and e.tleds(TMPL[0]) == expected_grid(0, 0x2B), f"MIDI 1 button: field 2 = start of the range (state {E1():#x}), the pads show 0 in orange")
    check(len(saves) == 1 and saves[0][0] == r32(T4_ + 0x10) and saves[0][3] == base and saves[0][4] == 0x78, f"the changed template was persisted when the field advanced (0x78 bytes from {saves[0][3]:#x})" if saves else "persist")
    e.knob_raw(0, 5)
    e.btn(2)
    check(E1() == 0xD0 and e.tleds(TMPL[0]) == expected_grid(127, 0x13), f"button: field 3 = end of the range (state {E1():#x}), 127 in light blue")
    e.knob_raw(0, -3)
    check(struct.unpack_from("<HHH", getrec(0, 0), 4) == (20, 5, 124), f"CC 20, range {struct.unpack_from('<HHH', getrec(0, 0), 4)}")
    n = len(saves)
    e.btn(2)
    check(E1() == 0x80 and len(saves) == n + 1, f"button after the end: saved (state {E1():#x}, {len(saves)} writes)")
    check(e.tleds(TMPL[0]) != expected_grid(124, 0x13), "the number is gone after the save (stock pads again)")
    # the descriptor was rebuilt: leave, open the track view and turn the knob
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    check(E1() == 0 and E2() == 0, "pad 25 again: editor off")
    e.btn(2)                                                                         # the track view
    emits.clear(); e.knob_raw(0, 3)
    check(emits[:1] and emits[0][:4] == "b214", f"the knob now sends CC 20: {emits[:2]}")
    # NRPN with a 14-bit value
    e.btn(8)
    e.uc.mem_write(rec(0, 1), bytes.fromhex("0200") + bytes([1, 0]) + struct.pack("<HHH", 300, 0, 16383))
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    e.knob_raw(1, 1)
    check(E1() == 0xC1 and e.tleds(TMPL[0]) == expected_grid(2, 0x32), "NRPN 14-bit (kind 2): field 1 = the MSB of the parameter (300 >> 7 = 2)")
    e.knob_raw(1, 4)
    check(struct.unpack_from("<H", getrec(0, 1), 4)[0] == 6 * 128 + 44, "MSB +4: 6 -> parameter 812")
    e.btn(2); e.knob_raw(1, 1)
    check(E1() == 0xC9 and struct.unpack_from("<H", getrec(0, 1), 4)[0] == 6 * 128 + 45 and e.tleds(TMPL[0]) == expected_grid(45, 0x44), "field 2 = the LSB (45, pink)")
    e.btn(2); e.knob_raw(1, 7)
    check(E1() == 0xD1 and struct.unpack_from("<H", getrec(0, 1), 4 + 2)[0] == 7 * 128 and e.tleds(TMPL[0]) == expected_grid(7, 0x2B), "field 3 = the MSB of the start (orange): 7 -> start 896")
    e.btn(2)
    check(E1() == 0xD9 and e.tleds(TMPL[0]) == expected_grid(0, 0x2D), "field 4 = the LSB of the start (yellow)")
    e.btn(2); e.knob_raw(1, 10)
    check(E1() == 0xE1 and struct.unpack_from("<H", getrec(0, 1), 8)[0] == 127 * 128 + 127 and e.tleds(TMPL[0]) == expected_grid(127, 0x13), "field 5 = the MSB of the end (light blue), 127")
    e.btn(2); e.knob_raw(1, -27)
    check(E1() == 0xE9 and struct.unpack_from("<H", getrec(0, 1), 8)[0] == 127 * 128 + 100 and e.tleds(TMPL[0]) == expected_grid(100, 0x4D), "field 6 = the LSB of the end (aqua): 100")
    n = len(saves)
    e.btn(2)
    check(E1() == 0x80 and len(saves) > n and struct.unpack_from("<HHH", getrec(0, 1), 4) == (6 * 128 + 45, 7 * 128, 127 * 128 + 100), f"after the sixth field: saved {struct.unpack_from('<HHH', getrec(0, 1), 4)}")
    # NRPN with a 7-bit value: 4 fields
    e.uc.mem_write(rec(0, 2), bytes.fromhex("0400") + bytes([1, 0]) + struct.pack("<HHH", 130, 10, 100))
    e.knob_raw(2, 1)
    e.btn(2); e.btn(2); e.btn(2)
    check(E1() == 0xDA and e.tleds(TMPL[0]) == expected_grid(100, 0x13), f"NRPN 7-bit (kind 4): the fourth field is the end ({E1():#x})")
    e.btn(2)
    check(E1() == 0x80, "then saved")
    # a template pad drops the selection; an invalid record does nothing
    e.knob_raw(3, 1)
    check(E1() == 0xC3, "knob 4 selected")
    e.padr(3); e.rel(3)
    check(E1() & 0xC0 == 0x80, f"template pad 4: the selection is dropped, the editor stays on (state {E1():#x})")
    e.uc.mem_write(rec(0, 4), bytes(10))
    e.knob_raw(4, 1); e.knob_raw(4, 5)
    check(getrec(0, 4) == bytes(10), "a record of kind 0 cannot be edited")
    # the other view buttons leave the editor
    e.btn(0)
    check(E1() == 0, f"Synth 1 button: the editor is off (state {E1():#x})")
    # buttons >= 16 and Shift keep it; the button of the OTHER track leaves it
    e.btn(8)
    e.btn(2); e.btn(8)
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    e.btn(16)
    check(E1() == 0x80, "Record (16) does not leave the editor")
    e.btn(3)
    check(E1() == 0, "the button of the other track leaves the editor")
    # stock behaviour without the editor: the button of the track toggles the views as always
    e.btn(2); e.btn(8)
    c0 = e.cur(); e.btn(2)
    check(c0 == 18 and e.cur() == 19, f"editor off: MIDI 1 again goes to the track view as stock ({c0} -> {e.cur()})")
    # MIDI 2
    e.btn(3); e.btn(8)
    e.padr(V.PAD_CC); e.rel(V.PAD_CC)
    check(E1() == 0x80 and E2() & 1 == 1 and e.tailb(V.O_ED + 2) == TMPL[1] & 0xFF, f"MIDI 2: editor on for track 2 (track {E2() & 1})")
    e.knob_raw(0, 1); e.knob_raw(0, 2)
    check(struct.unpack_from("<H", getrec(0, 0), 4)[0] == 22, "MIDI 2 knob 1: CC 22 (the two tracks use the same template 1 here)")
    e.btn(3); e.btn(3); e.btn(3)
    check(E1() == 0x80, "MIDI 2 button x3: saved")
    # boot: the state is volatile
    e.uc.mem_write(V.TAIL + V.O_ED, bytes([0xC9, 1, 0x12, 0x34]))
    gc.collect(); e2 = E20(img, man)
    e2.uc.mem_write(V.TAIL + V.O_ED, bytes([0xC9, 1, 0x12, 0x34]))
    e2.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([0x80])); e2.uc.mem_write(V.TAIL + V.O_SIG, bytes([V.SIG_VAL]))
    for _ in range(4): e2.vtick()
    check(e2.tailb(V.O_ED) == 0 and e2.tailb(V.O_ED + 1) == 0 and e2.tailb(V.O_ED + 2) == 0, "power-up: the editor state is cleared")
    print("SC23 CC EDITOR RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
