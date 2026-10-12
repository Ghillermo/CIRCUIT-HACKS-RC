"""Master FX DSP tests: each effect on the dsp56kEmu interpreter vs a bit-exact DSP56300 fixed-point model.

    python tools/emu_masterfx_dsp.py STOCK.bin
"""
from __future__ import annotations
import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402

N = 32
BASE = 0x2ACE


def s24(v): v &= 0xFFFFFF; return v - (1 << 24) if v & 0x800000 else v
def u24(v): return v & 0xFFFFFF


class Acc:
    """56-bit accumulator as an integer scaled by 2^47 (a1 = bits 47..24)."""
    def __init__(self, v=0): self.v = v
    @staticmethod
    def of(x24): return Acc(s24(x24) << 24)
    def mac(self, x, y, neg=False): self.v += (-1 if neg else 1) * ((s24(x) * s24(y)) << 1); return self
    def mpy(self, x, y): self.v = (s24(x) * s24(y)) << 1; return self
    def add24(self, x): self.v += s24(x) << 24; return self
    def sub24(self, x): self.v -= s24(x) << 24; return self
    def sub(self, o): self.v -= o.v; return self
    def asr(self): self.v >>= 1; return self
    def asl(self): self.v <<= 1; return self
    def lim(self):                      # move a,X (limited a1)
        hi = self.v >> 24
        return u24(max(-0x800000, min(0x7FFFFF, hi)))
    def a1(self): return u24(self.v >> 24)


def m_gate(buf, on, tgt, cur, k):
    out = list(buf)
    if not on: return out, 0x7FFFFF
    g = cur
    for i in range(N):
        b = Acc.of(g); a = Acc.of(tgt).sub24(g); x0 = a.lim(); b.mac(x0, k); g = b.lim()
        for c in (0, 1): out[2 * i + c] = Acc().mpy(g, out[2 * i + c]).lim()
    return out, g


def m_dig(buf, cnt, hl, hr, mask, n):
    out = list(buf); b = cnt
    for i in range(N):
        b -= 1
        if b <= 0:
            hl = u24((s24(out[2 * i]) & mask)); hr = u24((s24(out[2 * i + 1]) & mask)); b = n
        out[2 * i], out[2 * i + 1] = hl, hr
    return out, b, hl, hr


def m_afl(buf, f, q, st, hp):
    out = list(buf); st = list(st)
    for i in range(N):
        for c in (0, 1):
            low, band = st[2 * c], st[2 * c + 1]
            a = Acc.of(low).mac(f, band); low = a.lim()
            b = Acc.of(out[2 * i + c]).asr(); b.sub(a); b.mac(band, q, neg=True); high = b.lim()
            nb = Acc.of(band).mac(high, f); band = nb.lim()
            st[2 * c], st[2 * c + 1] = low, band
            o = (Acc.of(high) if hp else a).asl().lim()
            out[2 * i + c] = o
    return out, st


def m_pha(buf, A, fb, mix, last, st):
    out = list(buf); last = list(last); st = list(st)
    for i in range(N):
        for c in (0, 1):
            x = out[2 * i + c]
            a = Acc.of(x).mac(fb, last[c])
            for s in range(4):
                k = c * 8 + s * 2
                x1, y1 = st[k], st[k + 1]
                st[k] = a.lim()
                a.sub24(y1); y0 = a.lim()
                a = Acc.of(x1).mac(A, y0)
                st[k + 1] = a.lim()
            last[c] = a.lim()
            b = Acc.of(x); a.sub(b); x0 = a.lim(); b.mac(mix, x0)
            out[2 * i + c] = b.lim()
    return out, last, st


def m_vin(buf, noise, T, cr, hiss, lpk, hpk, st):
    out = list(buf); st = list(st)
    for i in range(N):
        n0, n1 = noise[4 * i], noise[4 * i + 1]
        a = Acc.of(n0)
        if abs(Acc.of(n0).v) < (s24(T) << 24): a = Acc(0)
        x0 = a.lim(); b = Acc().mpy(cr, x0); b.mac(hiss, n1); y1 = b.lim()
        for c in (0, 1):
            lp, hp = st[c], st[2 + c]
            a = Acc.of(out[2 * i + c]).add24(y1)
            b = Acc.of(lp); a.sub(b); x0 = a.lim(); b.mac(lpk, x0); lp = b.lim()
            a = Acc.of(hp); b.sub(a); x0 = b.lim(); a.mac(hpk, x0); hp = a.lim()
            b = Acc.of(lp); b.sub(a); out[2 * i + c] = b.lim()
            st[c], st[2 + c] = lp, hp
    return out, st


