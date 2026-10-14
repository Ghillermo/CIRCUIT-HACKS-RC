"""SC38.1 ARM tests (live RAM dump, the real routes: the pads / knobs of the MIDI 1 Preset view and the granular page, the DSP service tick, the mailbox): the
stretch mode of the granular engine (vcf21.use_stretch).

    python tools/emu_sc38_1.py SC38.1.bin SC38.1_manifest.json SC38.bin SC38_manifest.json
  * MIDI 1 in the granular state, its page: Shift + K6 = note mode 0 / 1 / 2 (stretch), clamped at 2; its LED dim / half / full;
  * in the stretch mode the DSP gets the pitch mode (mailbox 31 = 0), the scan frozen (26 = 0), the smallest zone (28 = -64) and, at every 4 ms slot (HAL & 3 = 1),
    the position s + (126 - s) x p / (6 N), p = the transport's ticks mod 6 N, N = ST_STEPS[(K3 + 64) x 12 / 128]: several ticks, K2 = 0 / 63, K3 = 0 / 63 / -64;
  * K3's LED shows its length (value + 64) in the stretch mode, |value| x 2 out of it;
  * back to the slicer (1): the stored scan / zone / position go to the DSP again; the FX sequencer state: not the stretch mode (c_strm 0);
  * SC38: Shift + K6 stops at 1 (no third mode).
"""
from __future__ import annotations
import gc, json, struct, sys
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc36 as T36  # noqa: E402  (configures vcf21 as SC36)
import vcf21_dsp as VD  # noqa: E402
from emu_sc17_7 import engine_of  # noqa: E402

V, E20 = T36.V, T36.E20
HAL = 0x2000081C


