"""SC24 DSP tests (the real core-0 program on the DSP emulator): the 7-bit mailbox, the dual oscillator and its interactions, the per-voice chain order, the paraphonic notes.

    python tools/emu_sc24_dsp.py SC24.bin SC24_manifest.json SC23.6.bin SC23.6_manifest.json
  * mailbox: codes 32..39 land in the OSC2 block, code 14 = the note of the second oscillator, ACT = act | route << 8 | dual << 9 is split, BITSYNC (code 37) = zone + position, the old codes as before;
  * route 0 (VCA, FX, filter) is the old chain bit for bit (against SC23.6); route 1 (filter, VCA, FX) differs as the order says;
  * one oscillator (dual off): the same samples as SC23.6; dual with MIX = 0 and no interaction: the same samples again; MIX = 127: the second oscillator alone at the pitch of NOTE2 + TUNE2 + FINE2;
    MIX = 64: both pitches; ring: the sum and the difference of the two frequencies; FM: sidebands of OSC1 spaced by the frequency of OSC2; bitwise: xor / or / and / nor / nand of two identical oscillators;
    soft sync: the slave reverses its direction at every N-th cycle of the master (counted against a model of the master's phase);
  * the key follow of the filter cutoff takes the mean of the two notes; the cost of the dual oscillator.
One mailbox word per voice and block: every message below goes in a block of its own.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import vcf21_dsp as V  # noqa: E402
import vcf21 as A  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.OSC, V.VFF = False, True, True, True, True, 0x4000, True, True
V.use_osc3(); V.use_gaterel(); V.use_sinefix(); V.use_gatefix(); V.use_typezones(); V.use_dual()
A.FTYPE_N = A.FXTYPE_N = 7
A.use_osc3(); A.use_neutral()

N, RING = 32, 0x1000
OSB, OS2 = V.OSB0, V.OS2B0
NAMES = ("FILT", "RES", "ENVF", "LFOF", "ATK", "DEC", "SUS", "REL", "FXAMT", "GAIN", "LRATE", "LFOV", "FXTYPE", "FXMOD", "ENVA", "FTYPE")


def main(img, man, prev, prev_man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
    dlp = {k: int(v, 16) for k, v in prev_man["report"]["sc16"]["dsp_labels"].items()}
    prog = lambda im: (lambda b: [int.from_bytes(b[i:i + 3], 'big') for i in range(0, len(b), 3)])(dsp_program(im))
    P0, PP = prog(img), prog(prev)
    off = dict(zip(NAMES, range(2, 18)))
    neutral = {n: A.DEFAULTS[i] for i, n in enumerate(NAMES)}
    check(len(P0) <= 0x4000, f"the DSP program fits in the P RAM ({len(P0):#x} words, {0x4000 - len(P0)} free)")

    class St:                                                                 # the DSP memory the program works on
        def __init__(self, act, note=60, **kw):
            b = [0] * (2 * V.VBS)
            for n, v in {**neutral, **kw}.items(): b[off[n]] = v & 0xFFFFFF
            b[V.ACT], b[V.NOTE] = act, note
            self.blk, self.osb, self.os2 = b, [0] * 96, [0] * 96

    def step(st, msg=None, ring=None, prog_=None, labels=None, dual=True):
        """one block of vpre with at most one mailbox message (voice, code, value); returns the output of input 1"""
        if msg:
            v, code, val = msg
            tag = ((st.blk[V.VBS * v + 1] >> 23) & 1) ^ 1
            st.blk[V.VBS * v] = (tag << 23) | (code << 16) | (val & 0xFFFF)
        mem = [('x', 0x3A, [N]), ('x', V.VB0, st.blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, ring or [0] * (2 * N)), ('x', OSB, st.osb)]
        dumps = [('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 96)]
        if dual: mem.append(('x', OS2, st.os2)); dumps.append(('x', OS2, 96))
        res, ran = run(prog_ or P0, (labels or dl)["vpre"], mem=mem, dumps=dumps, regs_code=[])
        assert 'pc=00' in ran, ran
        st.blk, st.osb = res[('x', V.VB0)], res[('x', OSB)]
        if dual: st.os2 = res[('x', OS2)]
        return [s24(x) for x in res[('y', RING)][0::2]]

    def send(st, *msgs, **kw):
        for m in msgs: step(st, m, **kw)

    # ---------------------------------------------------------------- mailbox
    st = St(1)
    send(st, (0, 19, 2 | (1 << 8) | (1 << 9)))
    check(st.blk[V.ACT] == 2 and st.osb[V.DFLAGS_OFF] == 3, f"ACT = 2 | route | dual: ACT slot {st.blk[V.ACT]}, DFLAGS {st.osb[V.DFLAGS_OFF]}")
    send(st, (0, 19, 1))
    check(st.blk[V.ACT] == 1 and st.osb[V.DFLAGS_OFF] == 0, f"ACT = 1 clears the flags ({st.blk[V.ACT]}, {st.osb[V.DFLAGS_OFF]})")
    send(st, (0, 19, 2 | (1 << 9)))
    check(st.osb[V.DFLAGS_OFF] == 2, "dual alone")
    send(st, (0, 13, 60))
    fxmod = st.blk[off["FXMOD"]]
    send(st, (0, 14, 73))
    check(st.osb[V.NOTE2_OFF] == 73 and st.blk[off["FXMOD"]] == fxmod, f"code 14 = NOTE2 ({st.osb[V.NOTE2_OFF]}), FXMOD untouched ({st.blk[off['FXMOD']]} = {fxmod})")
    for code, val in ((32, -5), (33, 7), (34, 40), (35, 50), (36, 90), (38, 33), (39, 120)):
        send(st, (0, code, val))
        check(s24(st.os2[code - 32]) == val, f"code {code} -> OSC2 block +{code - 32}: {s24(st.os2[code - 32])}")
    send(st, (0, 37, 54))
    check(st.os2[5] == (7 * 54) >> 7 == 2 and st.os2[8] == (7 * 54) & 127, f"BITSYNC 54: zone {st.os2[5]}, position {st.os2[8]}")
    send(st, (1, 36, 11), (1, 32, 3))
    check(st.os2[48 + 4] == 11 and st.os2[48 + 0] == 3 and st.os2[4] == 90, "voice 2 has its own OSC2 block (+48)")
    send(st, (0, 1, -5), (0, 22, 4), (0, 12, 9))
    check(s24(st.blk[off["FILT"]]) == -5 and st.osb[0] == 4 and st.blk[off["LFOV"]] == 9, "old codes (FILT, TUNE, LFOV) as before")

    # ---------------------------------------------------------------- the line input chain: route 0 = the old chain bit for bit
    tone = lambda i, f=1000, a=0x300000: [u24(int(a * math.sin(2 * math.pi * f * (i * N + k) / 48000))) for k in range(N) for _ in (0, 1)]
    def run_line(prog_, labels, dual, route, kw, msgs0=(), n=18):
        st = St(1, 60, **kw)
        q = [(0, 19, 1 | (route << 8))] + list(msgs0)
        outs = []
        for i in range(n):
            if i == len(q) + 1: st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 100
            outs.append(step(st, q[i] if i < len(q) else None, tone(i), prog_, labels, dual))
        return outs
    for name, kw, types in (("FX hard + LP filter", dict(FXAMT=60, FILT=-20, GAIN=70, ENVA=63), (1, 1)), ("saturating gain + FX fold", dict(FXAMT=40, GAIN=100, ENVA=63), (2, 0)),
                            ("plain", dict(ENVA=63), (0, 0))):
        ms = [(0, 13, types[0] * 18 + 3), (0, 16, types[1] * 18 + 3)]
        a0 = run_line(P0, dl, True, 0, kw, ms)
        b0 = run_line(PP, dlp, False, 0, kw, ms)
        check(a0 == b0, f"route 0 = the SC23.6 chain bit for bit ({name}; peak {max(abs(x) for b in a0 for x in b):#x})")
    kw = dict(FXAMT=127, GAIN=64, ENVA=63, FILT=-40)
    ms = [(0, 13, 1 * 18 + 3), (0, 16, 1 * 18 + 3)]
    o0 = run_line(P0, dl, True, 0, kw, ms, n=22)
    o1 = run_line(P0, dl, True, 1, kw, ms, n=22)
    rms = lambda outs: math.sqrt(sum(x * x for b in outs[12:] for x in b) / (len(outs[12:]) * N))
    check(o0 != o1 and rms(o1) > 3 * rms(o0), f"route 1 (filter, VCA, FX) differs: the hard clip after the low-pass keeps the level (rms {rms(o1):.0f} against {rms(o0):.0f})")

    # ---------------------------------------------------------------- oscillators
    def osc_run(n=56, note=60, note2=60, msgs=(), dual=True, **kw):
        """the messages go one per block (DUAL flag, NOTE2, then the others); returns the outputs and the state; k0 = the first block to analyse"""
        st = St(1, note, **kw)                                                # the line input: the oscillators start together with the last message (the ACT one)
        q = [(0, 14, note2)] + list(msgs) + [(0, 19, 2 | ((1 << 9) if dual else 0))]
        outs = []
        for i in range(n):
            if i == len(q): st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 127
            outs.append(step(st, q[i] if i < len(q) else None))
        return outs, st, len(q) + 6
    def fit(sig, f, n0):                                                      # amplitude of the component at f (least squares of A sin + B cos)
        w = 2 * math.pi * f / 48000
        sa = sum(x * math.sin(w * (n0 + j)) for j, x in enumerate(sig)) * 2 / len(sig)
        sb = sum(x * math.cos(w * (n0 + j)) for j, x in enumerate(sig)) * 2 / len(sig)
        return int(math.hypot(sa, sb))
    fr = lambda note: 440 * 2 ** ((note - 69) / 12)

    # one oscillator: the same as SC23.6
    st0 = St(2, 60)
    q0 = [(0, 19, 2)]
    sp = []
    for i in range(30):
        if i == 2: st0.blk[V.GATE], st0.blk[V.GNEW], st0.blk[V.VEL] = 1, 1, 127
        sp.append(step(st0, q0[i] if i < len(q0) else None, None, PP, dlp, False))
    st1 = St(2, 60)
    so = []
    for i in range(30):
        if i == 2: st1.blk[V.GATE], st1.blk[V.GNEW], st1.blk[V.VEL] = 1, 1, 127
        so.append(step(st1, q0[i] if i < len(q0) else None))
    check(so == sp, "one oscillator (dual off, route 0): the same samples as SC23.6")
    # two oscillators with MIX = 0 and no interaction: OSC1 alone, the same again (the gate opens in the third block in both runs)
    st2 = St(2, 60)
    q2 = [(0, 19, 2 | (1 << 9)), (0, 14, 60), (0, 36, 0)]
    sd = []
    for i in range(30):
        if i == 2: st2.blk[V.GATE], st2.blk[V.GNEW], st2.blk[V.VEL] = 1, 1, 127
        sd.append(step(st2, q2[i] if i < len(q2) else None))
    check(sd[4:] == sp[4:], "two oscillators with MIX = 0 and no interaction: OSC1 alone, the same samples")

    # MIX = 127: the second oscillator alone at NOTE2 + TUNE2 + FINE2
    for note2, tune2, fine2 in ((60, 0, 0), (67, 0, 0), (60, 7, 0), (60, 0, 32), (72, -12, 0)):
        outs, _, k0 = osc_run(56, 48, note2, [(0, 36, 127), (0, 32, tune2), (0, 33, fine2), (0, 35, 50)])
        s = [x for b in outs[k0:] for x in b]; n0 = k0 * N
        f = fr(note2 + tune2) * 2 ** (fine2 / 128 / 12)
        a2 = fit(s, f, n0); a1 = fit(s, fr(48), n0)
        check(a2 > 0x100000 and a1 < 0.12 * a2, f"MIX 127, NOTE2 {note2} TUNE2 {tune2} FINE2 {fine2}: {f:.1f} Hz present ({a2:#x}), OSC1's {fr(48):.1f} Hz absent ({a1:#x})")
    # MIX = 64: both
    outs, _, k0 = osc_run(56, 55, 62, [(0, 36, 64), (0, 35, 50)])
    s = [x for b in outs[k0:] for x in b]; n0 = k0 * N
    a1, a2 = fit(s, fr(55), n0), fit(s, fr(62), n0)
    check(abs(a1 - a2) < 0.1 * a1 and a1 > 0x100000, f"MIX 64: both pitches at about the same level ({fr(55):.1f} Hz {a1:#x}, {fr(62):.1f} Hz {a2:#x})")

    # ring modulation: MIX 0, RING 127: 2 o1 o2 = the difference and the sum frequencies
    outs, _, k0 = osc_run(56, 60, 67, [(0, 36, 0), (0, 39, 127), (0, 35, 50)])
    s = [x for b in outs[k0:] for x in b]; n0 = k0 * N
    f1, f2 = fr(60), fr(67)
    ad, asu, a1, a2 = fit(s, f2 - f1, n0), fit(s, f1 + f2, n0), fit(s, f1, n0), fit(s, f2, n0)
    check(ad > 0x80000 and asu > 0x80000 and a1 < 0.1 * ad and a2 < 0.1 * ad, f"ring: difference {f2 - f1:.0f} Hz {ad:#x}, sum {f1 + f2:.0f} Hz {asu:#x}, the carriers {a1:#x} / {a2:#x} are gone")

    # FM: OSC2 modulates the phase of OSC1: sidebands f1 +- f2
    f1, f2 = fr(60), fr(67)
    outs_f, _, k0 = osc_run(64, 60, 67, [(0, 36, 0), (0, 38, 60), (0, 35, 50)])
    outs_n, _, _ = osc_run(64, 60, 67, [(0, 36, 0), (0, 38, 0), (0, 35, 50)])
    sf, sn = [x for b in outs_f[k0:] for x in b], [x for b in outs_n[k0:] for x in b]; n0 = k0 * N
    sb_f = fit(sf, f1 + f2, n0) + fit(sf, abs(f1 - f2), n0)
    sb_n = fit(sn, f1 + f2, n0) + fit(sn, abs(f1 - f2), n0)
    check(sb_f > 0x100000 and sb_n < 0.25 * sb_f and fit(sf, f1, n0) < fit(sn, f1, n0), f"FM 60: sidebands {f1 - f2:.0f} / {f1 + f2:.0f} Hz {sb_f:#x} (without FM {sb_n:#x}), the carrier is weaker ({fit(sf, f1, n0):#x} < {fit(sn, f1, n0):#x})")

    # bitwise: two identical oscillators: o1 = o2 = o; the position w close to 1
    ref, _, k0 = osc_run(30, 60, 60, [(0, 36, 64), (0, 35, 50)])
    for zone, p, name in ((2, 54, "xor"), (3, 72, "or"), (4, 91, "nor"), (5, 109, "and"), (6, 127, "nand")):
        w = ((7 * p) & 127) / 127
        outs, _, _ = osc_run(30, 60, 60, [(0, 36, 64), (0, 35, 50), (0, 37, p)])
        a_ref = max(abs(x) for b in ref[k0:] for x in b)
        pk = max(abs(x) for b in outs[k0:] for x in b)
        dot = sum(x * y for b1, b2 in zip(outs[k0:], ref[k0:]) for x, y in zip(b1, b2))
        e = {2: abs(1 - w), 3: 1.0, 4: abs(1 - 2 * w), 5: 1.0, 6: abs(1 - 2 * w)}[zone]
        ok = abs(pk / a_ref - e) < 0.06 and (dot > 0) == (zone in (2, 3, 5))
        check(ok, f"bitwise {name} (zone {zone}, w {w:.2f}) of two identical oscillators: level {pk / a_ref:.3f} of the plain mix (expected {e:.3f}), sign {'+' if dot > 0 else '-'}")

    # soft sync: the slave reverses every N-th cycle of the master
    for p in (19, 36, 27):
        f = (7 * p) & 127; n_exp = 1 + (f >> 4)
        st = St(1, 60)
        q = [(0, 14, 72), (0, 36, 127), (0, 35, 50), (0, 37, p), (0, 19, 2 | (1 << 9))]
        for i in range(len(q) - 1): step(st, q[i])
        st.blk[V.GATE], st.blk[V.GNEW], st.blk[V.VEL] = 1, 1, 127
        phase1 = ((st.osb[10] + (1 << 23)) % (1 << 24)) - (1 << 23); flips = cnt = 0
        for i in range(40):
            step(st, q[-1] if i == 0 else None)                               # the oscillators start in this block, the zone is active from its first sample
            inc1 = st.osb[11]
            for k in range(N):                                                # the model of the master's phase: the signed 24-bit wrap of the sum
                nph = ((phase1 + inc1 + (1 << 23)) % (1 << 24)) - (1 << 23)
                if nph < phase1:
                    cnt += 1
                    if cnt >= n_exp: cnt = 0; flips += 1
                phase1 = nph
        check(st.os2[21] == n_exp and st.os2[20] == flips % 2 and st.os2[22] == cnt,
              f"sync zone, position {f}: period {st.os2[21]} (model {n_exp}), {flips} reversals -> direction {st.os2[20]} (model {flips % 2}), counter {st.os2[22]} (model {cnt})")
    st = St(1, 60)
    send(st, (0, 14, 72), (0, 36, 127), (0, 37, 0), (0, 19, 2 | (1 << 9)))
    for i in range(30): step(st)
    check(st.os2[20] == 0 and st.os2[22] == 0, "zone 0 (none): the slave never reverses")

    # the key follow takes the mean of the two notes
    tf = lambda idx: P0[dl["TF"] + idx]
    idx_of = lambda v: next(i for i in range(64) if tf(i) == v)
    def ff(n1, n2, dualflag):
        st = St(1, n1, FILT=0)
        send(st, (0, 19, 1 | (dualflag << 9)), (0, 14, n2), (0, 16, 36))
        step(st)
        return idx_of(st.blk[V.FF])
    i_mean, i_c, i_single, i_single_c = ff(48, 72, 1), ff(60, 60, 1), ff(60, 72, 0), ff(60, 60, 0)
    check(i_mean == i_c == i_single_c == 32 and i_single == 32, f"key follow, notes 48 / 72 (mean 60): index {i_mean} = the centre {i_c}; single oscillator ignores NOTE2: {i_single}")
    check(ff(60, 72, 1) > 32 and ff(72, 48, 0) > 32, f"key follow, notes 60 / 72: {ff(60, 72, 1)} above the centre; NOTE alone (72): {ff(72, 48, 0)}")

    # ---------------------------------------------------------------- the cost
    from dsp_session import Session
    def sess(image, vals, xextra=()):
        ss = Session(image)
        extra = [('y', 0x1000 + i, u24(int(0x300000 * math.sin(i * 0.31)))) for i in range(0x400)] + [('x', V.VB0 + o_, v) for o_, v in vals.items()] + list(xextra)
        res, rans = ss.run(blocks=24, per_block=True, extra=extra, spmax=True, dumps=[('x', V.VB0, 2 * V.VBS)])
        return rans
    ins = lambda rans: [int(x.split('ins=')[1].split()[0]) for x in rans if x.startswith('RAN')][2:]
    spm = lambda rans: int([x for x in rans if x.startswith('SPMAX')][0].split()[1])
    avg = lambda v: sum(v) / len(v)
    both = {}
    for t in (0, 1):
        for n_, v in {**neutral, "NOTE": 60, "GATE": 1, "ACT": 2, "VEL": 100, "GNEW": 1}.items():
            o_ = {**off, "GATE": V.GATE, "NOTE": V.NOTE, "ACT": V.ACT, "VEL": V.VEL, "GNEW": V.GNEW}[n_]
            both[V.VBS * t + o_] = v & 0xFFFFFF
    dualx = []
    for t in (0, 1):
        dualx += [('x', OSB + 48 * t + V.DFLAGS_OFF, 3), ('x', OSB + 48 * t + V.NOTE2_OFF, 67), ('x', OS2 + 48 * t + 4, 64), ('x', OS2 + 48 * t + 6, 40), ('x', OS2 + 48 * t + 7, 40),
                  ('x', OS2 + 48 * t + 5, 1), ('x', OS2 + 48 * t + 8, 60), ('x', OS2 + 48 * t + 3, 50)]
    rp, ro, rd = sess(prev, both), sess(img, both), sess(img, both, dualx)
    print(f"     DSP instructions/block, both voices on the oscillator: SC23.6 {avg(ins(rp)):.0f}, SC24 one oscillator {avg(ins(ro)):.0f}, SC24 two oscillators + FM + ring + sync {avg(ins(rd)):.0f}")
    check(abs(avg(ins(ro)) - avg(ins(rp))) < 500 and spm(ro) <= max(spm(rp), 7), f"one oscillator: cost {avg(ins(ro)) - avg(ins(rp)):+.0f} instructions per block, stack {spm(ro)} (SC23.6: {spm(rp)})")
    check(avg(ins(rd)) - avg(ins(rp)) < 30000 and spm(rd) <= max(spm(rp), 7), f"two oscillators on both tracks: +{avg(ins(rd)) - avg(ins(rp)):.0f} instructions per block (~{100 * (avg(ins(rd)) - avg(ins(rp))) / 166000:.1f}% of the ~166000 budget), stack {spm(rd)}")
    print("SC24 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
