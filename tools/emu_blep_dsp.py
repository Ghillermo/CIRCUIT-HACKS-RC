"""SC47.8 DSP test (vcf21_dsp.use_blep + use_foldlim): less aliasing in the MIDI 1 / 2 own synth's oscillator.

    python tools/emu_blep_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.7)

On the dsp56kEmu interpreter with each build's real core-0 program (study_alias_dsp.renderer: MIDI 1, one oscillator, the chain neutral):
  * what must not change, against PREV bit for bit: the sine and the triangle with no fold (shape 50), the sine fully folded at note 60 (the limit
    starts above about note 66) and the morph sine / triangle;
  * the aliasing below 8 kHz (study_alias's ASR, 128 blocks): the saw and the pulse at note 96 under -55 dB, the supersaw under -50 dB (PREV: about
    -18 / -20 / -21), the saw at note 72 under -55 dB; the fully folded sine at note 96 under -30 dB (the target) and 8 dB better than PREV (-24);
  * the instructions a block (the median), reported;
  * the whole core with the engine's traffic (emu_sc43_9_dsp.schedule): the system stack's depth against PREV's (the bscc inside the waves
    subroutine: one level more at most, under 16).
"""
from __future__ import annotations
import gc, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import study_alias as SA  # noqa: E402
import study_alias_dsp as AD  # noqa: E402


def spmax(im, sched):
    """the deepest system stack over 200 blocks of the engine's traffic (as emu_sc45_5_dsp)"""
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


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dw, pw = int(man["report"]["sc16"]["dsp_words"], 16), int(pman["report"]["sc16"]["dsp_words"], 16)
    check(dw <= 0x3FFC, f"core 0 ends at P:${dw:x} (PREV ${pw:x}: +{dw - pw} words)")
    new, old = AD.renderer(img, man), AD.renderer(prev, pman)
    new16, old16 = AD.renderer(img, man, nb=16), AD.renderer(prev, pman, nb=16)
    same = []
    for what, note, wave, shape in (("sine", 60, 0, 50), ("triangle", 72, 42, 50), ("sine fully folded", 60, 0, 100), ("sine / triangle morph", 72, 21, 50)):
        a, b = new16(note, wave, shape), old16(note, wave, shape)
        same.append((what, a[2] == b[2]))
    check(all(x[1] for x in same), f"bit for bit as PREV: {', '.join(w for w, ok in same if ok)}; different: {[w for w, ok in same if not ok]}")
    lows = {}
    for kind, note, wave, shape, limit in (("saw", 96, 84, 0, -55), ("saw", 72, 84, 0, -55), ("pulse", 96, 126, 50, -55), ("supersaw", 96, 84, 100, -50)):
        x, ins, _ = new(note, wave, shape)
        f = AD.asr_super if kind == "supersaw" else AD.asr
        r = f(x, note)
        xo, inso, _ = old(note, wave, shape); ro = f(xo, note)
        lows[(kind, note)] = (r[1], ro[1], ins, inso)
        check(r[1] < limit, f"{kind} note {note}: aliasing below 8 kHz {r[1]:.1f} dB (PREV {ro[1]:.1f}; limit {limit}); {ins} instructions a block (PREV {inso}, +{ins - inso})")
    x, _, _ = new(96, 0, 100); xo, _, _ = old(96, 0, 100)
    r, ro = AD.asr(x, 96), AD.asr(xo, 96)
    check(r[1] < -30 and r[1] < ro[1] - 8, f"the sine fully folded at note 96: aliasing below 8 kHz {r[1]:.1f} dB (PREV {ro[1]:.1f}; the target -30): the drive limited by the pitch")
    import emu_sc43_9_dsp as M
    sched = M.schedule(prev, pman)
    sn, so = spmax(img, sched), spmax(prev, sched); gc.collect()
    check(sn is not None and so is not None and sn <= so + 1 and sn < 15, f"the system stack: at most {sn} levels (PREV: {so})")
    print(f"{man.get('marker', '?')} DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
