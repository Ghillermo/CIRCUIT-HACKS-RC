"""SC39.1: the engine tests of earlier builds (emu_sc36_1: the FX sequencer / Glitch slots; emu_sc38_1: the granular stretch) on a build with the own-synth
patches.  Their harness has no model of the SD card, and from SC39.1 on the Preset view of MIDI 1 / 2 asks the card for its patch slots on every LED pass
(tools/mpatch.py), so the content API is answered here as a card without patch banks (size 0, the shared buffer's lock granted).

    python tools/emu_sc39_1_reg.py SC39.1.bin SC39.1_manifest.json SC38.bin SC38_manifest.json
"""
import json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_LR, UC_ARM_REG_PC
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc05  # noqa: E402
import packio as PK  # noqa: E402

_init = emu_sc05.E.__init__


def init(self, *a, **k):
    _init(self, *a, **k)
    def stub(v):
        def f(uc, a_, s, d): uc.reg_write(UC_ARM_REG_R0, v); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        return f
    for ad, v in ((PK.SIZE, 0), (PK.BUF_LOCK, PK.BUF), (PK.BUF_UNLOCK, 0), (PK.READ, 2), (PK.WRITE, 2)):
        self.uc.hook_add(UC_HOOK_CODE, stub(v), begin=ad & ~1, end=ad & ~1)


emu_sc05.E.__init__ = init

if __name__ == "__main__":
    a = sys.argv
    img, man = Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())
    import emu_sc36_1, emu_sc38_1  # noqa: E402
    f = emu_sc36_1.main(img, man) or 0
    f += emu_sc38_1.main(img, man, Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) or 0
    print("SC39.1 REGRESSION RESULT:", "ALL PASS" if f == 0 else f"{f} FAILURES")
    sys.exit(1 if f else 0)
