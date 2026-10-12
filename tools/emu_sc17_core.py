"""SC17 whole-core DSP session: Master FX master insert wired at P:$274, driven by the ARM tick.

    python tools/emu_sc17_core.py SC16.bin SC17.bin SC17_manifest.json
"""
from __future__ import annotations
import json, math, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R0  # noqa: E402
import build_sc17 as B  # noqa: E402
import masterfx_dsp as G  # noqa: E402

TICK = 0x2000081C


def run(img, man, fx_latch, blocks=24, trace=None):
    s = Session(img)
    if man is not None:
        L = {k: int(v, 16) for k, v in man["report"]["sc17"]["labels"].items()}
        s.e.call(L["c_gfst"]); st = s.e.uc.reg_read(UC_ARM_REG_R0)
        assert st == int(man["report"]["sc17"]["state"], 16), hex(st)
        s.e.uc.mem_write(st + B.S_LATCH, bytes([fx_latch]))
        s.e.w32(TICK, 1000)
        s.capture('fxtick', L["c_fxtick"])
    s.midi(bytes([0x90, 60, 100]))
    # a test signal in the master block cannot be injected (it is computed every block), so feed the
    # line inputs (mixed into the master by stock) with a tone
    ring = []
    for k in range(512):
        v = int(0x300000 * math.sin(2 * math.pi * 440 * k / 48000)) & 0xFFFFFF
        ring += [v, v]
    extra = [('y', 0x1000 + i, v) for i, v in enumerate(ring)]
    wf = tempfile.mktemp()
    res, rans = s.run(blocks=blocks, per_block=False, extra=extra, trace=trace, watchfile=wf,
                      watch=[('x', G.BUF, 64)], dumps=[('x', 0xEB, 0x70), ('x', G.FX_ON, 0x40)])
    outs = []
    cur = []
    for l in open(wf):
        pc, ad, rw, v = l.split()
        if rw == 'W' and ad == 'X:%06x' % G.BUF: cur = []; outs.append(cur)
        if rw == 'W': cur.append(int(v, 16))
    return {(sp, a): v for sp, a, v in res}, rans, s, outs


def main(s16, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    avg = lambda v: sum(v) / len(v)
    t16, t0, t1 = tempfile.mktemp(), tempfile.mktemp(), tempfile.mktemp()
    R16, r16, _, o16 = run(s16, None, 0, trace=t16)
    R0, r0, s0, o0 = run(img, man, 0, trace=t0)
    R1, r1, s1, o1 = run(img, man, 0b111011, trace=t1)          # Gater, AF LP, Digitise, Phaser, Vinyl latched
    check('pc=000113' in r1[1], f"DSP init completes ({r1[1]})")
    check(R0[('x', 0xEB)] == R16[('x', 0xEB)] == R1[('x', 0xEB)], "voice-slot table intact (SC16 / SC17 off / SC17 all on)")
    w = {a: v for _, ws in s1.events for _, sp, a, v in ws if sp == 'x'}
    check(w.get(G.FX_ON) == 0x1F, f"ARM tick wrote FX_ON = all five effects ({hex(w.get(G.FX_ON, -1))})")
    check(R1[('x', G.FX_ON)][0] == 0x1F and R1[('x', G.FX_ON)][G.G_CUR - G.FX_ON] != 0, "DSP sees FX_ON, gater gain state live")
    n = min(len(o0), len(o16))
    check(n > 10 and o0[:n] == o16[:n], f"all Master FX off: master block identical to SC16 ({n} blocks)")
    diff = sum(1 for a, b in zip(o0, o1) if a != b)
    check(diff > n // 2, f"all five on: master block processed ({diff} of {min(len(o0), len(o1))} blocks differ)")
    a16, a1 = open(t16, 'rb').read(), open(t1, 'rb').read()
    extra = [(sp, ad) for sp, o in (('x', 0), ('y', 0x80000)) for ad in range(0x80000) if a1[o + ad] and not a16[o + ad]]
    l3 = "linein3" in man["report"]            # SC17.5: delay / reverb capture buffers Y:$3A80..$3ADF are written every block
    ok_l3 = lambda sp, ad: l3 and sp == 'y' and 0x3A80 <= ad < 0x3AE0
    s18 = "sc18" in man["report"]                # SC18: drum control blocks X:$3A80..$3AFF (envelope / LFO run every block)
    ok_18 = lambda sp, ad: s18 and sp == 'x' and 0x3A80 <= ad < 0x3A80 + 4 * man['report']['sc18'].get('dsp_stride', 32)
    v20 = "vcf20" in man["report"]            # SC20+: the voice blocks X:$3B80..$3BFF (polled / written every block, the register save area)
    ok_v20 = lambda sp, ad: v20 and sp == 'x' and 0x3B80 <= ad < 0x3C00
    bad = [(sp, hex(ad)) for sp, ad in extra if not (sp == 'x' and G.FX_ON <= ad < G.FX_END) and not ok_l3(sp, ad) and not ok_18(sp, ad) and not ok_v20(sp, ad)]
    check(not bad, f"Master FX touches nothing new outside X:$3A40..$3A7F{' (and the SC17.5 capture buffers Y:$3A80..$3ADF)' if l3 else ''} ({len(extra)} new addresses, bad {bad[:8]})")
    i16, i0, i1 = avg(ins(r16)), avg(ins(r0)), avg(ins(r1))
    print(f"     DSP instructions/block: SC16 {i16:.0f}, SC17 off {i0:.0f}, SC17 all five on {i1:.0f}")
    check(i0 - i16 < ((450 if s18 else 350 if l3 else 40) + (300 if v20 else 0)), f"cost when off: +{i0 - i16:.0f} instructions per block")   # SC18.1: drum envelopes run every block
    check(i1 - i16 < 7000, f"cost with all five on: +{i1 - i16:.0f} instructions per block (~{100 * 2 * (i1 - i16) / 166000:.1f}% at ~250 MHz)")
    print("SC17 CORE RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    s16b, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(s16b, im, json.loads(Path(sys.argv[3]).read_text())) else 0)
