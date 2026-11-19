"""Alpha 7.06 (tools/dbtoggle.py): Shift + Synth 1 / 2 / MIDI 1 / 2 toggles that track's page, through the controller (emu_dblpress's harness).
For each track t: its page opened (sub-mode 9 t: Shift + t, again if the first only reached its Note view, as from the Mixer on a fresh start);
  * Shift + t = its Note view (sub-mode 9 t + 1), the Shift byte 1 again after;
  * Shift + t again = the page again;
  * Shift + another track u = u's page (unchanged).
The previous build (Alpha 7.05): Shift + t on its page stays on the page.

    python tools/emu_dbtoggle.py BUILD.bin manifest.json"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import emu_sc22_4 as T4  # noqa: E402,F401  (its import sets vcf21's options)
import srcview as SV  # noqa: E402

N = ["Synth 1", "Synth 2", "MIDI 1", "MIDI 2"]


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = X.EP(img, man); MGR = X.MGR
    sub = lambda: e.r8(MGR + SV.S_CUR)
    shift_byte = lambda: e.r8(e.r0(0x0803542C, e.r32(MGR + 0xC), 0))
    def sh(i):
        e.shift(True); e.btn(i); b = shift_byte(); e.shift(False); return b
    for t in range(4):
        e.btn(14)
        for _ in range(3):
            sh(t)
            if sub() == 9 * t: break
        p = sub()
        sb = sh(t); s1 = sub()
        sh(t); s2 = sub()
        u = (t + 1) % 4; sh(u); s3 = sub()
        check(p == 9 * t and s1 == 9 * t + 1 and sb == 1 and s2 == 9 * t and s3 == 9 * u,
              f"{N[t]}: its page ({p}); Shift + {N[t]} = its Note view ({s1}, Shift byte {sb}); again = the page ({s2}); Shift + {N[u]} = its page ({s3})")
    print(f"{man['marker']} DBTOGGLE RESULT: {'ALL PASS' if not fails else f'{fails} FAIL'}")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
