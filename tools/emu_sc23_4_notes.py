"""SC23.4: the drum Note view squares at the left of the bottom row are MIRRORED (pad 25 = drum 4 ... pad 28 = drum 1; pads 29-32 = drums 1-4 as stock), LEDs and presses / releases through the controller.

    python tools/emu_sc23_4_notes.py SC23.4.bin SC23.4_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc21_3 import E213, MGR, e_mode  # noqa: E402
import drumnote as N  # noqa: E402

N.MIRROR = True


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    gc.collect(); n = E213(img, man)
    for d in range(4):
        n.sel(d); n.call(0x08033320, MGR, 9, maxins=600000); n.call(0x0803381A, MGR, 9, maxins=600000)
        f = n.frame()[:32]
        check(e_mode(n) == 6 and all(f[24 + k] == f[31 - k] for k in range(4)) and len(set(f[28:32])) == 4, f"Drum {d + 1} Note view: pads 25-28 = the squares of pads 32-29 {[hex(x) for x in f[24:32]]}")
    n.sel(1); n.call(0x08033320, MGR, 9, maxins=600000); n.call(0x0803381A, MGR, 9, maxins=600000)
    n.hook_delegate(1)
    res = {}
    for p in range(24, 32):
        n.hits.clear(); n.pad(p); a = sorted(set(h for h in n.hits if h[0] == "press")); n.hits.clear()
        n.relpad(p); rl = sorted(set(h for h in n.hits if h[0] == "release")); n.hits.clear()
        res[p] = (a, rl)
    check(all(res[p] == res[55 - p] and res[p][0] != [] for p in range(24, 28)), f"pads 25-28 press / release = pads 32-29: {[res[p] for p in range(24, 32)]}")
    check(len({res[p][0][0] for p in range(28, 32)}) == 4 and res[24][0] == res[31][0] and res[27][0] == res[28][0], "pad 25 = drum 4, pad 28 = drum 1")
    print("SC23.4 DRUM NOTE MIRROR RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
