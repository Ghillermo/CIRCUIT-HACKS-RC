"""SC45.5 DSP test (vcf21_dsp.use_supersaw): the own engine's oscillator, SHAPE on the saw = plain .. supersaw of 7, on the triangle left of the
centre = exponential ramps; the four waves as a subroutine.

    python tools/emu_sc45_5_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC45.4)

On the dsp56kEmu interpreter with each build's real core-0 program, vpre called once a block with the voice and oscillator blocks carried (as
emu_sc22_3_dsp: the ring after vpre = the oscillator's samples):
  * what must not change, against PREV bit for bit (the ring and the oscillator block but the new words): the sine at shapes 0 / 50 / 100 (the square within 64 LSB: the morph
    leaves the saw 12 LSB of weight at WAVE 126), the triangle at 50 / 80 / 100, the morph between the sine and the triangle, the two oscillators (dual) on the sine and the square;
  * the block's parameters against a model: the triangle's curve c / 2 = max(-m, 0) / 2, s = (m + 1) / 2, D = 0.0183 s x the increment, 3 D = 2 D + the full D, 6 D = 2 x that,
    the saw's weights w (1 - s / 2) / 2 and w s / 16;
  * the samples against a model, bit-exact, three blocks running: the triangle at shapes 0 / 25 (its mean below zero: the exponential ramps), the saw
    at 0 (no side saws: their weight 0), 50 and 100 (six side phases advancing at the increment +- D, 3 D, 6 D);
  * the whole core with the engine's traffic (emu_sc43_9_dsp.schedule: both tracks, MIDI 1 with two oscillators, notes): the system stack's depth
    against PREV's (the subroutine call inside the sample loop: one level more at most, under 16).
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
PH_, INC_, GH_, C2_, PU_, W0_ = 10, 11, 12, 13, 14, 15
SSP, SSD, SSW = 28, 35, 42
D1 = int(round(0.0183 * (1 << 23)))


def lim(v):
    return u24(max(-0x800000, min(0x7FFFFF, v >> 24)))


def mpy(x, y): return Acc().mpy(u24(x), u24(y)).v


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) < 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")
    blk0 = [0] * (2 * V.VBS)
    names = dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT)
    sig = [u24((k * 7919) % 0x300000 - 0x180000) for k in range(2 * N)]

    def call(which, wave, pw, note=60, dual=False, blocks=1, osb=None, blk=None):
        P, vpre = progs[which]
        if blk is None:
            blk = list(blk0)
            for k, v in dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=note, ACT=2).items(): blk[names[k]] = v
        if osb is None:
            osb = [0] * 144
            for k, v in enumerate((0, 0, wave, pw)): osb[k] = v
            if dual:
                osb[V.DFLAGS_OFF] = 2; osb[V.NOTE2_OFF] = note + 7
                for k, v in enumerate((0, 0, wave, pw)): osb[0x60 + k] = v
        outs = []
        for _ in range(blocks):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, sig), ('x', OSB, osb)],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144)], regs_code=[])
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], res[('x', OSB)]
            outs.append(res[('y', RING)][0::2])
        return outs, osb, blk
    NEWW = set(range(SSP, SSP + 6)) | set(range(SSD, SSD + 3)) | {SSW, C2_, 17}

    # ---- unchanged: the sine, the square, the triangle right of the centre, the morph sine / triangle, the dual oscillator
    # (the square, WAVE 126: the morph leaves the saw a weight of 12 LSB (q = 0x7ffffc), so the new saw shows in the last bits: TOL)
    TOL = 64
    def diff(a_, b_): return max(abs(s24(x) - s24(y)) for p_, q_ in zip(a_, b_) for x, y in zip(p_, q_))
    same, dmax = [], 0
    for wave, pws in ((0, (0, 50, 100)), (126, (0, 50, 100)), (42, (50, 80, 100)), (21, (50, 100))):
        for pw in pws:
            on, bn, _ = call("new", wave, pw, blocks=2); oo, bo, _ = call("old", wave, pw, blocks=2)
            blk_ok = all(bn[i] == bo[i] for i in range(48) if i not in NEWW)
            if wave == 126: dv = diff(on, oo); dmax = max(dmax, dv); same.append((wave, pw, blk_ok and dv <= TOL))
            else: same.append((wave, pw, blk_ok and on == oo))
    check(all(x[2] for x in same), f"sine at 0 / 50 / 100, triangle at 50 / 80 / 100, the morph 21: as the previous build bit for bit; the square at 0 / 50 / 100 within {dmax} LSB ({[x[:2] for x in same if not x[2]]})")
    dd, dmax = [], 0
    for wave in (0, 126):
        on, bn, _ = call("new", wave, 70, dual=True, blocks=2); oo, bo, _ = call("old", wave, 70, dual=True, blocks=2)
        if wave == 126: dv = diff(on, oo); dmax = max(dmax, dv); dd.append(dv <= TOL)
        else: dd.append(on == oo)
    check(all(dd), f"two oscillators (dual): the sine as the previous build bit for bit, the square within {dmax} LSB ({dd})")

    # ---- the model
    def blockpar(osb, o=0):
        return dict(inc=osb[o + INC_], gh=osb[o + GH_], c2=osb[o + C2_], pu=osb[o + PU_], w=osb[o + W0_:o + W0_ + 4], d=osb[o + SSD:o + SSD + 3], ws=osb[o + SSW])
    def fold_model(Bv):
        p = (Bv >> 24) & 0xFFFFFF
        z = s24((s24(p) - 0x400000) & 0xFFFFFF)
        return ((0x7FFFFF - 2 * abs(z)) >> 1) & 0xFFFFFF
    def sine(u, gh):                                                    # the SINEFIX sine (as the build: P (0.775 + 0.225 |P|), drive, fold)
        y0 = 0x7FFFFF - min(abs(u), 0x7FFFFF); b = mpy(u, y0) << 2; y1 = lim(b); b = mpy(y1, min(abs(s24(y1)), 0x7FFFFF)); y0 = lim(b)
        b = mpy(y0, 0x1CCCCD) + mpy(0x633333, y1); y1 = lim(b); b = mpy(gh, y1) << 2
        return fold_model(b)
    def tri(u, gh, c2):
        t = lim((2 * abs(u) - 0x7FFFFF) << 24); y1 = t
        b = mpy(t, t); x0 = lim(b); b = (0x7FFFFF << 24) - (s24(x0) << 24); x0 = lim(b)
        b = mpy(c2, x0); x0 = lim(b); b = (s24(y1) << 24) - (s24(x0) << 24); y1 = lim(b)
        b = mpy(gh, y1) << 2
        return fold_model(b)
    def model(par, ph, sph, n=N):
        out = []
        for _ in range(n):
            ph = (ph + par["inc"]) & 0xFFFFFF; u = s24(ph)
            acc = mpy(sine(u, par["gh"]), par["w"][0]) + mpy(tri(u, par["gh"], par["c2"]), par["w"][1]) + mpy(ph, par["w"][2])
            for k in range(6):
                sph[k] = (sph[k] + par["inc"] + (s24(par["d"][k // 2]) if k % 2 == 0 else -s24(par["d"][k // 2]))) & 0xFFFFFF
                acc += mpy(par["ws"], sph[k])
            acc += mpy(0x400000 if u - s24(par["pu"]) < 0 else 0xC00000, par["w"][3])
            out.append(lim(acc))
        return out, ph, sph

    # ---- the block's parameters
    def m_of(pw):                                                       # the shape m (no envelope / LFO)
        a = mpy(u24((pw - 50) << 17), 0x51EB85) << 1
        return s24(lim(a))
    bad = []
    for wave, pw in ((84, 0), (84, 25), (84, 50), (84, 100), (42, 0), (42, 25), (63, 30)):
        _, osb, _ = call("new", wave, pw)
        m = m_of(pw); par = blockpar(osb)
        c2 = lim((max(-m, 0) << 24) >> 1); s = lim(((m << 24) >> 1) + (0x400000 << 24))
        dacc = mpy(D1, lim(mpy(s, par["inc"])))                           # as the DSP: b = D; a = 2 lim(b) + b (move b,a limits to 24 bits); 6 D = 2 a
        a3 = 2 * (s24(lim(dacc)) << 24) + dacc
        d = [lim(dacc), lim(a3), lim(2 * a3)]
        _, ob, _ = call("old", wave, pw); w = ob[W0_ + 2]
        bacc = mpy(s, w); aacc = (s24(w) << 24) - (bacc >> 1)
        w17, ws = lim(aacc >> 1), lim(bacc >> 4)
        if not (par["c2"] == c2 and par["d"] == d and osb[W0_ + 2] == w17 and par["ws"] == ws): bad.append((wave, pw, hex(par["c2"]), hex(c2), par["d"], d, hex(osb[W0_ + 2]), hex(w17), hex(par["ws"]), hex(ws)))
    check(not bad, f"the block: c / 2, D / 3 D / 6 D, the saw's centre and side weights as the model ({bad[:2]})")

    # ---- the samples, three blocks
    res = []
    for wave, pw in ((42, 0), (42, 25), (84, 0), (84, 50), (84, 100), (63, 20)):
        outs, osb, _ = call("new", wave, pw, blocks=3)
        par = blockpar(osb)
        ph, sph, exp = 0, [0] * 6, []
        for b in range(3):
            o, ph, sph = model(par, ph, sph); exp.append(o)
        res.append((wave, pw, outs == exp and osb[SSP:SSP + 6] == [x & 0xFFFFFF for x in sph], outs[2][:3], exp[2][:3]))
    check(all(r[2] for r in res), f"the samples bit-exact, three blocks (triangle 0 / 25, saw 0 / 50 / 100, morph 63 at 20): {[(r[0], r[1]) for r in res if not r[2]]} {[r[3:] for r in res if not r[2]][:1]}")
    tri0, _, _ = call("new", 42, 0, note=36, blocks=4)
    tri50, _, _ = call("new", 42, 50, note=36, blocks=4)
    mean = lambda o: sum(s24(x) for b in o for x in b) / (len(o) * N)
    check(mean(tri0) < mean(tri50) - 0x80000, f"the triangle at shape 0: its mean below the plain one's ({mean(tri0) / 2 ** 23:+.3f} / {mean(tri50) / 2 ** 23:+.3f}): exponential ramps")
    s0 = call("new", 84, 0, blocks=2)[1]; s100 = call("new", 84, 100, blocks=2)[1]
    check(s0[SSW] == 0 and s100[SSW] > 0 and len(set(s100[SSP:SSP + 6])) == 6, f"the saw: the side saws' weight 0 at the far left ({s0[SSW]:#x}), {s100[SSW]:#x} at the right, six distinct side phases")

    # ---- the system stack with the engine's traffic
    import emu_sc43_9_dsp as M
    sched = M.schedule(prev, pman)
    def spmax(im):
        s = DS.Session(im)
        prog = bytearray(DS.dsp_program(im))
        for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
        d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
        Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'SPMAX', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
        for _, w in s.events: Ls += s._mem(w)
        Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)])))
        for b in range(min(len(sched), 200)):
            for w, addr in sched[b]: Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
            Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
        sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
        try:
            out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
        finally:
            shutil.rmtree(d, ignore_errors=True)
        v = [int(l.split()[1]) for l in out.splitlines() if l.startswith('SPMAX')]
        return max(v) if v else None
    sn, so = spmax(img), spmax(prev); gc.collect()
    check(sn is not None and so is not None and sn <= so + 1 and sn < 15, f"the system stack: at most {sn} levels (the previous build: {so})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
