"""SC48 ARM tests (tools/notearp.py): the external keyboard through the arpeggiator on the normal Setup's Note button.  Through the controller
(buttons 0x08033320, pads 0x08033282) and the real LED task:
  * normal Setup, Note: bit 2 of gmdrum's flags on in both copies (the signature written), the save asked, still in Setup; Note's LED 0x74;
    Note again: off, LED 0x55; with Shift: nothing;
  * Advanced Setup (entered as at the boot, 0x08047494): pad 22 changes nothing and is dark.

    python tools/emu_notearp.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_gmdrum as EGM  # noqa: E402
import emu_sc42_6 as X  # noqa: E402
import notearp as NA  # noqa: E402
import arpx as AX  # noqa: E402
import gmdrum as G  # noqa: E402
import pgmch as PG  # noqa: E402

MGR = EGM.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = EGM.EG(Path(img).read_bytes(), man)
    flag = lambda c: e.param(G.P0, c)[G.B_FLAGS] & AX.F_ARX if e.param(G.P0, c)[1] == G.SIG else 0
    btn = lambda i: (e.call(0x08033320, MGR, i, maxins=8_000_000), e.call(0x0803381A, MGR, i, maxins=8_000_000))
    e.setup(True, adv=0); e.unpend()
    f0 = flag(0); btn(NA.NOTE_BTN); f = X.frame(e)
    check(f0 == 0 and flag(0) == flag(1) == AX.F_ARX and e.pending(), f"normal Setup, Note: on in both copies, the save asked ({flag(0)}, {flag(1)})")
    check(f[NA.LED_NOTE] == NA.COL_ON, f"Note's LED green ({f[NA.LED_NOTE]:#x})")
    btn(NA.NOTE_BTN); f = X.frame(e)
    check(flag(0) == 0 and f[NA.LED_NOTE] == NA.COL_OFF, f"Note again: off, its LED dim red ({flag(0)}, {f[NA.LED_NOTE]:#x})")
    e.shift(True); btn(NA.NOTE_BTN); e.shift(False)
    check(flag(0) == 0, "with Shift: nothing")
    e.setup(True, adv=1); e.call(0x08047494, e.r32(MGR + 0x68), 1, maxins=4_000_000)
    e.call(0x08033282, MGR, AX.PAD_ARX, 100, maxins=8_000_000); f = X.frame(e)
    check(flag(0) == 0 and f[AX.PAD_ARX] == 0, f"Advanced Setup, pad 22: nothing, dark ({flag(0)}, {f[AX.PAD_ARX]:#x})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