def run(img, man, stretch):
    e = E20(img, man)
    for _ in range(30): e.vtick()
    out = {}
    pad = lambda p: (e.padr(p), e.rel(p))
    def r0(fn, *a): e.call(fn, *a); return e.uc.reg_read(UC_ARM_REG_R0)
    def gval(code, t=0): return struct.unpack("b", bytes([e.r8(r0(e.vl["c_vvaddr"], t, code))]))[0]
    def collect(msgs, got):
        for w, ad in msgs:
            if ad == VD.VB0: got[(w >> 16) & 0x7F] = w & 0xFFFF
        return got
    def mbox(n=30):
        got = {}
        for _ in range(n): collect(e.vtick(), got)
        return got
    def slot():                                                                   # one service tick at HAL & 3 = 1 (the stretch position's slot), then the normal ones
        e.w32(HAL, ((e.r32(HAL) & ~7) + 40) | 1); e.dw.clear(); e.chain.clear(); e.call(e.vl["c_vtick"], maxins=3_000_000)
        got = collect([(x[1], x[2]) for x in e.dw if len(x) == 3], {})
        return collect(sum((e.vtick() for _ in range(6)), []), got)
    def ticks(t):
        st = e.r32(engine_of(img, man, V.ENGINE) + 0x90)
        for b in (e.r32(st + 0xC), e.r32(st + 0x10)): e.w32(b, t)
        return e.r32(r0(V.PARAM_GET, st, 0))
    e.btn(2); e.track(2); e.btn(8)
    for _ in range(3): pad(V.PAD_OSC)
    pad(V.PAD_VEL); pad(V.PAD_OSC); mbox()
    out["sig"] = e.tailb(V.O_SIG)
    pad(1); mbox()                                                                # the page row: OSC1 = the granular page
    e.knob_raw(5, -5, shift=True)
    modes = []
    for _ in range(3): e.knob_raw(5, 1, shift=True); modes.append(gval(26))
    out["modes"] = modes
    if not stretch:
        del e; gc.collect(); return out
    out["lvl26"] = r0(e.vl["c_grlvl"], 0, 13)
    e.knob_raw(1, -200); e.knob_raw(2, -200); e.knob_raw(2, 64)                    # K2 = 0, K3 = 0 (12 steps)
    out["k"] = (gval(19), gval(21)); out["in"] = mbox(); out["strm"] = r0(e.vl["c_strm"], 0)
    fr = e.frame(); out["k3led"] = fr[62]
    pos = []
    for s_, k3, ts in ((0, 0, (0, 18, 36, 71, 72, 100)), (63, 0, (36,)), (63, 63, (100,)), (63, -64, (100,))):
        e.knob_raw(1, -200); e.knob_raw(1, s_); e.knob_raw(2, -200); e.knob_raw(2, k3 + 64); mbox()
        for t in ts:
            tt = ticks(t); g = slot()
            pos.append((s_, gval(21), t, tt, g.get(24)))
    out["pos"] = pos
    e.knob_raw(5, -1, shift=True); out["out"] = mbox()                              # back to the slicer
    out["stored"] = (gval(19), gval(21), gval(23), gval(26))
    fr = e.frame(); out["k3led2"] = fr[62]
    out["lvl26b"] = r0(e.vl["c_grlvl"], 0, 13)
    e.knob_raw(5, 1, shift=True); mbox(); out["strm2"] = r0(e.vl["c_strm"], 0)
    pad(V.PAD_OSC); mbox(); out["strm_fs"] = r0(e.vl["c_strm"], 0)                # the FX sequencer state
    del e; gc.collect()
    return out


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    o = run(img, man, True)
    check(o["sig"] == 0xB4, f"MIDI 1 in the granular state (signature {o['sig']:#x})")
    check(o["modes"] == [1, 2, 2] and o["lvl26"] == 127, f"Shift + K6: note mode 1, 2 (stretch), clamped at 2 {o['modes']}; its LED full ({o['lvl26']})")
    g = o["in"]
    check(o["strm"] == 1 and g.get(31) == 0 and g.get(26) == 0 and g.get(28) == 0xFFC0,
          f"stretch: the DSP gets the pitch mode (31 = {g.get(31)}), the scan frozen (26 = {g.get(26)}), the smallest zone (28 = {g.get(28)})")
    col = V.COL_TRACK[0]
    check(o["k3led"] == ((0 + 64 + 2) << 8 | col), f"K3's LED shows its length (value + 64): {o['k3led']:#x}")
    bad = []
    for s_, k3, t, tt, got in o["pos"]:
        n = V.ST_STEPS[((k3 + 64) * len(V.ST_STEPS)) >> 7] * V.ST_TICKS
        want = s_ + (126 - s_) * (t % n) // n
        if tt != t or got != want: bad.append((s_, k3, t, tt, got, want))
    check(not bad and len(o["pos"]) == 9, f"the position at the 4 ms slot = s + (126 - s) x (ticks mod 6 N) / 6 N for 9 cases (K2 0 / 63, K3 0 / 63 / -64) {bad}")
    s19, s21, s23, s26 = o["stored"]
    g = o["out"]
    check(s26 == 1 and g.get(31) == 1 and g.get(26) == s21 & 0xFFFF and g.get(28) == s23 & 0xFFFF and g.get(24) == s19 & 0xFFFF,
          f"back to the slicer: the stored values go again (31 = {g.get(31)}, 26 = {g.get(26)} / {s21}, 28 = {g.get(28)} / {s23}, 24 = {g.get(24)} / {s19})")
    check(o["k3led2"] == ((min(126, abs(s21) * 2) + 2) << 8 | col) and o["lvl26b"] == 64, f"out of the stretch: K3 bipolar again ({o['k3led2']:#x}), Shift + K6 half ({o['lvl26b']})")
    check(o["strm2"] == 1 and o["strm_fs"] == 0, f"stretch again ({o['strm2']}); the FX sequencer state is not the stretch ({o['strm_fs']})")
    q = run(prev, prev_man, False)
    check(q["modes"] == [1, 1, 1], f"SC38: Shift + K6 stops at 1 {q['modes']}")
    print("SC38.1 ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
