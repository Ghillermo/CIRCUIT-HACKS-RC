"""SC20.1 ARM tests: scale keyboard on three rows, Pitch knob as a note bias in the chromatic view, Clear on the drum knobs of ours.

    python tools/emu_sc20_1.py SC20.bin SC20.1.bin SC20_manifest.json SC20.1_manifest.json
Real routes on the live RAM dump: the knobs through the controller's knob route (0x08033848, emu_sc19.E19), the LED frame through the stock LED task tail (emu_sc19_6.E196),
the pads through the drum Preset view's vtable.
  * scale mode: the pads 1-8 (top row) give no pitch and no LED, the three rows below are the SC20 ones; chromatic: all 32 pads as in SC20;
  * chromatic view: plain K1 = semitone bias (view +0x52) + the stock Pitch write, fine tune (+0x53) untouched; Shift + K1 = fine tune only; the pad adds the bias and clamps to 0..127;
    outside the chromatic view K1 is the stock pitch as before;
  * Clear (the store at [handler + 0x1C], parameter 0): K2 / K4 / K6 / K7 and the Shift layer: right = default value (extended bit kept) + dirty bit + blue LED, left = value kept + red LED;
    Shift + K8 = distortion type back to 0; the LED goes with Clear (released = the normal LEDs); stock-routed knobs: stock Clear (counter 0x28) and its red / blue LED on the right knob;
  * without Clear everything is as in SC20.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc19_6 import E196, MGR, DCODE, level  # noqa: E402
from emu_sc08 import VIEWS, MASKS, model, E8  # noqa: E402
import persist19 as P  # noqa: E402

PARAM_WRITE, STOCK_DEL = 0x08031A98, 0x0803C68C
DP_VT = 0x0805ABBC


class E201(E196):
    def __init__(self, image, man):
        super().__init__(image, man)
        self.log, self.dels = [], []
        for v in VIEWS: self.uc.mem_write(v + 0x51, b"\x00\x00\x00")                # not chromatic, bias 0, fine 0
        def h(uc, a, s, d):
            if a == PARAM_WRITE: self.log.append((uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            else: self.dels.append(uc.reg_read(UC_ARM_REG_R1))
        self.uc.hook_add(UC_HOOK_CODE, h, begin=PARAM_WRITE, end=PARAM_WRITE)
        self.uc.hook_add(UC_HOOK_CODE, h, begin=STOCK_DEL, end=STOCK_DEL)
        self.c_mh = int(man["report"]["sc18"]["labels"]["c_mh"], 16)
    def hd(self, d): self.call(self.c_mh, d); return self.uc.reg_read(UC_ARM_REG_R0)
    def held(self):
        self.call(0x0803542C, self.r32(self.hd(0) + 0x1C), 0); return self.r8(self.uc.reg_read(UC_ARM_REG_R0)) & 1
    def clear(self, on):                                                             # the real route: the Clear button (id 23) pressed / released on the controller
        if bool(self.held()) != on:
            self.call(0x08033320 if on else 0x0803381A, MGR, 23, maxins=600000)
        assert bool(self.held()) == on, "the Clear button does not reach the store at [handler + 0x1C]"
    def turn(self, k, delta, shift=False):
        self.log.clear(); self.dels.clear(); self._knob19(k, delta, shift); return list(self.log)
    def byte(self, d, code): return self.xm(P.XM_DRUMS + 9 * d + code - 1)
    def knobs(self): return self.frame()[60:68]


def main(prev, img, man0, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["marker"] in ("SC20.1", "SC20.2", "SC21", "SC21.1", "SC21.2", "SC21.3", "SC21.4", "SC22", "SC22.1", "SC22.2", "SC22.3", "SC22.4", "SC23", "SC23.1", "SC23.2", "SC23.3", "SC23.4", "SC23.5", "SC23.6", "SC24", "SC25", "SC26", "SC27", "SC28", "SC29", "SC30", "SC31", "SC32", "SC33", "SC34"), f"manifest: marker {man['marker']}")
    labels = {k: int(v, 16) for k, v in man["report"]["sc08"]["labels"].items()}
    # ---- 1) scale keyboard: no top row; chromatic unchanged
    ctx = 0x20060200
    bad = []
    gc.collect(); e = E8(img)
    for si, mask in enumerate(MASKS):
        for root in (0, 5, 11):
            e.set_scale(mask, root); e.call(labels["c_scale"], VIEWS[1], ctx)
            if e.uc.reg_read(UC_ARM_REG_R0): bad.append((si, root, "scale fail")); continue
            chroma = mask == 0
            for pad in range(32):
                e.call(labels["c_padval"], ctx, pad)
                got = (e.uc.reg_read(UC_ARM_REG_R0), e.uc.reg_read(UC_ARM_REG_R1))
                want = model(mask, root, pad)
                if not chroma and pad < 8: want = (0xFF, 0)
                if got != want: bad.append((si, root, pad, got, want))
    check(not bad, f"c_padval, 16 scales x 3 roots x 32 pads: scale mode top row = unused, the rest and the chromatic keyboard as before ({len(bad)} mismatches) {bad[:3]}")
    for flag_mask, name in ((MASKS[1], "scale"), (0, "chromatic")):
        e.set_scale(flag_mask, 0); e.setflag(VIEWS[0], True)
        e.call(0x0804758C, VIEWS[0]); led = e.leds(VIEWS[0])
        top = led[:8]
        check((not any(top)) if name == "scale" else any(top), f"{name} view LEDs: top row {'dark' if name == 'scale' else 'as before'} {[hex(x) for x in top]}")
        if name == "scale": check(all(led[8:]) or any(led[8:]), "scale view: the three lower rows are lit")
    e.set_scale(MASKS[1], 0); e.setflag(VIEWS[0], True)
    hits = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, d: hits.append(a) if a in (PARAM_WRITE, 0x0804E0BA) else None)
    fn = e.r32(DP_VT) & ~1
    e.call(fn, VIEWS[0], 3, 100)
    check(hits == [], f"scale mode, a top-row pad does nothing {hits}")
    e.call(fn, VIEWS[0], 11, 100)
    check(0x0804E0BA in hits, "scale mode, a pad of the second row plays")

    # ---- 2) chromatic view: the Pitch knob
    del e; gc.collect(); n = E201(img, man)
    for d in (0, 2):
        n.sel(d); v = VIEWS[d]
        n.uc.mem_write(v + 0x51, b"\x01\x00\x00")
        w = n.turn(0, 3)
        check(n.r8(v + 0x52) == 3 and n.r8(v + 0x53) == 0 and any(i == 40 + 5 * d for i, _ in w), f"drum {d + 1}, chromatic: K1 +3 = bias {n.r8(v + 0x52)}, fine {n.r8(v + 0x53)}, stock Pitch write {w}")
        w = n.turn(0, 2, True)
        check(n.r8(v + 0x52) == 3 and n.r8(v + 0x53) == 2 and w == [], f"drum {d + 1}, chromatic: Shift + K1 +2 = fine tune {n.r8(v + 0x53)} only, bias {n.r8(v + 0x52)}, stock writes {w}")
        n.uc.mem_write(v + 0x51, b"\x00")
        b0 = n.dval(d, 2)
        w = n.turn(0, 3)
        check(n.r8(v + 0x52) == 3 and any(i == 40 + 5 * d for i, _ in w), f"drum {d + 1}, not chromatic: K1 = the stock pitch ({w}), the bias is left alone")
        n.uc.mem_write(v + 0x51, b"\x00\x00\x00")
    # pads with the bias, clamped 0..127
    e = n; v = VIEWS[1]
    for bias, pad, root in ((5, 12, 0), (-20, 12, 0), (60, 12, 0), (-60, 28, 0), (63, 0 + 8, 11), (-64, 31, 0)):
        for mask in (MASKS[1], 0):
            e.set_scale(mask, root); e.uc.mem_write(v + 0x51, b"\x01"); e.uc.mem_write(v + 0x52, bytes([bias & 0xFF]))
            e.log.clear(); e.call(e.r32(DP_VT) & ~1, v, pad, 100)
            pv = model(mask, root, pad)[0]
            want = None if pv == 0xFF or (mask and pad < 8) and False else max(0, min(127, pv + bias))
            if mask != 0 and pad < 8: want = None
            got = [x for i, x in e.log if i == 45]
            check((got == [] and want is None) or got == [want], f"bias {bias:+d}, pad {pad}, {'scale' if mask else 'chromatic'}: Pitch {got} (want {want}; bare {pv})")

    # ---- 3) Clear on the knobs of ours
    d = 1; n.sel(d); v = VIEWS[d]
    DEF = P.REMAP_PLAIN
    mh = n.hd(d)
    for k, code in sorted(P.REMAP_PLAIN.items()):                       # K2 / K4 / K6 / K7 (ring mod freq, env -> cutoff, resonance, LFO amount)
        n.setcode(d, code, 0x40 + 9 if code in (2, 5, 6, 3) else 0)
        n.clear(False)
        n.setcode(d, code, (n.byte(d, code) & 0x80) | 37)
        n.clear(True)
        before = n.byte(d, code); flags = n.r8(mh + 0x3E) | (n.r8(mh + 0x3F) & 7) << 8
        w = n.turn(k, -4)
        kn = n.knobs()
        check(w == [] and n.byte(d, code) == before and kn[k] == 0x53, f"Clear + K{k + 1} left: value {before} kept, no stock write {w}, red LED {kn[k]:#x}")
        w = n.turn(k, 2)
        kn = n.knobs()
        check(w == [] and n.byte(d, code) == 0 and kn[k] == 0x46 and all(kn[j] != 0x46 for j in range(8) if j != k), f"Clear + K{k + 1} right: value {n.byte(d, code)} = default, blue LED {kn[k]:#x}, no stock write {w}")
        check(n.r8(mh + 0x3E) & 0x7F != 0 or n.r8(mh + 0x3F) & 7 != 0, f"Clear + K{k + 1} right: the DSP update is queued ({n.r8(mh + 0x3E):#x}, {n.r8(mh + 0x3F):#x})")
        n.clear(False)
        kn = n.knobs()
        check(kn[k] not in (0x53, 0x46) and n.r8(mh + 0x3F) & 0xF8 == 0, f"Clear released: the knob {k + 1} LED is normal again ({kn[k]:#x}), LED bits {n.r8(mh + 0x3F):#x}")
        for oc in range(1, 10):                                                      # the other codes hold their own values: a turn must read and change only its own
            if oc != code: n.setcode(d, oc, (n.byte(d, oc) & 0x80) | 11)
        others = [n.byte(d, oc) for oc in range(1, 10) if oc != code]
        n.turn(k, 3)
        check(others == [n.byte(d, oc) for oc in range(1, 10) if oc != code], f"without Clear a turn of K{k + 1} changes only code {code}")
        check(n.byte(d, code) & 0x7F == 3, f"without Clear K{k + 1} turns normally again (default 0 + 3 = {n.byte(d, code) & 0x7F})")
    # Shift layer (ring mod amount = code 8 on K2; filter mode on K5 = code 9; LFO speed K7 = code 4)
    for k, code in ((1, 8), (3, 7), (6, 4), (4, 9)):
        n.clear(False); n.set_p0(n.r32(MGR + 0xC), 0)
        n.setcode(d, code, (n.byte(d, code) & 0x80) | (3 if code == 9 else 21))
        n.clear(True); n.set_p0(n.r32(MGR + 0xC), 1)
        w = n.turn(k, 2, True)
        kn = n.knobs()
        mask_ = 0xF8 if code == 9 else 0x80
        check(w == [] and (n.byte(d, code) & ~mask_ & 0xFF) == 0 and kn[k] == 0x46, f"Clear + Shift + K{k + 1} right (code {code}): default {n.byte(d, code)}, blue LED {kn[k]:#x}")
        n.set_p0(n.r32(MGR + 0xC), 0); n.clear(False)
    # distortion type
    n.clear(False); n.set_p0(n.r32(MGR + 0xC), 1)
    n.turn(7, 1, True); n.turn(7, 1, True)
    print("     distortion type bits:", [n.xm(i) for i, m in P.XT_BITS[3:6]])
    n.clear(True)
    n.turn(7, 1, True)
    kn = n.knobs()
    xt_zero = all((n.xm(i) & m) == 0 for i, m in P.XT_BITS[3:6])
    check(xt_zero and kn[7] == 0x46, f"Clear + Shift + K8 right: the distortion type is 0, blue LED {kn[7]:#x}")
    n.turn(7, -1, True); kn = n.knobs()
    check(kn[7] == 0x53, f"Clear + Shift + K8 left: red LED {kn[7]:#x}")
    n.set_p0(n.r32(MGR + 0xC), 0); n.clear(False)

    # ---- 4) stock-routed knobs keep the stock Clear (40 steps), LED on the right knob
    for k, s, sb, pos in ((0, 1, 0, 0), (2, 3, 1, 2), (4, 7, 3, 4), (7, 5, 2, 7)):
        n.clear(False); n.turn(k, 0); n.clear(True)
        for _ in range(39): n.turn(k, -1)
        kn = n.knobs()
        ok39 = kn[pos] != 0x53
        w = n.turn(k, -1)
        kn = n.knobs()
        check(ok39 and n.r8(mh + 0x36 + sb) == 0x28 and kn[pos] == 0x53 and bool(n.dels), f"Clear + K{k + 1} (stock macro {sb}) left x40: stock Clear done (counter {n.r8(mh + 0x36 + sb):#x}, delete called {len(n.dels)}x), red LED on K{k + 1}: {kn[pos]:#x}")
        for _ in range(40): n.turn(k, 1)
        kn = n.knobs()
        check(n.r8(mh + 0x3A + sb) == 0x28 and kn[pos] == 0x46, f"Clear + K{k + 1} right x40: default (counter {n.r8(mh + 0x3A + sb):#x}), blue LED {kn[pos]:#x}")
        n.clear(False); n.knobs()
        kn = n.knobs()
        check(kn[pos] not in (0x53, 0x46), f"Clear released: K{k + 1} LED normal ({kn[pos]:#x})")

    print("SC20.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
