"""SC18.1 drum controls (tools/drums2_dsp.py), DSP tests on the dsp56kEmu interpreter.

    python tools/emu_sc18_1_dsp.py SC18.1.bin SC18.1_manifest.json [SC18.bin]
Same structure as emu_sc18_dsp.py: bit-exact models of every per-sample stage (ring modulator, bitcrush, the four SVF
outputs, comb, tremolo), the per-block control (mailbox codes 1..9, attack / decay envelope, filter modes, EQ save /
restore), the trigger, and whole-core runs with real ARM triggers.
"""
from __future__ import annotations
import json, math, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
from emu_sc18_dsp import m_crush, m_trem  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
TRAMP = 0x3900                                    # above the program (SC20 ends at $378x; the limit is $3800)
VOICE_R3 = 0x1E8D
BUF = 0x2C02
SC16_BLK = 0x3A10


def T(*l): return G.T(*l)


def m_ring(buf, s, c, f, amt):
    out = []; a = Acc.of(s); b = Acc.of(c)
    for x in buf:
        y0 = b.lim(); a.mac(f, y0)
        y0 = a.lim(); b.mac(f, y0, neg=True)
        sm = a.lim()
        y0 = b.lim(); a = Acc().mpy(y0, x); y0 = a.lim()
        a = Acc.of(x); a.v = -a.v; a.add24(y0); y0 = a.lim()
        a = Acc.of(x).mac(amt, y0); out.append(a.lim())
        a = Acc.of(sm)
    return out, a.lim(), b.lim()


def m_svf(buf, f, q, low, band, mode):
    out = []; a = Acc.of(low); x0 = band
    for x in buf:
        a.mac(f, x0)
        b = Acc.of(x).asr(); b.sub(a); b.mac(x0, q, neg=True); b.mac(x0, q, neg=True); x1 = b.lim()
        b = Acc.of(x0).mac(x1, f); x0 = b.lim()
        if mode == 1: o = Acc(a.v)
        elif mode == 2: o = Acc.of(x1)
        elif mode == 3: o = Acc.of(x0)
        else: o = Acc(a.v).add24(x1)
        out.append(o.asl().lim())
    return out, a.lim(), x0


def m_comb(buf, mem, wp, d, fb):
    y0 = Acc.of(0x7FFFFF).sub24(fb).lim()
    mem = list(mem); rd = (wp - d) % DD.COMB_N; out = []
    for x in buf:
        a = Acc().mpy(y0, x); a.mac(fb, mem[rd]); rd = (rd + 1) % DD.COMB_N
        v = a.lim(); mem[wp] = v; wp = (wp + 1) % DD.COMB_N; out.append(v)
    return out, mem, wp


