"""SC44 DSP test (vcf21_dsp.use_sampler): the sample source of the own engine on the whole core 0 (dsp_session), with the engine's real traffic
(emu_sc43_9_dsp.schedule) and MIDI 1's voice forced to ACT = 3:

    python tools/emu_sc44_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

  * a ramp in the external Y memory, entries 0 / 5 of the sample table pointing at it (start, length); a new note (GNEW = 1) at note 60 starts
    sample 0 (code 25 = 0) from 0: the position grows 32 a block (the sample as recorded); at note 72 64 a block, at note 48 16;
  * a TRIG of $105 = sample 5 (its start); the block that would pass the end stops it (playing = 0);
  * the VCA open: with a slow attack the gain target is already up at the first block (ENV still near 0);
  * no voice in the sample mode: the whole core 0 the same as the previous build's, block by block, with the same traffic (emu_sc43_9_dsp's
    comparison), but for X:$38CF (where the new build saves n4, the sample's step).
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402

VB, OSB = 0x3B80, 0x3900
ACT, NOTE, GNEW, ENV, GT, P_ATK = VB + 20, VB + 19, VB + 22, VB + 23, VB + 29, VB + 6
SM = OSB + 40                                     # SM_P, SM_F, -, -, SM_S, SM_L, SM_ON, SM_N
RAMP, RLEN = 0x40000, 3000
SAMPLE_TAB = 0x1D8D
N4_SAVE = 0x38C0 + 15                             # vcf21_dsp.SAVX + the index of n4 in its REGS


def run(img, sched, blocks, force, once, every):
    s = DS.Session(img)
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    Ls += ['Y %x %06x' % (RAMP + i, (i * 2000) & 0xFFFF00) for i in range(RLEN)]                     # a ramp (16 bits in the high bits)
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    for b in range(blocks):
        if b < len(sched):
            for w, addr in sched[b]:
                if b >= 60 and addr == VB and (w >> 16) & 0x7F in (17, 18, 19, 20, 21, 22): continue   # MIDI 1's own note / voice messages: the test's
                Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in force(b)]
        Ls += ['X %x %06x' % (a_, v_ & 0xFFFFFF) for a_, v_ in once.get(b, [])]
        Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
        Ls += ['DUMPX %x %d' % (a_, n_) for a_, n_ in every]
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


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sched = M.schedule(prev, pman)
    T0, T1 = 60, 90
    tab = [(SAMPLE_TAB, RAMP), (SAMPLE_TAB + 1, 1000), (SAMPLE_TAB + 20, RAMP + 1000), (SAMPLE_TAB + 21, RLEN - 1000), (OSB + 8, 0), (OSB, 0)]   # (OSB + 0 = TUNE: 0)
    def go(note, trig=1, atk=0):
        force = lambda b: tab + ([(ACT, 3), (NOTE, note), (VB + 13, 0)] if b >= T0 else []) + ([(P_ATK, atk)] if atk else [])   # (+ 13 = LFOV: no tremolo)
        R = run(img, sched, 100, force, {T0 + 1: [(GNEW, trig)]}, [(SM, 8), (VB + 23, 8), (0x3A, 1)])
        gc.collect()
        return R[SM], R[VB + 23], R[0x3A][-1][0]
    sm, _, F = go(60)                                                             # F = the frames of a block (X:$3A)
    p = [r[0] for r in sm]
    d60 = (p[T0 + 8] - p[T0 + 4]) // 4
    check(sm[T0 + 2][6] == 1 and sm[T0 + 2][4] == RAMP and sm[T0 + 2][5] == 1000 and d60 == F, f"note 60: sample 0 from its start ({sm[T0 + 2][4]:#x}, {sm[T0 + 2][5]}), the frames of a block ({d60} / {F})")
    on = [r[6] for r in sm]
    end = next((k for k in range(T0 + 2, len(on)) if on[k] == 0), None)
    check(end is not None and p[end - 1] + 2 * 64 + 1 >= 1000 and max(p[T0 + 2:]) < 1000, f"the end: playing stops at block {end} (position {p[end - 1] if end else '-'}, length 1000)")
    sm72, _, _ = go(72); d72 = (sm72[T0 + 8][0] - sm72[T0 + 4][0]) / 4
    sm48, _, _ = go(48); d48 = (sm48[T0 + 8][0] - sm48[T0 + 4][0]) / 4
    check(abs(d72 - 2 * F) <= 1 and abs(d48 - F / 2) <= 1, f"note 72: {d72} a block (2 x {F}), note 48: {d48} (half)")
    sm5, _, _ = go(60, trig=0x105)
    check(sm5[T0 + 2][4] == RAMP + 1000 and sm5[T0 + 2][5] == RLEN - 1000, f"TRIG $105: sample 5 ({sm5[T0 + 2][4]:#x}, {sm5[T0 + 2][5]})")
    sma, va, _ = go(60, atk=100)
    g = [r[6] for r in va]; env = [r[0] for r in va]
    check(g[T0 + 2] > 0 and env[T0 + 2] == 0 and len(set(g[T0 + 2:T0 + 20])) == 1, f"the VCA open: its target {g[T0 + 2]:#x} with the envelope at 0, steady ({len(set(g[T0 + 2:T0 + 20]))} value)")
    Rn, _ = M.dsp_run(img, sched); gc.collect()
    Rp, _ = M.dsp_run(prev, sched); gc.collect()
    check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{len(Rn)} / {len(Rp)} dumps")
    for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
        diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y and not (sn == 'x' and i == N4_SAVE)]
        check(sn == sp_ and not diff, f"no sample mode, block {M.CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF as the previous build's but n4's slot (differences at {[hex(i) for i in diff[:12]]})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
