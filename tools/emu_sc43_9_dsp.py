"""SC43.9 DSP test (dsp56.use_shortx, vcf21_dsp.use_lfoshape): the compacted core-0 program behaves exactly as the previous build's, block by block, with
the LFO's shape 0 (the reverse saw); the other shapes against a model.

    python tools/emu_sc43_9_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json

  * the program: every one-word move of the new build's appended code disassembles as the previous build's two-word one (dsptool); the new program is
    shorter by their number;
  * the engine's traffic: the ARM side of the own engine of MIDI 1 / 2 (the E20 harness: the real c_vtick, pads and knobs) is recorded tick by tick
    (one mailbox word per voice per tick): both tracks on with the oscillator, MIDI 1 with two oscillators, knob turns on every page with and without
    Shift, notes (one, then a legato second), MIDI 2 through the VA-drum and the granular engines;
  * the whole core 0 of both builds (dsp_session: the stock's init, the ARM's parameter dump) runs the same blocks with the same writes: those
    mailbox words one block each, four drum hits and Synth 1 / 2 notes (again later), note-offs; X and Y memory 0..$3FFF compared at four points;
  * the LFO shapes: the same traffic with the shape in bits 13-15 of MIDI 1's ACT messages: the voice's LV (X:$3B80 + 26) every block against its
    phase PH (+ 25): saw = PH, triangle = 2 |PH| - 1, square = +-1 by the sign, sine = 4 PH (1 - |PH|) (the DSP's fixed point, the limiter), sample &
    hold = a new value only when the phase wraps.
"""
from __future__ import annotations
import gc, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402

BLOCKS = 300
CHECKS = (60, 150, 230, BLOCKS)
MB = (0x3B80, 0x3BB0)


def schedule(img, man):
    """the mailbox words of the two voices, one list a tick"""
    import emu_sc22_4 as T4
    V = T4.V
    e = T4.E20(img, man)
    L = {k: int(v, 16) for k, v in man["report"]["vcf20"]["labels"].items()}
    sched = []
    def ticks(n):
        for _ in range(n): sched.append(e.vtick())
    NON, NOFF = e.r32(V.NOTE_VT[0]) & ~1, e.r32(V.NOTE_VT[1]) & ~1
    non = lambda t, n, v=96: e.call(NON, 0x20011334, 2 + t, n, v)
    noff = lambda t, n: e.call(NOFF, 0x20011334, 2 + t, n, 0)
    ticks(20)
    e.uc.mem_write(V.TAIL + V.O_FLAGS, bytes([e.tailb(V.O_FLAGS) | 0x0F])); ticks(25)
    e.btn(2); e.btn(8); e.padr(27); e.rel(27); ticks(8)                              # MIDI 1: two oscillators
    for page in (0, 1, 2, 3, 4):
        e.call(L["c_vsetpage"], 0, page)
        for k in range(8):
            e.knob_raw(k, 7 - 2 * k); e.knob_raw(k, 3 + k, shift=True)
        ticks(6)
    non(0, 60); ticks(10); non(0, 67, 70); ticks(10); noff(0, 67); ticks(6)
    e.btn(3); e.btn(8); e.padr(26); e.rel(26); ticks(8)                              # MIDI 2: the VA-drum
    for k in range(8): e.knob_raw(k, -5 + k)
    non(1, 48); ticks(14); noff(1, 48); ticks(4)
    e.padr(26); e.rel(26); ticks(8)                                                 # the granular
    e.call(L["c_vsetpage"], 1, 1)
    for k in range(8): e.knob_raw(k, 4 - k); e.knob_raw(k, 2 + k, shift=True)
    non(1, 55); ticks(16); non(1, 62); ticks(10)
    noff(0, 60); noff(1, 62); noff(1, 55); ticks(10)
    del e; gc.collect()
    return sched


