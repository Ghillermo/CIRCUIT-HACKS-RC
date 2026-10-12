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


class Asm:
    def __init__(self, base):
        self.base, self.items = base, []

    def label(self, n): self.items.append(('L', n))
    def emit(self, fn, *a): self.items.append(('I', fn, a))

    def assemble(self):
        labels, addr = {}, self.base
        for it in self.items:
            if it[0] == 'L': labels[it[1]] = addr
            else:
                args = [0 if isinstance(x, str) and x not in KEEP else x for x in it[2]]
                addr += len(it[1](*args) if callable(it[1]) else it[1])
        out, addr = [], self.base
        for it in self.items:
            if it[0] == 'L': continue
            fn, args = it[1], [labels[x] if isinstance(x, str) and x in labels else x for x in it[2]]
            ws = fn(*args) if callable(fn) else fn
            out += ws; addr += len(ws)
        return out, labels


def to_bytes(words):
    return b''.join(x.to_bytes(3, 'big') for x in words)
