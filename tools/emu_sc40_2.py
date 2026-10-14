"""SC40.2 ARM test (live RAM dump; the controller's knob route, the LED task from its caller; the master group through the stock getter): the knobs
of the Setup view (tools/compkn.py).

    python tools/emu_sc40_2.py SC40.2.bin SC40.2_manifest.json SC40.1.bin SC40.1_manifest.json
  * the Setup view active: K1 moves value 3 (the attack) and K2 value 4 (the release) of the master group, limited to 0..127; the compressor's
    switches, the master filter and the output gain untouched; K3..K8 nothing;
  * the knob LEDs: K1 / K2 white with their value;
  * the Advanced page of the view: the knobs do nothing;
  * the view's own handlers (pads, the other slots) are the stock's; the previous build: the knobs do nothing.
The Setup view is put in the controller by hand (as emu_sc38_3 does: no button of the emulated controller opens it).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc39_8 as T8  # noqa: E402
from emu_sc35 import MGR, PK  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
import compkn as CK  # noqa: E402

B = 0x08010000


def run(img, man):
    e = T8.E8(img, man); e.setup(man); o = {}
    g = lambda: [(e.call(CK.GETTER, CK.TYPE, i), e.uc.reg_read(UC_ARM_REG_R0) & 0xFF)[1] for i in range(8)]
    def knob(k, d): e.call(0x08033848, MGR, k, d & 0xFFFFFFFF, maxins=3_000_000)
    def knobs():
        e.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1)); e.uc.reg_write(UC_ARM_REG_R4, MGR)
        e.call(0x08033B3E, maxins=8_000_000)
        return list(struct.unpack("<69H", bytes(e.uc.mem_read(e.r32(e.r32(MGR + 0x90)), 138))))[60:68]
    e.w32(MGR + 0x6C, CK.SETUP_OBJ); e.uc.mem_write(CK.SETUP_OBJ + CK.ADV_OFF, bytes([0]))
    a = g(); knob(0, 20); knob(1, 9); knob(2, 5); knob(7, 5); b_ = g(); knob(0, 127); knob(0, 127); knob(1, -100); c = g()
    o["setup"] = (a, b_, c); o["led"] = knobs()
    e.uc.mem_write(CK.SETUP_OBJ + CK.ADV_OFF, bytes([1])); knob(0, -30); knob(1, 30); o["adv"] = (c, g(), knobs()[:2])
    del e; gc.collect(); return o


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["compkn"]["labels"].items()}
    w = lambda im, a: struct.unpack_from("<I", im, a - B)[0]
    from thumb import bl
    others = all(w(img, CK.SETUP_VT + 4 * i) == w(prev, CK.SETUP_VT + 4 * i) for i in range(-2, 10) if i != 4)
    head = next((int(man["report"][m]["labels"][n], 16) for m, n in (("patchain", "c_pcledtask"), ("stepmod", "c_rfledtask")) if m in man["report"]), L["c_ckledtask"])      # (a later build: the chain goes on)
    check(w(img, CK.SETUP_VT + 16) == L["c_ckknob"] | 1 and w(prev, CK.SETUP_VT + 16) == 0x080475A1 and others and all(bytes(img[c - B:c - B + 4]) == bl(c, head) for c in PK.LED_CALLS),
          "the hooks: slot 4 of the Setup view (the stock: a do-nothing stub), every other slot of the view as before, the two LED task calls")
    o = run(img, man)
    a, b_, c = o["setup"]
    check(b_[3] == a[3] + 20 and b_[4] == a[4] + 9 and b_[:3] + b_[5:] == a[:3] + a[5:] and c[3] == 127 and c[4] == 0, f"the Setup view: K1 = value 3 (the attack), K2 = value 4 (the release), limited ({a} -> {b_} -> {c}); the switches, the filter and the gain untouched; K3 / K8 nothing")
    check(o["led"][:2] == [CK.COL | (127 + 2) << 8, CK.COL | 2 << 8], f"the knob LEDs: K1 / K2 white with their value ({[hex(x) for x in o['led'][:3]]})")
    check(o["adv"][0] == o["adv"][1] and all(x >> 8 == 0 for x in o["adv"][2]), "the Advanced page: the knobs do nothing, no LEDs of ours")
    gc.collect(); q = run(prev, prev_man)
    check(q["setup"][0] == q["setup"][1] == q["setup"][2], "the previous build: the knobs do nothing in the Setup view")
    print("SC40.2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
