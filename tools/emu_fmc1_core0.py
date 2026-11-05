"""SC51.4: core 0's side of the FM slots on core 1 (vcf21_dsp.use_fmc1: the FM loop turned into a copy), the built image's own core 0 program on
the dsp56kEmu interpreter, its vc2_fmb called as the voice loop calls it (a = the slot's operator blocks, r0 / n0 = the output, r3 = OSC1).

    python tools/emu_fmc1_core0.py NEW.bin NEW_manifest.json
  * the first block (the state words as the ARM left them, not the mark): the reset count steps, the marks written, the stamp = CNT, age 0; the
    shared slot = the increment (OSC1 + 11), the stamp, the reset count, the four operators' R, AMP, K, M1-M4, HC; the output zeros;
  * the next block (CNT + 1, nothing written by the ARM): the reset count kept, age 1, zeros;
  * the third: age 2: the output = OUTF[RDOFS] at the slot's offset (slot 1: + 48; RDOFS 64 = the second buffer);
  * a block skipped (CNT + 2): age 0 again, zeros.
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
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P = W(dsp_program(img, 0))
    P += [0] * (0x4000 - len(P))
    fmb = int(man["report"]["sc16"]["dsp_labels"]["vc2_fmb"], 16)
    X0, OSB, OUT = 0x4030, 0x3900, 0x1000                                          # slot 1, MIDI 1's OSC1 block, a Y buffer
    off = X0 - 0x4000
    ops = []
    for k in range(4):
        ops += [0, 0, 0x100000 + k, 0x400000 - k, 0x200000 * (k == 0), 0x10 + k, 0x20 + k, 0x30 + k, 0x40 + k, 0, 0, 0x50 + k]
    params = [w for k in range(4) for w in ops[12 * k + 2:12 * k + 9] + [ops[12 * k + 11]]]
    pat = [0x010101 * (i + 1) for i in range(32)]

    def go(block, cnt, rdofs=64):
        regs = G.T("move #>$%x,a" % X0, "move #>$%x,r0" % OUT, "move #1,n0", "move #>$%x,r3" % OSB, "move #>$ffffff,m0", "move #>$ffffff,m3")
        mem = [('x', 0x3A, [32]), ('x', X0, block), ('x', GD.CNT, [cnt]), ('x', GD.RDOFS, [rdofs]), ('x', OSB + 11, [0x0ABCDE]),     # (X:$3A: the block's samples)
               ('x', GD.OUTF + GD.FNS * GD.FBS + off, pat), ('y', OUT, [0x777777] * 32)]
        res, ran = run(P, fmb, mem=mem, regs_code=regs, maxins=200_000, dumps=[('x', X0, 48), ('x', GD.SHF + off, 35), ('y', OUT, 32)])
        assert ran, ran
        return res[('x', X0)], res[('x', GD.SHF + off)], res[('y', OUT)]

    b1, sh1, o1 = go(ops, 10)
    M = VD.FC1_MARK
    marks = all(b1[12 * k + w] == M for k in range(4) for w in (VD.F_PH, VD.F_AS, VD.F_O2))
    check(b1[36] == 1 and marks and b1[12] == 10 and b1[24] == 0, f"first block: reset count 1, the marks, stamp 10, age 0 ({b1[36]}, {b1[12]}, {b1[24]})")
    check(sh1[:3] == [0x0ABCDE, 10, 1] and sh1[3:35] == params, f"the shared slot: increment, stamp, reset count, the parameters ({[hex(x) for x in sh1[:4]]})")
    check(o1 == [0] * 32, "the output: zeros")
    b2, sh2, o2 = go(b1, 11)
    check(b2[36] == 1 and b2[24] == 1 and sh2[1] == 11 and o2 == [0] * 32, f"next block: reset count kept, age 1, zeros ({b2[36]}, {b2[24]})")
    b3, sh3, o3 = go(b2, 12)
    check(b3[24] == 2 and o3 == pat, f"third block: age 2, the output = OUTF[1] at the slot's offset ({[hex(x) for x in o3[:3]]})")
    b4, sh4, o4 = go(b3, 14)
    check(b4[24] == 0 and o4 == [0] * 32, f"a block skipped: age 0, zeros ({b4[24]})")
    gc.collect()
    print(f"{man.get('marker', '?')} FMC1 CORE0 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text())) else 0)
