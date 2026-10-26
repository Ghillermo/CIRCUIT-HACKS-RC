"""SC46.6 DSP test (vcf21_dsp.use_fmvca / fmwide / fmcompact / fmorder / fmsine / fmsmooth / fbavg): the FM voice of the own engine.

    python tools/emu_fm2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC46.5 / Beta 3.22)

On the dsp56kEmu interpreter with each build's real core-0 program, vpre called once a block (emu_fm_dsp's harness):
  * the FM flag 0: the sine, the triangle, the saw, the square and the two oscillators as PREV bit for bit (ring and blocks);
  * the flag on: three blocks of samples against a bit-exact model of the new loop: the operators 4 to 1 (a modulator of a lower operator is the same
    sample's), the phase += base x R x 128, the smoothed AMP s += (AMP - s) >> 5, the modulation 4 x (sum M_kj OUT_j + HC_k x OUT_k two samples
    back), P = 4 (u - u |u|), the sine refinement 0.75 P + 0.25 P |P|, OUT = s x P, the sample = sum K_k OUT_k; the phases, the smoothed AMPs and the
    two-samples-back outputs left in the blocks; the noise level read from OSC1 + 38 into VD_NL;
  * the smoothed AMP settles to the target (and to 0 after a release);
  * the sine: one carrier at ratio 1 without modulation: the 3rd harmonic under -46 dB, the 5th under -54 dB (it was about -28.6 dB);
  * the VCA: the neutral defaults (GAIN 0, ENVA 63, REL 0), the gate on 2 blocks then off: with the FM flag the VCA target stays ENVA x VEL after the
    gate (the previous build: down to 0 within the release); with the flag 0 the same as the previous build;
  * the program ends at or below P:$3FFF; the system stack with the FM voice on no deeper than PREV's + 2.
"""
from __future__ import annotations
import cmath, gc, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_fm_dsp as F0  # noqa: E402  (sets vcf21_dsp's constants as emu_fm_dsp)
from emu_masterfx_dsp import s24, u24  # noqa: E402
V = F0.V
N, RING, OSB = F0.N, F0.RING, F0.OSB
s56, lim, mpy, a1 = F0.s56, F0.lim, F0.mpy, F0.a1


