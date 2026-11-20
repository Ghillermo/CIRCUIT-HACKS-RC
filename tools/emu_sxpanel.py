"""S714D2 test (tools/sxpanel.py) through the real incoming SysEx dispatcher 0x0801EB30 (emu_sc35d8's harness: the router stubbed):
  * Shift on / off: p0 of [MGR + 0xC] follows; each request answered (0x45, the same bytes);
  * button 14 (Mixer) pressed and released: the Mixer is the active view; a pad of the Mixer reaches its handler; a knob event reaches the
    controller's knob entry with val - 64;
  * the black box's ring holds those gestures; an unrelated SysEx (the firmware identity query) still goes on to the next hook.

    python tools/emu_sxpanel.py BUILD.bin manifest.json
"""
from __future__ import annotations
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc35d8 as D  # noqa: E402
import sxpanel as SP  # noqa: E402
from unicorn import UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2  # noqa: E402

MIXER = 0x200447D4


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    e = D.E8(img, man)
    seen = []
    for a in SP.ENTRY.values():
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, ad, s, d: seen.append((ad, uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2) & 0xFFFFFFFF)), begin=a, end=a)
    def g(kind, ident, val, seq=1):
        q = list(SP.RD.SIG) + [SP.CMD, seq, kind, ident, val, 0, 0, 0, 0, 0xF7]
        e.out.clear(); e.sysex(q, 0)
        return e.out
    def shift():
        e.call(0x080354FA, SP.MGR and e.r32(SP.MGR + 0xC), 0, maxins=100000)
        return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    def p0(st):
        e.call(0x0803542C, st, 0, maxins=100000); return e.r8(e.uc.reg_read(UC_ARM_REG_R0))
    o = g(6, 0, 1)
    ours = [x for x in o if x[2][:5] == bytes(list(SP.RD.SIG) + [0x45])]
    check(p0(e.r32(SP.MGR + 0xC)) == 1 and len(ours) == 1, f"Shift held: p0 1, answered (and the stock's own Shift report: {[x[2].hex(' ') for x in o]})")
    g(6, 0, 0); check(p0(e.r32(SP.MGR + 0xC)) == 0, "Shift let go: p0 0")
    seen.clear(); g(1, 14, 0, 2); g(2, 14, 0, 3)
    check(e.r32(SP.MGR + 0x6C) == MIXER and (SP.ENTRY[1], 14, 0) in [(a, b, 0) for a, b, c in seen], f"button 14: the Mixer on screen ({e.r32(SP.MGR + 0x6C):#x})")
    seen.clear(); g(3, 5, 100, 4); g(4, 5, 0, 5)
    check(any(a == SP.ENTRY[3] and b == 5 and c == 100 for a, b, c in seen) and any(a == SP.ENTRY[4] and b == 5 for a, b, c in seen), "pad 6 pressed (velocity 100) and released through the entries")
    seen.clear(); g(5, 2, 64 - 3, 6)
    check(any(a == SP.ENTRY[5] and b == 2 and c == (-3 & 0xFFFFFFFF) for a, b, c in seen), f"knob 3, -3: the knob entry ({[(hex(a), b, hex(c)) for a, b, c in seen][:3]})")
    import blackbox as BB
    ring = bytes(e.uc.mem_read(BB.BB + BB.O.RING, 128))
    check(any(ring[i:i + 1] for i in range(0, 128, 8)) and ring != bytes(128), "the black box's ring is not empty")
    e.out.clear(); e.fwd = 0
    e.sysex(list(SP.RD.SIG) + [0, 0x23] + [0] * 7 + [0xF7], 0)
    check(len(e.out) == 1 and e.out[0][2][4] == 0x40, "the firmware identity query still answered (forwarded to the black box / fwid)")
    print(f"{man.get('marker', '?')} SXPANEL RESULT:", "ALL PASS" if not fails else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(1 if main(Path(a[0]).read_bytes(), json.loads(Path(a[1]).read_text())) else 0)
