"""SC44.7 DSP core 1 (granular_dsp.use_stereo) on the dsp56kEmu interpreter: the granular voices in mid / side.

    python tools/emu_gst_core1.py
The harness of emu_gran_core1.py (a driver in place of the stock loop, a small ring, the sample at Y:$10000), with the one-word x:(Rn+d) moves.
  * the program fits (and is shorter than the 2047 words of before);
  * one grain, constant sample, width 0 (Shift + K4 = 0): the mid (OUT) as the mono engine (emu_gran_core1's trapezoid), the sides (SOUT) 0;
  * width 126, pan 127 (always right): SOUT = OUT x 126 / 128 (the grain's side gain +w); pan 0 (always left): SOUT = -OUT x w;
  * density 100, pan 64: grains on both sides (each sign at least 3 of the ~13 alive), each |side| = w;
  * Shift + K3 (code 34) -64: every grain reversed (the increment negative, from g + span); 0: forward, every increment 1; +63: the pitch spray
    (increments differ).
"""
from __future__ import annotations
import gc, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dsp56  # noqa: E402
dsp56.use_shortx()
import granular_dsp as GD  # noqa: E402
GD.use_stereo()
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import probe35_dsp as P5  # noqa: E402

RL, RN = 0x40000, 0x10000
SRC = 0x10000
DRV, STOP = 0x3800, 0x3FF0
GB = GD.GB
tabs = GD.tables()


def s24(v): return v - (1 << 24) if v & 0x800000 else v


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    w1, l1 = GD.core1_code(P5.C1_STOCK_WORDS, rl=RL, rn=RN)
    n = P5.C1_STOCK_WORDS + len(w1)
    check(n <= 0x800 and n < 2047, f"core 1 program {n} words (<= 2048; 2047 before the short forms)")
    C1 = l1["c1loop"]

    def program(nblocks):
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        emit("move x:>$%x,a" % GD.TASK, "tst a"); code += [0x0AF0A2, C1]
        emit("move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT)
        emit("move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P

    def vin(t, pan=0x400000, **kw):
        osb_n = dict(P17=0, P18=1, P19=2, P20=3, P21=4, P22=5, P23=6, P24=7, P25=8, P26=9, NOTE2=20, DFL=21)
        os2_n = dict(P27=0, P28=1, P29=2, P30=3, P33=6, P34=7)
        vb_n = dict(NOTE=19, ACT=20, ENV=23, LV=26)
        base = dict(P18=-64, P20=0, P23=63, NOTE=60, NOTE2=60, ACT=2, DFL=16, S=SRC, L=20000, P30=0, ENV=0, LV=0, P25=0)
        base.update(kw)
        osb, os2, vb = [0] * 22, [0] * 8, [0] * 48
        for k, x in base.items():
            if k in osb_n: osb[osb_n[k]] = x & 0xFFFFFF
            elif k in os2_n: os2[os2_n[k]] = x & 0xFFFFFF
            elif k in vb_n: vb[vb_n[k]] = x & 0xFFFFFF
        out = [('x', GD.SHA + 48 * t, osb), ('x', GD.SHA + 0x60 + 48 * t, os2), ('x', GD.SHB + 48 * t, vb), ('x', GD.SHPAN + 2 * t, [0x3F8000, pan])]
        out.append(('x', GD.SHT + 4 * base["P25"], [base["S"], base["L"], 0, 0]))
        return out

    passes = []
    def go(nblocks, mem, dumps, maxins=20_000_000):
        res, ran = run(program(nblocks), C1, mem=list(mem), regs_code=[], pc=C1, stop=STOP, maxins=maxins, dumps=dumps)
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res

    const = [0x400000] * 20000
    # ---------------------------------------------------------------- one grain: the mid as the mono engine, the sides by width / pan
    Lg = tabs["SIZE_T"][0]; fa, fr = GD.model_window(0); La, Lr = max(1, Lg * fa >> 8), max(1, Lg * fr >> 8); Lh = Lg - La - Lr
    gain = tabs["GAIN_T"][0]; dea = gain // La
    env, e = [], 0
    for i in range(Lg):
        e += dea if i < La else 0 if i < La + Lh else -(La * dea // Lr)
        env.append(e)
    exp_mid = [((2 * 0x400000 * x) >> 24) & 0xFFFFFF for x in env[:32]]
    def one(width, pan):
        R = go(2, [('y', SRC, const[:2000]), *vin(0, pan=pan, P19=0, P29=width)], [('x', GD.OUT, 128), ('x', GD.SOUT, 128), ('x', GD.GR0, GD.GW)])
        return R[('x', GD.OUT)][64:96], R[('x', GD.SOUT)][64:96], R[('x', GD.GR0)]
    o, sd, gr = one(0, 0x7FFFFF)
    check(o == exp_mid and sd == [0] * 32, f"width 0: the mid as the mono engine, the sides 0 ({[hex(x) for x in o[:4]]}, {[hex(x) for x in sd[:4]]})")
    w = 126 << 16
    for pan, sign, name in ((0x7FFFFF, 1, "pan 127: right"), (0, -1, "pan 0: left")):
        o, sd, gr = one(126, pan)
        exp_sd = [s24(x) * sign * w / (1 << 23) for x in o]
        okv = o == exp_mid and all(abs(s24(a) - b) <= 2 for a, b in zip(sd, exp_sd)) and s24(gr[GD.G_SD]) == sign * w
        check(okv, f"width 126, {name}: side gain {s24(gr[GD.G_SD]):#x}, SOUT = OUT x {sign} x 126 / 128 ({[hex(x) for x in sd[2:5]]})")
    gc.collect()
    # ---------------------------------------------------------------- density 100, pan 64: both sides
    R = go(12, [('y', SRC, const[:3000]), *vin(0, pan=0x400000, P20=100, P19=0, P29=126)], [('x', GD.GR0, GD.MAXG * GD.GW)])
    gr = R[('x', GD.GR0)]
    alive = [k for k in range(GD.MAXG) if gr[GD.GW * k] != 0]
    sides = [s24(gr[GD.GW * k + GD.G_SD]) for k in alive]
    check(sum(1 for x in sides if x > 0) >= 3 and sum(1 for x in sides if x < 0) >= 3 and all(abs(x) == w for x in sides),
          f"density 100, pan 64: {len(alive)} grains, sides {[('+' if x > 0 else '-') for x in sides]}")
    gc.collect()
    # ---------------------------------------------------------------- Shift + K3 bipolar: reverse left, pitch spray right
    ramp = [(i << 8) for i in range(6000)]
    def grains(p34, nb=12):
        R = go(nb, [('y', SRC, ramp), *vin(0, P20=100, P19=0, P34=p34)], [('x', GD.GR0, GD.MAXG * GD.GW)])
        gr = R[('x', GD.GR0)]
        return [(s24(gr[GD.GW * k + GD.G_IH]), gr[GD.GW * k + GD.G_IL]) for k in range(GD.MAXG) if gr[GD.GW * k] != 0]
    g = grains(-64)
    check(g and all(h < 0 for h, l in g), f"code 34 = -64: every grain reversed ({g[:4]})")
    g0 = grains(0)
    check(g0 and all((h, l) == (1, 0) for h, l in g0), f"code 34 = 0: forward, every increment 1 ({g0[:4]})")
    g = grains(63)
    check(len(set(g)) > 3 and all(h >= 0 for h, l in g), f"code 34 = +63: the pitch spray, increments differ ({len(set(g))} distinct)")
    gc.collect()
    print("CORE1 STEREO RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
