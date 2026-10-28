"""SC48.1 DSP test (cueclk + dsp56.use_shortmsb): the metronome's click on the cue side only, with the cue flag; everything else as SC48.

    python tools/emu_cueclk_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC48)

  * the program: the stock part differs only in the hooks' jsr / jmp targets and the click ($2291 = jsr cc_setup, the loop body at $229B); the
    appended code holds no two-word `move #>$hh0000,D` any more and is shorter;
  * the whole core 0 of both builds (emu_sc43_9_dsp's harness: the engine's traffic, drum hits, Synth notes; then FM on MIDI 1 and the sample mode
    on MIDI 2) with the flag 0: X and Y memory 0..$3FFF the same at four points;
  * the click (its trigger word Y:$111 = TRIG, as 0x08028FC2 writes master parameter 0x21:9; the clock's call 0x0803BD58(0xFF, 0, 0x60)
    sends whatever the parameter holds, 0 in the bare emulation; X:$DE = LEVEL in every run) at block T, X / Y dumped after T, T + 1 and T + 4:
    flag 0 = PREV word for word; the click present on L and R of the block (against no click); flag 1 = L of the block as with no click, R as with
    the click, the rest of the memory the same (but the flag word); the output ring's block on 64-word boundaries (the second pointer's
    linear walk never crosses the ring's end).
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402
import emu_shortbr_dsp as SB  # noqa: E402
import cueclk as CC  # noqa: E402

T = 100
TRIG = 0x000101
LEVEL = 0x400000                               # X:$DE, the click's level (0 with the metronome off: the bare emulation)
DUMPS = (T + 1, T + 2, T + 5)
RING = 0x3FF                                   # M7 of the output ring


def run(img, sched, flag=0, click=False, force=(), checks=DUMPS, blocks=T + 6):
    """emu_sc43_9_dsp.dsp_run with the click's trigger at block T and the cue flag written every block."""
    s = DS.Session(img)
    later = {}
    def ev(at, name, fn, *a):
        s.capture(name, fn, *a); later.setdefault(at, []).extend(s.events.pop()[1])
    def midi(at, msg):
        s.midi(bytes(msg)); later.setdefault(at, []).extend(s.events.pop()[1])
    for d in range(4): ev(2 + 3 * d, f"hit{d}", 0x08051B54, d, 100 - 10 * d)
    midi(5, (0x90, 60, 100)); midi(9, (0x91, 67, 90))
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    for b in range(blocks):
        Ls += s._mem(later.get(b, []))
        if b < len(sched):
            for w, addr in sched[b]: Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (a_, v_) for a_, v_ in force] + ['X %x %06x' % (CC.FLAG, flag), 'X de %06x' % LEVEL]
        if b == T: Ls += ['DUMPY ffd 1'] + (['Y 111 %06x' % TRIG] if click else [])
        Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
        if b + 1 in checks: Ls += ['DUMPX 0 16384', 'DUMPY 0 16384']
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
    try:
        out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
    dumps = []
    for l in out.splitlines():
        if l[:1] in 'XY' and ':' in l:
            k, v = l.split(':', 1); sp, a = k.split()
            dumps.append((sp.lower(), int(a, 16), [int(x, 16) for x in v.split()]))
    return dumps


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    pn, pp = DS.dsp_program(img), DS.dsp_program(prev)
    wn = [int.from_bytes(pn[i:i + 3], 'big') for i in range(0, len(pn), 3)]
    wp = [int.from_bytes(pp[i:i + 3], 'big') for i in range(0, len(pp), 3)]
    base = 0x2A5E
    click = set(range(CC.AT_X1, CC.AT_X1 + 2)) | set(range(CC.AT_BODY, CC.AT_BODY + 5))
    moved = [i for i in range(base) if wn[i] != wp[i] and i not in click]
    jumps = all(i > 0 and wp[i - 1] in (0x0BF080, 0x0AF080) and wn[i - 1] == wp[i - 1] and wp[i] >= base and wn[i] >= base for i in moved)
    check(jumps, f"the stock part: only the hooks' jsr / jmp targets moved besides the click ({len(moved)} words)")
    cc = int(man["report"]["sc16"]["dsp_labels"]["cc_setup"], 16)
    check(wn[CC.AT_X1:CC.AT_X1 + 2] == [0x0BF080, cc] and wn[CC.AT_BODY:CC.AT_BODY + 5] == CC.NEW_BODY,
          f"the click: jsr cc_setup (${cc:x}) and the two-pointer body")
    longmsb = lambda ws: sum(1 for i in range(base, len(ws) - 1) if ws[i] & 0xC0FFFF == 0x40F400 and (ws[i] >> 16) & 0x3F in (4, 5, 6, 7, 0x16, 0x17)
                             and ws[i + 1] & 0xFFFF == 0)
    check(longmsb(wn) < longmsb(wp) and len(wn) <= 0x4000, f"two-word move #>$hh0000,D: {longmsb(wp)} -> {longmsb(wn)}; the program "
                                                            f"${len(wp):x} -> ${len(wn):x} ({0x4000 - len(wn)} words free)")

    sched = M.schedule(prev, pman)
    for name, force in (("the engine's traffic", ()), ("with FM on MIDI 1 and the sample mode on MIDI 2", SB.fm_force())):
        Rn, _ = M.dsp_run(img, sched, force=force); gc.collect()
        Rp, _ = M.dsp_run(prev, sched, force=force); gc.collect()
        check(len(Rn) == len(Rp) == 2 * len(M.CHECKS), f"{name}: {len(Rn)} / {len(Rp)} dumps")
        for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
            diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
            check(sn == sp_ and not diff, f"{name}, block {M.CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF the same (differences at {[hex(i) for i in diff[:12]]})")

    sch = sched[:T + 6]
    P = run(prev, sch, click=True); gc.collect()
    A = run(img, sch, click=True); gc.collect()
    N = run(img, sch); gc.collect()
    C = run(img, sch, flag=1, click=True); gc.collect()
    Z = run(img, sch, flag=1); gc.collect()
    old = [v for s_, a, v in A if s_ == 'y' and a == 0xFFD][0][0]
    check(old & 63 == 0, f"the block's output in the ring at ${old:x} (on a 64-word boundary)")
    mem = lambda R, j, sp: [v for s_, a, v in R if s_ == sp and a == 0 and len(v) == 16384][j]
    for j, blk in enumerate(DUMPS):
        for sp in ('x', 'y'):
            a_, p_ = mem(A, j, sp), mem(P, j, sp)
            diff = [i for i in range(16384) if a_[i] != p_[i]]
            check(not diff, f"after block {blk - 1}, {sp.upper()}: the flag 0 with the click = SC48 (differences at {[hex(i) for i in diff[:8]]})")
        xa, xn, xc, xz = (mem(R, j, 'x') for R in (A, N, C, Z))
        # the ring words of block T (old .. old + 63, modulo the ring)
        ring0 = old - (old & RING)
        Lw = [ring0 + ((old - ring0 + 2 * i) & RING) for i in range(32)]
        Rw = [ring0 + ((old - ring0 + 2 * i + 1) & RING) for i in range(32)]
        if j == 0:
            check(any(xa[i] != xn[i] for i in Lw) and any(xa[i] != xn[i] for i in Rw),
                  f"block {T}: the click on L ({sum(xa[i] != xn[i] for i in Lw)} words) and R ({sum(xa[i] != xn[i] for i in Rw)}) without the flag")
            check(all(xc[i] == xn[i] for i in Lw), f"block {T}, the flag 1: L as with no click ({sum(xc[i] != xn[i] for i in Lw)} words differ)")
            check(all(xc[i] == xa[i] for i in Rw), f"block {T}, the flag 1: R as with the click ({sum(xc[i] != xa[i] for i in Rw)} words differ)")
        other = [i for i in range(16384) if i not in set(Lw) | set(Rw) | {CC.FLAG} and not (ring0 <= i <= ring0 + RING)]
        check(all(xc[i] == xa[i] for i in other) and all(xz[i] == xn[i] for i in other),
              f"after block {blk - 1}: outside the ring and the flag, X the same with and without the flag")
        ya, yc = mem(A, j, 'y'), mem(C, j, 'y')
        check(ya == yc, f"after block {blk - 1}: Y the same with and without the flag")
        if j:
            # later blocks: the click still decaying, written into the block that the ring pointer points at then: L untouched with the flag
            ycur = mem(A, j, 'y')[0xFFD]
            st = ring0 + ((ycur - ring0 - 64) & RING)
            Lb = [ring0 + ((st - ring0 + 2 * i) & RING) for i in range(32)]
            Rb = [ring0 + ((st - ring0 + 2 * i + 1) & RING) for i in range(32)]
            check(all(xc[i] == xn[i] for i in Lb) and all(xc[i] == xa[i] for i in Rb) and any(xa[i] != xn[i] for i in Rb),
                  f"after block {blk - 1} (the tail of the click, ${st:x}): the flag 1 = L clean, R = the click "
                  f"({sum(xa[i] != xn[i] for i in Rb)} words of click)")
    print(f"{man.get('marker', '?')} CUECLK DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails



if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
