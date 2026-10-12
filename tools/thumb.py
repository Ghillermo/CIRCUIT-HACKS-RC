"""Minimal Thumb/Thumb-2 encoder for the handful of instructions our patches need.

Every encoding is cross-checked by disassembling with Capstone in the patch
builder, so a wrong encoding fails the build instead of reaching hardware.
"""

from __future__ import annotations

import struct

COND = {"eq": 0, "ne": 1, "hs": 2, "cs": 2, "lo": 3, "cc": 3, "mi": 4, "pl": 5, "vs": 6, "vc": 7,
        "hi": 8, "ls": 9, "ge": 10, "lt": 11, "gt": 12, "le": 13, "al": 14}


def h(v: int) -> bytes:
    return struct.pack("<H", v & 0xFFFF)


def _lo(*regs):
    for r in regs:
        if not 0 <= r <= 7:
            raise ValueError(f"r{r} is not a low register")


def ldr_imm(rt, rn, imm):          # LDR Rt,[Rn,#imm]  T1
    _lo(rt, rn)
    assert imm % 4 == 0 and 0 <= imm <= 124
    return h(0x6800 | (imm // 4) << 6 | rn << 3 | rt)


def str_sp(rt, imm):               # STR Rt,[SP,#imm]  T2
    _lo(rt); assert imm % 4 == 0 and 0 <= imm <= 1020
    return h(0x9000 | rt << 8 | imm // 4)


def ldr_sp(rt, imm):               # LDR Rt,[SP,#imm]  T2
    _lo(rt); assert imm % 4 == 0 and 0 <= imm <= 1020
    return h(0x9800 | rt << 8 | imm // 4)


def ldrb_imm(rt, rn, imm=0):       # LDRB Rt,[Rn,#imm] T1
    _lo(rt, rn); assert 0 <= imm <= 31
    return h(0x7800 | imm << 6 | rn << 3 | rt)


def strb_imm(rt, rn, imm=0):       # STRB Rt,[Rn,#imm] T1
    _lo(rt, rn); assert 0 <= imm <= 31
    return h(0x7000 | imm << 6 | rn << 3 | rt)


def movs_imm(rd, imm):             # MOVS Rd,#imm8 (MOV<c> inside IT)
    _lo(rd); assert 0 <= imm <= 255
    return h(0x2000 | rd << 8 | imm)


def cmp_imm(rn, imm):              # CMP Rn,#imm8
    _lo(rn); assert 0 <= imm <= 255
    return h(0x2800 | rn << 8 | imm)


def subs_imm8(rdn, imm):           # SUBS Rdn,#imm8
    _lo(rdn); assert 0 <= imm <= 255
    return h(0x3800 | rdn << 8 | imm)


def adds_imm8(rdn, imm):           # ADDS Rdn,#imm8
    _lo(rdn); assert 0 <= imm <= 255
    return h(0x3000 | rdn << 8 | imm)


def subs_imm3(rd, rn, imm):        # SUBS Rd,Rn,#imm3
    _lo(rd, rn); assert 0 <= imm <= 7
    return h(0x1E00 | imm << 6 | rn << 3 | rd)


def adds_imm3(rd, rn, imm):        # ADDS Rd,Rn,#imm3 (ADD<c> inside IT)
    _lo(rd, rn); assert 0 <= imm <= 7
    return h(0x1C00 | imm << 6 | rn << 3 | rd)


def cmp_reg(rn, rm):               # CMP Rn,Rm  (T1 low / T2 any)
    if rn < 8 and rm < 8:
        return h(0x4280 | rm << 3 | rn)
    return h(0x4500 | (rn >> 3) << 7 | rm << 3 | (rn & 7))


def mov_reg(rd, rm):               # MOV Rd,Rm  T1 (no flags)
    return h(0x4600 | (rd >> 3) << 7 | rm << 3 | (rd & 7))


def tst_reg(rn, rm):
    _lo(rn, rm); return h(0x4200 | rm << 3 | rn)


def orrs_reg(rdn, rm):
    _lo(rdn, rm); return h(0x4300 | rm << 3 | rdn)


def lsls_reg(rdn, rm):
    _lo(rdn, rm); return h(0x4080 | rm << 3 | rdn)


def nop():
    return h(0xBF00)


def it(firstcond: str, mask_pattern: str = ""):
    """IT block. mask_pattern: '' (IT), 't'/'e' for 2nd, etc."""
    fc = COND[firstcond]
    bits = [((fc & 1) if c == "t" else (fc & 1) ^ 1) for c in mask_pattern]
    mask = 0
    for i, b in enumerate(bits):
        mask |= b << (3 - i)
    mask |= 1 << (3 - len(bits))
    return h(0xBF00 | fc << 4 | mask)


def b_cond(addr, target, cond):    # B<c> T1, +-256
    off = target - (addr + 4)
    assert off % 2 == 0 and -256 <= off <= 254, hex(off)
    return h(0xD000 | COND[cond] << 8 | (off >> 1) & 0xFF)


def b(addr, target):               # B T2, +-2KB
    off = target - (addr + 4)
    assert off % 2 == 0 and -2048 <= off <= 2046, hex(off)
    return h(0xE000 | (off >> 1) & 0x7FF)


def cbz(addr, target, rn, nz=False):
    _lo(rn)
    off = target - (addr + 4)
    assert off % 2 == 0 and 0 <= off <= 126
    i = (off >> 6) & 1
    imm5 = (off >> 1) & 0x1F
    return h(0xB100 | (0x800 if nz else 0) | i << 9 | imm5 << 3 | rn)


def bl(addr, target):              # BL T1 32-bit
    off = target - (addr + 4)
    assert off % 2 == 0 and -(1 << 24) <= off < (1 << 24)
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    imm10 = (off >> 12) & 0x3FF
    imm11 = (off >> 1) & 0x7FF
    j1 = (~i1 ^ s) & 1
    j2 = (~i2 ^ s) & 1
    return h(0xF000 | s << 10 | imm10) + h(0xD000 | j1 << 13 | j2 << 11 | imm11)


def cmp_w_imm(rn, imm):            # CMP.W Rn,#imm (imm <= 255 plain)
    assert 0 <= imm <= 255
    return h(0xF1B0 | rn) + h(0x0F00 | imm)


class Asm:
    """Sequential assembler with labels (two passes)."""

    def __init__(self, base):
        self.base = base
        self.items = []      # (kind, payload)

    def label(self, name):
        self.items.append(("label", name))

    def emit(self, fn, *args, **kw):
        self.items.append(("ins", (fn, args, kw)))

    def assemble(self, external=None):
        labels = dict(external or {})
        # pass 1: sizes (all our encodings have fixed size per function)
        size_of = {bl: 4, cmp_w_imm: 4}
        size_of.update({globals()['b_w']: 4, globals()['movw']: 4, globals()['movt']: 4})
        for _n in ('ldrb_w', 'strb_w', 'strh_w_imm', 'strh_w_reg_lsl1'):
            if _n in globals(): size_of[globals()[_n]] = 4
        addr = self.base
        for kind, p in self.items:
            if kind == "label":
                labels[p] = addr
            else:
                addr += len(p[1][0]) if p[0] is globals().get('raw') else size_of.get(p[0], 2)
        out = bytearray()
        addr = self.base
        for kind, p in self.items:
            if kind == "label":
                continue
            fn, args, kw = p
            names = args
            args = [labels[a] if isinstance(a, str) and a in labels else a for a in args]
            try:
                if fn in (b_cond, b, bl, cbz) or fn is globals().get('b_w'):
                    enc = fn(addr, *args, **kw)
                else:
                    enc = fn(*args, **kw)
            except AssertionError as ex:
                raise AssertionError(f"{ex} ({getattr(fn, '__name__', fn)} at {hex(addr)}, operands {names})") from None
            out += enc
            addr += len(enc)
        return bytes(out), labels


# ---- additions for SC03 ----------------------------------------------------
def b_w(addr, target):             # B.W T4, +-16MB
    off = target - (addr + 4)
    assert off % 2 == 0 and -(1 << 24) <= off < (1 << 24)
    s = (off >> 24) & 1
    i1 = (off >> 23) & 1
    i2 = (off >> 22) & 1
    imm10 = (off >> 12) & 0x3FF
    imm11 = (off >> 1) & 0x7FF
    j1 = (~i1 ^ s) & 1
    j2 = (~i2 ^ s) & 1
    return h(0xF000 | s << 10 | imm10) + h(0x9000 | j1 << 13 | j2 << 11 | imm11)


def lsls_imm(rd, rm, imm):
    _lo(rd, rm); assert 0 <= imm <= 31
    return h(0x0000 | imm << 6 | rm << 3 | rd)


def lsrs_imm(rd, rm, imm):
    _lo(rd, rm); assert 1 <= imm <= 31
    return h(0x0800 | imm << 6 | rm << 3 | rd)


def eors_reg(rdn, rm):
    _lo(rdn, rm); return h(0x4040 | rm << 3 | rdn)


def str_imm(rt, rn, imm):
    _lo(rt, rn); assert imm % 4 == 0 and 0 <= imm <= 124
    return h(0x6000 | (imm // 4) << 6 | rn << 3 | rt)


def ldrh_reg(rt, rn, rm):
    _lo(rt, rn, rm); return h(0x5A00 | rm << 6 | rn << 3 | rt)


def strh_imm(rt, rn, imm):
    _lo(rt, rn); assert imm % 2 == 0 and 0 <= imm <= 62
    return h(0x8000 | (imm // 2) << 6 | rn << 3 | rt)


def bx_lr():
    return h(0x4770)


def raw(data: bytes):
    return bytes(data)


SIZE4 = {b_w}


def bics_reg(rdn, rm):
    _lo(rdn, rm); return h(0x4380 | rm << 3 | rdn)


def push_lr():
    return h(0xB500)


def pop_pc():
    return h(0xBD00)


def movw(rd, imm16):                # MOVW Rd,#imm16 (T3)
    assert 0 <= imm16 <= 0xFFFF and rd < 13
    i = (imm16 >> 11) & 1; imm4 = imm16 >> 12; imm3 = (imm16 >> 8) & 7; imm8 = imm16 & 0xFF
    return h(0xF240 | i << 10 | imm4) + h(imm3 << 12 | rd << 8 | imm8)


def movt(rd, imm16):                # MOVT Rd,#imm16 (T1)
    assert 0 <= imm16 <= 0xFFFF and rd < 13
    i = (imm16 >> 11) & 1; imm4 = imm16 >> 12; imm3 = (imm16 >> 8) & 7; imm8 = imm16 & 0xFF
    return h(0xF2C0 | i << 10 | imm4) + h(imm3 << 12 | rd << 8 | imm8)


def push_list(regs, lr=False):
    m = 0
    for r in regs:
        _lo(r); m |= 1 << r
    return h(0xB400 | (0x100 if lr else 0) | m)


def pop_list(regs, pc=False):
    m = 0
    for r in regs:
        _lo(r); m |= 1 << r
    return h(0xBC00 | (0x100 if pc else 0) | m)


def ldrb_reg(rt, rn, rm):
    _lo(rt, rn, rm); return h(0x5C00 | rm << 6 | rn << 3 | rt)


def add_sp_imm(imm):                # ADD SP,SP,#imm
    assert imm % 4 == 0 and 0 <= imm <= 508
    return h(0xB000 | imm // 4)


def sub_sp_imm(imm):                # SUB SP,SP,#imm
    assert imm % 4 == 0 and 0 <= imm <= 508
    return h(0xB080 | imm // 4)


def ands_reg(rdn, rm):
    _lo(rdn, rm); return h(0x4000 | rm << 3 | rdn)


def strh_w_reg_lsl1(rt, rn, rm):    # STRH.W Rt,[Rn,Rm,LSL #1]
    return h(0xF820 | rn) + h(rt << 12 | 1 << 4 | rm)


# ---- additions for SC08 ----------------------------------------------------
def lsrs_reg(rdn, rm):
    _lo(rdn, rm); return h(0x40C0 | rm << 3 | rdn)


def muls(rdm, rn):                  # MULS Rdm,Rn,Rdm
    _lo(rdm, rn); return h(0x4340 | rn << 3 | rdm)


def blx_reg(rm):
    return h(0x4780 | rm << 3)


def adds_reg(rd, rn, rm):
    _lo(rd, rn, rm); return h(0x1800 | rm << 6 | rn << 3 | rd)


def subs_reg(rd, rn, rm):
    _lo(rd, rn, rm); return h(0x1A00 | rm << 6 | rn << 3 | rd)


def ldrh_imm(rt, rn, imm):
    _lo(rt, rn); assert imm % 2 == 0 and 0 <= imm <= 62
    return h(0x8800 | (imm // 2) << 6 | rn << 3 | rt)


def strb_reg(rt, rn, rm):
    _lo(rt, rn, rm); return h(0x5400 | rm << 6 | rn << 3 | rt)


def strh_w_imm(rt, rn, imm12):      # STRH.W Rt,[Rn,#imm12] T2
    assert 0 <= imm12 < 4096
    return h(0xF8A0 | rn) + h(rt << 12 | imm12)


def strh_reg(rt, rn, rm):
    _lo(rt, rn, rm); return h(0x5200 | rm << 6 | rn << 3 | rt)


def ldrb_w(rt, rn, imm12):          # LDRB.W Rt,[Rn,#imm12]
    assert 0 <= imm12 < 4096; return h(0xF890 | rn) + h(rt << 12 | imm12)


def strb_w(rt, rn, imm12):          # STRB.W Rt,[Rn,#imm12]
    assert 0 <= imm12 < 4096; return h(0xF880 | rn) + h(rt << 12 | imm12)
