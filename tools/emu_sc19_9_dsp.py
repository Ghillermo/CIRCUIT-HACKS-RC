"""SC19.9 drum DSP tests (distortion type, filter slope; tools/drums2_dsp.py with XTRA), on the dsp56kEmu interpreter.

    python tools/emu_sc19_9_dsp.py SC19.8.bin SC19.9.bin SC19.9_manifest.json SC19.8_manifest.json
Same method as emu_sc18_1_dsp.py (bit-exact models of the per-sample stages with the real core 0 program):
  * TYPE = 0 and SLOPE = 0: the output buffer and the drum block are exactly SC19.8's for the stock controls (ring mod, crush, the four filters, comb, tremolo);
  * distortion type 1 / 2 / 3 (soft / hard / fold) with the stock distortion value 0, 0.25 and 0.9: bit-exact models; no change to the other drums' blocks;
  * slope 24 dB: the SVF twice, bit-exact, the pass-1 state in LOW / BAND and the pass-2 state in LOW2 / BAND2, restored after; none for the comb / no filter;
  * dctl: TYPE = EXT bits 8-9, SLOPE = EXT bit 10; the crush nibbles (EXT bits 0-7) untouched;
  * a whole-core run with the shaper and the slope on: the program ends below P:$3800, the stack is no deeper than SC19.8's, the cost.
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
from emu_sc18_1_dsp import m_svf, m_ring, m_comb  # noqa: E402
from emu_sc18_dsp import m_crush, m_trem  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
VOICE_R3 = 0x1E8D
BUF = 0x2C02
SC16_BLK = 0x3A10
X1, Y0 = 0x7FFFFF << 24, s24(0x800001) << 24


def T(*l): return G.T(*l)


def m_shape(buf, amt, typ):
    out = []
    for x in buf:
        b = Acc().mpy(amt, x); b.v <<= 3; b.add24(x)
        if typ == 2:
            out.append(b.lim())
        elif typ == 1:
            x0 = b.lim(); y0 = Acc().mpy(x0, x0).lim(); a = Acc().mpy(y0, x0)
            b2 = Acc.of(x0); b2.sub(a); b2.asr()
            a2 = Acc.of(x0); a2.v += b2.v; out.append(a2.lim())
        else:
            v = b.v
            for _ in range(3):
                if v > X1: v = -v + 2 * X1
                if v < Y0: v = -v - 2 * X1
            out.append(Acc(v).lim())
    return out


def main(prev, img, man, mp):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    sp, spp = dsp_program(img), dsp_program(prev)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    Pp = [int.from_bytes(spp[i:i + 3], 'big') for i in range(0, len(spp), 3)]
    slope = bool(man["report"]["persist19"].get("extras_slope"))                    # the filter slope was discarded for SC19.9: its tests run only for a build with it
    check(len(P0) < 0x3800, f"program ends at P:${len(P0):x} (limit $3800; SC19.8: ${len(Pp):x})")
    rnd = random.Random(199)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(N)]
    blk = lambda vals, d=0: [('x', DD.DB + DD.STRIDE * d, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    def call(P, addr, mem, dumps, regs=()):
        res, ran = run(P, addr, mem=common + mem, dumps=dumps, regs_code=list(regs))
        assert 'pc=00' in ran, ran
        return res
    def stage(P, label_addr, vals, buf, amt=0, mem=()):
        return call(P, label_addr, blk(vals) + [('x', BUF, buf), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0x500000] + [0] * 10),
                                                ('x', 0xA3, [0, 0x10000, 0, amt, 0x123456])] + list(mem),
                    [('x', BUF, N), ('x', DD.DB, DD.STRIDE), ('x', DD.DB + DD.STRIDE, DD.STRIDE), ('x', 0xA3, 8)])
    dstage_n, dstage_p = dl["dstage"], None

    # ---- the stock controls as SC19.8 (TYPE = SLOPE = 0)
    # SC19.8's dstage address from its manifest is not needed: the block layouts are the same up to slot 38, so the same state gives the same output
    cases = [({}, "all off"), ({DD.RMF: 40, DD.RMA: 127, DD.RC: DD.q24(0.9)}, "ring mod"), ({DD.CRN: 2, DD.CRM: 0xFFF000, DD.CRC: 1, DD.CRH: 0x123456}, "bitcrush"),
             ({DD.FMODE: 1, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "LP"),
             ({DD.FMODE: 4, DD.FF: 0x180000, DD.FQ: 0x300000, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, "notch"),
             ({DD.FMODE: 5, DD.CD: 40, DD.FQ: 0x600000, DD.CWP: DD.COMB}, "comb"), ({DD.LFO: 10, DD.TG: 0x7FFFFF, DD.TGN: 0x300000}, "tremolo")]
    for vals, name in cases:
        buf = sig()
        rn = stage(P0, dstage_n, vals, buf)
        rp = stage(Pp, int(mp["report"]["sc16"]["dsp_labels"]["dstage"], 16), vals, buf)
        same = rn[('x', BUF)] == rp[('x', BUF)] and rn[('x', DD.DB)][:39] == rp[('x', DD.DB)][:39]
        check(same, f"{name}: output and block identical to SC19.8 (TYPE 0, SLOPE 0)")
    # ---- distortion types
    for typ, name in ((1, "soft"), (2, "hard"), (3, "fold")):
        for amt in (0, 0x200000, 0x720000):
            buf = sig(0x500000)
            r = stage(P0, dstage_n, {DD.TYPE: typ}, buf, amt=amt)
            exp = m_shape(buf, amt, typ)
            check(r[('x', BUF)] == exp, f"distortion type {typ} ({name}), stock distortion {amt / 2 ** 23:.2f}: bit-exact")
            if typ == 3 and amt == 0x720000:
                check(max(abs(s24(v)) for v in exp) <= 0x7FFFFF and exp != buf, "fold: stays inside +-1")
    r = stage(P0, dstage_n, {DD.TYPE: 2}, buf := sig(), amt=0x720000)
    check(sum(1 for v in r[('x', BUF)] if abs(s24(v)) >= 0x7FFFFE) > 4, "hard clip at a high drive: samples sit on the rails")
    # ---- filter slope
    if not slope:
        buf = sig(); f, q = 0x180000, 0x300000
        o1, lo1, ba1 = m_svf(buf, f, q, 0x010000, 0xFF0000, 1)
        r = stage(P0, dstage_n, {DD.FMODE: 1, DD.FF: f, DD.FQ: q, DD.LOW: 0x010000, DD.BAND: 0xFF0000, DD.SLOPE: 1}, buf)
        check(r[('x', BUF)] == o1, "no slope code in this build: a set SLOPE slot changes nothing (one 12 dB pass)")
    for mode, name in (((1, "LP"), (2, "HP"), (3, "band-pass"), (4, "notch")) if slope else ()):
        buf = sig(); f, q = 0x180000, 0x300000
        o1, lo1, ba1 = m_svf(buf, f, q, 0x010000, 0xFF0000, mode)
        o2, lo2, ba2 = m_svf(o1, f, q, 0x020000, 0x0F0000, mode)
        r = stage(P0, dstage_n, {DD.FMODE: mode, DD.FF: f, DD.FQ: q, DD.LOW: 0x010000, DD.BAND: 0xFF0000, DD.SLOPE: 1, DD.LOW2: 0x020000, DD.BAND2: 0x0F0000}, buf)
        b = r[('x', DD.DB)]
        check(r[('x', BUF)] == o2 and b[DD.LOW] == lo1 and b[DD.BAND] == ba1 and b[DD.LOW2] == lo2 and b[DD.BAND2] == ba2 and b[DD.PASS] == 0,
              f"filter {name} 24 dB: two passes bit-exact, states of both carried, LOW / BAND restored")
        r = stage(P0, dstage_n, {DD.FMODE: mode, DD.FF: f, DD.FQ: q, DD.LOW: 0x010000, DD.BAND: 0xFF0000, DD.LOW2: 0x020000}, buf)
        check(r[('x', BUF)] == o1 and r[('x', DD.DB)][DD.LOW2] == 0x020000, f"filter {name} 12 dB: one pass, the second state untouched")
    buf = sig(); mem = [u24(rnd.randrange(-0x100000, 0x100000)) for _ in range(DD.COMB_N)]
    exp, mem2, wp2 = m_comb(buf, mem, 0, 40, 0x600000)
    r = stage(P0, dstage_n, {DD.FMODE: 5, DD.CD: 40, DD.FQ: 0x600000, DD.CWP: DD.COMB, DD.SLOPE: 1}, buf, mem=[('x', DD.COMB, mem)])
    check(r[('x', BUF)] == exp, "comb with SLOPE set: no second pass (the comb is not an SVF)")
    # frequency response: an LP at 24 dB attenuates twice as many dB
    def gain(slope, f_hz, idx=40):
        w = 2 * math.pi * f_hz / 48000; amp = 0x200000; peak = 0
        r = None
        lo, ba, lo2, ba2 = 0, 0, 0, 0
        for blk_i in range(40):
            buf = [u24(int(amp * math.sin(w * (blk_i * N + i)))) for i in range(N)]
            vals = {DD.FMODE: 1, DD.FF: DD.tables()["TF"][idx], DD.FQ: DD.q24(DD.Q0), DD.LOW: lo, DD.BAND: ba, DD.SLOPE: slope, DD.LOW2: lo2, DD.BAND2: ba2}
            r = stage(P0, dstage_n, vals, buf)
            b = r[('x', DD.DB)]; lo, ba, lo2, ba2 = b[DD.LOW], b[DD.BAND], b[DD.LOW2], b[DD.BAND2]
            if blk_i >= 30: peak = max(peak, max(abs(s24(v)) for v in r[('x', BUF)]))
        return 20 * math.log10(peak / amp)
    if slope:
        res = [(f_hz, gain(0, f_hz), gain(1, f_hz)) for f_hz in (2000, 4000, 8000)]
        print("     LP gain (12 dB filter, 24 dB filter) at 2 / 4 / 8 kHz:", [(f_hz, round(a, 1), round(b, 1)) for f_hz, a, b in res])
        ok = [(f_hz, a, b) for f_hz, a, b in res if -40 < a < -8]
        check(bool(ok) and all(abs(b - 2 * a) < 0.15 * abs(2 * a) + 2 for _, a, b in ok), f"LP above the cutoff: the 24 dB filter attenuates about twice the dB of the 12 dB one {ok}")
    # ---- dctl: TYPE / SLOPE from EXT, the crush nibbles untouched
    def ctl(vals):
        r = call(P0, dl["dctl"], blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, 0]), ('x', 0x9F, [0]), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 0, 0] + [0] * 10)],
                 [('x', DD.DB, DD.STRIDE)], regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3))
        return r[('x', DD.DB)]
    for ext, typ, slp in ((0x000, 0, 0), (0x100, 1, 0), (0x203, 2, 0), (0x55A, 1, 1), (0x7A5, 3, 1)):
        b = ctl({DD.EXT: ext})
        t = DD.tables()["TCR"]; k = ((ext >> 4) & 15) * 2
        check(b[DD.TYPE] == typ and (b[DD.SLOPE] == slp if slope else b[DD.SLOPE] == 0) and b[DD.CRN] == t[k] and b[DD.CRM] == t[k + 1], f"EXT {ext:#05x}: TYPE {b[DD.TYPE]}, SLOPE {b[DD.SLOPE]}{'' if slope else ' (not decoded in this build)'}, crush nibbles as before")

    # ---- whole core
    def session(image, vals, blocks=30, spmax=False, label=""):
        s = Session(image)
        for d in range(4): s.capture(f'hit{d}', 0x08051B54, d, 100)
        extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
        extra += [('x', 0xA6 + 10 * d, 0x400000) for d in range(4)]
        for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, 0x3000), ('x', 0x1D8F + 4 * k, 0x8000)]
        for i in range(0x100): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
        for (d, off), val in vals.items(): extra.append(('x', DD.DB + DD.STRIDE * d + off, val & 0xFFFFFF))
        res, rans = s.run(blocks=blocks, per_block=False, extra=extra, spmax=spmax, dumps=[('x', DD.DB, 4 * DD.STRIDE), ('x', 0xEB, 0x70)])
        return {(sp_, a): v for sp_, a, v in res}, rans
    off = {}
    on = {(d, k): v for d in range(4) for k, v in ((DD.EXT, 0x7A5), (DD.FSEL, 1), (DD.EC, 20), (DD.RES, 90), (DD.RMF, 60), (DD.RMA, 80))}
    Ro, ro = session(img, off, spmax=True); Ra, ra = session(img, on, spmax=True)
    Rp, rp = session(prev, off, spmax=True)
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    avg = lambda v: sum(v) / len(v)
    print(f"     DSP instructions/block, 4 drums playing: SC19.8 {avg(ins(rp)):.0f}, SC19.9 off {avg(ins(ro)):.0f}, type fold + 24 dB slope + ring mod on {avg(ins(ra)):.0f}")
    check(avg(ins(ro)) - avg(ins(rp)) < 200, f"cost with the new controls off: {avg(ins(ro)) - avg(ins(rp)):+.0f} instructions per block")
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    check(spm(ra) <= spm(rp), f"stack depth {spm(ra)} <= SC19.8's {spm(rp)}")
    check(Ra[('x', 0xEB)] == Rp[('x', 0xEB)], "voice-slot table X:$EB..$15A identical")
    check(all(Ra[('x', DD.DB)][d * DD.STRIDE + DD.TYPE] == 3 for d in range(4)), "whole core: TYPE 3 reaches the four blocks")
    print("SC19.9 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text()), json.loads(Path(a[4]).read_text())) else 0)
