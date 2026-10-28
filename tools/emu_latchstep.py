"""SC48.4 / Beta 3.41: latched notes bright cyan with Shift (arpx.use_latchcyan) and Shift + a step in the Note view = the latched notes into
that step (latchstep), through the controller and the real LED source (emu_arpx's harness: Synth 1's Note view, a chord 64 / 60 / 67 at step 1):
  * nothing latched: Shift + step 3 leaves its record as it was (the stock's);
  * Shift + pad 21 (67) and Shift + pad 18 (62) latched: with Shift their keys 0x4D, every other key as without Shift;
  * Shift + step 3: its record = 67 and 62 (one step long, velocity 100, micro step 0), the step pad lit as a step with notes;
  * Shift + step 1 (64, 60, 67 there): only 62 added (4 notes);
  * the LED task's frame with Shift: nothing latched = the steps not yellow; latched = steps 1-16 yellow (0x2D); without Shift, not.

    python tools/emu_latchstep.py SC48.4.bin SC48.4_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arpx as AX  # noqa: E402
import emu_sc42_6 as X6  # noqa: E402
import arpx as X  # noqa: E402
import latchstep as LS  # noqa: E402

MGR = 0x20040B10


def notes(rec):
    m = rec[0]
    return sorted(rec[4 + 4 * u] for u in range(6) if m >> u & 1), [tuple(rec[4 + 4 * u:8 + 4 * u]) for u in range(6) if m >> u & 1]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    lab = {k: int(v, 16) for k, v in man["report"]["autorel"]["labels"].items()}
    e = AX.EX(img, man); e.note_view(setting=0)
    check(e.r8(MGR + 0x152) == 1, f"Synth 1's Note view (sub {e.r8(MGR + 0x152)})")
    e.call(lab["c_arpat"], 0); pat = e.uc.reg_read(UC_ARM_REG_R0)
    rec = lambda s: bytes(e.uc.mem_read(pat + 28 * s, 28))
    r0 = rec(2); l0 = e.pads()
    def frame(sh):
        e.set_p0(e.r32(MGR + 0xC), 1 if sh else 0); f = X6.frame(e); e.set_p0(e.r32(MGR + 0xC), 0); return [x & 0xFF for x in f[:16]]
    y0 = frame(True)
    check(y0 != [LS.COL_AV] * 16, f"nothing latched, Shift: the steps not yellow ({[hex(x) for x in y0]})")
    e.pad(2, shift=True)
    check(rec(2) == r0, f"nothing latched: Shift + step 3 leaves it ({rec(2)[:8].hex()})")
    e.pad(20, shift=True); e.pad(17, shift=True)
    ls, ln = e.pads(shift=True), e.pads()
    keys = [i for i in range(16, 32) if i not in (17, 20)]
    check(ls[20] & 0xFF == X.COL_CYAN and ls[17] & 0xFF == X.COL_CYAN and all(ls[i] == ln[i] for i in keys),
          f"with Shift: the latched keys cyan, the others as without Shift ({[hex(x) for x in ls[16:32]]})")
    check(ln[20] & 0xFF != X.COL_CYAN, f"without Shift: not cyan ({ln[20]:#x})")
    y1, y2 = frame(True), frame(False)
    check(y1 == [LS.COL_AV] * 16 and y2 != [LS.COL_AV] * 16, f"latched, Shift: steps 1-16 yellow; without Shift not ({[hex(x) for x in y1]}, {[hex(x) for x in y2]})")
    e.ifc.clear(); e.pad(2, shift=True); n2, u2 = notes(rec(2)); l2 = e.pads()
    check(n2 == [62, 67] and all(u[1:] == (LS.GATE, 0, LS.VEL) for u in u2), f"Shift + step 3: 62 and 67 written ({u2})")
    check(l2[2] != l0[2], f"step 3 lit as a step with notes ({l0[2]:#x} -> {l2[2]:#x})")
    e.pad(0, shift=True); n0, _ = notes(rec(0))
    check(n0 == [60, 62, 64, 67], f"Shift + step 1 (64, 60, 67 there): only 62 added ({n0})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} LATCHSTEP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
