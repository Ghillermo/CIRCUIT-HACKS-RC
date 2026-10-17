"""Tiny DSP56300 encoder for the few instructions SC10+ needs (verified by disassembling)."""
XR = {'x0': 0x44, 'x1': 0x45, 'y0': 0x46, 'y1': 0x47, 'a': 0x56, 'b': 0x57}
YR = {'x0': 0x4C, 'x1': 0x4D, 'y0': 0x4E, 'y1': 0x4F, 'a': 0x5E, 'b': 0x5F, 'r5': 0x6D}
MODE = {'+': 0b011, '': 0b100, '-': 0b010}


def w(op, *ext):
    return [op] + list(ext)


def move_imm_r(n, val):            # move #>val,rN
    return [0x60F400 | n << 16, val & 0xFFFFFF]


def move_imm_x(reg, val):          # move #>val,x0/x1/y0/y1/a/b
    code = {'x0': 0x44, 'x1': 0x45, 'y0': 0x46, 'y1': 0x47, 'a': 0x56, 'b': 0x57}[reg]
    return [code << 16 | 0xF400, val & 0xFFFFFF]


def ld_abs(space, reg, addr):      # move x:>addr,reg / move y:>addr,reg
    code = (XR if space == 'x' else YR)[reg]
    return [code << 16 | 0xF000, addr]


def st_abs(space, reg, addr):      # move reg,x:>addr
    code = (XR if space == 'x' else YR)[reg]
    return [code << 16 | 0x7000, addr]


def ld_ind(space, reg, n, mode='+'):   # move x:(rN)+,reg
    code = (XR if space == 'x' else YR)[reg]
    return [code << 16 | (0xC0 | MODE[mode] << 3 | n) << 8]


def st_ind(space, reg, n, mode='+'):   # move reg,x:(rN)+
    code = (XR if space == 'x' else YR)[reg]
    return [code << 16 | (0x40 | MODE[mode] << 3 | n) << 8]


def inc_r(n):                       # move (rN)+
    return [0x205800 | n << 8]


def jsr(addr): return [0x0BF080, addr]
def jmp(addr): return [0x0AF080, addr]
def do_x(aa, last): return [0x060000 | aa << 8, last]        # do x:aa,last   (aa < $40)
def jclr_a1(bit, t): return [0x0ACC00 | bit, t]
def jset_a1(bit, t): return [0x0ACC20 | bit, t]


RTS, NOP = [0x00000C], [0x000000]
CLR_A, CLR_B = [0x200013], [0x20001B]
MPY_Y0X0_A = [0x2000D0]
ASL2_A = [0x0C1D04]
ASR_X0_A, ASR_X0_B = [0x0C1E68], [0x0C1E79]
ADD_Y0_A, ADD_Y0_B = [0x200050], [0x200058]


KEEP = {'x', 'y', 'x0', 'x1', 'y0', 'y1', 'a', 'b', 'r5', '+', '-', ''}


SHORTX = False                     # SC43.9 (use_shortx)
SHORTX_MIN = 0x2A5E                # (SHORTX) only the code appended after the stock core-0 program
SHORTX_DDDD = (4, 5, 6, 7, 8, 9, 0xC, 0xD, 0xE, 0xF)    # x0 x1 y0 y1 a0 b0 a1 b1 a b: the registers of the one-word form


def use_shortx():
    """SC43.9 (the user, 2026-10-17: «Start with the DSP compaction (short x:(rn+d) forms)»): the two-word `move x:(Rn+xxxx),D` / `move D,x:(Rn+xxxx)`
    that dsptool assembles (0000 1010 0111 0RRR 1WDD DDDD + the displacement) becomes the one-word `x:(Rn+xxx)` form the stock's own voices use
    (0000 0010 dddd dRRR 1d0W DDDD: displacement bit 0 in bit 6, bits 1-5 in bits 11-15; drums2_dsp.sx, sampler_dsp.short_x), for a displacement 0..63
    and a register of SHORTX_DDDD.  Only instructions assembled from a move text (lists marked by mark(): never a data table), only in the blocks
    based at or after the end of the stock program (the code appended to core 0; the vector-area code and core 1 keep their layout).  Labels follow:
    the program shrinks and every block after it moves down."""
    global SHORTX
    SHORTX = True


class Marked(list):
    """words assembled from text, with .lx = the offsets of the two-word moves x:(Rn+xxxx) among them"""
    lx = ()


import re as _re
_LX = _re.compile(r"^\s*move\s+(?:x:\(r[0-7]\+[^)]*\),\w+|\w+,x:\(r[0-7]\+[^)]*\))\s*$")


def mark(pairs):
    """[(text, words)] -> one Marked list of all the words"""
    out, lx = Marked(), []
    for t, ws in pairs:
        if len(ws) == 2 and _LX.match(t): lx.append(len(out))
        out += ws
    out.lx = tuple(lx)
    return out


def short_of(w0, w1):
    """the one-word form of a two-word move x:(Rn+d), or None"""
    if w0 & 0xFFF880 != 0x0A7080: return None
    dd, wr, rn = w0 & 0x3F, (w0 >> 6) & 1, (w0 >> 8) & 7
    if dd not in SHORTX_DDDD or not 0 <= w1 <= 63: return None
    return 0x020080 | (w1 >> 6) << 16 | (w1 >> 1 & 0x1F) << 11 | rn << 8 | (w1 & 1) << 6 | wr << 4 | dd


def shorten(ws):
    if not isinstance(ws, Marked) or not ws.lx: return ws
    out, i, lx = [], 0, set(ws.lx)
    while i < len(ws):
        if i in lx:
            s_ = short_of(ws[i], ws[i + 1])
            if s_ is not None:
                out.append(s_); i += 2; continue
        out.append(ws[i]); i += 1
    return out


class Asm:
    def __init__(self, base):
        self.base, self.items = base, []

    def label(self, n): self.items.append(('L', n))
    def emit(self, fn, *a): self.items.append(('I', fn, a))

    def assemble(self):
        sx = SHORTX and self.base >= SHORTX_MIN
        labels, addr = {}, self.base
        for it in self.items:
            if it[0] == 'L': labels[it[1]] = addr
            else:
                args = [0 if isinstance(x, str) and x not in KEEP else x for x in it[2]]
                addr += len(it[1](*args) if callable(it[1]) else shorten(it[1]) if sx else it[1])
        out, addr = [], self.base
        for it in self.items:
            if it[0] == 'L': continue
            fn, args = it[1], [labels[x] if isinstance(x, str) and x in labels else x for x in it[2]]
            ws = fn(*args) if callable(fn) else shorten(fn) if sx else fn
            out += ws; addr += len(ws)
        return out, labels


def to_bytes(words):
    return b''.join(x.to_bytes(3, 'big') for x in words)
