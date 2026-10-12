"""SC17.5 DSP tests: delay / reverb returns as the synth noise source (modes 5 / 6), whole core 0 on dsptool.

    python tools/emu_sc17_5_dsp.py SC17.4.bin SC17.5.bin SC17.5_manifest.json

The emulated delay / reverb output is silent (their delay lines live in external memory), so the effects are
replaced for the test by routines that write known patterns into Y:$9C0 (delay output) and Y:$880 (reverb output)
exactly where the real ones leave their result.  Checks:
  * capture buffers Y:$3A80 / Y:$3AC0 = saturated L + R of those outputs (every block);
  * voice mix in mode 5 / 6 = capture x noise level (both synths), the other synth unchanged;
  * modes 0-4 and the final output block (X:$2C02 / X:$2C24) identical to SC17.4 when 5 / 6 are not selected;
  * the capture runs only while a synth uses mode 5 / 6 (no new X/Y access otherwise) and then touches only Y:$3A80..$3ADF.
"""
from __future__ import annotations
import gc, json, math, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session, dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import dsp56 as D  # noqa: E402

T = G.T
REVERB_CALL = 0xD1F                # jsr func_001964 (reverb), right before SC10's `jsr int_00009f`
FILL_AT = 0x2F80                   # free program words (CODE_P_END = $3000)
DELAY_PAT = (0x080000, 0x040000, 0x001000, 0x000400)     # L0, R0, dL, dR     (mono sum L+R)
REVERB_PAT = (0x020000, 0xFF0000, 0x000800, 0xFFFE00)    # R negative
SAT_PAT = (0x600000, 0x400000, 0x000000, 0x000000)       # sum > full scale -> saturates


def s24(v): return v - (1 << 24) if v & 0x800000 else v


SHIFT = 0                          # linein3.FX_GAIN_SHIFT of the image under test (manifest)


def pat_sum(p, n=32):
    out = []
    for i in range(n):
        l = s24((p[0] + p[2] * i) & 0xFFFFFF); r = s24((p[1] + p[3] * i) & 0xFFFFFF)
        out.append(max(-0x800000, min(0x7FFFFF, (l + r) << SHIFT)))
    return out


def fill_code(base, dpat, rpat):
    a = D.Asm(base)
    for dest, p, lab in ((0x9C0, dpat, "tf1"), (0x880, rpat, "tf2")):
        a.emit(T("move #>$%x,r0" % dest))
        a.emit(T("move #>$%06x,a" % p[0])); a.emit(T("move #>$%06x,b" % p[1]))
        a.emit(T("move #>$%06x,x0" % p[2])); a.emit(T("move #>$%06x,x1" % p[3]))
        a.emit(D.do_x, 0x3A, lab)
        a.emit(T("move a,y:(r0)+")); a.emit(T("move b,y:(r0)+")); a.emit(T("add x0,a"))
        a.label(lab); a.emit(T("add x1,b"))
    a.emit(D.RTS)
    return a.assemble()[0]


def test_program(img, dpat, rpat):
    prog = bytearray(dsp_program(img))
    at = max(FILL_AT, len(prog) // 3 + 0x10)            # SC18's program goes past $2F80
    prog += b"\0" * (3 * at - len(prog))
    words = fill_code(at, dpat, rpat)
    prog += D.to_bytes(words)
    o = 3 * REVERB_CALL
    assert int.from_bytes(prog[o:o + 3], 'big') == 0x0BF080 and int.from_bytes(prog[o + 3:o + 6], 'big') == 0x1964
    prog[o + 3:o + 6] = at.to_bytes(3, 'big')
    return bytes(prog)


def run(img, synth, modes, ring, blocks=30, program=None, watch_extra=(), dumps=(), trace=None):
    s = Session(img)
    s.midi(bytes([0xB0 | synth, 56, 127])); s.midi(bytes([0x90 | synth, 60, 100]))
    extra = [('y', 0x1000 + i, v) for i, v in enumerate(ring)]
    if modes is not None: extra += [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1])]
    wf = tempfile.mktemp()
    res, rans = s.run(blocks=blocks, per_block=False, extra=extra, watchfile=wf, program=program, trace=trace, dumps=list(dumps),
                      watch=[('x', 0x2c46, 32), ('x', 0x1400, 6 * 32), ('y', 0xffd, 1)] + list(watch_extra))
    del s; gc.collect()                                  # every Session maps ~0.5 GB: free it (Windows runs out otherwise)
    blk, cur = [], None
    for l in open(wf):
        pc, ad, rw, v = l.split(); a = int(ad[2:], 16); v = s24(int(v, 16))
        if pc == '0009ac' and rw == 'W' and a == 0x1405:
            cur = dict(lv=[], out=[]); blk.append(cur)
        if cur is None: continue
        if pc == '0009ac' and rw == 'W' and (a - 0x1400) % 6 == 5: cur['lv'].append(v)
        if pc == '0009c6' and rw == 'W' and 0x2c46 <= a < 0x2c66: cur['out'].append(v)
    return blk, res, rans, wf


