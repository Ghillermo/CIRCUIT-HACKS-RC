"""SC18 drum controls, DSP tests on the dsp56kEmu interpreter (the SC18 core-0 program).

    python tools/emu_sc18_dsp.py SC18.bin SC18_manifest.json [SC17.8.bin]
Unit tests call the new routines directly (dctl / dtrig / dstage) with prepared memory and compare with bit-exact
DSP56300 fixed-point models; the whole-core part triggers drums through the ARM (0x08051B54) with a test sample table.
"""
from __future__ import annotations
import json, math, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
import drums_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
TRAMP = 0x3700                        # free P memory for test trampolines
VOICE_R3 = 0x1E8D                     # voice state of drum 0 (stride $12)
BUF = 0x2C02
SC16_BLK = 0x3A10                     # SC16 side-chain blocks X:$3A10 + 9d (depth at +4 = 0: its mixhook does nothing)


def T(*l): return G.T(*l)


def m_hold(buf, hcnt, gain):
    out = []
    for x in buf:
        hcnt -= 1
        if hcnt < 0:
            hcnt = -1
            g = s24(gain) - DD.HOLD_STEP
            gain = u24(max(0, g))
        out.append(Acc().mpy(gain, x).lim())
    return out, u24(hcnt), gain


def m_crush(buf, crc, crh, crm, crn):
    out = []
    for x in buf:
        crc -= 1
        if crc <= 0:
            crh = u24(s24(x) & s24(crm)); crc = crn
        out.append(crh)
    return out, u24(crc), crh


def m_filter(buf, f, q, low, band, hp):
    out = []; a = Acc.of(low); x0 = band
    for x in buf:
        a.mac(f, x0)
        b = Acc.of(x).asr(); b.sub(a); b.mac(x0, q, neg=True); b.mac(x0, q, neg=True); x1 = b.lim()
        b = Acc.of(x0).mac(x1, f); x0 = b.lim()
        o = (Acc.of(x1) if hp else Acc(a.v)).asl().lim()
        out.append(o)
    return out, a.lim(), x0


