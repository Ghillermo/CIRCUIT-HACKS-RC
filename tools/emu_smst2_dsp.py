"""SC46.8 DSP test (vcf21_dsp.use_smstereo2): the stereo sample mode's second sample at the ARM's distance K and the longer length.

    python tools/emu_smst2_dsp.py NEW.bin NEW_manifest.json PREV.bin PREV_manifest.json      (PREV = SC46.7 / Beta 3.24)

vpre once a block on the dsp56kEmu interpreter (emu_smstereo_dsp's harness), MIDI 1 in the sample mode, WAVE 100, note 60 (one sample a frame):
  * the right = (N + K) & 63 with K at OSC1 + 43 (K 2: sample 5; K 61 from 3: sample 0), its own length at OSC1 + 34;
  * the left longer (900 / 700): every block against the model: both playing = the mid and the side of the two; once the furthest position of a
    block (the position + 129) passes the right's end, the right is silence (the mid L / 2, the side L / 2 x the width); when it passes the left's
    too, the note ends (playing 0, silence);
  * the right longer: the left silence after its end, the right goes on to its own end;
  * WAVE 0: the ring and the OSC1 block as PREV's (mono, the left's length).
"""
from __future__ import annotations
import json, sys
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


def main(img, man, prev, pman):
    fails = 0
    def check(c, m):
        nonlocal fails
        print(("ok  : " if c else "FAIL: ") + m); fails += 0 if c else 1
    progs = {}
    for name, im, mf in (("new", img, man), ("old", prev, pman)):
        sp = dsp_program(im)
        progs[name] = ([int.from_bytes(sp[i:i + 3], 'big') for i in range(0, len(sp), 3)], int(mf["report"]["sc16"]["dsp_labels"]["vpre"], 16))
    check(len(progs["new"][0]) <= 0x4000, f"core 0's program ends at P:${len(progs['new'][0]):x} (the previous build: ${len(progs['old'][0]):x})")
    YA, YB = 0x40000, 0x48000
    def data(la, lb):
        y = {}
        for i in range(la + 200): y[YA + i] = u24(int(0x500000 * ((i * 37 % 200) - 100) / 100)) & 0xFFFF00
        for i in range(lb + 200): y[YB + i] = u24(int(0x300000 * ((i * 53 % 160) - 80) / 80)) & 0xFFFF00
        return y
    def go(which, la, lb, k, wave, blocks, nl=3):
        ydat = data(la, lb)
        P, vpre = progs[which]
        blk = [0] * (2 * V.VBS)
        for kk, v in dict(GAIN=64, DEC=40, SUS=100, REL=40, LRATE=0, FXMOD=64, NOTE=60, ACT=3).items():
            blk[dict(GAIN=V.P_GAIN, DEC=V.P_DEC, SUS=V.P_SUS, REL=V.P_REL, LRATE=V.P_LRATE, FXMOD=V.P_FXMOD, NOTE=V.NOTE, ACT=V.ACT)[kk]] = v
        osb = [0] * 144
        osb[2] = wave; osb[8] = nl; osb[V.SM_N] = 1; osb[V.SM_K] = k
        tab = {}
        for slot in range(64): tab[V.SM_TAB + 4 * slot], tab[V.SM_TAB + 4 * slot + 1] = 0x60000, 100
        tab[V.SM_TAB + 4 * nl], tab[V.SM_TAB + 4 * nl + 1] = YA, la
        r = (nl + k) & 63
        tab[V.SM_TAB + 4 * r], tab[V.SM_TAB + 4 * r + 1] = YB, lb
        mem_y = [('y', a_, [v_]) for a_, v_ in ydat.items()]
        rd = 0x40
        outs, sides, osbs = [], [], []
        for _ in range(blocks):
            res, ran = run(P, vpre, mem=[('x', 0x3A, [N]), ('x', V.VB0, blk), ('x', V.FLAGS, [0]), ('y', V.RING_PTR, [RING]), ('y', RING, [0] * (2 * N)),
                                         ('x', OSB, osb), ('x', GD.RDOFS, [rd]), ('x', GD.SOUT, [0] * 128)] + [('x', a_, [v_]) for a_, v_ in tab.items()] + mem_y,
                           dumps=[('x', V.VB0, 2 * V.VBS), ('y', RING, 2 * N), ('x', OSB, 144), ('x', GD.SOUT, 128)], regs_code=[], maxins=4_000_000)
            assert 'pc=00' in ran, ran
            blk, osb = res[('x', V.VB0)], res[('x', OSB)]
            outs.append(res[('y', RING)][0::2]); sides.append(res[('x', GD.SOUT)][rd:rd + 32]); osbs.append(list(osb))
        return outs, sides, osbs, ydat
    def model(ydat, la, lb, blocks, w):
        Y = lambda a_: ydat.get(a_, 0)
        out, sid, on = [], [], []
        pos, frac, playing = 0, 0, True
        for _ in range(blocks):
            if not playing: out.append([0] * N); sid.append([0] * N); on.append(0); continue
            far = pos + 64 * 2 + 1
            dl, dr = far >= la, far >= lb
            if dl and dr: playing = False; out.append([0] * N); sid.append([0] * N); on.append(0); continue
            L_, npos, nfrac = S.interp(Y, YA, pos, frac, 1, 0, N)
            R_, _, _ = S.interp(Y, YB, pos, frac, 1, 0, N)
            if dl: L_ = [0] * N
            if dr: R_ = [0] * N
            out.append([lim(s56(((s24(l) << 24) + (s24(r) << 24)) >> 1)) for l, r in zip(L_, R_)])
            sid.append([lim(mpy(lim(s56(((s24(l) << 24) - (s24(r) << 24)) >> 1)), w << 16)) for l, r in zip(L_, R_)])
            on.append(1); pos, frac = npos, nfrac
        return out, sid, on
    for la, lb, nm in ((300, 200, "the left longer"), (200, 300, "the right longer")):
        bl = 12
        o, s_, q, yd = go("new", la, lb, 2, 100, bl)
        mo, ms, mon = model(yd, la, lb, bl, 100)
        ons = [x[V.SM_ON] for x in q]
        bad = [k for k in range(bl) if o[k] != mo[k] or s_[k] != ms[k] or (ons[k] != 0) != (mon[k] != 0)]
        check(q[0][V.SM_S2] == YB and q[0][V.SM_L2] == lb and q[0][V.SM_L] == la and not bad and 0 in ons and any(any(x) for x in o),
              f"{nm} ({la} / {lb}): the right = sample 5 (K 2), its own length; {bl} blocks against the model (both, one silent, the end at the longer: "
              f"playing {ons}; bad blocks {bad[:4]})")
    o, s_, q, yd = go("new", 300, 300, 61, 100, 1)
    check(q[0][V.SM_S2] == YB, f"K 61 from sample 3: the right = sample 0 ({q[0][V.SM_S2]:#x})")
    on_, sn, qn, _ = go("new", 300, 200, 2, 0, 8); oo, so, qo, _ = go("old", 300, 200, 2, 0, 8)
    ours = set(range(V.SM_S2, V.SM_T2 + 1)) | {V.SM_K, V.SM_L2, V.SM_FAR}
    check(on_ == oo and [[x for i, x in enumerate(r[:48]) if i not in ours] for r in qn] == [[x for i, x in enumerate(r[:48]) if i not in ours] for r in qo],
          "WAVE 0: the ring and the OSC1 block as the previous build's (mono, the left's length)")
    print(f"{man.get('marker', '?')} SMST2 DSP RESULT:", "ALL PASS" if fails == 0 else f"{fails} FAILURES")
    return fails


if __name__ == "__main__":
    a = sys.argv
    sys.exit(1 if main(Path(a[1]).read_bytes(), json.loads(Path(a[2]).read_text()), Path(a[3]).read_bytes(), json.loads(Path(a[4]).read_text())) else 0)
