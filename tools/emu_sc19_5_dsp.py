"""SC19.5 DSP tests: the Setup's FX returns reach the synth's line inputs (linein3.SETUP_RET), whole core 0 on dsptool.

    python tools/emu_sc19_5_dsp.py SC19.4.bin SC19.5.bin SC19.5_manifest.json

As in emu_sc17_5_dsp.py the (silent in emulation) delay / reverb are replaced by routines that write known patterns into Y:$9C0 / Y:$880.  X:$3A00 is the Setup's
FX-return flag word (bit 0: reverb -> strip 3 = audio in 1, bit 1: delay -> strip 4 = audio in 2), X:$3A01 / X:$3A02 the synth source modes.
  * flag bit 0: modes 1 / 3 (input 1 / inverted) play the reverb capture / its negation; modes 2 / 4 still read the line input;
  * flag bit 1: modes 2 / 4 play the delay capture / its negation; modes 1 / 3 still read the line input;
  * both: all four; no flag: modes 0-4 identical to SC19.4 (the same ring), modes 5 / 6 (not offered by the UI) still served;
  * the capture runs although no synth uses a return mode (only the flag is on);
  * the other synth is unaffected; cost.
"""
from __future__ import annotations
import gc, json, math, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session  # noqa: E402
import emu_sc17_5_dsp as T5  # noqa: E402
from emu_sc17_5_dsp import DELAY_PAT, REVERB_PAT, test_program, s24  # noqa: E402


def run2(img, synth, modes, flag, ring, program, blocks=30):
    s = Session(img)
    s.midi(bytes([0xB0 | synth, 56, 127])); s.midi(bytes([0x90 | synth, 60, 100]))
    extra = [('y', 0x1000 + i, v) for i, v in enumerate(ring)] + [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1]), ('x', 0x3A00, flag)]
    wf = tempfile.mktemp()
    res, rans = s.run(blocks=blocks, per_block=False, extra=extra, watchfile=wf, program=program,
                      watch=[('x', 0x2c46, 32), ('x', 0x1400, 6 * 32), ('y', 0xffd, 1)])
    del s; gc.collect()
    blk, cur = [], None
    for l in open(wf):
        pc, ad, rw, v = l.split(); a = int(ad[2:], 16); v = s24(int(v, 16))
        if pc == '0009ac' and rw == 'W' and a == 0x1405:
            cur = dict(lv=[], out=[]); blk.append(cur)
        if cur is None: continue
        if pc == '0009ac' and rw == 'W' and (a - 0x1400) % 6 == 5: cur['lv'].append(v)
        if pc == '0009c6' and rw == 'W' and 0x2c46 <= a < 0x2c66: cur['out'].append(v)
    return blk, rans


def neg(v): return max(-0x800000, min(0x7FFFFF, -v))


def main(s194, img, man):
    shift = man["report"]["linein3"].get("fx_gain_shift", 0)
    T5.SHIFT = shift
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    check(man["report"]["linein3"].get("setup_ret") == "0x3a00" and man["report"]["linein3"]["modes"] == 5, f"manifest: setup_ret {man['report']['linein3'].get('setup_ret')}, modes {man['report']['linein3']['modes']}")
    ring = []
    for k in range(512):
        v = int(0x300000 * math.sin(2 * math.pi * 440 * k / 48000)) & 0xFFFFFF
        ring += [v, (-v // 2) & 0xFFFFFF]
    dcap, rcap = T5.pat_sum(DELAY_PAT), T5.pat_sum(REVERB_PAT)
    prog = test_program(img, DELAY_PAT, REVERB_PAT)
    def outs(b): return [x['out'] for x in b]
    def match(blk, want):
        worst, n = 0, 0
        for b in blk[-10:]:
            for o, l, x in zip(b['out'], b['lv'], want):
                worst = max(worst, abs(o - ((x * l) >> 23))); n += 1
        return n >= 200 and worst <= 2 and any(any(b['out']) for b in blk[-10:]), n, worst
    for synth in (0, 1):
        base = {}
        for mode in (1, 2, 3, 4):
            modes = [0, 0]; modes[synth] = mode
            base[mode], _ = run2(img, synth, modes, 0, ring, prog)
        for flag, wants in ((1, {1: rcap, 3: [neg(v) for v in rcap]}), (2, {2: dcap, 4: [neg(v) for v in dcap]}),
                            (3, {1: rcap, 2: dcap, 3: [neg(v) for v in rcap], 4: [neg(v) for v in dcap]})):
            for mode in (1, 2, 3, 4):
                modes = [0, 0]; modes[synth] = mode
                blk, _ = run2(img, synth, modes, flag, ring, prog)
                if mode in wants:
                    ok, n, worst = match(blk, wants[mode])
                    name = {1: "reverb return", 3: "reverb return inverted", 2: "delay return", 4: "delay return inverted"}[mode]
                    check(ok, f"Synth {synth + 1}, flag {flag}, mode {mode}: plays the {name} x noise level ({n} samples, max err {worst})")
                else:
                    check(outs(blk) == outs(base[mode]), f"Synth {synth + 1}, flag {flag}, mode {mode}: still the line input (identical to flag 0)")
        other = [0, 0]; other[1 - synth] = 1
        bo, _ = run2(img, synth, other, 3, ring, prog); br, _ = run2(img, synth, [0, 0], 3, ring, prog)
        check(outs(bo) == outs(br), f"Synth {synth + 1} unaffected when only Synth {2 - synth} reads input 1 with both flags on")
    # no flag: modes 0-4 identical to SC19.4 (modes 5 / 6 differ by the capture gain x8; they must still play)
    p4 = test_program(s194, DELAY_PAT, REVERB_PAT)
    bad = []
    for mode in range(7):
        a, _ = run2(s194, 0, [mode, 0], 0, ring, p4); b, _ = run2(img, 0, [mode, 0], 0, ring, prog)
        if not any(any(x['out']) for x in b) or (mode < 5 and outs(a) != outs(b)): bad.append(mode)
    check(not bad, f"flag 0: modes 0..4 identical to SC19.4, modes 5 / 6 still play (the same ring and patterns) {bad}")
    # cost
    def ins(image, modes, flag):
        s = Session(image)
        s.midi(bytes([0xB0, 56, 127])); s.midi(bytes([0x90, 60, 100]))
        ex = [('y', 0x1000 + i, v) for i, v in enumerate(ring)] + [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1]), ('x', 0x3A00, flag)]
        _, rans = s.run(blocks=12, per_block=True, extra=ex)
        n = [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
        del s; gc.collect()
        return sum(n) / len(n)
    i5, i6, i6on = ins(s194, [1, 0], 0), ins(img, [1, 0], 0), ins(img, [1, 0], 1)
    check(i6 - i5 < 60 + (250 if "vcf20" in man["report"] else 0), f"cost with the flags off: +{i6 - i5:.0f} instructions per block (SC19.4 {i5:.0f})")
    print(f"     flag on, mode 1 (capture + inverted copy path not used): +{i6on - i5:.0f} instructions per block")
    print("SC19.5 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    s194, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(s194, im, json.loads(Path(sys.argv[3]).read_text())) else 0)