def m_trem(buf, tg, tgn):
    d = Acc.of(tgn).sub24(tg); d.v >>= 5; x1 = d.lim()
    b = Acc.of(tg); out = []
    for x in buf:
        b.add24(x1); y0 = b.lim()
        out.append(Acc().mpy(y0, x).lim())
    return out


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= TRAMP, f"program ends at P:${len(P0):x} (< test trampolines at ${TRAMP:x}, limit $3800)")
    tabs = DD.tables()
    for name in ("TEXP", "TLFO", "TF", "TCR"):
        check(P0[dl[name]:dl[name] + len(tabs[name])] == tabs[name], f"table {name} at P:${dl[name]:x} ({len(tabs[name])} words)")
    rnd = random.Random(18)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(N)]
    blk = lambda vals: [('x', DD.DB, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]

    def call(addr, mem, dumps, regs=(), P=None):
        res, ran = run(P or P0, addr, mem=common + mem, dumps=dumps, regs_code=list(regs))
        assert 'pc=007002' in ran or 'pc=00' in ran, ran
        return res

    # ---------------------------------------------------------------- dstage passes (drum 0)
    def stage(vals, buf, extra_dumps=()):
        r = call(dl["dstage"], blk(vals) + [('x', BUF, buf), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0x500000] + [0] * 10)],
                 [('x', BUF, N), ('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18)] + list(extra_dumps))
        return r[('x', BUF)], r[('x', DD.DB)], r[('x', VOICE_R3)]
    buf = sig()
    o, b, v = stage({}, buf)
    check(o == buf, "all controls off: drum block untouched")
    for hcnt, gain in ((100, 0x7FFFFF), (10, 0x7FFFFF), (0, 0x300000), (0xFFFFFF, 0x030000)):
        buf = sig(); exp, h2, g2 = m_hold(buf, s24(hcnt), gain)
        o, b, v = stage({DD.HOLD: 40, DD.HCNT: hcnt, DD.HGAIN: gain}, buf)
        ended = v[6] == 0 and v[7] == 0
        check(o == exp and b[DD.HCNT] == h2 and b[DD.HGAIN] == g2 and ended == (g2 == 0),
              f"hold: counter {s24(hcnt)}, gain {hex(gain)} -> bit-exact, counter {s24(h2)}, gain {hex(g2)}, voice ended {ended}")
    for crn, crm, crc in ((2, 0xFFF000, 1), (6, 0xF00000, 3), (1, 0xFFFF00, 0)):
        buf = sig(); exp, c2, h2 = m_crush(buf, crc, 0x123456, crm, crn)
        o, b, v = stage({DD.CRN: crn, DD.CRM: crm, DD.CRC: crc, DD.CRH: 0x123456}, buf)
        check(o == exp and b[DD.CRC] == c2 and b[DD.CRH] == h2, f"bitcrush N={crn} mask={hex(crm)}: bit-exact, state carried")
    for mode, f, q in ((1, 0x100000, 0x5A8241), (2, 0x300000, 0x200000), (1, 0x020000, 0x040000)):
        buf = sig(); exp, lo, ba = m_filter(buf, f, q, 0x010000, 0xFF0000, mode == 2)
        o, b, v = stage({DD.FMODE: mode, DD.FF: f, DD.FQ: q, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, buf)
        check(o == exp and b[DD.LOW] == lo and b[DD.BAND] == ba, f"DJ filter {'LP' if mode == 1 else 'HP'} f={hex(f)} q={hex(q)}: bit-exact, state carried")
    for tg, tgn in ((0x7FFFFF, 0x200000), (0x100000, 0x700000)):
        buf = sig(); exp = m_trem(buf, tg, tgn)
        o, b, v = stage({DD.LFO: 30, DD.TG: tg, DD.TGN: tgn}, buf)
        check(o == exp and b[DD.TG] == tgn, f"tremolo gain {hex(tg)} -> {hex(tgn)}: bit-exact ramp, TG updated")
    buf = sig()
    e1, _, _ = m_hold(buf, 5, 0x7FFFFF); e2, _, _ = m_crush(e1, 1, 0, 0xFFF000, 2)
    e3, _, _ = m_filter(e2, 0x200000, 0x300000, 0, 0, False); e4 = m_trem(e3, 0x7FFFFF, 0x400000)
    o, b, v = stage({DD.HOLD: 1, DD.HCNT: 5, DD.HGAIN: 0x7FFFFF, DD.CRN: 2, DD.CRM: 0xFFF000, DD.CRC: 1,
                     DD.FMODE: 1, DD.FF: 0x200000, DD.FQ: 0x300000, DD.LFO: 1, DD.TG: 0x7FFFFF, DD.TGN: 0x400000}, buf)
    check(o == e4, "chain hold -> bitcrush -> filter -> tremolo: bit-exact")

    # ---------------------------------------------------------------- dctl (drum 0): mailbox + per-block setup
    def ctl(vals, eq=0, mem=()):
        r = call(dl["dctl"], blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, eq & 0xFFFFFF]), ('x', 0x9F, [0])] + list(mem),
                 [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18)],
                 regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3))
        return r[('x', DD.DB)], r[('x', VOICE_R3)]
    def mb(tag, code, delta): return (tag << 23) | (code << 16) | (delta & 0xFFFF)
    cases = [((1, 1, -20), {}, DD.PE, -20), ((1, 1, -100), {DD.PE: -30}, DD.PE, -64), ((1, 3, 70), {DD.LFO: 10}, DD.LFO, 63),
             ((1, 2, 5), {}, DD.HOLD, 5), ((1, 2, -9), {DD.HOLD: 3}, DD.HOLD, 0), ((1, 6, 200), {}, DD.RES, 127),
             ((1, 4, -3), {}, DD.LSPD, -3), ((1, 5, 12), {DD.EC: -2}, DD.EC, 10)]
    for (tag, code, delta), init, off, exp in cases:
        vals = dict(init); vals[DD.MB] = mb(tag, code, delta); vals[DD.MBL] = 0
        b, _ = ctl(vals)
        check(s24(b[off]) == exp and b[DD.MBL] == vals[DD.MB], f"mailbox code {code} delta {delta}: {init.get(off, 0)} -> {exp} (clamped), message marked applied")
    b, _ = ctl({DD.MB: mb(1, 1, 7), DD.MBL: mb(1, 1, 7), DD.PE: 3})
    check(s24(b[DD.PE]) == 3, "mailbox: same tag again -> ignored")
    b, _ = ctl({DD.MB: mb(0, 1, 7), DD.MBL: mb(1, 1, 7), DD.PE: 3})
    check(s24(b[DD.PE]) == 10, "mailbox: tag toggled back to 0 -> applied")
    b, _ = ctl({DD.MB: mb(1, 7, 7), DD.MBL: 0, DD.PE: 3})
    check(s24(b[DD.PE]) == 3 and b[DD.MBL] == mb(1, 7, 7), "mailbox: unknown code -> no change")
    b, _ = ctl({DD.ENV: 0x7FFFFF})
    check(b[DD.ENV] == Acc().mpy(DD.KENV, 0x7FFFFF).lim(), f"envelope decays by {DD.KENV / 2**23:.5f} per block (tau {DD.ENV_TAU * 1000:.0f} ms)")
    b, _ = ctl({DD.LSPD: -64, DD.PH: 0x400000})
    check(b[DD.PH] == u24(0x400000 + tabs["TLFO"][0]) and b[DD.TRI] == Acc.of(u24(0x400000 + tabs["TLFO"][0])).asl().add24(0x800000).lim(),
          "LFO: phase += TLFO[speed + 64], tri = 2|phase| - 1")
    for v, ec, env, res, mode, idx in ((64, 0, 0, 0, 0, None), (0, 0, 0, 0, 1, 0), (32, 0, 0, 64, 1, 32), (100, 0, 0, 127, 2, 36),
                                       (32, 20, 0x7FFFFF, 0, 1, 51), (32, -40, 0x7FFFFF, 0, 1, 0), (127, 30, 0x7FFFFF, 0, 2, 63),
                                       (64, -16, 0x7FFFFF, 0, 1, 47)):
        b, _ = ctl({DD.EC: ec, DD.ENV: env, DD.RES: res}, eq=(v - 64) << 17)
        env2 = Acc().mpy(DD.KENV, env).lim()
        ok = b[DD.FMODE] == mode
        if mode:
            off = Acc().mpy(env2, u24(ec)).v >> 24
            exp_idx = max(0, min(63, (v if mode == 1 and v != 64 else (63 if v == 64 else v - 64)) + off))
            fq = Acc.of(q := DD.q24(DD.Q0)).sub(Acc().mpy(DD.QK, u24(res << 16))).lim()
            ok = ok and b[DD.FF] == tabs["TF"][exp_idx] and exp_idx == (idx if idx is not None else exp_idx) and b[DD.FQ] == fq
        check(ok, f"filter v={v} EC={ec} env={env / 2**23:.2f} res={res}: mode {mode}" + (f", index {idx}, damping {b[DD.FQ] / 2**23 * 2:.3f}" if mode else ""))
    for lfo, tri in ((32, 0x400000), (63, 0x7FFFFF), (-20, 0), (0, 0)):
        b, _ = ctl({DD.LFO: lfo, DD.TRI: tri, DD.PH: 0x400000, DD.LSPD: -64})
        tri2 = b[DD.TRI]
        if lfo > 0:
            d = Acc().mpy(u24(lfo << 17), Acc.of(tri2).asr().add24(0x400000).lim())
            exp = Acc.of(0x7FFFFF).sub(d).lim()
        else:
            exp = 0x7FFFFF
        check(b[DD.TGN] == exp, f"tremolo target LFO={lfo}: {hex(b[DD.TGN])}")
    for c in (0, 1, 7, 15):
        b, _ = ctl({DD.EXT: c << 4 | 9})
        check(b[DD.CRN] == tabs["TCR"][2 * c] and b[DD.CRM] == tabs["TCR"][2 * c + 1], f"bitcrush level {c}: hold {b[DD.CRN]} samples, mask {hex(b[DD.CRM])}")
    # pitch modulation (BASE != 0): incr = BASE * 2^(semis / 12)
    base = 0x200000
    for pe, env, lfo, tri, semis in ((0, 0x7FFFFF, 0, 0, 0.0), (-32, 0x7FFFFF, 0, 0, -12 * Acc().mpy(DD.KENV, 0x7FFFFF).lim() / 2**23),
                                     (21, 0x400000, 0, 0, None), (0, 0, -64, 0x7F0000, None), (0, 0, -32, 0x300000, None)):
        b, v = ctl({DD.BASE: base, DD.PE: pe, DD.ENV: env, DD.LFO: lfo, DD.PH: tri, DD.LSPD: -64})
        e2 = b[DD.ENV] / 2**23; t2 = s24(b[DD.TRI]) / 2**23
        semis = pe * 24 / 64 * e2 + (-lfo * 2 / 64 * t2 if lfo < 0 else 0)
        ratio = v[2] / base; want = 2 ** (semis / 12)
        check(abs(ratio / want - 1) < 0.003, f"pitch: PE={pe} env={e2:.3f} LFO={lfo} tri={t2:+.3f} -> {semis:+.2f} semitones, ratio {ratio:.4f} (want {want:.4f})")
    b, v = ctl({DD.BASE: 0, DD.PE: 40, DD.ENV: 0x7FFFFF}, mem=[('x', VOICE_R3 + 2, [0x123456])])
    check(v[2] == 0x123456, "pitch: no trigger yet (BASE = 0) -> increment untouched")

    # ---------------------------------------------------------------- dtrig (drum 0): trampoline jsr dtrig ; save a
    tramp = [0x0BF080, dl["dtrig"]] + T("move a1,x:>$3b10", "move a0,x:>$3b11") + [0x00000C]
    P1 = P0 + [0] * (TRAMP - len(P0)) + tramp
    def trig(vals, inc=0x200000, length=0x1000):
        r = call(TRAMP, blk(vals) + [('x', VOICE_R3, [0x3B00, length] + [0] * 16)],
                 [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18), ('x', 0x3B10, 2)],
                 regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3, "move #>$%x,a" % inc), P=P1)
        return r[('x', DD.DB)], r[('x', VOICE_R3)], r[('x', 0x3B10)]
    b, v, pos = trig({})
    check(b[DD.BASE] == 0x200000 and v[2] == 0x200000 and b[DD.ENV] == 0x7FFFFF and b[DD.PH] == 0x400000 and b[DD.TRI] == 0
          and pos == [0, 0], "trigger: BASE = increment, envelope 1, LFO restarted, position 0, increment unchanged (no modulation)")
    for h in (1, 64, 127):
        b, v, pos = trig({DD.HOLD: h})
        exp = (128 - h) ** 2 * 6
        check(abs(s24(b[DD.HCNT]) - exp) <= 3 and b[DD.HGAIN] == 0x7FFFFF, f"trigger, hold {h}: gate after {s24(b[DD.HCNT])} samples (~{exp}, {s24(b[DD.HCNT]) / 48:.1f} ms)")
    for s in (1, 8, 15):
        b, v, pos = trig({DD.EXT: s}, length=0x1000)
        idx = pos[0] * 4
        check(abs(idx - 0x1000 * s // 16) <= 4, f"trigger, start point {s}: playback from index {idx} of {0x1000} ({s}/16)")
    b, v, pos = trig({DD.PE: -64})
    check(abs(v[2] / 0x200000 - 0.25) < 0.003, f"trigger with PE=-64: increment x{v[2] / 0x200000:.4f} at the hit (-24 semitones)")

    # ---------------------------------------------------------------- whole core: real triggers through the ARM
    def session(image, vals, blocks=30, hits=((0, 100),), spmax=False, trace=None, watch=(), raw=()):
        s = Session(image)
        for d, vel in hits: s.capture(f'hit{d}', 0x08051B54, d, vel)
        extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
        for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, 0x3000), ('x', 0x1D8F + 4 * k, 0x8000)]
        for i in range(0x100): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
        for (d, off), val in vals.items(): extra.append(('x', DD.DB + DD.STRIDE * d + off, val & 0xFFFFFF))
        extra += list(raw)
        wf = tempfile.mktemp()
        res, rans = s.run(blocks=blocks, per_block=False, extra=extra, spmax=spmax, trace=trace, watchfile=wf,
                          watch=list(watch) or [('x', VOICE_R3 + 2, 1)], dumps=[('x', DD.DB, 4 * DD.STRIDE), ('x', VOICE_R3, 4 * 18), ('x', 0xEB, 0x70)])
        w = [l.split() for l in open(wf)]
        return {(sp_, a): v for sp_, a, v in res}, rans, w
    R, rans, w = session(img, {(0, DD.PE): -32})
    incs = [int(x[3], 16) for x in w if x[1] == 'X:%06x' % (VOICE_R3 + 2) and x[2] == 'W']
    check(len(incs) > 20 and incs[1] < incs[-1] and all(incs[i] <= incs[i + 1] for i in range(1, len(incs) - 1)),
          f"whole core, drum 1 hit with PE=-32: increment rises block by block towards the base ({hex(incs[1])} .. {hex(incs[-1])})")
    blk0 = R[('x', DD.DB)][:DD.STRIDE]
    check(blk0[DD.BASE] != 0 and blk0[DD.ENV] < 0x7FFFFF, "whole core: dtrig ran on the ARM-triggered hit (BASE set, envelope decaying)")
    R2, rans2, _ = session(img, {(1, DD.HOLD): 120}, hits=((1, 100),), blocks=20)
    v1 = R2[('x', VOICE_R3)][18:36]
    check(v1[6] == 0 and v1[7] == 0, f"whole core, drum 2 with hold 120 ({(8) ** 2 * 6} samples): the gate closed and ended the voice")
    if prev:
        allon = {(d, k): v for d in range(4) for k, v in ((DD.PE, 30), (DD.HOLD, 60), (DD.LFO, -40), (DD.EC, 20), (DD.RES, 90))}
        allon.update({(d, DD.EXT): 0x55 for d in range(4)})
        tp, t18 = tempfile.mktemp(), tempfile.mktemp()
        Rp, rp, _ = session(prev, {}, hits=tuple((d, 100) for d in range(4)), spmax=True, trace=tp)
        Ro, ro, _ = session(img, {}, hits=tuple((d, 100) for d in range(4)), spmax=True)
        eq = [('x', 0xA7 + 10 * d, u24((20 - 64) << 17)) for d in range(4)]   # K8 at 20: low-pass active in the 4 drums
        Ra, ra, _ = session(img, allon, hits=tuple((d, 100) for d in range(4)), spmax=True, trace=t18, raw=eq)
        check(all(Ra[('x', DD.DB)][d * DD.STRIDE + DD.FMODE] == 1 and Ra[('x', DD.DB)][d * DD.STRIDE + DD.CRN] for d in range(4)),
              "whole core, everything on: filter (LP) and bitcrush active in the 4 drums")
        ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
        avg = lambda v: sum(v) / len(v)
        ip, io, ia = avg(ins(rp)), avg(ins(ro)), avg(ins(ra))
        print(f"     DSP instructions/block, 4 drums playing: SC17.8 {ip:.0f}, SC18 controls off {io:.0f}, SC18 all on {ia:.0f}")
        check(io - ip < 800, f"cost with every control off: +{io - ip:.0f} instructions per block")
        check(ia - ip < 6000, f"cost with everything on in 4 drums: +{ia - ip:.0f} instructions per block (~{100 * 2 * (ia - ip) / 166000:.1f}% at ~250 MHz)")
        spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
        check(spm(ra) <= spm(rp), f"stack depth SC18 {spm(ra)} <= SC17.8 {spm(rp)}")
        check(Ra[('x', 0xEB)] == Rp[('x', 0xEB)], "voice-slot table X:$EB..$15A identical to SC17.8")
        a1, a2 = open(tp, 'rb').read(), open(t18, 'rb').read()
        new = [(s_, ad) for s_, o in (('x', 0), ('y', 0x80000)) for ad in range(0x80000) if a2[o + ad] and not a1[o + ad]]
        smp = lambda s_, ad: s_ == 'y' and 0x3B00 <= ad < 0x3B00 + 0x3000 + 8      # test sample data, played from a start point
        bad = [(s_, hex(ad)) for s_, ad in new if not (s_ == 'x' and DD.DB <= ad < DD.DB + 4 * DD.STRIDE) and not smp(s_, ad)]
        check(not bad, f"SC18 touches nothing new outside X:$3A80..$3AFF and the sample data ({len(new)} new addresses, bad {bad[:8]})")
    print("SC18 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes(); man = json.loads(Path(sys.argv[2]).read_text())
    prev = Path(sys.argv[3]).read_bytes() if len(sys.argv) > 3 else None
    sys.exit(1 if main(img, man, prev) else 0)
