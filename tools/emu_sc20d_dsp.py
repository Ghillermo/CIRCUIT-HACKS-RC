"""SC20D DSP tests: the capture meter, whole core 0 on dsptool.

    python tools/emu_sc20d_dsp.py SC19.1.bin SC20D.bin SC20D_manifest.json

As in emu_sc17_5_dsp.py the (silent in emulation) delay / reverb are replaced by routines that write known patterns into Y:$9C0 / Y:$880.  Checks:
  * the capture runs EVERY block (also with no synth in mode 5 / 6): Y:$3A80 / Y:$3AC0 = saturated (L + R) << shift;
  * the meter words Y:$3B00 / Y:$3B01 = sum over the 32 frames of |L + R| (unsaturated, << shift) / 32, limited to 24 bits; Y:$3B02 = 0x5A3C69;
  * the voices of modes 5 / 6 still play the capture (both synths), the other synth is unaffected;
  * the final output blocks (X:$2C02 / X:$2C24) are identical to SC19.1 for modes 0-4: the meter never changes the audio;
  * the only new X/Y accesses are Y:$3A80..$3ADF (capture) and Y:$3B00..$3B02 (meter);
  * cost.
"""
from __future__ import annotations
import gc, json, math, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session  # noqa: E402
import emu_sc17_5_dsp as T5  # noqa: E402
from emu_sc17_5_dsp import DELAY_PAT, REVERB_PAT, SAT_PAT, test_program, run, s24  # noqa: E402


def raw_sum(p, shift, n=32):
    out = []
    for i in range(n):
        l = s24((p[0] + p[2] * i) & 0xFFFFFF); r = s24((p[1] + p[3] * i) & 0xFFFFFF)
        out.append((l + r) << shift)
    return out


def meter_word(p, shift):
    return min(0x7FFFFF, sum(abs(x) >> 5 for x in raw_sum(p, shift)))


