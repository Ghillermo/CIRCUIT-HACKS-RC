"""Master FX master-insert DSP code (core 0), for SC17+.

Hook: P:$274 `move #>$2e10,r1` (2 words, right before the master compressor/gain func_0021c4) -> jsr fx_hook.
The block X:$2E10.. holds x:$3a stereo frames [L, R] after the master filter and the <<2 scaling.
Chain: Digitise -> Vinyl -> Phaser -> Auto-Filter -> Gater.  All parameters are written by the ARM.

X memory (inside the free X:$3339..$3BFF region, cleared by sc_init):
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56 as D  # noqa: E402

import sys as _sys; _sys.path.insert(0, __import__("os").path.dirname(__file__))
from dsptool_path import TOOL  # noqa: E402

BUF = 0x2E10
FX_ON = 0x3A40               # bit0 Gater, bit1 Auto-Filter, bit2 Digitise, bit3 Phaser, bit4 Vinyl, bit5 AF = HP
G_TGT, G_CUR, G_K = 0x3A41, 0x3A42, 0x3A43
AF_F, AF_Q, AF_ST = 0x3A44, 0x3A45, 0x3A46            # AF_ST: lowL, bandL, lowR, bandR
DG_N, DG_MASK, DG_CNT, DG_HL, DG_HR = 0x3A4A, 0x3A4B, 0x3A4C, 0x3A4D, 0x3A4E
PH_A, PH_FB, PH_MIX, PH_LAST = 0x3A50, 0x3A51, 0x3A52, 0x3A53      # PH_LAST: L, R
PH_ST = 0x3A58                                         # 2 ch x 4 stages x [x1, y1]
VN_T, VN_CR, VN_HISS, VN_LPK, VN_HPK, VN_ST = 0x3A68, 0x3A69, 0x3A6A, 0x3A6B, 0x3A6C, 0x3A6D   # VN_ST: lpL, lpR, hpL, hpR
NOISE, NOISE_STEP = 0xF7F, 4                           # stock noise table (regenerated every block, P:$19FD)
FX_END = 0x3A80
B_GATE, B_AF, B_DIG, B_PH, B_VN, B_HP = 0, 1, 2, 3, 4, 5

_cache = {}


def asm(lines):
    todo = [l for l in lines if l not in _cache]
    if todo:
        import dspasm_cache
        for l, ws in zip(todo, dspasm_cache.assemble(todo)): _cache[l] = ws
    if D.SHORTX: return D.mark([(l, _cache[l]) for l in lines])               # (SHORTX) the moves x:(Rn+d) marked
    return [w for l in lines for w in _cache[l]]


def T(*lines): return asm(list(lines))
def J(cc): return lambda t: [{"al": 0x0AF080, "ge": 0x0AF0A1, "ne": 0x0AF0A2, "gt": 0x0AF0A7, "lt": 0x0AF0A9, "eq": 0x0AF0AA,
                       "cs": 0x0AF0A8, "cc": 0x0AF0A0, "le": 0x0AF0AF}[cc], t]
def JCLR(bit, reg): return lambda t: [{"x0": 0x0AC400, "x1": 0x0AC500, "y0": 0x0AC600, "y1": 0x0AC700}[reg] | bit, t]
def JSET(bit, reg): return lambda t: [{"x0": 0x0AC420, "x1": 0x0AC520, "y0": 0x0AC620, "y1": 0x0AC720}[reg] | bit, t]


def code(base, ret_r1=BUF):
    a = D.Asm(base)
    L = lambda n: a.label(n)
    E = lambda *x: [a.emit(w) for w in x]
    def ld(addr, reg): a.emit(T("move x:>$%x,%s" % (addr, reg)))
    def st(reg, addr): a.emit(T("move %s,x:>$%x" % (reg, addr)))

    # ---------------- entry (P:$274 jsr)
    L("fx_hook")
    ld(FX_ON, "x0")
    a.emit(T("move x0,a")); a.emit(T("tst a")); a.emit(J("ne"), "fx_any")
    a.emit(T("move #>$7fffff,y0")); st("y0", G_CUR)                         # all off: gater gain = 1
    a.emit(J("al"), "fx_out")
    L("fx_any")
    a.emit(D.jsr, "dig"); a.emit(D.jsr, "vin"); a.emit(D.jsr, "pha"); a.emit(D.jsr, "afl"); a.emit(D.jsr, "gat")
    L("fx_out")
    a.emit(T("move #>$%x,r1" % ret_r1)); a.emit(D.RTS)

    # ---------------- Digitise: sample & hold every N frames, quantise to MASK
    L("dig")
    ld(FX_ON, "x0"); a.emit(JCLR(B_DIG, "x0"), "rts_")
    ld(DG_CNT, "b"); ld(DG_HL, "x0"); ld(DG_HR, "y0"); ld(DG_MASK, "x1"); ld(DG_N, "y1")
    a.emit(T("move #>$%x,r0" % BUF))
    a.emit(D.do_x, 0x3A, "dg_e")
    a.emit(T("sub #1,b")); a.emit(J("gt"), "dg_k")
    a.emit(T("move x:(r0)+,a")); a.emit(T("and x1,a")); a.emit(T("move a1,x0"))
    a.emit(T("move x:(r0)-,a")); a.emit(T("and x1,a")); a.emit(T("move a1,y0"))
    a.emit(T("tfr y1,b"))
    L("dg_k"); a.emit(T("move x0,x:(r0)+"))
    L("dg_e"); a.emit(T("move y0,x:(r0)+"))
    st("b", DG_CNT); st("x0", DG_HL); st("y0", DG_HR)
    L("rts_"); a.emit(D.RTS)

    # ---------------- Vinyl: + crackle (sparse noise peaks) + hiss, low-pass (tone), high-pass (wear)
    L("vin")
    ld(FX_ON, "x0"); a.emit(JCLR(B_VN, "x0"), "vn_off")
    a.emit(T("move #>$%x,r0" % BUF)); a.emit(T("move #>$%x,r5" % NOISE)); a.emit(T("move #%d,n5" % NOISE_STEP))
    a.emit(D.do_x, 0x3A, "vn_e")
    # noise n: crackle c = n if |n| >= T else 0 ; d = c*CR + n'*HISS  (n' = next stream of the table)
    a.emit(T("move y:(r5),a")); ld(VN_T, "x0")
    a.emit(T("tfr a,b")); a.emit(T("abs b")); a.emit(T("cmp x0,b")); a.emit(T("clr a iflt"))
    a.emit(T("move a,x0")); ld(VN_CR, "y0"); a.emit(T("mpy y0,x0,b"))
    a.emit(T("move (r5)+")); a.emit(T("move y:(r5)-,x0")); ld(VN_HISS, "y0"); a.emit(T("mac y0,x0,b"))
    a.emit(T("move (r5)+n5"))
    a.emit(T("move b,y1"))                                                   # y1 = noise added to both channels
    for ch in (0, 1):
        lp, hp = VN_ST + ch, VN_ST + 2 + ch
        # lp += LPK * (x + d - lp) ; hp += HPK * (lp - hp) ; out = lp - hp
        a.emit(T("move x:(r0),a")); a.emit(T("add y1,a"))
        ld(lp, "b"); a.emit(T("sub b,a")); a.emit(T("move a,x0"))
        ld(VN_LPK, "y0"); a.emit(T("mac y0,x0,b")); st("b", lp)
        ld(hp, "a"); a.emit(T("sub a,b")); a.emit(T("move b,x0"))
        ld(VN_HPK, "y0"); a.emit(T("mac y0,x0,a")); st("a", hp)
        ld(lp, "b"); a.emit(T("sub a,b"))
        if ch == 1:
            L("vn_e")
        a.emit(T("move b,x:(r0)+"))
    a.emit(D.RTS)
    L("vn_off")
    a.emit(T("clr a")); a.emit(T("move #>$%x,r4" % VN_ST))
    for _ in range(4): a.emit(T("move a,x:(r4)+"))
    a.emit(D.RTS)

    # ---------------- Phaser: 4 first-order all-passes per channel, feedback, dry/wet mix
    L("pha")
    ld(FX_ON, "x0"); a.emit(JCLR(B_PH, "x0"), "ph_off")
    ld(PH_A, "y1")
    a.emit(T("move #>$%x,r0" % BUF))
    a.emit(D.do_x, 0x3A, "ph_e")
    a.emit(T("move #>$%x,r4" % PH_ST)); a.emit(T("move #>$%x,r1" % PH_LAST))
    for ch in (0, 1):
        # u = x + FB * last
        a.emit(T("move x:(r1),x0")); ld(PH_FB, "y0")
        a.emit(T("move x:(r0),a")); a.emit(T("mac y0,x0,a"))
        for stg in range(4):
            # y = A * (u - y1) + x1 ; x1 = u ; y1 = y
            a.emit(T("move x:(r4),x0"))           # x1
            a.emit(T("move a,x:(r4)+"))           # x1 = u
            a.emit(T("move x:(r4),x1"))           # y1
            a.emit(T("sub x1,a"))                 # u - y1
            a.emit(T("move a,y0"))
            a.emit(T("tfr x0,a"))
            a.emit(T("mac y1,y0,a"))              # x1 + A*(u - y1)
            a.emit(T("move a,x:(r4)+"))           # y1 = y
        a.emit(T("move a,x:(r1)+"))               # last = all-pass output
        # out = x + MIX * (ap - x)
        a.emit(T("move x:(r0),b")); a.emit(T("sub b,a")); a.emit(T("move a,x0"))
        ld(PH_MIX, "y0"); a.emit(T("mac y0,x0,b"))
        if ch == 0:
            a.emit(T("move b,x:(r0)+"))
        else:
            L("ph_e"); a.emit(T("move b,x:(r0)+"))
    a.emit(D.RTS)
    L("ph_off")
    a.emit(T("clr a")); st("a", PH_LAST); st("a", PH_LAST + 1)
    a.emit(T("move #>$%x,r4" % PH_ST))
    a.emit(D.do_imm if hasattr(D, "do_imm") else (lambda n, t: [0x060080 | (n & 0xFF) << 8 | (n >> 8) & 0xF, t]), 16, "ph_c")
    L("ph_c"); a.emit(T("move a,x:(r4)+"))
    a.emit(D.RTS)

    # ---------------- Auto-Filter: Chamberlin state-variable filter, LP or HP, input / 2, output * 2
    L("afl")
    ld(FX_ON, "x0"); a.emit(JCLR(B_AF, "x0"), "af_off")
    ld(AF_F, "y0"); ld(AF_Q, "y1")
    a.emit(T("move #>$%x,r0" % BUF))
    a.emit(JSET(B_HP, "x0"), "af_hp")
    for mode in ("lp", "hp"):
        if mode == "hp":
            L("af_hp")
        a.emit(T("move #>$%x,r4" % AF_ST))
        a.emit(D.do_x, 0x3A, "af_e_" + mode)
        for ch in (0, 1):
            a.emit(T("move x:(r4)+,a"))           # low
            a.emit(T("move x:(r4)-,x0"))          # band
            a.emit(T("mac y0,x0,a"))              # low += f * band
            a.emit(T("move a,x:(r4)+"))
            a.emit(T("move x:(r0),b")); a.emit(T("asr b"))
            a.emit(T("sub a,b"))                  # x/2 - low
            a.emit(T("mac -x0,y1,b"))             # - q * band  = high
            a.emit(T("move b,x1"))
            a.emit(T("tfr x0,b")); a.emit(T("mac x1,y0,b"))   # band += f * high
            a.emit(T("move b,x:(r4)+"))
            if mode == "lp":
                a.emit(T("asl a"))                # out = 2 * low
                out = "a"
            else:
                a.emit(T("move x1,a")); a.emit(T("asl a"))      # out = 2 * high
                out = "a"
            if ch == 1:
                a.emit(T("move #>$%x,r4" % AF_ST))
                L("af_e_" + mode)
            a.emit(T("move %s,x:(r0)+" % out))
        a.emit(D.RTS)
    L("af_off")
    a.emit(T("clr a")); a.emit(T("move #>$%x,r4" % AF_ST))
    for _ in range(4): a.emit(T("move a,x:(r4)+"))
    a.emit(D.RTS)

    # ---------------- Gater: gain g -> G_TGT smoothly (g += K*(tgt-g) per frame), applied to L and R
    L("gat")
    ld(FX_ON, "x0"); ld(G_CUR, "y0")
    a.emit(JSET(B_GATE, "x0"), "gt_on")
    a.emit(T("move #>$7fffff,y0")); st("y0", G_CUR); a.emit(D.RTS)
    L("gt_on")
    ld(G_TGT, "x1"); ld(G_K, "y1")
    a.emit(T("move #>$%x,r0" % BUF))
    a.emit(D.do_x, 0x3A, "gt_e")
    a.emit(T("tfr y0,b")); a.emit(T("tfr x1,a")); a.emit(T("sub y0,a")); a.emit(T("move a,x0"))
    a.emit(T("mac x0,y1,b")); a.emit(T("move b,y0"))
    a.emit(T("move x:(r0),x0")); a.emit(T("mpy y0,x0,a")); a.emit(T("move a,x:(r0)+"))
    a.emit(T("move x:(r0),x0")); a.emit(T("mpy y0,x0,a"))
    L("gt_e"); a.emit(T("move a,x:(r0)+"))
    st("y0", G_CUR)
    a.emit(D.RTS)
    return a.assemble()


def disasm(words, base):
    return subprocess.run([TOOL, "dis", "/dev/stdin", "%x" % base], input=D.to_bytes(words), capture_output=True).stdout.decode()


if __name__ == "__main__":
    w, l = code(0x2ACE)
    print(disasm(w, 0x2ACE)); print(len(w), {k: hex(v) for k, v in l.items()})
