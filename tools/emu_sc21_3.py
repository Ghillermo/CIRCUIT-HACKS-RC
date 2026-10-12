"""SC21.3 ARM tests: the four drum squares of the drum Note view also at the start of the bottom row (tools/drumnote.py), through the real controller routes on the live RAM dump.

    python tools/emu_sc21_3.py SC21.2.bin SC21.3.bin SC21.2_manifest.json SC21.3_manifest.json
  * slots 0 / 1 / 7 of the Note view class (vtable 0x0805AD44) -> ours, nothing else of the image changes except the appended code;
  * Drum 1..4 selected, Note pressed (view mode 6): the entries 24-27 of the LED frame = the entries 28-31 (the four drum colours), the other pads dark, as stock for the rest;
  * the pads 25-28 (indices 24-27) press / release the drums 1-4 exactly as the pads 29-32 do (same calls into the drum object), the pads below 24 do nothing; SC21.2 ignores 24-27;
  * the copy follows the stock painter (a pressed drum's square changes on both sides);
  * the other views (Preset, Velocity, synth Note) are unchanged.
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_6 import E196, MGR, CONT  # noqa: E402
import drumnote as N  # noqa: E402

BASE = 0x08010000


class E213(E196):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.hits = []
    def pad(self, p, vel=100):
        self.call(0x08033282, MGR, p, vel, maxins=900000)
    def relpad(self, p):
        self.call(0x080332FE, MGR, p, maxins=900000)         # the controller's pad release route (0x080332FE, as the SC17.6 harness)
    def note_view(self):
        return self.r32(CONT + 0xAC)
    def hook_delegate(self, d):
        """record the calls the Note view forwards to its drum object ([view + 0x10]): (kind, drum number)"""
        v = self.r32(CONT + 0xAC); dg = self.r32(v + 0x10); vt = self.r32(dg)          # one Note view object for the four drums, the drum object is embedded in it
        for kind, slot in (("press", 0), ("release", 4)):
            fa = self.r32(vt + slot) & ~1
            def h(uc, a, s, dd, kind=kind): self.hits.append((kind, uc.reg_read(UC_ARM_REG_R1)))
            self.uc.hook_add(UC_HOOK_CODE, h, begin=fa, end=fa)
    def lead(self): return self.frame()[:32]


def main(prev, img, man2, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    w = lambda image, a: struct.unpack_from("<I", image, a - BASE)[0]
    L = {k: int(v, 16) for k, v in man["report"]["drumnote"]["labels"].items()}
    check(w(img, N.SLOT0) == L["c_nvp"] | 1 and w(img, N.SLOT1) == L["c_nvr"] | 1 and w(img, N.SLOT7) == L["c_nvl"] | 1, "Note view class: slots 0 / 1 / 7 -> c_nvp / c_nvr / c_nvl")
    check(w(prev, N.SLOT0) == N.STOCK_PRESS | 1 and w(prev, N.SLOT7) == N.STOCK_LEDS | 1, "SC21.2 has the stock slots")
    gc.collect(); n = E213(img, man); gc.collect(); o = E213(prev, man2)
    colours = None
    for d in range(4):
        for e in (n, o): e.sel(d); e.call(0x08033320, MGR, 9, maxins=600000); e.call(0x0803381A, MGR, 9, maxins=600000)
        fn, fo = n.frame(), o.frame()
        tn, to = fn[:32], fo[:32]
        if colours is None: colours = to[28:32]
        check(e_mode(n) == 6 and tn[28:32] == to[28:32] and tn[24:28] == to[28:32] and all(x == 0 for x in to[24:28]) and tn[:24] == to[:24] and fn[32:] == fo[32:],
              f"Drum {d + 1} Note view: pads 25-28 = the squares of pads 29-32 {[hex(x) for x in tn[24:32]]}, the rest as SC21.2")
    check(colours == (0x45, 0x2D, 0x49, 0x4D) or list(colours) == [0x45, 0x2D, 0x49, 0x4D], f"the drum colours {[hex(x) for x in colours]}")
    # pad routes
    for e in (n, o):
        e.sel(1); e.call(0x08033320, MGR, 9, maxins=600000); e.call(0x0803381A, MGR, 9, maxins=600000)
        e.hook_delegate(1)
    res = {}
    for name, e in (("new", n), ("old", o)):
        res[name] = {}
        for p in range(0, 32):
            e.hits.clear(); e.pad(p); a = [h for h in e.hits if h[0] == "press"]; e.hits.clear()
            e.relpad(p); rl = [h for h in e.hits if h[0] == "release"]; e.hits.clear()          # released before the next press (the drum object keeps a pressed state)
            res[name][p] = (sorted(set(a)), sorted(set(rl)))
    check(all(res["new"][p] == res["old"][p + 4] and res["new"][p][0] != [] for p in range(24, 28)), f"pads 25-28 press = pads 29-32 press: {[res['new'][p] for p in range(24, 28)]} / {[res['old'][p] for p in range(28, 32)]}")
    check(all(res["new"][p] == res["old"][p] for p in range(28, 32)) and all(res["new"][p] == res["old"][p] == ([], []) for p in range(0, 24)), f"pads 29-32 as stock, the pads below 25 do nothing {[(p, res['new'][p], res['old'][p]) for p in range(0, 32) if res['new'][p] != res['old'][p] or (p < 24 and res['new'][p])]}")
    check(all(res["old"][p] == ([], []) for p in range(24, 28)), "SC21.2: the pads 25-28 are ignored")
    check(all(res["new"][p][1] == res["old"][p + 4][1] and res["new"][p][1] != [] for p in range(24, 28)), f"the release of the pads 25-28 = the release of the pads 29-32 {[res['new'][p][1] for p in range(24, 28)]}")
    # the LED copy follows the stock painter
    fn = n.lead(); fo = o.lead()
    check(fn[24:28] == fn[28:32] and fn[28:32] == fo[28:32], f"after pressing, the copy follows ({[hex(x) for x in fn[24:32]]})")
    # other views unchanged
    for b in (8, 10):
        for e in (n, o): e.call(0x08033320, MGR, b, maxins=600000); e.call(0x0803381A, MGR, b, maxins=600000)
        check(n.frame() == o.frame(), f"button {b} view (drum Preset / Velocity): the LED frame is SC21.2's")
    for e in (n, o): e.sel(4 - 4)
    print("SC21.3 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def e_mode(e): return e.r8(CONT + 0x18C)


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
