"""SC48 ARM tests (tools/midipre.py): MIDI 1 / 2 pressed twice = their Preset view; pad 27 dim white there with the engine off.  Through the
controller (0x08033320 / 0x0803381A) and the real LED task:
  * MIDI 1 once: its track view (the controller's subview 19); again 500 ms later: still there (not a double press); twice within 400 ms: its
    Preset view (18), as the Preset button gives; MIDI 2 the same (27); with Shift held: nothing of ours;
  * the MIDI 1 Preset view with the engine off: pad 27 = 0x02; the engine on (the oscillator, modesel's row): pad 27 its colour, not 0x02.

    python tools/emu_midipre.py SC48.bin SC48_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402  (its import sets vcf21's options)
import midipre as M  # noqa: E402

MGR = X.MGR
CUR = 0x152                                      # the controller's subview: 9 x track + 0 (Preset) / 1 (track view)


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(Path(img).read_bytes(), man)
    cur = lambda: e.r8(MGR + CUR)
    t = 1000; e.at(t)
    e.btn(0); e.btn(2); c1 = cur()
    t += 500; e.at(t); e.btn(2); c2 = cur()
    check(c1 == 19 and c2 == 19, f"MIDI 1 once, again 500 ms later: its track view ({c1}, {c2})")
    t += 1000; e.at(t); e.btn(2); t += 150; e.at(t); e.btn(2)
    check(cur() == 18, f"MIDI 1 twice within 400 ms: its Preset view ({cur()})")
    t += 1000; e.at(t); e.btn(3); t += 150; e.at(t); e.btn(3)
    check(cur() == 27, f"MIDI 2 twice: its Preset view ({cur()})")
    t += 1000; e.at(t); e.btn(2); c3 = cur(); t += 150; e.at(t); e.shift(True); e.btn(2); e.shift(False)
    check(cur() == c3, f"with Shift: nothing of ours ({c3} -> {cur()})")
    t += 1000; e.at(t); e.btn(2); t += 150; e.at(t); e.btn(2); f = X.frame(e)
    check(cur() == 18 and f[M.PAD] & 0xFF == M.COL_OFF, f"MIDI 1 Preset view, the engine off: pad 27 dim white ({f[M.PAD]:#x})")
    e.pad(26); e.pad(16 + 2); e.pad(26); f = X.frame(e)
    check(f[M.PAD] & 0xFF not in (0, M.COL_OFF), f"the engine on (the oscillator): pad 27 its colour ({f[M.PAD]:#x})")
    del e; gc.collect()
    print(f"{Path(img).stem} RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(a[0], json.loads(Path(a[1]).read_text())) else 0)
