"""SC46.7 DSP test (vcf21_dsp.use_smstereo, use_oscsub): the sample mode of MIDI 1 / 2 in stereo.

    python tools/emu_smstereo_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC46.6 / Beta 3.23)

On the dsp56kEmu interpreter with each build's real core-0 program, vpre called once a block (MIDI 1's voice in the sample mode, two samples in
the external Y memory, the sample table pointing at them):
  * WAVE 0 (mono): the ring and the OSC1 block as PREV's, bit for bit, over four blocks;
  * WAVE 100, no filter: a new note on sample N takes N + 1 as the right (63 -> 0), the length = the shorter one; each block the ring = the mid
    (L + R) / 2 and the granular's side buffer (SOUT, its half RDOFS) = the side (L - R) / 2 x WAVE << 16, both against a bit-exact model of the
    two interpolated reads; the capture (a negative sample) stays mono;
  * WAVE 100 with the low-pass (DJ filter left): the ring = the engine's SVF over the mid (its state), the side = the same SVF over the side with
    a state of its own (X:$3340), against the model;
  * the program ends at or below P:$3FFF.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_fm_dsp as F0  # noqa: E402  (sets vcf21_dsp's constants)
from emu_masterfx_dsp import s24, u24  # noqa: E402
import granular_dsp as GD  # noqa: E402
V = F0.V
N, RING, OSB = F0.N, F0.RING, F0.OSB
s56, lim, mpy = F0.s56, F0.lim, F0.mpy
SMP_L, SMP_R, SMP_C = 0x40000, 0x48000, 0x50000          # Y: the left sample, the right one, a third
TAB = V.SM_TAB


def interp(Y, start, pos, frac, n4, y1, nfr):
    """the engine's sample loop: (samples, the next position, the next fraction)"""
    out, r4, x1 = [], start + pos, frac
    for _ in range(nfr):
        s0, s1 = Y(r4), Y(r4 + 1)
        y0 = lim(s56((s24(s1) << 24) - (s24(s0) << 24)))
        a = s56((s24(s0) << 24) + mpy(y0, x1))
        out.append(lim(a))
        b = (x1 + y1) & 0xFFFFFF
        if b & 0x800000: b &= 0x7FFFFF; r4 += 1
        x1 = b; r4 += n4
    return out, r4 - start, x1


