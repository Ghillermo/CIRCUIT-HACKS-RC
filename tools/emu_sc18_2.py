"""SC18.2 / SC18.3 ARM tests: FX view button LEDs and the new drum knob LEDs, through the stock LED path.

    python tools/emu_sc18_2.py SC18.1.bin SC18.2.bin SC18.2_manifest.json
The LED frame is produced by running the stock tail of the controller's store listener at 0x08033B3E (r4 = controller:
ldr r2,[r4,#0x90]; mov r0,r4; ldr r1,[r2]; bl LED task  <- patched;  pop {r0,r1,r4,pc}) with a fake frame, so the patched
call site, the wrapper and the stock task all run; the 69 panel LEDs are read from [[ctrl+0x90]].
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc17_5 import EA, MGR  # noqa: E402
from emu_sc05 import STOP  # noqa: E402
from emu_sc08 import CONT  # noqa: E402
import leds18 as L  # noqa: E402
import ct_fw  # noqa: E402
from thumb import bl as bl_enc  # noqa: E402

TAIL = 0x08033B3E
SEL_TRACK = 0x188                     # container: store of the selected track (0..7, drums 4..7)


class E182(EA):
    def frame(self):
        self.uc.mem_write(0x2006F000, struct.pack("<4I", 0, 0, MGR, STOP | 1))
        self.uc.reg_write(UC_ARM_REG_R4, MGR)
        self.call(TAIL, maxins=5_000_000)
        return list(struct.unpack("<69H", bytes(self.uc.mem_read(self.r32(self.r32(MGR + 0x90)), 138))))
    def track(self, t): self.set_p0(self.r32(CONT + SEL_TRACK), t)


def main(prev, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]["leds18"]
    lab = {k: int(v, 16) for k, v in rep["labels"].items()}
    for c in L.LED_TASK_CALLS:
        check(bytes(img[c - ct_fw.APP_BASE:c - ct_fw.APP_BASE + 4]) == bl_enc(c, lab["c_ledtask"]), f"call {c:#x} -> c_ledtask")
    want = {int(k): int(v, 16) for k, v in rep["fx_leds"].items()}           # LED -> code, as built (SC18.3: other Octave colours)

    def frames(image, setup):
        gc.collect(); e = E182(image); setup(e); return e.frame()
    # ---- FX view
    for name, setup in (("FX view", lambda e: e.btn(15)), ("FX view, delay page (Octave UP)", lambda e: (e.btn(15), e.btn(20))),
                        ("FX view, reverb page (Octave DOWN)", lambda e: (e.btn(15), e.btn(19)))):
        a, b = frames(prev, setup), frames(img, setup)
        check(all(b[i] == v for i, v in want.items()), f"{name}: Octave UP / DOWN, Duplicate, 1-16/17-32 = {[hex(b[i]) for i in want]}")
        check(all(a[i] == b[i] for i in range(69) if i not in want), f"{name}: every other LED as SC18.1")
        if man["marker"] == "SC18.3" and "page" not in name:                      # Octave UP / DOWN = colour of pads 1 / 17
            check(b[L.LED_OCT_UP] == b[0] and b[L.LED_OCT_DN] == b[16], f"{name}: Octave UP = pad 1 ({b[0]:#x}), DOWN = pad 17 ({b[16]:#x})")
    # ---- other views untouched
    for name, setup in (("Mixer", lambda e: e.btn(14)), ("power-up view", lambda e: None)):
        a, b = frames(prev, setup), frames(img, setup)
        check(a == b, f"{name}: all 69 LEDs as SC18.1")
    # ---- drum knobs: K1 / K3 / K5 / K7 in the drum colour, K2 / K4 / K6 / K8 stock
    dc = [int(x, 16) for x in rep["drum_codes"]]
    check(dc == [0x45, 0x2D, 0x49, 0x4D], f"drum colours = palette 5..8 {rep['drum_codes']}")
    for t in range(8):
        setup = lambda e, t=t: e.track(t)
        a, b = frames(prev, setup), frames(img, setup)
        if t < 4:
            check(a == b, f"track {t + 1} (synth / MIDI): LEDs as SC18.1")
            continue
        d = t - 4
        kn_a, kn_b = a[60:68], b[60:68]
        check(kn_a[0::2] == [0] * 4 and kn_b[0::2] == [dc[d]] * 4 and kn_b[1::2] == kn_a[1::2] == [0xE1 + 4 * d + i for i in range(4)],
              f"drum {d + 1}: K1/K3/K5/K7 lit {hex(dc[d])}, K2/K4/K6/K8 stock {[hex(x) for x in kn_b]}")
        check(a[:60] == b[:60] and a[68] == b[68], f"drum {d + 1}: other LEDs as SC18.1")
    print("SC18.2 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes(), json.loads(Path(sys.argv[3]).read_text())) else 0)
