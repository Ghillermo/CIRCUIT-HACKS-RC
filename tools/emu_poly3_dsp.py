"""SC47.4 DSP test (vcf21_dsp.use_poly3): FM polyphonic, each voice on its own operator blocks (X:FV0 + 48 s).

    python tools/emu_poly3_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.3 / Beta 3.30)

vpre once a block on the interpreter (emu_poly2_dsp's harness), MIDI 1 in FM (the flag), the chain neutral:
  * one voice (the poly word 0): the FM voice as PREV's (the ring, the OSC blocks and the operator blocks bit for bit);
  * two voices (notes 48 / 55) on the operator blocks X:$3C00 / $3C30 (the same routing and levels as the one-voice runs): the ring = the sum of the
    two one-voice runs x the gain that goes from 0 to the target over the first block, then the target; each voice's phases / outputs stay in its
    own blocks (as the one-voice run's blocks); the track's blocks untouched;
  * a voice's noise: the record's + 10 (OSC1 + NZ_OFF) on = the ring differs, off = the same.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_smstereo_dsp as S  # noqa: E402
from emu_masterfx_dsp import s24, u24  # noqa: E402
import granular_dsp as GD  # noqa: E402
V = S.V
N, RING, OSB = S.N, S.RING, S.OSB
s56, lim, mpy = S.s56, S.lim, S.mpy
PVW = V.OS2B0 + V.PV_OFF - OSB
REC, RS = V.PV_REC0, V.PV_RS
T = 0x400000


def ops():
    F = 0x7FFFFF
    one = 1 << 19
    R, AMP, K = [one, one * 3 // 2, one, 4 * one], [0x600000, 0x500000, 0x600000, 0x380000], [0x1FFFFF, 0, 0x1FFFFF, 0]
    MM = [[0, F, 0, 0], [0, 0, 0, 0], [0, 0, 0, F], [0, 0, 0, 0x500000]]
    blk = [0] * 48
    for k in range(4):
        b = 12 * k
        blk[b + V.F_R], blk[b + V.F_AMP], blk[b + V.F_K] = R[k], AMP[k], K[k]
        for j in range(4): blk[b + V.F_M + j] = MM[k][j]
        blk[b + V.F_AS] = AMP[k]
    return blk


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    import poly as _PL
    _PL.adopt(man["report"])                                                          # (SC47.6: the six-record layout)
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")

    def go(which, note, blocks, recs=None, nz=0):
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.NOTE, note), (V.ACT, 2), (V.VEL, 127)):
            blk[k_] = v_
        osb = [0] * 144
        osb[V.FM_FLAG] = 1; osb[V.NZ_OFF] = nz
        fm = ops()
        fv = [0] * (48 * V.FV_N)
        rec = [0] * (RS * V.PV_N)
        if recs is not None:
            osb[PVW] = REC
            for i, r in enumerate(recs): rec[RS * i:RS * i + RS] = r
            for s_ in range(len(recs)): fv[48 * s_:48 * s_ + 48] = ops()
        outs, fms, fvs = [], [], []
        for b in range(blocks):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', REC, rec),
                                         ('x', V.FMB0, fm), ('x', V.FV0, fv), ('y', V.PV_Y0, [0] * (RS * V.PV_N))],
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', REC, RS * V.PV_N), ('x', V.FMB0, 48), ('x', V.FV0, 48 * V.FV_N)],
                           regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, rec, fm, fv = res[('x', V.VB0)], list(res[('x', OSB)]), list(res[('x', REC)]), list(res[('x', V.FMB0)]), list(res[('x', V.FV0)])
            outs.append(res[('y', RING)][0::2]); fms.append(fm); fvs.append(fv)
        gc.collect()
        return outs, fms, fvs

    def record(note, tgt, trig, fmb, nz=0):
        r = [0] * RS
        r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG], r[V.PV_FMB] = note, tgt, trig, fmb
        r[V.NZ_OFF - 28] = nz
        return r
    def mix(ring, gs, xs): return [lim(s56((s24(r) << 24) + mpy(g, x))) for r, g, x in zip(ring, gs, xs)]
    def ramp(g0, g1):
        inc = (g1 - g0) >> 5
        return [u24(g0 + inc * (i + 1)) for i in range(N)]

    # ---- one voice: as PREV
    on_, fn_, _ = go("new", 57, 4); oo, fo, _ = go("old", 57, 4)
    check(on_ == oo and fn_ == fo and any(any(x) for x in on_), "one FM voice: the ring and the operator blocks as the previous build's")
    # ---- two voices
    BL = 4
    recs = [record(48, T, 1, V.FV0), record(55, T, 1, V.FV0 + 48), record(0, 0, 0, 0), record(0, 0, 0, 0)]
    po, pf, pv = go("new", 64, BL, recs=recs)
    m0, f0, _ = go("new", 48, BL); m1, f1, _ = go("new", 55, BL)
    exp = [mix(mix([0] * N, ramp(0, T) if b == 0 else [T] * N, m0[b]), ramp(0, T) if b == 0 else [T] * N, m1[b]) for b in range(BL)]
    bad = [b for b in range(BL) if po[b] != exp[b]]
    check(not bad and any(any(x) for x in po), f"two FM voices (48 / 55): the sum x the gains block by block (bad blocks {bad[:4]}"
          f"{'' if not bad else ': ' + str([hex(x) for x in po[bad[0]][:3]]) + ' / ' + str([hex(x) for x in exp[bad[0]][:3]])})")
    check(pv[-1][:48] == f0[-1] and pv[-1][48:96] == f1[-1] and pf[-1] == ops(), "each voice's state in its own operator blocks (as the one-voice runs'), the track's blocks untouched")
    # ---- the noise of a voice
    rn = [record(48, T, 1, V.FV0, nz=0x100000), record(0, 0, 0, 0), record(0, 0, 0, 0), record(0, 0, 0, 0)]
    r0 = [record(48, T, 1, V.FV0), record(0, 0, 0, 0), record(0, 0, 0, 0), record(0, 0, 0, 0)]
    pn, _, _ = go("new", 64, 3, recs=rn); pz, _, _ = go("new", 64, 3, recs=r0)
    check(pn != pz and pz[1] == mix([0] * N, [T] * N, m0[1]), "a voice's noise (the record's + 10): on = added, off = the voice alone")
    print(f"{man.get('marker', '?')} POLY3 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
