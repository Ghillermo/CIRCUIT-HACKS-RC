"""SC45.6 DSP test (vcf21_dsp.use_fm): the 4-operator FM variant of the own engine's oscillator.

    python tools/emu_fm_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC45.5)

On the dsp56kEmu interpreter with each build's real core-0 program, vpre called once a block with the voice, oscillator and FM blocks carried (as
emu_sc45_5_dsp: the ring after vpre = the oscillator's samples):
  * the FM flag 0 (X:OSB0 + 27): the sine, the triangle, the saw, the square and the two oscillators as PREV bit for bit (ring and blocks);
  * the flag on: three blocks of samples against a bit-exact model (the phase += base x R x 16, the modulation 4 x sum(M_kj OUT_j) with the outputs
    of the previous sample for the operators not yet computed, OUT = AMP x 4 u (1 - |u|), the sample = sum K_k OUT_k): the stack 4-3-2-1, two
    stacks with two carriers, the feedback, the organ (four carriers), operators at different ratios, a pitch above the 16 x ratio limit; the
    phases left in the blocks; the noise level (F_NZ) copied into VD_NL, the VA-drum's noise added only when it is not 0;
  * the system stack with the engine's traffic and the FM voice on (two nested loops): at most two levels deeper than PREV's, under 16.
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import dsp_session as DS  # noqa: E402
from emu_masterfx_dsp import Acc, s24, u24  # noqa: E402
import vcf21_dsp as V  # noqa: E402
V.TILT, V.FB, V.SLOPES, V.FXMORE, V.BISEND, V.PLIMIT, V.OSC, V.VFF = False, True, True, True, True, 0x4000, True, True
V.use_osc3()

N = 32
RING = 0x1000
OSB = 0x3900
M56 = (1 << 56) - 1


def s56(v): v &= M56; return v - (1 << 56) if v >> 55 else v
def lim(v): v = s56(v); return u24(max(-0x800000, min(0x7FFFFF, v >> 24)))
def mpy(x, y): return Acc().mpy(u24(x), u24(y)).v
def a1(v): return (s56(v) >> 24) & 0xFFFFFF


def model(blk, base, nblk):
    """blk: the 48 words of the FM voice (ops at 12 k); base: the oscillator's increment; returns the samples of nblk blocks and the phases"""
    o = list(blk); out = []
    for _ in range(nblk):
        bo = []
        for _s in range(N):
            b = 0
            for k in range(4):
                r = 12 * k
                v = s56(mpy(o[r + V.F_R], base) << 4) + (s24(o[r + V.F_PH]) << 24)
                ph = a1(v); o[r + V.F_PH] = ph
                acc = 0
                for j in range(4): acc = s56(acc + mpy(o[r + V.F_M + j], o[12 * j + V.F_OUT]))
                acc = s56(acc << 2) + (s24(ph) << 24)
                u = a1(acc)
                va = s24(u) << 24
                y0 = lim(abs(va))
                y0 = lim((0x7FFFFF << 24) - (s24(y0) << 24))
                x0 = lim(s56(mpy(u, y0) << 2))
                va = mpy(o[r + V.F_AMP], x0)
                o[r + V.F_OUT] = lim(va)
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
    names = dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT)
    sig = [u24((k * 7919) % 0x300000 - 0x180000) for k in range(2 * N)]

    def call(which, wave, pw, note=60, dual=False, blocks=1, fm=None, osb=None, fmb=None):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k, v in dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=note, ACT=2).items(): blk[names[k]] = v
        if osb is None:
            osb = [0] * 144
            for k, v in enumerate((0, 0, wave, pw)): osb[k] = v
            if dual:
                osb[V.DFLAGS_OFF] = 2; osb[V.NOTE2_OFF] = note + 7
                for k, v in enumerate((0, 0, wave, pw)): osb[0x60 + k] = v
            if fm is not None: osb[V.FM_FLAG] = 1
        if fmb is None: fmb = list(fm) if fm is not None else [0] * 48
        outs = []
        for _ in range(blocks):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig), ('x', OSB, osb),
                                         ('x', V.FMB0, fmb)],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', V.FMB0, 48)], regs_code=[])
            assert 'pc=00' in ran, ran
            blk, osb, fmb = res[('x', V.VB0)], res[('x', OSB)], res[('x', V.FMB0)]
            outs.append(res[('y', RING)][0::2])
        return outs, osb, fmb

    # ---- the flag off: as the previous build
    same = []
    for wave, pw, dual in ((0, 50, False), (42, 20, False), (84, 70, False), (126, 50, False), (0, 70, True), (84, 30, True)):
        on, bn, _ = call("new", wave, pw, dual=dual, blocks=2); oo, bo, _ = call("old", wave, pw, dual=dual, blocks=2)
        same.append(((wave, pw, dual), on == oo and bn[:48] == bo[:48] and bn[0x60:0x90] == bo[0x60:0x90]))
    check(all(x[1] for x in same), f"FM flag 0: sine / triangle / saw / square and two oscillators as the previous build ({[x[0] for x in same if not x[1]]})")

    # ---- the FM voice against the model
    def voice(R, AMP, K, M, nz=0):
        b = [0] * 48
        for k in range(4):
            b[12 * k + V.F_R], b[12 * k + V.F_AMP], b[12 * k + V.F_K] = R[k], AMP[k], K[k]
            for j in range(4): b[12 * k + V.F_M + j] = M[k][j]
        b[V.F_NZ] = nz
        return b
    one = 1 << 19                                                            # the ratio 1 (R = ratio / 16)
    F = 0x7FFFFF
    cases = {
        "stack 4-3-2-1": voice([one, 2 * one, 3 * one, one], [0x7FFFFF, 0x400000, 0x300000, 0x200000], [0x3FFFFF, 0, 0, 0],
                               [[0, F, 0, 0], [0, 0, F, 0], [0, 0, 0, F], [0, 0, 0, 0]]),
        "two stacks, feedback": voice([one, one * 3 // 2, one, 4 * one], [0x600000, 0x500000, 0x600000, 0x380000], [0x1FFFFF, 0, 0x1FFFFF, 0],
                                      [[0, F, 0, 0], [0, 0, 0, 0], [0, 0, 0, F], [0, 0, 0, 0x500000]]),
        "organ": voice([one // 2, one, 2 * one, 4 * one], [0x7FFFFF] * 4, [0x0FFFFF] * 4, [[0] * 4] * 4),
        "4 on three, high ratio": voice([one, 14 * one, 15 * one, 16 * one], [0x500000, 0x500000, 0x500000, 0x7FFFFF], [0x155555, 0x155555, 0x155555, 0],
                                        [[0, 0, 0, F], [0, 0, 0, F], [0, 0, 0, F], [0, 0, 0, 0]]),
    }
    for nm, fmb in cases.items():
        for note in (48, 72):
            outs, osb, fmo = call("new", 0, 50, note=note, blocks=3, fm=fmb)
            base = osb[11]
            exp, o = model(fmb, base, 3)
            ph = [fmo[12 * k + V.F_PH] for k in range(4)]
            check(outs == exp and ph == [o[12 * k + V.F_PH] for k in range(4)] and max(abs(s24(x)) for b_ in outs for x in b_) > 0x10000,
                  f"{nm}, note {note}: three blocks bit-exact with the model, the phases kept ({[hex(x) for x in outs[2][:3]]} / {[hex(x) for x in exp[2][:3]]})")
    fmb = cases["stack 4-3-2-1"]
    q0, o0, _ = call("new", 0, 50, blocks=1, fm=fmb)
    fz = list(fmb); fz[V.F_NZ] = 0x200000
    q1, o1, _ = call("new", 0, 50, blocks=1, fm=fz)
    check(o0[V.VD_NL] == 0 and o1[V.VD_NL] == 0x200000 and q1 != q0, f"the noise: F_NZ into VD_NL ({o1[V.VD_NL]:#x}), added to the FM samples ({q0 == q1})")

    # ---- the system stack with the engine's traffic, the FM voice on
    import emu_sc43_9_dsp as M
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
                for i, w in enumerate(cases["two stacks, feedback"]): Ls.append('X %x %06x' % (V.FMB0 + 48 * t + i, w))
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
    print(f"{man.get('marker', '?')} FM DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
