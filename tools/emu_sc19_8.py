"""SC19.8 ARM tests: the drum knobs follow the panel labels (persist19.REMAP), through the controller's knob route (0x08033848).

    python tools/emu_sc19_8.py SC19.7.bin SC19.8.bin SC19.7_manifest.json SC19.8_manifest.json
K1 pitch, K2 osc mod (ring mod freq / amount), K3 amp envelope (decay), K4 filter envelope (env -> cutoff / env shape), K5 filter frequency (EQ / filter mode),
K6 resonance, K7 modulation (LFO amount / speed), K8 FX (distortion).  The stock ones are called with the stock knob index, so their parameter writes (the argument pairs of
0x08031A98 = what the MIDI follows) must be exactly those the SC19.7 knob of the same parameter gives; ours change only their own saved byte.
  * stock-driven knobs: identical parameter writes to the old knob (pitch old K2, decay old K4, EQ old K8, distortion old K6), no saved byte of ours changes;
  * ours: the saved byte of the expected code changes (+3), nothing else (no stock write, no other code);  Shift + K6: nothing at all;
  * the K3 / K8 extended values (start point / bitcrush) count as the old K4 / K6 did;
  * the LED of every position: stock dynamic codes moved with their parameter, ours = drum colour + brightness of their value (Shift layers).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_6 import E196, MGR, DCODE, level, PLAIN as _P  # noqa: E402
from emu_sc08 import VIEWS  # noqa: E402
import persist19 as P  # noqa: E402

PARAM_WRITE = 0x08031A98
STOCK_OLD = {0: 1, 2: 3, 4: 7, 7: 5}            # new physical knob -> old physical knob of the same stock parameter


class EW(E196):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.log = []
        for v in VIEWS: self.uc.mem_write(v + 0x51, b"\x00")                        # not chromatic (see the chromatic test)
        def h(uc, a, s, d): self.log.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PARAM_WRITE, end=PARAM_WRITE)
    def knob19(self, k, delta, shift=False): self._knob19(k, delta, shift)         # physical knobs: no SC19.7-layout translation (emu_sc19.E19 does that for its own tests)
    def turn(self, k, delta, shift=False):
        self.log.clear(); self.knob19(k, delta, shift); return list(self.log)
    def codes(self, d): return [self.dval(d, c) if c != 9 else self.xm(P.XM_DRUMS + 9 * d + 8) & 7 for c in range(1, 10)]


def main(prev, img, man7, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    rep = man["report"]["persist19"]
    check(rep.get("remap") is True and not man7["report"]["persist19"].get("remap"), "manifest: remap on (SC19.8), off in SC19.7")
    gc.collect(); n = EW(img, man); gc.collect(); o = EW(prev, man7)
    for d in (0, 1, 3):
        n.sel(d); o.sel(d)
        for k in range(8):
            for shift in (False, True):
                base = n.codes(d)
                w = n.turn(k, 3, shift)
                after = n.codes(d)
                chg = [i + 1 for i in range(9) if after[i] != base[i]]
                if not shift and k in P.REMAP_PLAIN_STOCK or shift and k in P.REMAP_SHIFT_STOCK:
                    s = P.REMAP_PLAIN_STOCK[k] if not shift else P.REMAP_SHIFT_STOCK[k]
                    ow = o.turn(s, 3, shift)
                    check(w == ow and chg == [], f"drum {d + 1}, K{k + 1}{' + Shift' if shift else ''}: the stock parameter of old K{s + 1} (writes {w} = {ow}), none of ours {chg}")
                else:
                    code = (P.REMAP_SHIFT if shift else P.REMAP_PLAIN).get(k)
                    want = [] if code is None else [code]
                    check(w == [] and chg == want, f"drum {d + 1}, K{k + 1}{' + Shift' if shift else ''}: code {code} only (changed {chg}, stock writes {w})")
    # ---- chromatic drum view: Shift + K1 is the stock pitch knob (semitone bias) as Shift + K2 was; outside it, the pitch envelope
    for d in range(4):
        for x in (n, o): x.sel(d); x.uc.mem_write(VIEWS[d] + 0x51, b"\x01")
        w, ow = n.turn(0, 3, True), o.turn(1, 3, True)
        check(w == ow and n.codes(d)[0] == 0 or w == ow, f"drum {d + 1}, chromatic view: Shift + K1 = the stock pitch knob with Shift ({w} = {ow})")
        for x in (n, o): x.uc.mem_write(VIEWS[d] + 0x51, b"\x00")
    # ---- extended values: K3 (decay) counts the start point, K8 (distortion) the bitcrush, as the old K4 / K6
    for k, s, nib in ((2, 3, 0), (7, 5, 4)):
        n.sel(1); o.sel(1)
        for _ in range(140): n.knob19(k, -1); o.knob19(s, -1)
        for _ in range(5): n.knob19(k, -1); o.knob19(s, -1)
        check(n.dext(1) == o.dext(1) and (n.dext(1) >> nib) & 15 > 0, f"K{k + 1} to the left past 0: extended value {(n.dext(1) >> nib) & 15} = the old K{s + 1}'s {(o.dext(1) >> nib) & 15}")
        for _ in range(5): n.knob19(k, 1); o.knob19(s, 1)
        check(n.dext(1) == o.dext(1), f"K{k + 1} to the right: back to {n.dext(1):#x} as old K{s + 1}")
    # ---- LEDs
    for d in range(4):
        n.track(4 + d); o.track(4 + d)
        for q in range(8):
            for i in range(9): n.setcode(d, i + 1, 0)
        n.setcode(d, 2, 100); n.setcode(d, 5, 0x6C); n.setcode(d, 6, 0x20); n.setcode(d, 3, 0x7B); n.setcode(d, 1, 0x14); n.setcode(d, 8, 0x30); n.setcode(d, 7, 0x1E); n.setcode(d, 4, 0x08); n.setcode(d, 9, 3)
        fo = o.frame()
        for shift in (False, True):
            if shift: n.set_p0(n.r32(MGR + 0xC), 1)
            fn = n.frame(); fn2 = n.frame()
            check(fn == fn2, f"drum {d + 1}{', Shift' if shift else ''}: a second frame gives the same LEDs (the LED buffer is persistent)")
            if shift: n.set_p0(n.r32(MGR + 0xC), 0)
            kn = fn[60:68]
            stock = {0: fo[61], 2: fo[63], 7: fo[65], 4: fo[67]}              # pitch, decay, distortion, EQ of the old layout
            stock = {0: fo[61], 2: fo[63], 4: fo[67], 7: fo[65]}
            codes = {}
            for pos, pc, sc in P.REMAP_LEDS:
                c = sc if shift else pc
                if c is not None: codes[pos] = DCODE[d] | ((level(c, [0, 0x14, 100, 0x7B, 0x08, 0x6C, 0x20, 0x1E, 0x30, 3][c] if c != 9 else 3) + 2) << 8)
            colour = {1, 3, 5, 6}
            ok = True
            for pos in range(8):
                if pos in codes: ok &= kn[pos] == codes[pos]
                elif pos in stock: ok &= kn[pos] == stock[pos]
                else: ok &= (kn[pos] & 0xFF) == DCODE[d]
            check(ok, f"drum {d + 1}{', Shift' if shift else ''}: knob LEDs {[hex(x) for x in kn]} (stock codes moved with their parameter, ours = colour + brightness)")
    print("SC19.8 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
