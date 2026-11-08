"""SC54 tests: tools/extstep.py (the Setup view's Note toggle on: an external note played while a step is held goes into that step, as a pad would),
on emu_arpx's harness (the MIDI-in dispatcher, Synth 1's Note view).

    python tools/emu_extstep.py BUILD.bin manifest.json
  * the toggle off, step 3 held, an external 62: step 3 stays empty;
  * the toggle on, no step held, an external 62: nothing written;
  * the toggle on, step 3 held, external 62 then 65: step 3 has both (velocity 90 / 80);
  * an internal injection with step 3 held: not written.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_arpx as AX  # noqa: E402
import emu_arp as EA_  # noqa: E402
import arpx as X  # noqa: E402
import gmdrum as G  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = AX.EX(img, man)
    p = e.note_view(setting=0)
    base = e.settings(0, p) - 0x380
    def step(s):
        b = bytes(e.uc.mem_read(base + 28 * s, 28))
        return sorted((b[4 + 4 * u], b[7 + 4 * u]) for u in range(6) if b[0] >> u & 1)
    def take(n, v, inj=False):
        e.pad(2, up=False); e.midi(0x90, n, v, inj); e.midi(0x80, n, 0, inj); e.unpad(2)
    take(62, 90)
    check(step(2) == [], f"the toggle off: step 3 stays empty ({step(2)})")
    e.call(e.lab("gmdrum", "c_gmput"), G.B_FLAGS, X.F_ARX)
    e.midi(0x90, 62, 90); e.midi(0x80, 62, 0)
    check(step(2) == [], f"the toggle on, no step held: nothing written ({step(2)})")
    e.pad(2, up=False); e.midi(0x90, 62, 90); e.midi(0x90, 65, 80); e.midi(0x80, 62, 0); e.midi(0x80, 65, 0); e.unpad(2)
    check(step(2) == [(62, 90), (65, 80)], f"the toggle on, step 3 held: external 62 and 65 in the step ({step(2)})")
    take(67, 70, inj=True)
    check(67 not in [n for n, _ in step(2)], f"an internal injection: not written ({step(2)})")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} EXTSTEP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes()
    man = json.loads(Path(sys.argv[2]).read_text())
    sys.exit(1 if main(img, man) else 0)