def main(stock):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    sp = dsp_program(stock)
    P = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    words, lab = G.code(BASE)
    P = P[:BASE] + [0] * (BASE - len(P)) + words
    rnd = random.Random(3)
    sig = lambda amp=0x300000: [u24(rnd.randrange(-amp, amp)) for _ in range(2 * N)]
    common = [('x', 0x3A, [N])]
    def fx(mem, dumps):
        res, ran = run(P, lab["fx_hook"], mem=common + mem, dumps=dumps)
        assert 'pc=007002' in ran, ran
        return res

    # all off: buffer untouched, gater gain reset to 1, r1 = buffer
    buf = sig()
    r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [0]), ('x', G.G_CUR, [0x123456])], [('x', G.BUF, 2 * N), ('x', G.G_CUR, 1)])
    check(r[('x', G.BUF)] == buf and r[('x', G.G_CUR)] == [0x7FFFFF], "all off: master block untouched, gater gain = 1")

    # Gater
    for tgt, cur, k in ((0, 0x7FFFFF, 0x040000), (0x200000, 0x100000, 0x100000), (0x7FFFFF, 0, 0x020000)):
        buf = sig()
        exp, g = m_gate(buf, True, tgt, cur, k)
        r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1]), ('x', G.G_TGT, [tgt, cur, k])], [('x', G.BUF, 2 * N), ('x', G.G_CUR, 1)])
        check(r[('x', G.BUF)] == exp and r[('x', G.G_CUR)] == [g], f"Gater tgt={hex(tgt)} from {hex(cur)} k={hex(k)}: bit-exact, gain -> {hex(g)}")
    # Digitise
    for n, mask, cnt in ((4, 0xFFF000, 1), (1, 0xFFFFFF, 0), (13, 0xF00000, 7)):
        buf = sig()
        exp, b, hl, hr = m_dig(buf, cnt, 0x111111, 0x222222, mask, n)
        r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_DIG]), ('x', G.DG_N, [n, mask, cnt, 0x111111, 0x222222])],
               [('x', G.BUF, 2 * N), ('x', G.DG_N, 5)])
        check(r[('x', G.BUF)] == exp and r[('x', G.DG_N)][2:] == [b, hl, hr], f"Digitise N={n} mask={hex(mask)}: bit-exact, state carried")
    # Auto-Filter LP / HP
    for hp in (0, 1):
        f, q = 0x200000, 0x400000
        st = [0] * 4
        buf = [u24(int(0x200000 * math.sin(2 * math.pi * 5000 * i / 48000))) for i in range(N) for _ in (0, 1)]
        exp, nst = m_afl(buf, f, q, st, hp)
        r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [(1 << G.B_AF) | (hp << G.B_HP)]), ('x', G.AF_F, [f, q] + st)],
               [('x', G.BUF, 2 * N), ('x', G.AF_ST, 4)])
        check(r[('x', G.BUF)] == exp and r[('x', G.AF_ST)] == nst, f"Auto-Filter {'HP' if hp else 'LP'}: bit-exact SVF, state carried")
    # Auto-Filter frequency response (LP, f for ~600 Hz): low tone passes, high tone attenuated (many blocks)
    def af_gain(freq, hp=0, f=0x0A0000, q=0x600000, blocks=12):
        st = [0] * 4; pk = 0
        for blk in range(blocks):
            buf = [u24(int(0x200000 * math.sin(2 * math.pi * freq * (blk * N + i) / 48000))) for i in range(N) for _ in (0, 1)]
            r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [(1 << G.B_AF) | (hp << G.B_HP)]), ('x', G.AF_F, [f, q] + st)],
                   [('x', G.BUF, 2 * N), ('x', G.AF_ST, 4)])
            st = r[('x', G.AF_ST)]
            if blk >= blocks - 4: pk = max(pk, max(abs(s24(v)) for v in r[('x', G.BUF)]))
        return pk / 0x200000
    gl, gh = af_gain(150), af_gain(8000)
    check(gl > 0.7 and gh < 0.1, f"Auto-Filter LP response: 150 Hz x{gl:.2f}, 8 kHz x{gh:.3f}")
    gl, gh = af_gain(150, hp=1), af_gain(8000, hp=1)
    check(gl < 0.2 and gh > 0.7, f"Auto-Filter HP response: 150 Hz x{gl:.2f}, 8 kHz x{gh:.3f}")
    # Phaser
    for A, fb, mix in ((u24(-0x400000), 0x300000, 0x400000), (0x200000, 0, 0x7FFFFF)):
        buf = sig(); last = [u24(rnd.randrange(-0x100000, 0x100000)) for _ in range(2)]
        st = [u24(rnd.randrange(-0x100000, 0x100000)) for _ in range(16)]
        exp, nl, ns = m_pha(buf, A, fb, mix, last, st)
        r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_PH]), ('x', G.PH_A, [A, fb, mix] + last), ('x', G.PH_ST, st)],
               [('x', G.BUF, 2 * N), ('x', G.PH_LAST, 2), ('x', G.PH_ST, 16)])
        check(r[('x', G.BUF)] == exp and r[('x', G.PH_LAST)] == nl and r[('x', G.PH_ST)] == ns,
              f"Phaser A={hex(A)} fb={hex(fb)} mix={hex(mix)}: bit-exact (4 all-passes x 2 ch), state carried")
    r = fx([('x', G.FX_ON, [0]), ('x', G.PH_LAST, [5] * 2 + [9, 9, 9] + [7] * 16 + [0x654321])], [('x', G.PH_LAST, 22)])
    check(r[('x', G.PH_LAST)] == [5] * 2 + [9, 9, 9] + [7] * 16 + [0x654321], "all off: phaser states untouched (fast path)")
    r = fx([('x', G.FX_ON, [1]), ('x', G.G_TGT, [0x7FFFFF, 0x7FFFFF, 0x10000]), ('x', G.PH_LAST, [5] * 2 + [9, 9, 9] + [7] * 16 + [0x654321])],
           [('x', G.PH_LAST, 22)])
    check(r[('x', G.PH_LAST)] == [0] * 2 + [9, 9, 9] + [0] * 16 + [0x654321], "phaser off (others on): its states cleared, gap and VN_T untouched")
    # Vinyl
    noise = [u24(rnd.randrange(-0x700000, 0x700000)) for _ in range(4 * N)]
    for T, cr, hiss, lpk, hpk in ((0x600000, 0x400000, 0x080000, 0x300000, 0x010000), (0x7FFFFF, 0, 0, 0x7FFFFF, 0)):
        buf = sig(); st = [u24(rnd.randrange(-0x100000, 0x100000)) for _ in range(4)]
        exp, nst = m_vin(buf, noise, T, cr, hiss, lpk, hpk, st)
        r = fx([('x', G.BUF, buf), ('x', G.FX_ON, [1 << G.B_VN]), ('x', G.VN_T, [T, cr, hiss, lpk, hpk] + st), ('y', G.NOISE, noise)],
               [('x', G.BUF, 2 * N), ('x', G.VN_ST, 4)])
        check(r[('x', G.BUF)] == exp and r[('x', G.VN_ST)] == nst, f"Vinyl T={hex(T)} cr={hex(cr)} hiss={hex(hiss)}: bit-exact, state carried")
    # chain: all on = models applied in order
    buf = sig(0x200000); noise2 = noise
    p = dict(tgt=0x500000, cur=0x7FFFFF, k=0x080000, f=0x180000, q=0x500000, n=3, mask=0xFFC000, A=u24(-0x300000), fb=0x200000, mix=0x400000,
             T=0x680000, cr=0x300000, hiss=0x040000, lpk=0x500000, hpk=0x008000)
    e, b, hl, hr = m_dig(buf, 1, 0, 0, p['mask'], p['n'])
    e, vst = m_vin(e, noise2, p['T'], p['cr'], p['hiss'], p['lpk'], p['hpk'], [0] * 4)
    e, pl, pst = m_pha(e, p['A'], p['fb'], p['mix'], [0, 0], [0] * 16)
    e, ast = m_afl(e, p['f'], p['q'], [0] * 4, 0)
    e, g = m_gate(e, True, p['tgt'], p['cur'], p['k'])
    mem = [('x', G.BUF, buf), ('x', G.FX_ON, [0x1F]), ('x', G.G_TGT, [p['tgt'], p['cur'], p['k']]), ('x', G.AF_F, [p['f'], p['q'], 0, 0, 0, 0]),
           ('x', G.DG_N, [p['n'], p['mask'], 1, 0, 0]), ('x', G.PH_A, [p['A'], p['fb'], p['mix'], 0, 0]), ('x', G.PH_ST, [0] * 16),
           ('x', G.VN_T, [p['T'], p['cr'], p['hiss'], p['lpk'], p['hpk'], 0, 0, 0, 0]), ('y', G.NOISE, noise2)]
    res, ran = run(P, lab["fx_hook"], mem=common + mem, dumps=[('x', G.BUF, 2 * N)])
    check(res[('x', G.BUF)] == e, f"chain Digitise -> Vinyl -> Phaser -> Auto-Filter -> Gater, all on: bit-exact ({ran})")
    print("MASTERFX DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes()) else 0)