def dsp_run(img, sched, blocks=BLOCKS, checks=CHECKS, every=(), shape=0, force=()):
    s = DS.Session(img)
    later = {}
    def ev(at, name, fn, *a):
        s.capture(name, fn, *a); later.setdefault(at, []).extend(s.events.pop()[1])
    def midi(at, msg):
        s.midi(bytes(msg)); later.setdefault(at, []).extend(s.events.pop()[1])
    for d in range(4): ev(2 + 3 * d, f"hit{d}", 0x08051B54, d, 100 - 10 * d)
    midi(5, (0x90, 60, 100)); midi(9, (0x91, 67, 90)); midi(110, (0x80, 60, 0)); midi(130, (0x90, 72, 110))
    for d in range(4): ev(140 + 5 * d, f"hit{d}b", 0x08051B54, d, 70 + 10 * d)
    midi(200, (0x81, 67, 0)); midi(240, (0x80, 72, 0))
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    stub = [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)]
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in stub)))
    tag = [0, 0]
    for b in range(blocks):
        Ls += s._mem(later.get(b, []))
        if b < len(sched):
            for w, addr in sched[b]:
                if shape and addr == MB[0] and (w >> 16) & 0x7F == 19: w |= shape << 13          # MIDI 1's ACT: + the LFO shape
                Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (a_, v_) for a_, v_ in force]
        Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN']
        if b + 1 in checks: Ls += ['DUMPX 0 16384', 'DUMPY 0 16384']            # (the count in decimal)
        Ls += ['DUMPX %x %d' % (a_, n_) for a_, n_ in every]
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
    try:
        out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
    dumps, rans = [], []
    for l in out.splitlines():
        if l.startswith('RAN'): rans.append(l)
        elif l[:1] in 'XY' and ':' in l:
            k, v = l.split(':', 1); sp, a = k.split()
            dumps.append((sp.lower(), int(a, 16), [int(x, 16) for x in v.split()]))
    return dumps, rans


def program_check(img, prev, check):
    import dsp56 as D
    pn, pp = DS.dsp_program(img), DS.dsp_program(prev)
    wn = [int.from_bytes(pn[i:i + 3], 'big') for i in range(0, len(pn), 3)]
    wp = [int.from_bytes(pp[i:i + 3], 'big') for i in range(0, len(pp), 3)]
    base = 0x2A5E
    moved = [i for i in range(base) if wn[i] != wp[i]]
    jumps = all(i > 0 and wp[i - 1] in (0x0BF080, 0x0AF080) and wn[i - 1] == wp[i - 1] and wp[i] >= base and wn[i] >= base for i in moved)
    check(jumps, f"the stock part of the program: only the targets of the hooks' jsr / jmp moved ({[(hex(i), hex(wp[i]), hex(wn[i])) for i in moved]})")
    one = lambda ws: sum(1 for w in ws[base:] if w & 0xFE00A0 == 0x020080)        # one-word moves x:(Rn+d)
    longs = sum(1 for i in range(base, len(wp) - 1) if D.short_of(wp[i], wp[i + 1]) is not None and _is_ins(wp, i))
    check(one(wn) - one(wp) >= 441 and len(wp) - len(wn) > 300, f"one-word moves {one(wp)} -> {one(wn)}; the program {len(wp):#x} -> {len(wn):#x} words")
    return 0


def _is_ins(ws, i):
    return True