def main(img, man, prev=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) <= 0x3800, f"program ends at P:${len(P0):x} (limit $3800)")
    tabs = DD.tables()
    for name in ("TEXP", "TLFO", "TF", "TCR", "TATK", "TDEC", "TCOMB"):
        check(P0[dl[name]:dl[name] + len(tabs[name])] == tabs[name], f"table {name} at P:${dl[name]:x} ({len(tabs[name])} words)")
    rnd = random.Random(181)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(N)]
    blk = lambda vals, d=0: [('x', DD.DB + DD.STRIDE * d, [vals.get(i, 0) & 0xFFFFFF for i in range(DD.STRIDE)])]
    common = [('x', 0x3A, [N]), ('x', 0x39, [5]), ('x', SC16_BLK, [0] * 36), ('x', 0x1ED6, [0x9F, 0xA3, VOICE_R3])]
    def call(addr, mem, dumps, regs=(), P=None):
        res, ran = run(P or P0, addr, mem=common + mem, dumps=dumps, regs_code=list(regs))
        assert 'pc=00' in ran, ran
        return res

    # ---------------------------------------------------------------- dstage (drum 0)
    def stage(vals, buf, mem=(), dumps=()):
        r = call(dl["dstage"], blk(vals) + [('x', BUF, buf), ('x', VOICE_R3, [0x3B00, 0xF0, 0x400000, 0, 0, 0, 1, 0x500000] + [0] * 10),
                                            ('x', 0xA3, [0, 0x10000, 0, 0, 0x123456])] + list(mem),
                 [('x', BUF, N), ('x', DD.DB, DD.STRIDE), ('x', 0xA3, 5)] + list(dumps))
        return r
    buf = sig()
    r = stage({}, buf)
    check(r[('x', BUF)] == buf and r[('x', 0xA3)][4] == 0x123456, "all controls off: drum block and EQ value untouched")
    r = stage({DD.FSAV: 1, DD.GSV: 0x2A0000}, buf)
    check(r[('x', 0xA3)][4] == 0x2A0000 and r[('x', DD.DB)][DD.FSAV] == 0, "dstage restores the EQ value zeroed by dctl")
    for rmf, rma, s0, c0 in ((40, 127, 0, DD.q24(0.9)), (127, 64, 0x123456, 0x400000), (0, 10, 0xF00000, 0x100000)):
        buf = sig(); f = tabs["TF"][rmf >> 1]
        exp, s2, c2 = m_ring(buf, s0, c0, f, u24(rma << 16))
        r = stage({DD.RMF: rmf, DD.RMA: rma, DD.RS: s0, DD.RC: c0}, buf)
        b = r[('x', DD.DB)]
        check(r[('x', BUF)] == exp and b[DD.RS] == s2 and b[DD.RC] == c2, f"ring mod freq {rmf} amount {rma}: bit-exact, oscillator carried")
    # the oscillator keeps its amplitude over many blocks (magic circle)
    s0, c0 = 0, DD.q24(0.9); f = tabs["TF"][50]
    for _ in range(400): _, s0, c0 = m_ring([0] * N, s0, c0, f, 0)
    check(0.8 < math.hypot(s24(s0), s24(c0)) / 2**23 < 1.0, f"ring oscillator amplitude stable after 400 blocks ({math.hypot(s24(s0), s24(c0)) / 2**23:.3f})")
    for crn, crm, crc in ((2, 0xFFF000, 1), (6, 0xF00000, 3)):
        buf = sig(); exp, c2, h2 = m_crush(buf, crc, 0x123456, crm, crn)
        r = stage({DD.CRN: crn, DD.CRM: crm, DD.CRC: crc, DD.CRH: 0x123456}, buf)
        check(r[('x', BUF)] == exp, f"bitcrush N={crn}: bit-exact")
    for mode, name in ((1, "LP"), (2, "HP"), (3, "band-pass"), (4, "notch")):
        buf = sig(); f, q = 0x180000, 0x300000
        exp, lo, ba = m_svf(buf, f, q, 0x010000, 0xFF0000, mode)
        r = stage({DD.FMODE: mode, DD.FF: f, DD.FQ: q, DD.LOW: 0x010000, DD.BAND: 0xFF0000}, buf)
        b = r[('x', DD.DB)]
        check(r[('x', BUF)] == exp and b[DD.LOW] == lo and b[DD.BAND] == ba, f"filter {name}: bit-exact, state carried")
    for d_, fb, wp in ((40, 0x600000, 0), (6, 0x790000, 250), (255, 0x100000, 17)):
        buf = sig(); mem = [u24(rnd.randrange(-0x100000, 0x100000)) for _ in range(DD.COMB_N)]
        exp, mem2, wp2 = m_comb(buf, mem, wp, d_, fb)
        r = stage({DD.FMODE: 5, DD.CD: d_, DD.FQ: fb, DD.CWP: DD.COMB + wp}, buf, mem=[('x', DD.COMB, mem)], dumps=[('x', DD.COMB, DD.COMB_N)])
        b = r[('x', DD.DB)]
        check(r[('x', BUF)] == exp and r[('x', DD.COMB)] == mem2 and b[DD.CWP] == DD.COMB + wp2,
              f"comb delay {d_} feedback {fb / 2**23:.2f} (write {wp}): bit-exact, buffer wraps (modulo 256), pointer carried")
    buf = sig(); mem = [0] * DD.COMB_N
    r = stage({DD.FMODE: 5, DD.CD: 10, DD.FQ: 0x400000, DD.CWP: DD.COMB}, buf, mem=[('x', DD.COMB, mem), ('x', DD.COMB + DD.COMB_N, [0x5555] * 8)],
              dumps=[('x', DD.COMB + DD.COMB_N, 8)])
    check(r[('x', DD.COMB + DD.COMB_N)] == [0x5555] * 8, "comb of drum 1 stays inside its 256 words (drum 2's buffer untouched)")
    buf = sig(); exp = m_trem(buf, 0x7FFFFF, 0x300000)
    r = stage({DD.LFO: 10, DD.TG: 0x7FFFFF, DD.TGN: 0x300000}, buf)
    check(r[('x', BUF)] == exp, "tremolo: bit-exact")

    # ---------------------------------------------------------------- dctl (drum 0)
    def ctl(vals, eq=0, trig=0, active=0, mem=()):
        voice = [0x3B00, 0xF0, 0x400000, 0, 0, 0, active, 0] + [0] * 10
        r = call(dl["dctl"], blk(vals) + [('x', 0xA3, [0, 0x10000, 0, 0, u24(eq)]), ('x', 0x9F, [trig]), ('x', VOICE_R3, voice)] + list(mem),
                 [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18), ('x', 0xA3, 5)],
                 regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3))
        return r[('x', DD.DB)], r[('x', VOICE_R3)], r[('x', 0xA3)]
    def mb(tag, code, delta): return (tag << 23) | (code << 16) | (delta & 0xFFFF)
    for (code, delta), init, off, exp in (((7, -20), {}, DD.ENVS, -20), ((7, 90), {}, DD.ENVS, 63), ((2, 50), {DD.RMF: 100}, DD.RMF, 127),
                                          ((8, -5), {DD.RMA: 3}, DD.RMA, 0), ((1, -70), {}, DD.PE, -64), ((6, 30), {}, DD.RES, 30)):
        vals = dict(init); vals[DD.MB] = mb(1, code, delta)
        b, _, _ = ctl(vals)
        check(s24(b[off]) == exp, f"mailbox code {code} delta {delta}: -> {exp}")
    for start, delta, exp in ((0, 1, 1), (4, 1, 0), (0, -1, 4), (2, -3, 1), (3, 0, 4)):
        b, _, _ = ctl({DD.MB: mb(1, 9, delta), DD.FSEL: start})
        check(b[DD.FSEL] == exp, f"filter mode {start} + step({delta:+}) -> {exp} (0 DJ, 1 band-pass, 2 notch, 3 comb, 4 tilt EQ)")
    # envelope
    b, _, _ = ctl({DD.ENV: 0x7FFFFF})
    check(b[DD.ATK] == 0 and b[DD.DK] == tabs["TDEC"][64] and b[DD.ENV] == Acc().mpy(tabs["TDEC"][64], 0x7FFFFF).lim(),
          f"envelope centre: no attack, decay x{tabs['TDEC'][64] / 2**23:.4f} per block (tau {DD.DEC_BASE * 1000:.0f} ms)")
    b, _, _ = ctl({DD.ENVS: 40, DD.ENV: 0x7FFFFF})
    check(b[DD.DK] == tabs["TDEC"][104], f"envelope +40: longer decay (tau {DD.DEC_BASE * 2 ** (40 / DD.DEC_OCT):.2f} s)")
    b, _, _ = ctl({DD.ENVS: -32, DD.ENV: 0x100000, DD.EPH: 1})
    check(b[DD.ENV] == u24(0x100000 + tabs["TATK"][32]) and b[DD.EPH] == 1, f"envelope -32: attack phase, +{tabs['TATK'][32] / 2**23:.4f} per block ({DD.ATK_MAX * 500:.0f} ms)")
    b, _, _ = ctl({DD.ENVS: -32, DD.ENV: 0x7FF000, DD.EPH: 1})
    check(b[DD.ENV] == 0x7FFFFF and b[DD.EPH] == 0, "envelope: attack reaches 1, then decay phase")
    # filter modes
    for fsel, v, ec, active, mode, idx in ((0, 20, 0, 1, 1, 20), (0, 64, 0, 1, 0, None), (0, 100, 0, 1, 2, 36), (1, 20, 0, 1, 3, 10),
                                            (2, 100, 0, 1, 4, 50), (1, 64, 30, 1, 3, None), (3, 64, 0, 1, 5, 64), (3, 0, 20, 1, 5, None),
                                            (4, 20, 0, 1, 0, None), (0, 20, 0, 0, 1, 20)):
        b, v_, eq = ctl({DD.FSEL: fsel, DD.EC: ec, DD.ENV: 0x7FFFFF, DD.RES: 64}, eq=(v - 64) << 17, active=active)
        env2 = Acc().mpy(tabs["TDEC"][64], 0x7FFFFF).lim()
        off = Acc().mpy(env2, u24(ec)).v >> 24
        ok = b[DD.FMODE] == mode
        # dctl jumps into the real voice: with the voice playing, dstage runs too and restores the EQ value it zeroed
        zeroed = fsel != 4 and active
        ok = ok and eq[4] == u24((v - 64) << 17) and b[DD.FSAV] == 0 and b[DD.GSV] == (u24((v - 64) << 17) if fsel != 4 else 0)
        if mode in (1, 2, 3, 4):
            ii = (v if mode == 1 else v - 64) if mode < 3 else v // 2
            ii = max(0, min(63, ii + off))
            ok = ok and b[DD.FF] == tabs["TF"][ii] and (idx is None or ii == idx)
        if mode == 5:
            ci = max(0, min(127, v + ((2 * Acc().mpy(env2, u24(ec)).v) >> 24)))
            ok = ok and b[DD.CD] == tabs["TCOMB"][ci] and b[DD.FQ] == Acc().mpy(DD.FBK, u24(64 << 16)).lim()
        check(ok, f"filter mode {fsel}, K8 {v}, EC {ec}, voice {'on' if active else 'off'}: FMODE {mode}" +
              (f", EQ saved ({hex(b[DD.GSV])}), zeroed for the voice and restored by dstage" if zeroed else ", EQ untouched"))
    b, _, eq = ctl({DD.FSEL: 1}, eq=(30 - 64) << 17, trig=100)
    check(b[DD.GSV] == u24((30 - 64) << 17) and eq[4] == u24((30 - 64) << 17), "a pending trigger also saves / zeroes the EQ for this block (restored after)")
    # pitch still as SC18 (offsets changed)
    b, v_, _ = ctl({DD.BASE: 0x200000, DD.PE: -32, DD.ENV: 0x7FFFFF})
    e2 = b[DD.ENV] / 2**23
    check(abs(v_[2] / 0x200000 / 2 ** (-12 * e2 / 12) - 1) < 0.003, f"pitch envelope amount (Shift + K1) -32: ratio {v_[2] / 0x200000:.4f}")

    # ---------------------------------------------------------------- dtrig
    tramp = [0x0BF080, dl["dtrig"]] + T("move a1,x:>$3b90", "move a0,x:>$3b91") + [0x00000C]
    P1 = P0 + [0] * (TRAMP - len(P0)) + tramp
    def trig(vals):
        r = call(TRAMP, blk(vals) + [('x', VOICE_R3, [0x3B00, 0x1000] + [0] * 16)], [('x', DD.DB, DD.STRIDE), ('x', VOICE_R3, 18)],
                 regs=T("move #>$9f,r1", "move #>$a3,r2", "move #>$%x,r3" % VOICE_R3, "move #>$200000,a"), P=P1)
        return r[('x', DD.DB)], r[('x', VOICE_R3)]
    b, v_ = trig({})
    check(b[DD.ENV] == 0x7FFFFF and b[DD.EPH] == 0 and b[DD.RS] == 0 and b[DD.RC] == DD.q24(DD.RING_C0) and b[DD.BASE] == 0x200000,
          "trigger, no attack: envelope 1 (decay), ring oscillator restarted")
    b, v_ = trig({DD.ATK: 0x1000})
    check(b[DD.ENV] == 0 and b[DD.EPH] == 1, "trigger with attack: envelope from 0, attack phase")

    # ---------------------------------------------------------------- whole core
    def session(image, vals, blocks=30, hits=((0, 100),), spmax=False, trace=None, raw=(), stride=DD.STRIDE, db=DD.DB):
        s = Session(image)
        for d, vel in hits: s.capture(f'hit{d}', 0x08051B54, d, vel)
        extra = [('x', 0xA4 + 10 * d, 0x10000) for d in range(4)] + [('x', 0xA5 + 10 * d, 0x7FFFFF) for d in range(4)]
        for k in range(64): extra += [('x', 0x1D8D + 4 * k, 0x3B00), ('x', 0x1D8E + 4 * k, 0x3000), ('x', 0x1D8F + 4 * k, 0x8000)]
        for i in range(0x100): extra.append(('y', 0x3B00 + i, u24(int(0x400000 * math.sin(i * 0.2)))))
        for (d, off), val in vals.items(): extra.append(('x', db + stride * d + off, val & 0xFFFFFF))
        extra += list(raw)
        res, rans = s.run(blocks=blocks, per_block=False, extra=extra, spmax=spmax, trace=trace,
                          dumps=[('x', db, 4 * stride), ('x', 0xEB, 0x70), ('x', 0xA3, 40)])
        return {(sp_, a): v for sp_, a, v in res}, rans
    R, _ = session(img, {(0, DD.ENVS): -4, (0, DD.PE): 30})
    b0 = R[('x', DD.DB)][:DD.STRIDE]
    check(b0[DD.BASE] != 0 and b0[DD.EPH] == 0 and b0[DD.ENV] > 0x600000, f"whole core, hit with attack: envelope rose to the top and decays ({hex(b0[DD.ENV])})")
    eqv = [('x', 0xA7 + 10 * d, u24((30 - 64) << 17)) for d in range(4)] + [('y', 0x109 + d, u24((30 - 64) << 17)) for d in range(4)]
    R, _ = session(img, {(d, DD.FSEL): 1 for d in range(4)}, raw=eqv, hits=tuple((d, 100) for d in range(4)))
    check(all(R[('x', 0xA3)][10 * d + 4] == u24((30 - 64) << 17) for d in range(4)), "whole core, filter mode band-pass: the EQ values are restored after every block")
    if prev:
        allon = {(d, k): v for d in range(4) for k, v in ((DD.PE, 30), (DD.ENVS, 20), (DD.RMF, 60), (DD.RMA, 80), (DD.LFO, -40),
                                                           (DD.EC, 20), (DD.RES, 90), (DD.FSEL, 3))}
        allon.update({(d, DD.EXT): 0x55 for d in range(4)})
        import drums_dsp as D1
        tp, t1 = tempfile.mktemp(), tempfile.mktemp()
        hits4 = tuple((d, 100) for d in range(4))
        Rp, rp = session(prev, {}, hits=hits4, spmax=True, trace=tp, stride=D1.STRIDE, db=D1.DB)
        Ro, ro = session(img, {}, hits=hits4, spmax=True)
        Ra, ra = session(img, allon, hits=hits4, spmax=True, trace=t1, raw=eqv)
        check(all(Ra[('x', DD.DB)][d * DD.STRIDE + DD.FMODE] == 5 for d in range(4)), "whole core, everything on: comb active in the 4 drums")
        ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
        avg = lambda v: sum(v) / len(v)
        ip, io, ia = avg(ins(rp)), avg(ins(ro)), avg(ins(ra))
        print(f"     DSP instructions/block, 4 drums playing: SC18 {ip:.0f}, SC18.1 controls off {io:.0f}, all on (comb) {ia:.0f}")
        check(io - ip < 400, f"cost with every control off vs SC18: {io - ip:+.0f} instructions per block")
        check(ia - ip < 7000, f"cost with everything on in 4 drums: +{ia - ip:.0f} instructions per block vs SC18 off (~{100 * 2 * (ia - ip) / 166000:.1f}% at ~250 MHz)")
        spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
        check(spm(ra) <= spm(rp), f"stack depth SC18.1 {spm(ra)} <= SC18 {spm(rp)}")
        check(Ra[('x', 0xEB)] == Rp[('x', 0xEB)], "voice-slot table X:$EB..$15A identical to SC18")
        a1, a2 = open(tp, 'rb').read(), open(t1, 'rb').read()
        new = [(s_, ad) for s_, o in (('x', 0), ('y', 0x80000)) for ad in range(0x80000) if a2[o + ad] and not a1[o + ad]]
        ok_ = lambda s_, ad: (s_ == 'x' and (DD.COMB <= ad < DD.COMB + 4 * DD.COMB_N or DD.DB <= ad < DD.DB + 4 * DD.STRIDE or ("vcf20" in man["report"] and 0x3B80 <= ad < 0x3C00))) or \
                             (s_ == 'y' and 0x3B00 <= ad < 0x3B00 + 0x3000 + 8)
        bad = [(s_, hex(ad)) for s_, ad in new if not ok_(s_, ad)]
        check(not bad, f"SC18.1 touches nothing new outside X:$3400..$37FF (comb), X:$3A80..$3B7F and the sample data ({len(new)} new, bad {bad[:8]})")
    print("SC18.1 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    img = Path(sys.argv[1]).read_bytes(); man = json.loads(Path(sys.argv[2]).read_text())
    prev = Path(sys.argv[3]).read_bytes() if len(sys.argv) > 3 else None
    sys.exit(1 if main(img, man, prev) else 0)
