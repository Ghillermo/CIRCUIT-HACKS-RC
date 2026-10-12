"""SC20 DSP tests: the VCF / VCA of the MIDI tracks' audio inputs (tools/vcf20_dsp.py), on the dsp56kEmu interpreter with the real core 0 program.

    python tools/emu_sc20_dsp.py SC19.9.bin SC20.bin SC20_manifest.json
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
import vcf20_dsp as V  # noqa: E402
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
    check(len(P0) < 0x3800, f"program ends at P:${len(P0):x} (limit $3800)")
    rnd = random.Random(2020)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(2 * N)]          # interleaved [in1, in2]
    blk0 = [0] * (2 * V.VBS)

    def params(t, **kw):
        names = dict(FILT=V.P_FILT, RES=V.P_RES, ENVF=V.P_ENVF, LFOF=V.P_LFOF, ATK=V.P_ATK, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, DRIVE=V.P_DRIVE, LEVEL=V.P_LEVEL,
                     LRATE=V.P_LRATE, LFOV=V.P_LFOV, LSHAPE=V.P_LSHAPE, KEY=V.P_KEY, VELE=V.P_VELE, VMODE=V.P_VMODE, GATE=V.GATE, NOTE=V.NOTE, ACT=V.ACT, VEL=V.VEL, GNEW=V.GNEW)
        return {V.VBS * t + names[k]: v for k, v in kw.items()}
    DEFAULT = dict(LEVEL=127, DEC=40, SUS=100, REL=40, LRATE=40)

    def mk(blk, extra):
        b = list(blk)
        for off, v in extra.items(): b[off] = v & 0xFFFFFF
        return b

    def call_pre(blk, ring, flags=0, extra=()):
        res, ran = run(P0, dl["vpre"], mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [flags]), ('y', V.RING_PTR, [RING]), ('y', RING, ring)] + list(extra),
                       dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', V.SAV, 16)],
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
    TR = 0x3900
    regs = ["x0", "x1", "y0", "y1", "r0", "r1", "r6", "r7", "n0", "m0"]
    init = T("move #>$a5a5a5,x0", "move #>$5a5a5a,x1", "move #>$123456,y0", "move #>$654321,y1", "move #>$33,r0", "move #>$44,r1", "move #>$55,r6", "move #>$66,r7", "move #>7,n0", "move #>$ffff,m0")
    for name in ("vpre", "vret"):
        tramp = [0x0BF080, dl[name]] + T(*["move %s,x:>$%x" % (r, 0x3B90 + i) for i, r in enumerate(regs)]) + [0x00000C]
        P1 = P0 + [0] * (TR - len(P0)) + tramp
        onx = mk(blk0, {**params(0, ACT=1, FILT=-30, DRIVE=30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
        res, ran = run(P1, TR, mem=[('x', 0x3A, [N]), ('x', V.VB0, onx), ('x', V.FLAGS, [3 if name == "vret" else 0]), ('x', 0xEC, [3 if name == "vret" else 0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig()),
                                    ('y', 0x880, sig()), ('y', 0x9C0, sig())], dumps=[('x', 0x3B90, 10)], regs_code=init)
        got = res[('x', 0x3B90)]
        exp = [0xA5A5A5, 0x5A5A5A, 0x123456, 0x654321, 0x33, 0x44, 0x55, 0x66, 7, 0xFFFF]
        if name == "vret":                                                         # SC10's returns (our tail call) uses x0, y0 and reloads r0, r6, r7 itself: free at that hook
            for k in (0, 2, 4, 6, 7): exp[k] = got[k]
        check(got == exp, f"{name}: the registers are restored {[hex(x) for x in got]}")
    # ---- mode on, defaults: bit-exact bypass
    on = mk(blk0, {**params(0, ACT=1, **DEFAULT), **params(1, ACT=1, **DEFAULT)})
    blk, out = call_pre(on, ring)
    check(out == ring and blk[V.FMODE] == 0 and blk[V.VCAON] == 0, "mode on with the default values: bit-exact bypass (no filter, no saturation, VCA off)")
    check(blk[V.VBS + V.FMODE] == 0 and blk[V.ACTP] == 1, "both voices start; activation remembered")

    # ---- VCF: low-pass / high-pass laws
    def vcf_case(filt, res, **kw):
        ex = mk(blk0, params(0, ACT=1, FILT=filt, RES=res, **DEFAULT, **kw))
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
    ring_, blk_, out_ = vcf_case(0, 40, LFOF=-30, LSHAPE=1)
    check(blk_[V.FMODE] == 1 and blk_[V.FF] == TAB["TF"][33], f"centre + negative LFO depth: low-pass opened to 63 and closed by the LFO (square LFO: index 33, FF {blk_[V.FF]:#x})")
    ring_, blk_, out_ = vcf_case(0, 40, KEY=40, NOTE=72)
    check(blk_[V.FMODE] == 1 and blk_[V.FF] == TAB["TF"][63], "centre + key follow: low-pass at 63 (the key offset opens it, clamped)")
    ring_, blk_, out_ = vcf_case(-40, 40, KEY=-64, NOTE=100)
    off = (-64 * ((100 - 60) << 16)) // (1 << 23)                                  # KEY x (note - 60) / 128 in table steps
    check(blk_[V.FF] == TAB["TF"][max(0, -40 + 64 + off)], f"key follow: note 100, KEY -64 closes the low-pass by {-off} steps")

    # ---- the two inputs are independent
    ex = mk(blk0, {**params(0, ACT=1, FILT=-30, **DEFAULT), **params(1, ACT=1, FILT=25, **DEFAULT)})
    ring_ = sig()
    blk_, out_ = call_pre(ex, ring_)
    f0, f1 = TAB["TF"][34], TAB["TF"][25]
    q0 = blk_[V.FQ]
    e0, _, _ = m_svf(ring_[0::2], f0, q0, 0, 0, 1)
    e1, _, _ = m_svf(ring_[1::2], f1, blk_[V.VBS + V.FQ], 0, 0, 2)
    check(out_[0::2] == e0 and out_[1::2] == e1 and blk_[V.VBS + V.FMODE] == 2, "voice 1: low-pass on input 1, voice 2: high-pass on input 2, each with its own state")

    # ---- drive + saturation
    def sat_model(buf, d):
        out = []
        for x in buf:
            x0 = u24(x); b = Acc().mpy(d, x0); b.v <<= 4; b.add24(x0); u = b.lim()
            y0 = Acc().mpy(u, u).lim(); c = Acc().mpy(u, y0)
            a = Acc.of(u); a.sub(c); a.asr(); a.add24(u); out.append(a.lim())
        return out
    for drive in (10, 64, 127):
        ex = mk(blk0, params(0, ACT=1, DRIVE=drive, **DEFAULT))
        ring_ = sig(0x400000); blk_, out_ = call_pre(ex, ring_)
        check(blk_[V.DRVF] == u24(drive << 16) and out_[0::2] == sat_model(ring_[0::2], u24(drive << 16)) and out_[1::2] == ring_[1::2], f"drive {drive}: u = x (1 + 16 d), soft saturation, bit-exact")
    # ---- VCA: level, bit-exact gain
    for level in (0, 64, 100):
        ex = mk(blk0, params(0, ACT=1, **{**DEFAULT, "LEVEL": level}))
        ring_ = sig(); blk_, out_ = call_pre(ex, ring_)
        g = level << 16
        check(blk_[V.GT] == g and blk_[V.VCAON] == 1 and out_[0::2] == [Acc().mpy(x, g).lim() for x in ring_[0::2]], f"level {level}: gain {g / 2 ** 23:.3f}, VCA bit-exact")
    # ---- gate mode: ADSR over blocks
    def run_blocks(n, p0, gate_script, flags=0):
        blk_ = mk(blk0, params(0, ACT=1, **p0))
        envs, stgs = [], []
        for i in range(n):
            if i in gate_script: blk_ = mk(blk_, {V.GATE: gate_script[i][0], V.GNEW: gate_script[i][1], V.VEL: 100})
            ring_ = sig(); blk_, out_ = call_pre(blk_, ring_, flags)
            envs.append(blk_[V.ENV]); stgs.append(blk_[V.STG])
        return envs, stgs
    p = dict(DEFAULT); p.update(VMODE=1, ATK=60, DEC=70, SUS=60, REL=50)
    envs, stgs = run_blocks(60, p, {2: (1, 1), 40: (0, 0)})
    atk = TAB["TATK"][63 - (60 >> 1)]; dk = TAB["TDEC"][64 + (70 >> 1)]; rk = TAB["TDEC"][64 + (50 >> 1)]; sus = 60 << 16
    exp_e, exp_s, e, s = [], [], 0, 0
    for i in range(60):
        if i == 2: e, s = 0, 1                                                   # GNEW with an attack time
        if i == 40 and 1 <= s <= 3: s = 4                                        # gate off
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
    # stage transitions, from injected states: decay -> sustain, release -> idle
    ex = mk(blk0, {**params(0, ACT=1, **p), V.STG: 2, V.ENV: sus + 0x2010, V.GATE: 1, V.ACTP: 1, V.GINIT: 0})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] == 3 and blk_[V.ENV] == sus, "decay within 0x2000 of the sustain: stage 3 at the sustain value")
    ex = mk(blk0, {**params(0, ACT=1, **p), V.STG: 4, V.ENV: 0x8010, V.ACTP: 1})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] == 0 and blk_[V.ENV] == 0, "release below 1/256: idle, envelope 0")
    ex = mk(blk0, {**params(0, ACT=1, **{**p, "ATK": 0}), V.GNEW: 1, V.GATE: 1})
    blk_, _ = call_pre(ex, sig())
    check(blk_[V.STG] in (2, 3) and blk_[V.ENV] >= sus, "no attack time: the envelope jumps to the top and decays")
    # gate mode: the VCA gain follows level x envelope, ramped inside the block (the ramp start = the previous target)
    ex = mk(blk0, {**params(0, ACT=1, **p), V.STG: 3, V.ENV: sus, V.GATE: 1, V.ACTP: 1, V.GCUR: 0x100000})
    ring_ = sig(); blk_, out_ = call_pre(ex, ring_)
    gt = Acc().mpy(0x7FFFFF, sus).lim()
    ginc = Acc.of(gt); ginc.sub24(0x100000); ginc.asr(); ginc.asr(); ginc.asr(); ginc.asr(); ginc.asr(); ginc = ginc.lim()
    exp = []; g = 0x100000
    for x in ring_[0::2]:
        g = Acc.of(g).add24(ginc).lim(); exp.append(Acc().mpy(x, g).lim())
    check(blk_[V.GT] == gt and blk_[V.GINC] == ginc and out_[0::2] == exp and blk_[V.GCUR] == gt, f"gate mode: target {gt:#x}, ramp {ginc:#x} per frame, 32 frames bit-exact, the next block starts from the target")
    # LFO: the four shapes
    for shape in range(4):
        ex = mk(blk0, params(0, ACT=1, LSHAPE=shape, **{**DEFAULT, "LRATE": 60}))
        ex[V.PH] = 0x123456
        blk_, _ = call_pre(ex, sig())
        ph = (0x123456 + TAB["TLFO"][60]) & 0xFFFFFF; phs = s24(ph)
        want = {0: u24(max(-0x800000, min(0x7FFFFF, 2 * abs(phs) - 0x800000))), 1: 0x7FFFFF if phs >= 0 else 0x800000, 2: ph, 3: u24(-phs)}[shape]
        check(blk_[V.PH] == ph and blk_[V.LV] == want, f"LFO shape {shape}: phase += TLFO[60], value {s24(want) / 2 ** 23:+.3f}")
    # tremolo
    ex = mk(blk0, params(0, ACT=1, LFOV=100, LSHAPE=1, **{**DEFAULT, "LRATE": 0}))
    ex[V.PH] = 0x100000
    blk_, out_ = call_pre(ex, sig())
    lv = blk_[V.LV]
    m = Acc.of(0x7FFFFF); m.sub24(lv); m.asr(); m = m.lim()
    tv = Acc().mpy(u24(100 << 16), m)
    y0 = Acc.of(0x7FFFFF).sub(tv).lim()
    gt = Acc().mpy(0x7FFFFF, y0).lim()
    check(blk_[V.VCAON] == 1 and blk_[V.GT] == gt, f"tremolo: depth 100 on a square LFO (LV {s24(lv) / 2 ** 23:+.2f}): gain target {blk_[V.GT]:#x}")
    # velocity -> level
    ex = mk(blk0, params(0, ACT=1, VELE=64, **DEFAULT)); ex[V.VEL] = 32
    blk_, _ = call_pre(ex, sig())
    k = 64 << 16; f = Acc.of(0x7FFFFF); f.sub24(k); f.mac(k, u24(32 << 16)); f = f.lim()
    check(blk_[V.VCAON] == 1 and blk_[V.GT] == Acc().mpy(0x7FFFFF, f).lim(), f"velocity 32 with VELE 64: level x {s24(f) / 2 ** 23:.3f}")

    # ---- mailbox
    def mbox(code, value, tag=1, off=0):
        return mk(blk0, {off + V.MB: (tag << 23) | (code << 16) | (value & 0xFFFF), off + V.MBL: 0})
    blk_, _ = call_pre(mbox(V.P_FILT - 1, -37), sig())
    check(s24(blk_[V.P_FILT]) == -37 and blk_[V.MBL] == (1 << 23 | (V.P_FILT - 1) << 16 | (-37 & 0xFFFF)), "mailbox: code 1 = FILT = -37 (sign-extended 16 bits), the tag remembered")
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
    ref, _ = run(P0, 0x9F, mem=[('x', 0x3A, [N]), ('x', 0xEC, [3]), ('x', V.FLAGS, [3]), ('y', 0x880, rev), ('y', 0x9C0, dly)], dumps=[('y', 0x880, 2 * N), ('y', 0x9C0, 2 * N)], regs_code=[])
    on_ctl, _ = call_pre(on, sig(), flags=3)                                     # the control of the voices runs in vpre; vret only uses its results
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
    on_all = {**params(0, ACT=1, FILT=-30, RES=60, DRIVE=40, **{**DEFAULT, "LEVEL": 90}, VMODE=1, LFOF=20, ENVF=20), **params(1, ACT=1, FILT=25, RES=60, DRIVE=40, **{**DEFAULT, "LEVEL": 90}, LFOV=50)}
    gc.collect(); Ra, ra = sess(img, on_all)
    print(f"     DSP instructions/block: SC19.9 {avg(ins(rp)):.0f}, SC20 voices off {avg(ins(ro)):.0f}, both voices with VCF + drive + VCA + LFO {avg(ins(ra)):.0f}")
    check(avg(ins(ro)) - avg(ins(rp)) < 150, f"cost with the voices off: {avg(ins(ro)) - avg(ins(rp)):+.0f} instructions per block")
    check(avg(ins(ra)) - avg(ins(rp)) < 12000, f"cost with both voices on: +{avg(ins(ra)) - avg(ins(rp)):.0f} instructions per block (~{100 * (avg(ins(ra)) - avg(ins(rp))) / 166000:.1f}% of the ~166000 available)")
    check(spm(ra) <= max(spm(rp), 7), f"stack depth {spm(ra)} (SC19.9 {spm(rp)})")
    check(Ra[('x', 0xEB)] == Rp[('x', 0xEB)], "voice-slot table X:$EB..$15A identical")
    print("SC20 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), Path(a[2]).read_bytes(), json.loads(Path(a[3]).read_text())) else 0)
