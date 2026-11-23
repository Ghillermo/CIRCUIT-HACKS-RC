"""Alpha 7.32 test (novasec.use_v3, the own synth of MIDI 1), through the controller:
  * the assigned-knob page (pad 1): pad 1 held + K2 = slot 2 freed (code 0), K2's LED red; Duplicate + K3 there = nothing;
  * Clear + K4 there = vcf21's (the slot stays);
  * OSC 1, Duplicate + K3 (code 19) = into slot 2 (p4dest), slot 2's LED (K2) white; Duplicate + K3 again = the same hint, nothing more;
  * Shift held + pad 1 held + K1 = the non-sequenceable page's slot 1 freed, K1 red;
  * without anything held, a knob on page 4 still goes to the chain (the row unchanged).
    python tools/emu_novasec3own.py firmware/a7.32
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import vcf21 as V  # noqa: E402
import novasec as N  # noqa: E402

MGR, DUPB, CLRB = 0x20040B10, 24, 23
PRESS, RELEASE = 0x08033282, 0x080332FE
WHITE, RED, ORANGE = N.FL_COL


def main(a):
    d = Path(a[0]); img = next(d.glob("*.bin")).read_bytes(); man = json.loads((d / "manifest.json").read_text())
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.r8(V.TAIL + V.O_FLAGS) | 0x05]))
    row = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow"], 0), 8))
    row2 = lambda: tuple(e.uc.mem_read(e.r0(e.vl["c_vrow2"], 0), 8))
    btn = lambda i, v: e.call(0x08033320 if v else 0x0803381A, MGR, i, maxins=8_000_000)
    def held(k, dl=1, b=None, pad=None, n=2):
        if b is not None: btn(b, True)
        if pad is not None: e.call(PRESS, MGR, pad, 100, maxins=8_000_000)
        for _ in range(n): e.knob(k, dl)
        f = X.frame(e)
        if pad is not None: e.call(RELEASE, MGR, pad, maxins=8_000_000)
        if b is not None: btn(b, False)
        return f
    e.btn(2); e.btn(8)
    r40, r20 = row(), row2()
    e.pad(0)
    f = held(1, pad=0)
    check(row()[1] == 0 and row()[:1] + row()[2:] == r40[:1] + r40[2:] and f[61] & 0xFF == RED, f"pad 1 held + K2: slot 2 freed ({row()}), K2 red ({f[61]:#x})")
    r_a = row(); held(2, b=DUPB)
    check(row() == r_a, f"Duplicate + K3 on the assigned page: nothing ({row()})")
    held(3, -1, b=CLRB, n=4)
    check(row() == r_a, f"Clear + K4 there: the slot stays ({row()})")
    e.pad(1); f = held(2, b=DUPB)
    check(row()[1] == 19 and f[61] & 0xFF == WHITE, f"OSC 1, Duplicate + K3: code 19 into slot 2 ({row()}), K2 white ({f[61]:#x})")
    f = held(2, b=DUPB)
    check(row().count(19) == 1 and f[61] & 0xFF == WHITE, f"again: the same hint, nothing more ({f[61]:#x})")
    e.shift(True); f = held(0, pad=0); e.shift(False)
    check(row2()[0] == 0 and row2()[1:] == r20[1:] and f[60] & 0xFF == RED, f"Shift + pad 1 held + K1: the non-sequenceable slot 1 freed ({row2()}), K1 red ({f[60]:#x})")
    e.pad(0); r_b = row(); e.knob(0, 3)
    check(row() == r_b, "a knob alone on page 4: the row unchanged")
    print("NOVASEC3OWN RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
