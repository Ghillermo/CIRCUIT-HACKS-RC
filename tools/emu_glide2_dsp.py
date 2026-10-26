"""SC47.6 DSP test (vcf21_dsp.use_glide2, use_poly6): the track's glide under the unison, the jump, six FM voices' blocks.

    python tools/emu_glide2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC47.5 / Beta 3.32)

vpre once a block on the interpreter (emu_poly3_dsp's harness), MIDI 1, the chain neutral:
  * the glide off: the ring as the previous build's (one oscillator, a note change 60 -> 72);
  * the glide on, one voice: the track's offset (OSC2 + 46) block by block = (GT - (note - last) << 16) x GK towards 0; OSC1 + 34 stays 0;
  * the jump: with the ARM's counter (OSC2 + 47) ahead of the one seen (+ 41) a note change does not glide (GT 0, the counter seen);
  * the records on (the unison): the glide follows the first record's note (the track's note unchanged);
  * two FM voices on the slots 4 / 5 (X:$3CC0, $3FB4) ring as the same two on the slots 0 / 1.
"""
from __future__ import annotations
import gc, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dspemu import run  # noqa: E402
from dsp_session import dsp_program  # noqa: E402
import emu_smstereo_dsp as S  # noqa: E402
import emu_poly3_dsp as P3  # noqa: E402
from emu_masterfx_dsp import s24  # noqa: E402
import granular_dsp as GD  # noqa: E402
import vmode as VM  # noqa: E402
import poly as PL  # noqa: E402
V = S.V
N, RING, OSB = S.N, S.RING, S.OSB
T = 0x400000


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    assert PL.adopt(man["report"]), "a build with poly.use_v5"
    O2 = V.OS2B0 - OSB
    GO, GK, LN, GT, JMP, JSN, PVW = V.GO_OFF, O2 + V.GK_OFF, O2 + V.LN_OFF, O2 + V.GT_OFF, O2 + V.JMP_OFF, O2 + V.JSN_OFF, O2 + V.PV_OFF
    REC, RS = V.PV_REC0, V.PV_RS
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")

    def go(which, steps, osb0=None, recs=None, fm=False, fvs=None):
        """steps: a list of (the track's note, the first record's note or None, a jump before this block)."""
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for k_, v_ in ((V.P_GAIN, 64), (V.P_DEC, 40), (V.P_SUS, 100), (V.P_REL, 40), (V.P_FXMOD, 64), (V.ACT, 2), (V.VEL, 127)):
            blk[k_] = v_
        osb = list(osb0) if osb0 else [0] * 144
        if fm: osb[V.FM_FLAG] = 1
        rec = [0] * (RS * V.PV_N)
        if recs is not None:
            osb[PVW] = REC
            for i, r in enumerate(recs): rec[RS * i:RS * i + RS] = r
        fvs = dict(fvs or {})
        outs, gts, os1 = [], [], []
        for nt, rn, jump in steps:
            blk[V.NOTE] = nt
            if rn is not None: rec[V.PV_NOTE] = rn
            if jump: osb[JMP] = (osb[JMP] + 1) & 0xFFFFFF
            mem = [('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                   ('x', OSB, osb), ('x', GD.RDOFS, [0x40]), ('x', GD.SOUT, [0] * 128), ('x', V.SIDE0, [0, 0]), ('x', REC, rec),
                   ('y', V.PV_Y0, [0] * (RS * V.PV_N))] + [('x', a_, b_) for a_, b_ in fvs.items()]
            if fm: mem.append(('x', V.FMB0, P3.ops()))
            res, ran = run(P, vpre, mem=mem, dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', REC, RS * V.PV_N)]
                           + [('x', a_, 48) for a_ in fvs], regs_code=[], maxins=20_000_000)
            assert 'pc=00' in ran, ran
            blk, osb, rec = res[('x', V.VB0)], list(res[('x', OSB)]), list(res[('x', REC)])
            fvs = {a_: list(res[('x', a_)]) for a_ in fvs}
            outs.append(res[('y', RING)][0::2]); gts.append(s24(osb[GT])); os1.append(osb[GO])
        gc.collect()
        return outs, gts, os1, osb

    def model(notes, g, jumps=()):
        want, gt, ln = [], 0, notes[0]
        for i, nt in enumerate(notes):
            if nt != ln and i in jumps: x = 0
            else: x = max(-0x800000, min(0x7FFFFF, gt - ((nt - ln) << 16)))
            ln = nt
            prod = x * g * 2
            gt = (prod >> 24) + (1 if prod < 0 else 0)
            want.append(gt)
        return want

    st = [(60, None, False)] * 3 + [(72, None, False)] * 4
    a_, _, _, _ = go("new", st); b_, _, _, _ = go("old", st)
    check(a_ == b_ and any(any(x) for x in a_), "the glide off: the ring as the previous build's (a note change too)")
    g = VM.gk(48)
    base = [0] * 144; base[GK] = g; base[LN] = 60
    notes = [60] * 2 + [72] * 6
    _, gts, os1, _ = go("new", [(n_, None, False) for n_ in notes], osb0=base)
    check(gts == model(notes, g) and gts[2] < 0 and not any(os1), f"one voice: the track's offset = the model ({gts[2:5]}), OSC1 + 34 stays 0")
    notes = [60] * 2 + [72] * 3 + [67] * 3
    stj = [(n_, None, i == 2) for i, n_ in enumerate(notes)]
    _, gts, _, osb = go("new", stj, osb0=base)
    check(gts == model(notes, g, jumps={2}) and gts[2] == 0 and gts[5] != 0 and osb[JSN] == osb[JMP], f"the jump: 72 without a glide ({gts[2]}), 67 glides ({gts[5]}), the counter seen")
    rec0 = [0] * RS; rec0[V.PV_NOTE], rec0[V.PV_TGT], rec0[V.PV_TRIG] = 60, T, 1
    blank = [0] * RS
    rnotes = [60] * 2 + [72] * 4
    _, gts, _, _ = go("new", [(60, n_, False) for n_ in rnotes], osb0=base, recs=[rec0] + [blank] * (V.PV_N - 1))
    check(gts == model(rnotes, g) and gts[2] < 0, f"the records on: the glide follows the first record's note ({gts[2:5]})")
    # ---- FM voices on the slots 4 / 5
    def frec(note, fmb):
        r = [0] * RS; r[V.PV_NOTE], r[V.PV_TGT], r[V.PV_TRIG], r[V.PV_FMB] = note, T, 1, fmb; return r
    fa = V.FV_ADDRS
    lo, _, _, _ = go("new", [(64, None, False)] * 3, recs=[frec(48, fa[0]), frec(55, fa[1])] + [blank] * (V.PV_N - 2), fm=True, fvs={fa[0]: P3.ops(), fa[1]: P3.ops()})
    hi, _, _, _ = go("new", [(64, None, False)] * 3, recs=[frec(48, fa[4]), frec(55, fa[5])] + [blank] * (V.PV_N - 2), fm=True, fvs={fa[4]: P3.ops(), fa[5]: P3.ops()})
    check(lo == hi and any(any(x) for x in hi), f"two FM voices on the slots 4 / 5 ({fa[4]:#x}, {fa[5]:#x}) ring as on the slots 0 / 1")
    print(f"{man.get('marker', '?')} GLIDE2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
