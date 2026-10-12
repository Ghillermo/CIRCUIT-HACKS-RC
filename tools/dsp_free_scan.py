"""Find DSP core-0 X/Y addresses that are provably unused, for patch state.

An address is a candidate only if it is
  * never read or written in a whole-core emulation session (init, ARM tables, full parameter dump,
    every project / drum group handler, synth 1+2 chords, drum hits, note-offs, many audio blocks),
  * never written by the ARM in that session (SHI capture),
  * not an absolute operand anywhere in the program, and
  * not inside [base, base+span) of any immediate address loaded into an address register.

    python tools/dsp_free_scan.py stock.bin [image_for_program.bin]
"""
from __future__ import annotations
import re, struct, subprocess, sys, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dsp_session import Session, dsp_program, TOOL  # noqa: E402

GROUPS = 0x0805B3B0
DRUM_HANDLERS = (0x080287DE, 0x0802887A, 0x0802890E, 0x080289A2)


def session_trace(img, blocks=24):
    s = Session(img)
    for i in range(10):
        fn = struct.unpack('<I', img[GROUPS - 0x08010000 + 4 * i:][:4])[0]
        s.capture(f'group{i}', fn & ~1)
    for h in DRUM_HANDLERS: s.capture('drum', h)
    for msg in ([0x90, 60, 100], [0x90, 64, 90], [0x90, 67, 80], [0x91, 48, 100], [0x91, 55, 100],
                [0x99, 60, 120], [0x99, 62, 110], [0x99, 64, 100], [0x99, 65, 90]):
        s.midi(bytes(msg))
    t = tempfile.mktemp()
    _, rans = s.run(blocks=blocks, trace=t, per_block=False)
    for msg in ([0x80, 60, 0], [0x80, 64, 0], [0x81, 48, 0]):
        s.midi(bytes(msg))
    t2 = tempfile.mktemp()
    _, rans2 = s.run(blocks=blocks * 2, trace=t2, per_block=False)
    a, b = open(t, 'rb').read(), open(t2, 'rb').read()
    tr = bytes(x | y for x, y in zip(a, b))
    arm = {(sp, ad) for _, ws in s.events for _, sp, ad, _ in ws} | {(sp, ad) for _, sp, ad, _ in s.init_writes}
    return tr[:0x80000], tr[0x80000:], arm, rans + rans2


def static_refs(prog_words_asm):
    absx, absy, bases = set(), set(), set()
    for l in prog_words_asm.splitlines():
        t = l[30:] if len(l) > 30 else ''
        for sp, a in re.findall(r'\b([xy]):[<>]?\$([0-9a-f]+)\b', t):
            v = int(a, 16)
            if v < 0xFFFF80: (absx if sp == 'x' else absy).add(v)
        for a in re.findall(r"#[<>]?\$([0-9a-f]+),r[0-7]", t):
            bases.add(int(a, 16))
    return absx, absy, bases


def main(stock_path, prog_path=None):
    stock = Path(stock_path).read_bytes()
    progimg = Path(prog_path).read_bytes() if prog_path else stock
    trx, try_, arm, rans = session_trace(progimg)
    print('runs:', rans)
    pb = tempfile.mktemp(); open(pb, 'wb').write(dsp_program(progimg))
    asm = subprocess.run([TOOL, 'dis', pb, '0'], capture_output=True, text=True).stdout
    absx, absy, bases = static_refs(asm)
    SPAN = 0x100
    near = set()
    for b in bases:
        if b < 0x8000: near.update(range(b, b + SPAN))
    res = {}
    for sp, tr, absr in (('x', trx, absx), ('y', try_, absy)):
        free = [a for a in range(0x0, 0x4000) if not tr[a] and (sp, a) not in arm and a not in absr and a not in near]
        runs, cur = [], None
        for a in free:
            if cur and a == cur[1] + 1: cur[1] = a
            else:
                cur = [a, a]; runs.append(cur)
        runs = [r for r in runs if r[1] - r[0] >= 7]
        res[sp] = runs
        print(sp, 'free runs >= 8 words:', [(hex(x), hex(y), y - x + 1) for x, y in runs][:30])
        print(sp, 'touched (emu):', sum(1 for a in range(0x4000) if tr[a]))
    return res


if __name__ == '__main__':
    main(*sys.argv[1:3])
