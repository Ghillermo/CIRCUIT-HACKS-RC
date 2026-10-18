"""SC44.3 DSP test (vcf21_dsp.use_lfoshape2: the own engine's LFO shape 6 = slewed sample & hold), on emu_sc43_9_dsp's harness:

    python tools/emu_sc44_3_dsp.py SC44.3.bin SC44.3_manifest.json SC44.2.bin SC44.2_manifest.json

  * the engine's traffic of the ARM side (both tracks, every page, notes, the VA-drum and the granular engines) run on the whole core 0 of both
    builds: X and Y 0..$3FFF the same at four points (shape 0);
  * shapes 1-5 against emu_sc43_9_dsp's models (saw, triangle, square, sine, sample & hold);
  * shape 6, MIDI 1's LFO rate at 127: at every wrap of the phase the old value goes to OSC1 + 26 and the noise generator (OSC1 + 24) gives a new
    one; every block LV = prev + (new - prev) x (p + 1) / 2 in the DSP's fixed point (the model: y0 = (new - prev) / 2, x0 = p / 2 + 1/2,
    LV = prev + (4 y0 x0 >> 24), limited): a glide that ends near the new value when the next wrap comes.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emu_sc43_9_dsp as M  # noqa: E402

OSC1 = 0x3900
PH, LV = 0x3B80 + 25, 0x3B80 + 26


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sched = M.schedule(prev, pman)
    check(sum(len(x) for x in sched) > 100, f"the engine's traffic: {len(sched)} ticks")
    Rn, _ = M.dsp_run(img, sched); gc.collect()
    Rp, _ = M.dsp_run(prev, sched); gc.collect()
    check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{len(Rn)} / {len(Rp)} dumps")
    for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
        diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
        check(sn == sp_ and not diff, f"block {M.CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF the same as the previous build ({len(diff)} differences: {[hex(i) for i in diff[:8]]})")
    M.shape_tests(img, sched, check)
    # shape 6: slewed sample & hold
    R, _ = M.dsp_run(img, sched, blocks=450, checks=(), every=((PH, 2), (OSC1 + 24, 3)), shape=6, force=((0x3B80 + 12, 127),)); gc.collect()
    ph = [(M.s24(v[0]), M.s24(v[1])) for sp_, a_, v in R if sp_ == 'x' and a_ == PH]
    st = [(M.s24(v[0]), M.s24(v[2])) for sp_, a_, v in R if sp_ == 'x' and a_ == OSC1 + 24]       # (the new value, prev)
    rows = list(zip(ph, st))
    on = next((k for k, ((p, lv), _) in enumerate(rows) if p or lv), len(rows)); rows = rows[on:]
    bad = wraps = glides = 0
    for k, ((p, lv), (t, pv)) in enumerate(rows):
        if k and rows[k - 1][0][0] >= 0 and p < 0:
            wraps += 1
            if pv != rows[k - 1][1][0] or t == rows[k - 1][1][0]: bad += 1                         # prev = the old value, a new one
        y0 = (t - pv) >> 1; x0 = (p >> 1) + 0x400000                                            # (the halves' low bits stay in the accumulators: the half of the difference)
        want = M.lim(pv + ((4 * y0 * x0) >> 24))
        if lv != want: bad += 1
        if k and rows[k - 1][0][0] < p and lv != rows[k - 1][0][1]: glides += 1                     # inside a cycle: LV moves
    check(wraps >= 2 and glides > 50 and not bad and len(rows) > 100,
          f"LFO shape 6 (slewed sample & hold): LV as the model in {len(rows) - bad} / {len(rows)} blocks, {wraps} wraps, {glides} blocks gliding")
    print("SC44.3 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
