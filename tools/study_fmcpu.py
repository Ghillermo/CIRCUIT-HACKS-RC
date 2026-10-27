"""Study (2026-10-27, the user: «se oye crackling en algunos fm al tocar muchas 4 notas o más»): what the FM voices cost core 0, on the emulated
build's own core-0 program (vpre once a block, emu_poly3_dsp's harness: MIDI 1 in FM, the chain neutral, poly records with N voices sounding).

    python tools/study_fmcpu.py BUILD.bin manifest.json

Prints the median instructions a block of vpre (both MIDI tracks' voices) for: no FM (the oscillator), FM one voice (mono), FM poly with
1..6 voices, and the budget left: core 0 runs about 166 000 instructions a block (0.67 ms), the stock and the rest of the mod about 118 000
with everything on (docs/RECURSOS.md).
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_poly3_dsp as P3  # noqa: E402

V, N, RING, OSB, GD = P3.V, P3.N, P3.RING, P3.OSB, P3.GD
BUDGET, OTHERS = 166_000, 118_000


def main(img, man):
    import poly as PL
    PL.adopt(man["report"])
    sp = dsp_program(img)
    prog = [int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)]
    vpre = int(man["report"]["sc16"]["dsp_labels"]["vpre"], 16)
    fvs = list(getattr(V, "FV_ADDRS", None) or [V.FV0 + 48 * s for s in range(V.FV_N)])
    RS, REC, PVW = V.PV_RS, V.PV_REC0, V.OS2B0 + V.PV_OFF - OSB

    def go(fm, nv, blocks=5):
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.NOTE, 60), (V.ACT, 2), (V.VEL, 127)):
            blk[k_] = v_
        osb = [0] * 144
        osb[V.FM_FLAG] = 1 if fm else 0
        rec = [0] * (RS * V.PV_N * 2)
        mem = {}
        if nv:
            osb[PVW] = REC
            for i in range(nv):
                r = [0] * RS
                r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG], r[V.PV_FMB] = 48 + 3 * i, P3.T, 1, fvs[i] if fm else 0
                rec[RS * i:RS * i + RS] = r
            for i in range(min(nv, len(fvs))): mem[fvs[i]] = P3.ops()
        ins = []
        for b in range(blocks):
            m = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)), ('x', OSB, osb),
                 ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', REC, rec), ('x', V.FMB0, P3.ops()),
                 ('y', V.PV_Y0, [0] * (RS * V.PV_N))] + [('x', a, v) for a, v in mem.items()]
            res, ran = run(prog, vpre, mem=m, dumps=[('x', V.VB0, 2 * V.VBS), ('x', OSB, 144), ('x', REC, RS * V.PV_N * 2)] + [('x', a, 48) for a in mem],
                           regs_code=[], maxins=40_000_000)
            assert 'pc=00' in ran, ran
            ins.append(int(ran.split('ins=')[1].split()[0]))
            blk, osb, rec = res[('x', V.VB0)], list(res[('x', OSB)]), list(res[('x', REC)])
            mem = {a: list(res[('x', a)]) for a in mem}
        gc.collect()
        return sorted(ins[1:])[len(ins[1:]) // 2]

    rows = [("oscillator, one voice", go(False, 0)), ("FM mono (one voice)", go(True, 0))]
    for n in range(1, len(fvs) + 1): rows.append((f"FM poly, {n} voice{'s' if n > 1 else ''}", go(True, n)))
    base = rows[0][1]
    for name, ins in rows:
        print(f"{name:26s} {ins:7d} instructions a block  (+{ins - base:6d} over the oscillator; with the rest {OTHERS + ins - base:7d} of {BUDGET})")


if __name__ == "__main__":
    main(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_text()))
