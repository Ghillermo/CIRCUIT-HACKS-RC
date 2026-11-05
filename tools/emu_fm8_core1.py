"""The 8-operator FM on DSP core 1 (granular_dsp.use_fm8) on the dsp56kEmu interpreter, against SC51.4's 4-operator renderer (use_fmc1).

    python tools/emu_fm8_core1.py
The driver of emu_fmc1_core1 (bumps CNT, stamps the sounding slots).  The reference = the 4-operator renderer on the same operators.
  * N = 4: the states (OUT, PH, AS, O2) of the 4 operators and the block's samples = the reference's bit for bit;
  * N = 8, operators 5-8 = operators 1-4 again (the same R, AMP, M on each other through M5-M8, K = 0): operators 1-4 and the samples = the
    reference's, operators 5-8's states = 1-4's (the modulation sum on M5-M8 wired to operators 5-8);
  * N = 6, operators 5-6 silent: the samples = the reference's;
  * a slot with N = 4 at slot 13 sounding too; the instructions of a block with one N = 4 voice against the reference's (the same, within the dispatch).
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
SAVE = ("FBS", "SHF", "OUTF", "FRS", "FSB", "FM8", "C1MS")


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    dsp56.use_shortx()
    GD.use_stereo()
    GD.FMC1 = True
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    GD.use_c1ms()
    old = {k: getattr(GD, k) for k in SAVE}
    wR, lR = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    GD.use_fm8()
    new = {k: getattr(GD, k) for k in SAVE}
    wN, lN = GD.core1_code(P5.C1_STOCK_WORDS, rl=0x40000, rn=0x10000)
    check(P5.C1_STOCK_WORDS + len(wN) <= 0x1800, f"core 1 program {P5.C1_STOCK_WORDS + len(wN):#x} words (<= $1800 with MS = 1; was {P5.C1_STOCK_WORDS + len(wR):#x})")

    def program(w1, l1, c, nblocks, per, slots):
        C1 = l1["c1loop"]
        P = P1s + w1 + [0] * (0x4000 - len(P1s) - len(w1))
        P[0x10E:0x110] = [0x0AF080, DRV]
        code = []
        def emit(*ls): code.extend(G.T(*ls))
        emit("move x:>$%x,a" % PASS, "move #>1,x0", "add x0,a", "move a1,x:>$%x" % PASS, "move #>%d,x0" % per, "cmp x0,a")
        code += [0x0AF0A9, C1]
        emit("clr a", "move a,x:>$%x" % PASS, "move x:>$%x,a" % GD.CNT)
        for s in slots: emit("move a1,x:>$%x" % (c["SHF"] + c["FBS"] * s + 1))
        emit("move #>1,x0", "add x0,a", "move a1,x:>$%x" % GD.CNT, "move #>%d,x1" % nblocks, "cmp x1,a")
        code += [0x0AF0AA, STOP, 0x0AF080, C1]
        P[DRV:DRV + len(code)] = code; P[STOP] = 0
        return P, C1

    # operators: R, AMP, K, M (4 wide), HC
    ops4 = [(0x100000 * (k + 1) + 0x31 * k, 0x500000 - 0x90000 * k, 0x200000 if k == 0 else 0,
             [0x080000, 0x040000 * (k == 3), 0x020000 * k, 0x010000], 0x060000) for k in range(4)]

    def ref_slot():
        return [INC, 0, 1] + [w for (r, amp, kk, m, hc) in ops4 for w in [r, amp, kk] + m + [hc]]

    def new_slot(n, dup=False):
        out = [INC, 0, 1, n]
        for k in range(8):
            if k < 4:
                r, amp, kk, m, hc = ops4[k]; m8 = m + [0] * 4
            elif dup and k < n:
                r, amp, kk, m, hc = ops4[k - 4]; kk = 0; m8 = [0] * 4 + m
            else:
                r, amp, kk, m8, hc = 0, 0, 0, [0] * 8, 0
            out += [r, amp, kk] + m8 + [hc]
        return out

    def go(w1, l1, c, slot, nb=6, per=200, extra=()):
        GD.__dict__.update(c)
        P, C1 = program(w1, l1, c, nb, per, [0] + list(extra))
        mem = [('x', c["SHF"], slot)] + [('x', c["SHF"] + c["FBS"] * s, slot) for s in extra]
        res, ran = run(P, C1, mem=mem, regs_code=[], pc=C1, stop=STOP, maxins=120_000_000,
                       dumps=[('x', c["FSB"], c["FBS"]), ('x', c["OUTF"], 2 * GD.FNS * c["FBS"]), ('x', GB + GD.FS, 5)])
        assert ran and 'pc=003ff0' in ran.lower(), ran
        m = re.search(r"ins[=: ]+(\d+)", ran, re.I)
        return res, int(m.group(1)) if m else None

    NB = 6
    c = NB - 1
    def buf(res, cc, s):
        o = res[('x', cc["OUTF"])]; n = GD.FNS * cc["FBS"]
        return o[(c & 1) * n + cc["FBS"] * s:(c & 1) * n + cc["FBS"] * s + 32]
    ref, iref = go(wR, lR, old, ref_slot())
    rS = ref[('x', old["FSB"])]
    st_ref = [rS[12 * k + w] for k in range(4) for w in range(4)]
    out_ref = buf(ref, old, 0)
    check(any(out_ref) and any(st_ref), "the reference sounds")
    gc.collect()
    r4, i4 = go(wN, lN, new, new_slot(4), extra=(13,))
    nS = r4[('x', new["FSB"])]
    st4 = [nS[16 * k + w] for k in range(4) for w in range(4)]
    check(st4 == st_ref, f"N = 4: the states = the reference's, bit for bit ({[hex(x) for x in st4[:4]]})")
    check(buf(r4, new, 0) == out_ref, f"N = 4: the block's samples = the reference's ({[hex(x) for x in buf(r4, new, 0)[28:32]]})")
    check(buf(r4, new, 13) == out_ref and not any(buf(r4, new, 5)), "slot 13 the same at its offset; a silent slot untouched")
    pb = [nS[16 * k + 4 + j] for k in range(8) for j in range(12)]
    check(pb[:48] == new_slot(4)[4:52], "the parameters copied to core 1's layout (R, AMP, K, M1-M8, HC at + 4..15)")
    gc.collect()
    r8, i8 = go(wN, lN, new, new_slot(8, dup=True))
    nS = r8[('x', new["FSB"])]
    lo = [nS[16 * k + w] for k in range(4) for w in range(4)]
    hi = [nS[16 * k + w] for k in range(4, 8) for w in range(4)]
    check(lo == st_ref and buf(r8, new, 0) == out_ref, "N = 8: operators 1-4 and the samples = the reference's")
    check(hi == lo, f"N = 8: operators 5-8 (on M5-M8) = 1-4, bit for bit ({[hex(x) for x in hi[:4]]})")
    gc.collect()
    r6, i6 = go(wN, lN, new, new_slot(6))
    check(buf(r6, new, 0) == out_ref, "N = 6, operators 5-6 silent: the samples = the reference's")
    gc.collect()
    rr, ir1 = go(wR, lR, old, ref_slot(), nb=3)
    gc.collect()
    rn, in1 = go(wN, lN, new, new_slot(4), nb=3)
    gc.collect()
    rn8, in8 = go(wN, lN, new, new_slot(8), nb=3)
    if ir1 and in1:
        print(f"info: 2 blocks, one voice: reference {ir1}, N = 4 {in1}, N = 8 {in8} instructions (with the driver and the stock loop)")
    print("FM8 CORE1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