def svf_lp(xs, low, band, ff, fq):
    """the engine's 12 dB SVF (the LP tail) over xs: (outputs, low, band) as the DSP leaves them"""
    a = s24(low) << 24; x0 = band; out = []
    for v in xs:
        a = s56(a + mpy(ff, x0))
        b = s56((s24(v) << 24) >> 1)
        b = s56(b - a); b = s56(b - mpy(x0, fq)); b = s56(b - mpy(x0, fq))
        x1 = lim(b)
        b = s56((s24(x0) << 24) + mpy(x1, ff)); x0 = lim(b)
        out.append(lim(s56(a << 1)))
    return out, lim(a), x0


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")
    LL, LR, LC = 900, 700, 800
    ydat = {}
    for i in range(LL + 2): ydat[SMP_L + i] = u24(int(0x500000 * ((i * 37 % 200) - 100) / 100)) & 0xFFFF00
    for i in range(LR + 2): ydat[SMP_R + i] = u24(int(0x300000 * ((i * 53 % 160) - 80) / 80)) & 0xFFFF00
    for i in range(LC + 2): ydat[SMP_C + i] = u24(int(0x200000 * ((i * 11 % 90) - 45) / 45)) & 0xFFFF00
    Y = lambda addr: ydat.get(addr, 0)
    def table(n_left):                                                     # entries: sample n_left -> L, n_left + 1 -> R, 7 -> the third
        t = {}
        for k, (s_, l_) in ((n_left, (SMP_L, LL)), ((n_left + 1) & 63, (SMP_R, LR)), (7, (SMP_C, LC))):
            t[TAB + 4 * k], t[TAB + 4 * k + 1] = s_, l_
        return [('x', a_, [v_]) for a_, v_ in t.items()]
    def go(which, n_left, wave, blocks=4, filt=0, sample=None):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k, v in dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=60, ACT=3).items():
            blk[dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT)[k]] = v
        blk[V.P_FILT] = u24(filt)
        osb = [0] * 144
        osb[2] = wave; osb[8] = u24(n_left if sample is None else sample); osb[V.SM_N] = 1
        rd = 0x40
        sf = [0, 0]
        outs, sides, blks, osbs = [], [], [], []
        mem_y = [('y', a_, [v_]) for a_, v_ in ydat.items()]
        for _ in range(blocks):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [rd]), ('x', GD.SOUT, [0] * 128), ('x', 0x3340, sf)] + table(n_left) + mem_y,
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', GD.SOUT, 128), ('x', 0x3340, 2)], regs_code=[], maxins=4_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, sf = res[('x', V.VB0)], res[('x', OSB)], res[('x', 0x3340)]
            outs.append(res[('y', RING)][0::2]); sides.append(res[('x', GD.SOUT)][rd:rd + 32]); blks.append(list(blk)); osbs.append(list(osb))
        return outs, sides, blks, osbs

    # ---- WAVE 0: as the previous build
    on, sn, bn, qn = go("new", 3, 0); oo, so, bo, qo = go("old", 3, 0)
    ours = set(range(V.SM_S2, V.SM_T2 + 1))
    check(on == oo and [[x for i, x in enumerate(q[:48]) if i not in ours] for q in qn] == [[x for i, x in enumerate(q[:48]) if i not in ours] for q in qo]
          and any(any(x) for x in on), "WAVE 0 (mono): the ring and the OSC1 block (but the new words 28..32) as the previous build's")
    check(all(not any(x) for x in sn), "WAVE 0: nothing in the side buffer")
    # ---- WAVE 100, no filter: the model
    on, sn, bn, qn = go("new", 3, 100)
    q = qn[0]
    check(q[V.SM_S] == SMP_L and q[V.SM_S2] == SMP_R and q[V.SM_L] == min(LL, LR) and q[V.SM_SR] != 0,
          f"a new note on sample 3: left {q[V.SM_S]:#x}, right {q[V.SM_S2]:#x} (sample 4), the length {q[V.SM_L]} (the shorter), stereo ({q[V.SM_SR]:#x})")
    # the step of note 60 = 1 sample a frame: n4 = 1, the fraction 0 (the ratio's integer part)
    good = True; pos, frac = 0, 0
    for k in range(4):
        L_, npos, nfrac = interp(Y, SMP_L, pos, frac, 1, 0, N)
        R_, _, _ = interp(Y, SMP_R, pos, frac, 1, 0, N)
        M_ = [lim(s56(((s24(l) << 24) + (s24(r) << 24)) >> 1)) for l, r in zip(L_, R_)]
        w = 100 << 16
        S_ = [lim(mpy(lim(s56(((s24(l) << 24) - (s24(r) << 24)) >> 1)), w)) for l, r in zip(L_, R_)]
        if on[k] != M_ or sn[k] != S_: good = False; bad = (k, [hex(x) for x in on[k][:3]], [hex(x) for x in M_[:3]], [hex(x) for x in sn[k][:3]], [hex(x) for x in S_[:3]])
        pos, frac = npos, nfrac
    check(good, f"WAVE 100: four blocks, the ring = (L + R) / 2, the side buffer = (L - R) / 2 x WAVE, bit-exact ({'' if good else bad})")
    on, sn, bn, qn = go("new", 63, 100)
    check(qn[0][V.SM_S2] == SMP_R, f"sample 63: the right = sample 0 ({qn[0][V.SM_S2]:#x})")
    on, sn, bn, qn = go("new", 3, 100, sample=-1)
    check(qn[0][V.SM_SR] == 0 and all(not any(x) for x in sn), "the capture (a negative sample): mono, no side")
    # ---- WAVE 100 with the low-pass: the same SVF over the mid (its state) and over the side (its own)
    on, sn, bn, qn = go("new", 3, 100, filt=-40)
    b0 = bn[0]
    ff, fq, fmode = b0[V.FF], b0[V.FQ], b0[V.FMODE]
    good = fmode == 1; pos, frac = 0, 0; lowm = bandm = lows = bands = 0
    for k in range(4):
        L_, npos, nfrac = interp(Y, SMP_L, pos, frac, 1, 0, N)
        R_, _, _ = interp(Y, SMP_R, pos, frac, 1, 0, N)
        M_ = [lim(s56(((s24(l) << 24) + (s24(r) << 24)) >> 1)) for l, r in zip(L_, R_)]
        S_ = [lim(mpy(lim(s56(((s24(l) << 24) - (s24(r) << 24)) >> 1)), 100 << 16)) for l, r in zip(L_, R_)]
        Mf, lowm, bandm = svf_lp(M_, lowm, bandm, ff, fq)
        Sf, lows, bands = svf_lp(S_, lows, bands, ff, fq)
        if on[k] != Mf or sn[k] != Sf: good = False; bad = (k, [hex(x) for x in on[k][:3]], [hex(x) for x in Mf[:3]], [hex(x) for x in sn[k][:3]], [hex(x) for x in Sf[:3]])
        pos, frac = npos, nfrac
    check(good, f"the low-pass (FMODE {fmode}): the mid and the side through the same SVF with their own states, bit-exact ({'' if good else bad})")
    print(f"{man.get('marker', '?')} SMSTEREO DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
