"""SC38.1 on DSP core 1 (tools/granular_dsp.py, unchanged; dsp56kEmu interpreter): what the stretch mode of vcf21.use_stretch sends places the grains.

    python tools/emu_sc38_1_core1.py
The voice gets the pitch mode (P26 0), the scan frozen (P21 0), the smallest zone (P23 -64) and a position P19: the zone is Z = L / 128, its start
ZS = (L - Z) P19 / 128, the playhead stays 0, so the first grain starts at S + ZS (a block later it has read 32 samples): P19 = 0 / 32 / 63 / 126.
A playhead left by an earlier scan is folded back into [0, Z) at once (so the stretch is never more than L / 128 off).  Same driver as emu_gran_core1.py.
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
L = 20000


def main():
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    stock = (Path(__file__).resolve().parents[1] / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    W = lambda bb: [int.from_bytes(bb[i:i + 3], "big") for i in range(0, len(bb), 3)]
    P1s = W(dsp_program(stock, 1))
    w1, l1 = GD.core1_code(P5.C1_STOCK_WORDS, rl=RL, rn=RN)
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

    def vin(t, **kw):
        osb_n = dict(P17=0, P18=1, P19=2, P20=3, P21=4, P22=5, P23=6, P24=7, P25=8, P26=9, NOTE2=20, DFL=21)
        vb_n = dict(NOTE=19, ACT=20, ENV=23, LV=26)
        base = dict(P18=-64, P20=0, P23=-64, P21=0, P26=0, NOTE=60, NOTE2=60, ACT=2, DFL=16, S=SRC, L=L, ENV=0, LV=0, P25=0)
        base.update(kw)
        osb, os2, vb = [0] * 22, [0] * 8, [0] * 48
        for k, x in base.items():
            if k in osb_n: osb[osb_n[k]] = x & 0xFFFFFF
            elif k in vb_n: vb[vb_n[k]] = x & 0xFFFFFF
        return [('x', GD.SHA + 48 * t, osb), ('x', GD.SHA + 0x60 + 48 * t, os2), ('x', GD.SHB + 48 * t, vb), ('x', GD.SHT + 4 * base["P25"], [base["S"], base["L"], 0, 0])]

    def go(nblocks, mem, dumps):
        res, ran = run(program(nblocks), C1, mem=list(mem), regs_code=[], pc=C1, stop=STOP, maxins=20_000_000, dumps=dumps)
        assert ran and 'pc=003ff0' in ran.lower(), ran
        return res

    const = [0x400000] * L
    Z = max(64, L >> 7)
    for p19 in (0, 32, 63, 126):
        R = go(2, [('y', SRC, const), *vin(0, P19=p19)], [('x', GD.GR0, 12), ('x', GD.VS0, 32)])
        vs, gr = R[('x', GD.VS0)], R[('x', GD.GR0)]
        zs = ((L - Z) * p19) >> 7
        check(vs[GD.V_Z] == Z and vs[GD.V_ZS] == zs and vs[GD.V_PH] == 0 and gr[GD.G_PH] == SRC + zs + 32,
              f"P19 {p19}: zone {vs[GD.V_Z]} (L / 128 = {Z}), start {vs[GD.V_ZS]} (want {zs}), playhead {vs[GD.V_PH]}, grain at {gr[GD.G_PH] - 32 - SRC}")
        gc.collect()
    # a playhead left by a scan (the voice already on, PH = 5000 > Z): folded back into [0, Z)
    R = go(2, [('y', SRC, const), *vin(0, P19=63), ('x', GD.VS0 + GD.V_ON, [1]), ('x', GD.VS0 + GD.V_PH, [5000])], [('x', GD.VS0, 32)])
    vs = R[('x', GD.VS0)]
    check(0 <= vs[GD.V_PH] < Z, f"an earlier playhead 5000 is folded into [0, {Z}): {vs[GD.V_PH]}")
    print("SC38.1 CORE 1 RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
