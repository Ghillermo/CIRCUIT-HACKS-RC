"""S513D: the dummy FM load of DSP core 1 (granular_dsp.use_fmload) on the dsp56kEmu interpreter.

    python tools/emu_fmload_core1.py
A driver in place of the stock loop (P:$10E) counts the passes and bumps the block counter CNT every PER passes (a block = PER passes of the stock loop);
the granular voices are off (their tasks still run, one pass each), the Glitch is the stub of the diagnostic.
  * first pass: NZ = the OR of X:$2B00..$2BFF (0 here);
  * LN 0: no chunk, nothing late, IDLAST = the passes left after the granular's tasks;
  * LN 2, LCH 8, LS 4: 16 chunks a block, IDLAST 16 fewer, nothing late; the output words X:$2BC0.. written (operator data set: not 0); the cost of a
    chunk (instructions) = 4 samples x the FM loop of core 0;
  * LN 6, LCH 8 with too few passes: every block late (LATE counts them, the rest dropped), IDLAST 0, IDMIN 0;
  * LN changed: LATE and IDMIN start again.
"""
from __future__ import annotations
import gc, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
import probe35_dsp as P5  # noqa: E402

DRV, STOP, PASS = 0x3800, 0x3FF0, 0x3F80
GB = GD.GB


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    GD.use_stereo()
    GD.use_fmload()
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    w1, l1 = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    check(P5.C1_STOCK_WORDS + len(w1) <= 0x800, f"core 1 program {P5.C1_STOCK_WORDS + len(w1):#x} words (<= $800)")
    C1 = l1["c1loop"]

    def program(nblocks, per):
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>%d,x0" % per, "cmp x0,a")
        code += [0x0AF0A9, C1]                                            # jlt c1loop
        emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT)
        emit("move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P

    ops = []
    for k in range(4):                                                    # some operator data (R, AMP, K, M): the outputs are not 0
        ops += [0, 0, 0x100000 * (k + 1), 0x300000, 0x200000, 0x080000, 0x040000, 0, 0, 0, 0, 0]

    def go(nblocks, per, ln, lch=8, ls=4):
        res, ran = run(program(nblocks, per), C1, mem=[('x', GD.LN, [ln, lch, ls, 4])] + ([('x', GD.FLB, ops)] if ln else []), regs_code=[], pc=C1, stop=STOP,
                       maxins=40_000_000, dumps=[('x', GD.LW, 11), ('x', GD.FLB + 0xC0, 8)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        m = re.search(r"ins[=: ]+(\d+)", ran, re.I)
        w = res[('x', GD.LW)]
        return dict(late=w[5], idlast=w[6], idmin=w[7], nz=w[8], rem=w[4], out=res[('x', GD.FLB + 0xC0)], ins=int(m.group(1)) if m else None, ran=ran)

    PER, NB = 120, 6
    r0 = go(NB, PER, 0)
    tasks = 2 * (GD.MAXG + 1) + 1
    check(r0["nz"] == 0 and go(2, PER, 2)["nz"] != 0, "first pass: NZ = the OR of X:$2B00..$2BFF (0 when empty, not 0 with the operator data in it)")
    check(r0["late"] == 0 and r0["idlast"] >= PER - tasks - 2, f"LN 0: nothing late, {r0['idlast']} idle passes a block ({tasks} granular tasks, {PER} passes)")
    gc.collect()
    r2 = go(NB, PER, 2)
    check(r2["late"] == 0 and r2["idlast"] == r0["idlast"] - 16, f"LN 2 x 8 chunks: nothing late, idle passes {r0['idlast']} -> {r2['idlast']}")
    check(any(r2["out"]) and r2["rem"] == 0, f"the chunks ran: output words {[hex(x) for x in r2['out'][:4]]}, none left")
    if r0["ins"] and r2["ins"]:
        per_chunk = (r2["ins"] - r0["ins"]) / (2 * 8 * (NB - 1))
        print(f"info: {per_chunk:.0f} instructions a chunk of 4 samples = {per_chunk / 4:.0f} a sample (a voice's block = {per_chunk * 8:.0f})")
    else:
        print("info: no instruction count in", r2["ran"])
    gc.collect()
    r6 = go(NB, 60, 6)
    check(r6["late"] >= NB - 2 and r6["idlast"] == 0 and r6["idmin"] == 0, f"LN 6 x 8 in 60 passes: late every block ({r6['late']}), no idle pass")
    gc.collect()
    print("FMLOAD CORE1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
