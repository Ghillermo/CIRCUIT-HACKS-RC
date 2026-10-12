"""SC37.5 DSP core 1: the Glitch's simulated overload (granular_dsp.use_overload) against the code of SC37.4, on the dsp56kEmu interpreter.

    python tools/emu_sc37_5_core1.py
The driver of emu_gran_core1.py (a small ring prefilled with known frames, the block counter bumped every pass); the head is read from the Glitch
state after 1..N blocks (each run from the start: the interpreter is deterministic).
  * the core-1 program still fits ($800 words);
  * K4 0 / 40 / 63: the output and the state are word for word those of SC37.4 (the chaos below the middle is unchanged);
  * K4 94, K1 127 (below the brake): the head moves 32 frames per block, or 0 (a late block played again) / 64 (caught up) in turn, starting with a repeat; it is
    never ahead of its path nor more than 32 frames behind; late blocks about (K4 - 64) / 128 of the blocks;
  * K4 90, K1 127: no brake yet (the speed stays 1 between late blocks);
  * K4 127, K1 127: the brake, 24 / 56 of the speed between late blocks (lower and slower);
  * K4 127, K1 0 (backwards): not braked;
  * K4 127, K2 0 (short segments): no chaos (direction and mute unchanged).
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
DRV, STOP = 0x3800, 0x3FF0


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    GD.OVERLOAD = False
    wo, lo = GD.core1_code(P5.C1_STOCK_WORDS, rl=RL, rn=RN)
    GD.use_overload()
    wn, ln = GD.core1_code(P5.C1_STOCK_WORDS, rl=RL, rn=RN)
    real, _ = GD.core1_code(P5.C1_STOCK_WORDS)
    check(P5.C1_STOCK_WORDS + len(real) <= 0x800, f"the core-1 program fits: {P5.C1_STOCK_WORDS + len(real)} of 2048 words")

    def program(w1, C1, nblocks):
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        emit("move x:>$%x,a" % GD.TASK, "tst a"); code += [0x0AF0A2, C1]
        emit("move #>$%x,r0" % GD.MIN, "move x:>$3f82,a")
        code += G.T("do #32,$%x" % 0); dpos = len(code) - 1
        emit("move #>1,x0", "add x0,a", "move a1,x1", "move x1,b", "asl #8,b,b", "move b1,x:(r0)+", "neg b", "move b1,x:(r0)+")
        code[dpos] = DRV + len(code) - 1
        emit("move a1,x:>$3f82")
        emit("move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT)
        emit("move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P

    P_ = lambda f: ((f * 37) & 0x7FFF) << 8
    Q_ = lambda f: ((f * 91 + 5) & 0x7FFF) << 8
    pre = [('y', RL, [P_(f) for f in range(4096)]), ('y', RL + RN, [Q_(f) for f in range(4096)]),
           ('x', GD.MAGW, [GD.C1MAGIC]), ('x', GD.WR, [4096]), ('x', GD.RNG, [0x1234])]

    def glitch(code, nb, k1, k2, k3, k4):
        w1, l1 = code
        res, ran = run(program(w1, l1["c1loop"], nb), l1["c1loop"], mem=pre + [('x', GD.GIN, [GD.GMAGIC, k1, k2, k3, k4]), ('x', GD.GOUT, [0x5A5A5A] * 128)],
                       regs_code=[], pc=l1["c1loop"], stop=STOP, maxins=20_000_000, dumps=[('x', GD.GOUT, 128), ('x', GD.GS, 16), ('x', GD.RNG, 1)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res[('x', GD.GOUT)], res[('x', GD.GS)], res[('x', GD.RNG)][0]

    OLD, NEW = (wo, lo), (wn, ln)
    # ---- below the middle: SC37.4 word for word (chaos with short segments, so it acts)
    for k4 in (0, 40, 63):
        a, b = glitch(NEW, 40, 127, 0, 1, k4), glitch(OLD, 40, 127, 0, 1, k4)
        check(a == b, f"K4 {k4}: output, state and random numbers as SC37.4 after 40 blocks (head {a[1][GD.S_HH] - RL}, dir {a[1][GD.S_DIR]}, mute {a[1][GD.S_MUTE]})")
        gc.collect()

    def heads(k1, k4, n, k2=127):
        hs = []
        for nb in range(3, n + 1):
            _, gs, _ = glitch(NEW, nb, k1, k2, 1, k4)
            hs.append((gs[GD.S_HH] - RL) + gs[GD.S_HL] / (1 << 24))
        return hs
    # ---- K4 94: late blocks, speed 1 (with K1 127 the brake starts at K4 96)
    N = 40
    hs = heads(127, 94, N)
    d = [round(hs[i + 1] - hs[i], 6) for i in range(len(hs) - 1)]
    ev = [x for x in d if x != 32]
    off, offs = 0, []
    for x in d: off += x - 32; offs.append(off)
    check(set(d) <= {0, 32, 64} and ev and ev[0] == 0 and all(ev[i] != ev[i + 1] for i in range(len(ev) - 1)),
          f"K4 94: per block 32 frames, or a late block (0 = played again) then caught up (64), in turn: {d}")
    check(all(o in (0, -32) for o in offs), f"the head never ahead of its path nor more than 32 frames behind it ({sorted(set(offs))})")
    frac = len(ev) / len(d)
    check(0.08 <= frac <= 0.45, f"late blocks {len(ev)} of {len(d)} ({frac:.2f}; p = 30 / 128 = 0.23)")
    gc.collect()
    # ---- K4 90: no brake yet
    hs = heads(127, 90, 24)
    d = [round(hs[i + 1] - hs[i], 6) for i in range(len(hs) - 1)]
    check(set(d) <= {0, 32, 64} and 32 in d, f"K4 90: no brake (32 frames per block between late blocks): {d}")
    gc.collect()
    # ---- K4 127: the brake
    hs = heads(127, 127, 30)
    d = [hs[i + 1] - hs[i] for i in range(len(hs) - 1)]
    sp = 32 * 24 / 56
    norm = [x for x in d if abs(x - sp) < 0.01]
    late = [x for x in d if abs(x - sp) >= 0.01]
    check(len(norm) >= len(d) // 3 and all(abs(abs(x - sp) - 32) < 0.01 for x in late),
          f"K4 127, K1 127: braked to 24 / 56 = {sp:.2f} frames per block between late blocks ({[round(x, 2) for x in d]})")
    gc.collect()
    hs = heads(0, 127, 12)
    d = [hs[i + 1] - hs[i] for i in range(len(hs) - 1)]
    check(all(abs(x + 32) < 0.01 or abs(abs(x + 32) - 32) < 0.01 for x in d), f"K4 127, K1 0 (backwards): not braked ({[round(x, 2) for x in d]})")
    gc.collect()
    # ---- no chaos above the middle
    out, gs, _ = glitch(NEW, 60, 127, 0, 1, 127)
    check(gs[GD.S_DIR] == 1 and gs[GD.S_MUTE] == 0, f"K4 127, K2 0 (short segments, 60 blocks): no chaos (direction {gs[GD.S_DIR]}, mute {gs[GD.S_MUTE]})")
    print("SC37.5 CORE1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
