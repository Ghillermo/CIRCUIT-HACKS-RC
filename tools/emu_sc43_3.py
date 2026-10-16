"""SC43.3 ARM tests (the user, 2026-10-16, a MIDI track in a fresh project: «Set centre for bipolar parameters and 0 for unipolar, both with dimmer =
no modulation, brighter = positive or negative modulation»), through the controller and the real LED task, MIDI 1 with its own engine:
  * page 1, the destination pitch (bipolar): an empty pair = 64, its LED dim (brightness 2); knob 1 +5 / -10 = 69 / 59, brightness 2 + 2 x 5;
  * page 1, FM (unipolar): an empty pair = 0, dim; knob 2 +5 = 5, brightness 2 + 5; the pair at 69 now 2 + 69; c_sdfx adds the value (40 + 5,
    40 + 69);
  * page 2, WAVE (unipolar): empty = 0, knob 1 +5 = 5, its LED WAVE's colour at 2 + 5; OSC 2 pitch (bipolar): empty = 64, knob 2 +5 = 69 at 2 + 10;
  * the pitch-vel toggle: the transposition counts from the point (FM: 5 -> 1 degree, 16 -> 2; pitch: 69 -> 1, 59 -> -1).

    python tools/emu_sc43_3.py SC43.3.bin SC43.3_manifest.json
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc42_6 as X  # noqa: E402
import vcf21 as V  # noqa: E402

MGR = X.MGR


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    s32 = lambda x: x - (1 << 32) if x >= 1 << 31 else x
    e = X.EP(img, man)
    e.btn(2); e.btn(8)
    for _ in range(2): e.pad(26)                                                      # the oscillator engine
    e.pad(29)                                                                         # the step-drummer view
    h0 = e.r0(e.vl["c_sdhalf"], 0)
    br = lambda f, k: f[60 + k] >> 8
    f = X.frame(e)
    check(e.r0(e.vl["c_sdbase"], 0) == 64 and all(br(f, k) == 2 for k in range(8)), f"page 1, pitch (bipolar): empty = 64, LEDs dim ({[br(f, k) for k in range(8)]})")
    e.knob(0, 5); f = X.frame(e); a = (e.lane(0, h0, 0), br(f, 0))
    e.knob(0, -10); f = X.frame(e); b_ = (e.lane(0, h0, 0), br(f, 0))
    check(a == (69, 12) and b_ == (59, 12), f"knob 1 +5 / -10: 69 / 59, brightness 2 + 2 x 5 ({a}, {b_})")
    e.knob(0, 10)                                                                     # back to 69
    e.pad(19)                                                                         # pad 20: FM
    f = X.frame(e)
    check(e.r0(e.vl["c_sdbase"], 0) == 0 and br(f, 1) == 2 and br(f, 0) == 2 + 69, f"page 1, FM (unipolar): empty = 0 and dim ({br(f, 1)}), the pair at 69 = {br(f, 0)}")
    e.knob(1, 5); f = X.frame(e)
    check(e.lane(0, h0 + 2, 0) == 5 and br(f, 1) == 7, f"knob 2 +5 from 0: 5, brightness 7 ({e.lane(0, h0 + 2, 0)}, {br(f, 1)})")
    gf = e.r0(int(man["report"]["sc17"]["labels"]["c_gfst"], 16))
    fx = []
    for st in (h0 + 2, h0):
        e.uc.mem_write(gf + V.SD_AUD, bytes([st + 1])); fx.append(e.r1(e.vl["c_sdfx"], 0, 40, 32))
    check(fx == [45, 109], f"c_sdfx, FM stored 40: + the value (45, 109) = {fx}")
    # page 2
    e.btn(19); e.pad(18)                                                              # page 2 -> WAVE
    pl = e.pl
    check(e.r0(pl["c_pvbase2"], 0, 2) == 0 and e.r0(pl["c_pvbase2"], 0, 1) == 64, "page 2: WAVE's point 0, OSC 2 pitch's 64")
    e.knob(0, 5); f = X.frame(e)
    check(e.lane(0, h0, 192) == 5 and f[60] == V.SD_DCOL[2] | (5 + 2) << 8, f"page 2, WAVE, knob 1 +5: 5 at brightness 7 ({e.lane(0, h0, 192)}, {f[60]:#x})")
    e.pad(17); e.knob(1, 5); f = X.frame(e)                                           # OSC 2 pitch
    check(e.lane(0, h0 + 2, 192) == 69 and f[61] == V.SD_DCOL[1] | (10 + 2) << 8 and f[60] == V.SD_DCOL[1] | (2 * 59 + 2) << 8,
          f"page 2, OSC 2 pitch: knob 2 from 64 (+5 = {e.lane(0, h0 + 2, 192)}) at 12 ({f[61]:#x}); the pair at 5 = 59 from the centre ({f[60]:#x})")
    e.uc.mem_write(gf + V.SD_AUD, bytes([h0 + 2 + 1])); o2 = s32(e.r0(pl["c_pvoff2"], 0))
    check(o2 == 5, f"page 2's offset = value - 64 for a bipolar destination ({o2})")
    # the pitch-vel toggle
    e.btn(20); e.pad(31)
    pat = e.r0(e.vl["c_sdpat"], 0); lane = lambda st: e.r0(e.vl["c_sdlna"], pat, st)
    ks = []
    for v in (5, 16):
        e.uc.mem_write(lane(h0 + 4), bytes([v] * 6)); ks.append(s32(e.r0(pl["c_pvk"], 0, h0 + 4)))
    e.pad(16)                                                                         # page 1 -> pitch (bipolar)
    for v in (69, 59):
        e.uc.mem_write(lane(h0 + 4), bytes([v] * 6)); ks.append(s32(e.r0(pl["c_pvk"], 0, h0 + 4)))
    check(ks == [1, 2, 1, -1], f"the toggle: degrees from the point (FM 5 / 16, pitch 69 / 59) = {ks}")
    del e; gc.collect()
    print(f"{man.get('marker', '?')} ARM RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text())) else 0)
