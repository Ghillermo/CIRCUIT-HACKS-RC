"""SC54 (room in the flash; the user, 2026-11-07: «Busca métodos de optimización para reducir el tamaño», then «Yes» to the dead code + the Master
FX tables): eight of Master FX's knob tables (512 B each in the flash) are steps or straight lines; build_sc17.use_gentab() leaves them out of the
image and c_gtgen (called at the head of c_fxtick) writes them once into free RAM, byte for byte the same as tables() gives (checked here at build
time by running the same integer formulas in Python):

  GDIV = 1 << (6 k >> 7)           AFN = 64 >> (7 k >> 7)           DGN = 1 + (31 k^2 + 8064) / 16129      DGM = 0xFFFFFF << (21 k / 127) & 0xFFFFFF
  LDIV = (2 + (k & 1)) << ((k >> 1) + 1) for k < 16, else 0          MIX / AFQ / PHFB = A + (D (k - k0) + R >> s), the few misses stored as they are

RAM: six tables at 0x20047300 (the stamp at 0x20047F00), the rest at 0x20048220 (both free in every build: tools/memmap.py's map).  The stamp is a
CRC of the tables' bytes: a new build with other tables writes them again."""
from __future__ import annotations
import struct
import zlib
from thumb import (adds_imm8, adds_reg, ands_reg, b, b_cond, cmp_imm, cmp_reg, h, ldr_imm, lsls_imm, lsls_reg, lsrs_imm, lsrs_reg, mov_reg, movs_imm,
                   movt, movw, muls, pop_list, push_list, raw, str_imm, subs_imm8)

GEN = ("GDIV", "AFN", "AFQ", "PHFB", "MIX", "DGN", "DGM", "LDIV")
RAM_A, RAM_A_END, RAM_B, RAM_B_END = 0x20047300, 0x20048000, 0x20048220, 0x20049000
LIN = {"MIX": (5, 0, 0, 2113665, 16), "AFQ": (7, 1, 8327840, -7778287, 64), "PHFB": (7, 0, 0, 7186461, 64)}    # s, k0, A, D, R


def udiv(rd, rn, rm): return h(0xFBB0 | rn) + h(0xF0F0 | rd << 8 | rm)
def asrs(rd, rm, n): return h(0x1000 | n << 6 | rm << 3 | rd)
def str_w(rt, rn, imm12): return h(0xF8C0 | rn) + h(rt << 12 | imm12)
def ldr_reg_lsl2_st(rt, rn, rm): return h(0xF840 | rn) + h(rt << 12 | 2 << 4 | rm)    # str.w rt, [rn, rm, lsl #2]


def model(name, k):
    if name == "GDIV": return 1 << (6 * k >> 7)
    if name == "AFN": return 64 >> (7 * k >> 7)
    if name == "DGN": return 1 + (31 * k * k + 8064) // 16129
    if name == "DGM": return (0xFFFFFF << (21 * k // 127)) & 0xFFFFFF
    if name == "LDIV": return (2 + (k & 1)) << ((k >> 1) + 1) if k < 16 else 0
    s, k0, A, D, R = LIN[name]
    return (A + ((D * (k - k0) + R) >> s)) & 0xFFFFFFFF


def layout(tabs):
    """{name: RAM address} for the tables of GEN that the build has"""
    names = [n for n in GEN if n in tabs]
    out, at = {}, RAM_A
    for n in names:
        if at + 512 > RAM_A_END - 16: break
        out[n] = at; at += 512
    stamp = at
    at = RAM_B
    for n in names:
        if n in out: continue
        out[n] = at; at += 512
        assert at <= RAM_B_END
    return out, stamp


def plan(tabs):
    """the addresses, the stamp, the misses [(name, k, value)] and the CRC"""
    ram, stamp = layout(tabs)
    miss = []
    for n in ram:
        for k in range(128):
            want = tabs[n][k] & 0xFFFFFFFF
            if model(n, k) != want:
                assert n in LIN, (n, k, model(n, k), want)
                miss.append((n, k, want))
    assert len(miss) <= 12, miss
    crc = zlib.crc32(b"".join(struct.pack("<128I", *[v & 0xFFFFFFFF for v in tabs[n]]) for n in ram)) | 1
    return ram, stamp, miss, crc


def emit(a, tabs, bc):
    """c_gtgen in build_sc17's assembler; returns the RAM addresses for tabaddr"""
    ram, stamp, miss, crc = plan(tabs)
    E = a.emit
    def imm32(rd, v): E(movw, rd, v & 0xFFFF); E(movt, rd, (v >> 16) & 0xFFFF)
    a.label("c_gtgen")
    E(push_list, [4, 5], lr=True)
    imm32(0, stamp); E(ldr_imm, 1, 0, 0); imm32(2, crc); E(cmp_reg, 1, 2); bc("gt_x", "eq")
    E(movs_imm, 4, 0)
    a.label("gt_l")
    for n, at in ram.items():
        if n == "GDIV": E(movs_imm, 0, 6); E(muls, 0, 4); E(lsrs_imm, 0, 0, 7); E(movs_imm, 1, 1); E(lsls_reg, 1, 0); E(mov_reg, 0, 1)
        elif n == "AFN": E(movs_imm, 0, 7); E(muls, 0, 4); E(lsrs_imm, 0, 0, 7); E(movs_imm, 1, 64); E(lsrs_reg, 1, 0); E(mov_reg, 0, 1)
        elif n == "DGN":
            E(mov_reg, 0, 4); E(muls, 0, 4); E(movs_imm, 1, 31); E(muls, 0, 1); E(movw, 1, 8064); E(adds_reg, 0, 0, 1)
            E(movw, 1, 16129); E(raw, udiv(0, 0, 1)); E(adds_imm8, 0, 1)
        elif n == "DGM":
            E(movs_imm, 0, 21); E(muls, 0, 4); E(movs_imm, 1, 127); E(raw, udiv(0, 0, 1)); imm32(1, 0xFFFFFF); E(mov_reg, 2, 1); E(lsls_reg, 1, 0)
            E(ands_reg, 1, 2); E(mov_reg, 0, 1)
        elif n == "LDIV":
            E(movs_imm, 0, 0); E(cmp_imm, 4, 16); E(b_cond, "gt_ld", "hs")
            E(movs_imm, 1, 1); E(ands_reg, 1, 4); E(adds_imm8, 1, 2); E(lsrs_imm, 0, 4, 1); E(adds_imm8, 0, 1); E(lsls_reg, 1, 0); E(mov_reg, 0, 1)
            a.label("gt_ld")
        else:
            s, k0, A, D, R = LIN[n]
            E(mov_reg, 0, 4)
            if k0: E(subs_imm8, 0, k0)
            imm32(1, D & 0xFFFFFFFF); E(muls, 0, 1)
            if R: E(adds_imm8, 0, R)
            if s: E(raw, asrs(0, 0, s))
            if A: imm32(1, A); E(adds_reg, 0, 0, 1)
        imm32(1, at); E(raw, ldr_reg_lsl2_st(0, 1, 4))
    E(adds_imm8, 4, 1); E(cmp_imm, 4, 128); bc("gt_l", "lo")
    for n, k, v in miss: imm32(0, v); imm32(1, ram[n]); E(raw, str_w(0, 1, 4 * k))
    imm32(0, stamp); imm32(1, crc); E(str_imm, 1, 0, 0)
    a.label("gt_x"); E(pop_list, [4, 5], pc=True)
    return ram
