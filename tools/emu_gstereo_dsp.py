"""SC44.7 DSP test (granular_dsp.use_stereo, core 0): the sides of the granular voices added to the mix before the master filter, on the whole core 0
(dsp_session) with the engine's real traffic (emu_sc43_9_dsp.schedule); core 1 is not emulated: its OUT (the mid) and SOUT (the sides) are written by
the test.

    python tools/emu_gstereo_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

  * MIDI 1's voice in the granular engine (ACT 2, DFLAGS bit 4), OUT = c, SOUT = 0: the mix arrays X:$2C02 (L) / X:$2C24 (R) right after smp_post
    (P:$D55) get the mid m on both sides (centre pan) -- the reference;
  * SOUT = c (every grain on the right, the whole width): L = 0 and R = 2 m (within the rounding): the sides at the mid's level (S_K);
  * SOUT = -c: L = 2 m, R = 0;
  * the copy of X:$56..$59 (levels and pans of MIDI 1 / 2) in the shared memory (SHPAN) for core 1;
  * no granular voice (SOUT = 0): the whole core 0 the same as the previous build's, block by block, but for the new code's words.
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402
import granular_dsp as GD  # noqa: E402

VB, OSB = 0x3B80, 0x3900
ACT, NOTE, GNEW = VB + 20, VB + 19, VB + 22
PF_L, PF_R, AFTER = 0x2C02, 0x2C24, 0xD55


def run(img, sched, blocks, force, at_block, dumps_after):
    s = DS.Session(img)
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    for b in range(blocks):
        if b < len(sched):
            for w, addr in sched[b]:
                if b >= 60 and addr == VB and (w >> 16) & 0x7F in (17, 18, 19, 20, 21, 22): continue
                Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in force(b)]
        if b == at_block:
            Ls += [f'PC {DS.STUB:x}', f'STOP {AFTER:x}', 'RUN'] + ['DUMPX %x %d' % (a_, n_) for a_, n_ in dumps_after]
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


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def measure(img, sched, c, s):
    T0, TM = 60, 75
    def force(b):
        f = []
        if b >= T0:
            f += [(ACT, 2), (NOTE, 60), (OSB + 21, 16), (VB + 13, 0)]
            f += [(0x56, 100 << 15), (0x57, 0x400000)]                    # MIDI 1: level 100, pan centre (as the stock group writes them)
            f += [(GD.OUT + i, c if (i & 63) < 32 else 0) for i in range(128)]
            f += [(GD.SOUT + i, s if (i & 63) < 32 else 0) for i in range(128)]
        return f
    R = run(img, sched, TM + 2, force, TM, [(PF_L, 32), (PF_R, 32), (VB + GD.GCUR_OFF, 1), (VB + GD.VCAON_OFF, 1), (0x56, 4), (GD.SHPAN, 4)])
    gc.collect()
    g = lambda a: R[a][0]
    return [s24(x) for x in g(PF_L)], [s24(x) for x in g(PF_R)], g(VB + GD.GCUR_OFF)[0], g(VB + GD.VCAON_OFF)[0], g(0x56), g(GD.SHPAN)


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sched = M.schedule(prev, pman)
    C = 0x200000
    L0, R0, gcur, von, lv, shp = measure(img, sched, 0, 0)
    Lm, Rm, *_ = measure(img, sched, C, 0)
    m = [a - b for a, b in zip(Lm, L0)]; mr = [a - b for a, b in zip(Rm, R0)]
    print(f"     reference: GCUR {gcur:#x} (VCA {'on' if von else 'off'}), X:$56..$59 {[hex(x) for x in lv]}, the mid in L {m[8:12]}, in R {mr[8:12]}")
    check(m[8] != 0 and m == mr, "the mid of the granular voice reaches L and R equally (centre pan)")
    check(shp == lv, f"SHPAN = X:$56..$59 for core 1 ({[hex(x) for x in shp]})")
    Lr, Rr, *_ = measure(img, sched, C, C)
    dl = [a - b for a, b in zip(Lr, L0)]; dr = [a - b for a, b in zip(Rr, R0)]
    mm = max(abs(x) for x in m)
    tol = lambda x, y: abs(x - y) <= 8 + mm // 256                                  # (S_COEF is the mid's gain rounded: 0.1 %)
    check(all(tol(x, 0) for x in dl[4:]) and all(tol(x, 2 * y) for x, y in zip(dr[4:], m[4:])),
          f"SOUT = OUT: L = 0, R = 2 x the mid (L {dl[8:10]}, R {dr[8:10]}, mid {m[8:10]})")
    Ll, Rl, *_ = measure(img, sched, C, -C)
    dl = [a - b for a, b in zip(Ll, L0)]; dr = [a - b for a, b in zip(Rl, R0)]
    check(all(tol(x, 2 * y) for x, y in zip(dl[4:], m[4:])) and all(tol(x, 0) for x in dr[4:]),
          f"SOUT = -OUT: L = 2 x the mid, R = 0 (L {dl[8:10]}, R {dr[8:10]})")
    Rn, _ = M.dsp_run(img, sched); gc.collect()
    Rp, _ = M.dsp_run(prev, sched); gc.collect()
    check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{len(Rn)} / {len(Rp)} dumps")
    for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
        diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
        check(sn == sp_ and not diff, f"no granular voice, block {M.CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF as the previous build's (differences at {[hex(i) for i in diff[:12]]})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
