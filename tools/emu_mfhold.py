"""SC44.6 tests: the master filter off (FX view, Shift + pad 25) holds whatever the knob does; on again = the knob's current position
(mfbyp.use_hold), through the controller, the real LED task and the stock DSP group flush.

    python tools/emu_mfhold.py NEW.bin NEW_manifest.json PREVIOUS.bin
  * the two reads of the filter for X:$CF (the stock master group, SC14's Auto-Filter restore) -> c_mfget;
  * off: the parameter keeps its value, the DSP gets X:$CF = 64; moving the filter while off changes the parameter, not the DSP, and it stays off
    (LED red); on again: the DSP gets the current position; on, the filter moves the DSP as always;
  * c_mfget: the centre while off, the parameter while on;
  * pad 25 without Shift in the FX view and Shift + pad 25 outside it leave the stores, views and LEDs as PREVIOUS (SC44.5) does.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_mfbyp import EM, RED_KNOB  # noqa: E402
from emu_sc17_5 import FX  # noqa: E402
import mfbyp as M  # noqa: E402
import fxkeys as K  # noqa: E402
from thumb import bl  # noqa: E402

BASE = 0x08010000
CF = 0xCF


def main(img, man, prev):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["mfbyp"]["labels"].items()}
    o = int(man["report"]["sc14"]["labels"]["gt_f_off"], 16)
    sites = [M.GROUP_GET] + [x for x in range(o, o + 24, 2) if img[x - BASE:x - BASE + 4] == bl(x, L["c_mfget"])]
    check(len(sites) == 2 and img[M.GROUP_GET - BASE:M.GROUP_GET - BASE + 4] == bl(M.GROUP_GET, L["c_mfget"]),
          f"the stock master group and SC14's restore read the filter through c_mfget {[hex(s) for s in sites]}")

    e = EM(img); e.btn(15)
    check(e.view() == FX, "FX button: FX view active")
    e.w32(M.MFB, 0x12345678)
    e.pset(0x21, 0, 20); e.pset(0x21, 1, 50); e.flush()
    def mfget():
        e.call(L["c_mfget"], 0x21, 0, maxins=2_000_000); return e.uc.reg_read(UC_ARM_REG_R0)
    check(mfget() == 20, f"on: c_mfget = the position ({mfget()})")
    e.pad(M.PAD, shift=True)
    w = e.flush()
    check(e.off() and e.get(0x21, 0) == 20, f"Shift + pad 25: off, the parameter stays 20 ({e.get(0x21, 0)})")
    check(w.get(CF) == 64 << 16, f"the DSP gets X:$CF = 64 ({w.get(CF, -1) >> 16})")
    check(mfget() == 64, f"off: c_mfget = 64 ({mfget()})")
    check(e.frame()[M.LED_FILT] == RED_KNOB, "off: filter LED red")
    e.pset(0x21, 0, 90); w = e.flush(); f0 = e.frame()
    check(e.off() and e.get(0x21, 0) == 90, f"the filter moved to 90 while off: the parameter 90, still off")
    check(w.get(CF, 64 << 16) == 64 << 16, f"... and the DSP stays at 64 ({w.get(CF, 64 << 16) >> 16})")
    check(f0[M.LED_FILT] == RED_KNOB, f"... LED still red ({f0[M.LED_FILT]:#x})")
    e.pset(0x21, 0, 100); e.flush()
    e.pad(M.PAD, shift=True); w = e.flush()
    check(not e.off() and w.get(CF) == 100 << 16, f"Shift + pad 25 again: on, the DSP gets the current position 100 ({w.get(CF, -1) >> 16})")
    check(e.frame()[M.LED_FILT] != RED_KNOB, "on: filter LED not red")
    e.pset(0x21, 0, 30); w = e.flush()
    check(w.get(CF) == 30 << 16, f"on: the filter moves the DSP as always ({w.get(CF, -1) >> 16})")
    check(e.get(0x21, 1) == 50, "the resonance untouched")
    e.pad(M.PAD, shift=True); e.btn(14); e.pset(0x21, 0, 10); w = e.flush()
    check(e.off() and w.get(CF, 64 << 16) == 64 << 16 and e.frame()[M.LED_FILT] == RED_KNOB, "off, in the Mixer: the knob does not reach the DSP, LED red")
    e.btn(15); e.pad(M.PAD, shift=True); w = e.flush()
    check(not e.off() and w.get(CF) == 10 << 16, f"on from the FX view: 10 ({w.get(CF, -1) >> 16})")
    del e; gc.collect()

    def seq(image, prelude, shift):
        x = EM(image)
        x.w32(M.MFB, 0)
        for p in prelude: x.btn(p)
        x.pset(0x21, 0, 20)
        x.pad(M.PAD, shift=shift)
        r = x.regions() + [bytes([x.get(0x21, 0)])]
        fr = x.frame()
        del x; gc.collect()
        return r, fr
    for name, prelude, shift in (("FX view, no Shift", [15], False), ("track view, Shift", [], True), ("Mixer, Shift", [14], True)):
        (a, fa), (b, fb) = seq(prev, prelude, shift), seq(img, prelude, shift)
        check(a == b, f"{name}: pad 25 leaves the stores and views as SC44.5 (filter {b[-1][0]})")
        check(fa == fb, f"{name}: the LEDs as SC44.5")
    print("SC44.6 mfhold RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes()) else 0)
