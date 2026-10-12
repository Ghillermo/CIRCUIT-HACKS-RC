"""Run DSP56300 code with dsptool (dsp56kEmu interpreter)."""
import subprocess, tempfile, os, sys, shutil
sys.path.insert(0, os.path.dirname(__file__))
from dsp56 import jsr, jmp, to_bytes
import sys as _sys; _sys.path.insert(0, __import__("os").path.dirname(__file__))
from dsptool_path import TOOL  # noqa: E402
STUB = 0x7000


def run(pwords, call, mem=(), dumps=(), maxins=2_000_000, regs_code=(), pc=None, stop=None):
    """pwords: full P image (list of words from 0). call: P address to jsr.
    mem: [(space, addr, [words])]. dumps: [(space, addr, n)] -> dict."""
    d = tempfile.mkdtemp()
    pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(to_bytes(pwords))
    stub = list(regs_code) + jsr(call) + jmp(STUB + len(regs_code) + 2)
    lines = [f'LOADP {pb} 0', 'P %x %s' % (STUB, ' '.join('%06x' % x for x in stub))]
    for sp, addr, ws in mem:
        lines.append('%s %x %s' % (sp.upper(), addr, ' '.join('%06x' % (x & 0xFFFFFF) for x in ws)))
    if pc is None:
        lines += [f'PC {STUB:x}', f'STOP {STUB + len(regs_code) + 2:x}']
    else:
        lines += [f'PC {pc:x}', f'STOP {stop:x}']
    lines += [f'MAX {maxins}', 'RUN']
    for sp, addr, n in dumps:
        lines.append(f'DUMP{sp.upper()} {addr:x} {n}')
    sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(lines) + '\n')
    try:
        out = subprocess.run([TOOL, 'run', sc], capture_output=True, text=True).stdout
    finally:
        shutil.rmtree(d, ignore_errors=True)                       # every run used to leave its 48 KB directory behind (5 GB by 2026-10-10)
    res, ran = {}, None
    for l in out.splitlines():
        if l.startswith('RAN'): ran = l
        elif l[:1] in 'XYP' and ':' in l:
            k, v = l.split(':', 1); sp, a = k.split()
            res[(sp.lower(), int(a, 16))] = [int(x, 16) for x in v.split()]
    return res, ran
