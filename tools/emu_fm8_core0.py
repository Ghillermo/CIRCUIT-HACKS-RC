"""Core 0's side of the 8-operator FM (vcf21_dsp.use_fm8): the built image's own core 0 program on the dsp56kEmu interpreter, its vc2_fmb called
as the voice loop calls it (a = the slot's operator blocks, r0 / n0 = the output, r3 = OSC1).

    python tools/emu_fm8_core0.py NEW.bin NEW_manifest.json
  * N = 8 (the slot's + 64): the marks in all 8 operators' PH / AS / O2, the reset count (+ 48) steps, stamp (+ 16) = CNT, age (+ 32) 0; the
    shared slot = increment, stamp, reset count, 8, then per operator R, AMP, K, M1-M8, HC (12 words); the output zeros;
  * N = 0 (a slot the ARM never set) = 4: the shared N = 4, operators 1-4 with R, AMP, K, M1-M4 and HC at + 11, operators 5-8 untouched;
    operator 5's state words not marked;
  * N = 6: six operators, M1-M6;
  * the next blocks: age 1, then 2 = the output from OUTF[RDOFS] at the slot's offset (slot 1: + 128).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import masterfx_dsp as G  # noqa: E402
import granular_dsp as GD  # noqa: E402
import vcf21_dsp as VD  # noqa: E402


def main(img, man):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    VD.FMC1 = GD.FMC1 = GD.C1MS = True
    VD.FV0 = 0x4000
    VD.use_fm8(); GD.use_fm8()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P = W(dsp_program(img, 0))
    P += [0] * (0x4000 - len(P))
    fmb = int(man["report"]["sc16"]["dsp_labels"]["vc2_fmb"], 16)
    X0, OSB, OUT = 0x4080, 0x3900, 0x1000                                          # slot 1, MIDI 1's OSC1 block, a Y buffer
    off = X0 - 0x4000
    M = VD.FC1_MARK
    def ops(n):
        b = []
        for k in range(8):
            b += [0, 0, 0x100000 + k, 0x400000 - k, 0x200000 * (k == 0)] + [0x100 * (k + 1) + j for j in range(8)] + [0, 0, 0x50 + k]
        b[VD.F8_N] = n
        return b
    def shared(n):
        nn = n or 4
        out = []
        for k in range(nn):
            o = ops(n)[16 * k:16 * k + 16]
            out += o[2:5] + o[5:5 + nn] + [None] * (8 - nn) + [o[15]]
        return out
    pat = [0x010101 * (i + 1) for i in range(32)]

    def go(block, cnt, rdofs=64):
        regs = G.T("move #>$%x,a" % X0, "move #>$%x,r0" % OUT, "move #1,n0", "move #>$%x,r3" % OSB, "move #>$ffffff,m0", "move #>$ffffff,m3")
        mem = [('x', 0x3A, [32]), ('x', X0, block), ('x', GD.CNT, [cnt]), ('x', GD.RDOFS, [rdofs]), ('x', OSB + 11, [0x0ABCDE]),
               ('x', GD.OUTF + GD.FNS * GD.FBS + off, pat), ('y', OUT, [0x777777] * 32), ('x', GD.SHF + off, [0x999999] * 104)]
        res, ran = run(P, fmb, mem=mem, regs_code=regs, maxins=200_000, dumps=[('x', X0, 128), ('x', GD.SHF + off, 104), ('y', OUT, 32)])
        assert ran, ran
        return res[('x', X0)], res[('x', GD.SHF + off)], res[('y', OUT)]

    def same(sh, n):
        exp = shared(n)
        return all(e is None or e == g for e, g in zip(exp, sh[4:4 + len(exp)]))

    for n in (8, 0, 6):
        nn = n or 4
        b1, sh1, o1 = go(ops(n), 10)
        marks = all(b1[16 * k + w] == M for k in range(nn) for w in (VD.F_PH, VD.F8_AS, VD.F8_O2))
        unm = all(b1[16 * k + w] == ops(n)[16 * k + w] for k in range(nn, 8) for w in (VD.F_PH, VD.F8_AS, VD.F8_O2)) if nn < 8 else True
        check(b1[48] == 1 and marks and unm and b1[16] == 10 and b1[32] == 0,
              f"N = {n}: reset count 1, the marks on {nn} operators only, stamp 10, age 0 ({b1[48]}, {b1[16]}, {b1[32]})")
        check(sh1[:4] == [0x0ABCDE, 10, 1, nn] and same(sh1, n), f"N = {n}: the shared slot: increment, stamp, resets, {nn}, the parameters ({[hex(x) for x in sh1[:6]]})")
        check(sh1[4 + 12 * nn] == 0x999999, f"N = {n}: nothing past the {nn} operators")
        check(o1 == [0] * 32, f"N = {n}: the output zeros")
        gc.collect()
    b2, sh2, o2 = go(b1, 11)
    check(b2[48] == 1 and b2[32] == 1 and sh2[1] == 11 and o2 == [0] * 32, f"next block: reset count kept, age 1, zeros ({b2[48]}, {b2[32]})")
    b3, sh3, o3 = go(b2, 12)
    check(b3[32] == 2 and o3 == pat, f"third block: age 2, the output = OUTF[1] at the slot's offset ({[hex(x) for x in o3[:3]]})")
    print(f"{man.get('marker', '?')} FM8 CORE0 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
