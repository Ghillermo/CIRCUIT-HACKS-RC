"""SC40.1 ARM test (live RAM dump, the real routes: the controller's buttons, pads and knobs, the LED task from its caller; the project's parameters
through the stock getter): the knobs of the Sidechain view (tools/sckn.py).

    python tools/emu_sc40_1.py SC40.1.bin SC40.1_manifest.json SC40.bin SC40_manifest.json
  * Shift + FX = the Sidechain view; K1..K4 move attack / hold / decay / depth of Synth 1 (nothing chosen yet), limited to 0..127; the source and the
    other tracks untouched; K5..K8 nothing;
  * a preset pad of MIDI 2 (page 2, the lower row): its four values as the stock writes them, and it is the chosen track: the knobs move its values;
  * the knob LEDs of the frame: K1..K4 = the values in the colour of the track, K5..K8 dark;
  * out of the view: the knobs are the stock's (the side-chain values do not move);
  * the previous build: the knobs do nothing in the Sidechain view.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_8 as T8  # noqa: E402
from emu_sc35 import MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import sckn as SK  # noqa: E402

B = 0x08010000


def run(img, man, new):
    e = T8.E8(img, man); e.setup(man); o = {}
    sc = lambda: [e.get(i) for i in range(26, 46)]
    def knob(k, d): e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=3_000_000)
    def knobs():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=8_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))[60:68]
    e.set_p0(e.r32(MGR + 0xC), 1); e.btn(15); e.set_p0(e.r32(MGR + 0xC), 0)
    cont = e.r32(MGR + 0x2C); o["mode"] = e.r8(cont + SK.MODE_OFF)
    for i, v in zip(range(26, 31), (2, 10, 50, 70, 100)): e.put(i, v)
    a = sc(); knob(0, 5); knob(1, -7); knob(2, 100); knob(3, -120); knob(4, 9); knob(7, -9); o["s1"] = (a, sc())
    o["led1"] = knobs()
    if not new:
        del e; gc.collect(); return o
    e.btn(19); e.pad(26); e.rel(26); p = sc()                                     # page 2, the lower row, preset 3: MIDI 2
    knob(0, 3); knob(3, -10); o["m2"] = (p, sc()); o["led2"] = knobs()
    e.btn(20); e.pad(17); e.rel(17); p = sc(); knob(1, 1); o["s1b"] = (p, sc())  # page 1, the upper row, preset 2: Synth 1 again
    e.btn(0); b_ = sc(); knob(0, 5); o["out"] = (e.r8(cont + SK.MODE_OFF), b_ == sc())
    del e; gc.collect()
    return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["sckn"]["labels"].items()}
    w = lambda a: struct.unpack_from("<I", img, a - B)[0]
    from thumb import bl
    check(w(SK.SC_VT) == L["c_skpad"] | 1 and w(SK.CT_VT + 16) == L["c_skknob"] | 1 and all(bytes(img[c - B:c - B + 4]) == bl(c, int(man["report"]["compkn"]["labels"]["c_ckledtask"], 16) if "compkn" in man["report"] else L["c_skledtask"]) for c in PK.LED_CALLS),
          "the hooks: slot 0 of the Sidechain object, slot 4 of the container, the two LED task calls")
    o = run(img, man, True)
    a, b_ = o["s1"]
    check(o["mode"] == SK.MODE_SC and b_[:5] == [2, 15, 43, 127, 0] and b_[5:] == a[5:], f"Shift + FX = the Sidechain view; K1..K4 move attack / hold / decay / depth of Synth 1 ({a[:5]} -> {b_[:5]}), limited; the source and the other tracks untouched; K5 / K8 nothing")
    c = SK.COL[0]
    check(o["led1"] == [c | (15 + 2) << 8, c | (43 + 2) << 8, c | (127 + 2) << 8, c | 2 << 8, 0, 0, 0, 0], f"the knob LEDs: the four values in Synth 1's colour, K5..K8 dark ({[hex(x) for x in o['led1']]})")
    p, q = o["m2"]
    check(p[16:20] == [5, 70, 70, 100] and q[16:20] == [8, 70, 70, 90] and q[:15] == p[:15], f"a preset pad of MIDI 2: its values ({p[16:20]}), and the knobs move them ({q[16:20]}); the other tracks untouched")
    c = SK.COL[3]
    check(o["led2"][:4] == [c | (8 + 2) << 8, c | (70 + 2) << 8, c | (70 + 2) << 8, c | (90 + 2) << 8], "the knob LEDs in MIDI 2's colour")
    p, q = o["s1b"]
    check(p[1:5] == [5, 50, 80, 80] and q[1:5] == [5, 51, 80, 80] and q[15:] == p[15:], "a preset pad of Synth 1: the knobs are Synth 1's again")
    check(o["out"][0] != SK.MODE_SC and o["out"][1], "out of the view: the knobs do not move the side-chain")
    gc.collect(); r = run(prev, prev_man, False)
    check(r["s1"][0] == r["s1"][1] and all(x >> 8 == 0 for x in r["led1"]), f"the previous build: the knobs do nothing in the Sidechain view ({[hex(x) for x in r['led1'][:4]]})")
    print("SC40.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
