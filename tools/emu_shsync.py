"""SC46.1 tests (vcf21_dsp.use_shsync, modmx.use_shsync): the sample & hold of a synced LFO with the transport running.

    python tools/emu_shsync.py NEW.bin NEW_manifest.json [OLD.bin OLD_manifest.json]      (OLD = SC46: no new values)
  * the engine's LFO on the whole core 0 (emu_sc43_9_dsp's traffic and harness): MIDI 1's LRATE synced (-8), its increment in OS2B0 + 40 as
    lfosync.py writes it, the phase set to $800000 every 60 blocks as lfosync.py does at every cycle's start: shapes 5 (sample & hold) and 6
    (slewed) take a new value at every one of those starts; the free LFO (LRATE +63) as before (a new value at each wrap of the phase);
  * the matrix's LFO 2 (c_mxsync on its block): a new tick that sets the phase back to the cycle's start stores it less the advance (the add that
    follows overflows: a new value); a tick a little back, or forward, stores the phase itself.
"""
from __future__ import annotations
import gc, json, os, shutil, struct, subprocess, sys, tempfile
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp_session as DS  # noqa: E402
import emu_sc43_9_dsp as M  # noqa: E402

VB = 0x3B80
PH, LV, LRATE = VB + 25, VB + 26, VB + 12
LINC = 0x3960 + 40
s24 = lambda v: v - (1 << 24) if v & 0x800000 else v


def dsp(img, sched, shape, lrate, reset_every, blocks=420, inc=0x8000):
    s = DS.Session(img)
    prog = bytearray(DS.dsp_program(img))
    for a in DS.SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
    d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
    Ls = [f'LOADP {pb} 0', 'MAX 2000000000', 'PC 107', 'STOP 25f3', 'RUN'] + s._mem(s.init_writes) + ['PC 25f3', 'STOP 113', 'RUN']
    for _, w in s.events: Ls += s._mem(w)
    Ls.append('P %x %s' % (DS.STUB, ' '.join('%06x' % x for x in [0x0BF080, 0x0001ED, 0x0C0000 | (DS.STUB + 2)])))
    resets = 0
    for b in range(blocks):
        if b < len(sched):
            for w, addr in sched[b]:
                if addr == M.MB[0] and (w >> 16) & 0x7F == 19: w = w & ~(7 << 13) | shape << 13
                Ls.append('X %x %06x' % (addr, w & 0xFFFFFF))
        Ls += ['X %x %06x' % (LRATE, lrate & 0xFFFFFF), 'X %x %06x' % (LINC, inc)]
        if reset_every and b >= 100 and b % reset_every == 0: Ls.append('X %x %06x' % (PH, 0x800000)); resets += 1
        Ls += [f'PC {DS.STUB:x}', f'STOP {DS.STUB + 2:x}', 'RUN', 'DUMPX %x 2' % PH]
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(Ls) + '\n')
    try:
        out = subprocess.run([DS.TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)
    rows = [[int(x, 16) for x in l.split(':', 1)[1].split()] for l in out.splitlines() if l[:1] == 'X' and ':' in l][100:]
    ph = [s24(r[0]) for r in rows]; lv = [r[1] for r in rows]
    wraps = sum(1 for a, b in zip(ph, ph[1:]) if b < a - 0x400000)
    changes = sum(1 for a, b in zip(lv, lv[1:]) if a != b)
    return resets, wraps, changes, len(set(lv))


def matrix(img, man):
    from emu_lfosync import EA
    import modmx as MX, lfosync as LF
    e = EA(img)
    Mx = {k: int(v, 16) for k, v in man["report"]["modmx"]["labels"].items()}
    blk = MX.MXR + MX.T0
    def ptr(fn, st, i): e.call(fn, st, i, maxins=200000); return e.uc.reg_read(UC_ARM_REG_R0)
    e.uc.mem_write(ptr(LF.PARAM_GET, LF.TEMPO, 0), bytes([120]))
    def at(tick, ph0):
        e.uc.mem_write(ptr(LF.PARAM_GET, e.r32(LF.ENG + 0x90), 0), struct.pack("<I", tick))
        e.uc.mem_write(blk + MX.B_PH, struct.pack("<H", ph0))
        e.call(Mx["c_mxsync"], 0, 9, 10, blk, maxins=2_000_000)
        return e.uc.reg_read(UC_ARM_REG_R1), struct.unpack("<H", bytes(e.uc.mem_read(blk + MX.B_PH, 2)))[0]
    e.uc.mem_write(MX.SYNC_RAM, bytes(8))
    r = dict(start=at(960, 0xFF40), back=at(960 + 47, 0x8400), fwd=at(960 + 48, 0x7000))           # 1 bar = 96 ticks: 960 = a cycle's start
    del e; gc.collect()
    return r


def main(img, man, old=None, oman=None):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sched = M.schedule(img, man); gc.collect()
    for shape in (5, 6):
        rs, w, ch, n = dsp(img, sched, shape, -8, 60); gc.collect()
        check(ch >= rs - 1 and n >= rs - 1 and rs >= 4, f"shape {shape}, synced, the phase set to the cycle's start {rs} times: {ch} new values ({n} distinct)" if shape == 5 else
              f"shape {shape} (slewed), synced, {rs} cycle starts: the value moves ({ch} changes, {n} distinct)")
    rs, w, ch, n = dsp(img, sched, 5, 63, 0); gc.collect()
    check(w >= 2 and ch == w, f"shape 5, free (LRATE +63): a new value at each wrap ({w} wraps, {ch} changes)")
    r = matrix(img, man)
    adv = r["start"][0]
    check(r["start"][1] == (-adv) & 0xFFFF and adv > 0, f"matrix LFO 2, synced: the cycle's start stored less the advance ({r['start'][1]:#x}, advance {adv}): the add overflows")
    check(r["back"][1] == ((47 << 16) // 96) and r["fwd"][1] == ((48 << 16) // 96), f"a tick a little back / forward: the phase itself ({r['back'][1]:#x}, {r['fwd'][1]:#x})")
    if old is not None:
        rs, w, ch, n = dsp(old, sched, 5, -8, 60); gc.collect()
        check(ch == 0, f"the build before: shape 5 synced, {rs} cycle starts, {ch} new values")
    print(f"{man.get('marker', '?')} RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    old = Path(a[3]).read_bytes() if len(a) > 4 else None
    om = json.loads(Path(a[4]).read_text()) if len(a) > 4 else None
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), old, om) else 0)
