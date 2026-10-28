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


SHORTBR = False                    # SC47.3 (use_shortbr)


def use_shortbr():
    """SC47.3 (room on core 0 for the polyphony of FM / two oscillators / VA-drum, the user, 2026-10-26: «add polyphony to the remaing voices»):
    a two-word absolute jump emitted by a callable (jcc xxxx 0AF0Ac, jmp xxxx 0AF080, jsr xxxx 0BF080: the J / jsr lambdas with a label) whose
    target lies within -256..+255 words of it becomes the one-word PC-relative form (bcc / bra / bsr xxx: 0000 0101 CCCC 01aa aa0a aaaa, 0000 0101
    0000 11.., 0000 0101 0000 10..; the 9-bit displacement from the branch itself, the same condition codes; checked with dsptool's disassembler).
    Decided on the layout with every jump long; shrinking only brings code closer, so a jump chosen short stays in range (asserted).  Only in the
    blocks based at or after the end of the stock program, like use_shortx; plain word lists (data, tables, the jumps written as lists) are left
    alone.  Labels follow: every block after a shorter one moves down."""
    global SHORTBR
    SHORTBR = True


SHORTMSB = False                   # SC48.1 (use_shortmsb)
MSB_DDDDD = {0x04: 0x04, 0x05: 0x05, 0x06: 0x06, 0x07: 0x07, 0x16: 0x0E, 0x17: 0x0F}   # x0 x1 y0 y1 a b: the long form's register -> the short form's


def use_shortmsb():
    """SC48.1 (room on core 0 for the cue click, the user, 2026-10-27: «Add metronome on Cue listen only»): a two-word `move #>V,D` assembled from
    a text line (44F400..47F400 / 56F400 / 57F400 + V) with D = x0 / x1 / y0 / y1 / a / b and V & $FFFF = 0 becomes the one-word `move #$hh,D`
    (001d dddd iiii iiii 0000 0000: the 8 bits in the MSBs of D, the rest 0, a / b sign-extended: the same operand bit for bit; vcf21_dsp.use_shortimm
    did it for its own lines only).  Like use_shortx: only lines marked by mark(), only in the blocks based at or after the end of the stock program
    (not core 1); labels follow."""
    global SHORTMSB
    SHORTMSB = True


def msb_of(w0, w1):
    """the one-word form of a two-word move #>V,D, or None"""
    if w0 & 0xC0FFFF != 0x40F400 or w1 & 0xFFFF: return None
    d = MSB_DDDDD.get((w0 >> 16) & 0x3F)
    return None if d is None else 0x200000 | d << 16 | (w1 >> 16) << 8


SHORTBS = False                    # (use_shortbs)


def use_shortbs():
    """(vcf21_dsp.use_blep) with use_shortbr, a jscc xxxx (0BF0A0 | cc) near enough becomes the one-word bscc xxx (0000 0101 CCCC 00aa aa0a aaaa,
    checked with dsptool's disassembler: bses)."""
    global SHORTBS
    SHORTBS = True


def br_short(w0, at, t):
    """the one-word relative form of the absolute jump (w0, t) at `at`, or None"""
    d = t - at
    if not -256 <= d <= 255: return None
    disp = ((d >> 5) & 0xF) << 6 | (d & 0x1F)
    if w0 == 0x0AF080: return 0x050C00 | disp
    if w0 == 0x0BF080: return 0x050800 | disp
    if w0 & 0xFFFFF0 == 0x0AF0A0: return 0x050400 | (w0 & 0xF) << 12 | disp
    if SHORTBS and w0 & 0xFFFFF0 == 0x0BF0A0: return 0x050000 | (w0 & 0xF) << 12 | disp
    return None


class Marked(list):
    """words assembled from text, with .lx = the offsets of the two-word moves x:(Rn+xxxx) among them, .li = those of the moves #>V,D"""
    lx = ()
    li = ()


import re as _re
_LX = _re.compile(r"^\s*move\s+(?:x:\(r[0-7]\+[^)]*\),\w+|\w+,x:\(r[0-7]\+[^)]*\))\s*$")
_LI = _re.compile(r"^\s*move\s+#>[^,\s]+,(?:x0|x1|y0|y1|a|b)\s*$")


def mark(pairs):
    """[(text, words)] -> one Marked list of all the words"""
    out, lx, li = Marked(), [], []
    for t, ws in pairs:
        if len(ws) == 2 and _LX.match(t): lx.append(len(out))
        if len(ws) == 2 and _LI.match(t): li.append(len(out))
        out += ws
    out.lx, out.li = tuple(lx), tuple(li)
    return out


def short_of(w0, w1):
    """the one-word form of a two-word move x:(Rn+d), or None"""
    if w0 & 0xFFF880 != 0x0A7080: return None
    dd, wr, rn = w0 & 0x3F, (w0 >> 6) & 1, (w0 >> 8) & 7
    if dd not in SHORTX_DDDD or not 0 <= w1 <= 63: return None
    return 0x020080 | (w1 >> 6) << 16 | (w1 >> 1 & 0x1F) << 11 | rn << 8 | (w1 & 1) << 6 | wr << 4 | dd


def shorten(ws, msb=False, sx=True):
    if not isinstance(ws, Marked) or not (sx and ws.lx or msb and ws.li): return ws
    out, i, lx, li = [], 0, set(ws.lx) if sx else set(), set(ws.li) if msb else set()
    while i < len(ws):
        if i in lx or i in li:
            s_ = short_of(ws[i], ws[i + 1]) if i in lx else msb_of(ws[i], ws[i + 1])
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
        sx = SHORTX and (self.base >= SHORTX_MIN or getattr(self, "force_sx", False))   # (force_sx: granular_dsp.use_stereo, core 1)
        msb = SHORTMSB and self.base >= SHORTX_MIN                               # (use_shortmsb) core 0's appended code only
        sh = lambda ws: shorten(ws, msb, sx) if sx or msb else ws
        labels, addr = {}, self.base
        sizes = []
        for it in self.items:
            if it[0] == 'L': labels[it[1]] = addr
            else:
                args = [0 if isinstance(x, str) and x not in KEEP else x for x in it[2]]
                n = len(it[1](*args) if callable(it[1]) else sh(it[1]))
                sizes.append(n); addr += n
        short = set()
        if SHORTBR and self.base >= SHORTX_MIN:                                  # (use_shortbr) the jumps near enough, on the long layout
            addr, k = self.base, 0
            for it in self.items:
                if it[0] == 'L': continue
                if callable(it[1]):
                    ws = it[1](*[labels[x] if isinstance(x, str) and x in labels else x for x in it[2]])
                    if len(ws) == 2 and br_short(ws[0], addr, ws[1]) is not None: short.add(k)
                addr += sizes[k]; k += 1
            labels, addr, k = {}, self.base, 0
            for it in self.items:
                if it[0] == 'L': labels[it[1]] = addr
                else: addr += 1 if k in short else sizes[k]; k += 1
        out, addr, k = [], self.base, 0
        for it in self.items:
            if it[0] == 'L': continue
            fn, args = it[1], [labels[x] if isinstance(x, str) and x in labels else x for x in it[2]]
            ws = fn(*args) if callable(fn) else sh(fn)
            if k in short:
                s_ = br_short(ws[0], addr, ws[1]); assert s_ is not None, (hex(addr), [hex(w) for w in ws]); ws = [s_]
            out += ws; addr += len(ws); k += 1
        return out, labels


def to_bytes(words):
    return b''.join(x.to_bytes(3, 'big') for x in words)
