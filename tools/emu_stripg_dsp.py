"""SC47.1 DSP test (granular_dsp.use_stripgain): the sides of the stereo sample mode and of the granular with the stock mixer's strip settled, as on
the device (S469D: MIDI 1 at level 100, centre pan: Y:$5B / $5C = X:$20C pairs = $063FC0; the emulation's ramp from 0 takes > 250 blocks, so the test
holds Y:$5B / $5C at the device's value every block), on the whole core 0 (emu_smswap_dsp's harness) with the engine's real traffic:

    python tools/emu_stripg_dsp.py NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json      (OLD = SC47 / Beta 3.27)

  * the sample mode, WAVE 0: the first sample on both sides (the reference m);
  * WAVE 126, only the first sample: L = m, R near 0; only the second: R = m, L near 0; OLD: the first on both sides (L 0.61 m, R 0.39 m: the device's bug);
  * the strip at 0 (Y:$5B / $5C = 0; the stock's ramp still moves it one step a block): nothing of MIDI 1 in the mix (OLD: the sides went on, ~12 %);
  * the strip hard left (Y:$5C = 0): R = 0; the first sample on the left, the second silent (the mid and the side cancel);
  * the granular: OUT = c, SOUT = c (every grain on the right): L near 0, R = 2 x the mid; OLD: L = 0.78 x the mid.
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402
import emu_gstereo_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
import vcf21_dsp as V  # noqa: E402

VB, OSB = 0x3B80, 0x3900
YA, YB = 0x40000, 0x48000
STRIP = 0x063FC0                                   # the device's Y:$5B / $5C at level 100, centre pan
T0, TM = 60, 76


def run(img, sched, blocks, force, yforce, at_block, dumps_after, ywrites):
    s = DS.Session(img)
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    Ls += ['Y %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in ywrites]
    for b in range(blocks):
        if b < len(sched):
            for w, addr in sched[b]:
                if b >= 60 and addr == VB and (w >> 16) & 0x7F in (17, 18, 19, 20, 21, 22): continue
                Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in force(b)]
        Ls += ['Y %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in yforce(b)]
        if b == at_block:
            Ls += [f'PC {DS.STUB:x}', f'STOP {G.AFTER:x}', 'RUN'] + ['DUMPX %x %d' % (a_, n_) for a_, n_ in dumps_after]
            Ls += [f'STOP {DS.STUB + 2:x}', 'RUN']
        else:
            Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
    try:
        out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
    rows = {}
    for l in out.splitlines():
        if l[:1] == 'X' and ':' in l:
            k, v = l.split(':', 1); a_ = int(k.split()[1], 16)
            rows.setdefault(a_, []).append([int(x, 16) for x in v.split()])
    return rows


def measure(img, sched, gl=STRIP, gr=STRIP, sample=None, gran=None):
    """sample = (wave, first, second): the sample mode; gran = (out, sout): the granular voice.  The mix L / R (32 frames) after smp_post."""
    def force(b):
        f = []
        if b < T0: return f
        f += [(0x56, 100 << 15), (0x57, 0x400000)]
        if sample:
            wave = sample[0]
            f += [(VB + V.ACT, 3), (VB + V.NOTE, 60), (OSB + 21, 0), (OSB + 2, wave), (OSB + 8, 3), (OSB + V.SM_K, 1),
                  (VB + V.P_LFOV, 0), (VB + V.P_FXAMT, 0), (VB + V.P_FILT, 0), (VB + V.P_ENVF, 0), (VB + V.P_LFOF, 0), (VB + V.P_FTYPE, 0)]
            if b == T0: f += [(OSB + V.SM_N, 1)]
            for k, (st, ln) in ((3, (YA, 4000)), (4, (YB, 4000))): f += [(V.SM_TAB + 4 * k, st), (V.SM_TAB + 4 * k + 1, ln)]
        else:
            c, s = gran
            f += [(G.ACT, 2), (G.NOTE, 60), (OSB + 21, 16), (VB + 13, 0)]
            f += [(GD.OUT + i, c if (i & 63) < 32 else 0) for i in range(128)]
            f += [(GD.SOUT + i, s if (i & 63) < 32 else 0) for i in range(128)]
        return f
    yforce = lambda b: [(0x5B, gl), (0x5C, gr)] if b >= T0 - 4 else []
    yw = []
    if sample: yw = [(YA + i, sample[1]) for i in range(3000)] + [(YB + i, sample[2]) for i in range(3000)]
    R = run(img, sched, TM + 2, force, yforce, TM, [(G.PF_L, 32), (G.PF_R, 32), (0x20C, 4)], yw)
    gc.collect()
    g = lambda a: R[a][0]
    return [G.s24(x) for x in g(G.PF_L)], [G.s24(x) for x in g(G.PF_R)], g(0x20C)


def main(img, man, old, oman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    C = 0x200000
    res = {}
    for nm, im, mf in (("new", img, man), ("old", old, oman)):
        sched = M.schedule(im, mf)
        r = {}
        L0, R0, strip = measure(im, sched, sample=(126, 0, 0))
        d = lambda LR: ([a - b for a, b in zip(LR[0], L0)][8], [a - b for a, b in zip(LR[1], R0)][8])
        r["strip"] = strip
        r["mono"] = d(measure(im, sched, sample=(0, C, 0)))
        r["first"] = d(measure(im, sched, sample=(126, C, 0)))
        if nm == "new":
            r["second"] = d(measure(im, sched, sample=(126, 0, C)))
        r["mute"] = d(measure(im, sched, 0, 0, sample=(126, C, 0)))
        if nm == "new":
            r["lfirst"] = d(measure(im, sched, STRIP, 0, sample=(126, C, 0)))
            r["lsecond"] = d(measure(im, sched, STRIP, 0, sample=(126, 0, C)))
        G0 = measure(im, sched, gran=(0, 0))
        dg = lambda LR: ([a - b for a, b in zip(LR[0], G0[0])][8], [a - b for a, b in zip(LR[1], G0[1])][8])
        r["gmid"] = dg(measure(im, sched, gran=(C, 0)))
        r["gwide"] = dg(measure(im, sched, gran=(C, C)))
        res[nm] = r
        gc.collect()
    n, o = res["new"], res["old"]
    m = n["mono"][0]
    near = lambda x, y, ref=m: abs(x - y) <= abs(ref) // 20
    print(f"     strip X:$20C {[hex(x) for x in n['strip']]}; mono {n['mono']}; first {n['first']}; second {n['second']}; strip 0 {n['mute']}; "
          f"hard left {n['lfirst']} / {n['lsecond']}; granular mid {n['gmid']} wide {n['gwide']}")
    print(f"     OLD: mono {o['mono']}; first {o['first']}; strip 0 {o['mute']}; granular mid {o['gmid']} wide {o['gwide']}")
    check(all(x == STRIP - 1 or x == STRIP for x in n["strip"]), "the strip held at the device's gain")
    check(m != 0 and n["mono"][0] == n["mono"][1], "WAVE 0: the first sample alone, the same on both sides")
    check(near(n["first"][0], m) and near(n["first"][1], 0), f"WAVE 126, the first sample: on the left ({n['first']})")
    check(near(n["second"][1], m) and near(n["second"][0], 0), f"WAVE 126, the second sample: on the right ({n['second']})")
    check(abs(o["first"][1]) > abs(m) // 4, f"OLD: the first sample on both sides (the device's bug reproduced: {o['first']})")
    check(near(n["mute"][0], 0) and near(n["mute"][1], 0), f"the strip at 0: nothing of MIDI 1 ({n['mute']})")
    check(abs(o["mute"][0]) > abs(m) // 16, f"OLD: the strip at 0, the sides went on ({o['mute']})")
    check(near(n["lfirst"][0], m) and near(n["lfirst"][1], 0) and near(n["lsecond"][0], 0) and near(n["lsecond"][1], 0),
          f"hard left: the first on the left, the second silent, R = 0 ({n['lfirst']}, {n['lsecond']})")
    gm = n["gmid"][0]
    check(gm != 0 and n["gmid"][0] == n["gmid"][1], f"the granular mid on both sides ({n['gmid']})")
    check(near(n["gwide"][0], 0, gm) and near(n["gwide"][1], 2 * gm, gm), f"the granular, every grain on the right: L = 0, R = 2 x the mid ({n['gwide']})")
    check(abs(o["gwide"][0]) > abs(o["gmid"][0]) // 2, f"OLD: the granular's width collapsed ({o['gwide']} with the mid {o['gmid']})")
    print(f"{man.get('marker', '?')} STRIPG DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