def main(s191, img, man):
    shift = man["report"]["linein3"].get("fx_gain_shift", 0)
    T5.SHIFT = shift
    my, mc = [int(x, 16) for x in man["report"]["linein3"]["meter"]], None
    check_y = 0x3B02
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["linein3"]["meter"] == ["0x3b00", "0x3b01"] and shift == 3 and man["report"]["linein3"]["modes"] == 7,
          f"manifest: meter words {man['report']['linein3']['meter']}, capture shift {shift}, 7 modes")
    ring = []
    for k in range(512):
        v = int(0x300000 * math.sin(2 * math.pi * 440 * k / 48000)) & 0xFFFFFF
        ring += [v, v]
    dumps = [('y', 0x3A80, 32), ('y', 0x3AC0, 32), ('y', 0x3B00, 3)]
    for pat in ((DELAY_PAT, REVERB_PAT), (REVERB_PAT, DELAY_PAT), (SAT_PAT, REVERB_PAT), ((0, 0, 0, 0), (0, 0, 0, 0))):
        prog = test_program(img, *pat)
        for modes in ([0, 0], [5, 0]):
            blk, res, rans, wf = run(img, 0, modes, ring, program=prog, dumps=dumps)
            cap = {a: v for sp, a, v in res if sp == 'y'}
            dcap = [s24(x) for x in cap[0x3A80]]; rcap = [s24(x) for x in cap[0x3AC0]]
            T5.SHIFT = shift
            check(dcap == T5.pat_sum(pat[0]) and rcap == T5.pat_sum(pat[1]),
                  f"modes {modes}, patterns {pat[0][0]:06x}/{pat[1][0]:06x}: capture buffers filled (capture runs every block)")
            mw = [x & 0xFFFFFF for x in cap[0x3B00]]
            check(mw[0] == meter_word(pat[0], shift) and mw[1] == meter_word(pat[1], shift) and mw[2] == 0x5A3C69,
                  f"   meter words {mw[0]:06x} / {mw[1]:06x} (expected {meter_word(pat[0], shift):06x} / {meter_word(pat[1], shift):06x}), check constant {mw[2]:06x}")
    # the voices still play the capture
    dsum, rsum = T5.pat_sum(DELAY_PAT), T5.pat_sum(REVERB_PAT)
    for synth in (0, 1):
        for mode, want in ((5, dsum), (6, rsum)):
            prog = test_program(img, DELAY_PAT, REVERB_PAT)
            modes = [0, 0]; modes[synth] = mode
            blk, res, rans, wf = run(img, synth, modes, ring, program=prog)
            worst, n = 0, 0
            for b in blk[-10:]:
                for o, l, x in zip(b['out'], b['lv'], want):
                    worst = max(worst, abs(o - ((x * l) >> 23))); n += 1
            check(n >= 200 and worst <= 2 and any(any(b['out']) for b in blk[-10:]), f"Synth {synth + 1}, mode {mode}: voice mix = capture x noise level ({n} samples, max err {worst})")
            other = [0, 0]; other[1 - synth] = mode
            bo, *_ = run(img, synth, other, ring, program=prog); br, *_ = run(img, synth, [0, 0], ring, program=prog)
            check([b['out'] for b in bo] == [b['out'] for b in br], f"Synth {synth + 1} unaffected when only Synth {2 - synth} uses mode {mode}")
    # the meter never changes the audio: final blocks identical to SC19.1 (modes 0-4)
    out = [(0x2C02, 64), (0x2C24, 64)]
    xs = [('y', 0x1000 + i, v) for i, v in enumerate(ring)]
    def final(image, modes):
        s = Session(image)
        s.midi(bytes([0xB0, 56, 127])); s.midi(bytes([0x90, 60, 100]))
        ex = xs + [('x', 0x52, 0x7F0000), ('x', 0x53, 0x400000), ('x', 0xE3, 0x500000), ('x', 0xE7, 0x500000), ('x', 0xE5, 0x300000)]
        if modes is not None: ex += [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1])]
        res, _ = s.run(blocks=24, per_block=True, extra=ex, dumps=[('x', a, n) for a, n in out] + [('y', 0x800, 64)])
        del s; gc.collect()
        return [(sp, a, v) for sp, a, v in res]
    for modes in (None, [0, 0], [1, 2], [3, 4], [2, 1]):
        a, b = final(s191, modes), final(img, modes)
        check(a == b and any(any(v) for _, _, v in a), f"modes {modes}: final output blocks identical to SC19.1 (24 blocks)")
    # new accesses vs SC19.1
    def new_access(modes):
        t0, t1 = tempfile.mktemp(), tempfile.mktemp()
        run(s191, 0, modes, ring, blocks=24, trace=t0); run(img, 0, modes, ring, blocks=24, trace=t1)
        a0, a1 = open(t0, 'rb').read(), open(t1, 'rb').read()
        return [(sp, ad) for sp, o in (('x', 0), ('y', 0x80000)) for ad in range(0x80000) if a1[o + ad] and not a0[o + ad]]
    for modes in ([0, 0], [5, 0]):
        new = new_access(modes)
        bad = [n for n in new if not (n[0] == 'y' and (0x3A80 <= n[1] < 0x3AE0 or 0x3B00 <= n[1] <= 0x3B02))]
        check(new and not bad, f"modes {modes}: {len(new)} new X/Y accesses vs SC19.1, all in Y:$3A80..$3ADF / Y:$3B00..$3B02 (bad {[(a, hex(b)) for a, b in bad[:6]]})")
    # cost
    def ins(image, modes):
        s = Session(image)
        s.midi(bytes([0xB0, 56, 127])); s.midi(bytes([0x90, 60, 100]))
        ex = [('y', 0x1000 + i, v) for i, v in enumerate(ring)] + [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1])]
        _, rans = s.run(blocks=12, per_block=True, extra=ex)
        n = [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
        del s; gc.collect()
        return sum(n) / len(n)
    i191, i20 = ins(s191, [0, 0]), ins(img, [0, 0])
    check(i20 - i191 < 700, f"cost: +{i20 - i191:.0f} instructions per block with the meter on (SC19.1 {i191:.0f})")
    print("SC20D DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    s191, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(s191, im, json.loads(Path(sys.argv[3]).read_text())) else 0)
