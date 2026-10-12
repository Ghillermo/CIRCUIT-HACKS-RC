"""SC22 DSP tests (SC21.4 + the FX types ring mod / comb / chorus, the program up to P:$3FFF, the register save area at X:$38C0, envelope -> VCA and LFO -> VCA bipolar): SC21's VCF / VCA / FX (tools/vcf21_dsp.py) without the tilt EQ, plus the feedback of the FX returns (pmfb, capture after vret), on the dsp56kEmu interpreter with the real core 0 program.

    python tools/emu_sc22_dsp.py SC19.9.bin SC22.bin SC22_manifest.json
Each block is one call of the hook routines (vpre = P:$23C, vret = the P:$D21 chain) with the voice block carried from call to call.
  * voices off (ACT = 0): the ring and the returns are untouched, the registers the stock code may rely on are restored;
  * mode on with the default values: bit-exact bypass; the mailbox writes the values / gate / note / activation;
  * VCF: LP / HP index law (FILT, + ENVF x ENV + LFOF x LV + KEY x (note - 60) / 128), the coefficient tables, resonance; the SVF itself bit-exact against the drum model;
    the two inputs have independent state; the voice of one track does not touch the other input;
  * VCA: level, gate mode (ADSR over blocks: attack, decay to the sustain, release; the table values), tremolo, velocity; per-sample gain ramp bit-exact;
  * drive + saturation bit-exact; LFO shapes;
  * with the Setup's return flag the line input is left alone (the stock zeroing) and the return buffer (Y:$880 / $9C0, both channels) is processed instead;
  * whole core: stack depth and cost against SC19.9, and the synth sources still hear the clean input.
"""
from __future__ import annotations
import gc, json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import Session, dsp_program  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
from emu_sc18_1_dsp import m_svf  # noqa: E402
import drums2_dsp as DD  # noqa: E402
import vcf21_dsp as V  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.VFF = False, True, True, True, True, 0x4000, True
import masterfx_dsp as G  # noqa: E402

N = 32
RING = 0x1000
TAB = DD.tables()


def T(*l): return G.T(*l)


def vaddr(t, off): return V.VB0 + V.VBS * t + off