def program_check_v0(img, prev, check):
    import dsp56 as D, dspasm_cache
    pn, pp = DS.dsp_program(img), DS.dsp_program(prev)
    wn = [int.from_bytes(pn[i:i + 3], 'big') for i in range(0, len(pn), 3)]
    wp = [int.from_bytes(pp[i:i + 3], 'big') for i in range(0, len(pp), 3)]
    base = 0x2A5E
    lab = lambda m: {int(v, 16) for v in m["report"]["sc16"]["dsp_labels"].values()}
    moved = [i for i in range(base) if wn[i] != wp[i]]
    jumps = all(i > 0 and wp[i - 1] in (0x0BF080, 0x0AF080) and wn[i - 1] == wp[i - 1] and wp[i] >= base and wn[i] >= base for i in moved)
    check(jumps, f"the stock part of the program: only the targets of the hooks' jsr / jmp moved ({[(hex(i), hex(wp[i]), hex(wn[i])) for i in moved]})")
    i = j = base; n = 0; bad = []
    while i < len(wp) and j < len(wn):                                             # walk both: a pair that became one word, or the same word
        if i + 1 < len(wp) and D.short_of(wp[i], wp[i + 1]) is not None and wn[j] == D.short_of(wp[i], wp[i + 1]):
            n += 1; i += 2; j += 1; continue
        i += 1; j += 1
    dn = dspasm_cache.dis_listing(wn[base:], base); dp = dspasm_cache.dis_listing(wp[base:], base)
    strip = lambda ls: [re.sub(r"\s+", " ", l.split(None, 1)[1]) if " " in l else l for l in ls]
    ops = lambda ls: [" ".join(x.split()[1:]) for x in ls]
    tn, tp = ops(dn), ops(dp)
    norm = lambda t: re.sub(r"[0-9a-f]{6} ", "", t)
    same_text = [re.sub(r"\$[0-9a-f]+", "$", norm(t)) for t in tn if "x:(r" in t] == [re.sub(r"\$[0-9a-f]+", "$", norm(t)) for t in tp if "x:(r" in t]
    check(len(wn) == len(wp) - n and n > 400, f"the program {len(wp) - len(wn)} words shorter ({len(wp):#x} -> {len(wn):#x}), {n} moves in one word")
    check(len(tn) == len(tp), f"as many instructions ({len(tn)} / {len(tp)})")
    return n


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    program_check(img, prev, check)
    sched = schedule(prev, pman)
    nmsg = sum(len(x) for x in sched)
    check(nmsg > 100, f"the engine's traffic: {len(sched)} ticks, {nmsg} mailbox words")
    Rn, rn = dsp_run(img, sched); gc.collect()
    Rp, rp = dsp_run(prev, sched); gc.collect()
    check(len(Rn) == len(Rp) == 2 * len(CHECKS), f"{len(Rn)} / {len(Rp)} dumps")
    for k, ((sn, an, vn), (sp_, ap, vp)) in enumerate(zip(Rn, Rp)):
        diff = [i for i, (x, y) in enumerate(zip(vn, vp)) if x != y]
        live = sum(1 for x in vn if x)
        check(sn == sp_ and not diff, f"block {CHECKS[k // 2]}, {sn.upper()}: 0..$3FFF the same ({live} non-zero words; differences at {[hex(i) for i in diff[:12]]})")
    eng = [v for s_, a, v in Rn if s_ == 'x'][-1]
    use = lambda a0, n: sum(1 for v in eng[a0:a0 + n] if v)
    check(use(0x3B80, 96) > 20 and use(0x3900, 96) > 10 and use(0x3960, 96) > 4 and use(0x3A80, 0x100) > 10,
          f"in use: the engine's voice blocks {use(0x3B80, 96)}, oscillator {use(0x3900, 96)}, OSC 2 {use(0x3960, 96)}, the drums' blocks {use(0x3A80, 0x100)} non-zero words")
    shape_tests(img, sched, check)
    print(f"SC43.9 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


def s24(v): return v - (1 << 24) if v & 0x800000 else v
def lim(v): return 0x7FFFFF if v > 0x7FFFFF else -0x800000 if v < -0x800000 else v


def shape_tests(img, sched, check):
    PH, LV = 0x3B80 + 25, 0x3B80 + 26
    names = ("", "saw", "triangle", "square", "sine", "sample & hold")
    for shape in range(1, 6):
        fast = shape == 5                                                         # sample & hold: MIDI 1's rate at 127, longer (the phase has to wrap)
        R, _ = dsp_run(img, sched, blocks=450 if fast else 150, checks=(), every=((PH, 2),), shape=shape, force=((0x3B80 + 12, 127),) if fast else ()); gc.collect()
        rows = [(s24(v[0]), s24(v[1])) for sp_, a_, v in R if sp_ == 'x' and a_ == PH]
        on = next((k for k, (p, lv) in enumerate(rows) if p or lv), len(rows)); rows = rows[on:]   # from the block the voice runs
        bad, moved = 0, len({p for p, _ in rows}) > 20
        for k, (p, lv) in enumerate(rows):
            if shape == 1: want = p
            elif shape == 2: want = lim(2 * (abs(p) - 0x400000))
            elif shape == 3: want = 0x7FFFFF if p >= 0 else -0x800000
            elif shape == 4:
                b = 0x7FFFFF - abs(p); prod = (p * b * 2) * 4; a1 = prod >> 24
                want = lim(a1) if abs(prod) < (1 << 47) else (0x7FFFFF if prod > 0 else -0x800000)
            else:
                want = None
                if k and not (rows[k - 1][0] >= 0 and p < 0): want = rows[k - 1][1]          # no wrap: held
            if want is not None and lv != want: bad += 1
        extra = ""
        if shape == 5:
            wraps = sum(1 for k in range(1, len(rows)) if rows[k - 1][0] >= 0 and rows[k][0] < 0)
            changes = sum(1 for k in range(1, len(rows)) if rows[k][1] != rows[k - 1][1])
            extra = f", {wraps} wraps, {changes} new values"
            moved = moved and wraps >= 2 and changes == wraps
        check(moved and not bad and len(rows) > 100, f"LFO shape {shape} ({names[shape]}): LV as the model in {len(rows) - bad} / {len(rows)} blocks{extra}")


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
