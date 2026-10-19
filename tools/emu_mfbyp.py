"""SC44.5 tests: Shift + pad 25 in the FX view = the master filter off / on (mfbyp.py), through the controller and the real LED task.

    python tools/emu_mfbyp.py NEW.bin NEW_manifest.json PREVIOUS.bin
  * the hooks: slot 0 of the FX view's class -> c_mfpress, every LED task call -> c_mfledtask;
  * FX view, Shift + pad 25: the filter (0x21 idx 0) to 64, its position kept; again: the position back; the resonance and every send stay;
  * LEDs: while off the filter knob's LED (68) red, also outside the FX view; with Shift in the FX view pad 25 yellow (on) / red (off);
  * the filter moved while off (the knob, a project): on again from there, the next Shift + pad 25 keeps the new position;
  * without Shift pad 25 in the FX view, and Shift + pad 25 outside it, leave the stores and views as PREVIOUS (SC44.4) does.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_fxres import EF  # noqa: E402
from emu_sc17_5 import FX  # noqa: E402
from emu_sc17_6 import PRESS, RELEASE  # noqa: E402
from emu_sc08 import MGR  # noqa: E402
import mfbyp as M  # noqa: E402
import packio as PK  # noqa: E402
import build_sc14 as S14  # noqa: E402
from thumb import bl  # noqa: E402

BASE = 0x08010000
RED_KNOB = (100 + 2) << 8 | M.RED


class EM(EF):
    def pad(self, p, shift=False):
        if shift: self.set_p0(self.r32(MGR + 0xC), 1)
        self.call(PRESS, MGR, p, 100, maxins=8_000_000); self.call(RELEASE, MGR, p, maxins=8_000_000)
        if shift: self.set_p0(self.r32(MGR + 0xC), 0)
    def off(self): return self.r32(M.MFB) == M.SIG


def main(img, man, prev):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    L = {k: int(v, 16) for k, v in man["report"]["mfbyp"]["labels"].items()}
    check(struct.unpack_from("<I", img, S14.FX_VT - BASE)[0] == L["c_mfpress"] | 1, "slot 0 of the FX view's class -> c_mfpress")
    check(all(img[c - BASE:c - BASE + 4] == bl(c, L["c_mfledtask"]) for c in PK.LED_CALLS), "every LED task call -> c_mfledtask")

    e = EM(img); e.btn(15)
    check(e.view() == FX, "FX button: FX view active")
    e.w32(M.MFB, 0x12345678)                                                     # the power-up pattern: on
    e.pset(0x21, 0, 20); e.pset(0x21, 1, 50)
    sends = [e.get(0x20, i) for i in range(25)]
    f = e.frame(shift=True)
    check(f[M.PAD] == M.YELLOW and f[M.LED_FILT] != RED_KNOB, f"on, Shift: pad 25 yellow ({f[M.PAD]:#x}), filter LED not red ({f[M.LED_FILT]:#x})")
    e.flush()
    e.pad(M.PAD, shift=True)
    check(e.get(0x21, 0) == 64 and e.off() and e.r8(M.MFB + 4) == 20, f"Shift + pad 25: filter {e.get(0x21, 0)} (64), kept {e.r8(M.MFB + 4)} (20)")
    w = e.flush(); check(len(w) > 0, f"the DSP gets the filter ({len(w)} writes)")
    check(e.get(0x21, 1) == 50 and [e.get(0x20, i) for i in range(25)] == sends, "resonance and every send / FX parameter untouched")
    f0, f1 = e.frame(), e.frame(shift=True)
    check(f0[M.LED_FILT] == RED_KNOB and f1[M.LED_FILT] == RED_KNOB, f"off: filter knob LED red ({f0[M.LED_FILT]:#x})")
    check(f1[M.PAD] == M.RED, f"off, Shift: pad 25 red ({f1[M.PAD]:#x})")
    check(f0[M.PAD] != M.RED and f0[M.PAD] != M.YELLOW, f"off, no Shift: pad 25 the stock's ({f0[M.PAD]:#x})")
    check(e.off(), "the LED task keeps it off while the filter is 64")
    e.pad(M.PAD, shift=True)
    check(e.get(0x21, 0) == 20 and not e.off(), f"Shift + pad 25 again: filter back to {e.get(0x21, 0)} (20)")
    f1 = e.frame(shift=True)
    check(f1[M.PAD] == M.YELLOW and f1[M.LED_FILT] != RED_KNOB, "on again: pad 25 yellow with Shift, filter LED not red")
    # ---- the filter moved while off
    e.pad(M.PAD, shift=True); check(e.off() and e.get(0x21, 0) == 64, "off again")
    e.pset(0x21, 0, 90); f0 = e.frame()
    check(not e.off() and f0[M.LED_FILT] != RED_KNOB, f"the filter moved to 90 while off: on again, LED not red ({f0[M.LED_FILT]:#x})")
    e.pad(M.PAD, shift=True); check(e.r8(M.MFB + 4) == 90 and e.get(0x21, 0) == 64, "the next Shift + pad 25 keeps 90")
    e.pad(M.PAD, shift=True); check(e.get(0x21, 0) == 90, "and gives 90 back")
    # ---- a filter already at the centre
    e.pset(0x21, 0, 64); e.pad(M.PAD, shift=True)
    check(e.off() and e.get(0x21, 0) == 64 and e.frame()[M.LED_FILT] == RED_KNOB, "from 64: off (LED red), still 64")
    e.pad(M.PAD, shift=True); check(not e.off() and e.get(0x21, 0) == 64, "on: 64")
    # ---- off, outside the FX view: the LED stays red
    e.pset(0x21, 0, 30); e.pad(M.PAD, shift=True); e.btn(14)
    f1 = e.frame(shift=True)
    check(e.view() != FX and f1[M.LED_FILT] == RED_KNOB, f"off, Mixer: filter LED red ({f1[M.LED_FILT]:#x})")
    e.pad(M.PAD, shift=True); check(e.off() and e.get(0x21, 0) == 64, "Shift + pad 25 in the Mixer: the filter stays off")
    del e; gc.collect()

    # ---- as SC44.4: pad 25 without Shift in the FX view, Shift + pad 25 elsewhere
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
    for name, prelude, shift in (("FX view, no Shift", [15], False), ("track view, Shift", [], True), ("Mixer, Shift", [14], True),
                                 ("Preset (8), Shift", [8], True)):
        (a, fa), (b, fb) = seq(prev, prelude, shift), seq(img, prelude, shift)
        check(a == b, f"{name}: pad 25 leaves the stores and views as SC44.4 (filter {b[-1][0]})")
        check(fa == fb, f"{name}: the LEDs as SC44.4")
    print("SC44.5 mfbyp RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text()), Path(a[2]).read_bytes()) else 0)