def main(s174, img, man):
    global SHIFT
    SHIFT = man["report"]["linein3"].get("fx_gain_shift", 0)
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    ring = []
    for k in range(512):
        v = int(0x300000 * math.sin(2 * math.pi * 440 * k / 48000)) & 0xFFFFFF
        ring += [v, v]
    dsum, rsum, ssum = pat_sum(DELAY_PAT), pat_sum(REVERB_PAT), pat_sum(SAT_PAT)
    for synth in (0, 1):
        for mode, pat, want in ((5, (DELAY_PAT, REVERB_PAT), dsum), (6, (DELAY_PAT, REVERB_PAT), rsum), (5, (SAT_PAT, REVERB_PAT), ssum)):
            prog = test_program(img, *pat)
            modes = [0, 0]; modes[synth] = mode
            blk, res, rans, wf = run(img, synth, modes, ring, program=prog,
                                     dumps=[('y', 0x3A80, 32), ('y', 0x3AC0, 32)])
            cap = {a: v for sp, a, v in res if sp == 'y'}
            dcap = [s24(x) for x in cap[0x3A80]]; rcap = [s24(x) for x in cap[0x3AC0]]
            check(dcap == pat_sum(pat[0]) and rcap == pat_sum(pat[1]),
                  f"capture buffers = saturated (L+R) << {SHIFT} of Y:$9C0 / Y:$880 (pattern {pat[0][0]:06x}/{pat[1][0]:06x})")
            worst, n = 0, 0
            for b in blk[-10:]:
                for o, l, x in zip(b['out'], b['lv'], want):
                    worst = max(worst, abs(o - ((x * l) >> 23))); n += 1
            check(n >= 200 and worst <= 2 and any(any(b['out']) for b in blk[-10:]),
                  f"Synth {synth+1}, mode {mode}: voice mix = {'saturated ' if pat[0] is SAT_PAT else ''}{'delay' if mode == 5 else 'reverb'} return x noise level ({n} samples, max err {worst})")
            other = [0, 0]; other[1 - synth] = mode
            bo, *_ = run(img, synth, other, ring, program=prog)
            br, *_ = run(img, synth, [0, 0], ring, program=prog)
            check([b['out'] for b in bo] == [b['out'] for b in br], f"Synth {synth+1} unaffected when only Synth {2-synth} uses mode {mode}")
    # mode 6 vs 5 are different sources
    prog = test_program(img, DELAY_PAT, REVERB_PAT)
    b5, *_ = run(img, 0, [5, 0], ring, program=prog); b6, *_ = run(img, 0, [6, 0], ring, program=prog)
    check([b['out'] for b in b5[-5:]] != [b['out'] for b in b6[-5:]], "modes 5 and 6 read different buffers")
    # regression: modes 0-4 and the final mix identical to SC17.4
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
        a, b = final(s174, modes), final(img, modes)
        check(a == b and any(any(v) for _, _, v in a), f"modes {modes}: final output blocks identical to SC17.4 (24 blocks)")
    # the capture runs only for modes 5 / 6 and writes nothing outside Y:$3A80..$3ADF
    def new_access(modes):
        t0, t1 = tempfile.mktemp(), tempfile.mktemp()
        run(s174, 0, modes, ring, blocks=24, trace=t0); run(img, 0, modes, ring, blocks=24, trace=t1)
        a0, a1 = open(t0, 'rb').read(), open(t1, 'rb').read()
        s18 = "sc18" in man["report"]                 # SC18: its drum blocks X:$3A80..$3AFF are updated every block
        return [(sp, hex(ad)) for sp, o in (('x', 0), ('y', 0x80000)) for ad in range(0x80000) if a1[o + ad] and not a0[o + ad]
                and not (s18 and sp == 'x' and 0x3A80 <= ad < 0x3A80 + 4 * man['report']['sc18'].get('dsp_stride', 32))
                and not ("vcf20" in man["report"] and sp == 'x' and 0x3B80 <= ad < 0x3C00)]       # SC20: the voice blocks are polled every block
    for modes in ([1, 0], [0, 0], [0, 4]):
        new = new_access(modes)
        check(not new, f"modes {modes}: no new X/Y access at all vs SC17.4 (capture idle) {new[:6]}")
    for modes in ([5, 0], [0, 6]):
        new = new_access(modes)
        bad = [n for n in new if not (n[0] == 'y' and 0x3A80 <= int(n[1], 16) < 0x3AE0)]
        check(new and not bad, f"modes {modes}: new X/Y accesses vs SC17.4 = {len(new)} addresses, all in Y:$3A80..$3ADF (bad {bad[:6]})")
    # cost
    def ins(image, modes):
        s = Session(image)
        s.midi(bytes([0xB0, 56, 127])); s.midi(bytes([0x90, 60, 100]))
        ex = [('y', 0x1000 + i, v) for i, v in enumerate(ring)] + [('x', 0x3A01, modes[0]), ('x', 0x3A02, modes[1])]
        _, rans = s.run(blocks=12, per_block=True, extra=ex)
        n = [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
        del s; gc.collect()
        return sum(n) / len(n)
    i4, i5, i5on = ins(s174, [0, 0]), ins(img, [0, 0]), ins(img, [5, 0])
    base18 = 400 if "sc18" in man["report"] else 0    # SC18: per-block drum control (~65 instructions per drum) + idle stage
    if man["report"].get("vcf20"): base18 += 250                                      # SC20: the two voices are polled every block (ACT, mailbox): ~+120 with both off
    if man["report"].get("persist19", {}).get("extras"): base18 += 100              # SC19.9: distortion type / filter slope bookkeeping (+44 measured by emu_sc19_9_dsp.py)
    check(i5 - i4 < 40 + base18, f"cost when idle: +{i5 - i4:.0f} instructions per block (SC17.4 {i4:.0f}{', SC18 drum control included' if base18 else ''})")
    print(f"     capture on (mode 5): +{i5on - i4:.0f} instructions per block")
    print("SC17.5 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    s174, im = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
    sys.exit(1 if main(s174, im, json.loads(Path(sys.argv[3]).read_text())) else 0)
