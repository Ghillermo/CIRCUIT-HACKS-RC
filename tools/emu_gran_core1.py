"""SC36 DSP core 1 (tools/granular_dsp.py) on the dsp56kEmu interpreter: the granular voices and the Glitch.

    python tools/emu_gran_core1.py
A driver in place of the stock loop (P:$10E) bumps the block counter CNT every pass and writes a fresh MIN block (frames k, values from a counter);
the ring is small (RL = $40000, RN = $10000) and the sample lives at Y:$10000 so everything fits the 512 K words of the emulator.
  * init: the magic, nothing before the counter moves;
  * the ring: MIN lands at RL + w (L) / RL + RN + w (R), w += 32;
  * a voice off (ACT 1, or no DFLAGS bit 4, or a too short sample): its OUT is 0, no grain;
  * one grain, constant sample, pitch 0, rectangle window: the trapezoid envelope (attack La = Lg fa / 256 with de = gain / La, hold, release
    de = -(La de) / Lr), the gain of the density, the sample value, pos += 1 per sample, freed at the end;
  * pitch -12 st on a ramp: increment 1/2, the interpolated value between two words; +12 st: 2 per sample;
  * reverse probability 127: the increment is negative and the grain starts at g + span;
  * density 100: ~16 grains alive, the interval Lg / 16;
  * slicer: NOTE 36 + k plays slice k (start = k L / 16);
  * the tags OTAG / GTAG = the block that filled the buffer; the outputs go to buffer c & 1;
  * Glitch: off = no output; on, K1 127, K2 127 (continuous), K3 0: after the fade-in the output = the ring delayed by 64 frames; K1 = 92 (speed 1/2):
    the head moves half as fast; K1 = 0: backwards; K2 small: the head returns to the segment start; the stack depth stays small.
"""
from __future__ import annotations
import gc, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
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
    check(P5.C1_STOCK_WORDS + len(w1) <= 0x800, f"core 1 program {P5.C1_STOCK_WORDS + len(w1):#x} words (<= $800)")
    C1 = l1["c1loop"]

    def program(nblocks, minfill=True):
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        # the driver (core 0's part): only when core 1 is idle (TASK 0): MIN = frame counter values (L = n << 8, R = -(n << 8)), CNT + 1; stop after nblocks
        emit("move x:>$%x,a" % GD.TASK, "tst a"); code += [0x0AF0A2, C1]
        if minfill:
            emit("move #>$%x,r0" % GD.MIN, "move x:>$3f82,a")
            code += G.T("do #32,$%x" % 0)                                 # patched below
            dpos = len(code) - 1
            emit("move #>1,x0", "add x0,a", "move a1,x1", "move x1,b", "asl #8,b,b", "move b1,x:(r0)+", "neg b", "move b1,x:(r0)+")
            code[dpos] = DRV + len(code)                                   # LA = the last word (do #n,LA stores LA - 1 ... dsptool asm stores expr - 1)
            code[dpos] = DRV + len(code) - 1
            emit("move a1,x:>$3f82")
        emit("move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT)
        emit("move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P

    def vin(t, **kw):
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
        out = [('x', GD.SHA + 48 * t, osb), ('x', GD.SHA + 0x60 + 48 * t, os2), ('x', GD.SHB + 48 * t, vb)]
        if base["P25"] >= 0: out.append(('x', GD.SHT + 4 * base["P25"], [base["S"], base["L"], 0, 0]))
        else: out.append(('x', GD.SHLEN, [base["L"]]))
        return out

    def go(nblocks, mem, dumps, minfill=True, maxins=20_000_000):
        res, ran = run(program(nblocks, minfill), C1, mem=list(mem), regs_code=[], pc=C1, stop=STOP, maxins=maxins, dumps=dumps)
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res

    const = [0x400000] * 20000
    # ---------------------------------------------------------------- init / ring / voice off
    R = go(3, [('y', SRC, const[:300]), *vin(0, ACT=1), *vin(1, DFL=0)],
           [('x', GB, 0x20), ('x', GD.OUT, 128), ('y', RL, 96), ('y', RL + RN, 96), ('x', GD.VS0, 32), ('x', GD.VS0 + 0x20, 32), ('x', GD.GR0, 24)])
    g = R[('x', GB)]
    check(g[1] == GD.C1MAGIC and g[GD.WR - GB] == 64, f"init: magic, blocks 1 and 2 into the ring (w = {g[GD.WR - GB]})")
    L_, R_ = R[('y', RL)], R[('y', RL + RN)]
    check(L_[:4] == [1 << 8, 2 << 8, 3 << 8, 4 << 8] and R_[:2] == [(-(1 << 8)) & 0xFFFFFF, (-(2 << 8)) & 0xFFFFFF] and L_[63] == 64 << 8,
          "ring: MIN L / R frames at RL + w / RL + RN + w")
    check(R[('x', GD.OUT)] == [0] * 128 and R[('x', GD.VS0)][0] == 0 and R[('x', GD.VS0 + 0x20)][0] == 0, "voices off (ACT 1 / no granular flag): outputs 0, state off")
    check(g[GD.TASK - GB] == 0 and g[GD.OBP - GB] == GD.OUT and g[GD.GOBP - GB] == GD.GOUT, f"block 2 made into buffer 0 (OBP {g[GD.OBP - GB]:#x}), core 1 idle again")
    gc.collect()

    # ---------------------------------------------------------------- one grain, constant sample, rectangle window
    # P18 -64 -> Lg = 240; density 0 -> D 1, interval 240; window 0 -> fa = fr = 5 -> La = Lr = 240 x 5 / 256 = 4, Lh = 232
    Lg = tabs["SIZE_T"][0]; fa, fr = GD.model_window(0); La, Lr = max(1, Lg * fa >> 8), max(1, Lg * fr >> 8); Lh = Lg - La - Lr
    gain = tabs["GAIN_T"][0]; dea = gain // La; epk = La * dea; der = -(epk // Lr)
    env = []
    e = 0
    for i in range(Lg):
        e += dea if i < La else 0 if i < La + Lh else der
        env.append(e)
    def expect_out(sval, envs):
        return [((2 * sval * x) >> 24) & 0xFFFFFF for x in envs]
    outs = []
    for nb in (2, 3, 9):
        R = go(nb, [('y', SRC, const[:2000]), *vin(0, P19=0)], [('x', GD.OUT, 128), ('x', GD.GR0, 24), ('x', GD.VS0, 32)], minfill=False)
        c = nb - 1                                                       # the last block processed (the driver stops when CNT reaches nb)
        outs.append((c, R[('x', GD.OUT)][64 * (c & 1):64 * (c & 1) + 32], R[('x', GD.GR0)]))
    c, o, gr = outs[0]
    exp = expect_out(0x400000, env[:32])
    check(o == exp, f"first grain block: trapezoid attack de = {dea:#x} over La = {La}, then hold ({[hex(x) for x in o[:6]]} vs {[hex(x) for x in exp[:6]]})")
    check(gr[GD.G_PH] == SRC + 32 * 1 and gr[GD.G_IH] == 1 and gr[GD.G_IL] == 0, f"pos += 1 per sample (pos {gr[GD.G_PH]:#x}, inc {gr[GD.G_IH]}:{gr[GD.G_IL]:#x})")
    # the whole life: blocks 1..8 (the second grain starts at block 8: the countdown 240 - 7 x 32 < 0)
    seq = []
    for nb in range(2, 10):
        R = go(nb, [('y', SRC, const[:2000]), *vin(0, P19=0)], [('x', GD.OUT, 128)], minfill=False)
        c = nb - 1; seq += R[('x', GD.OUT)][64 * (c & 1):64 * (c & 1) + 32]
    tot = [0] * 256
    for t0 in (0, 224):
        for i, x in enumerate(env):
            if t0 + i < 256: tot[t0 + i] += x
    exp = [((2 * 0x400000 * x) >> 24) & 0xFFFFFF for x in tot]
    check(seq == exp, f"8 blocks: hold, release de = {der:#x} to {env[-1]:#x}, freed after {Lg} samples, the next grain at block 8 ({[hex(x) for x in seq[220:228]]})")
    gc.collect()
    # ---------------------------------------------------------------- pitch on a ramp (sample i = i << 8)
    ramp = [(i << 8) for i in range(4000)]
    for st, name in ((-12, "-12 st: increment 1/2"), (12, "+12 st: increment 2")):
        R = go(2, [('y', SRC, ramp), *vin(0, P17=st, P19=0, L=4000)], [('x', GD.OUT, 128), ('x', GD.GR0, 12)], minfill=False)
        o = R[('x', GD.OUT)][64:96]; gr = R[('x', GD.GR0)]
        num, den = (1, 2) if st < 0 else (2, 1)
        ok = True
        for n_ in range(32):
            pos2 = n_ * num                                                # position x den
            s0 = (pos2 // den) << 8; fr = pos2 % den
            s = s0 + (128 if fr else 0)
            if o[n_] != ((2 * s * env[n_]) >> 24) & 0xFFFFFF: ok = False
        inc = (gr[GD.G_IH], gr[GD.G_IL])
        check(ok and inc == ((0, 0x800000) if st < 0 else (2, 0)), f"{name}: interpolated ramp exact, inc {inc[0]}:{inc[1]:#x}")
    gc.collect()
    # ---------------------------------------------------------------- reverse
    R = go(2, [('y', SRC, ramp), *vin(0, P34=127, P19=0, L=4000)], [('x', GD.OUT, 128), ('x', GD.GR0, 12)], minfill=False)
    o = R[('x', GD.OUT)][64:96]; gr = R[('x', GD.GR0)]
    exp = [((2 * ((240 - n_) << 8) * env[n_]) >> 24) & 0xFFFFFF for n_ in range(32)]
    check(gr[GD.G_IH] == 0xFFFFFF and o == exp and gr[GD.G_PH] == SRC + 240 - 32, f"reverse probability 127: from g + span = {SRC + 240:#x} down, inc -1")
    # ---------------------------------------------------------------- density 100 -> 16 grains
    R = go(12, [('y', SRC, const[:3000]), *vin(0, P20=100, P19=0)], [('x', GD.GR0, GD.MAXG * GD.GW), ('x', GD.VS0, 32)], minfill=False)
    alive = sum(1 for k in range(GD.MAXG) if R[('x', GD.GR0)][GD.GW * k] != 0)
    vs = R[('x', GD.VS0)]
    cd, life = 0, []
    for blk in range(1, 12):
        cd -= 32; n_ = 4
        while cd <= 0 and n_:
            if sum(1 for x in life if x > 0) < GD.MAXG: life.append(240)
            cd += 15; n_ -= 1
        if cd < 0: cd = 0
        life = [x - 32 for x in life]
    malive = sum(1 for x in life if x > 0)
    check(vs[GD.V_D] == 16 and vs[GD.V_I] == 15 and alive == malive, f"density 100: D {vs[GD.V_D]}, interval {vs[GD.V_I]}, {alive} grains alive (model {malive})")
    # ---------------------------------------------------------------- slicer
    R = go(2, [('y', SRC, const[:20000]), *vin(0, P26=1, NOTE=39)], [('x', GD.GR0, 12), ('x', GD.VS0, 32)], minfill=False)
    vs = R[('x', GD.VS0)]; gr = R[('x', GD.GR0)]
    check(vs[GD.V_Z] == 20000 >> 4 and vs[GD.V_ZS] == 3 * (20000 >> 4) and gr[GD.G_PH] == SRC + 3 * 1250 + 32, f"slicer: NOTE 39 -> slice 3 (zone {vs[GD.V_ZS]}..+{vs[GD.V_Z]}), grain at {gr[GD.G_PH] - 32 - SRC}")
    gc.collect()

    # ---------------------------------------------------------------- Glitch: a prefilled ring, w = 2048, delay K3 = 1 -> 1088 frames
    P_ = lambda f: ((f * 37) & 0x7FFF) << 8
    Q_ = lambda f: ((f * 91 + 5) & 0x7FFF) << 8
    pre = [('y', RL, [P_(f) for f in range(2048)]), ('y', RL + RN, [Q_(f) for f in range(2048)]),
           ('x', GD.MAGW, [GD.C1MAGIC]), ('x', GD.WR, [2048]), ('x', GD.RNG, [0x1234])]
    def glitch(nb, k1, k2, k3=1, k4=0, on=GD.GMAGIC):
        R = go(nb, pre + [('x', GD.GIN, [on, k1, k2, k3, k4]), ('x', GD.GOUT, [0x5A5A5A] * 128)], [('x', GD.GOUT, 128), ('x', GD.GS, 16)])
        c = nb - 1
        o = R[('x', GD.GOUT)][64 * (c & 1):64 * (c & 1) + 64]
        return o[0::2], o[1::2], R[('x', GD.GS)], o, c
    full = (0x7FFFFF // 64) * 64
    sc = lambda v: ((2 * v * full) >> 24) & 0xFFFFFF
    head0 = 2080 - 1088
    Lo, Ro, gs, tg, c = glitch(4, 127, 127)
    check(Lo == [sc(P_(head0 + 64 + n_)) for n_ in range(32)] and Ro == [sc(Q_(head0 + 64 + n_)) for n_ in range(32)] ,
          "Glitch K1 127, K2 127, K3 1: after the fade-in the ring delayed by 1088 frames, L and R")
    Lo, Ro, gs, tg, c = glitch(2, 127, 127)
    check(Lo == [((2 * P_(head0 + n_) * ((n_ + 1) * (0x7FFFFF // 64))) >> 24) & 0xFFFFFF for n_ in range(32)], "Glitch: the fade-in from 0 over 64 frames")
    Lo, Ro, gs, tg, c = glitch(4, 92, 127)
    check(Lo == [sc(P_(head0 + (64 + n_) // 2)) for n_ in range(32)], f"Glitch K1 92: half speed (head {gs[GD.S_HH] - RL})")
    Lo, Ro, gs, tg, c = glitch(4, 0, 127)
    check(Lo == [sc(P_(head0 - 64 - n_)) for n_ in range(32)], f"Glitch K1 0: backwards (head {gs[GD.S_HH] - RL})")
    Lo, Ro, gs, tg, c = glitch(17, 127, 0)
    body = tabs["SIZE_T"][0] * 2 - 128; seg = 64 + body + 64
    exp = []
    for n_ in range(32):
        k = 15 * 32 + n_
        if k < seg: exp.append(None)
        else:
            j = k - seg; exp.append(((2 * P_(head0 + j) * ((j + 1) * (0x7FFFFF // 64))) >> 24) & 0xFFFFFF)
    check(all(x is None or x == y for x, y in zip(exp, Lo)) and any(x is not None for x in exp), f"Glitch K2 0: after {seg} frames the head returns to the segment start, with a fade-in")
    Lo, Ro, gs, tg, c = glitch(3, 127, 127, on=1)
    check(gs[GD.S_ON] == 0 and tg == [0x5A5A5A] * 64, "Glitch without the magic: no output (the buffer untouched)")
    # ---------------------------------------------------------------- the longest pass (core 0 waits for core 1's stock loop: every task must stay short)
    import re
    def onepass(mem):
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1)); P[0x10E] = 0x00000C           # one pass: c1loop, then back to the stub
        res, ran = run(P, C1, mem=list(mem), dumps=[('x', GD.TASK, 1)], regs_code=[], maxins=200000)
        return int(re.search(r"ins=(\d+)", ran).group(1)), res[('x', GD.TASK)][0]
    base = [('y', SRC, const[:20000]), *vin(0, P20=100, P19=0), *vin(1, P20=100, P19=0), ('x', GD.MAGW, [GD.C1MAGIC]), ('x', GD.CNT, [5]), ('x', GD.OBP, [GD.OUT]),
            ('x', GD.GOBP, [GD.GOUT]), ('x', GD.GIN, [GD.GMAGIC, 127, 0, 1, 127])]
    full = [('x', GD.GR0 + GD.GW * k, [200, 100, 1, 0x200000, 0, SRC + 100 * k, 0, 1, 0x400000, 50, 50, 0xF00000]) for k in range(2 * GD.MAXG)]
    on = [('x', GD.VS0, [1]), ('x', GD.VS0 + GD.VSS, [1])]
    worst = []
    for task, mem, name in ((0, [], "the ring"), (1, [('x', GD.VS0 + GD.V_CD, [0])], "voice 0 with 4 spawns"), (2, on + full, "a grain"), (2 + GD.MAXG, [], "voice 1"),
                            (3 + 2 * GD.MAXG, [('x', GD.GS, [1])], "the Glitch")):
        n_, t2 = onepass(base + full + [('x', GD.TASK, [task])] + mem)
        worst.append((n_, name))
    mx = max(worst)
    check(mx[0] <= 3000, f"the longest pass: {mx[0]} instructions ({mx[1]}); all: {[(n_, nm) for n_, nm in worst]}")
    gc.collect()
    print("CORE1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
