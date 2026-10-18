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
        if COMPACT:
            return _assemble_compact(self, external)
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


# ---- (option) literal pools ------------------------------------------------
# COMPACT: every `movw rd, lo` + `movt rd, hi` pair (8 B) becomes one LDR rd, [pc, #off] (2 B for r0-r7 when the pool is
# 0..1020 B ahead, else LDR.W, 4 B) from a pool of shared words placed after an instruction that never falls through
# (b, b.w, bx, pop {pc}).  Kept as a pair: inside an IT block, before a `*_fix` label (patched later in place), or with no
# usable pool in reach.  A pool that would push a short branch (b<c>, b, cbz) out of range is not placed.  Off: the
# assembler is the one above, byte for byte.
COMPACT = False
LAST = None         # (seq, addrs, pools, kept pairs, load sizes) of the last compacted block, for the checkers
STATS = dict(pairs=0, narrow=0, wide=0, kept=0, pools=0, words=0, pad=0, before=0, after=0)
# labels whose first N bytes a builder later reads or patches at fixed offsets: their pairs stay
KEEP = dict(c_m1=8, c_m2=8, c_ckledtask=16, c_shbtn2=0x3C, c_conv0=64)


def ldr_lit_n(rt, off):             # LDR Rt,[PC,#off] T1 (off from Align(PC, 4))
    _lo(rt); assert off % 4 == 0 and 0 <= off <= 1020, off
    return h(0x4800 | rt << 8 | off // 4)


def ldr_lit_w(rt, off):             # LDR.W Rt,[PC,#+-off] T2
    assert -4095 <= off <= 4095 and rt < 13, off
    return h(0xF85F | (0x80 if off >= 0 else 0)) + h(rt << 12 | abs(off))


def _size(fn, args):
    if fn is raw:
        return len(args[0])
    return 4 if fn in (bl, cmp_w_imm, b_w, movw, movt, ldrb_w, strb_w, strh_w_imm, strh_w_reg_lsl1) else 2


def _it_count(fn, args, kw):
    if fn is it:
        return 1 + len(args[1] if len(args) > 1 else kw.get("mask_pattern", ""))
    if fn is raw and len(args[0]) == 2:
        v = args[0][0] | args[0][1] << 8
        if v & 0xFF00 == 0xBF00 and v & 0xF:
            m = v & 0xF
            return 4 - ((m & -m).bit_length() - 1)
    return 0


def _barrier(fn, args, kw):
    """1 = never falls through; 2 = raw bytes that decode as such (a pool only if code, not more raw data, follows)."""
    if fn in (b, b_w, bx_lr, pop_pc):
        return 1
    if fn is pop_list and (kw.get("pc") or (len(args) > 1 and args[1])):
        return 1
    if fn is raw:
        d = args[0]
        if len(d) == 2:
            v = d[0] | d[1] << 8
            if v == 0x4770 or v & 0xFF00 == 0xBD00 or v & 0xFF87 == 0x4700 or v & 0xF800 == 0xE000:
                return 2
        elif len(d) == 4:
            h1, h2 = d[0] | d[1] << 8, d[2] | d[3] << 8
            if (h1 & 0xF800 == 0xF000 and h2 & 0xD000 == 0x9000) or (h1 == 0xE8BD and h2 & 0x8000) or (h1 == 0xF85D and h2 == 0xFB04):
                return 2
    return 0


def _assemble_compact(asm, external):
    items, n = asm.items, len(asm.items)
    seq, it_left, i, u, keep = [], 0, 0, 0, -1
    while i < n:
        kind, p = items[i]
        if kind == "label":
            if p in KEEP: keep = max(keep, u + KEEP[p])
            seq.append(("label", p)); i += 1; continue
        fn, args, kw = p
        nx = items[i + 1] if i + 1 < n else None
        u += _size(fn, args)
        if (fn is movw and u - 4 >= keep and not it_left and not kw and nx and nx[0] == "ins" and nx[1][0] is movt and not nx[1][2]
                and nx[1][1][0] == args[0] and isinstance(args[1], int) and isinstance(nx[1][1][1], int)
                and not (i + 2 < n and items[i + 2][0] == "label" and str(items[i + 2][1]).endswith("_fix"))):
            seq.append(("lit", args[0], args[1] | nx[1][1][1] << 16)); i += 2; u += 4; continue
        inside = it_left > 0
        if inside:
            it_left -= 1
        seq.append(("ins", fn, args, kw, _size(fn, args)))
        c = _it_count(fn, args, kw)
        if c:
            it_left = c
        if not inside:
            bk = _barrier(fn, args, kw)
            if bk == 2:
                j = i + 1
                while j < n and items[j][0] == "label": j += 1
                if j < n and items[j][1][0] is raw: bk = 0
            if bk:
                seq.append(("site",))
        i += 1
    base = asm.base
    lits = [k for k, e in enumerate(seq) if e[0] == "lit"]
    lsz = {k: 2 if seq[k][1] < 8 else 4 for k in lits}
    forbid, pair = set(), set()

    def sz(k):
        e = seq[k]
        return e[4] if e[0] == "ins" else (8 if k in pair else lsz[k]) if e[0] == "lit" else 0

    for _attempt in range(400):
        # (a) pools, greedily: flush at a site when the next usable site would leave an open load out of reach
        pools, owner, addrs, open_, addr = {}, {}, {}, [], base
        for k, e in enumerate(seq):
            addrs[k] = addr
            if e[0] == "site" and open_ and k not in forbid:
                vals, a2, nxt = {seq[j][2] for j, _ in open_}, addr, None
                for j in range(k + 1, len(seq)):
                    if seq[j][0] == "site" and j not in forbid:
                        nxt = a2; break
                    if seq[j][0] == "lit" and j not in pair:
                        vals.add(seq[j][2])
                    a2 += sz(j)
                flush = nxt is None or any(nxt + 2 + 4 * (len(vals) - 1) - ((aj + 4) & ~3) > (1020 if lsz[j] == 2 else 4095) for j, aj in open_)
                if flush:
                    pv = []
                    for j, _ in open_:
                        if seq[j][2] not in pv: pv.append(seq[j][2])
                        owner[j] = k
                    pools[k], open_ = pv, []
                    addr += (addr & 2) + 4 * len(pv)
                continue
            if e[0] == "lit" and k not in pair:
                open_.append((k, addr))
            addr += sz(k)
        changed = bool(open_)
        pair |= {j for j, _ in open_}
        if changed:
            continue
        # (b) the size each load needs where its pool landed (sizes only grow, so this ends)
        offs = {}
        for j in lits:
            if j in pair: continue
            s = owner[j]
            off = addrs[s] + (addrs[s] & 2) + 4 * pools[s].index(seq[j][2]) - ((addrs[j] + 4) & ~3)
            need = 2 if seq[j][1] < 8 and 0 <= off <= 1020 else 4 if -4095 <= off <= 4095 else 8
            if need == 8: pair.add(j); changed = True
            elif need > lsz[j]: lsz[j] = need; changed = True
            offs[j] = off
        if changed:
            continue
        # (c) encode; a short branch out of range forbids the sites between it and its target
        labels = dict(external or {})
        for k, e in enumerate(seq):
            if e[0] == "label": labels[e[1]] = addrs[k]
        out, fail = bytearray(), None
        for k, e in enumerate(seq):
            assert base + len(out) == addrs[k], (hex(base + len(out)), hex(addrs[k]))
            if e[0] == "label":
                continue
            if e[0] == "site":
                if k in pools:
                    if addrs[k] & 2: out += nop()
                    for v in pools[k]: out += struct.pack("<I", v)
                continue
            if e[0] == "lit":
                rd, v = e[1], e[2]
                out += (movw(rd, v & 0xFFFF) + movt(rd, v >> 16) if k in pair else
                        ldr_lit_n(rd, offs[k]) if lsz[k] == 2 else ldr_lit_w(rd, offs[k]))
                continue
            fn, args, kw = e[1], e[2], e[3]
            a = [labels[x] if isinstance(x, str) and x in labels else x for x in args]
            try:
                enc = fn(addrs[k], *a, **kw) if fn in (b_cond, b, bl, cbz, b_w) else fn(*a, **kw)
            except AssertionError as ex:
                tgt = args[0] if args and isinstance(args[0], str) else None
                if fn in (b_cond, b, cbz) and tgt and any(x[0] == "label" and x[1] == tgt for x in seq):
                    fail = (k, tgt); break
                raise AssertionError(f"{ex} ({getattr(fn, '__name__', fn)} at {hex(addrs[k])}, operands {args})") from None
            assert len(enc) == e[4], (getattr(fn, "__name__", fn), len(enc), e[4])
            out += enc
        if fail:
            k0, tgt = fail
            t = next(j for j, x in enumerate(seq) if x[0] == "label" and x[1] == tgt)
            new = {j for j in range(min(k0, t), max(k0, t)) if seq[j][0] == "site"} - forbid
            if not new:
                raise AssertionError(f"branch out of range without a pool between ({hex(addrs[k0])} -> {tgt})")
            forbid |= new
            continue
        STATS["pairs"] += len(lits); STATS["kept"] += len(pair)
        STATS["narrow"] += sum(1 for j in lits if j not in pair and lsz[j] == 2)
        STATS["wide"] += sum(1 for j in lits if j not in pair and lsz[j] == 4)
        STATS["pools"] += len(pools); STATS["words"] += sum(len(v) for v in pools.values())
        STATS["pad"] += sum(2 for s in pools if addrs[s] & 2)
        STATS["before"] += sum(8 if e[0] == "lit" else e[4] if e[0] == "ins" else 0 for e in seq); STATS["after"] += len(out)
        global LAST
        LAST = (seq, addrs, pools, pair, lsz)
        return bytes(out), labels
    raise AssertionError("literal pools: no stable layout")
