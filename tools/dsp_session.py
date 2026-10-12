"""Whole-core DSP session: ARM-captured init tables + full parameter dump + MIDI events, replayed on dsptool.

    from dsp_session import Session
    s = Session(stock_bin)                      # captures init tables and a full parameter dump
    s.midi(bytes([0x90, 60, 100]))              # capture the SHI writes of any MIDI message (synth 1 = ch 1)
    out = s.run(blocks=8, dumps=[('y', 0x800, 64)])   # init core 0, replay, run N audio blocks (jsr $1ED)
"""
from __future__ import annotations
import os, subprocess, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from emu_sc05 import E, CTX  # noqa: E402
from shi_capture import attach  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_R0  # noqa: E402
from unicorn import UC_HOOK_CODE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
import sys as _sys; _sys.path.insert(0, __import__("os").path.dirname(__file__))
from dsptool_path import TOOL  # noqa: E402
DIRTY = 0x200067FC
STUB = 0x7000
# emulation-only: the inter-core semaphore / sample-counter spin loops never see the other core here
SPIN_NOPS = (0x76A, 0x76F, 0x77D)


DSP_TABLE = 0x08029700                 # [core0 mode0, core0 mode1, core1 mode0, core1 mode1] bootstrap blocks


def dsp_block(img: bytes, core=0):
    """(flash address, word count) of the mode-0 bootstrap block of a core, via the ARM pointer table."""
    a = int.from_bytes(img[DSP_TABLE - 0x08010000 + 8 * core:][:4], 'little')
    o = a - 0x08010000
    return a, int.from_bytes(img[o:o + 3], 'big')


def dsp_program(img: bytes, core=0):
    a, n = dsp_block(img, core)
    o = a - 0x08010000
    return img[o + 6:o + 6 + 3 * n]


class Session:
    def __init__(self, img: bytes):
        self.img = img
        self.e = E(img); self.e.stubs[0x0801B394] = 'delay'
        self.shi = attach(self.e)
        self.e.call(0x08029492, maxins=50_000_000)               # post-upload init: tables + x:$FFF
        self.init_writes = self._take()
        self.full_dump()

    def _take(self):
        w = [x for x in self.shi.writes if x[0] == 0]; self.shi.writes.clear(); return w

    def full_dump(self):
        """Mark every parameter group dirty and run the flush task -> all current parameters."""
        e = self.e
        e.uc.mem_write(DIRTY + 0x16, b'\xff' * 0x2A)
        def h(uc, a, s, d):
            if a == 0x080297A4:
                uc.reg_write(UC_ARM_REG_R0, 1); uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)
        hk = e.uc.hook_add(UC_HOOK_CODE, h)
        e.call(0x080213B0, maxins=50_000_000)
        e.uc.hook_del(hk)
        self.events = [('params', self._take())]

    def capture(self, name, fn, *args):
        """Run any ARM function and append the DSP writes it produces as an event."""
        self.e.call(fn, *args, maxins=20_000_000)
        self.events.append((name, self._take()))

    def midi(self, msg: bytes, flush=True):
        m = 0x2006E000; self.e.uc.mem_write(m, bytes(msg) + b'\0')
        self.e.call(0x08051720, CTX, m, maxins=20_000_000)
        if flush:
            self.e.call(0x0802148C, 0); self.e.call(0x0802148C, 1)
        self.events.append(('midi ' + bytes(msg).hex(), self._take()))

    def run(self, blocks=4, dumps=(), program=None, extra=(), hist=None, per_block=True, maxins=200_000_000, trace=None, watch=(), watchfile=None, spmax=False):
        prog = bytearray(program if program is not None else dsp_program(self.img))
        for a in SPIN_NOPS: prog[3 * a:3 * a + 3] = b'\0\0\0'
        d = tempfile.mkdtemp(); pb = os.path.join(d, 'p.bin'); open(pb, 'wb').write(prog)
        L = [f'LOADP {pb} 0', f'MAX {maxins}']
        if hist: L.append(f'HIST {hist}')
        L += ['PC 107', 'STOP 25f3', 'RUN']
        L += self._mem(self.init_writes)
        L += ['PC 25f3', 'STOP 113', 'RUN']
        for _, w in self.events: L += self._mem(w)
        L += self._mem([(0, sp, a, v) for sp, a, v in extra])
        stub = [0x0BF080, 0x0001ED, 0x0C0000 | (STUB + 2)]     # jsr $1ED ; jmp *
        L.append('P %x %s' % (STUB, ' '.join('%06x' % x for x in stub)))
        if watchfile:
            L.append(f'WATCHFILE {watchfile}')
            L += [f'WATCH {sp.upper()} {a:x} {n}' for sp, a, n in watch]
        if spmax: L.append('SPMAX')
        if trace: L.append(f'TRACE {trace}')      # X/Y access bits of the audio blocks only (memtrace dsptool)
        for _ in range(blocks):
            L += [f'PC {STUB:x}', f'STOP {STUB + 2:x}', 'RUN']
            if per_block: L += [f'DUMP{sp.upper()} {a:x} {n}' for sp, a, n in dumps]
        if not per_block: L += [f'DUMP{sp.upper()} {a:x} {n}' for sp, a, n in dumps]
        sc = os.path.join(d, 's.txt'); open(sc, 'w').write('\n'.join(L) + '\n')
        try:
            out = subprocess.run([TOOL, 'run', sc], capture_output=True, text=True).stdout
        finally:
            shutil.rmtree(d, ignore_errors=True)                   # the directory used to stay behind (see dspemu.run)
        res, rans = [], []
        for l in out.splitlines():
            if l.startswith('RAN') or l.startswith('SPMAX'): rans.append(l)
            elif l[:1] in 'XYP' and ':' in l:
                k, v = l.split(':', 1); sp, a = k.split()
                res.append((sp.lower(), int(a, 16), [int(x, 16) for x in v.split()]))
        return res, rans

    @staticmethod
    def _mem(writes):
        return ['%s %x %06x' % (sp.upper(), a, v & 0xFFFFFF) for _, sp, a, v in writes]
