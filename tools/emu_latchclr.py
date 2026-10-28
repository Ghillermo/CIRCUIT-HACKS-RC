"""SC48.3 / Beta 3.40 (latchclr): Clear + a note track's button lets go of its latched notes (emu_arpx's harness, the controller).

    python tools/emu_latchclr.py SC48.3.bin SC48.3_manifest.json

  * Synth 1's Note view, the arpeggiator off: Shift + pad 21 = 67 latched (its note on);
  * Synth 1's button alone: nothing let go; Clear held + Synth 1's button: 67's note off, the latch bits of Synth 1 at 0;
  * pad 21 again: a plain note on (not the latch's stop).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arpx as AX  # noqa: E402

CLEAR = 23


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["arpx"]["labels"].items()}
    e = AX.EX(img, man); e.note_view(setting=0)
    e.ifc.clear(); e.pad(20, shift=True); on = [x for x in e.ifc if x[0] == "on"]
    def bits():
        out = []
        for j in range(16):
            e.call(lab["c_ltbit"], 0, 8 * j); out.append(e.r8(e.uc.reg_read(AX.EA_.UC_ARM_REG_R0)))
        return out
    b0 = bits()
    check(len(on) == 1 and on[0][2] == 67 and any(b0), f"Shift + pad 21: 67 on, latched ({on}, bits {sum(bin(x).count('1') for x in b0)})")
    e.ifc.clear(); e.press(0); e.release(0); plain = list(e.ifc)
    check(not [x for x in plain if x[0] == "off"] and bits() == b0, f"Synth 1's button alone: nothing let go ({plain})")
    e.note_view(setting=0)
    e.ifc.clear(); e.press(CLEAR); e.press(0); e.release(0); e.release(CLEAR); cl = list(e.ifc); b1 = bits()
    check(("off", cl[0][1] if cl else 0, 67) in [(x[0], x[1], x[2]) for x in cl] and not any(b1), f"Clear + Synth 1: 67 off, the latch bits at 0 ({cl}, {b1})")
    e.note_view(setting=0)
    e.ifc.clear(); e.pad(20); again = list(e.ifc)
    check([x[0] for x in again][:1] == ["on"], f"pad 21 again: a plain note on ({again})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} LATCHCLR RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
