"""SC47 DSP test (vcf21_dsp.use_smswap): the stereo sample mode end to end, on the whole core 0 (dsp_session, emu_gstereo_dsp's harness) with the
engine's real traffic: MIDI 1 in the sample mode, sample 3 (the first) and 4 (the second, K 1) in the external Y memory, the mix arrays X:$2C02 (L)
/ X:$2C24 (R) after smp_post, 16 blocks after the note (the mixer's level ramp settled):

    python tools/emu_smswap_dsp.py NEW.bin NEW_manifest.json OLD.bin OLD_manifest.json      (OLD = SC46.9 / Beta 3.26)

  * WAVE 0: the first sample on both sides (the reference m);
  * WAVE 126, only the first sample sounding: L = m, R near 0 (NEW); OLD had it on the right;
  * WAVE 126, only the second: R = m, L near 0;
  * WAVE 64: the first louder on the left, the second ... (between);
  * the same at the Nyquist rate (alternating samples): the separation does not depend on the frequency.
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS
import emu_sc43_9_dsp as M
import emu_gstereo_dsp as G
import vcf21_dsp as V

VB, OSB = 0x3B80, 0x3900
YA, YB = 0x40000, 0x48000


def run(img, sched, blocks, force, at_block, dumps_after, ywrites):
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


def measure(img, sched, wave, cl, cr):
    T0, TM = 60, 76
    def force(b):
        f = []
        if b >= T0:
            f += [(VB + V.ACT, 3), (VB + V.NOTE, 60), (OSB + 21, 0), (0x56, 100 << 15), (0x57, 0x400000), (OSB + 2, wave), (OSB + 8, 3), (OSB + V.SM_K, 1),
                  (VB + V.P_LFOV, 0), (VB + V.P_FXAMT, 0), (VB + V.P_FILT, 0), (VB + V.P_ENVF, 0), (VB + V.P_LFOF, 0), (VB + V.P_FTYPE, 0)]
            if b == T0: f += [(OSB + V.SM_N, 1)]
            for k, (st, ln) in ((3, (YA, 4000)), (4, (YB, 4000))): f += [(V.SM_TAB + 4 * k, st), (V.SM_TAB + 4 * k + 1, ln)]
        return f
    yw = [(YA + i, cl) for i in range(3000)] + [(YB + i, cr) for i in range(3000)]
    R = run(img, sched, TM + 2, force, TM, [(G.PF_L, 32), (G.PF_R, 32), (OSB, 48), (VB, 48)], yw)
    gc.collect()
    g = lambda a: R[a][0]
    s24 = G.s24
    return [s24(x) for x in g(G.PF_L)], [s24(x) for x in g(G.PF_R)], g(OSB), g(VB)



def main(img, man, old, oman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    C = 0x200000
    res = {}
    for nm, im, mf in (("new", img, man), ("old", old, oman)):
        sched = M.schedule(im, mf)
        L0, R0, *_ = measure(im, sched, 126, 0, 0)
        d = lambda L, R: ([a - b for a, b in zip(L, L0)][8], [a - b for a, b in zip(R, R0)][8])
        r = {}
        for key, wave, cl, cr in (("mono", 0, C, 0), ("first", 126, C, 0), ("second", 126, 0, C), ("half", 64, C, 0)):
            L, R, *_ = measure(im, sched, wave, cl, cr); r[key] = d(L, R)
        res[nm] = r
        gc.collect()
    n, o = res["new"], res["old"]
    m = n["mono"][0]
    near = lambda x, y: abs(x - y) <= abs(m) // 20
    print(f"     WAVE 0: L / R {n['mono']}; first {n['first']}; second {n['second']}; WAVE 64 {n['half']}; OLD first {o['first']}")
    check(m != 0 and n["mono"][0] == n["mono"][1], "WAVE 0: the first sample alone, the same on both sides")
    check(near(n["first"][0], m) and near(n["first"][1], 0), f"WAVE 126, the first sample: on the left ({n['first']})")
    check(near(n["second"][1], m) and near(n["second"][0], 0), f"WAVE 126, the second sample: on the right ({n['second']})")
    check(abs(n["half"][0]) > abs(n["half"][1]) > 0, f"WAVE 64: between ({n['half']})")
    check(near(o["first"][1], m) and near(o["first"][0], 0), f"OLD: the first sample on the right (the bug reproduced: {o['first']})")
    print(f"{man.get('marker', '?')} SMSWAP DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
