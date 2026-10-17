"""SC44.1 / RC2.01 DSP tests: the captured sample of Master FX before the master filter (sampler_dsp.use_prefilter).

    python tools/emu_sc44_1_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC44)
Logic (dspemu, sampler_dsp.code with FILT, the two mono arrays X:$2C02 / $2C24 of the mix before the filter, x:$3a frames):
  * a recording holds (L + R) / 2 x 16 of each frame (the level of the old capture: the filter's last stage and P:$269 shift << 2 each), and never
    the sample that plays;
  * a playing sample adds sample / 16 to L and to R;
  * r4 / r5 / r6 / m4 come back, r0 / r1 = X:$2C02 / $2C24 + the frames (as the mix loop leaves them);
  * smp_tail (from a stand-in of fx_hook: jmp smp_tail): m4 back, x0 = X:FX_ON at the chain's second instruction.
With the images:
  * P:$D53 = jsr smp_post (SC44: nop, nop), fx_hook = jmp smp_tail, smp_tail ends with the replaced instruction + jmp fx_hook + 2;
  * the whole core 0 with the engine's traffic (emu_sc43_9_dsp.schedule) and no sample: X / Y 0..$3FFF the same as SC44 block by block but for the
    three saved registers (X:$3D18..$3D1A);
  * the whole core 0, a noise sample playing on a silent master, the master filter in the middle or at one end (X:$CF; its smoothed position
    y:$20A8 and its dry / filtered mix y:$20CB pinned, the master gain y:$7FF = X:$72 at the top: the ARM is not there), the block X:$2E10 read at
    P:$274 (after the filter and the << 2, before Master FX): SC44 has no sample there (it is added later), SC44.1 has it, changed by the filter
    position, with the noise's level in the middle;
    the stack no deeper than SC44's (the capture's base moved to Y:$40000 in the program copies of both: the interpreter keeps no Y memory at $E80000).
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import sampler_dsp as S  # noqa: E402
import dsp56 as D  # noqa: E402

FXH, AT, DRV = 0x0800, 0x1000, 0x2000
TB, TMAX = 0x40000, 0x400
NF = 32
T_ = G.T
LOW_BASE = 0x40000                                    # (the whole-core runs: the capture moved here in the program copy)


def chain():
    """the stand-in for fx_hook: [jmp smp_tail], then from FXH + 2: x0 kept in X:$3C10 and rts"""
    a = D.Asm(FXH)
    a.emit([0, 0])                                                            # (patched below with jmp smp_tail)
    a.emit(T_("move x0,x:>$3c10")); a.emit(D.RTS)
    return a.assemble()


def logic(check):
    S.PRE, S.V34, S.HOLD = True, True, True
    S.use_prefilter()
    w, lab = S.code(AT, TB, TMAX, pre_ret=FXH + 2)
    cw, _ = chain()
    P = [0] * 0x4000
    P[FXH:FXH + len(cw)] = cw; P[FXH:FXH + 2] = D.jmp(lab["smp_tail"]); P[AT:AT + len(w)] = w

    def setx(addr, v): return T_("move #>$%x,x0" % (v & 0xFFFFFF), "move x0,x:>$%x" % addr)
    def go(steps, mem=()):
        drv = T_("move #>$123456,m4", "move #>$111,r4", "move #>$222,r5", "move #>$333,r6", "move #>$444,r0", "move #>$555,r1")
        for s_ in steps: drv += D.jsr(AT) if s_ == "call" else D.jsr(FXH) if s_ == "tail" else s_
        drv += T_("move m4,x:>$3c00", "move r4,x:>$3c01", "move r5,x:>$3c02", "move r6,x:>$3c03", "move r0,x:>$3c04", "move r1,x:>$3c05") + [0x00000C]
        P2 = list(P); P2[DRV:DRV + len(drv)] = drv
        return run(P2, DRV, mem=[('x', 0x3A, [NF]), ('x', G.FX_ON, [0x2A]), ('x', S.MAGIC_AT, [S.MAGIC])] + list(mem), maxins=3_000_000,
                   dumps=[('x', S.SMB, 0x20), ('x', S.PF_L, NF), ('x', S.PF_R, NF), ('y', TB, TMAX), ('x', 0x3C00, 6), ('x', 0x3C10, 1)])
    st = lambda r, k: r[('x', S.SMB)][k - S.SMB]
    Ls, Rs = [0x1000 * (i + 1) for i in range(NF)], [0x0800 * (i + 1) for i in range(NF)]
    arrays = lambda l, r: [('x', S.PF_L, l), ('x', S.PF_R, r)]
    # ---- record
    r, ran = go([setx(S.STATE, 1), "call"], mem=arrays(Ls, Rs))
    y = r[('y', TB)]
    check(st(r, S.LEN) == NF and y[:NF] == [(l + r_) * 8 for l, r_ in zip(Ls, Rs)], f"the capture = (L + R) / 2 x 16 of the mix before the filter ({ran})")
    check(r[('x', S.PF_L)] == Ls and r[('x', S.PF_R)] == Rs, "the mix itself untouched by a recording")
    regs = r[('x', 0x3C00)]
    check(regs == [0x123456, 0x111, 0x222, 0x333, S.PF_L + NF, S.PF_R + NF], f"m4 / r4 / r5 / r6 back, r0 / r1 = the ends of the arrays ({[hex(v) for v in regs]})")
    # ---- play
    LENP = 300
    ramp = [(i + 1) * 0x100 for i in range(LENP)]
    base = [('y', TB, ramp), ('x', S.LEN, [LENP]), ('x', S.PREV, [0])]
    pre = setx(S.SF, 0) + setx(S.EF, 0x7FFFFF) + setx(S.INCI, 1) + setx(S.INCF, 0) + setx(S.MODE, 0) + setx(S.CMD, 1)
    r, _ = go([pre, "call"], mem=base + arrays([0] * NF, [0] * NF))
    check(r[('x', S.PF_L)] == [v >> 4 for v in ramp[:NF]] and r[('x', S.PF_R)] == [v >> 4 for v in ramp[:NF]] and st(r, S.PLAY) == 1,
          "CMD 1 on a silent mix: the sample / 16 on L and R (x 16 after the filter: as before)")
    r, _ = go([pre, "call"], mem=base + arrays(Ls, Rs))
    check(r[('x', S.PF_L)] == [l + (v >> 4) for l, v in zip(Ls, ramp)] and r[('x', S.PF_R)] == [l + (v >> 4) for l, v in zip(Rs, ramp)],
          "on a mix with signal: the mix + the sample / 16")
    regs = r[('x', 0x3C00)]
    check(regs == [0x123456, 0x111, 0x222, 0x333, S.PF_L + NF, S.PF_R + NF], f"after a playback too ({[hex(v) for v in regs]})")
    # ---- a recording while a sample plays never holds it
    r, _ = go([pre, "call", setx(S.STATE, 1), "call"], mem=base + arrays([0] * NF, [0] * NF))
    y = r[('y', TB)]
    first = [(v >> 4) * 2 * 8 for v in ramp[:NF]]                            # the first call's sample / 16 left in L and R: the master of the second call
    check(y[:NF] == first and st(r, S.PLAY) == 0, "recording while playing: the capture = the mix only, the playback stopped")
    # ---- the tail
    r, _ = go([setx(G.FX_ON, 0x2A), "tail"])
    check(r[('x', 0x3C00)][0] == 0x123456 and r[('x', 0x3C10)] == [0x2A], f"smp_tail: m4 back, x0 = X:FX_ON at fx_hook + 2 ({r[('x', 0x3C10)]})")


def prog(img):
    from dsp_session import dsp_program
    sp = dsp_program(img); return [int.from_bytes(sp[k:k + 3], 'big') for k in range(0, len(sp), 3)]


def whole(img, extra_blocks, blocks, dumps_at, spmax=False):
    """the whole core 0 (dsp_session) with no traffic: `extra_blocks(b)` -> script lines for block b; dumps of X:$2E10 (64 words) at the blocks dumps_at,
    taken at P:$274: after the master filter and the << 2, before Master FX (here, with no ARM, the Master FX chain leaves the block silent)"""
    import dsp_session as DS
    s = DS.Session(img)
    p = bytearray(DS.dsp_program(img))
    for a_ in DS.SPIN_NOPS: p[3 * a_:3 * a_ + 3] = b'\0\0\0'
    for k in range(0x2A5E, len(p) // 3):                                     # the capture's base -> Y:LOW_BASE (the interpreter keeps no Y memory at $E80000)
        if int.from_bytes(p[3 * k:3 * k + 3], 'big') == S.HIGH_BASE: p[3 * k:3 * k + 3] = LOW_BASE.to_bytes(3, 'big')
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(p)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    if spmax: Ls.append('SPMAX')                                             # (before the runs: it tracks from here on)
    for b in range(blocks):
        Ls += extra_blocks(b)
        if b in dumps_at:                                                    # the master after the filter, before Master FX (P:$274): then the block goes on
            Ls += [f'PC {DS.STUB:x}', 'STOP 274', 'RUN', 'DUMPX %x %d' % (G.BUF, 2 * 32), f'STOP {DS.STUB + 2:x}', 'RUN']
        else:
            Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
    try:
        out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
    rows = [[int(x, 16) for x in l.split(':', 1)[1].split()] for l in out.splitlines() if l.startswith('X ') and ':' in l]
    sp = [int(l.split()[1]) for l in out.splitlines() if l.startswith('SPMAX')]
    return rows, (sp[0] if sp else None)


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def main(img=None, man=None, prev=None, pman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    logic(check)
    if img is not None:
        dl = {k: int(v, 16) for k, v in man["report"]["sc16"]["dsp_labels"].items()}
        P0 = prog(img)
        check(P0[S.PF_AT:S.PF_AT + 2] == D.jsr(dl["smp_post"]) and P0[dl["fx_hook"]:dl["fx_hook"] + 2] == D.jmp(dl["smp_tail"]),
              "P:$D53 = jsr smp_post, fx_hook = jmp smp_tail")
        tail = T_("move x:>$%x,x0" % G.FX_ON) + D.jmp(dl["fx_hook"] + 2)
        hit = [k for k in range(dl["smp_tail"], len(P0) - 3) if P0[k:k + 4] == tail]
        check(len(hit) == 1 and len(P0) <= 0x4000, f"smp_tail ends with the replaced instruction + jmp fx_hook + 2; the program ends at P:${len(P0):x}")
        if prev is not None:
            P1 = prog(prev)
            check(P1[S.PF_AT:S.PF_AT + 2] == [0, 0], "SC44: nop, nop at P:$D53")
            # ---- no sample: the whole core the same
            import emu_sc43_9_dsp as M
            sched = M.schedule(prev, pman)
            Rn, _ = M.dsp_run(img, sched); gc.collect()
            Rp, _ = M.dsp_run(prev, sched); gc.collect()
            ok_ = len(Rn) == len(Rp) == 2 * len(M.CHECKS)
            skip = set(range(S.SAVF4, S.SAVF6 + 1))
            for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
                diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y and not (sn == 'x' and i in skip)]
                check(ok_ and sn == sp_ and not diff, f"no sample, block {M.CHECKS[k // 2]}, {sn.upper()}: as SC44 but X:$3D18..$3D1A (differences at {[hex(i) for i in diff[:12]]})")
            # ---- a sample playing, the master filter in the middle / at one end
            import random
            rnd = random.Random(7)
            NS, T0 = 4000, 40
            noise = [(rnd.randrange(-0x6000, 0x6000) << 8) & 0xFFFF00 for _ in range(NS)]
            def blocks_for(fpos):
                def f(b):
                    out = ['X cf %06x' % (fpos << 16), 'Y 20a8 %06x' % (fpos << 16), 'Y 20cb %06x' % (0 if fpos == 64 else 0x7FFFFF),
                           'X 72 7fffff', 'Y 7ff 7fffff']                     # (the filter's smoothed position and dry / filtered mix, the master gain: settled)
                    if b == 2: out += ['Y %x %s' % (LOW_BASE + i, ' '.join('%06x' % v for v in noise[i:i + 64])) for i in range(0, NS, 64)]
                    if b == T0:
                        for addr, v in ((S.LEN, NS), (S.SF, 0), (S.EF, 0x7FFFFF), (S.INCI, 1), (S.INCF, 0), (S.MODE, 0), (S.STATE, 0), (S.PREV, 0), (S.CMD, 1)):
                            out.append('X %x %06x' % (addr, v))
                    return out
                return f
            at = list(range(T0 + 3, T0 + 40, 4))
            res = {}
            for name, im in (("new", img), ("old", prev)):
                for fpos in (64, 127):
                    res[(name, fpos)] = whole(im, blocks_for(fpos), T0 + 42, set(at), spmax=True); gc.collect()
            rms = lambda rows: (sum(s24(v) ** 2 for r_ in rows for v in r_) / max(1, sum(len(r_) for r_ in rows))) ** 0.5
            o64, o127, n64, n127 = (rms(res[k][0]) for k in (("old", 64), ("old", 127), ("new", 64), ("new", 127)))
            played = [s24(v) for v in noise[3 * 32:(3 + 40) * 32]]                   # (the frames of the playing blocks, roughly)
            rn = (sum(v * v for v in played) / len(played)) ** 0.5
            check(o64 == 0 and o127 == 0, f"SC44: no sample after the filter, before Master FX (it is added later; rms {o64:.0f} / {o127:.0f})")
            check(n64 > 0 and res[("new", 64)][0] != res[("new", 127)][0] and abs(n127 - n64) > 0.05 * n64,
                  f"SC44.1: the sample went through the filter, which changes it (rms {n64:.0f} in the middle, {n127:.0f} at 127)")
            check(0.85 < n64 / rn < 1.15, f"SC44.1 with the filter in the middle: the level of the sample ({n64:.0f} / {rn:.0f})")
            spn, spo = res[("new", 64)][1], res[("old", 64)][1]
            check(spn is not None and spo is not None and 0 < spn <= spo, f"the stack: SPMAX {spn} (SC44: {spo})")
    print(f"{(man or {}).get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    if len(a) > 4: sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
    sys.exit(1 if main() else 0)