def main(prev, img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    sp = dsp_program(img)
    P0 = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    check(len(P0) < 0x4000, f"program ends at P:${len(P0):x} (the program RAM is 16 K words: P:$0000-$3FFF)")
    rnd = random.Random(2020)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(2 * N)]          # interleaved [in1, in2]
    blk0 = [0] * (2 * V.VBS)

    def params(t, **kw):
        names = dict(FILT=V.P_FILT, RES=V.P_RES, ENVF=V.P_ENVF, LFOF=V.P_LFOF, ATK=V.P_ATK, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, FXAMT=V.P_FXAMT, GAIN=V.P_GAIN,
                     LRATE=V.P_LRATE, LFOV=V.P_LFOV, FXTYPE=V.P_FXTYPE, FXMOD=V.P_FXMOD, ENVA=V.P_ENVA, FTYPE=V.P_FTYPE, GATE=V.GATE, NOTE=V.NOTE, ACT=V.ACT, VEL=V.VEL, GNEW=V.GNEW)
        return {V.VBS * t + names[k]: v for k, v in kw.items()}
    DEFAULT = dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=40, FXMOD=64, NOTE=60)           # NOTE 60: the ARM sends it at boot (key tracking is always on)

    def mk(blk, extra):
        b = list(blk)
        for off, v in extra.items(): b[off] = v & 0xFFFFFF
        return b

    def call_pre(blk, ring, flags=0, extra=()):
        res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [flags]), ('y', V.RING_PTR, [RING]), ('y', RING, ring)] + list(extra),
                       dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', V.SAVX, 32)],
                       regs_code=T("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$123456,y0", "move #>$654321,y1", "move #>$33,r0", "move #>$44,r1", "move #>$55,r6", "move #>$66,r7", "move #>7,n0", "move #>$ffff,m0"))
        assert 'pc=00' in ran, ran
        return res[('x', V.VB0)], res[('y', RING)]

    def call_ret(blk, rev, dly, flags, extra=()):
        res, ran = run(P0, dl["vret"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [flags]), ('y', 0x880, rev), ('y', 0x9C0, dly)] + list(extra),
                       dumps=[('x', V.VB0, 2 * V.VBS), ('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)], regs_code=[])
        assert 'pc=00' in ran, ran
        return res[('x', V.VB0)], res[('y', 0x880)], res[('y', 0x9C0)]

    # ---- voices off
    ring = sig()
    blk, out = call_pre(blk0, ring)
    check(out == ring and blk == blk0, "voices off: the ring and the voice blocks are untouched")
    rev, dly = sig(), sig()
    b2, r2, d2 = call_ret(blk0, rev, dly, 3)
    ref, _ = run(P0, 0x9F, mem=[('x', 0x3A, [N]), ('x', V.FLAGS, [3]), ('x', 0xEC, [3]), ('y', 0x880, rev), ('y', 0x9C0, dly)], dumps=[('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)], regs_code=[])
    check(r2 == ref[('y', 0x880)] and d2 == ref[('y', 0x9C0)], "voices off: the return chain is exactly the stock one (SC10 returns)")

    # ---- the registers the stock code may rely on are restored (vpre and vret, voices on)
    TR = 0x3C00
    regs = ["x0", "x1", "y0", "y1", "r0", "r1", "r6", "r7", "n0", "m0"]
    init = T("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$123456,y0", "move #>$654321,y1", "move #>$33,r0", "move #>$44,r1", "move #>$55,r6", "move #>$66,r7", "move #>7,n0", "move #>$ffff,m0")
    for name in ("vpre", "vret"):
        tramp = [0x0BF080, dl[name]] + T(*["move %s,x:>$%x" % (r, 0x3B90 + i) for i, r in enumerate(regs)]) + [0x00000C]
        P1 = P0 + [0] * (TR - len(P0)) + tramp
        onx = mk(blk0, {**params(0, ACT=1, FILT=-30, FXAMT=30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
        res, ran = run(P1, TR, mem=[('x', 0x3A, [N]), ('x', V.VB0, onx), ('x', V.FLAGS, [3 if name == "vret" else 0]), ('x', 0xEC, [3 if name == "vret" else 0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig()),
                                    ('y', 0x880, sig()), ('y', 0x9C0, sig())], dumps=[('x', 0x3B90, 10)], regs_code=init)
        got = res[('x', 0x3B90)]
        exp = [0xA5A5A5, 0x5A5A5A, 0x123456, 0x654321, 0x33, 0x44, 0x55, 0x66, 7, 0xFFFF]
        if name == "vret":                                                         # SC10's returns (our tail call) uses x0, y0 and reloads r0, r6, r7 itself: free at that hook
            for k in (0, 2, 4, 6, 7, 5): exp[k] = got[k]          # SC21.1: fx_cap now runs after vret and uses r0 / r1 (free at P:$D21, as documented)
        check(got == exp, f"{name}: the registers are restored {[hex(x) for x in got]}")
    # ---- mode on, defaults: bit-exact bypass
    on = mk(blk0, {**params(0, ACT=1, **DEFAULT), **params(1, ACT=1, **DEFAULT)})
    blk, out = call_pre(on, ring)
    check(out == ring and blk[V.FMODE] == 0 and blk[V.VCAON] == 0, "mode on with the default values: bit-exact bypass (no filter, no saturation, VCA off)")
    check(blk[V.VBS + V.FMODE] == 0 and blk[V.ACTP] == 1, "both voices start; activation remembered")

    # ---- VCF: low-pass / high-pass laws
    def vcf_case(filt, res, **kw):
        ex = mk(blk0, params(0, ACT=1, FILT=filt, RES=res, **{**DEFAULT, **kw}))
        ring_ = sig()
        blk_, out_ = call_pre(ex, ring_)
        return ring_, blk_, out_
    for filt, mode, idx in ((-64, 1, 0), (-30, 1, 34), (-3, 1, 61), (3, 2, 3), (20, 2, 20), (63, 2, 63)):
        res = 40
        ring_, blk_, out_ = vcf_case(filt, res)
        f = TAB["TF"][idx]
        qa = Acc.of(DD.q24(DD.Q0)); qa.sub(Acc().mpy(u24(res << 16), DD.QK)); q = qa.lim()
        exp, lo, ba = m_svf(ring_[0::2], f, q, 0, 0, mode)
        got = out_[0::2]
        check(blk_[V.FMODE] == mode and blk_[V.FF] == f and blk_[V.FQ] == q and got == exp and out_[1::2] == ring_[1::2] and blk_[V.LOW0] == lo and blk_[V.BAND0] == ba,
              f"FILT {filt:+d}: {'LP' if mode == 1 else 'HP'} index {idx}, coefficient and resonance from the tables, SVF bit-exact, state carried, the other input untouched")
    for filt in (-2, 0, 2):
        ring_, blk_, out_ = vcf_case(filt, 40)
        check(blk_[V.FMODE] == 0 and out_ == ring_, f"FILT {filt:+d}: the dead zone is a bypass")
    ring_, blk_, out_ = vcf_case(0, 40, LFOF=-30)
    ph = TAB["TLFO"][40] & 0xFFFFFF; lv = min(0x7FFFFF, -s24(ph)); steps = (-30 * lv) >> 23
    check(blk_[V.FMODE] == 1 and blk_[V.FF] == TAB["TF"][max(0, min(63, 63 + steps))], f"centre + LFO depth: low-pass opened to 63, moved by the reverse sawtooth ({steps:+d} steps)")
    ring_, blk_, out_ = vcf_case(-40, 40, NOTE=100)
    off = (V.KEYK * ((100 - 60) << 16)) // (1 << 23)                                # fixed key tracking: KEYK x (note - 60) / 128 in table steps
    check(blk_[V.FF] == TAB["TF"][max(0, min(63, -40 + 64 + off))], f"key tracking (always on): note 100 moves the low-pass by {off:+d} steps")
    ring_, blk_, out_ = vcf_case(0, 40, NOTE=72)
    check(blk_[V.FMODE] == 0 and out_ == ring_, "centre + key tracking alone: still a bypass (the DJ filter needs FILT or a modulation depth)")
    # ---- filter types: 1 band-pass, 2 notch, 3 tilt EQ (FILT = cutoff; tilt: fixed cutoff 32, FILT < 0 = bass lift, else treble lift)
    def svf_model(buf, f, q, mode):
        out = []; a = Acc.of(0); x0 = 0
        for x in buf:
            a.mac(f, x0)
            b = Acc.of(x).asr(); b.sub(a); b.mac(x0, q, neg=True); b.mac(x0, q, neg=True); x1 = b.lim()
            b = Acc.of(x0).mac(x1, f); x0 = b.lim()
            if mode == 3: o = Acc.of(x0)
            elif mode == 4: o = Acc(a.v).add24(x1)
            elif mode == 5: o = Acc.of(x1).asr(); o.v += a.v
            else: o = Acc(a.v).asr(); o.add24(x1)
            out.append(o.asl().lim())
        return out, a.lim(), x0
    for ftype, filt, mode, idx in ((3, 20, 3, 42), (3, -64, 3, 0), (3, 63, 3, 63), (4, -30, 4, 17), (4, 2, 4, 33)):
        res = 40
        ring_, blk_, out_ = vcf_case(filt, res, FTYPE=ftype)
        f = TAB["TF"][idx]
        qa = Acc.of(DD.q24(DD.Q0)); qa.sub(Acc().mpy(u24(res << 16), DD.QK)); q = qa.lim()
        exp, lo, ba = svf_model(ring_[0::2], f, q, mode)
        check(blk_[V.FMODE] == mode and blk_[V.FF] == f and out_[0::2] == exp and out_[1::2] == ring_[1::2] and blk_[V.LOW0] == lo and blk_[V.BAND0] == ba,
              f"filter type {ftype}, FILT {filt:+d}: mode {mode}, table index {idx}, SVF {['', '', '', 'band-pass', 'notch', 'tilt (bass)', 'tilt (treble)'][mode]} bit-exact, state carried")
    ring_, blk_, out_ = vcf_case(0, 40, FTYPE=3)
    check(blk_[V.FMODE] == 3 and out_ != ring_, "band-pass at the centre of FILT is a real filter (no bypass dead zone outside the DJ type)")
    ring_, blk_, out_ = vcf_case(0, 40, FTYPE=4, LFOF=-10)
    check(blk_[V.FMODE] == 4, "notch: the modulation moves the cutoff")
    # ---- SC21.4: low-pass / high-pass of 12 dB (types 1 / 2, the SVF once) and 24 dB (types 5 / 6, the SVF twice, the second stage with its own state at X:$3800 + 48 t + 2 c); K5 = the cutoff
    def slope_case(ftype, filt, res, t_=0, st1=(0, 0), st2=(0, 0)):
        off = V.VBS * t_
        ex = mk(blk0, params(t_, ACT=1, FILT=filt, RES=res, FTYPE=ftype, **DEFAULT))
        ex[off + V.LOW0], ex[off + V.BAND0] = st1
        ring_ = sig()
        resx, _ = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, ex), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring_), ('x', 0x3800 + 48 * t_, list(st2))],
                      dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', 0x3800 + 48 * t_, 2)], regs_code=[])
        return ring_, resx[('x', V.VB0)], resx[('y', RING)], resx[('x', 0x3800 + 48 * t_)]
    def qof(res):
        qa = Acc.of(DD.q24(DD.Q0)); qa.sub(Acc().mpy(u24(res << 16), DD.QK)); return qa.lim()
    for ftype, filt, mode_, name in ((1, -20, 1, "LP 12"), (1, 63, 1, "LP 12"), (2, 10, 2, "HP 12"), (2, -64, 2, "HP 12")):
        res = 50; ring_, blk_, out_, s2 = slope_case(ftype, filt, res)
        f = TAB["TF"][(filt + 64) >> 1]
        exp, lo, ba = m_svf(ring_[0::2], f, qof(res), 0, 0, mode_)
        check(blk_[V.FMODE] == ftype and blk_[V.FF] == f and out_[0::2] == exp and out_[1::2] == ring_[1::2] and blk_[V.LOW0] == lo and s2 == [0, 0],
              f"{name} dB, K5 {filt:+d}: cutoff index {(filt + 64) >> 1}, one SVF pass, bit-exact, no second stage")
    for ftype, filt, mode_, name in ((5, -20, 1, "LP 24"), (5, 40, 1, "LP 24"), (6, 10, 2, "HP 24"), (6, -50, 2, "HP 24")):
        res = 50
        st1, st2 = (0x012345, 0x0A0B0C), (0x045678, 0x00ABCD)
        ring_, blk_, out_, s2 = slope_case(ftype, filt, res, st1=st1, st2=st2)
        f = TAB["TF"][(filt + 64) >> 1]; q = qof(res)
        mid, lo1, ba1 = m_svf(ring_[0::2], f, q, st1[0], st1[1], mode_)
        exp, lo2, ba2 = m_svf(mid, f, q, st2[0], st2[1], mode_)
        check(blk_[V.FMODE] == ftype and out_[0::2] == exp and out_[1::2] == ring_[1::2] and blk_[V.LOW0] == lo1 and blk_[V.BAND0] == ba1 and s2 == [lo2, ba2],
              f"{name} dB, K5 {filt:+d}: the SVF twice, bit-exact, both states carried (stage 1 in the block, stage 2 at X:$3800)")
        check(out_[0::2] != m_svf(ring_[0::2], f, q, st1[0], st1[1], mode_)[0], f"{name} dB: differs from the 12 dB output (a real second stage)")
    # the second voice has its own second-stage state (X:$3830), and the two channels of a return (L / R) their own (X:$3800 + 2 c)
    ring_, blk_, out_, s2 = slope_case(5, 0, 40, t_=1, st2=(0x111111, 0x222222))
    exp, _, _ = m_svf(m_svf(ring_[1::2], TAB["TF"][32], qof(40), 0, 0, 1)[0], TAB["TF"][32], qof(40), 0x111111, 0x222222, 1)
    check(out_[1::2] == exp and out_[0::2] == ring_[0::2], "voice 2: its own second stage at X:$3830, input 1 untouched")
    onr, _ = call_pre(mk(blk0, {**params(0, ACT=1, FILT=-10, FTYPE=5, **DEFAULT)}), sig(), flags=1)          # the control of the voice runs in vpre; vret uses its results
    rev, dly = sig(0x200000), sig(0x200000)
    resr, _ = run(P0, dl["vret"], mem=[('x', 0x3A, [N]), ('x', V.VB0, onr), ('x', V.FLAGS, [1]), ('x', 0xEC, [1]), ('y', 0x880, rev), ('y', 0x9C0, dly), ('x', 0x3800, [0x010000, 0x020000, 0x030000, 0x040000])],
                  dumps=[('y', 0x880, 2 * N), ('x', 0x3800, 4)], regs_code=[])
    # (the return buffer passes through the stock return chain afterwards: compare the filter states only)
    f = TAB["TF"][27]; q = qof(0)
    m1L, lo1L, ba1L = m_svf(rev[0::2], f, q, 0, 0, 1); m1R, lo1R, ba1R = m_svf(rev[1::2], f, q, 0, 0, 1)
    _, lo2L, ba2L = m_svf(m1L, f, q, 0x010000, 0x020000, 1); _, lo2R, ba2R = m_svf(m1R, f, q, 0x030000, 0x040000, 1)
    check(resr[('x', 0x3800)] == [lo2L, ba2L, lo2R, ba2R], "the reverb return (voice 1, LP 24): the left channel's second stage at X:$3800, the right channel's at X:$3802")
    initr = T("move #>$77,r2")
    tramp = [0x0BF080, dl["vpre"]] + T("move r2,x:>$3bd6") + [0x00000C]
    Pt = P0 + [0] * (0x3C00 - len(P0)) + tramp
    onx2 = mk(blk0, {**params(0, ACT=1, FILT=5, FTYPE=6, **DEFAULT)})
    resq, _ = run(Pt, 0x3C00, mem=[('x', 0x3A, [N]), ('x', V.VB0, onx2), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig())], dumps=[('x', 0x3BD6, 1)], regs_code=initr)
    check(resq[('x', 0x3BD6)] == [0x77], "r2 (the second-stage pointer / flag) is restored by vpre")


    # ---- the two inputs are independent
    ex = mk(blk0, {**params(0, ACT=1, FILT=-30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
    ring_ = sig()
    blk_, out_ = call_pre(ex, ring_)
    f0, f1 = TAB["TF"][34], TAB["TF"][25]
    q0 = blk_[V.FQ]
    e0, _, _ = m_svf(ring_[0::2], f0, q0, 0, 0, 1)
    e1, _, _ = m_svf(ring_[1::2], f1, blk_[V.VBS + V.FQ], 0, 0, 2)
    check(out_[0::2] == e0 and out_[1::2] == e1 and blk_[V.VBS + V.FMODE] == 2, "voice 1: low-pass on input 1, voice 2: high-pass on input 2, each with its own state")

    # ---- FX: amount, parameter, the four types, bit-exact
    def fx_model(buf, d, typ, thr, bias):
        out = []
        for x in buf:
            x0 = u24(x); b = Acc().mpy(d, x0); b.v <<= 4; b.add24(x0); u = s24(b.lim())
            if typ < 2:
                a = min(u, thr); a = max(a, -thr)
                if typ == 0:
                    ua = u24(a); y0 = Acc().mpy(ua, ua).lim(); c = Acc().mpy(ua, y0)
                    z = Acc.of(ua); z.sub(c); z.asr(); z.add24(ua); out.append(z.lim()); continue
                out.append(u24(a)); continue
            a = u + bias
            if a - thr <= 0:
                if a < -thr: a = -a - 2 * thr
            else: a = 2 * thr - a
            out.append(u24(max(-0x800000, min(0x7FFFFF, a))))
        return out
    for typ in range(4):
        for amt, mod in ((10, 64), (64, 0), (127, 127), (30, 100)):
            ex = mk(blk0, params(0, ACT=1, FXAMT=amt, FXTYPE=typ, **{**DEFAULT, "FXMOD": mod}))
            ring_ = sig(0x400000); blk_, out_ = call_pre(ex, ring_)
            if typ < 3:
                a_ = Acc.of(u24(mod << 16)); b_ = Acc.of(u24(mod << 16)).asr(); a_.asr(); a_.asr(); a_.v += b_.v; a_.add24(0x200000); thr = s24(a_.lim()); bias = 0
            else:
                thr, bias = 0x400000, s24(u24((mod - 64) << 16))
            check(blk_[V.DRVF] == u24(amt << 16) and blk_[V.FXP] == u24(thr) and blk_[V.FXB] == u24(bias) and out_[0::2] == fx_model(ring_[0::2], u24(amt << 16), typ, thr, bias) and out_[1::2] == ring_[1::2],
                  f"FX type {typ} ({['soft', 'hard', 'fold', 'wavefold'][typ]}), amount {amt}, parameter {mod}: threshold {thr:#x}, bias {bias:#x}, 32 frames bit-exact")
    # ---- the order of the chain: FX first, then the filter (then the VCA): out = SVF(FX(x))
    for typ, amt, mod, ftype, filt, mode_ in ((1, 64, 0, 1, 10, 1), (2, 100, 30, 2, -20, 2), (0, 127, 127, 3, 0, 3)):
        res = 40
        ex = mk(blk0, params(0, ACT=1, FXAMT=amt, FXTYPE=typ, FILT=filt, RES=res, FTYPE=ftype, **{**DEFAULT, "FXMOD": mod}))
        ring_ = sig(0x400000); blk_, out_ = call_pre(ex, ring_)
        a_ = Acc.of(u24(mod << 16)); b_ = Acc.of(u24(mod << 16)).asr(); a_.asr(); a_.asr(); a_.v += b_.v; a_.add24(0x200000); thr = s24(a_.lim())
        fxo = fx_model(ring_[0::2], u24(amt << 16), typ, thr, 0)
        exp, lo, ba = m_svf(fxo, blk_[V.FF], blk_[V.FQ], 0, 0, mode_)
        exp_rev, _, _ = m_svf(ring_[0::2], blk_[V.FF], blk_[V.FQ], 0, 0, mode_)
        exp_rev = fx_model(exp_rev, u24(amt << 16), typ, thr, 0)
        check(out_[0::2] == exp and out_[0::2] != exp_rev and blk_[V.LOW0] == lo, f"chain order: FX type {typ} (amount {amt}) then the filter (type {ftype}): out = SVF(FX(x)), bit-exact, not FX(SVF(x))")
    # ---- SC22 FX types: 4 ring mod, 5 comb, 6 chorus (state at X:$3840 + 48 t, buffers in Y)
    def fxs(t_, *words): return ('x', V.FXS + 48 * t_, list(words))
    def run_fx(ftype, amt, mod, ring_, t_=0, xs=(), ys=(), dumps=()):
        ex = mk(blk0, params(t_, ACT=1, FXAMT=amt, FXTYPE=ftype, **{**DEFAULT, "FXMOD": mod}))
        resx, _ = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, ex), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring_)] + list(xs) + list(ys),
                      dumps=[('y', RING, 2 * N), ('x', V.FXS + 48 * t_, 8)] + list(dumps), regs_code=[])
        return resx
    def ring_model(buf, k, m, s, c):
        out = []
        for x in buf:
            b = Acc.of(c); a = Acc.of(s); y1 = b.lim()
            a.mac(k, y1); s = a.lim(); y1 = s
            b.mac(k, y1, neg=True); c = b.lim()
            a = Acc.of(y1); a.v -= 0x7FFFFF << 24; a.asr(); y1 = a.lim()
            a = Acc().mpy(m, y1); a.asl(); a.v += 0x7FFFFF << 24; y1 = a.lim()
            out.append(Acc().mpy(x, y1).lim())
        return out, s, c
    for amt, mod, s0, c0 in ((60, 64, 0x123456, 0x400000), (127, 100, 0, 0), (20, 10, 0x100000, 0x500000)):
        ring_ = sig(0x400000)
        r_ = run_fx(4, amt, mod, ring_, xs=[fxs(0, s0, c0)])
        k = TAB["TF"][mod >> 1]
        c_start = c0 if c0 else 0x600000
        exp, s1, c1 = ring_model(ring_[0::2], k, u24(amt << 16), s0, c_start)
        check(r_[('y', RING)][0::2] == exp and r_[('y', RING)][1::2] == ring_[1::2] and r_[('x', V.FXS)][:2] == [s1, c1],
              f"ring mod, depth {amt}, frequency {mod} (k = TF[{mod >> 1}] = {k:#x}): bit-exact, the oscillator state carried (s {s1:#x}, c {c1:#x}){' (cos starts at $600000)' if not c0 else ''}")
    # the oscillator keeps its amplitude over many blocks (the magic-circle form)
    s_, c_ = 0, 0x600000
    for _ in range(400): _, s_, c_ = ring_model([0] * N, TAB["TF"][40], 0, s_, c_)
    check(0.7 < math.hypot(s24(s_), s24(c_)) / 2 ** 23 < 0.8, f"ring mod oscillator amplitude stable over 400 blocks ({math.hypot(s24(s_), s24(c_)) / 2 ** 23:.3f})")
    def comb_model(buf, base_buf, w, d, m):
        out = []; buf_ = list(base_buf)
        a = Acc.of(u24(m)); b = Acc.of(u24(m)); b.v >>= 3; a.v -= b.v; g = a.lim()
        omg = u24(0x7FFFFF - s24(g))
        rd = (w - d) & 255
        for x in buf:
            yd = buf_[rd]; rd = (rd + 1) & 255
            a = Acc().mpy(omg, x); a.mac(g, yd); o = a.lim()
            buf_[w] = o; w = (w + 1) & 255; out.append(o)
        return out, buf_, w
    for amt, mod, w0, t_ in ((90, 100, 5, 0), (127, 0, 250, 0), (40, 64, 100, 1)):
        ring_ = sig(0x400000)
        init = [u24(rnd.randrange(-0x200000, 0x200000)) for _ in range(256)]
        base = 0x3400 + 256 * t_
        r_ = run_fx(5, amt, mod, ring_, t_=t_, xs=[('x', V.FXS + 48 * t_ + 2, [w0])], ys=[('y', base, init)], dumps=[('y', base, 256)])
        d = 255 - 2 * mod
        exp, buf2, w2 = comb_model(ring_[t_::2], init, w0, d, amt << 16)
        other = ring_[(1 - t_)::2]
        check(r_[('y', RING)][t_::2] == exp and r_[('y', RING)][(1 - t_)::2] == other and r_[('y', base)] == buf2 and r_[('x', V.FXS + 48 * t_)][2] == w2,
              f"comb, voice {t_ + 1}, feedback {amt}, pitch {mod} (delay {d} samples): the output and the 256-word circular buffer bit-exact, write index {w0} -> {w2}")
    def chorus_model(buf, bufin, w, ph, d0, mod, m, base):
        inc = TAB["TLFO"][mod]
        ph = u24(ph + inc)
        a = Acc.of(ph); a.v = abs(a.v); a.asl(); a.v += s24(0x800000) << 24; y1 = a.lim()
        a = Acc().mpy(0x2CCCCC, y1); a.v += 0x466666 << 24; d1 = a.lim()
        if d0 == 0: d0 = d1
        a = Acc.of(d1); a.v -= s24(d0) << 24; a.asr(); a.asr(); a.asr(); a.asr(); a.asr(); step = a.lim()
        out = []; bufw = list(bufin); d = d0
        for x in buf:
            d = u24(d + step)
            di = d >> 14
            f = ((d & 0x3FFF) << 9)
            rd = (w - di) & 511
            x1, x0 = bufw[rd], bufw[(rd - 1) & 511]
            a = Acc.of(x0); a.sub24(x1); a.asr(); y0 = a.lim()
            a = Acc().mpy(f, y0); a.asl(); a.add24(x1); wet = a.lim()
            bufw[w] = x; w = (w + 1) & 511
            a = Acc.of(wet); a.sub24(x); a.asr(); y0 = a.lim()
            a = Acc().mpy(u24(m), y0); a.add24(x); out.append(a.lim())
        return out, bufw, w, ph, d, d1, step
    for amt, mod, w0, ph0, d0, t_ in ((80, 20, 40, 0x123456, 0x400000, 0), (127, 100, 500, 0x7FFFF0, 0, 0), (50, 5, 3, 0x000100, 0x300000, 1)):
        ring_ = sig(0x400000)
        init = [u24(rnd.randrange(-0x300000, 0x300000)) for _ in range(512)]
        base = 0x3600 + 512 * t_
        r_ = run_fx(6, amt, mod, ring_, t_=t_, xs=[('x', V.FXS + 48 * t_ + 3, [w0, ph0, d0])], ys=[('y', base, init)], dumps=[('y', base, 512)])
        exp, buf2, w2, ph2, dend, d1, step = chorus_model(ring_[t_::2], init, w0, ph0, d0, mod, amt << 16, base)
        st = r_[('x', V.FXS + 48 * t_)]
        check(r_[('y', RING)][t_::2] == exp and r_[('y', RING)][(1 - t_)::2] == ring_[(1 - t_)::2] and r_[('y', base)] == buf2 and st[3] == w2 and st[4] == ph2 and st[5] == dend and st[6] == step and st[7] == base,
              f"chorus, voice {t_ + 1}, mix {amt}, rate {mod}: the output and the 512-word input buffer bit-exact, write index {w0} -> {w2}, phase {ph2:#x}, delay ramp {d0:#x} -> {dend:#x} (step {step:#x})")
    r_ = run_fx(6, 100, 30, sig(0x400000), xs=[('x', V.FXS + 5, [0])])
    check(r_[('x', V.FXS)][5] != 0 and r_[('x', V.FXS)][6] == 0, "chorus: the first block starts at the target delay (no ramp from 0)")
    for typ in (4, 5, 6):
        ring_ = sig(); ex = mk(blk0, params(0, ACT=1, FXAMT=0, FXTYPE=typ, **DEFAULT))
        r_ = run_fx(typ, 0, 64, ring_)
        check(r_[('y', RING)] == ring_, f"FX type {typ} with amount 0: bypass")
    ex = mk(blk0, params(0, ACT=1, FXAMT=0, FXTYPE=2, **DEFAULT)); ring_ = sig(); blk_, out_ = call_pre(ex, ring_)
    check(out_ == ring_ and blk_[V.VCAON] == 0, "FX amount 0: bypass, whatever the type")

    # ---- VCA: gain (GAIN 64 = x1; 0 = closed; above: up to +18 dB), bit-exact, with the output saturation above the middle
    def vca_model(buf, g, ginc, cur, sat):
        out = []; gr = cur
        for x in buf:
            gr = Acc.of(gr).add24(ginc).lim()
            b = Acc().mpy(x, gr); b.v <<= 3; out.append(b.lim())
        if sat:
            o2 = []
            for x in out:
                y0 = Acc().mpy(x, x).lim(); c = Acc().mpy(x, y0); z = Acc.of(x); z.sub(c); z.asr(); z.add24(x); o2.append(z.lim())
            out = o2
        return out
    for gain in (0, 20, 63, 65, 100, 127):
        ex = mk(blk0, params(0, ACT=1, **{**DEFAULT, "GAIN": gain}))
        ex[V.GCUR] = 0; ex[V.ACTP] = 1; ex[V.GINIT] = 0
        ring_ = sig(); blk_, out_ = call_pre(ex, ring_)
        t0 = (gain << 14) if gain < 64 else 0x100000 + ((gain - 64) * 7 << 14)
        gt = min(t0, 0x7FFFFF)
        ginc = Acc.of(gt); ginc.sub24(0); ginc.asr(); ginc.asr(); ginc.asr(); ginc.asr(); ginc.asr(); ginc = ginc.lim()
        check(blk_[V.GT] == gt and blk_[V.VCAON] == 1 and blk_[V.GINC] == ginc and out_[0::2] == vca_model(ring_[0::2], gt, ginc, 0, gain > 64),
              f"GAIN {gain}: target {gt:#x} (x{gt / 0x100000:.3f}), ramp from 0, VCA{' + saturation' if gain > 64 else ''} bit-exact")
    ring_ = sig(); blk_, out_ = call_pre(mk(blk0, params(0, ACT=1, **DEFAULT)), ring_)
    check(out_ == ring_ and blk_[V.VCAON] == 0, "GAIN 64, no envelope amount, no tremolo: no VCA, bit-exact bypass")
    # ---- the whole chain: VCA (with its saturation) -> FX -> filter
    for gain, typ, amt, mod, ftype, filt, mode_ in ((100, 1, 64, 0, 1, 10, 1), (30, 2, 100, 30, 2, -20, 2)):
        res = 40
        ex = mk(blk0, params(0, ACT=1, FXAMT=amt, FXTYPE=typ, FILT=filt, RES=res, FTYPE=ftype, **{**DEFAULT, "FXMOD": mod, "GAIN": gain}))
        ex[V.GCUR] = 0; ex[V.ACTP] = 1; ex[V.GINIT] = 0
        ring_ = sig(0x300000); blk_, out_ = call_pre(ex, ring_)
        gt = (gain << 14) if gain < 64 else 0x100000 + ((gain - 64) * 7 << 14)
        v_ = vca_model(ring_[0::2], gt, blk_[V.GINC], 0, gain > 64)
        a_ = Acc.of(u24(mod << 16)); b_ = Acc.of(u24(mod << 16)).asr(); a_.asr(); a_.asr(); a_.v += b_.v; a_.add24(0x200000); thr = s24(a_.lim())
        exp, lo, ba = m_svf(fx_model(v_, u24(amt << 16), typ, thr, 0), blk_[V.FF], blk_[V.FQ], 0, 0, mode_)
        check(out_[0::2] == exp and out_[1::2] == ring_[1::2], f"chain: GAIN {gain} VCA{' + saturation' if gain > 64 else ''} -> FX type {typ} -> filter type {ftype}, bit-exact")
    # ---- gate mode: ADSR over blocks (the envelope itself)
    def run_blocks(n, p0, gate_script, flags=0):
        blk_ = mk(blk0, params(0, ACT=1, **p0))
        envs, stgs = [], []
        for i in range(n):
            if i in gate_script: blk_ = mk(blk_, {V.GATE: gate_script[i][0], V.GNEW: gate_script[i][1], V.VEL: 100})
            ring_ = sig(); blk_, out_ = call_pre(blk_, ring_, flags)
            envs.append(blk_[V.ENV]); stgs.append(blk_[V.STG])
        return envs, stgs
    p = dict(DEFAULT); p.update(ENVA=60, ATK=60, DEC=70, SUS=60, REL=50)
    envs, stgs = run_blocks(60, p, {2: (1, 1), 40: (0, 0)})
    atk = TAB["TATK"][63 - (60 >> 1)]; dk = TAB["TDEC"][64 + (70 >> 1)]; rk = TAB["TDEC"][64 + (50 >> 1)]; sus = 60 << 16
    exp_e, exp_s, e, s = [], [], 0, 0
    for i in range(60):
        if i == 2: e, s = 0, 1
        if i == 40 and 1 <= s <= 3: s = 4
        if s == 1:
            e += atk
            if e >= 0x7FFFFF: e, s = 0x7FFFFF, 2
        elif s == 2:
            e = (Acc().mpy(u24(e - sus), dk).v >> 24) + sus
            if e - sus <= 0x2000: e, s = sus, 3
        elif s == 3: e = sus
        elif s == 4:
            e = Acc().mpy(u24(e), rk).v >> 24
            if e < 0x8000: e, s = 0, 0
        exp_e.append(e); exp_s.append(s)
    check(envs == exp_e and stgs == exp_s, f"the whole ADSR (60 blocks, attack {atk:#x} per block, decay x{dk / 2 ** 23:.4f}, sustain {sus:#x}, release x{rk / 2 ** 23:.4f}) = the model, stage by stage")
    check(stgs.index(1) == 2 and envs[2] == atk and 4 in stgs and envs[59] < envs[41], "attack from block 2 (the table value per block), release after the gate off")
    ex = mk(blk0, {**params(0, ACT=1, **p), V.STG: 2, V.ENV: sus + 0x2010, V.GATE: 1, V.ACTP: 1, V.GINIT: 0})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] == 3 and blk_[V.ENV] == sus, "decay within 0x2000 of the sustain: stage 3 at the sustain value")
    ex = mk(blk0, {**params(0, ACT=1, **p), V.STG: 4, V.ENV: 0x8010, V.ACTP: 1})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] == 0 and blk_[V.ENV] == 0, "release below 1/256: idle, envelope 0")
    ex = mk(blk0, {**params(0, ACT=1, **{**p, "ATK": 0}), V.GNEW: 1, V.GATE: 1})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] in (2, 3) and blk_[V.ENV] >= sus, "no attack time: the envelope jumps to the top and decays")
    # envelope -> VCA: GAIN (bias) + ENVA x ENV x velocity; GAIN 0 = closed unless the envelope / LFO open it
    def env_gt(gain, enva, vel, sus_, lfov=0):
        ex = mk(blk0, {**params(0, ACT=1, **{**DEFAULT, "GAIN": gain, "ENVA": enva, "SUS": sus_, "LFOV": lfov}), V.STG: 3, V.ENV: sus_ << 16, V.GATE: 1, V.ACTP: 1, V.VEL: vel, V.GINIT: 0, V.GCUR: 0x100000})
        return call_pre(ex, sig())[0]
    for gain, enva, vel, sus_ in ((64, 50, 127, 60), (0, 63, 127, 100), (0, 63, 64, 100), (0, 60, 32, 127), (100, 50, 100, 80), (64, -30, 127, 80), (64, -64, 127, 127), (0, -20, 100, 100), (100, -40, 90, 70)):
        blk_ = env_gt(gain, enva, vel, sus_)
        t0 = (gain << 14) if gain < 64 else 0x100000 + ((gain - 64) * 7 << 14)
        b_ = Acc().mpy(u24(enva << 17), u24(sus_ << 16)); c1 = b_.lim()
        b2 = Acc().mpy(c1, u24(vel << 16)); b2.v >>= 3
        a_ = Acc.of(t0); a_.v += b2.v
        gt = a_.lim() if a_.v >= 0 else 0                                          # a negative envelope send closes the VCA at 0 (it never inverts the signal)
        check(blk_[V.GT] == gt and blk_[V.VCAON] == 1, f"VCA = GAIN {gain} + ENVA {enva} x envelope ({sus_ << 16:#x}) x velocity {vel}: target {gt:#x}")
    check(env_gt(0, 0, 127, 100)[V.GT] == 0, "GAIN 0, no envelope amount: the VCA is closed (target 0)")
    # LFO: reverse sawtooth only
    for rate in (0, 60, 127):
        ex = mk(blk0, params(0, ACT=1, **{**DEFAULT, "LRATE": rate}))
        ex[V.PH] = 0x123456
        blk_, _ = call_pre(ex, sig())
        ph = (0x123456 + TAB["TLFO"][rate]) & 0xFFFFFF; phs = s24(ph)
        check(blk_[V.PH] == ph and blk_[V.LV] == u24(min(0x7FFFFF, -phs)), f"LFO (reverse sawtooth) rate {rate}: phase += TLFO[{rate}], value {-phs / 2 ** 23:+.3f}")
    # tremolo (bipolar depth): * (1 - |depth| * (1 - LV') / 2), LV' = LV for depth > 0, -LV for depth < 0
    for depth in (50, 63, -50, -64):
        ex = mk(blk0, params(0, ACT=1, LFOV=depth, **{**DEFAULT, "LRATE": 0}))
        ex[V.PH] = 0x100000
        blk_, out_ = call_pre(ex, sig())
        lv = s24(blk_[V.LV])
        lve = lv if depth > 0 else -lv
        m = Acc.of(0x7FFFFF); m.sub24(u24(lve)); m.asr(); m = m.lim()
        d_ = abs(depth) << 17
        tv = Acc().mpy(u24(min(d_, 0x7FFFFF)), m)
        y0 = Acc.of(0x7FFFFF).sub(tv).lim()
        gt = Acc().mpy(0x100000, y0).lim()
        check(blk_[V.VCAON] == 1 and blk_[V.GT] == gt, f"tremolo: depth {depth:+d} (LV {lv / 2 ** 23:+.2f}): gain target {blk_[V.GT]:#x}")
    check(call_pre(mk(blk0, params(0, ACT=1, LFOV=0, **DEFAULT)), sig())[0][V.VCAON] == 0, "LFO -> VCA 0 = no send (the VCA stage does not run)")

    # ---- mailbox
    def mbox(code, value, tag=1, off=0):
        return mk(blk0, {off + V.MB: (tag << 23) | (code << 16) | (value & 0xFFFF), off + V.MBL: 0})
    blk_, _ = call_pre(mbox(V.P_FILT - 1, -37), sig())
    check(s24(blk_[V.P_FILT]) == -37 and blk_[V.MBL] == (1 << 23 | (V.P_FILT - 1) << 16 | (-37 & 0xFFFF)), "mailbox: code 1 = FILT = -37 (sign-extended 16 bits), the tag remembered")
    for code, name in ((9, "P_FXAMT"), (10, "P_GAIN"), (13, "P_FXTYPE"), (14, "P_FXMOD"), (15, "P_ENVA"), (16, "P_FTYPE")):
        blk_, _ = call_pre(mbox(code, 77), sig()); check(blk_[getattr(V, name)] == 77, f"mailbox: code {code} = {name[2:]}")
    blk_, _ = call_pre(mbox(19, 1), sig()); check(blk_[V.ACT] == 1, "mailbox: code 19 = ACT")
    blk_, _ = call_pre(mbox(17, 1), sig()); check(blk_[V.GATE] == 1, "mailbox: code 17 = GATE")
    blk_, _ = call_pre(mbox(21, 1), sig()); check(blk_[V.GNEW] == 1, "mailbox: code 21 = TRIG")
    blk_, _ = call_pre(mbox(18, 64), sig()); check(blk_[V.NOTE] == 64, "mailbox: code 18 = NOTE")
    bm = mbox(5, 99); bm[V.MBL] = bm[V.MB]
    blk_, _ = call_pre(bm, sig()); check(blk_[V.P_ATK] == 0, "mailbox: the same tag again is ignored")
    blk_, _ = call_pre(mbox(22, 5), sig()); check(blk_[V.P_ATK] == 0 and all(blk_[i] == 0 for i in range(V.ACT + 3, V.VBS) if i not in (V.MB, V.MBL)), "mailbox: a code above 21 is ignored")
    blk_, _ = call_pre(mbox(3, 20, off=V.VBS), sig()); check(s24(blk_[V.VBS + V.P_ENVF]) == 20 and blk_[V.P_ENVF] == 0, "mailbox: the second voice has its own block")

    # ---- the FX returns: the Setup's flag sends the return through the strip; the line input is left alone (stock zeroing), the return is processed
    on = mk(blk0, {**params(0, ACT=1, FILT=-30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
    ring_ = sig()
    blk_, out_ = call_pre(on, ring_, flags=3)
    check(out_[0::2] == [0] * N and out_[1::2] == [0] * N, "flags 3: the line inputs are zeroed by the stock code, our stage does not touch them")
    check(blk_[V.LOW0] == 0 and blk_[V.VBS + V.LOW0] == 0, "flags 3: no filter state written by the ring stage")
    rev, dly = sig(0x200000), sig(0x200000)
    on_ctl, _ = call_pre(on, sig(), flags=3)
    b3, r3, d3 = call_ret(on_ctl, rev, dly, 3, extra=[('x', 0xEC, [3])])
    f0, f1 = TAB["TF"][34], TAB["TF"][25]
    q = b3[V.FQ]; q1 = b3[V.VBS + V.FQ]
    eL, loL, baL = m_svf(rev[0::2], f0, q, 0, 0, 1); eR, loR, baR = m_svf(rev[1::2], f0, q, 0, 0, 1)
    dL, _, _ = m_svf(dly[0::2], f1, q1, 0, 0, 2); dR, _, _ = m_svf(dly[1::2], f1, q1, 0, 0, 2)
    ref2, _ = run(P0, 0x9F, mem=[('x', 0x3A, [N]), ('x', 0xEC, [3]), ('x', V.FLAGS, [3]), ('y', 0x880, [v for pair in zip(eL, eR) for v in pair]), ('y', 0x9C0, [v for pair in zip(dL, dR) for v in pair])],
                  dumps=[('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)], regs_code=[])
    check(r3 == ref2[('y', 0x880)] and d3 == ref2[('y', 0x9C0)] and b3[V.LOW0] == loL and b3[V.LOW1] == loR, "flags 3: reverb (voice 1, low-pass) and delay (voice 2, high-pass) returns filtered per channel, then the stock return chain; four filter states")
    b3, r3, d3 = call_ret(on_ctl, rev, dly, 0)
    ref0, _ = run(P0, 0x9F, mem=[('x', 0x3A, [N]), ('x', 0xEC, [0]), ('x', V.FLAGS, [0]), ('y', 0x880, rev), ('y', 0x9C0, dly)], dumps=[('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)], regs_code=[])
    check(r3 == ref0[('y', 0x880)] and d3 == ref0[('y', 0x9C0)], "flags 0: the returns are not ours (the line inputs carry the voices)")

    # ---- feedback of the FX returns (SC21.1): the capture is taken AFTER vret, and the premix puts it into the ring of the strip's input instead of zeros
    CAP = (0x3A80, 0x3AC0)                                                           # delay, reverb capture (Y, mono)
    def cap_model(buf, k, shift=3):
        return [Acc.of(buf[2 * i]).add24(buf[2 * i + 1]).asl().asl().asl().lim() for i in range(N)]
    on_ctl2, _ = call_pre(on, sig(), flags=3)
    rev, dly = sig(0x200000), sig(0x200000)
    resfb, ranfb = run(P0, dl["vret"], mem=[('x', 0x3A, [N]), ('x', V.VB0, on_ctl2), ('x', V.FLAGS, [3]), ('x', 0xEC, [3]), ('y', 0x880, rev), ('y', 0x9C0, dly)],
                       dumps=[('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N), ('y', CAP[0], N), ('y', CAP[1], N)], regs_code=[])
    eL, _, _ = m_svf(rev[0::2], TAB["TF"][34], on_ctl2[V.FQ], 0, 0, 1); eR, _, _ = m_svf(rev[1::2], TAB["TF"][34], on_ctl2[V.FQ], 0, 0, 1)
    dL, _, _ = m_svf(dly[0::2], TAB["TF"][25], on_ctl2[V.VBS + V.FQ], 0, 0, 2); dR, _, _ = m_svf(dly[1::2], TAB["TF"][25], on_ctl2[V.VBS + V.FQ], 0, 0, 2)
    pr = [v for pair in zip(eL, eR) for v in pair]; pd = [v for pair in zip(dL, dR) for v in pair]
    check(resfb[('y', CAP[1])] == cap_model(pr, 1) and resfb[('y', CAP[0])] == cap_model(pd, 0),
          "the chain vret -> fx_cap: the capture (L + R) x 8 is of the PROCESSED returns (reverb: low-pass of voice 1, delay: high-pass of voice 2)")
    check('pc=00' in ranfb, f"the chain returns through the SC10 returns ({ranfb})")
    resnf, _ = run(P0, dl["vret"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk0), ('x', V.FLAGS, [3]), ('x', 0xEC, [3]), ('y', 0x880, rev), ('y', 0x9C0, dly)],
                   dumps=[('y', CAP[0], N), ('y', CAP[1], N)], regs_code=[])
    check(resnf[('y', CAP[1])] == cap_model(rev, 1) and resnf[('y', CAP[0])] == cap_model(dly, 0), "voices off: the capture is of the plain returns (as SC19.5)")
    resfl, _ = run(P0, dl["vret"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk0), ('x', V.FLAGS, [0]), ('x', 0xEC, [0]), ('y', 0x880, rev), ('y', 0x9C0, dly), ('y', CAP[0], [0x123456] * N), ('y', CAP[1], [0x654321] * N)],
                   dumps=[('y', CAP[0], N), ('y', CAP[1], N)], regs_code=[])
    check(resfl[('y', CAP[0])] == [0x123456] * N and resfl[('y', CAP[1])] == [0x654321] * N, "flags 0: no capture (the buffers are left alone)")
    # the premix: ring <- capture (even words = input 1 <- reverb, odd words = input 2 <- delay)
    capr, capd = sig(0x300000)[:N], sig(0x300000)[:N]
    ringb = sig()
    for flags, want1, want2 in ((0, False, False), (1, True, False), (2, False, True), (3, True, True)):
        blk_, out_ = call_pre(blk0, ringb, flags=flags, extra=[('y', CAP[0], capd), ('y', CAP[1], capr)])
        e1 = capr if want1 else ringb[0::2]
        e2 = capd if want2 else ringb[1::2]
        check(out_[0::2] == e1 and out_[1::2] == e2, f"flags {flags}: input 1 {'<- reverb capture' if want1 else 'untouched'}, input 2 {'<- delay capture' if want2 else 'untouched'}")
    # with the flag a voice does not process the ring (vret does the return): the ring carries the capture as it is
    on_f = mk(blk0, {**params(0, ACT=1, FILT=-30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
    blk_, out_ = call_pre(on_f, ringb, flags=3, extra=[('y', CAP[0], capd), ('y', CAP[1], capr)])
    check(out_[0::2] == capr and out_[1::2] == capd and blk_[V.LOW0] == 0, "flags 3 with both voices on: the ring = the captures, untouched by the voices")
    blk_, out_ = call_pre(on_f, ringb, flags=0, extra=[('y', CAP[0], capd), ('y', CAP[1], capr)])
    e0, _, _ = m_svf(ringb[0::2], TAB["TF"][34], blk_[V.FQ], 0, 0, 1)
    check(out_[0::2] == e0 and blk_[V.FMODE] == 1, "flags 0: the voices process the line inputs as before (the feedback is only for the Setup's returns)")
    # r5 / r1 / the stock registers around the premix
    tramp = [0x0BF080, dl["vpre"]] + T("move r5,x:>$3bd4", "move r1,x:>$3bd5") + [0x00000C]
    Pt = Pbig + [0] * (0x3C00 - len(Pbig)) + tramp if False else P0 + [0] * (0x3C00 - len(P0)) + tramp
    resr, _ = run(Pt, 0x3C00, mem=[('x', 0x3A, [N]), ('x', V.FLAGS, [3]), ('y', V.RING_PTR, [RING]), ('y', RING, sig()), ('y', CAP[0], capd), ('y', CAP[1], capr)],
                  dumps=[('x', 0x3BD4, 2)], regs_code=T("move #>$44,r1", "move #>$99,r5"))
    check(resr[('x', 0x3BD4)] == [RING, 0x44], f"after the premix r5 = the first ring frame ({RING:#x}) and r1 is back ({[hex(x) for x in resr[('x', 0x3BD4)]]})")

    # ---- the registers the FX loops use (r2, r3, r4, m2, m4) are restored by vpre and vret, and the save area does not collide with the return buffer pointer (SC21.4 saved r2 on top of it)
    init5 = T("move #>$77,r2", "move #>$78,r3", "move #>$79,r4", "move #>$7a,m2", "move #>$7b,m4", "move #>$44,r1")
    for name, ftype, flg in (("vpre", 5, 0), ("vpre", 6, 0), ("vret", 5, 1), ("vret", 6, 1), ("vret", 4, 1)):
        trampq = [0x0BF080, dl[name]] + T("move r2,x:>$3c20", "move r3,x:>$3c21", "move r4,x:>$3c22", "move m2,x:>$3c23", "move m4,x:>$3c24") + [0x00000C]
        Pq = P0 + [0] * (0x3C00 - len(P0)) + trampq
        onq, _ = call_pre(mk(blk0, params(0, ACT=1, FXAMT=60, FXTYPE=ftype, FILT=-10, FTYPE=5, **DEFAULT)), sig(), flags=flg)
        resq, _ = run(Pq, 0x3C00, mem=[('x', 0x3A, [N]), ('x', V.VB0, onq), ('x', V.FLAGS, [flg]), ('x', 0xEC, [flg]), ('y', V.RING_PTR, [RING]), ('y', RING, sig()), ('y', 0x880, sig(0x200000)), ('y', 0x9C0, sig(0x200000))],
                      dumps=[('x', 0x3C20, 5)], regs_code=init5)
        check(resq[('x', 0x3C20)] == [0x77, 0x78, 0x79, 0x7A, 0x7B], f"{name} with FX type {ftype}, FTYPE 24 dB: r2 / r3 / r4 / m2 / m4 restored {[hex(x) for x in resq[('x', 0x3C20)]]}")
    # ---- whole core: stack, cost, the synths still hear the clean input
    def sess(image, vals, blocks=24, spmax=True):
        s = Session(image)
        extra = [('y', 0x1000 + i, u24(int(0x300000 * math.sin(i * 0.31)))) for i in range(0x400)] + [('x', V.VB0 + off, v) for off, v in vals.items()]
        res, rans = s.run(blocks=blocks, per_block=True, extra=extra, spmax=spmax, dumps=[('x', V.VB0, 2 * V.VBS), ('x', 0xEB, 0x70)])
        return {(sp_, a_): v for sp_, a_, v in res}, rans
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    avg = lambda v: sum(v) / len(v)
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    gc.collect(); Rp, rp = sess(prev, {})
    gc.collect(); Ro, ro = sess(img, {})
    on_all = {**params(0, ACT=1, FILT=-30, RES=60, FXAMT=40, FXTYPE=5, FTYPE=0, ENVA=50, ENVF=20, LFOF=20, **{**DEFAULT, "GAIN": 90}), **params(1, ACT=1, FILT=25, RES=60, FXAMT=40, FXTYPE=6, FTYPE=6, LFOV=-30, **{**DEFAULT, "GAIN": 100})}
    gc.collect(); Ra, ra = sess(img, on_all)
    print(f"     DSP instructions/block: SC19.9 {avg(ins(rp)):.0f}, SC21 voices off {avg(ins(ro)):.0f}, both voices with filter + FX + VCA + LFO {avg(ins(ra)):.0f}")
    check(avg(ins(ro)) - avg(ins(rp)) < 150, f"cost with the voices off: {avg(ins(ro)) - avg(ins(rp)):+.0f} instructions per block")
    check(avg(ins(ra)) - avg(ins(rp)) < 14000, f"cost with both voices on: +{avg(ins(ra)) - avg(ins(rp)):.0f} instructions per block (~{100 * (avg(ins(ra)) - avg(ins(rp))) / 166000:.1f}% of the ~166000 available)")
    check(spm(ra) <= max(spm(rp), 7), f"stack depth {spm(ra)} (SC19.9 {spm(rp)})")
    check(Ra[('x', 0xEB)] == Rp[('x', 0xEB)], "voice-slot table X:$EB..$15A identical")
    print("SC22 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) else 0)