def model(blk, base, nblk, wide=True, order=True, sine=True, smooth=True, fbavg=True):
    """blk: the 48 words of the FM voice; base: the oscillator's increment; returns the samples of nblk blocks and the blocks after them"""
    o = list(blk); out = []
    ks = (3, 2, 1, 0) if order else (0, 1, 2, 3)
    for _ in range(nblk):
        bo = []
        for _s in range(N):
            b = 0
            for k in ks:
                r = 12 * k
                amp = o[r + V.F_AMP]
                if smooth:
                    v = ((s24(o[r + V.F_AMP]) - s24(o[r + V.F_AS])) << 24) >> 5
                    o[r + V.F_AS] = lim(v + (s24(o[r + V.F_AS]) << 24)); amp = o[r + V.F_AS]
                v = s56(mpy(o[r + V.F_R], base) << (7 if wide else 4)) + (s24(o[r + V.F_PH]) << 24)
                ph = a1(v); o[r + V.F_PH] = ph
                acc = 0
                for j in range(4): acc = s56(acc + mpy(o[r + V.F_M + j], o[12 * j + V.F_OUT]))
                if fbavg: acc = s56(acc + mpy(o[r + V.F_HC], o[r + V.F_O2]))
                acc = s56(acc << 2) + (s24(ph) << 24)
                u = a1(acc)
                y0 = lim(abs(s24(u)) << 24)
                va = s56(-mpy(u, y0) + (s24(u) << 24))
                va = s56(va << 2)
                if sine:
                    x0 = lim(va); y0 = lim(abs(va))
                    va = s56(mpy(y0, x0) - (s24(x0) << 24))
                    va = s56((va >> 2) + (s24(x0) << 24))
                x0 = lim(va)
                va = mpy(amp, x0)
                old = o[r + V.F_OUT]
                o[r + V.F_OUT] = lim(va)
                if fbavg: o[r + V.F_O2] = old
                b = s56(b + mpy(o[r + V.F_K], lim(va)))
            bo.append(lim(b))
        out.append(bo)
    return out, o


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
    names = dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT, ENVA=V.P_ENVA,
                 ATK=V.P_ATK, GATE=V.GATE, VEL=V.VEL)
    sig = [u24((k * 7919) % 0x300000 - 0x180000) for k in range(2 * N)]

    def call(which, wave, pw, note=60, dual=False, blocks=1, fm=None, osb=None, fmb=None, vals=None, gate_blocks=None, keep=None):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k, v in (vals or dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=note, ACT=2)).items(): blk[names[k]] = v
        if osb is None:
            osb = [0] * 144
            for k, v in enumerate((0, 0, wave, pw)): osb[k] = v
            if dual:
                osb[V.DFLAGS_OFF] = 2; osb[V.NOTE2_OFF] = note + 7
                for k, v in enumerate((0, 0, wave, pw)): osb[0x60 + k] = v
            if fm is not None: osb[V.FM_FLAG] = 1
        if fmb is None: fmb = list(fm) if fm is not None else [0] * 48
        outs, blks = [], []
        for bi in range(blocks):
            if gate_blocks is not None: blk[V.GATE] = 1 if bi < gate_blocks else 0
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig), ('x', OSB, osb),
                                         ('x', V.FMB0, fmb)],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', V.FMB0, 48)], regs_code=[])
            assert 'pc=00' in ran, ran
            blk, osb, fmb = res[('x', V.VB0)], res[('x', OSB)], res[('x', V.FMB0)]
            outs.append(res[('y', RING)][0::2]); blks.append(list(blk))
        return outs, osb, fmb, blks

    # ---- the flag off: as the previous build
    same = []
    for wave, pw, dual in ((0, 50, False), (42, 20, False), (84, 70, False), (126, 50, False), (0, 70, True), (84, 30, True)):
        on, bn, _, _ = call("new", wave, pw, dual=dual, blocks=2); oo, bo, _, _ = call("old", wave, pw, dual=dual, blocks=2)
        same.append(((wave, pw, dual), on == oo and bn[:48] == bo[:48] and bn[0x60:0x90] == bo[0x60:0x90]))
    check(all(x[1] for x in same), f"FM flag 0: sine / triangle / saw / square and two oscillators as the previous build ({[x[0] for x in same if not x[1]]})")

    # ---- the FM voice against the model
    def voice(R, AMP, K, M, AS=(0, 0, 0, 0), HC=(0, 0, 0, 0), O2=(0, 0, 0, 0)):
        b = [0] * 48
        for k in range(4):
            b[12 * k + V.F_R], b[12 * k + V.F_AMP], b[12 * k + V.F_K] = R[k], AMP[k], K[k]
            b[12 * k + V.F_AS], b[12 * k + V.F_HC], b[12 * k + V.F_O2] = AS[k], HC[k], O2[k]
            for j in range(4): b[12 * k + V.F_M + j] = M[k][j]
        return b
    one = 1 << 16                                                            # the ratio 1 (R = ratio / 128)
    F = 0x7FFFFF
    cases = {
        "stack 4-3-2-1": voice([one, 2 * one, 3 * one, one], [0x7FFFFF, 0x400000, 0x300000, 0x200000], [0x3FFFFF, 0, 0, 0],
                               [[0, F, 0, 0], [0, 0, F, 0], [0, 0, 0, F], [0, 0, 0, 0]], AS=(0x7FFFFF, 0x400000, 0x300000, 0x200000)),
        "two stacks, feedback (averaged)": voice([one, one * 3 // 2, one, 4 * one], [0x600000, 0x500000, 0x600000, 0x380000], [0x1FFFFF, 0, 0x1FFFFF, 0],
                                                 [[0, F, 0, 0], [0, 0, 0, 0], [0, 0, 0, F], [0, 0, 0, 0x280000]], HC=(0, 0, 0, 0x280000)),
        "organ, AMP gliding": voice([one // 2, one, 2 * one, 4 * one], [0x7FFFFF] * 4, [0x0FFFFF] * 4, [[0] * 4] * 4),
        "4 on three, ratios 14 / 15 / 64": voice([one, 14 * one, 15 * one, 64 * one], [0x500000, 0x500000, 0x500000, 0x7FFFFF], [0x155555, 0x155555, 0x155555, 0],
                                                 [[0, 0, 0, F], [0, 0, 0, F], [0, 0, 0, F], [0, 0, 0, 0]], AS=(0x500000, 0x500000, 0x500000, 0x7FFFFF)),
    }
    for nm, fmb in cases.items():
        for note in (48, 72):
            outs, osb, fmo, _ = call("new", 0, 50, note=note, blocks=3, fm=fmb)
            base = osb[11]
            exp, o = model(fmb, base, 3)
            words = [fmo[12 * k + w] for k in range(4) for w in (V.F_PH, V.F_AS, V.F_O2, V.F_OUT)]
            check(outs == exp and words == [o[12 * k + w] for k in range(4) for w in (V.F_PH, V.F_AS, V.F_O2, V.F_OUT)]
                  and max(abs(s24(x)) for b_ in outs for x in b_) > 0x10000,
                  f"{nm}, note {note}: three blocks bit-exact with the model, the blocks' words kept ({[hex(x) for x in outs[2][:3]]} / {[hex(x) for x in exp[2][:3]]})")
    # the smoothed AMP settles
    fmb = voice([one, 0, 0, 0], [0x400000, 0, 0, 0], [0x3FFFFF, 0, 0, 0], [[0] * 4] * 4)
    _, _, f1, _ = call("new", 0, 50, blocks=12, fm=fmb)
    f2 = list(f1); f2[V.F_AMP] = 0
    _, _, f3, _ = call("new", 0, 50, blocks=16, fm=f2)
    check(abs(f1[V.F_AS] - 0x400000) < 0x400 and f3[V.F_AS] == 0, f"the smoothed AMP: 12 blocks -> {f1[V.F_AS]:#x} (target 0x400000); the target 0: {f3[V.F_AS]:#x}")
    # the sine: one carrier, ratio 1, no modulation, 64 samples a cycle (the DSP's increment comes from the note: the model, bit-exact above, at a whole
    # number of cycles); the previous loop's parabola for the comparison
    fmb = voice([one, 0, 0, 0], [0x7FFFFF, 0, 0, 0], [0x7FFFFF, 0, 0, 0], [[0] * 4] * 4, AS=(0x7FFFFF, 0, 0, 0))
    exp, _ = model(fmb, 1 << 18, 4)
    sam = [s24(x) for b_ in exp for x in b_]
    exp0, _ = model(fmb, 1 << 18, 4, sine=False)
    sam0 = [s24(x) for b_ in exp0 for x in b_]
    def harm(xs, h):
        n = len(xs); return abs(sum(x * cmath.exp(-2j * math.pi * h * i * 2 / n) for i, x in enumerate(xs))) / n
    db = lambda xs, h: 20 * math.log10(max(harm(xs, h), 1e-9) / harm(xs, 1))
    check(db(sam, 3) < -46 and db(sam, 5) < -54, f"the sine: the 3rd harmonic {db(sam, 3):.1f} dB, the 5th {db(sam, 5):.1f} dB (the parabola: {db(sam0, 3):.1f} / {db(sam0, 5):.1f})")

    # ---- the VCA: the neutral defaults, the gate on 2 blocks then off
    vals = dict(GAIN=0, ENVA=63, ATK=0, DEC=0, SUS=127, REL=0, LRATE=0, FXMOD=64, NOTE=60, ACT=2, VEL=100)
    fmb = cases["stack 4-3-2-1"]
    def gt(which, flag):
        osb = [0] * 144; osb[V.FM_FLAG] = flag
        _, _, _, blks = call(which, 0, 50, blocks=12, osb=osb, fmb=list(fmb), vals=vals, gate_blocks=2)
        return [(b[V.GT], b[V.GCUR]) for b in blks]
    gn1, gn0, go0 = gt("new", 1), gt("new", 0), gt("old", 0)
    check(gn1[-1][0] > 0x40000 and gn1[-1][0] == gn1[2][0] and gn1[-1][1] > 0x40000, f"FM: the VCA target after the gate stays ({gn1[2][0]:#x} -> {gn1[-1][0]:#x}, GCUR {gn1[-1][1]:#x})")
    check(gn0 == go0 and go0[-1][0] < go0[1][0] // 8, f"flag 0: the VCA as the previous build ({gn0 == go0}: {go0[1][0]:#x} down to {go0[-1][0]:#x} after the gate)")

    # ---- the system stack with the engine's traffic, the FM voice on
    import emu_sc43_9_dsp as M, dsp_session as DS, os, shutil, subprocess, tempfile
    sched = M.schedule(prev, pman)
    def spmax(im, fm_on):
        s = DS.Session(im)
        prog = bytearray(DS.dsp_program(im))
        for a_ in DS.SPIN_NOPS: prog[3 * a_:3 * a_ + 3] = b'\0\0\0'
        d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
        Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'SPMAX', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
        for _, w in s.events: Ls += s._mem(w)
        if fm_on:
            for t in (0, 1):
                Ls.append('X %x %06x' % (OSB + 48 * t + V.FM_FLAG, 1))
                for i, w in enumerate(cases["two stacks, feedback (averaged)"]): Ls.append('X %x %06x' % (V.FMB0 + 48 * t + i, w))
        Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)])))
        for b_ in range(min(len(sched), 200)):
            for w, addr in sched[b_]: Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
            Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
        sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
        try:
            out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
        finally:
            shutil.rmtree(d, ignore_errors=True)
        v = [int(l.split()[1]) for l in out.splitlines() if l.startswith('SPMAX')]
        return max(v) if v else None
    sn, so = spmax(img, True), spmax(prev, False); gc.collect()
    check(sn is not None and so is not None and sn <= so + 2 and sn < 15, f"the system stack with FM on: at most {sn} levels (the previous build: {so})")
    print(f"{man.get('marker', '?')} FM2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
