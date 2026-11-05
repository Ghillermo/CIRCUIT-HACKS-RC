"""SC51.4: the FM slots on DSP core 1 (granular_dsp.use_fmc1) on the dsp56kEmu interpreter, against core 0's FM loop.

    python tools/emu_fmc1_core1.py
A driver in place of the stock loop (P:$10E) bumps the block counter CNT every PER passes and, as core 0 would, stamps the sounding slots with
the CNT of the block before (granular_dsp.SHF + 48 s + 1).  The reference is S513D's load (granular_dsp.use_fmload): core 0's FM loop
instruction for instruction, on core 0's layout, 32 samples a block with the same increment ($123456).
  * slot 0 with the reference's operators (R, AMP, K, M, the feedback's half), its own state words garbage and a reset count that moved: after
    the blocks its phases, outputs, smoothed AMPs and y[n - 2] are the reference's bit for bit, and so are the block's last four samples;
  * slot 13 (a track's own) sounding too: its samples at its offset; a silent slot (no stamp): its samples untouched;
  * the outputs of block c in buffer c & 1;
  * too few passes for the work: the late count steps (granular_dsp.FL), what was made is still bit for bit.
"""
from __future__ import annotations
import gc, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import dsp56  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
import probe35_dsp as P5  # noqa: E402

DRV, STOP, PASS = 0x3800, 0x3FF0, 0x3F80
GB = GD.GB
INC = 0x123456


def build(fmc1):
    GD.FMLOAD = not fmc1
    GD.FMC1 = fmc1
    return GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dsp56.use_shortx()
    GD.use_stereo()
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    wN, lN = build(True)
    wR, lR = build(False)
    check(P5.C1_STOCK_WORDS + len(wN) <= 0x800, f"core 1 program {P5.C1_STOCK_WORDS + len(wN):#x} words (<= $800)")

    def program(w1, l1, nblocks, per, slots):
        C1 = l1["c1loop"]
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>%d,x0" % per, "cmp x0,a")
        code += [0x0AF0A9, C1]                                            # jlt c1loop
        emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT)
        for s in slots: emit("move a1,x:>$%x" % (GD.SHF + GD.FBS * s + 1))    # core 0's stamps: this block's CNT
        emit("move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT, "move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P, C1

    # the operators (core 0's layout: OUT, PH, R, AMP, K, M1-M4, AS, O2, HC)
    opsA = []
    for k in range(4):
        opsA += [0, 0, 0x100000 * (k + 1) + 0x31 * k, 0x500000 - 0x90000 * k, 0x200000 if k == 0 else 0, 0x080000, 0x040000 * (k == 3), 0x020000 * k, 0x010000, 0, 0, 0x060000]
    params = [w for k in range(4) for w in opsA[12 * k + 2:12 * k + 9] + [opsA[12 * k + 11]]]    # R, AMP, K, M1-M4, HC
    opsB = [0, 0, 0x300000, 0x500000, 0x200000, 0x000000, 0x000000, 0, 0, 0, 0, 0] * 4
    paramsB = [w for k in range(4) for w in opsB[12 * k + 2:12 * k + 9] + [opsB[12 * k + 11]]]

    def go_new(nb, per, slots, garbage=True, reset=1):
        P, C1 = program(wN, lN, nb, per, slots)
        mem = [('x', GD.SHF + GD.FBS * 0, [INC, 0, reset] + params), ('x', GD.SHF + GD.FBS * 13, [INC // 2, 0, 0] + paramsB)]
        if garbage: mem.append(('x', GD.FSB, [0x111111 * (1 + i % 7) for i in range(48)]))
        res, ran = run(P, C1, mem=mem, regs_code=[], pc=C1, stop=STOP, maxins=60_000_000,
                       dumps=[('x', GD.FSB, 48), ('x', GD.FSB + 13 * 48, 48), ('x', GD.OUTF, 2 * GD.FNS * GD.FBS), ('x', GB + GD.FS, 5)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        m = re.search(r"ins[=: ]+(\d+)", ran, re.I)
        return res, int(m.group(1)) if m else None

    def go_ref(nb, per):
        GD.FMLOAD, GD.FMC1 = True, False
        P, C1 = program(wR, lR, nb, per, [])
        res, ran = run(P, C1, mem=[('x', GD.LN, [1, 8, 4, 4]), ('x', GD.FLB, opsA)], regs_code=[], pc=C1, stop=STOP, maxins=60_000_000,
                       dumps=[('x', GD.FLB, 48), ('x', GD.FLB + 0xC0, 4), ('x', GD.LW, 11)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res

    NB, PER = 6, 150
    ref = go_ref(NB, PER)
    rA = ref[('x', GD.FLB)]
    new, ins = go_new(NB, PER, [0, 13])
    nA = new[('x', GD.FSB)]
    st_ref = [rA[12 * k + w] for k in range(4) for w in (0, 1, 9, 10)]                       # OUT, PH, AS, O2 (core 0's layout)
    st_new = [nA[12 * k + w] for k in range(4) for w in (0, 1, 2, 3)]                        # (core 1's)
    check(ref[('x', GD.LW)][5] == 0 and st_ref == st_new and any(st_ref),
          f"slot 0 after {NB - 1} blocks: the states = core 0's loop's, bit for bit ({[hex(x) for x in st_new[:4]]})")
    pb = [nA[12 * k + 4 + j] for k in range(4) for j in range(8)]
    check(pb == params, "its parameters copied to core 1's layout (R, AMP, K, M1-M4, HC at + 4..11)")
    out = new[('x', GD.OUTF)]
    c = NB - 1                                                                               # the last block made (the driver stops at CNT = NB)
    buf = lambda par, s: out[par * GD.FNS * GD.FBS + GD.FBS * s: par * GD.FNS * GD.FBS + GD.FBS * s + 32]
    check(buf(c & 1, 0)[28:32] == ref[('x', GD.FLB + 0xC0)], f"its block's last four samples = the reference's ({[hex(x) for x in buf(c & 1, 0)[28:32]]})")
    check(any(buf(c & 1, 13)) and any(buf((c - 1) & 1, 0)) and not any(buf(0, 5) + buf(1, 5)),
          "slot 13 sounding at its offset; the block before in the other buffer; a silent slot (5) untouched")
    st = new[('x', GB + GD.FS)]
    check(st[2] <= 1, f"enough passes: no late block ({st[2]}; the first block may count one)")
    if ins: print(f"info: {ins} instructions in all")
    gc.collect()
    late, _ = go_new(NB, 40, [0, 13], garbage=False, reset=0)
    st = late[('x', GB + GD.FS)]
    check(st[2] >= NB - 3, f"40 passes a block for two voices (16 tasks + the slots + the granular's 35): late ({st[2]})")
    print("FMC1 CORE1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
